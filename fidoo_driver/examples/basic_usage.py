"""
Example: Basic Usage Patterns

Demonstrates fundamental driver operations:
- Initialization
- Discovery (list available objects)
- Schema retrieval (understand endpoints)
- Simple queries
- Resource cleanup
"""

import sys
import os

# Add parent directory to path for local imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fidoo import FidooDriver


def main():
    """Demonstrate basic driver usage"""

    print("=" * 70)
    print("FIDOO DRIVER - BASIC USAGE EXAMPLE")
    print("=" * 70)

    # Step 1: Initialize driver from environment
    print("\n1. Initializing driver from environment variables...")
    client = FidooDriver.from_env()
    print("   ✓ Driver initialized successfully")

    try:
        # Step 2: Get driver capabilities
        print("\n2. Checking driver capabilities...")
        caps = client.get_capabilities()
        print(f"   ✓ Read operations: {caps.read}")
        print(f"   ✓ Write operations: {caps.write}")
        print(f"   ✓ Update operations: {caps.update}")
        print(f"   ✓ Delete operations: {caps.delete}")
        print(f"   ✓ Max page size: {caps.max_page_size}")

        # Step 3: List available objects
        print("\n3. Discovering available objects...")
        objects = client.list_objects()
        print(f"   ✓ Found {len(objects)} object types:")
        for obj in objects:
            print(f"     - {obj}")

        # Step 4: Get schema for specific object
        print("\n4. Getting schema for 'user' object...")
        fields = client.get_fields("user")
        print(f"   ✓ Available endpoints: {fields.get('endpoints', [])}")
        print(f"   ✓ Available fields:")
        for field_name, field_info in fields.get("fields", {}).items():
            field_type = field_info.get("type", "unknown")
            required = field_info.get("required", False)
            required_str = "[REQUIRED]" if required else "[optional]"
            print(f"     - {field_name}: {field_type} {required_str}")

        # Step 5: Simple read operation
        print("\n5. Reading user data...")
        users = client.read("user/get-users", limit=5)
        print(f"   ✓ Retrieved {len(users)} users")
        if users:
            print(f"   ✓ Sample user:")
            first_user = users[0]
            print(f"     - ID: {first_user.get('userId', 'N/A')}")
            print(f"     - Name: {first_user.get('firstName', 'N/A')} {first_user.get('lastName', 'N/A')}")
            print(f"     - Email: {first_user.get('email', 'N/A')}")

        # Step 6: Get rate limit status
        print("\n6. Checking rate limit status...")
        status = client.get_rate_limit_status()
        print(f"   ✓ Daily limit: {status.get('limit')} requests")
        print(f"   ✓ Period: {status.get('period')}")

        print("\n" + "=" * 70)
        print("✓ BASIC USAGE EXAMPLE COMPLETED SUCCESSFULLY")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        if hasattr(e, 'details'):
            print(f"  Details: {e.details}")
        return 1

    finally:
        print("\n7. Cleaning up...")
        client.close()
        print("   ✓ Driver closed successfully")

    return 0


if __name__ == "__main__":
    sys.exit(main())
