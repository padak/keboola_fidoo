#!/usr/bin/env python3
"""
Fidoo Expense Management Data Extractor for Keboola

This component extracts data from Fidoo expense management system and loads it into Keboola Storage.

Configuration:
- FIDOO_API_KEY: Fidoo API key (encrypted)
- objects: List of objects to export (e.g., ["user", "card", "transaction", "expense"])
- output_bucket: Destination bucket in Keboola Storage (default: out.c-fidoo)

Available objects:
- user: User management
- card: Prepaid cards
- transaction: Card transactions
- cash_transaction: Cash transactions
- mvc_transaction: MVC transactions
- expense: Expenses
- travel_report: Travel reports
- travel_request: Travel requests
- personal_billing: Personal billing
- account: Accounts
- cost_center: Cost centers
- project: Projects
- account_assignment: Account assignments
- accounting_category: Accounting categories
- vat_breakdown: VAT breakdowns
- vehicle: Vehicles
- receipt: Receipts

State file tracks:
- last_run: Last successful run timestamp
- object_counts: Number of records exported per object
"""

import logging
import csv
import json
import os
import time
from datetime import datetime

import duckdb
import pandas as pd


# Time profiler for tracking execution times
class TimeProfiler:
    def __init__(self):
        self.start_time = time.time()
        self.api_calls = {}  # {endpoint: {"time": float, "records": int}}
        self.dependent_calls = {}  # {endpoint: {"time": float, "calls": int, "records": int}}
        self.processing = {
            "duckdb_inserts": 0.0,
            "csv_export": 0.0,
            "nested_extraction": 0.0,
        }

    def format_duration(self, seconds):
        """Format seconds into human-readable string"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        minutes = int(seconds // 60)
        secs = seconds % 60
        if minutes < 60:
            return f"{minutes}m {secs:.0f}s"
        hours = int(minutes // 60)
        mins = minutes % 60
        return f"{hours}h {mins}m {secs:.0f}s"

    def print_summary(self):
        """Print the time profile summary"""
        total_time = time.time() - self.start_time

        # Calculate totals
        api_total = sum(v["time"] for v in self.api_calls.values())
        dependent_total = sum(v["time"] for v in self.dependent_calls.values())
        processing_total = sum(self.processing.values())

        lines = [
            "",
            "=" * 50,
            "TIME PROFILE",
            "=" * 50,
            f"Total runtime: {self.format_duration(total_time)}",
            "",
            "API Calls (Primary Endpoints):",
        ]

        # Sort by time descending
        for name, data in sorted(self.api_calls.items(), key=lambda x: -x[1]["time"]):
            lines.append(f"  {name:30} {self.format_duration(data['time']):>8} ({data['records']} records)")

        if self.dependent_calls:
            lines.append("")
            lines.append("Dependent Endpoints (iterate over parent IDs):")
            for name, data in sorted(self.dependent_calls.items(), key=lambda x: -x[1]["time"]):
                lines.append(f"  {name:30} {self.format_duration(data['time']):>8} ({data['calls']} calls, {data['records']} records)")

        lines.extend([
            "",
            "Processing:",
            f"  {'DuckDB inserts':30} {self.format_duration(self.processing['duckdb_inserts']):>8}",
            f"  {'CSV export':30} {self.format_duration(self.processing['csv_export']):>8}",
            f"  {'Nested extraction':30} {self.format_duration(self.processing['nested_extraction']):>8}",
            "",
            "Summary:",
        ])

        all_api_time = api_total + dependent_total
        if total_time > 0:
            api_pct = (all_api_time / total_time) * 100
            proc_pct = (processing_total / total_time) * 100
            lines.append(f"  API calls total:       {self.format_duration(all_api_time):>8} ({api_pct:.0f}%)")
            lines.append(f"  Processing total:      {self.format_duration(processing_total):>8} ({proc_pct:.0f}%)")

        lines.append("=" * 50)

        return "\n".join(lines)


# Global profiler instance
profiler = TimeProfiler()

try:
    from keboola.component import CommonInterface
    from keboola.component.dao import BaseType, ColumnDefinition
except ImportError:
    # For local testing
    pass

from fidoo_driver import (
    FidooDriver,
    ValidationError,
    TimeoutError,
    AuthenticationError,
    RateLimitError,
    ObjectNotFoundError,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Primary endpoints - can be batch-read directly
PRIMARY_ENDPOINTS = {
    "user": "user/get-users",
    "card": "card/get-cards",
    "transaction": "transaction/get-card-transactions",
    "cash_transaction": "cash-transactions/get-cash-transactions",
    "mvc_transaction": "mvc-transaction/get-transactions",
    "expense": "expense/get-expenses",
    "travel_report": "travel/get-travel-reports",
    "travel_request": "travel/get-travel-requests",
    "personal_billing": "personal-billing/get-billings",
    "account": "accounts/get-accounts",
    "cost_center": "settings/get-cost-centers",
    "project": "settings/get-projects",
    "account_assignment": "settings/get-account-assignments",
    "accounting_category": "settings/get-accounting-categories",
    "vat_breakdown": "settings/get-vat-breakdowns",
    "vehicle": "settings/get-vehicles",
}

# Dependent endpoints - require IDs from primary objects
DEPENDENT_ENDPOINTS = {
    "expense_item": {
        "endpoint": "expense/get-expense-items",
        "source_table": "expense",
        "source_id_field": "expenseId",
        "param_name": "expenseId",
    },
    "travel_report_detail": {
        "endpoint": "travel/get-travel-report-detail",
        "source_table": "travel_report",
        "source_id_field": "travelReportId",
        "param_name": "travelReportId",
    },
    "travel_request_detail": {
        "endpoint": "travel/get-travel-request-detail",
        "source_table": "travel_request",
        "source_id_field": "travelRequestId",
        "param_name": "travelRequestId",
    },
}

# Combined for backward compatibility
OBJECT_ENDPOINTS = {**PRIMARY_ENDPOINTS}


def flatten_json(obj):
    """Flatten nested JSON objects to string representation"""
    if isinstance(obj, dict):
        return json.dumps(obj)
    elif isinstance(obj, list):
        return json.dumps(obj)
    return str(obj) if obj is not None else ""


def flatten_record(record):
    """Flatten a single record, converting nested objects to JSON strings"""
    flat = {}
    for key, value in record.items():
        if isinstance(value, (dict, list)):
            flat[key] = json.dumps(value)
        else:
            flat[key] = value
    return flat


def detect_primary_key(records, table_name):
    """Detect the primary key field for a table"""
    if not records:
        return None

    # Common primary key patterns
    candidates = [
        f"{table_name}Id",  # expenseId, userId
        f"{table_name.rstrip('s')}Id",  # expenses -> expenseId
        "id",
        "Id",
    ]

    first_record = records[0]
    for candidate in candidates:
        if candidate in first_record:
            return candidate

    # Fallback: first field ending with 'Id'
    for key in first_record.keys():
        if key.endswith('Id'):
            return key

    return None


def extract_nested(records, table_name, primary_key=None):
    """
    Extract nested objects/arrays into separate normalized tables.

    Args:
        records: List of records (dicts)
        table_name: Name of the main table
        primary_key: Primary key field name (auto-detected if None)

    Returns:
        Tuple of (main_records, nested_tables_dict)
        nested_tables_dict: {table_name: [records]}
    """
    if not records:
        return [], {}

    # Auto-detect primary key if not provided
    if primary_key is None:
        primary_key = detect_primary_key(records, table_name)

    main_records = []
    nested_tables = {}  # {field_name: [records]}

    for record in records:
        main = {}
        pk_value = record.get(primary_key) if primary_key else None

        for key, value in record.items():
            if isinstance(value, dict) and value:
                # Nested object → separate table
                nested_name = f"{table_name}__{key}"
                if nested_name not in nested_tables:
                    nested_tables[nested_name] = []

                nested_record = {"parent_id": pk_value, **value}
                nested_tables[nested_name].append(nested_record)

            elif isinstance(value, list) and value:
                # Check if it's a list of objects or primitives
                if isinstance(value[0], dict):
                    # Array of objects → separate table
                    nested_name = f"{table_name}__{key}"
                    if nested_name not in nested_tables:
                        nested_tables[nested_name] = []

                    for i, item in enumerate(value):
                        nested_record = {"parent_id": pk_value, "idx": i, **item}
                        nested_tables[nested_name].append(nested_record)
                else:
                    # Array of primitives → separate table with value column
                    nested_name = f"{table_name}__{key}"
                    if nested_name not in nested_tables:
                        nested_tables[nested_name] = []

                    for i, item in enumerate(value):
                        nested_record = {"parent_id": pk_value, "idx": i, "value": item}
                        nested_tables[nested_name].append(nested_record)
            else:
                # Regular field or empty list/dict
                if isinstance(value, (dict, list)):
                    main[key] = json.dumps(value) if value else None
                else:
                    main[key] = value

        main_records.append(main)

    # Recursively extract nested from nested tables
    all_nested = {}
    for nested_name, nested_records in nested_tables.items():
        # Extract any further nesting
        flat_nested, deeper_nested = extract_nested(nested_records, nested_name, "parent_id")
        all_nested[nested_name] = flat_nested
        all_nested.update(deeper_nested)

    return main_records, all_nested


def insert_to_duckdb(conn, table_name, records):
    """Insert records into DuckDB table, creating it if needed."""
    if not records:
        return

    start = time.time()
    df = pd.DataFrame(records)

    # Check if table exists
    tables = [t[0] for t in conn.execute("SHOW TABLES").fetchall()]

    if table_name not in tables:
        conn.execute(f"CREATE TABLE \"{table_name}\" AS SELECT * FROM df")
    else:
        conn.execute(f"INSERT INTO \"{table_name}\" SELECT * FROM df")

    profiler.processing["duckdb_inserts"] += time.time() - start


def export_primary_to_duckdb(conn, driver, object_type, endpoint):
    """
    Export a primary object type from Fidoo directly to DuckDB.
    Automatically normalizes nested objects into separate tables.

    Args:
        conn: DuckDB connection
        driver: FidooDriver instance
        object_type: Type of object (table name)
        endpoint: API endpoint path

    Returns:
        Number of records exported (main table only)
    """
    logger.info(f"Exporting {object_type} from endpoint: {endpoint}")

    # Collect all records first for proper normalization
    all_records = []
    api_start = time.time()
    try:
        for batch in driver.read_batched(endpoint, batch_size=100):
            if not batch:
                continue
            all_records.extend(batch)
            logger.info(f"  Fetched batch: {len(batch)} records (total: {len(all_records)})")

    except ObjectNotFoundError as e:
        logger.warning(f"Object {object_type} not found or empty: {e.message}")
        profiler.api_calls[object_type] = {"time": time.time() - api_start, "records": 0}
        return 0
    except RateLimitError as e:
        logger.error(f"Rate limit exceeded: {e.message}")
        raise
    except TimeoutError as e:
        logger.error(f"Request timed out: {e.message}")
        raise

    api_time = time.time() - api_start
    profiler.api_calls[object_type] = {"time": api_time, "records": len(all_records)}

    if not all_records:
        logger.warning(f"No records found for {object_type}")
        return 0

    # Extract nested objects into separate tables
    nested_start = time.time()
    main_records, nested_tables = extract_nested(all_records, object_type)
    profiler.processing["nested_extraction"] += time.time() - nested_start

    # Drop existing tables
    conn.execute(f"DROP TABLE IF EXISTS \"{object_type}\"")
    for nested_name in nested_tables.keys():
        conn.execute(f"DROP TABLE IF EXISTS \"{nested_name}\"")

    # Insert main table
    insert_to_duckdb(conn, object_type, main_records)
    logger.info(f"Total {object_type} records: {len(main_records)}")

    # Insert nested tables
    for nested_name, nested_records in nested_tables.items():
        if nested_records:
            insert_to_duckdb(conn, nested_name, nested_records)
            logger.info(f"  → {nested_name}: {len(nested_records)} records")

    return len(main_records)


def export_dependent_to_duckdb(conn, driver, object_type, config):
    """
    Export a dependent object type that requires IDs from a primary table.

    Args:
        conn: DuckDB connection
        driver: FidooDriver instance
        object_type: Type of object (table name)
        config: Configuration dict with endpoint, source_table, source_id_field, param_name

    Returns:
        Number of records exported
    """
    endpoint = config["endpoint"]
    source_table = config["source_table"]
    source_id_field = config["source_id_field"]
    param_name = config["param_name"]

    # Check if source table exists
    tables = conn.execute("SHOW TABLES").fetchall()
    table_names = [t[0] for t in tables]

    if source_table not in table_names:
        logger.warning(f"Source table {source_table} not found, skipping {object_type}")
        return 0

    # Get unique IDs from source table
    try:
        ids = conn.execute(f"SELECT DISTINCT {source_id_field} FROM {source_table} WHERE {source_id_field} IS NOT NULL").fetchall()
        ids = [row[0] for row in ids]
    except Exception as e:
        logger.warning(f"Could not get IDs from {source_table}.{source_id_field}: {e}")
        return 0

    if not ids:
        logger.warning(f"No IDs found in {source_table}.{source_id_field}, skipping {object_type}")
        return 0

    logger.info(f"Exporting {object_type} for {len(ids)} {source_id_field}s")

    # Collect all records first for proper normalization
    all_records = []
    api_start = time.time()
    call_count = 0

    for i, id_value in enumerate(ids):
        try:
            # Call endpoint with the ID parameter
            records = driver.read(endpoint, limit=100, **{param_name: id_value})
            call_count += 1

            if not records:
                continue

            # Add source ID to each record for reference
            for record in records:
                record[f"_source_{source_id_field}"] = id_value

            all_records.extend(records)

            if (i + 1) % 10 == 0:
                logger.info(f"  Processed {i + 1}/{len(ids)} IDs (total records: {len(all_records)})")

        except Exception as e:
            logger.warning(f"Error fetching {object_type} for {id_value}: {e}")
            continue

    api_time = time.time() - api_start
    profiler.dependent_calls[object_type] = {"time": api_time, "calls": call_count, "records": len(all_records)}

    if not all_records:
        logger.info(f"Total {object_type} records: 0")
        return 0

    # Extract nested objects into separate tables
    nested_start = time.time()
    main_records, nested_tables = extract_nested(all_records, object_type)
    profiler.processing["nested_extraction"] += time.time() - nested_start

    # Drop existing tables
    conn.execute(f"DROP TABLE IF EXISTS \"{object_type}\"")
    for nested_name in nested_tables.keys():
        conn.execute(f"DROP TABLE IF EXISTS \"{nested_name}\"")

    # Insert main table
    insert_to_duckdb(conn, object_type, main_records)
    logger.info(f"Total {object_type} records: {len(main_records)}")

    # Insert nested tables
    for nested_name, nested_records in nested_tables.items():
        if nested_records:
            insert_to_duckdb(conn, nested_name, nested_records)
            logger.info(f"  → {nested_name}: {len(nested_records)} records")

    return len(main_records)


def get_primary_key_for_table(conn, table_name):
    """
    Detect primary key columns for a table.

    Returns:
        List of column names that form the primary key
    """
    # Get columns for this table
    columns = conn.execute(f"DESCRIBE \"{table_name}\"").fetchall()
    column_names = [col[0] for col in columns]

    # Nested tables use parent_id + _index as composite key
    if "__" in table_name:
        pk = []
        if "parent_id" in column_names:
            pk.append("parent_id")
        if "idx" in column_names:
            pk.append("idx")
        return pk if pk else None

    # Primary tables - look for {table_name}Id pattern
    base_name = table_name.replace("_", "")
    candidates = [
        f"{table_name}Id",           # expenseId
        f"{base_name}Id",            # expense -> expenseId
        f"{table_name.rstrip('s')}Id",  # users -> userId
        "id",
        "Id",
    ]

    for candidate in candidates:
        if candidate in column_names:
            return [candidate]

    # Fallback: first column ending with 'Id'
    for col in column_names:
        if col.endswith('Id') and not col.startswith('_'):
            return [col]

    return None


def export_duckdb_to_csv(conn, ci, output_bucket, set_primary_keys=True):
    """
    Export all tables from DuckDB to CSV files for Keboola.

    Args:
        conn: DuckDB connection
        ci: CommonInterface instance
        output_bucket: Destination bucket in Keboola Storage
        set_primary_keys: Whether to set primary keys in manifests

    Returns:
        Dict of table_name -> record_count
    """
    tables = conn.execute("SHOW TABLES").fetchall()
    table_names = [t[0] for t in tables]

    export_counts = {}

    for table_name in table_names:
        # Get record count
        count = conn.execute(f"SELECT COUNT(*) FROM \"{table_name}\"").fetchone()[0]

        if count == 0:
            logger.info(f"Skipping empty table: {table_name}")
            export_counts[table_name] = 0
            continue

        # Detect primary key
        primary_key = get_primary_key_for_table(conn, table_name) if set_primary_keys else None

        # Create output table definition
        csv_name = f"{table_name}.csv"
        destination = f"{output_bucket}.{table_name}"

        out_table = ci.create_out_table_definition(
            name=csv_name,
            destination=destination,
            primary_key=primary_key,
            incremental=False,
            has_header=True,
        )

        # Export to CSV using DuckDB
        csv_start = time.time()
        conn.execute(f"COPY \"{table_name}\" TO '{out_table.full_path}' (HEADER, DELIMITER ',')")
        profiler.processing["csv_export"] += time.time() - csv_start

        pk_info = f" [PK: {', '.join(primary_key)}]" if primary_key else ""
        logger.info(f"Exported {count} records from {table_name}{pk_info}")

        # Write manifest
        ci.write_manifest(out_table)

        export_counts[table_name] = count

    return export_counts


def update_state(ci, object_counts):
    """Update state file for tracking"""
    state = {
        "last_run": datetime.now().isoformat(),
        "object_counts": object_counts,
    }
    ci.write_state_file(state)
    logger.info(f"State updated: {object_counts}")


def main():
    """Main entry point for Keboola component"""
    global profiler
    profiler = TimeProfiler()  # Reset profiler for this run

    try:
        # Initialize Keboola Common Interface
        ci = CommonInterface()
        logger.info("Keboola CommonInterface initialized")

        # Get configuration
        parameters = ci.configuration.parameters

        # Get API key
        api_key = parameters.get('#FIDOO_API_KEY')
        if not api_key:
            logger.error("Missing required parameter: #FIDOO_API_KEY")
            raise ValueError("Missing #FIDOO_API_KEY")

        # Get objects to export
        objects = parameters.get('objects', ['user', 'card', 'transaction', 'expense'])
        if isinstance(objects, str):
            objects = [obj.strip() for obj in objects.split(',')]

        # Get output bucket
        output_bucket = parameters.get('output_bucket', 'out.c-fidoo')

        # Optional: API URL (for demo environment)
        api_url = parameters.get('api_url', None)

        # Include dependent objects (expense_item, travel_report_detail, travel_request_detail)
        include_dependent = parameters.get('include_dependent', True)

        # Set primary keys in manifests
        set_primary_keys = parameters.get('set_primary_keys', True)

        logger.info(f"Configuration loaded:")
        logger.info(f"  - Objects: {objects}")
        logger.info(f"  - Output bucket: {output_bucket}")
        logger.info(f"  - Include dependent: {include_dependent}")
        logger.info(f"  - Set primary keys: {set_primary_keys}")
        if api_url:
            logger.info(f"  - API URL: {api_url}")

        # Initialize Fidoo driver
        try:
            driver_kwargs = {'api_key': api_key}
            if api_url:
                driver_kwargs['base_url'] = api_url

            driver = FidooDriver(**driver_kwargs)
            logger.info("Fidoo driver initialized")

        except AuthenticationError as e:
            logger.error(f"Authentication failed: {e.message}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize driver: {e}")
            raise

        # Create DuckDB connection (in-memory or file-based)
        data_dir = ci.tables_out_path if hasattr(ci, 'tables_out_path') else '/tmp'
        duckdb_path = os.path.join(data_dir, 'fidoo_working.duckdb')
        conn = duckdb.connect(duckdb_path)
        logger.info(f"DuckDB initialized: {duckdb_path}")

        object_counts = {}
        total_records = 0

        try:
            # Phase 1: Export primary objects to DuckDB
            logger.info(f"\n{'='*50}")
            logger.info("PHASE 1: Exporting primary objects")
            logger.info(f"{'='*50}")

            for object_type in objects:
                if object_type not in PRIMARY_ENDPOINTS:
                    logger.warning(f"Unknown object type: {object_type}, skipping")
                    continue

                endpoint = PRIMARY_ENDPOINTS[object_type]
                logger.info(f"\n--- {object_type} ---")

                try:
                    count = export_primary_to_duckdb(conn, driver, object_type, endpoint)
                    object_counts[object_type] = count
                    total_records += count

                except Exception as e:
                    logger.error(f"Failed to export {object_type}: {e}")
                    object_counts[object_type] = 0

            # Phase 2: Export dependent objects
            if include_dependent:
                logger.info(f"\n{'='*50}")
                logger.info("PHASE 2: Exporting dependent objects")
                logger.info(f"{'='*50}")

                for object_type, config in DEPENDENT_ENDPOINTS.items():
                    # Only export if source table was requested
                    if config["source_table"] not in objects:
                        logger.info(f"Skipping {object_type} (source {config['source_table']} not in export list)")
                        continue

                    logger.info(f"\n--- {object_type} ---")

                    try:
                        count = export_dependent_to_duckdb(conn, driver, object_type, config)
                        object_counts[object_type] = count
                        total_records += count

                    except Exception as e:
                        logger.error(f"Failed to export {object_type}: {e}")
                        object_counts[object_type] = 0

            # Phase 3: Export from DuckDB to CSV
            logger.info(f"\n{'='*50}")
            logger.info("PHASE 3: Exporting to CSV")
            logger.info(f"{'='*50}")

            export_counts = export_duckdb_to_csv(conn, ci, output_bucket, set_primary_keys)

        finally:
            conn.close()
            driver.close()
            logger.info("Connections closed")

            # Clean up DuckDB file
            if os.path.exists(duckdb_path):
                os.remove(duckdb_path)
                logger.info(f"Cleaned up {duckdb_path}")

        # Update state
        update_state(ci, object_counts)

        # Summary
        logger.info(f"\n{'='*50}")
        logger.info("EXPORT SUMMARY")
        logger.info(f"{'='*50}")
        for obj, count in object_counts.items():
            logger.info(f"  {obj}: {count} records")
        logger.info(f"  TOTAL: {total_records} records")

        # Time profile
        logger.info(profiler.print_summary())

        logger.info("Component execution completed successfully")

        return 0

    except Exception as e:
        logger.exception(f"Component execution failed: {e}")
        exit(1)


if __name__ == '__main__':
    main()
