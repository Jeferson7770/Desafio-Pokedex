# Users API Guide

This document explains authentication, lawyer profile, billing, and notification settings endpoints.

## 1. Base URLs

```text
/api/users/register/
/api/users/login/
/api/users/logout/
/api/users/laywer-profile/
/api/users/billing/subscription/
/api/users/notifications/settings/
```

## 2. Register

```http
POST /api/users/register/
```

No authentication required.

Backend creates `User` and `LawyerProfile` in one atomic transaction.

## 3. Login

```http
POST /api/users/login/
```

No authentication required.

Returns `access` and `refresh` tokens.

## 4. Logout

```http
POST /api/users/logout/
```

Requires authentication and invalidates refresh token.

## 5. Lawyer profile

### 5.1 Retrieve profile

```http
GET /api/users/laywer-profile/
```

Returns full profile including personal data, office profile, billing data, devices, and notification settings.

### 5.2 Create profile

```http
POST /api/users/laywer-profile/
```

Used in onboarding. A second profile for same user is not allowed.

### 5.3 Update profile

```http
PATCH /api/users/laywer-profile/
PUT /api/users/laywer-profile/
```

### 5.4 Change password

```http
POST /api/users/laywer-profile/change-password/
```

Behavior:

1. Validates current password.
2. Updates password.
3. Invalidates all active refresh tokens.
4. Returns new `access` and `refresh` tokens.

### 5.5 Disconnect one device

```http
POST /api/users/laywer-profile/disconnect-device/{device_pk}/
```

### 5.6 Disconnect all devices

```http
POST /api/users/laywer-profile/disconnect-all-devices/
```

### 5.7 Delete account

```http
POST /api/users/laywer-profile/delete-account/
```

Irreversible operation.

## 6. Tax regimes

- `SIMPLES`
- `LUCRO_PRESUMIDO`
- `LUCRO_REAL`
- `AUTONOMO_PF`

## 7. Profile variables

### Income variability (`income_variability`)

- `LOW`
- `MEDIUM`
- `HIGH`

### Financial goal (`goal_type`)

- `SURVIVAL`
- `STABILITY`
- `GROWTH`

## 8. Billing

### 8.1 Current subscription

```http
GET /api/users/billing/subscription/
```

Possible statuses: `ACTIVE`, `CANCELED`, `PAST_DUE`, `TRIALING`.

`is_premium_active` is true for active/trial subscriptions and also for canceled subscriptions still inside paid period.

### 8.2 Request upgrade

```http
POST /api/users/billing/subscription/upgrade/
```

Currently returns `501` (gateway integration pending).

### 8.3 Request cancellation

```http
POST /api/users/billing/subscription/cancel/
```

Currently returns `501` (gateway integration pending).

## 9. Notification settings

### 9.1 Retrieve settings

```http
GET /api/users/notifications/settings/
```

### 9.2 Update settings

```http
PATCH /api/users/notifications/settings/
```

## 10. Frontend Checklist

1. Startup flow: register -> login -> store tokens -> create profile (onboarding).
2. Refresh `access` using SimpleJWT refresh endpoint (`/api/token/refresh/`).
3. After password change, replace old tokens immediately.
4. `has_bank_connected` indicates Open Finance connection.
5. `onboarding_completed` indicates onboarding completion state.
6. Upgrade/cancel billing endpoints currently return `501`.
