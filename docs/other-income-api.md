# Other Income API Guide

This document explains how frontend clients should consume Other Income endpoints.

## 1. Authentication

All endpoints require JWT token:

```http
Authorization: Bearer <token>
Content-Type: application/json
```

Base URL:

```text
/api/other-income/
```

Legacy alias also available:

- `/api/outras-entradas/`

## 2. Important Integration Rules

1. Multi-tenant by firm: backend always uses authenticated user's firm.
2. Date filter is mandatory only for list endpoint.
3. In list endpoint, send either:
   - `year` + `month`, or
   - `start_date` + `end_date`.
4. For installment records:
   - installments are generated on header `POST`;
   - header status is derived from installments;
   - do not patch header status directly for installment records.
5. If all installments are `RECEBIDO`, header becomes `RECEBIDO`.
6. If any installment is `PENDENTE`, header becomes `PENDENTE`.
7. A fixed-value record can be converted to installment mode via `PATCH`.
8. Changing structural fields (`total_installments`, `installment_value`, `date`, `amount`) recreates installments.

## 3. List records

```http
GET /api/other-income/?year=2026&month=6
GET /api/other-income/?start_date=2026-06-01&end_date=2026-06-30
```

Common list errors:

- Missing filters.
- Partial year/month or partial start/end pair.
- Mixing year/month with start/end range.

## 4. Create record

```http
POST /api/other-income/
```

Supports fixed and installment payloads. For installment payloads, backend creates installments automatically from `date`, `installment_value`, and `total_installments`.

## 5. Update header

```http
PATCH /api/other-income/{id}/
```

Behavior highlights:

- For non-installment records, header status update syncs single installment.
- Converting fixed to installment recreates installments.
- For installment records, changing structural fields recreates installments.

## 6. Update single installment

```http
PATCH /api/other-income/{id}/installments/{installment_id}/
```

After this patch, backend recalculates header status automatically.

## 7. Delete record

```http
DELETE /api/other-income/{id}/
```

Deletes header and cascades related installments.

## 8. Bulk import

```http
POST /api/other-income/import/
```

Behavior:

1. Payload must be an array.
2. Partial processing (`created` + `errors`).
3. Max 500 items per request.

## 9. Frontend Checklist

1. Always send token.
2. In list endpoint, always provide a valid filter pair.
3. Retrieve/update/delete by ID do not require date filters.
4. For installment status, update by installment endpoint.
5. For fixed -> installment conversion, send `is_installment: true` plus structural fields.
6. Handle `400` validation errors at field/message level.
7. For import, handle `created` and `errors` together.
