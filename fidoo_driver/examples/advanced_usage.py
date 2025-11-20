"""
Example: Advanced Usage Patterns

Demonstrates advanced driver capabilities:
- Complex filtering and searching
- Combining multiple operations
- Performance optimization
- Complex error recovery
- Data transformation pipelines
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path for local imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fidoo import FidooDriver
from fidoo.exceptions import RateLimitError, ConnectionError


def advanced_filtering_example(client):
    """Example: Advanced filtering and searching"""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: ADVANCED FILTERING")
    print("=" * 70)

    try:
        print("\nScenario: Get all expenses from the last 30 days")

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        print(f"  Date range: {start_date.date()} to {end_date.date()}")

        # Query expenses
        print(f"\nFetching expenses...")
        expenses = client.read("expense/get-expenses", limit=100)

        print(f"✓ Retrieved {len(expenses)} expenses")

        # Filter and analyze
        recent_expenses = [
            e for e in expenses
            if datetime.fromisoformat(e.get('createdDate', '')) >= start_date
        ] if any('createdDate' in e for e in expenses) else expenses

        # Calculate totals
        total_amount = sum(
            float(e.get('originalAmount', 0))
            for e in recent_expenses
            if e.get('originalAmount')
        )

        print(f"\nAnalysis:")
        print(f"  Total expenses in period: {len(recent_expenses)}")
        print(f"  Total amount: {total_amount} {e.get('currency', 'CZK')}")

        # Group by state
        by_state = {}
        for expense in recent_expenses:
            state = expense.get('state', 'unknown')
            by_state[state] = by_state.get(state, 0) + 1

        print(f"\nExpenses by state:")
        for state, count in sorted(by_state.items()):
            print(f"  {state}: {count}")

    except Exception as e:
        print(f"\n✗ Error: {e}")


def pipeline_processing_example(client):
    """Example: Data transformation pipeline"""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: DATA TRANSFORMATION PIPELINE")
    print("=" * 70)

    try:
        print("\nScenario: Process users and enrich with card information")

        # Step 1: Get users
        print("\nStep 1: Fetching users...")
        users = client.read("user/get-users", limit=5)
        print(f"✓ Retrieved {len(users)} users")

        # Step 2: Enrich with card data
        print("\nStep 2: Enriching with card data...")
        enriched_users = []

        for user in users:
            user_id = user.get('userId')

            # Get cards for user
            cards = client.read("card/get-cards", limit=10)

            # Calculate user's card statistics
            user_cards = [c for c in cards if user_id in c.get('connectedUserIds', [])]

            enriched_user = {
                **user,
                "card_count": len(user_cards),
                "total_balance": sum(
                    float(c.get('availableBalance', 0))
                    for c in user_cards
                ),
                "cards": user_cards
            }

            enriched_users.append(enriched_user)

        # Step 3: Display results
        print(f"\nStep 3: Displaying enriched data...")
        for user in enriched_users:
            print(f"\n  {user['firstName']} {user['lastName']}")
            print(f"    Email: {user['email']}")
            print(f"    Cards: {user['card_count']}")
            print(f"    Total Balance: {user['total_balance']} CZK")

        print(f"\n✓ Pipeline processing complete")

    except Exception as e:
        print(f"\n✗ Error: {e}")


def resilient_query_example(client):
    """Example: Resilient querying with error recovery"""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: RESILIENT QUERYING WITH ERROR RECOVERY")
    print("=" * 70)

    def query_with_retry(endpoint, max_attempts=3):
        """Query with automatic retry on transient errors"""
        for attempt in range(max_attempts):
            try:
                print(f"  Attempt {attempt + 1}/{max_attempts}...", end="")
                data = client.read(endpoint, limit=100)
                print(f" ✓ ({len(data)} records)")
                return data

            except RateLimitError as e:
                wait_time = e.details.get('retry_after', 60)
                print(f" Rate limited")
                if attempt < max_attempts - 1:
                    print(f"    Waiting {wait_time}s before retry...")
                    # In real scenario, would call time.sleep(wait_time)
                    # For demo, just continue
                else:
                    print(f"    Max retries exceeded")
                    raise

            except ConnectionError as e:
                print(f" Connection error")
                if attempt < max_attempts - 1:
                    print(f"    Retrying...")
                else:
                    print(f"    Max retries exceeded")
                    raise

            except Exception as e:
                print(f" Unexpected error: {e}")
                raise

        return []

    try:
        print("\nQuerying transactions with resilience...")
        transactions = query_with_retry("transaction/get-card-transactions")

        print(f"\n✓ Retrieved {len(transactions)} transactions")

    except Exception as e:
        print(f"\n✗ Failed after retries: {e}")


def performance_optimization_example(client):
    """Example: Performance optimization techniques"""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: PERFORMANCE OPTIMIZATION")
    print("=" * 70)

    try:
        print("\nScenario: Process large dataset efficiently")

        # Technique 1: Batch processing instead of loading all at once
        print("\n1. Using read_batched() for memory efficiency...")
        total_users = 0
        batch_count = 0

        for batch in client.read_batched("user/get-users", batch_size=100):
            batch_count += 1
            total_users += len(batch)
            print(f"   Batch {batch_count}: {len(batch)} users (total: {total_users})")

        print(f"✓ Processed {total_users} users in {batch_count} batches")

        # Technique 2: Adjust limits based on data volume
        print("\n2. Adaptive page sizing...")

        # Start with conservative size
        page_size = 50
        sample = client.read("transaction/get-card-transactions", limit=page_size)
        print(f"   Sample fetch: {len(sample)} records")

        if len(sample) > 0:
            # If we got results, try larger size
            page_size = 100
            print(f"   Increasing page size to {page_size}")

        # Technique 3: Minimize API calls
        print("\n3. Caching schema information...")

        # Get schema once
        user_schema = client.get_fields("user")
        expense_schema = client.get_fields("expense")

        print(f"   Cached schemas for 2 objects")
        print(f"   User fields: {len(user_schema.get('fields', {}))}")
        print(f"   Expense fields: {len(expense_schema.get('fields', {}))}")

        print(f"\n✓ Performance optimization examples complete")

    except Exception as e:
        print(f"\n✗ Error: {e}")


def multi_operation_workflow_example(client):
    """Example: Complex multi-step workflow"""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: MULTI-OPERATION WORKFLOW")
    print("=" * 70)

    try:
        print("\nScenario: Complete user onboarding workflow")

        # Step 1: Verify user doesn't exist
        print("\nStep 1: Checking if user exists...")
        existing_users = client.read("user/get-users", limit=1000)
        test_email = f"workflow-test-{int(datetime.now().timestamp())}@example.com"
        email_exists = any(u.get('email') == test_email for u in existing_users)
        print(f"✓ Email exists: {email_exists}")

        # Step 2: Discover available options
        print("\nStep 2: Discovering available configuration...")
        try:
            cost_centers = client.read("settings/get-cost-centers", limit=10)
            projects = client.read("settings/get-projects", limit=10)
            print(f"✓ Found {len(cost_centers)} cost centers")
            print(f"✓ Found {len(projects)} projects")
        except Exception as e:
            print(f"  Note: Could not fetch settings: {e}")

        # Step 3: Prepare user creation
        print("\nStep 3: Preparing user creation...")
        new_user_data = {
            "firstName": "Workflow",
            "lastName": "Test",
            "email": test_email,
            "active": True,
            "usesApplication": True,
            "language": "en"
        }
        print("✓ User data prepared")

        # Step 4: Create user (would happen here in real scenario)
        print("\nStep 4: User creation (simulated)...")
        print(f"  Would create user: {new_user_data['firstName']} {new_user_data['lastName']}")
        print(f"  Email: {new_user_data['email']}")

        # Step 5: Verify creation
        print("\nStep 5: Workflow complete")
        print("✓ Multi-operation workflow demonstrated successfully")

    except Exception as e:
        print(f"\n✗ Error in workflow: {e}")


def main():
    """Run all advanced usage examples"""

    print("\n" + "=" * 70)
    print("FIDOO DRIVER - ADVANCED USAGE EXAMPLES")
    print("=" * 70)

    client = FidooDriver.from_env()

    try:
        advanced_filtering_example(client)
        pipeline_processing_example(client)
        resilient_query_example(client)
        performance_optimization_example(client)
        multi_operation_workflow_example(client)

        print("\n" + "=" * 70)
        print("✓ ADVANCED USAGE EXAMPLES COMPLETED")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        return 1

    finally:
        client.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
