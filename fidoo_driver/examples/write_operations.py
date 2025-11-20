"""
Example: Write Operations

Demonstrates creating, updating, and deleting records:
- Creating new users
- Updating existing records
- Handling write operation errors
- Best practices for data modifications
"""

import sys
import os
from datetime import datetime

# Add parent directory to path for local imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fidoo import FidooDriver
from fidoo.exceptions import ValidationError, AuthenticationError


def create_user_example(client):
    """Example: Create a new user"""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: CREATE NEW USER")
    print("=" * 70)

    try:
        # Create new user data
        new_user = {
            "firstName": "John",
            "lastName": "Doe",
            "email": f"john.doe.{datetime.now().timestamp()}@example.com",
            "active": True,
            "usesApplication": True,
            "language": "en",
            "position": "Software Engineer"
        }

        print(f"\nCreating user with data:")
        for key, value in new_user.items():
            print(f"  {key}: {value}")

        # Create user
        result = client.create("user", new_user)

        print(f"\n✓ User created successfully!")
        print(f"  User ID: {result.get('userId', 'N/A')}")
        print(f"  Name: {result.get('firstName')} {result.get('lastName')}")
        print(f"  Email: {result.get('email')}")

        return result.get('userId')

    except ValidationError as e:
        print(f"\n✗ Validation Error: {e.message}")
        print(f"  Details: {e.details}")
        return None

    except Exception as e:
        print(f"\n✗ Error: {e}")
        return None


def update_expense_example(client):
    """Example: Update an existing expense"""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: UPDATE EXPENSE")
    print("=" * 70)

    try:
        # First, get an expense to update
        print("\nFetching existing expenses...")
        expenses = client.read("expense/get-expenses", limit=1)

        if not expenses:
            print("  No expenses found to update (skipping example)")
            return

        expense = expenses[0]
        expense_id = expense.get('expenseId', expense.get('id'))

        print(f"\nFound expense: {expense_id}")
        print(f"  Current name: {expense.get('name', 'N/A')}")

        # Update expense
        update_data = {
            "name": f"Updated Expense - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "externalReferenceId": f"EXP-{int(datetime.now().timestamp())}"
        }

        print(f"\nUpdating with:")
        for key, value in update_data.items():
            print(f"  {key}: {value}")

        result = client.update("expense", expense_id, update_data)

        print(f"\n✓ Expense updated successfully!")
        print(f"  Expense ID: {result.get('expenseId', 'N/A')}")
        print(f"  New name: {result.get('name', 'N/A')}")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        if hasattr(e, 'details'):
            print(f"  Details: {e.details}")


def batch_operations_example(client):
    """Example: Batch operations (load multiple cards)"""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: BATCH OPERATIONS")
    print("=" * 70)

    try:
        # First, get some cards
        print("\nFetching cards for batch operations...")
        cards = client.read("card/get-cards", limit=2)

        if len(cards) < 2:
            print(f"  Not enough cards found (found {len(cards)}, need 2+) - skipping")
            return

        print(f"\n✓ Found {len(cards)} cards")

        # Prepare batch load operations
        batch_operations = []
        for i, card in enumerate(cards):
            card_id = card.get('cardId')
            if card_id:
                operation = {
                    "cardId": card_id,
                    "amount": 100.00 + (i * 50),  # Different amounts
                    "message": f"Batch load #{i + 1}",
                    "customerProcessId": f"BATCH-{int(datetime.now().timestamp())}-{i}"
                }
                batch_operations.append(operation)
                print(f"  Card {i + 1}: Load {operation['amount']} CZK")

        print(f"\nPrepared batch operations for {len(batch_operations)} cards")
        print("Note: Actual batch operation would be executed via call_endpoint()")

    except Exception as e:
        print(f"\n✗ Error: {e}")


def error_handling_example(client):
    """Example: Handle errors during write operations"""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: ERROR HANDLING FOR WRITE OPERATIONS")
    print("=" * 70)

    try:
        # Try to create user with invalid data (missing required fields)
        print("\nAttempting to create user with missing required fields...")

        invalid_user = {
            "firstName": "Jane"
            # Missing: lastName (usually required)
        }

        result = client.create("user", invalid_user)
        print(f"  Created: {result}")

    except ValidationError as e:
        print(f"\n✓ Caught validation error (as expected):")
        print(f"  Error: {e.message}")
        print(f"  Details: {e.details}")

    except AuthenticationError as e:
        print(f"\n✓ Caught authentication error:")
        print(f"  Error: {e.message}")
        print(f"  Solution: {e.details}")

    except Exception as e:
        print(f"\n✓ Caught unexpected error:")
        print(f"  Type: {type(e).__name__}")
        print(f"  Error: {e}")


def main():
    """Run all write operation examples"""

    print("\n" + "=" * 70)
    print("FIDOO DRIVER - WRITE OPERATIONS EXAMPLE")
    print("=" * 70)

    client = FidooDriver.from_env()

    try:
        # Get driver capabilities
        caps = client.get_capabilities()

        if not caps.write:
            print("\n✗ Driver does not support write operations")
            return 1

        print("\n✓ Driver supports write operations")

        # Run examples
        create_user_example(client)
        update_expense_example(client)
        batch_operations_example(client)
        error_handling_example(client)

        print("\n" + "=" * 70)
        print("✓ WRITE OPERATIONS EXAMPLES COMPLETED")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        return 1

    finally:
        client.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
