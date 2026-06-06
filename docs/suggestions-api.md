# Suggestions API Guide

This document explains how to consume suggestion and feedback endpoints.

## 1. Authentication

```http
Authorization: Bearer <token>
Content-Type: application/json
```

Base URL:

```text
/api/suggestions/
```

## 2. Module Purpose

Suggestions module allows platform users to submit feedback, report bugs, and request new features directly in the app. Each suggestion is linked to the authenticated user's firm.

## 3. Data Structure

### Suggestion

```json
{
  "id": 1,
  "name": "Maria da Silva",
  "email": "maria@example.com",
  "category": "NOVA_FUNC",
  "category_display": "Nova Funcionalidade",
  "subject": "Export report as PDF",
  "message": "It would be useful to export monthly report to PDF for partners.",
  "created_at": "2026-06-04T10:00:00Z"
}
```

Category values:

- `MELHORIA`
- `NOVA_FUNC`
- `BUG`
- `OUTRO`

## 4. List suggestions

```http
GET /api/suggestions/
```

Returns firm-scoped suggestions ordered by newest first.

## 5. Create suggestion

```http
POST /api/suggestions/
```

## 6. Retrieve suggestion by ID

```http
GET /api/suggestions/{id}/
```

## 7. Update suggestion

```http
PATCH /api/suggestions/{id}/
```

## 8. Delete suggestion

```http
DELETE /api/suggestions/{id}/
```

## 9. Frontend Checklist

1. Always send token.
2. `name` and `email` represent sender identity; can be prefilled from logged-in profile.
3. `category_display` is localized backend label; display it directly in UI.
4. Suggestions are firm-isolated.
