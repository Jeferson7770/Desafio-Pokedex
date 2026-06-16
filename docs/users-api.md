# Users API Guide

This document covers authentication, lawyer profile, billing, and notification settings endpoints.

## Base URLs

All users endpoints are under `/api/auth/`:

```text
POST /api/auth/register/
POST /api/auth/login/
POST /api/auth/logout/
GET|POST|PATCH|PUT|DELETE /api/auth/laywer-profile/
POST /api/auth/laywer-profile/change-password/
POST /api/auth/laywer-profile/disconnect-device/{device_pk}/
POST /api/auth/laywer-profile/disconnect-all-devices/
POST /api/auth/laywer-profile/delete-account/
GET  /api/auth/billing/subscription/
POST /api/auth/billing/cancel/
GET|PATCH /api/auth/notifications/settings/
```

---

## 1. Register

```http
POST /api/auth/register/
```

No authentication required.

Backend creates `User` and `LawyerProfile` in one atomic transaction. It also:
- Auto-creates a `Firm` if firm details are provided.
- Creates a `FirmSubscription` with `status=TRIAL` and `trial_ends_at=now+7days`.
- Sends a welcome email in a background thread (via Resend).

---

## 2. Login

```http
POST /api/auth/login/
```

No authentication required. Returns `access` and `refresh` JWT tokens.

---

## 3. Logout

```http
POST /api/auth/logout/
Authorization: Bearer <JWT>
```

Invalidates the refresh token.

---

## 4. Google OAuth

### Register with Google

```http
POST /api/auth/google/register/
```

Creates a new account using Google identity. Sends welcome email on first registration.

### Login with Google

```http
POST /api/auth/google/login/
```

Returns `access` and `refresh` tokens for an existing Google-authenticated account.

---

## 5. Lawyer Profile

### 5.1 Retrieve profile

```http
GET /api/auth/laywer-profile/
Authorization: Bearer <JWT>
```

Returns the full profile: personal data, firm info, billing status, connected devices, and notification settings.

### 5.2 Create profile

```http
POST /api/auth/laywer-profile/
Authorization: Bearer <JWT>
```

Used during onboarding. A second profile for the same user is not allowed.

### 5.3 Update profile

```http
PATCH /api/auth/laywer-profile/
PUT  /api/auth/laywer-profile/
Authorization: Bearer <JWT>
```

### 5.4 Delete profile

```http
DELETE /api/auth/laywer-profile/
Authorization: Bearer <JWT>
```

### 5.5 Change password

```http
POST /api/auth/laywer-profile/change-password/
Authorization: Bearer <JWT>
```

Behavior:
1. Validates current password.
2. Updates the password.
3. Invalidates all active refresh tokens.
4. Returns new `access` and `refresh` tokens.

### 5.6 Disconnect one device

```http
POST /api/auth/laywer-profile/disconnect-device/{device_pk}/
Authorization: Bearer <JWT>
```

### 5.7 Disconnect all devices

```http
POST /api/auth/laywer-profile/disconnect-all-devices/
Authorization: Bearer <JWT>
```

### 5.8 Delete account

```http
POST /api/auth/laywer-profile/delete-account/
Authorization: Bearer <JWT>
```

Irreversible. Deletes user and all associated data.

---

## 6. Profile Enums

### Tax regime (`tax_regime`)

| Value |
|---|
| `SIMPLES` |
| `LUCRO_PRESUMIDO` |
| `LUCRO_REAL` |
| `AUTONOMO_PF` |

### Income variability (`income_variability`)

| Value |
|---|
| `LOW` |
| `MEDIUM` |
| `HIGH` |

### Financial goal (`goal_type`)

| Value |
|---|
| `SURVIVAL` |
| `STABILITY` |
| `GROWTH` |

---

## 7. Billing

The `billing` object is returned as part of `GET /api/auth/laywer-profile/`.

For the full billing reference — including trial flow, all scenarios, field descriptions, and access control logic — see [stripe-payment.md](stripe-payment.md).

### 7.1 View current subscription

```http
GET /api/auth/billing/subscription/
Authorization: Bearer <JWT>
```

Returns the current `FirmSubscription` record.

Possible `status` values: `TRIAL`, `PENDING`, `ACTIVE`, `CANCELLED`, `EXPIRED`.

### 7.2 Cancel subscription

```http
POST /api/auth/billing/cancel/
Authorization: Bearer <JWT>
Content-Type: application/json
```

**Request:**

```json
{
  "reason": "preco",
  "feedback": "The price is too high for small offices."
}
```

Both fields are optional.

**Response `200`:**

```json
{ "detail": "Assinatura cancelada ao fim do período." }
```

Calls Stripe with `cancel_at_period_end=True`. Access continues until `current_period_end`. Status transitions to `CANCELLED` when the `customer.subscription.deleted` webhook arrives after the period ends.

**Errors:**
- `403` — subscription is not `ACTIVE`
- `400` — no `stripe_subscription_id` on record

### 7.3 Request upgrade (placeholder)

```http
POST /api/auth/billing/subscription/upgrade/
Authorization: Bearer <JWT>
```

Currently returns `501` (gateway integration pending).

---

## 8. Password Reset

Three-step flow: request code → verify code → set new password.

For the full spec see [password-reset.md](password-reset.md).

```text
POST /api/auth/password/forgot/
POST /api/auth/password/verify-code/
POST /api/auth/password/reset/
```

---

## 9. Notification Settings

### Retrieve

```http
GET /api/auth/notifications/settings/
Authorization: Bearer <JWT>
```

### Update

```http
PATCH /api/auth/notifications/settings/
Authorization: Bearer <JWT>
```

---

## 10. Frontend Checklist

1. Startup flow: `register` → `login` → store tokens → `POST /api/auth/laywer-profile/` (onboarding).
2. Use SimpleJWT refresh endpoint (`/api/token/refresh/`) to renew the `access` token.
3. After password change, replace stored tokens immediately with the new ones from the response.
4. Gate app access on `billing.is_premium_active`, not on `billing.status` alone.
5. Show trial banner when `billing.is_on_trial === true`, with `billing.trial_ends_at` as the expiry date.
6. `has_bank_connected` indicates Open Finance connection status.
7. `onboarding_completed` indicates whether the onboarding wizard has been finished.
