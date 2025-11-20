# FidooDriver Examples

Comprehensive collection of example scripts demonstrating driver usage patterns.

## Quick Navigation

| Example | File | Purpose | Complexity |
|---------|------|---------|-----------|
| Basic Usage | `basic_usage.py` | Initialization, discovery, simple queries | ⭐ Beginner |
| List Users | `list_all_users.py` | Query all users with basic filtering | ⭐ Beginner |
| Error Handling | `error_handling.py` | Exception handling and recovery | ⭐⭐ Intermediate |
| Get Cards | `get_user_cards.py` | Card operations and filtering | ⭐⭐ Intermediate |
| Batch Processing | `batch_processing.py` | Large dataset pagination | ⭐⭐ Intermediate |
| Write Operations | `write_operations.py` | Create, update, batch operations | ⭐⭐ Intermediate |
| Debug Mode | `debug_mode.py` | Enable logging for troubleshooting | ⭐⭐ Intermediate |
| Advanced Usage | `advanced_usage.py` | Complex workflows and optimization | ⭐⭐⭐ Advanced |

## Running Examples

### Setup

```bash
# Set environment variables
export FIDOO_API_KEY="your_api_key_here"

# Optional
export FIDOO_BASE_URL="https://api.fidoo.com/v2"
export FIDOO_DEBUG="false"
export FIDOO_TIMEOUT="30"
```

### Run Example

```bash
# From examples directory
python basic_usage.py

# Or from project root
python -m fidoo.examples.basic_usage
```

## Example Descriptions

### 1. basic_usage.py ⭐ Beginner

**What it does:**
- Initializes driver from environment
- Checks capabilities
- Discovers available objects
- Retrieves object schema
- Executes simple query
- Checks rate limits

**Key patterns:**
```python
client = FidooDriver.from_env()
objects = client.list_objects()
fields = client.get_fields("user")
users = client.read("user/get-users", limit=5)
client.close()
```

**When to use:**
- First time learning the driver
- Understanding basic operations
- Testing setup

---

### 2. list_all_users.py ⭐ Beginner

**What it does:**
- Lists all users
- Handles pagination
- Formats output

**Key patterns:**
```python
users = client.read("user/get-users", limit=100)
for user in users:
    print(f"{user['firstName']} {user['lastName']}")
```

**When to use:**
- Learning query execution
- Testing pagination
- Verifying API access

---

### 3. error_handling.py ⭐⭐ Intermediate

**What it does:**
- Catches specific exceptions
- Handles different error types
- Provides recovery strategies
- Demonstrates error details

**Error types covered:**
- `AuthenticationError` - Invalid credentials
- `RateLimitError` - API quota exceeded
- `ObjectNotFoundError` - Unknown object
- `ConnectionError` - Network issues
- `ValidationError` - Invalid data
- `TimeoutError` - Request timeout

**Key patterns:**
```python
try:
    data = client.read(...)
except AuthenticationError as e:
    print(f"Error: {e.message}")
    print(f"Details: {e.details}")
except RateLimitError as e:
    print(f"Retry in {e.details['retry_after']}s")
except Exception as e:
    print(f"Unexpected: {e}")
finally:
    client.close()
```

**When to use:**
- Production code
- Graceful error handling
- User feedback

---

### 4. get_user_cards.py ⭐⭐ Intermediate

**What it does:**
- Gets cards for a user
- Displays card details
- Shows balances

**Key patterns:**
```python
cards = client.read("card/get-cards", limit=100)
for card in cards:
    print(f"Card: {card['embossedName']}")
    print(f"Balance: {card['availableBalance']} CZK")
```

**When to use:**
- Card operations
- Account information
- Balance queries

---

### 5. batch_processing.py ⭐⭐ Intermediate

**What it does:**
- Processes large datasets
- Uses `read_batched()` for memory efficiency
- Shows progress

**Key patterns:**
```python
for batch in client.read_batched("user/get-users", batch_size=100):
    for user in batch:
        process_user(user)
    print(f"Processed {len(batch)} records")
```

**When to use:**
- Large dataset queries (1000+ records)
- Memory-constrained environments
- Real-time processing

---

### 6. write_operations.py ⭐⭐ Intermediate

**What it does:**
- Creates new users
- Updates existing records
- Demonstrates batch operations
- Shows error handling for writes

**Key patterns:**
```python
# Create
new_user = client.create("user", {
    "firstName": "John",
    "lastName": "Doe",
    "email": "john@example.com"
})

# Update
updated = client.update("expense", expense_id, {
    "name": "New name"
})

# Delete (requires confirmation)
if user_confirms():
    deleted = client.delete("user", user_id)
```

**When to use:**
- Creating records
- Modifying data
- Batch operations

---

### 7. debug_mode.py ⭐⭐ Intermediate

**What it does:**
- Enables debug logging
- Shows all API calls
- Displays request payloads

**Key patterns:**
```python
client = FidooDriver.from_env(debug=True)

# Now shows:
# [DEBUG] POST https://api.fidoo.com/v2/user/get-users
# [DEBUG]   Payload: {"limit": 100}
```

**When to use:**
- Troubleshooting API issues
- Understanding request/response flow
- Debugging integration problems

---

### 8. advanced_usage.py ⭐⭐⭐ Advanced

**What it does:**
- Advanced filtering
- Data transformation pipelines
- Resilient querying with retry
- Performance optimization
- Multi-operation workflows

**Key patterns:**

**1. Advanced Filtering:**
```python
expenses = client.read("expense/get-expenses")
recent = [e for e in expenses if is_recent(e)]
```

**2. Data Pipeline:**
```python
users = client.read("user/get-users")
for user in users:
    cards = client.read("card/get-cards")
    user['total_balance'] = sum(c['balance'] for c in cards)
```

**3. Resilient Querying:**
```python
def query_with_retry(endpoint, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            return client.read(endpoint)
        except RateLimitError:
            time.sleep(5)
        except ConnectionError:
            continue
```

**4. Performance Optimization:**
```python
# Use batching for large datasets
for batch in client.read_batched(endpoint, batch_size=100):
    process(batch)

# Cache schema
schema = client.get_fields("user")
```

**When to use:**
- Production systems
- Complex data workflows
- Performance-sensitive code

---

## Design Patterns Reference

### 1. Discovery Pattern

```python
# Always discover capabilities first
objects = client.list_objects()
fields = client.get_fields("user")
caps = client.get_capabilities()
```

### 2. Resource Cleanup Pattern

```python
client = FidooDriver.from_env()
try:
    # Your code
    pass
finally:
    client.close()
```

### 3. Error Handling Pattern

```python
try:
    result = client.read(...)
except RateLimitError as e:
    wait = e.details['retry_after']
except ValidationError as e:
    details = e.details
except Exception as e:
    logger.error(f"Unexpected: {e}")
```

### 4. Pagination Pattern

```python
# For small datasets
data = client.read(endpoint, limit=100)

# For large datasets
for batch in client.read_batched(endpoint, batch_size=100):
    process(batch)
```

### 5. Batch Operations Pattern

```python
# Create multiple users
for user_data in users_list:
    client.create("user", user_data)

# Load funds to multiple cards
for card_id, amount in cards:
    client.call_endpoint(
        "/card/load-card",
        method="POST",
        data={"cardId": card_id, "amount": amount}
    )
```

---

## Common Scenarios

### Scenario 1: Export all users to CSV

```python
import csv

client = FidooDriver.from_env()
users = client.read("user/get-users", limit=10000)

with open('users.csv', 'w') as f:
    writer = csv.DictWriter(f, fieldnames=['userId', 'firstName', 'lastName', 'email'])
    writer.writeheader()
    for user in users:
        writer.writerow(user)

client.close()
```

### Scenario 2: Get high-balance accounts

```python
client = FidooDriver.from_env()
cards = client.read("card/get-cards", limit=1000)

high_balance = [
    card for card in cards
    if float(card.get('availableBalance', 0)) > 10000
]

print(f"Accounts with >10k CZK: {len(high_balance)}")
client.close()
```

### Scenario 3: Archive old expenses

```python
from datetime import datetime, timedelta

client = FidooDriver.from_env()
cutoff_date = (datetime.now() - timedelta(days=365)).isoformat()

expenses = client.read("expense/get-expenses", limit=1000)
old_expenses = [
    e for e in expenses
    if e.get('createdDate', '') < cutoff_date
]

print(f"Found {len(old_expenses)} expenses older than 1 year")
client.close()
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'fidoo'"

**Solution:**
```bash
# Add parent directory to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/.."

# Or run from parent directory
python -m fidoo.examples.basic_usage
```

### "AuthenticationError: Missing API key"

**Solution:**
```bash
export FIDOO_API_KEY="your_api_key_here"
```

### "ConnectionError: Cannot reach Fidoo API"

**Solution:**
```bash
# Check API is reachable
curl https://api.fidoo.com/v2/status/user-info \
  -H "X-Api-Key: your_api_key"

# Try demo environment
export FIDOO_BASE_URL="https://api-demo.fidoo.com/v2"
```

### "RateLimitError: API rate limit exceeded"

**Solution:**
```python
# Use batch processing with delays
import time

for batch in client.read_batched(endpoint, batch_size=50):
    process(batch)
    time.sleep(1)  # Add delay between batches
```

---

## Testing Guide

### Run all examples

```bash
for script in *.py; do
    echo "Running $script..."
    python "$script"
    echo "---"
done
```

### Test with mocked API

See `write_operations.py` for mock testing patterns:

```python
from unittest.mock import patch, Mock

@patch('fidoo.client.requests.request')
def test_example(mock_request):
    # Setup mock
    mock_response = Mock()
    mock_response.json.return_value = {"data": [...]}
    mock_request.return_value = mock_response

    # Test
    client = FidooDriver(api_key="test")
    result = client.read(...)

    assert len(result) > 0
```

---

## Performance Tips

1. **Use `read_batched()` for large datasets**
   - More memory efficient
   - Processes data incrementally

2. **Set appropriate timeouts**
   ```python
   client = FidooDriver.from_env(timeout=60)
   ```

3. **Cache schema information**
   ```python
   user_schema = client.get_fields("user")  # Cache this
   ```

4. **Minimize API calls**
   - Get data once, process multiple times
   - Use pagination to avoid huge responses

5. **Add delays for bulk operations**
   ```python
   import time
   for item in items:
       process(item)
       time.sleep(0.1)  # Small delay between requests
   ```

---

## Further Reading

- **README.md** - Complete API reference
- **03_quick_reference.md** - Quick lookup guide
- **API Docs** - https://www.fidoo.com/expense-management/integrace/api
- **API Swagger** - https://api-demo.fidoo.com/v2/swagger.json

---

## Contributing Examples

To add new examples:

1. Create new Python file in `examples/`
2. Follow naming convention: `descriptive_name.py`
3. Include docstring explaining the example
4. Add error handling
5. Test with real API
6. Update this README with new example

---

**Last Updated:** 2025-11-20
**Examples Status:** ✅ Complete & Tested
**Total Examples:** 8
