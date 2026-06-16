# Password Reset — Implementation Spec

Complete password recovery flow via email with a 6-digit code. The user does not click a link — they type the code directly in the app.

---

## 1. User Flow

```
[Login screen]
      │
      ▼
"Forgot my password"
      │
      ▼
[1] Enter email
      │
      ▼  POST /api/auth/password/forgot/
      │
      ▼
Receives email with 6-digit code (expires in 15 min)
      │
      ▼
[2] Enter code in app
      │
      ▼  POST /api/auth/password/verify-code/
      │
      ▼
Receives temporary reset_token
      │
      ▼
[3] Set new password
      │
      ▼  POST /api/auth/password/reset/
      │
      ▼
Password updated → redirected to login
```

---

## 2. Data Model

### `PasswordResetCode`

New model in `src/users/models/password_reset.py`:

```python
import uuid
from django.db import models
from django.utils import timezone
from .user import User

EXPIRY_MINUTES = 15
MAX_ATTEMPTS = 5


class PasswordResetCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="password_reset_codes")
    code_hash = models.CharField(max_length=64)           # HMAC-SHA256 of the code
    reset_token = models.UUIDField(null=True, blank=True) # filled after successful verification
    is_verified = models.BooleanField(default=False)
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def is_expired(self):
        return timezone.now() > self.expires_at

    def is_valid(self):
        return not self.is_used and not self.is_expired() and self.attempts < MAX_ATTEMPTS
```

**Why HMAC for the code?**
The 6-digit code is stored as `HMAC-SHA256(code, SECRET_KEY)` — if the database leaks, active codes cannot be recovered.

**Why a separate `reset_token`?**
After verifying the code, the frontend needs a token for step 3. A UUID ensures the 6-digit code does not circulate beyond what is necessary.

---

## 3. Endpoints

### 3.1 `POST /api/auth/password/forgot/`

Requests delivery of the recovery code.

**Permission:** AllowAny  
**Rate limit:** 3 requests per IP/minute + 3 per email/hour

**Request:**
```json
{ "email": "lawyer@office.com" }
```

**Internal logic:**
1. Looks up `User` by email.
2. If not found → returns `200` with a generic response (does not reveal whether the email exists).
3. If user registered via Google (no usable password) → returns `200` with specific instructions.
4. Invalidates all previous unused codes for the same user (marks `is_used=True`).
5. Generates a random 6-digit numeric code (`secrets.randbelow`).
6. Saves `PasswordResetCode` with `code_hash = HMAC(code)` and `expires_at = now + 15min`.
7. Sends `EmailService().enviar_codigo_reset(email, name, code)` in a background thread.
8. Tracks `senha_reset_solicitado` in PostHog.

**Response `200` (all cases — never reveals whether email exists):**
```json
{
  "detail": "If this email is registered, you will receive a code shortly."
}
```

**Special case — Google account (response `200`):**
```json
{
  "detail": "This account was created with Google. Sign in using the 'Continue with Google' button.",
  "method": "google"
}
```

---

### 3.2 `POST /api/auth/password/verify-code/`

Validates the 6-digit code and returns a token for the password reset step.

**Permission:** AllowAny  
**Rate limit:** 10 requests per IP/minute (primary protection is `MAX_ATTEMPTS` in the DB)

**Request:**
```json
{
  "email": "lawyer@office.com",
  "code": "482917"
}
```

**Internal logic:**
1. Finds the most recent valid `PasswordResetCode` for the email (`is_used=False`, not expired, `attempts < MAX_ATTEMPTS`).
2. If not found → `400`.
3. Computes `HMAC(provided_code)` and compares to `code_hash`.
4. If invalid: increments `attempts`, saves. If `attempts >= MAX_ATTEMPTS`, returns lockout error.
5. If valid: generates `reset_token = uuid4()`, saves with `is_verified=True`.
6. Tracks `senha_codigo_verificado` in PostHog.
7. Returns `reset_token`.

**Response `200`:**
```json
{
  "reset_token": "a3f8c2d1-7b4e-4f9a-8c1d-2e3f4a5b6c7d"
}
```

**Errors:**
```json
// incorrect code (attempts remaining)
{ "detail": "Incorrect code. You have X attempt(s) remaining." }

// code expired
{ "detail": "This code has expired. Request a new one." }

// locked out
{ "detail": "Too many incorrect attempts. Request a new code." }

// no active code found
{ "detail": "No active code found for this email." }
```

---

### 3.3 `POST /api/auth/password/reset/`

Resets the password using the `reset_token` obtained in the previous step.

**Permission:** AllowAny  
**Rate limit:** 5 requests per IP/minute

**Request:**
```json
{
  "reset_token": "a3f8c2d1-7b4e-4f9a-8c1d-2e3f4a5b6c7d",
  "new_password": "MyNewStr0ng@Pass"
}
```

**Internal logic:**
1. Looks up `PasswordResetCode` by `reset_token` where `is_verified=True`, `is_used=False`, and not expired.
2. If not found → `400`.
3. Validates `new_password` with `validate_password_strength()` (8–16 chars, uppercase, lowercase, digit, special character).
4. Calls `user.set_password(new_password)` and `user.save()`.
5. Marks code as `is_used=True`.
6. Invalidates all active refresh tokens for the user (clears open sessions) via `OutstandingToken`.
7. Tracks `senha_redefinida` in PostHog.

**Response `200`:**
```json
{
  "detail": "Password updated successfully. Sign in with your new password."
}
```

**Errors:**
```json
// invalid, expired, or already used token
{ "detail": "Reset link is invalid or expired. Request a new code." }

// weak password
{ "new_password": ["Password must be between 8 and 16 characters"] }
```

---

## 4. Files to Create / Modify

```
src/users/
├── models/
│   └── password_reset.py          ← new: PasswordResetCode
├── views/
│   └── password_reset.py          ← new: ForgotPasswordView, VerifyCodeView, ResetPasswordView
├── services/
│   └── email_service.py           ← add: enviar_codigo_reset()
└── urls.py                        ← add: 3 routes
```

Routes to add in `src/users/urls.py`:

```python
from .views.password_reset import ForgotPasswordView, VerifyCodeView, ResetPasswordView

path('password/forgot/', ForgotPasswordView.as_view()),
path('password/verify-code/', VerifyCodeView.as_view()),
path('password/reset/', ResetPasswordView.as_view()),
```

---

## 5. Email — Recovery Code

Sent via `EmailService.enviar_codigo_reset(user_email, user_name, code)`.

### Design

Follows brand colors (same pattern as the welcome email):

```
┌─────────────────────────────────────────┐
│  [header #0D1117 dark]                  │
│       Fince.  ← lime green logo         │
│         Password recovery               │
│   "Hi, {name}! We received your        │
│    password reset request."             │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│  Your verification code:                │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │                                   │  │
│  │      4  8  2  9  1  7             │  │
│  │  (dark bg, lime green digits)     │  │
│  │                                   │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ⏱ This code expires in 15 minutes.    │
│                                         │
│  If you did not request a password     │
│  reset, you can safely ignore this      │
│  email.                                 │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│  © 2026 Fince · suafince.com.br        │
└─────────────────────────────────────────┘
```

**Code visual:**
- Background: `#0D1117` (dark navy)
- Digits: `#B2E62A` (lime green), monospace, 40px, spaced
- Border-radius: 14px
- Each digit separated for easy reading on mobile

---

## 6. Security

| Protection | Mechanism |
|---|---|
| Do not reveal if email exists | Generic `200` response on `/forgot/` |
| Brute-force protection | `MAX_ATTEMPTS = 5` — locks the code after 5 wrong attempts |
| Expiring code | `expires_at = now + 15 min` — never reusable after |
| Hashed code | `HMAC-SHA256(code, SECRET_KEY)` stored in DB |
| Single-use token | `is_used=True` immediately after `/reset/` |
| IP rate limiting | `django-ratelimit` on all 3 routes |
| Session invalidation | `OutstandingToken.objects.filter(user=user).delete()` on `/reset/` |
| Google OAuth | Detects `has_usable_password()` and responds with specific instructions |
| Parallel codes | `/forgot/` invalidates previous codes before creating a new one |

---

## 7. PostHog Events

| Event | When | Properties |
|---|---|---|
| `senha_reset_solicitado` | Email sent successfully | `user_id`, `method: "email"` |
| `senha_reset_google_bloqueado` | Google user attempts reset | `user_email` |
| `senha_codigo_verificado` | Code correct | `user_id` |
| `senha_codigo_falha` | Code wrong | `user_id`, `attempts_remaining` |
| `senha_codigo_bloqueado` | MAX_ATTEMPTS reached | `user_id` |
| `senha_redefinida` | Password changed successfully | `user_id` |

---

## 8. Migration

After creating the model, run:

```bash
python manage.py makemigrations users --name add_password_reset_code
python manage.py migrate

# Railway:
railway run python manage.py migrate
```

---

## 9. Implementation Checklist

- [ ] Create `src/users/models/password_reset.py` with `PasswordResetCode`
- [ ] Register the model in `src/users/models/__init__.py`
- [ ] Create and apply migration locally + Railway
- [ ] Create `src/users/views/password_reset.py` with `ForgotPasswordView`, `VerifyCodeView`, `ResetPasswordView`
- [ ] Add `enviar_codigo_reset()` to `email_service.py` with HTML code template
- [ ] Register 3 routes in `src/users/urls.py`
- [ ] Test full flow: request → receive email → verify → reset → login with new password
- [ ] Test Google OAuth case (should return specific message)
- [ ] Test expiration (test with 15-min expired code)
- [ ] Test lockout at MAX_ATTEMPTS (5 wrong attempts)
- [ ] Verify old sessions are invalidated after reset
- [ ] Deploy on Railway
