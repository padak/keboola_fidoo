"""
Example: Batch processing with pagination

Demonstrates memory-efficient processing of large datasets.
"""

import sys
import os

# Add parent directory to path for local imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fidoo import FidooDriver


def main():
    """Process large datasets in batches"""

    # Initialize client
    client = FidooDriver.from_env()

    try:
        print("Processing users in batches...")
        print("-" * 60)

        total_processed = 0
        batch_count = 0

        # Use read_batched for memory efficiency
        for batch in client.read_batched("user/get-users", batch_size=100):
            batch_count += 1
            print(f"\nBatch {batch_count}: Processing {len(batch)} records...")

            # Process each record in batch
            for user in batch:
                # Do something with user
                first_name = user.get("firstName", "")
                last_name = user.get("lastName", "")

                # Example processing logic
                process_user(user)

            total_processed += len(batch)
            print(f"  Total processed so far: {total_processed}")

        print(f"\n{'=' * 60}")
        print(f"Complete! Processed {total_processed} users in {batch_count} batches")

    except Exception as e:
        print(f"Error: {e}")
        print(f"Details: {getattr(e, 'details', {})}")

    finally:
        client.close()


def process_user(user):
    """Process a single user record"""
    user_id = user.get("userId")
    first_name = user.get("firstName", "")
    last_name = user.get("lastName", "")

    # Your processing logic here
    # Example: update database, send notifications, etc.
    pass


if __name__ == "__main__":
    main()
