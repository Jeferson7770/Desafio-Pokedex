# Finance API Guide (Accounts, Transactions, Dashboard)

This document explains how to consume the finance module endpoints: bank accounts, transactions, and dashboard summary.

## 1. Authentication

```http
Authorization: Bearer <token>
Content-Type: application/json
```

Base endpoints:

```text
/api/finance/accounts/
/api/finance/transactions/
/api/finance/dashboard-summary/
```

Legacy alias note:

- Finance reports alias exists at `/api/relatorios/` for reports (see reports docs).

## 2. Bank Accounts (`BankAccount`)

### 2.1 Structure

```json
{
  "id": 1,
  "firm": 10,
  "name": "Office Itau",
  "account_type": "CHECKING",
  "provider_name": "Itau",
  "external_account_id": "abc-123",
  "initial_balance": "0.00",
  "current_balance": "15420.50",
  "created_at": "2026-06-01T10:00:00Z"
}
```

`account_type` values:

- `CHECKING`
- `SAVINGS`
- `INVESTMENT`
- `CASH`

### 2.2 List accounts

```http
GET /api/finance/accounts/
```

Returns only accounts from authenticated user's firm.

### 2.3 Create account manually

```http
POST /api/finance/accounts/
```

```json
{
  "name": "Office cash",
  "account_type": "CASH",
  "initial_balance": "500.00"
}
```

`current_balance` and `firm` are set by backend.

### 2.4 Update account

```http
PATCH /api/finance/accounts/{id}/
```

`current_balance` cannot be updated directly; it changes via transactions.

### 2.5 Delete account

```http
DELETE /api/finance/accounts/{id}/
```

## 3. Open Finance (Pluggy)

### 3.1 Generate connect token

```http
POST /api/finance/accounts/pluggy/connect-token/
```

Returns temporary token for frontend Pluggy widget.

### 3.2 Synchronize accounts

```http
POST /api/finance/accounts/pluggy/sincronizar/
```

```json
{
  "item_id": "pluggy-item-uuid"
}
```

Behavior:

1. Waits for Pluggy item update to finish (45s timeout).
2. Synchronizes balances for all item accounts in one transaction.
3. Triggers current-month transaction sync in background.

### 3.3 Refresh dashboard balances

```http
POST /api/finance/accounts/pluggy/atualizar-dashboard/
```

Utility endpoint; returns confirmation without blocking.

## 4. Transactions (`Transaction`)

### 4.1 Structure

```json
{
  "id": 1,
  "account": 1,
  "account_name": "Office Itau",
  "description": "Client fee payment",
  "amount": "3000.00",
  "transaction_type": "INFLOW",
  "date": "2026-06-04",
  "expense_installment": null,
  "fee_installment": 101,
  "external_transaction_id": null,
  "is_reconciled": false,
  "created_at": "2026-06-04T10:00:00Z"
}
```

`transaction_type` values:

- `INFLOW`
- `OUTFLOW`

### 4.2 List transactions

```http
GET /api/finance/transactions/
```

### 4.3 Create manual transaction

```http
POST /api/finance/transactions/
```

```json
{
  "account": 1,
  "description": "Court fee reimbursement",
  "amount": "350.00",
  "transaction_type": "INFLOW",
  "date": "2026-06-04"
}
```

When created:

- `INFLOW` adds to account `current_balance`.
- `OUTFLOW` subtracts from account `current_balance`.

Constraint: cannot link `expense_installment` and `fee_installment` at the same time.

### 4.4 Delete transaction

```http
DELETE /api/finance/transactions/{id}/
```

Account `current_balance` is automatically reverted.

### 4.5 Cash flow summary

```http
GET /api/finance/transactions/cash-flow-summary/
```

## 5. Financial Dashboard Summary

```http
GET /api/finance/dashboard-summary/
GET /api/finance/dashboard-summary/?year=2026&month=6
```

Optional parameters: `year`, `month`. If omitted, current month is used.

The response keeps backend field names as implemented (Portuguese snake_case keys), for compatibility.

## 6. Frontend Checklist

1. Always send auth token.
2. Open Finance flow: generate token -> connect in widget -> call sync endpoint.
3. Imported Open Finance transactions come with `is_reconciled: true` and `external_transaction_id`.
4. Manual transaction create/delete automatically adjusts account balance.
5. Dashboard supports optional `year` and `month`.
