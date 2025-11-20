"""
Example: Comprehensive error handling

Demonstrates how to handle different error types from the Fidoo API.
"""

import sys
import os

# Add parent directory to path for local imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fidoo import FidooDriver
from fidoo.exceptions import (
    AuthenticationError,
    RateLimitError,
    ObjectNotFoundError,
    ConnectionError,
    ValidationError
)


def main():
    """Demonstrate error handling"""

    try:
        # Initialize client
        client = FidooDriver.from_env()

    except AuthenticationError as e:
        print("Authentication Error:")
        print(f"  Message: {e.message}")
        print(f"  Details: {e.details}")
        print("\nSolution: Check your FIDOO_API_KEY environment variable")
        return

    try:
        print("Attempting to read users...")

        # This will succeed if authentication is valid
        users = client.read("user/get-users", limit=10)
        print(f"Success! Found {len(users)} users")

    except AuthenticationError as e:
        print("Authentication Error - API key is invalid or expired")
        print(f"  {e.message}")

    except RateLimitError as e:
        print("Rate Limit Exceeded - Hit daily quota (6,000 requests/day)")
        print(f"  Message: {e.message}")
        print(f"  Retry after: {e.details.get('retry_after')} seconds")
        print("  Solution: Wait until next day or contact Fidoo support")

    except ConnectionError as e:
        print("Connection Error - Cannot reach Fidoo API")
        print(f"  Message: {e.message}")
        print(f"  Details: {e.details}")
        print("  Solution: Check your internet connection and base_url")

    except ObjectNotFoundError as e:
        print("Object Not Found - The requested object doesn't exist")
        print(f"  Message: {e.message}")
        print(f"  Available objects: {e.details.get('available')}")

    except ValidationError as e:
        print("Validation Error - Invalid request parameters")
        print(f"  Message: {e.message}")
        print(f"  Details: {e.details}")

    except Exception as e:
        print(f"Unexpected error: {type(e).__name__}")
        print(f"  Message: {e}")

    finally:
        if 'client' in locals():
            client.close()
            print("\nClient closed")


if __name__ == "__main__":
    main()
