#!/usr/bin/env python3
"""
Test Fidoo API connection and list available objects.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from fidoo_driver import Fidoo7Driver, AuthenticationError

# Load .env file
load_dotenv()

def main():
    # Get API key from environment (note: .env uses FIDOO_API)
    api_key = os.getenv('FIDOO_API') or os.getenv('FIDOO_API_KEY')

    if not api_key:
        print("ERROR: Set FIDOO_API or FIDOO_API_KEY in .env file")
        sys.exit(1)

    print("Connecting to Fidoo API...")

    try:
        driver = Fidoo7Driver(api_key=api_key)
        print("Connected successfully!\n")

        # List available objects
        objects = driver.list_objects()
        print(f"Available objects ({len(objects)}):")
        for obj in objects:
            print(f"  - {obj}")

        # Show capabilities
        caps = driver.get_capabilities()
        print(f"\nDriver capabilities:")
        print(f"  - Read: {caps.read}")
        print(f"  - Write: {caps.write}")
        print(f"  - Update: {caps.update}")
        print(f"  - Delete: {caps.delete}")
        print(f"  - Max page size: {caps.max_page_size}")

        driver.close()

    except AuthenticationError as e:
        print(f"Authentication failed: {e.message}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
