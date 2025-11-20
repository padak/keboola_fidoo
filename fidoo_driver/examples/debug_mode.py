"""
Example: Using debug mode

Demonstrates how to enable debug logging for troubleshooting.
"""

import sys
import os

# Add parent directory to path for local imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fidoo import FidooDriver


def main():
    """Enable debug mode to see all API calls"""

    print("Initializing FidooDriver with debug mode enabled...\n")

    # Initialize with debug=True
    client = FidooDriver.from_env(debug=True)

    try:
        print("Making API calls with debug output:\n")
        print("=" * 60)

        # This will print debug information showing:
        # - HTTP method and URL
        # - Request payloads
        # - Retry attempts
        # - Rate limit warnings
        users = client.read("user/get-users", limit=10)

        print("=" * 60)
        print(f"\nGot {len(users)} users")

    except Exception as e:
        print(f"\nError: {e}")

    finally:
        client.close()


if __name__ == "__main__":
    main()
