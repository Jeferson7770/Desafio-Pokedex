# Expenses API Guide

This document explains how to use the expenses endpoints.

## Base URL and Authentication

```text
/api/expenses/
```

All endpoints require JWT.

```http
Authorization: Bearer <JWT>
Content-Type: application/json
```

---

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/expenses/` | List expenses |
| POST | `/api/expenses/` | Create expense |
| GET | `/api/expenses/{id}/` | Retrieve expense |
| PATCH | `/api/expenses/{id}/` | Update expense |
| DELETE | `/api/expenses/{id}/` | Delete expense |
| POST | `/api/expenses/import/` | Bulk import |
| POST | `/api/expenses/defer-installment/{installment_id}/` | Defer installment |
| GET | `/api/expenses/yearly-summary/` | Yearly summary |

---

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
  "frequency": "MONTHLY",
  "category": "ESTRUTURA_E_OPERACAO",
  "subcategory": "Aluguel",
  "category_display": "Estrutura e Operação",
  "priority": "ALTA",
  "priority_display": "Alta",
  "is_reembolsavel": false,
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

`status` values: `PAGO`, `VENCIDO`, `A_VENCER`.

---

## Enums

### `frequency`

| Value | Description |
|---|---|
| `ONE_TIME` | One-time expense |
| `MONTHLY` | Recurring monthly |
| `ANNUAL` | Recurring annually |

### `category`

| Value | Display |
|---|---|
| `PESSOAL_E_REMUNERACAO` | Pessoal e Remuneração |
| `FISCAL_E_OBRIGACOES_LEGAIS` | Fiscal e Obrigações Legais |
| `CUSTAS_PROCESSUAIS_E_JUDICIAIS` | Custas Processuais e Judiciais |
| `ESTRUTURA_E_OPERACAO` | Estrutura e Operação |
| `TECNOLOGIA_E_ASSINATURA` | Tecnologia e Assinaturas |
| `FINANCEIRA` | Financeiro |
| `MARKETING_E_AQUISICAO` | Marketing e Aquisição |
| `MOBILIDADE_E_DESLOCAMENTO` | Mobilidade e Deslocamento |
| `INVESTIMENTOS_NO_ESCRITORIO` | Investimentos no Escritório |
| `CAPACITACAO_E_DESENVOLVIMENTO` | Capacitação e Desenvolvimento |
| `A_CLASSIFICAR` | A Classificar |

> Expenses created with `A_CLASSIFICAR` appear in the priority engine's `pendentes_categorizacao` list and do not participate in the payment ranking until recategorized.

### `priority`

| Value | Display | Default categories |
|---|---|---|
| `CRITICA` | Crítica | `PESSOAL_E_REMUNERACAO`, `FISCAL_E_OBRIGACOES_LEGAIS` |
| `ESPECIAL` | Especial | `CUSTAS_PROCESSUAIS_E_JUDICIAIS` |
| `ALTA` | Alta | `ESTRUTURA_E_OPERACAO` |
| `MEDIA_ALTA` | Média-Alta | `TECNOLOGIA_E_ASSINATURA` |
| `MEDIA` | Média | `FINANCEIRA`, `MARKETING_E_AQUISICAO` |
| `MEDIA_BAIXA` | Média-Baixa | `MOBILIDADE_E_DESLOCAMENTO` |
| `BAIXA` | Baixa | `INVESTIMENTOS_NO_ESCRITORIO`, `CAPACITACAO_E_DESENVOLVIMENTO` |
| `INDEFINIDA` | Indefinida | `A_CLASSIFICAR` — excluded from priority ranking |

### `subcategory`

Free-text field (max 100 chars). Used by the priority engine to look up specific consequence warnings. Example values: `"Pró-labore"`, `"DAS"`, `"Aluguel"`, `"Software jurídico"`.

### `is_reembolsavel`

Boolean. Applicable to `CUSTAS_PROCESSUAIS_E_JUDICIAIS` expenses where the lawyer advances costs on behalf of a client and expects reimbursement. When `true`, the expense is tracked as a receivable from the client and does not impact net firm result — only cash flow temporarily.

---

## 1. List Expenses

```http
GET /api/expenses/
```

Optional query params: `year`, `month`.

Behavior:
1. Always scoped to the authenticated user's firm.
2. Only returns `is_active=true` expenses.
3. If both `year` and `month` are provided, response is unpaginated.
4. Without period filters, standard paginated ModelViewSet behavior applies.

---

## 2. Create Expense

```http
POST /api/expenses/
```

Rules:
1. `firm` is set automatically by the backend.
2. If `is_installment=true`, installments are generated automatically from `amount` and `total_installments`.
3. Rounding residue is applied to the last installment.
4. Installment due dates advance by one month from `due_date`.
5. If `category` is omitted, defaults to `A_CLASSIFICAR`.
6. If `priority` is omitted, defaults to `INDEFINIDA`.

---

## 3. Retrieve Expense

```http
GET /api/expenses/{id}/
```

Returns the full expense with embedded installments.

---

## 4. Update Expense

```http
PATCH /api/expenses/{id}/
```

Important behavior:
- Setting `is_paid=true` sets `paid_at` on the header record and all installments.
- Setting `is_paid=false` clears `paid_at` on the header record and all installments.

---

## 5. Delete Expense

```http
DELETE /api/expenses/{id}/
```

Deletes the expense and all related installments (cascade).

---

## 6. Bulk Import

```http
POST /api/expenses/import/
Content-Type: application/json
```

Rules:
1. Payload must be a JSON array.
2. Maximum 500 items per request.
3. Partial processing: one invalid item does not abort the entire batch.
4. Response always includes `created` (list) and `errors` (list).
5. `errors[].index` is 0-based.
6. Backend forces `is_active=true` on all imported items.
7. If `category` is `null`, backend defaults to `A_CLASSIFICAR`.
8. If `installment_value` is provided, backend validates: `installment_value × total_installments === amount`.

**Response:**

```json
{
  "created": [ /* list of created expense objects */ ],
  "errors": [
    { "index": 2, "detail": "amount: This field is required." }
  ]
}
```

---

## 7. Defer Installment

```http
POST /api/expenses/defer-installment/{installment_id}/
Content-Type: application/json
```

**Request:**

```json
{
  "new_date": "2026-11-15",
  "penalty_amount": 50.00
}
```

Behavior:
1. Creates a deferral record linked to the installment.
2. Updates `installment.due_date` to `new_date`.
3. Adds `penalty_amount` to the installment amount when provided.

---

## 8. Yearly Summary

```http
GET /api/expenses/yearly-summary/
```

Returns a grouped summary and dashboard data per period, plus total bank balance.

---

## Frontend Checklist

1. Always send JWT.
2. Set `subcategory` on expenses to get specific consequence warnings in the priority engine (`aviso` field).
3. For installments: keep `amount`, `total_installments`, and `installment_value` consistent (`amount = installment_value × total_installments`).
4. For filtered list, send `year` and `month` together.
5. Marking `is_paid` affects all installments simultaneously.
6. Set `is_reembolsavel=true` for `CUSTAS_PROCESSUAIS_E_JUDICIAIS` expenses where the client will reimburse the firm.
7. Expenses with `A_CLASSIFICAR` / `INDEFINIDA` will not appear in the payment priority ranking until categorized.
