# Fees API Guide

This document explains how frontend clients should consume fees endpoints.

## 1. Authentication

All endpoints require JWT token:

```http
Authorization: Bearer <token>
Content-Type: application/json
```

Base URL:

```text
/api/fees/
```

Legacy alias also available in routes:

- `/api/honorarios/`

## 2. Important Integration Rules

1. Multi-tenant by firm: backend always resolves authenticated user's firm.
2. Date filter (`year` and/or `month`) is optional in list endpoint and filters by installment `due_date`.
3. For installment fees:
   - installments are generated automatically on `POST`;
   - changing header status syncs all installments;
   - use installment endpoint for per-installment updates.
4. Changing `amount`, `date`, or `total_installments` recreates all installments.
5. `installment_value` is read-only and computed by backend.
6. `late_interest_cost` is computed dynamically per installment.

## 3. Data Structure

### Fee

```json
{
  "id": 1,
  "title": "Employment contract - Client X",
  "amount": "9000.00",
  "date": "2026-06-01",
  "status": "PENDENTE",
  "notes": "",
  "is_installment": true,
  "total_installments": 3,
  "installment_value": 3000.0,
  "interest_rate_month": "2.00",
  "created_at": "2026-06-04T10:00:00Z",
  "installments": [
    {
      "id": 101,
      "installment_number": 1,
      "amount": "3000.00",
      "due_date": "2026-06-01",
      "status": "PENDENTE",
      "late_interest_cost": "0.00",
      "paid_at": null
    }
  ]
}
```

Status values (as implemented):

- Header: `PENDENTE`, `RECEBIDO`
- Installment: `PENDENTE`, `RECEBIDO`

## 4. List fees

```http
GET /api/fees/
GET /api/fees/?year=2026&month=6
GET /api/fees/?year=2026
```

## 5. Create fee

```http
POST /api/fees/
```

Single payment example:

```json
{
  "title": "Legal consultation",
  "amount": "1500.00",
  "date": "2026-06-10",
  "status": "PENDENTE",
  "notes": "",
  "is_installment": false,
  "total_installments": 1,
  "interest_rate_month": "0.00"
}
```

Installment example:

```json
{
  "title": "Labor contract",
  "amount": "9000.00",
  "date": "2026-06-01",
  "status": "PENDENTE",
  "notes": "",
  "is_installment": true,
  "total_installments": 3,
  "interest_rate_month": "2.00"
}
```

## 6. Update fee header

```http
PATCH /api/fees/{id}/
```

- Updating `status` on header synchronizes all installments.
- Updating structure (`amount`, `date`, `total_installments`) recreates installments.

## 7. Update single installment

```http
PATCH /api/fees/{id}/installments/{installment_id}/
```

Example mark as received:

```json
{
  "status": "RECEBIDO",
  "paid_at": "2026-06-04T14:00:00Z"
}
```

## 8. Delete fee

```http
DELETE /api/fees/{id}/
```

Removes fee and all installments.

## 9. Bulk import

```http
POST /api/fees/import/
```

Rules:

1. Max 500 items per request.
2. Partial success processing.
3. Response includes `created` and `errors`.

## 10. Frontend Checklist

1. Always send token.
2. Do not send `installment_value` on POST.
3. Use installment endpoint for single-installment status changes.
4. Use header `status` to update all installments at once.
5. Handle `400` validation errors per field/message.
