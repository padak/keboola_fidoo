# Fidoo Driver

Python API driver for the Fidoo Expense Management platform.

## Overview

Fidoo is a comprehensive expense management and corporate card platform. This driver provides programmatic access to:

- User management (create, activate, deactivate users)
- Card operations (get cards, load/unload funds, track balance)
- Transaction monitoring (cards, cash, MVC account transactions)
- Expense tracking and management
- Travel and billing reports
- Configuration management (cost centers, projects, VAT rates, vehicles)

**API Documentation:** https://www.fidoo.com/expense-management/integrace/api

## Installation

```bash
pip install fidoo-driver
```

Or from source:

```bash
git clone <repo>
cd fidoo
pip install -e .
```

## Quick Start

### Environment Setup

Set required environment variables:

```bash
export FIDOO_API_KEY="your_api_key_here"
# Optional:
export FIDOO_BASE_URL="https://api.fidoo.com/v2"  # Production (default)
export FIDOO_TIMEOUT="30"
export FIDOO_DEBUG="false"
```

### Basic Usage

```python
from fidoo import FidooDriver

# Initialize from environment variables
client = FidooDriver.from_env()

try:
    # List available objects
    objects = client.list_objects()
    print(f"Available objects: {objects}")

    # Get schema for an object
    fields = client.get_fields("user")
    print(f"User fields: {fields}")

    # Query data
    users = client.read("user/get-users", limit=10)
    print(f"Found {len(users)} users")

    # Get cards
    cards = client.read("card/get-cards", limit=50)
    print(f"Found {len(cards)} cards")

finally:
    client.close()
```

### Explicit Credentials

```python
from fidoo import FidooDriver

client = FidooDriver(
    api_key="your_api_key_here",
    base_url="https://api.fidoo.com/v2",
    timeout=30,
    debug=False
)

try:
    # Your code here
    pass
finally:
    client.close()
```

## Authentication

### Getting an API Key

1. Log in to Fidoo with Main Administrator role
2. Navigate to: Settings → Company → API Key Management
3. Generate a new API key
4. **Save immediately** - keys are only shown once
5. Choose permissions:
   - Read-only
   - Read/Write

### API Key Storage

Store your API key securely using environment variables:

```bash
# .env file (never commit to git!)
FIDOO_API_KEY=your_api_key_here
```

Load in your Python code:

```python
from fidoo import FidooDriver

client = FidooDriver.from_env()
```

## API Reference

### Core Methods

#### `list_objects() -> List[str]`

Discover available objects/endpoints.

```python
objects = client.list_objects()
# Returns: ['user', 'card', 'transaction', 'expense', 'travel', 'settings', ...]
```

#### `get_fields(object_name: str) -> Dict[str, Any]`

Get schema and available parameters for an object.

```python
fields = client.get_fields("card")
# Returns:
# {
#   "endpoints": ["get-cards", "load-card", "unload-card", ...],
#   "fields": {
#       "userId": {"type": "string", "required": True},
#       "cardId": {"type": "string", "required": False},
#       "amount": {"type": "number", "required": False},
#       "limit": {"type": "integer", "required": False, "default": 100, "max": 100},
#       ...
#   }
# }
```

#### `read(query: str, limit: int = 100, offset: str = None) -> List[Dict[str, Any]]`

Query data from an endpoint.

**Parameters:**
- `query` (str): Endpoint path (e.g., "user/get-users", "card/get-cards")
- `limit` (int): Records per request (default: 100, max: 100)
- `offset` (str): Pagination token (optional)

**Returns:** List of records

```python
# Get all users
users = client.read("user/get-users", limit=100)

# Get cards for a specific user
cards = client.read("card/get-cards", limit=50)

# Get transactions for a card
transactions = client.read(
    "transaction/get-card-transactions",
    limit=100
)
```

#### `read_batched(query: str, batch_size: int = 100) -> Iterator[List[Dict]]`

Read large datasets in memory-efficient batches.

```python
# Process 100,000 transactions in batches of 1,000
for batch in client.read_batched("transaction/get-card-transactions", batch_size=100):
    print(f"Processing batch with {len(batch)} records")
    process_transactions(batch)
```

#### `create(object_name: str, data: Dict[str, Any]) -> Dict[str, Any]`

Create a new record.

```python
new_user = client.create("user", {
    "firstName": "John",
    "lastName": "Doe",
    "email": "john@example.com",
    "active": True,
    "usesApplication": True,
    "language": "en"
})
# Returns: {"userId": "...", "firstName": "John", ...}
```

#### `update(object_name: str, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]`

Update an existing record.

```python
updated_expense = client.update("expense", expense_id, {
    "name": "Updated expense name",
    "externalReferenceId": "EXP-123"
})
```

#### `delete(object_name: str, record_id: str) -> bool`

Delete a record.

**⚠️ WARNING:** Require explicit user confirmation before deleting!

```python
# Ask user first!
if user_confirms_deletion():
    deleted = client.delete("user", user_id)
    if deleted:
        print("User deleted successfully")
```

#### `get_capabilities() -> DriverCapabilities`

Get driver capabilities.

```python
caps = client.get_capabilities()
print(f"Read: {caps.read}")           # True
print(f"Write: {caps.write}")         # True
print(f"Max page size: {caps.max_page_size}")  # 100
```

#### `call_endpoint(endpoint: str, method: str = "POST", params: Dict = None, data: Dict = None) -> Dict`

Call API endpoint directly (low-level access).

```python
result = client.call_endpoint(
    "/user/get-users",
    method="GET"
)

# Or with POST
result = client.call_endpoint(
    "/card/get-cards",
    method="POST",
    data={"userId": "...", "limit": 10}
)
```

#### `close()`

Close connections and cleanup resources.

```python
client = FidooDriver.from_env()
try:
    # Use client
    data = client.read("user/get-users")
finally:
    client.close()  # Always close!
```

## Available Objects & Endpoints

### User Management

- `user/get-user` - Get individual user
- `user/get-users` - List all users
- `user/get-user-by-email` - Find user by email
- `user/get-user-by-employee-number` - Find user by employee ID
- `user/add-user` - Create new user
- `user/activate-user` - Activate user
- `user/activate-application` - Grant app access
- `user/deactivate-user` - Deactivate user
- `user/delete-user` - Delete user

### Card Operations

- `card/get-cards` - List cards with balances
- `card/load-card` - Add funds to card
- `card/load-cards` - Batch load multiple cards
- `card/load-status` - Check load status
- `card/unload-card` - Remove funds from card
- `card/unload-cards` - Batch unload multiple cards
- `card/unload-status` - Check unload status

### Transactions

- `transaction/get-card-transactions` - Card transaction history
- `cash-transactions/get-cash-transactions` - Wallet transactions
- `mvc-transaction/get-transactions` - Fidoo account transactions

### Expenses

- `expense/get-expenses` - Retrieve expense records
- `expense/get-expense-items` - Get line items
- `expense/edit-expense` - Modify expense

### Travel & Billing

- `travel/get-travel-reports` - Business trip summaries
- `travel/get-travel-requests` - Travel request status
- `personal-billing/get-billings` - Billing records

### Settings

- `settings/get-cost-centers` - Cost center list
- `settings/get-projects` - Project list
- `settings/get-account-assignments` - Accounting mappings
- `settings/get-vehicles` - Vehicle registry
- `settings/get-vat-breakdowns` - VAT configurations

## Capabilities

This driver supports:

- ✅ Read operations (query any endpoint)
- ✅ Write operations (create records)
- ✅ Update operations (modify records)
- ✅ Delete operations (remove records)
- ✅ Batch operations (load/unload multiple cards)
- ✅ Pagination (offset token-based)
- ✅ Error handling (structured exceptions)
- ❌ Transactions (not at API level)

## Common Patterns

### Pagination for Large Datasets

The API returns data in pages of up to 100 records. Use `read_batched()` for efficient processing:

```python
total_processed = 0

for batch in client.read_batched("user/get-users", batch_size=100):
    # Process each batch
    for user in batch:
        process_user(user)

    total_processed += len(batch)
    print(f"Processed {total_processed} users...")

print(f"Complete! Total: {total_processed} users")
```

### Error Handling

```python
from fidoo import FidooDriver
from fidoo.exceptions import ObjectNotFoundError, RateLimitError, AuthenticationError

client = FidooDriver.from_env()

try:
    users = client.read("user/get-users")

except AuthenticationError as e:
    print(f"Auth error: {e.message}")
    print(f"Check your API key: {e.details}")

except RateLimitError as e:
    print(f"Rate limited!")
    print(f"Retry after {e.details['retry_after']} seconds")

except ObjectNotFoundError as e:
    print(f"Object not found: {e.message}")
    print(f"Available: {e.details['available']}")

finally:
    client.close()
```

### Filtering and Pagination

```python
from datetime import datetime, timedelta

# Get expenses from last 30 days
thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()

# Query with date range
expenses = client.read(
    "expense/get-expenses",
    limit=100,
    # Note: Filtering is done via API parameters, not in driver
)
```

### Batch Operations

```python
# Load funds to multiple cards at once
for batch in cards:
    batch_size = client.read(
        "card/load-cards",
        # Pass array of load operations
    )
```

## Rate Limiting

Fidoo API limits: **6,000 requests per customer per day**

The driver automatically retries failed requests with exponential backoff:

```python
# Check rate limit status (documentation only)
status = client.get_rate_limit_status()
print(f"Daily limit: {status['limit']} requests")

# If you hit the limit:
# - Wait until next day
# - Reduce batch size
# - Increase delays between requests
```

## Debug Mode

Enable debug logging to see all API calls:

```python
import logging

# Enable debug output
client = FidooDriver.from_env(debug=True)

# Now you'll see:
# [DEBUG] POST https://api.fidoo.com/v2/user/get-users
# [DEBUG]   Payload: {"limit": 100}
```

Or via environment:

```bash
export FIDOO_DEBUG=true
```

## Configuration

### Timeout

Increase timeout for large datasets:

```python
client = FidooDriver.from_env(timeout=60)  # 60 seconds
```

### Retry Attempts

Configure automatic retry behavior:

```python
client = FidooDriver.from_env(max_retries=5)  # Retry up to 5 times
```

### Alternative Base URL

Use the demo environment for testing:

```python
client = FidooDriver(
    api_key="demo_key",
    base_url="https://api-demo.fidoo.com/v2"
)
```

## Troubleshooting

### AuthenticationError: "Missing API key"

**Problem:** Driver can't find API key

**Solution:**
```bash
export FIDOO_API_KEY="your_api_key_here"
```

Or pass directly:
```python
client = FidooDriver(api_key="your_api_key_here")
```

### AuthenticationError: "Invalid API key"

**Problem:** API key is incorrect or expired

**Solution:**
1. Verify API key in Fidoo settings
2. Generate a new API key if needed
3. Check you're using the correct environment (production vs. demo)

### ConnectionError: "Cannot reach Fidoo API"

**Problem:** Network connectivity issue or API is down

**Solution:**
1. Check internet connection
2. Verify `base_url` is correct
3. Check if Fidoo API is operational
4. Try increasing timeout: `timeout=60`

### RateLimitError: "API rate limit exceeded"

**Problem:** Hit the 6,000 requests per day limit

**Solution:**
1. Wait until next day
2. Reduce batch size
3. Add delays between requests
4. Contact Fidoo for higher limits

### ValueError: "limit cannot exceed 100"

**Problem:** Requested page size exceeds API maximum

**Solution:**
```python
# Use default or smaller page size
users = client.read("user/get-users", limit=100)  # Max is 100
```

## Testing

### Mock API Responses

```python
from unittest.mock import patch, Mock

@patch('fidoo.client.requests.request')
def test_list_users(mock_request):
    # Mock API response
    mock_response = Mock()
    mock_response.json.return_value = {
        "data": [
            {"userId": "1", "firstName": "John", "lastName": "Doe"},
            {"userId": "2", "firstName": "Jane", "lastName": "Smith"}
        ],
        "complete": True
    }
    mock_request.return_value = mock_response

    # Test
    client = FidooDriver(api_key="test_key")
    users = client.read("user/get-users")

    assert len(users) == 2
    assert users[0]["firstName"] == "John"
```

## Examples

See `examples/` directory for complete scripts:

- `list_all_users.py` - Query all users
- `get_cards_by_user.py` - Get cards for specific user
- `recent_transactions.py` - Get transactions from last 30 days
- `batch_load_cards.py` - Load funds to multiple cards
- `expense_report.py` - Generate expense report

## Support

- **Documentation:** https://www.fidoo.com/expense-management/integrace/api
- **API Swagger:** https://api-demo.fidoo.com/v2/swagger.json
- **Issues:** Check existing issues in repository

## License

MIT License - see LICENSE file for details

## Version

Driver Version: 1.0.0
Fidoo API Version: v2
