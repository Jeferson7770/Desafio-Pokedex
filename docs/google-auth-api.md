# Google Authentication (OAuth 2.0)

This document covers the two Google authentication endpoints, what the frontend needs to implement, and the required backend environment variables.

---

## Required backend environment variables

| Variable | Description | Where to get it |
|---|---|---|
| `GOOGLE_CLIENT_ID` | Client ID from the Google Cloud Console project | [console.cloud.google.com](https://console.cloud.google.com) → APIs & Services → Credentials |

> **Important:** the `GOOGLE_CLIENT_ID` is the same for backend and frontend. Create a project in Google Cloud Console, enable the **Google Identity API**, and create an **OAuth 2.0 Client ID** credential (type "Web application"). Add the frontend origin under *Authorized JavaScript origins* and the frontend redirect under *Authorized redirect URIs*.

---

## What the frontend needs to do

The backend **does not redirect** to Google. The frontend is responsible for opening the OAuth flow and obtaining the `id_token`. The backend only validates that token.

### Recommended flow (Google Identity Services — GSI)

1. Include the Google SDK on the page:
   ```html
   <script src="https://accounts.google.com/gsi/client" async defer></script>
   ```

2. Initialize the client with your `GOOGLE_CLIENT_ID`:
   ```js
   google.accounts.id.initialize({
     client_id: "YOUR_GOOGLE_CLIENT_ID",
     callback: handleCredentialResponse,
   });
   ```

3. Render the button or trigger the prompt:
   ```js
   google.accounts.id.renderButton(document.getElementById("google-btn"), {
     theme: "outline",
     size: "large",
   });
   // or: google.accounts.id.prompt();
   ```

4. In the callback you receive `credential` — this is the `id_token` to send to the backend:
   ```js
   function handleCredentialResponse(response) {
     const idToken = response.credential; // <-- send this to the backend
   }
   ```

5. Send the `id_token` to one of the endpoints below depending on the case (register or login).

---

## Endpoints

### 1. Register via Google

**POST** `/users/auth/google/register/`

Creates a new account linked to Google. Should be used when the user does not have an existing account.

#### Request body

```json
{
  "id_token": "eyJhbGciOiJSUzI1NiIs...",
  "cpf": "123.456.789-09",
  "oab_number": "123456",
  "oab_state": "SP",
  "device_uuid": "optional-device-uuid"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `id_token` | string | ✅ | ID Token returned by the Google SDK |
| `cpf` | string | ✅ | Lawyer's CPF (with or without formatting) |
| `oab_number` | string | ✅ | OAB registration number |
| `oab_state` | string | ✅ | OAB state (2 letters, e.g. `SP`) |
| `device_uuid` | string | ❌ | Unique device UUID for session management |

> `email` and `full_name` are extracted automatically from the Google token — do not send them.

#### Response `201 Created`

```json
{
  "user": {
    "id": 42,
    "email": "user@gmail.com"
  },
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "refresh": "eyJhbGciOiJIUzI1NiIs..."
}
```

#### Possible errors

| Status | Payload | Reason |
|---|---|---|
| `400` | `{"id_token": ["Token do Google inválido ou expirado."]}` | Invalid, expired, or tampered token |
| `400` | `{"id_token": ["O email da conta Google não está verificado."]}` | Google account without a verified email |
| `400` | `{"email": ["Este email já está cadastrado. Use o login com Google."]}` | Account with this email already exists |
| `400` | `{"cpf": ["CPF já está cadastrado"]}` | CPF already linked to another account |
| `400` | `{"detail": "Email ou CPF já cadastrados"}` | Race condition / database integrity error |

---

### 2. Login via Google

**POST** `/users/auth/google/login/`

Authenticates an existing user with the Google token. If the user already has an account (registered via email+password), the `google_id` is linked automatically on the first use.

#### Request body

```json
{
  "id_token": "eyJhbGciOiJSUzI1NiIs...",
  "device_uuid": "optional-device-uuid"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `id_token` | string | ✅ | ID Token returned by the Google SDK |
| `device_uuid` | string | ❌ | Unique device UUID |

#### Response `200 OK`

```json
{
  "user": {
    "id": 42,
    "email": "user@gmail.com"
  },
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "refresh": "eyJhbGciOiJIUzI1NiIs..."
}
```

#### Possible errors

| Status | Payload | Reason |
|---|---|---|
| `400` | `{"id_token": ["Token do Google inválido ou expirado."]}` | Invalid or expired token |
| `400` | `{"detail": "Usuário não encontrado. Realize o cadastro primeiro."}` | No user found with that email/google_id |

---

## Account linking logic

```
Login with Google
       │
       ▼
 google_id exists in the database?
       │
    Yes ─────────────────────────────→ Log in normally
       │
      No
       │
       ▼
 email from token exists in the database?
       │
    Yes ──→ Link google_id to the account and log in
       │
      No
       │
       ▼
    Return 400 (user not found)
```

This allows a lawyer who registered via email+password to also use "Sign in with Google" without creating a duplicate account.

---

## Using the returned JWT tokens

After registration or login (via Google or otherwise), token behavior is identical to the traditional flow:

- `access`: short-lived token (30 min). Send in the `Authorization: Bearer <access>` header on all authenticated requests.
- `refresh`: long-lived token (7 days). Use at `/users/token/refresh/` to obtain a new `access` token without prompting the user to log in again.

---

## Frontend checklist

- [ ] Create a project in Google Cloud Console and enable the Google Identity API
- [ ] Create an OAuth 2.0 credential (type "Web application") and copy the `GOOGLE_CLIENT_ID`
- [ ] Add the frontend origin under *Authorized JavaScript origins* (e.g. `https://app.fince.com.br`)
- [ ] Integrate the `@google/identity-services` SDK or the GSI script
- [ ] Upon receiving `credential` (id_token), decide the flow:
  - New user → call `/users/auth/google/register/` with `cpf` + `oab_number` + `oab_state`
  - Existing user → call `/users/auth/google/login/`
- [ ] Store `access` and `refresh` the same way as in the email/password flow
- [ ] Optional: generate and persist a `device_uuid` (e.g. `crypto.randomUUID()`) for device tracking

---

## Security

- The `id_token` is **validated by the backend** using the `google-auth` library with the `GOOGLE_CLIENT_ID`. Tokens from other applications are rejected.
- Google `id_token`s are short-lived (~1 hour). Do not store or reuse them — always obtain a fresh token before calling the API.
- The `id_token` must never be exposed in logs or URLs.
