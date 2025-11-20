"""
Example: Get cards for a user

Demonstrates card querying with user-specific filtering.
"""

import sys
import os

# Add parent directory to path for local imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fidoo import FidooDriver


def main():
    """Get cards for a specific user"""

    # Initialize client
    client = FidooDriver.from_env()

    try:
        # Example: You would get this from your application
        user_id = "YOUR_USER_ID_HERE"

        if user_id == "YOUR_USER_ID_HERE":
            print("Error: Set user_id in the script before running")
            return

        print(f"Fetching cards for user {user_id}...")

        # Get cards
        # Note: The Fidoo API expects userId in the request body
        cards = client.read("card/get-cards", limit=100)

        print(f"\nFound {len(cards)} cards:")
        print("-" * 60)

        for card in cards:
            card_id = card.get("cardId", "N/A")
            embossed_name = card.get("embossedName", "N/A")
            state = card.get("state", "N/A")
            card_type = card.get("type", "N/A")
            available_balance = card.get("availableBalance", 0)
            currency = "CZK"  # Fidoo uses CZK

            print(f"  Card ID: {card_id}")
            print(f"    Name: {embossed_name}")
            print(f"    State: {state}")
            print(f"    Type: {card_type}")
            print(f"    Available Balance: {available_balance} {currency}")
            print()

    except Exception as e:
        print(f"Error: {e}")
        print(f"Details: {getattr(e, 'details', {})}")

    finally:
        client.close()


if __name__ == "__main__":
    main()
