#!/usr/bin/env python3
"""
Test exporting Fidoo data to CSV files.
"""

import os
import sys
import csv
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from fidoo_driver import FidooDriver, AuthenticationError

# Load .env file
load_dotenv()

def flatten_value(value):
    """Flatten nested objects to JSON string"""
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    return str(value) if value is not None else ""

def export_object(driver, endpoint, output_file):
    """Export object to CSV file"""
    print(f"Exporting {endpoint} to {output_file}...")

    # Fetch all records
    all_records = []
    for batch in driver.read_batched(endpoint, batch_size=100):
        all_records.extend(batch)
        print(f"  Fetched {len(all_records)} records...")

    if not all_records:
        print(f"  No records found")
        return 0

    # Get columns from first record
    columns = list(all_records[0].keys())

    # Write to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()

        for record in all_records:
            flat_record = {k: flatten_value(v) for k, v in record.items()}
            writer.writerow(flat_record)

    print(f"  Exported {len(all_records)} records to {output_file}")
    return len(all_records)

def main():
    api_key = os.getenv('FIDOO_API') or os.getenv('FIDOO_API_KEY')
    base_url = os.getenv('FIDOO_BASE_URL') or os.getenv('FIDOO_API_URL')

    if not api_key:
        print("ERROR: Set FIDOO_API or FIDOO_API_KEY in .env file")
        sys.exit(1)

    # Create output directory
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    os.makedirs(output_dir, exist_ok=True)

    print(f"Exporting Fidoo data to {output_dir}\n")

    try:
        driver = FidooDriver(api_key=api_key, base_url=base_url)

        # Export users
        export_object(
            driver,
            "user/get-users",
            os.path.join(output_dir, "users.csv")
        )

        # Export cards
        export_object(
            driver,
            "card/get-cards",
            os.path.join(output_dir, "cards.csv")
        )

        # Export transactions
        export_object(
            driver,
            "transaction/get-card-transactions",
            os.path.join(output_dir, "transactions.csv")
        )

        driver.close()
        print("\nExport completed!")

    except AuthenticationError as e:
        print(f"Authentication failed: {e.message}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
