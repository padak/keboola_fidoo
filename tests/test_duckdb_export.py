#!/usr/bin/env python3
"""
Test DuckDB-based export functionality.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import duckdb
from dotenv import load_dotenv
from fidoo_driver import FidooDriver, AuthenticationError

# Load .env file
load_dotenv()

# Import functions from main
from main import (
    export_primary_to_duckdb,
    export_dependent_to_duckdb,
    PRIMARY_ENDPOINTS,
    DEPENDENT_ENDPOINTS,
    flatten_record,
)


def main():
    api_key = os.getenv('FIDOO_API') or os.getenv('FIDOO_API_KEY')
    base_url = os.getenv('FIDOO_BASE_URL') or os.getenv('FIDOO_API_URL')

    if not api_key:
        print("ERROR: Set FIDOO_API or FIDOO_API_KEY in .env file")
        sys.exit(1)

    print("Testing DuckDB export functionality...\n")

    try:
        driver = FidooDriver(api_key=api_key, base_url=base_url)

        # Create in-memory DuckDB
        conn = duckdb.connect(':memory:')

        # Test objects to export
        test_objects = ['expense', 'travel_report']

        print("=" * 50)
        print("PHASE 1: Primary objects")
        print("=" * 50)

        total = 0
        for obj_name in test_objects:
            if obj_name not in PRIMARY_ENDPOINTS:
                print(f"{obj_name}: SKIP (not in PRIMARY_ENDPOINTS)")
                continue

            endpoint = PRIMARY_ENDPOINTS[obj_name]
            try:
                count = export_primary_to_duckdb(conn, driver, obj_name, endpoint)
                total += count
                print(f"{obj_name}: {count} records")
            except Exception as e:
                print(f"{obj_name}: ERROR - {e}")

        print(f"\nPrimary total: {total}")

        print("\n" + "=" * 50)
        print("PHASE 2: Dependent objects")
        print("=" * 50)

        for obj_name, config in DEPENDENT_ENDPOINTS.items():
            # Only test if source was exported
            if config["source_table"] not in test_objects:
                print(f"{obj_name}: SKIP (source not exported)")
                continue

            try:
                count = export_dependent_to_duckdb(conn, driver, obj_name, config)
                total += count
                print(f"{obj_name}: {count} records")
            except Exception as e:
                print(f"{obj_name}: ERROR - {e}")

        print("\n" + "=" * 50)
        print("DuckDB Tables")
        print("=" * 50)

        tables = conn.execute("SHOW TABLES").fetchall()
        for table in tables:
            table_name = table[0]
            count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            print(f"{table_name}: {count} records")

        print("\n" + "=" * 50)
        print(f"TOTAL: {total} records")
        print("=" * 50)

        # Test CSV export
        print("\nTesting CSV export...")
        test_csv = "/tmp/test_expense.csv"
        conn.execute(f"COPY expense TO '{test_csv}' (HEADER, DELIMITER ',')")

        # Count lines in CSV
        with open(test_csv) as f:
            lines = len(f.readlines()) - 1  # minus header
        print(f"Exported {lines} records to {test_csv}")

        # Cleanup
        os.remove(test_csv)

        conn.close()
        driver.close()

        print("\n✅ Test completed successfully!")

    except AuthenticationError as e:
        print(f"Authentication failed: {e.message}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
