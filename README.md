# Keboola Fidoo Integration

Keboola custom component for extracting data from Fidoo expense management system.

## Features

- Export data from 17 Fidoo object types
- Automatic pagination handling
- Rate limiting with exponential backoff
- Incremental state tracking

## Available Objects

| Object | Description |
|--------|-------------|
| user | User management |
| card | Prepaid cards |
| transaction | Card transactions |
| cash_transaction | Cash transactions |
| mvc_transaction | MVC transactions |
| expense | Expenses |
| travel_report | Travel reports |
| travel_request | Travel requests |
| personal_billing | Personal billing |
| account | Accounts |
| cost_center | Cost centers |
| project | Projects |
| account_assignment | Account assignments |
| accounting_category | Accounting categories |
| vat_breakdown | VAT breakdowns |
| vehicle | Vehicles |
| receipt | Receipts |

## Configuration

### Required Parameters

| Parameter | Description |
|-----------|-------------|
| `#FIDOO_API_KEY` | Fidoo API key (encrypted) |

### Optional Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `objects` | `["user", "card", "transaction", "expense"]` | List of objects to export |
| `output_bucket` | `out.c-fidoo` | Destination bucket in Keboola Storage |
| `api_url` | `https://api.fidoo.com/v2/` | API URL (use demo URL for testing) |

### Example Configuration

```json
{
  "parameters": {
    "#FIDOO_API_KEY": "your-api-key-here",
    "objects": ["user", "card", "transaction", "expense", "travel_report"],
    "output_bucket": "out.c-fidoo"
  }
}
```

## Output

Each object type is exported to a separate table:
- `out.c-fidoo.user`
- `out.c-fidoo.card`
- `out.c-fidoo.transaction`
- etc.

Nested JSON fields are automatically flattened to JSON strings.

## Development

### Installation

```bash
pip install -r requirements.txt
```

### Local Testing

```bash
# Set environment variables
export FIDOO_API_KEY=your-api-key

# Run component
python main.py
```

## API Rate Limits

Fidoo API has a limit of 6,000 requests per day per customer. The driver automatically handles rate limiting with exponential backoff.

## License

MIT
