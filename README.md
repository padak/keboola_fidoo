# Keboola Fidoo Extractor

Data extractor for Fidoo expense management system.

## Objects

| Object | Description | Nested Tables |
|--------|-------------|---------------|
| user | Users | - |
| card | Payment cards | card__connectedUserIds |
| transaction | Card transactions | - |
| cash_transaction | Cash transactions | cash_transaction__receiptUrls |
| mvc_transaction | MVC transactions | - |
| expense | Expenses | expense__receiptIds, expense__receiptUrls, expense__projectIds |
| travel_report | Travel reports | - |
| travel_request | Travel requests | - |
| personal_billing | Personal billing | personal_billing__user, personal_billing__closedByUser, personal_billing__summaryByCurrencyList |
| account | Accounts | account__bankAccountNumber |
| cost_center | Cost centers | - |
| project | Projects | - |
| account_assignment | Account assignments | - |
| accounting_category | Accounting categories | - |
| vat_breakdown | VAT breakdowns | - |
| vehicle | Vehicles | - |

**Automatically extracted dependent objects** (when `include_dependent: true`):
- expense_item → requires `expense` in objects list
- travel_report_detail + parts → requires `travel_report` in objects list
- travel_request_detail + parts → requires `travel_request` in objects list

## Configuration

```json
{
  "parameters": {
    "#FIDOO_API_KEY": "your-api-key",
    "api_url": "https://api.fidoo.com/v2/",
    "output_bucket": "out.c-fidoo",
    "objects": ["user", "card", "transaction", "expense"],
    "include_dependent": true,
    "set_primary_keys": true,
    "auto_incremental": false
  }
}
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `#FIDOO_API_KEY` | required | Fidoo API key |
| `api_url` | production | API URL (use demo for testing) |
| `output_bucket` | out.c-fidoo | Target bucket in Keboola Storage |
| `objects` | basic set | List of objects to extract |
| `include_dependent` | true | Extract dependent objects (expense_item, etc.) |
| `set_primary_keys` | true | Auto-detect and set primary keys |
| `auto_incremental` | false | Enable incremental loading using last_run from state |

## Incremental Loading

When `auto_incremental: true`, the extractor uses the `last_run` timestamp from Keboola state to fetch only new records since the last successful run.

**Supported objects for incremental loading:**
- transaction, cash_transaction, mvc_transaction
- expense, travel_report, travel_request

**Always full load:**
- user, card, account, personal_billing
- All settings objects (cost_center, project, vehicle, etc.)

Incremental objects are exported with `incremental: true` in their manifest, so Keboola Storage appends new records instead of replacing the table.

## Output

- **Automatic output mapping** - tables are created in the specified bucket via manifest
- **Primary keys** - automatically detected (e.g., `expenseId`, `userId`, `[_parent_id, _index]` for nested)
- **Nested objects** - flattened into separate tables with foreign key reference

## Local Run

### Installation

```bash
# Install uv if you haven't already
# macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows:
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Setup and Run

```bash
# Install dependencies using uv
uv sync

# Run the application
uv run python main.py

# Or with the KBC_DATADIR environment variable
KBC_DATADIR=./data uv run python main.py
```

### Development

```bash
# Install development dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Format code
uv run black .

# Lint code
uv run ruff check .
```

## License

MIT
