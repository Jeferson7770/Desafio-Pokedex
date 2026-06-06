# Financial Reports API Guide

This document explains how to consume consolidated financial report endpoints.

## 1. Authentication

```http
Authorization: Bearer <token>
Content-Type: application/json
```

Primary base URL:

```text
/api/reports/
```

Legacy alias also available:

- `/api/relatorios/`

## 2. What Reports Represent

Reports module stores consolidated financial-health snapshots by month/year. Unlike dashboard endpoints (real-time calculation), reports return processed and categorized persisted data.

If no consolidated report exists for the requested period, backend returns an empty/zeroed object without error.

## 3. Data Structure

### `FinancialReportSummary`

```json
{
  "id": 1,
  "firm": 10,
  "month": 6,
  "year": 2026,
  "total_revenue": "18000.00",
  "total_expense": "7200.00",
  "expenses_fixed": "3500.00",
  "expenses_variable": "1800.00",
  "expenses_eventual": "900.00",
  "expenses_payroll": "4200.00",
  "expenses_taxes": "1100.00",
  "expenses_structure": "2000.00",
  "expenses_late_interest": "150.00",
  "team_size": 3,
  "last_sync_at": "2026-06-04T10:00:00Z",
  "is_fully_categorized": true
}
```

Derived model fields (not serialized by default):

- `net_result = total_revenue - total_expense`
- `profit_margin = (net_result / total_revenue) * 100`

## 4. Retrieve period report

```http
GET /api/reports/
GET /api/reports/?year=2026&month=6
```

Optional params: `year`, `month`. Current month is used when omitted.

Behavior:

- If report exists: return persisted values.
- If not: return zeroed object without error.

## 5. Consolidate report (upsert)

```http
POST /api/reports/
```

Upsert behavior:

- existing `firm + month + year` -> update
- missing -> create

Response codes:

- `201 Created` when inserted
- `200 OK` when updated

## 6. Expense categories

- `expenses_fixed`
- `expenses_variable`
- `expenses_eventual`
- `expenses_payroll`
- `expenses_taxes`
- `expenses_structure`
- `expenses_late_interest`

## 7. Frontend Checklist

1. Call `GET /api/reports/?year=YYYY&month=MM` for selected month.
2. Do not treat zeroed response as an error.
3. Call `POST /api/reports/` to consolidate month data.
4. `is_fully_categorized: true` indicates trusted complete categorization.
5. Use `last_sync_at` to show last synchronization timestamp.
