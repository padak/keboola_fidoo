#!/usr/bin/env python3
"""
Test reading all available object types from Fidoo API.
Shows count of records for each object type.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from fidoo_driver import Fidoo7Driver, AuthenticationError

# Load .env file
load_dotenv()

# Endpoint mapping
ENDPOINTS = {
    "user": "user/get-users",
    "card": "card/get-cards",
    "transaction": "transaction/get-card-transactions",
    "cash_transaction": "transaction/get-cash-transactions",
    "expense": "expense/get-expenses",
    "travel_report": "travel/get-travel-reports",
    "account": "account/get-accounts",
    "cost_center": "settings/get-cost-centers",
    "project": "settings/get-projects",
}

def main():
    api_key = os.getenv('FIDOO_API') or os.getenv('FIDOO_API_KEY')

    if not api_key:
        print("ERROR: Set FIDOO_API or FIDOO_API_KEY in .env file")
        sys.exit(1)

    print("Reading all object types from Fidoo...\n")
    print(f"{'Object':<20} {'Count':<10} {'Status'}")
    print("-" * 50)

    try:
        driver = Fidoo7Driver(api_key=api_key)

        total = 0
        for obj_name, endpoint in ENDPOINTS.items():
            try:
                records = driver.read(endpoint, limit=100)
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
