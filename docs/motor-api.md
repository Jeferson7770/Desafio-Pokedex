# Priority Engine API Guide

This document explains how to consume the payment priority engine (`/api/motor/`) endpoints.

## 1. Authentication

```http
Authorization: Bearer <JWT>
Content-Type: application/json
```

Base URL: `/api/motor/`

---

## 2. What the Priority Engine Does

The engine analyzes current-month firm expenses and suggests a payment order based on the firm's available cash balance (sum of all `BankAccount.current_balance`).

**Core rule:** items are processed strictly in order. The balance decrements after every item — even when it goes negative. This allows the frontend to show exactly how deep in the red a given payment would put the firm.

**Two paths:**
- **Fresh (no saved simulation):** items are auto-sorted by priority + category + late interest per day + due date. The engine processes them sequentially.
- **Saved simulation:** items are processed in the exact user-defined order. New expenses created after saving are appended at the end, sorted by priority.

Expenses with `priority = INDEFINIDA` or `category = A_CLASSIFICAR` are excluded from the ranked list and returned separately in `pendentes_categorizacao`.

---

## 3. Priority Levels

| Priority | Weight | Default categories |
|---|---|---|
| `CRITICA` | 1 | `PESSOAL_E_REMUNERACAO`, `FISCAL_E_OBRIGACOES_LEGAIS` |
| `ESPECIAL` | 2 | `CUSTAS_PROCESSUAIS_E_JUDICIAIS` |
| `ALTA` | 3 | `ESTRUTURA_E_OPERACAO` |
| `MEDIA_ALTA` | 4 | `TECNOLOGIA_E_ASSINATURA` |
| `MEDIA` | 5 | `FINANCEIRA`, `MARKETING_E_AQUISICAO` |
| `MEDIA_BAIXA` | 6 | `MOBILIDADE_E_DESLOCAMENTO` |
| `BAIXA` | 7 | `INVESTIMENTOS_NO_ESCRITORIO`, `CAPACITACAO_E_DESENVOLVIMENTO` |
| `INDEFINIDA` | 99 | `A_CLASSIFICAR` — excluded from ranking |

Tie-breaking within the same priority level: highest late-interest cost per day → earliest due date.

---

## 4. Get Current Month Simulation

```http
GET /api/motor/
Authorization: Bearer <JWT>
```

Returns the current month's prioritization. If a saved simulation exists, it is returned; otherwise the engine computes a fresh auto-sorted one.

**Response `200`:**

```json
{
  "id": 1,
  "reference_period": "2026-06",
  "saldo_total_disponivel": 3000.00,
  "saldo_restante_pos_pagamentos": -13000.00,
  "pagamentos_recomendados": [
    {
      "tipo": "despesa",
      "parcela": 15,
      "outra_entrada_installment_id": null,
      "expense_title": "Pró-labore Sócio",
      "category": "PESSOAL_E_REMUNERACAO",
      "priority": "CRITICA",
      "priority_label": "Crítica",
      "due_date": "2026-06-10",
      "amount_snapshot": 2000.00,
      "late_interest_snapshot": 0.00,
      "status_recomendacao": "RECOMENDADO",
      "saldo_pos_pagamento": 1000.00,
      "aviso": "Ação trabalhista com multa de 40% sobre FGTS + 1 mês de aviso prévio por ano trabalhado."
    }
  ],
  "pagamentos_nao_cobertos": [
    {
      "tipo": "despesa",
      "parcela": 22,
      "outra_entrada_installment_id": null,
      "expense_title": "Compra de Notebooks",
      "category": "INVESTIMENTOS_NO_ESCRITORIO",
      "priority": "BAIXA",
      "priority_label": "Baixa",
      "due_date": "2026-06-15",
      "amount_snapshot": 5000.00,
      "late_interest_snapshot": 0.00,
      "status_recomendacao": "NAO_COBERTO",
      "saldo_pos_pagamento": -4000.00,
      "aviso": "Retomada do bem em contratos com alienação fiduciária (equipamentos financiados)."
    }
  ],
  "pendentes_categorizacao": [
    {
      "tipo": "despesa",
      "parcela": 31,
      "outra_entrada_installment_id": null,
      "expense_title": "Unknown Expense",
      "category": "A_CLASSIFICAR",
      "priority": "INDEFINIDA",
      "priority_label": "Indefinida",
      "due_date": "2026-06-20",
      "amount_snapshot": 800.00,
      "late_interest_snapshot": 0.00,
      "aviso": "Expense without category — the priority engine cannot calculate risk or display alerts. Categorize to activate the engine."
    }
  ]
}
```

### Response fields

| Field | Description |
|---|---|
| `id` | `null` if no simulation is saved; integer if a saved simulation exists |
| `saldo_total_disponivel` | Current total bank balance (sum of all accounts) |
| `saldo_restante_pos_pagamentos` | Balance after processing all ranked items (can be negative) |
| `pagamentos_recomendados` | Items where balance was ≥ amount at the time of processing |
| `pagamentos_nao_cobertos` | Items where balance was < amount at the time of processing |
| `pendentes_categorizacao` | Items with `INDEFINIDA` priority or `A_CLASSIFICAR` category — excluded from ranking |

### Per-item fields

| Field | Description |
|---|---|
| `tipo` | `"despesa"` or `"outra_entrada"` |
| `parcela` | `ParcelaDespesa.id` (null for `outra_entrada`) |
| `outra_entrada_installment_id` | `OutraEntradaInstallment.id` (null for `despesa`) |
| `expense_title` | Expense or income entry title |
| `category` | Category code |
| `priority` | Priority code |
| `priority_label` | Human-readable priority (e.g. `"Crítica"`, `"Alta"`) |
| `due_date` | Due date `"YYYY-MM-DD"` |
| `amount_snapshot` | Amount at the time of simulation |
| `late_interest_snapshot` | Late interest accrued at the time of simulation |
| `status_recomendacao` | `"RECOMENDADO"` or `"NAO_COBERTO"` (absent on `pendentes_categorizacao` items) |
| `saldo_pos_pagamento` | Running balance **after** this item is deducted (absent on `pendentes_categorizacao` items) — can be negative |
| `aviso` | Consequence warning for non-payment, looked up from `avisos_prioridade.json` by category + subcategory |

### Running balance example

With `saldo_total_disponivel = 3000`:

| # | Item | Amount | `saldo_pos_pagamento` | `status_recomendacao` |
|---|---|---|---|---|
| 1 | Pró-labore | 2000 | 1000 | RECOMENDADO |
| 2 | Aluguel | 5000 | -4000 | NAO_COBERTO |
| 3 | DAS | 4000 | -8000 | NAO_COBERTO |
| 4 | Notebooks | 5000 | -13000 | NAO_COBERTO |

---

## 5. Save Custom Order

```http
POST /api/motor/salvar-configuracao/
Authorization: Bearer <JWT>
Content-Type: application/json
```

Persists the user-defined payment order. The exact array order is preserved.

**Request:**

```json
{
  "pagamentos_recomendados": [
    { "parcela": 15, "status_recomendacao": "RECOMENDADO", ... },
    { "parcela": 22, "status_recomendacao": "RECOMENDADO", ... }
  ],
  "pagamentos_nao_cobertos": [
    { "parcela": 31, "status_recomendacao": "NAO_COBERTO", ... }
  ]
}
```

The backend concatenates both arrays (`recomendados + nao_cobertos`) and recomputes `status_recomendacao` and `saldo_pos_pagamento` from scratch using the current bank balance. The frontend's `status_recomendacao` values in the request payload are ignored for the computation — only the order matters.

**Response `201`:** the saved `SimulacaoPrioridade` object.

**Behavior:**
1. Deletes any existing simulation for the current month.
2. Recomputes each item's status sequentially using current balance.
3. Always deducts, even when `NAO_COBERTO` — so subsequent items correctly show negative balance.
4. New items not included in the payload will appear auto-sorted by priority on the next `GET /api/motor/`.
5. Empty payload returns `400`.

---

## 6. Consequence Warnings (`aviso`)

Each item includes an `aviso` field containing a human-readable description of the consequences of not paying that expense. This is driven by `src/motor/utils/avisos_prioridade.json`.

Lookup priority:
1. **Subcategory match** — `expense.subcategory` normalized (lowercase, no accents) → looked up in the category's dict.
2. **Category fallback** — if subcategory not found or blank, uses `_aviso_padrao` for the category.
3. `null` if the category has no entry in the JSON.

Example subcategory values that trigger specific warnings: `"DAS"`, `"Pró-labore"`, `"Aluguel"`, `"Software jurídico"`, `"Domínio"`, etc.

To add or adjust consequence messages, edit `src/motor/utils/avisos_prioridade.json` directly — no code change needed.

---

## 7. Frontend Integration Checklist

1. On load, call `GET /api/motor/` to get the current simulation.
2. Display `saldo_total_disponivel` as the starting balance.
3. For each item, display `saldo_pos_pagamento` as the running balance after that payment — use negative values to show the firm would be in deficit.
4. Use `status_recomendacao` to style items: green checkmark for `RECOMENDADO`, red warning for `NAO_COBERTO`.
5. Show `aviso` below the item to communicate payment risk to the user.
6. Show `priority_label` as a badge (e.g. "Crítica", "Alta").
7. Items in `pendentes_categorizacao` should be shown in a separate section with a prompt to categorize them.
8. When the user reorders items, call `POST /api/motor/salvar-configuracao/` with the full ordered array (both recommended and not-covered combined in user order).
9. After saving, re-fetch `GET /api/motor/` to get the recomputed balances.
10. The response is cached for 30 minutes. Saving a new configuration invalidates the cache automatically.
