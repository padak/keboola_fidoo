#!/usr/bin/env python3
"""
Test reading users from Fidoo API.
"""

import os
import sys
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from fidoo_driver import Fidoo8Driver, AuthenticationError, ObjectNotFoundError

# Load .env file
load_dotenv()

def main():
    api_key = os.getenv('FIDOO_API') or os.getenv('FIDOO_API_KEY')
    base_url = os.getenv('FIDOO_BASE_URL') or os.getenv('FIDOO_API_URL')

    if not api_key:
        print("ERROR: Set FIDOO_API or FIDOO_API_KEY in .env file")
        sys.exit(1)

    print("Fetching users from Fidoo...\n")

    try:
        driver = Fidoo8Driver(api_key=api_key, base_url=base_url)

        # Read first 10 users
        users = driver.read("User", limit=10)

        print(f"Found {len(users)} users:\n")

        for i, user in enumerate(users, 1):
            print(f"{i}. {user.get('firstName', '')} {user.get('lastName', '')}")
            print(f"   Email: {user.get('email', 'N/A')}")
            print(f"   State: {user.get('userState', 'N/A')}")
            print(f"   ID: {user.get('id', 'N/A')}")
            print()

        # Show raw data for first user
        if users:
            print("\nRaw data (first user):")
            print(json.dumps(users[0], indent=2, default=str))

        driver.close()

    except ObjectNotFoundError as e:
        print(f"No users found: {e.message}")
    except AuthenticationError as e:
        print(f"Authentication failed: {e.message}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
