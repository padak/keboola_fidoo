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
from datetime import datetime

try:
    from keboola.component import CommonInterface
    from keboola.component.dao import BaseType, ColumnDefinition
except ImportError:
    # For local testing
    pass

from fidoo_driver import (
    Fidoo7Driver,
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


# Endpoint mapping for each object type
OBJECT_ENDPOINTS = {
    "user": "user/get-users",
    "card": "card/get-cards",
    "transaction": "transaction/get-card-transactions",
    "cash_transaction": "transaction/get-cash-transactions",
    "mvc_transaction": "transaction/get-mvc-transactions",
    "expense": "expense/get-expenses",
    "travel_report": "travel/get-travel-reports",
    "travel_request": "travel/get-travel-requests",
    "personal_billing": "billing/get-personal-billings",
    "account": "account/get-accounts",
    "cost_center": "settings/get-cost-centers",
    "project": "settings/get-projects",
    "account_assignment": "settings/get-account-assignments",
    "accounting_category": "settings/get-accounting-categories",
    "vat_breakdown": "settings/get-vat-breakdowns",
    "vehicle": "settings/get-vehicles",
    "receipt": "receipt/get-receipts",
}


def flatten_json(obj):
    """Flatten nested JSON objects to string representation"""
    if isinstance(obj, dict):
        return json.dumps(obj)
    elif isinstance(obj, list):
        return json.dumps(obj)
    return str(obj) if obj is not None else ""


def export_fidoo_object(ci, driver, object_type, output_bucket):
    """
    Export a single object type from Fidoo and write to Keboola output table

    Args:
        ci: CommonInterface instance
        driver: Fidoo7Driver instance
        object_type: Type of object to export (e.g., "user", "card")
        output_bucket: Destination bucket in Keboola Storage

    Returns:
        Number of records exported
    """
    if object_type not in OBJECT_ENDPOINTS:
        logger.error(f"Unknown object type: {object_type}")
        raise ValueError(f"Unknown object type: {object_type}. Available: {list(OBJECT_ENDPOINTS.keys())}")

    endpoint = OBJECT_ENDPOINTS[object_type]
    logger.info(f"Exporting {object_type} from endpoint: {endpoint}")

    # Fetch all records using batched reading
    all_records = []
    try:
        for batch in driver.read_batched(endpoint, batch_size=100):
            all_records.extend(batch)
            logger.info(f"  Fetched batch: {len(batch)} records (total: {len(all_records)})")
    except ObjectNotFoundError as e:
        logger.warning(f"Object {object_type} not found or empty: {e.message}")
        return 0
    except RateLimitError as e:
        logger.error(f"Rate limit exceeded: {e.message}")
        raise
    except TimeoutError as e:
        logger.error(f"Request timed out: {e.message}")
        raise

    if not all_records:
        logger.warning(f"No records found for {object_type}")
        return 0

    logger.info(f"Total {object_type} records: {len(all_records)}")

    # Determine columns from first record
    if all_records:
        columns = list(all_records[0].keys())
    else:
        columns = []

    # Create output table definition
    table_name = f"{object_type}.csv"
    destination = f"{output_bucket}.{object_type}"

    out_table = ci.create_out_table_definition(
        name=table_name,
        destination=destination,
        incremental=False,
        has_header=True,
    )

    logger.info(f"Writing {len(all_records)} records to {out_table.full_path}")

    # Write records to CSV
    with open(out_table.full_path, 'w+', newline='', encoding='utf-8') as f:
        if columns:
            writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
            writer.writeheader()

            for record in all_records:
                # Flatten any nested objects
                flat_record = {}
                for key, value in record.items():
                    if isinstance(value, (dict, list)):
                        flat_record[key] = flatten_json(value)
                    else:
                        flat_record[key] = value if value is not None else ""
                writer.writerow(flat_record)

    logger.info(f"Wrote {len(all_records)} {object_type} records to CSV")

    # Write manifest
    ci.write_manifest(out_table)
    logger.info(f"Manifest written to {out_table.full_path}.manifest")

    return len(all_records)


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

        logger.info(f"Configuration loaded:")
        logger.info(f"  - Objects: {objects}")
        logger.info(f"  - Output bucket: {output_bucket}")
        if api_url:
            logger.info(f"  - API URL: {api_url}")

        # Initialize Fidoo driver
        try:
            driver_kwargs = {'api_key': api_key}
            if api_url:
                driver_kwargs['base_url'] = api_url

            driver = Fidoo7Driver(**driver_kwargs)
            logger.info("Fidoo driver initialized")

        except AuthenticationError as e:
            logger.error(f"Authentication failed: {e.message}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize driver: {e}")
            raise

        # Export each object type
        object_counts = {}
        total_records = 0

        try:
            for object_type in objects:
                logger.info(f"\n{'='*50}")
                logger.info(f"Exporting: {object_type}")
                logger.info(f"{'='*50}")

                try:
                    count = export_fidoo_object(ci, driver, object_type, output_bucket)
                    object_counts[object_type] = count
                    total_records += count
                    logger.info(f"Exported {count} {object_type} records")

                except Exception as e:
                    logger.error(f"Failed to export {object_type}: {e}")
                    object_counts[object_type] = 0
                    # Continue with other objects

        finally:
            driver.close()
            logger.info("Driver connection closed")

        # Update state
        update_state(ci, object_counts)

        # Summary
        logger.info(f"\n{'='*50}")
        logger.info("EXPORT SUMMARY")
        logger.info(f"{'='*50}")
        for obj, count in object_counts.items():
            logger.info(f"  {obj}: {count} records")
        logger.info(f"  TOTAL: {total_records} records")
        logger.info("Component execution completed successfully")

        return 0

    except Exception as e:
        logger.exception(f"Component execution failed: {e}")
        exit(1)


if __name__ == '__main__':
    main()
