"""
Example: List all users from Fidoo

Demonstrates basic user querying with pagination.
"""

import sys
import os

# Add parent directory to path for local imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fidoo import FidooDriver


def main():
    """List all users from Fidoo"""

    # Initialize client from environment
    client = FidooDriver.from_env()

    try:
        print("Fetching all users...")

        # Query users
        users = client.read("user/get-users", limit=100)

        print(f"\nFound {len(users)} users:")
        print("-" * 60)

        for user in users:
            first_name = user.get("firstName", "N/A")
            last_name = user.get("lastName", "N/A")
            email = user.get("email", "N/A")
            user_id = user.get("userId", "N/A")

            print(f"  {first_name} {last_name}")
            print(f"    Email: {email}")
            print(f"    ID: {user_id}")
            print()

    except Exception as e:
        print(f"Error: {e}")
        print(f"Details: {getattr(e, 'details', {})}")

    finally:
        client.close()


if __name__ == "__main__":
    main()
