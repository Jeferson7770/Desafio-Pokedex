# Payroll (Pro-Labore) API Guide

This document explains how to consume the payroll simulation endpoint.

## 1. Authentication

```http
Authorization: Bearer <token>
Content-Type: application/json
```

Primary base URL:

```text
/api/payroll/
```

Legacy alias also available:

- `/api/prolabore/`

## 2. What This Endpoint Provides

The payroll endpoint calculates three monthly withdrawal scenarios based on the lawyer financial history and tax regime:

- `conservador`: safer lower withdrawal.
- `equilibrado`: balanced withdrawal.
- `maximo_seguro`: highest safer withdrawal.

Each scenario includes gross amount, partner INSS, partner net amount, employer INSS, and total office cost.

Result is also saved in simulation history.

## 3. Calculate payroll simulation

```http
POST /api/payroll/
```

No request body is required.

Backend uses:

- authenticated lawyer profile (`tax_regime`)
- bank transaction history

Response keeps current field names as implemented.

## 4. List simulation history

```http
GET /api/payroll/
```

Returns all saved simulations for authenticated user, newest first.

## 5. Stage profiles

- `INICIANTE`
- `INTERMEDIARIO`
- `AVANCADO`

## 6. Prerequisites

- User must have a `LawyerProfile` with `tax_regime`.
- Tax regime is required for INSS and payroll burden calculations.
- Missing profile returns `404`.

## 7. Frontend Checklist

1. Call `POST /api/payroll/` to calculate (no body).
2. Show all three scenarios so user can choose.
3. If `mensagem_alerta` is not `null`, show it prominently.
4. Use `GET /api/payroll/` to display historical simulations.
