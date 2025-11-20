#!/usr/bin/env python3
"""
Test reading all available object types from Fidoo API.
Shows count of records for each object type.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from fidoo_driver import Fidoo8Driver, AuthenticationError

# Load .env file
load_dotenv()

# Object names (new driver uses these directly)
OBJECTS = [
    "User",
    "Card",
    "Transaction",
    "CashTransaction",
    "Expense",
    "TravelReport",
    "CostCenter",
    "Project",
]

def main():
    api_key = os.getenv('FIDOO_API') or os.getenv('FIDOO_API_KEY')
    base_url = os.getenv('FIDOO_BASE_URL') or os.getenv('FIDOO_API_URL')

    if not api_key:
        print("ERROR: Set FIDOO_API or FIDOO_API_KEY in .env file")
        sys.exit(1)

    print("Reading all object types from Fidoo...\n")
    print(f"{'Object':<20} {'Count':<10} {'Status'}")
    print("-" * 50)

    try:
        driver = Fidoo8Driver(api_key=api_key, base_url=base_url)

        total = 0
        for obj_name in OBJECTS:
            try:
                records = driver.read(obj_name, limit=100)
                count = len(records)
                total += count
                print(f"{obj_name:<20} {count:<10} OK")
            except Exception as e:
                print(f"{obj_name:<20} {'?':<10} {str(e)[:30]}")

        print("-" * 50)
        print(f"{'TOTAL':<20} {total:<10}")

        driver.close()

    except AuthenticationError as e:
        print(f"Authentication failed: {e.message}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
