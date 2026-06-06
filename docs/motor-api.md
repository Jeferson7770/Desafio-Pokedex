# Priority Engine API Guide

This document explains how to consume payment-priority engine endpoints.

## 1. Authentication

```http
Authorization: Bearer <token>
Content-Type: application/json
```

Base URL:

```text
/api/motor/
```

## 2. What the Priority Engine Does

The priority engine analyzes current-month firm expenses and suggests payment order based on available cash balance. It separates items into two groups:

- `pagamentos_recomendados`: expenses covered by available balance.
- `pagamentos_nao_cobertos`: expenses that exceed available balance.

Frontend can reorder cards and persist custom configuration.

## 3. Data Structure

### `SimulacaoPrioridade`

```json
{
  "id": 1,
  "reference_period": "2026-06",
  "saldo_total_disponivel": "22400.00",
  "saldo_restante_pos_pagamentos": "5200.00",
  "created_at": "2026-06-04T10:00:00Z",
  "pagamentos_recomendados": [],
  "pagamentos_nao_cobertos": []
}
```

Recommendation status values:

- `RECOMENDADO`
- `NAO_COBERTO`

## 4. Calculate priorities dynamically

```http
GET /api/motor/
```

Returns current-month prioritization without persisting.

## 5. Save custom configuration

```http
POST /api/motor/salvar-configuracao/
```

Behavior:

1. Preserves exact array order from payload.
2. Creates or overwrites current-month simulation for the firm.
3. Returns saved object.

## 6. Frontend Checklist

1. On load, call `GET /api/motor/`.
2. On user confirmation, call `POST /api/motor/salvar-configuracao/` with both arrays.
3. Ensure payload includes all cards across both arrays.
4. Empty payload returns validation error.
5. Keep snapshot values aligned with UI values.
