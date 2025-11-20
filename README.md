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
    "objects": ["user", "card", "transaction", "expense"],
    "output_bucket": "out.c-fidoo",
    "include_dependent": true,
    "api_url": "https://api.fidoo.com/v2/"
  }
}
```

## Local Run

```bash
uv pip install -r requirements.txt
KBC_DATADIR=./data python main.py
```

## License

MIT
