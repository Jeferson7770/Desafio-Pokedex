# Expenses API Guide

This document explains how to use the current expenses endpoints.

## Base URL and Authentication

- Base: `/api/expenses/`
- All endpoints require JWT.

```http
Authorization: Bearer <token>
Content-Type: application/json
```

## Endpoints Overview

1. `GET /api/expenses/`
2. `POST /api/expenses/`
3. `GET /api/expenses/{id}/`
4. `PATCH /api/expenses/{id}/`
5. `DELETE /api/expenses/{id}/`
6. `POST /api/expenses/import/`
7. `POST /api/expenses/defer-installment/{installment_id}/`
8. `GET /api/expenses/yearly-summary/`

## Data Structures

### Expense

```json
{
  "id": 1,
  "firm": 10,
  "title": "Office Rent",
  "description": "Annual contract",
  "amount": "4800.00",
  "due_date": "2026-10-10",
  "frequency": "ONE_TIME",
  "category": "ESTRUTURA",
  "priority": "LEGAL",
  "is_paid": false,
  "paid_at": null,
  "is_active": true,
  "is_installment": false,
  "total_installments": 1,
  "installment_value": 4800.0,
  "interest_rate_month": "0.00",
  "installments": [],
  "created_at": "2026-06-04T10:00:00Z"
}
```

### Installment (`ParcelaDespesa`)

```json
{
  "id": 11,
  "installment_number": 2,
  "amount": "3000.00",
  "due_date": "2026-07-10",
  "is_paid": false,
  "paid_at": null,
  "status": "A_VENCER",
  "late_interest_cost": "0.00",
  "deferrals": []
}
```

## Accepted Enums

### `frequency`

- `ONE_TIME`
- `MONTHLY`
- `ANNUAL`

### `category`

- `PESSOAL_E_REMUNERACAO`
- `CUSTAS_PROCESSUAIS_E_JUDICIAIS`
- `FINANCEIRA`
- `CAPACITACAO_E_DESENVOLVIMENTO`
- `FISCAL_E_OBRIGACOES_LEGAIS`
- `ESTRUTURA_E_OPERACAO`
- `TECNOLOGIA_E_ASSINATURA`
- `MARKETING_E_AQUISICAO`
- `MOBILIDADE_E_DESLOCAMENTO`
- `INVESTIMENTOS_NO_ESCRITORIO`
- `A_CLASSIFICAR`
- Legados aceitos por compatibilidade:
- `ESTRUTURA`
- `PESSOAS`
- `IMPOSTOS`
- `OPERACIONAL`

### `priority`

- `LEGAL`
- `OPERACIONAL`
- `OPCIONAL`

## 1) List expenses

```http
GET /api/expenses/
```

Optional query params:

- `year`
- `month`

Behavior:

1. Always filters by authenticated user's firm.
2. Always returns only `is_active=true`.
3. If `year` and `month` are both sent, response is unpaginated list.
4. Without period filters, default ModelViewSet behavior applies.

## 2) Create expense

```http
POST /api/expenses/
```

Rules:

1. `firm` is set by backend.
2. If `is_installment=true`, installments are generated automatically.
3. Installments are derived from `amount` and `total_installments`.
4. Rounding residue is applied to the last installment.
5. Installment due dates move monthly from `due_date`.

## 3) Retrieve expense by ID

```http
GET /api/expenses/{id}/
```

Returns full expense with embedded installments.

## 4) Update expense

```http
PATCH /api/expenses/{id}/
```

Important behavior:

- Setting `is_paid=true` updates `paid_at` on header and all installments.
- Setting `is_paid=false` clears `paid_at` on header and all installments.

## 5) Delete expense

```http
DELETE /api/expenses/{id}/
```

Removes expense and cascades related installments.

## 6) Bulk import

```http
POST /api/expenses/import/
```

Rules implemented:

1. Payload must be an array.
2. Maximum 500 items per request.
3. Partial processing: one invalid item does not abort entire batch.
4. Response always includes `created` and `errors`.
5. `errors[index]` is 0-based.
6. Backend forces `is_active=true`.
7. If `category` is `null`, backend normalizes to `OPERACIONAL` (legado).
8. If `installment_value` is sent, backend validates consistency with `amount` and `total_installments`.

## 7) Defer installment

```http
POST /api/expenses/defer-installment/{installment_id}/
```

Example payload:

```json
{
  "new_date": "2026-11-15",
  "penalty_amount": 50.00
}
```

Behavior:

1. Creates deferral entry.
2. Updates installment `due_date`.
3. Adds penalty to installment amount when provided.

## 8) Yearly summary

```http
GET /api/expenses/yearly-summary/
```

Returns grouped summary and dashboard section per period, plus total bank balance.

## Frontend Checklist

1. Always send JWT.
2. For import, send array and handle `created` plus `errors`.
3. For installments, keep `amount`, `total_installments`, `installment_value` consistent.
4. For filtered list, send `year` and `month` together.
5. Paid/unpaid state affects all installments.
