# Fidoo Data - SQL Samples

Example SQL queries for working with Fidoo data in Keboola Storage (Snowflake).

## Data Structure

Data is normalized - nested arrays are stored in separate tables with `__fieldName` suffix and linked via `_parent_id`.

## Basic Queries

### Users and Their Cards Overview

```sql
SELECT
    u."firstName",
    u."lastName",
    u."email",
    c."maskedNumber",
    c."cardType",
    c."availableBalance"
FROM "user" u
LEFT JOIN "card" c ON u."userId" = c."userId"
ORDER BY u."lastName", u."firstName";
```

### Transactions with Card and User Details

```sql
SELECT
    t."transactionDate",
    t."merchantName",
    t."originalAmount",
    t."originalCurrency",
    t."categoryName",
    u."firstName" || ' ' || u."lastName" AS "userName",
    c."maskedNumber"
FROM "transaction" t
LEFT JOIN "user" u ON t."userId" = u."userId"
LEFT JOIN "card" c ON t."cardId" = c."cardId"
ORDER BY t."transactionDate" DESC;
```

### Expenses with Project Assignments

```sql
SELECT
    e."expenseId",
    e."dateTime",
    e."name",
    e."amount",
    e."currency",
    e."merchantName",
    p."value" AS "projectId"
FROM "expense" e
LEFT JOIN "expense__projectIds" p ON e."expenseId" = p."parent_id"
ORDER BY e."dateTime" DESC;
```

## Aggregation and Reporting

### Monthly Expense Summary by User

```sql
SELECT
    DATE_TRUNC('month', e."dateTime") AS "month",
    u."firstName" || ' ' || u."lastName" AS "userName",
    COUNT(*) AS "transactionCount",
    SUM(e."amount") AS "totalAmount",
    e."currency"
FROM "expense" e
JOIN "user" u ON e."ownerUserId" = u."userId"
GROUP BY 1, 2, e."currency"
ORDER BY 1 DESC, 4 DESC;
```

### Top 10 Merchants by Volume

```sql
SELECT
    "merchantName",
    COUNT(*) AS "transactionCount",
    SUM("originalAmount") AS "totalAmount",
    "originalCurrency"
FROM "transaction"
WHERE "merchantName" IS NOT NULL
GROUP BY "merchantName", "originalCurrency"
ORDER BY "totalAmount" DESC
LIMIT 10;
```

### Expenses by Cost Center

```sql
SELECT
    cc."name" AS "costCenterName",
    COUNT(DISTINCT e."expenseId") AS "expenseCount",
    SUM(e."amount") AS "totalAmount"
FROM "expense" e
JOIN "cost_center" cc ON CONTAINS(e."costCenterIds", cc."costCenterId")
GROUP BY cc."name"
ORDER BY "totalAmount" DESC;
```

## Working with Normalized Arrays

### Expenses with Multiple Receipts

```sql
SELECT
    e."expenseId",
    e."name",
    e."amount",
    COUNT(r."value") AS "receiptCount"
FROM "expense" e
LEFT JOIN "expense__receiptUrls" r ON e."expenseId" = r."parent_id"
GROUP BY e."expenseId", e."name", e."amount"
HAVING COUNT(r."value") > 1
ORDER BY "receiptCount" DESC;
```

### Cards with Multiple Connected Users

```sql
SELECT
    c."cardId",
    c."maskedNumber",
    c."cardType",
    cu."value" AS "connectedUserId"
FROM "card" c
JOIN "card__connectedUserIds" cu ON c."cardId" = cu."parent_id";
```

### Cash Transactions with Receipts

```sql
SELECT
    ct."cashTransactionId",
    ct."dateTime",
    ct."amount",
    ct."currency",
    ct."name",
    r."value" AS "receiptUrl"
FROM "cash_transaction" ct
LEFT JOIN "cash_transaction__receiptUrls" r ON ct."cashTransactionId" = r."parent_id";
```

## Travel Management

### Travel Requests with Details

```sql
SELECT
    tr."travelRequestId",
    tr."destination",
    tr."startDateTime",
    tr."endDateTime",
    trd."travelRequestDetailId",
    tdp."value" AS "detailPart"
FROM "travel_request" tr
LEFT JOIN "travel_request_detail" trd ON tr."travelRequestId" = trd."travelRequestId"
LEFT JOIN "travel_request_detail__parts" tdp ON trd."travelRequestDetailId" = tdp."parent_id";
```

### Travel Reports with Settlement

```sql
SELECT
    trp."travelReportId",
    trp."destination",
    trp."status",
    trd."travelReportDetailId",
    tdp."value" AS "reportPart"
FROM "travel_report" trp
LEFT JOIN "travel_report_detail" trd ON trp."travelReportId" = trd."travelReportId"
LEFT JOIN "travel_report_detail__parts" tdp ON trd."travelReportDetailId" = tdp."parent_id";
```

## Personal Billing

### Personal Accounts with Currency Summary

```sql
SELECT
    pb."personalBillingId",
    pb."state",
    u."firstName" || ' ' || u."lastName" AS "userName",
    sc."value" AS "currencySummary"
FROM "personal_billing" pb
LEFT JOIN "personal_billing__user" pu ON pb."personalBillingId" = pu."parent_id"
LEFT JOIN "user" u ON pu."value" = u."userId"
LEFT JOIN "personal_billing__summaryByCurrencyList" sc ON pb."personalBillingId" = sc."parent_id";
```

## Analytical Queries

### Expense Trends Over Time

```sql
SELECT
    DATE_TRUNC('week', "dateTime") AS "week",
    COUNT(*) AS "expenseCount",
    SUM("amount") AS "totalAmount",
    AVG("amount") AS "avgAmount"
FROM "expense"
WHERE "dateTime" >= DATEADD('month', -3, CURRENT_DATE())
GROUP BY 1
ORDER BY 1;
```

### Card vs Cash Transactions Comparison

```sql
SELECT
    'Card' AS "transactionType",
    COUNT(*) AS "count",
    SUM("originalAmount") AS "totalAmount"
FROM "transaction"
UNION ALL
SELECT
    'Cash' AS "transactionType",
    COUNT(*) AS "count",
    SUM("amount") AS "totalAmount"
FROM "cash_transaction";
```

### Unclosed Expenses

```sql
SELECT
    e."expenseId",
    e."name",
    e."amount",
    e."currency",
    e."dateTime",
    u."firstName" || ' ' || u."lastName" AS "owner"
FROM "expense" e
JOIN "user" u ON e."ownerUserId" = u."userId"
WHERE e."closed" = false
ORDER BY e."dateTime";
```

## Notes

- All identifiers (tables, columns) are quoted to preserve camelCase in Snowflake
- Tables with `__` in name are normalized arrays - join via `"parent_id"`
- Dates are in ISO 8601 format
- For Snowflake use `DATE_TRUNC`, other databases may have different syntax
