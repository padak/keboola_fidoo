# Fidoo Driver - Developer Documentation

## API Reference

### Core Methods

#### `list_objects() -> List[str]`
```python
objects = client.list_objects()
```

#### `get_fields(object_name: str) -> Dict[str, Any]`
```python
fields = client.get_fields("card")
```

#### `read(query: str, limit: int = 100, offset: str = None, **kwargs) -> List[Dict]`
```python
users = client.read("user/get-users", limit=100)
items = client.read("expense/get-expense-items", expenseId="...")
```

#### `read_batched(query: str, batch_size: int = 100) -> Iterator[List[Dict]]`
```python
for batch in client.read_batched("transaction/get-card-transactions"):
    process(batch)
```

#### `create(object_name: str, data: Dict) -> Dict`
```python
new_user = client.create("user", {"firstName": "John", ...})
```

#### `update(object_name: str, record_id: str, data: Dict) -> Dict`
```python
updated = client.update("expense", expense_id, {"name": "Updated"})
```

#### `delete(object_name: str, record_id: str) -> bool`
```python
deleted = client.delete("user", user_id)
```

## Error Handling

```python
from fidoo_driver import FidooDriver
from fidoo_driver.exceptions import (
    AuthenticationError,
    RateLimitError,
    ObjectNotFoundError,
    ValidationError,
    TimeoutError
)

try:
    users = client.read("user/get-users")
except AuthenticationError as e:
    print(f"Auth error: {e.message}, details: {e.details}")
except RateLimitError as e:
    print(f"Rate limited, retry after: {e.details['retry_after']}s")
except ObjectNotFoundError as e:
    print(f"Not found: {e.message}")
finally:
    client.close()
```

## Available Endpoints

### User Management
- `user/get-users` - List users
- `user/get-user` - Get by ID
- `user/get-user-by-email` - Get by email
- `user/add-user` - Create
- `user/update-user` - Update
- `user/activate-user` / `deactivate-user`
- `user/delete-user`

### Card Operations
- `card/get-cards` - List cards
- `card/load-card` / `unload-card`
- `card/load-cards` / `unload-cards` (batch)
- `card/load-status` / `unload-status`

### Transactions
- `transaction/get-card-transactions`
- `cash-transactions/get-cash-transactions`
- `mvc-transaction/get-transactions`

### Expenses
- `expense/get-expenses`
- `expense/get-expense-items` (requires expenseId)
- `expense/edit-expense`

### Travel & Billing
- `travel/get-travel-reports`
- `travel/get-travel-report-detail` (requires travelReportId)
- `travel/get-travel-requests`
- `travel/get-travel-request-detail` (requires travelRequestId)
- `personal-billing/get-billings` (requires fromDate, toDate)

### Settings
- `settings/get-cost-centers`
- `settings/get-projects`
- `settings/get-account-assignments`
- `settings/get-accounting-categories`
- `settings/get-vat-breakdowns`
- `settings/get-vehicles`
- `accounts/get-accounts`

## Rate Limiting

- Limit: 6,000 requests per customer per day
- Driver automatically retries with exponential backoff
- Check status: `client.get_rate_limit_status()`

## Debug Mode

```python
client = FidooDriver.from_env(debug=True)
```

Or:
```bash
export FIDOO_DEBUG=true
```

## Configuration Options

```python
client = FidooDriver(
    api_key="...",                    # Required
    base_url="https://api.fidoo.com/v2",  # Default
    timeout=30,                       # Seconds
    max_retries=3,                    # Retry attempts
    debug=False                       # Debug logging
)
```

## Testing

```python
from unittest.mock import patch, Mock

@patch('fidoo_driver.client.requests.request')
def test_list_users(mock_request):
    mock_response = Mock()
    mock_response.json.return_value = {
        "userList": [{"userId": "1", "firstName": "John"}],
        "complete": True
    }
    mock_request.return_value = mock_response

    client = FidooDriver(api_key="test")
    users = client.read("user/get-users")
    assert len(users) == 1
```

## Examples

See `fidoo_driver/examples/` directory.
