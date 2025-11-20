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

**Automatically extracted dependent objects:**
- expense_item (expense line items)
- travel_report_detail (travel report details) + parts
- travel_request_detail (travel request details) + parts

## Configuration

```json
{
  "parameters": {
    "#FIDOO_API_KEY": "your-api-key",
    "api_url": "https://api.fidoo.com/v2/",
    "output_bucket": "out.c-fidoo",
    "objects": ["user", "card", "transaction", "expense"],
    "include_dependent": true,
    "set_primary_keys": true
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

## Output

- **Automatic output mapping** - tables are created in the specified bucket via manifest
- **Primary keys** - automatically detected (e.g., `expenseId`, `userId`, `[_parent_id, _index]` for nested)
- **Nested objects** - flattened into separate tables with foreign key reference

## Local Run

```bash
uv pip install -r requirements.txt
KBC_DATADIR=./data python main.py
```

## License

MIT
