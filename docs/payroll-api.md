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

## 4. List pro-labore payment history

```http
GET /api/payroll/
GET /api/payroll/?months=12
```

Returns a list of monthly paid pro-labore history for authenticated user.

Each item includes:

- `month`
- `amount_paid`
- `comparison` (`status`, `difference`, `difference_percentage`)

`months` defaults to `12` and is clamped between `1` and `36`.

## 5. Detailed pro-labore history payload (optional)

```http
GET /api/payroll/history/
GET /api/payroll/history/?months=12
```

Returns a detailed payload with `monthly_history` plus consolidated `summary` and latest suggested value.

Rules:

1. Uses paid expense installments (`is_paid=true`, with `paid_at`) from payroll categories.
2. Categories considered: `PESSOAL_E_REMUNERACAO` and legacy `PESSOAS`.
3. `months` defaults to `12` and is clamped between `1` and `36`.
4. Comparison status:
- `ACIMA_DO_SUGERIDO`
- `ABAIXO_DO_SUGERIDO`
- `ALINHADO_AO_SUGERIDO`
- `SEM_REFERENCIA` (when there is no suggested simulation)

Response example:

```json
{
	"months_window": 12,
	"latest_suggested_pro_labore": 8500.0,
	"monthly_history": [
		{
			"month": "2026-05",
			"amount_paid": 9000.0,
			"comparison": {
				"status": "ACIMA_DO_SUGERIDO",
				"difference": 500.0,
				"difference_percentage": 5.88
			}
		}
	],
	"summary": {
		"total_paid": 9000.0,
		"average_paid": 9000.0,
		"last_paid": 9000.0,
		"comparison": {
			"status": "ACIMA_DO_SUGERIDO",
			"difference": 500.0,
			"difference_percentage": 5.88
		}
	}
}
```

## 6. Stage profiles

- `INICIANTE`
- `INTERMEDIARIO`
- `AVANCADO`

## 7. Prerequisites

- User must have a `LawyerProfile` with `tax_regime`.
- Tax regime is required for INSS and payroll burden calculations.
- Missing profile returns `404`.

## 8. Frontend Checklist

1. Call `POST /api/payroll/` to calculate (no body).
2. Show all three scenarios so user can choose.
3. If `mensagem_alerta` is not `null`, show it prominently.
4. Use `GET /api/payroll/` to display historical paid pro-labore list.
5. Use `GET /api/payroll/history/` only if you need the detailed payload with summary.
