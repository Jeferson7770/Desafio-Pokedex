# Firms API Guide (Law Offices)

This document explains how to consume firm and member endpoints.

## 1. Authentication

```http
Authorization: Bearer <token>
Content-Type: application/json
```

Base URL:

```text
/api/firms/
```

## 2. Important Rules

1. A user can belong to multiple firms, but current backend behavior uses the first membership.
2. When creating a firm, the creator is automatically assigned as `OWNER`.
3. A user can only see firms where they are a member.

## 3. Data Structures

### Firm

```json
{
  "id": 10,
  "name": "Silva & Partners",
  "type": "OFFICE",
  "created_at": "2026-01-10T10:00:00Z"
}
```

`type` values:

- `SOLO`
- `OFFICE`

### FirmMember

```json
{
  "id": 5,
  "user": 2,
  "user_email": "joao@example.com",
  "role": "LAWYER",
  "created_at": "2026-02-01T10:00:00Z"
}
```

`role` values:

- `OWNER`
- `LAWYER`
- `STAFF`

## 4. List firms

```http
GET /api/firms/
```

Returns firms where authenticated user is a member.

## 5. Create firm

```http
POST /api/firms/
```

```json
{
  "name": "Souza Law",
  "type": "SOLO"
}
```

The creator is added as `OWNER` automatically. On creation, the backend also creates a `FirmSubscription` with `status=TRIAL` and `trial_ends_at=now+7days` — no credit card required. See [stripe-payment.md](stripe-payment.md) for the full trial and billing flow.

## 6. Retrieve firm

```http
GET /api/firms/{id}/
```

## 7. Update firm

```http
PATCH /api/firms/{id}/
```

## 8. Delete firm

```http
DELETE /api/firms/{id}/
```

Deletes the firm and related data by cascade.

## 9. List members

```http
GET /api/firms/{id}/members/
```

Returns all firm members.

## 10. Add member

```http
POST /api/firms/{id}/add_member/
```

```json
{
  "user": 5,
  "role": "STAFF"
}
```

## 11. Frontend Checklist

1. Always send auth token.
2. New firm creator becomes `OWNER` automatically.
3. To invite members, call `POST /api/firms/{id}/add_member/`.
4. Handle validation errors as field-level feedback.
