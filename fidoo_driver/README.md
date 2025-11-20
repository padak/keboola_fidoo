# Fidoo Driver

Python API driver pro Fidoo Expense Management.

## Použití

```python
from fidoo_driver import FidooDriver

client = FidooDriver.from_env()

try:
    users = client.read("user/get-users", limit=100)

    for batch in client.read_batched("expense/get-expenses"):
        process(batch)
finally:
    client.close()
```

## Konfigurace

```bash
export FIDOO_API_KEY="your_api_key"
export FIDOO_BASE_URL="https://api.fidoo.com/v2"  # optional
```

## API dokumentace

- Fidoo API: https://www.fidoo.com/expense-management/integrace/api
- Swagger: https://api-demo.fidoo.com/v2/swagger.json

## Developer dokumentace

Viz [docs/DEVELOPERS.md](../docs/DEVELOPERS.md)
