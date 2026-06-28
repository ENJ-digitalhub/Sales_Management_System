# 🚀 Phase 2 — Authentication
## Sales Management System (Offline-First POS)

**Stack:** Flask · Raw SQLAlchemy 2.0 · SQLite · Vanilla JS · bcrypt · JWT (PyJWT)

**Team:**
| Person | Owns |
|---|---|
| **Goodness** | `frontend/` — login UI, session persistence, token storage |
| **Covenant** | `backend/routes/`, `controllers/`, `services/`, `utils/` — auth endpoints, JWT logic |
| **ENJ** | `backend/models/` — User + Device models, `database/schema.sql`, `cli/cli.py` — seed users |

---

## 🎯 Phase 2 Goal (one sentence)

By end of phase: a real user can log in with username + password, receive a JWT, and every subsequent request is validated against that token — with role-based access enforced at the route level.

### ⚠️ Critical dependencies
- Covenant's auth routes are blocked on ENJ's `User` and `Device` models existing — **ENJ ships both models by Day 2**
- Goodness's login UI is blocked on Covenant's `POST /auth/login` endpoint returning a real JWT — **Covenant ships the endpoint by Day 3**
- Agree on the JWT payload shape and response contract **before** anyone writes code — locked below

---

## 🔒 Locked Contracts (agree before coding)

### JWT Payload
```json
{
  "sub": "user_uuid",
  "role": "admin | manager | employee",
  "device_id": "device_uuid",
  "exp": 1234567890
}
```

### POST /auth/login — Request
```json
{
  "username": "string",
  "password": "string",
  "device_id": "string"
}
```

### POST /auth/login — Response (success)
```json
{
  "success": true,
  "token": "jwt_string",
  "user": {
    "id": "uuid",
    "name": "string",
    "role": "admin | manager | employee"
  }
}
```

### POST /auth/login — Response (failure)
```json
{
  "success": false,
  "message": "Invalid username or password"
}
```

### POST /auth/logout — Request
```json
{
  "device_id": "string"
}
```

### GET /auth/verify — Response
```json
{
  "valid": true,
  "user": {
    "id": "uuid",
    "role": "string"
  }
}
```

---

## 🔐 Auth Rules (non-negotiable)
- JWT expiry: **24 hours**
- One active session per user — new login invalidates previous device
- Password hashing: **bcrypt only**, via `backend/utils/security.py`
- Token storage on client: **localStorage**
- Server never trusts client role claims — role is always read from DB, not token
- All protected routes return `401` if token is missing or expired
- All protected routes return `403` if token is valid but role is insufficient

---

## 👤 ENJ — Models + Schema + CLI

### Execution Checklist
- [x] `backend/models/models.py`: add `User` model — fields: `id, name, username, password_hash, role, phone_or_email, account_name, bank_name, account_number, pin_hash, is_active, created_at` (per `DATABASE_SCHEMA.md §1`)
- [x] `backend/models/models.py`: add `Device` model — fields: `id, user_id, device_name, is_active, last_seen_at` (per `DATABASE_SCHEMA.md §8`)
- [x] `backend/utils/security.py`: `hash_password(plain: str) -> str` and `verify_password(plain: str, hashed: str) -> bool` using bcrypt
- [x] `database/schema.sql`: add `users` and `devices` tables matching the ORM models
- [x] `cli/cli.py`: extend `seed` to insert one user per role (admin, manager, employee) with hashed passwords — use `security.py`, never store plain text
- [x] `cli/cli.py`: extend `reset` to clear `users` and `devices` tables safely

### Socratic Task Spec
**Objective:** Define `User` and `Device` models in SQLAlchemy 2.0 declarative syntax, implement bcrypt password hashing in a shared utility, and seed one user per role so Covenant can test auth endpoints immediately.

**Constraints:**
- `Mapped` / `mapped_column` only — no legacy `Column()` style
- `password_hash` field stores the bcrypt hash — never the plain password
- `role` must be constrained to exactly three values: `admin`, `manager`, `employee`
- `security.py` is the **only** place bcrypt is imported — no other file touches bcrypt directly

**Required Documentation:**
- SQLAlchemy 2.0 declarative mapping docs
- bcrypt Python library docs

**Expected Output:** Running `seed` produces three users (one per role) with hashed passwords in the DB. `verify_password` correctly returns `True` for the right password and `False` for the wrong one.

**Guiding questions for ENJ:**
1. `role` has exactly three valid values — how do you enforce that at the database level in SQLAlchemy 2.0, and what happens if someone tries to insert an invalid role?
2. Your `Device` model has a `user_id` foreign key — what does `relationship()` look like on the `User` side, and do you need it in Phase 2 or can it wait?

---

## 👤 Covenant — Auth Endpoints + JWT + Middleware

### Execution Checklist
- [ ] `requirements.txt`: add `PyJWT`, `bcrypt`
- [ ] `backend/utils/jwt_utils.py`: `generate_token(user_id, role, device_id) -> str` and `decode_token(token: str) -> dict` — 24hr expiry, uses `SECRET_KEY` from config
- [ ] `backend/utils/auth_middleware.py`: `require_auth` decorator — extracts Bearer token from `Authorization` header, decodes it, attaches user to `flask.g`
- [ ] `backend/utils/auth_middleware.py`: `require_role(*roles)` decorator — checks `flask.g.user.role` against allowed roles, returns `403` if insufficient
- [ ] `backend/routes/auth.py`: Blueprint with three routes — `POST /auth/login`, `POST /auth/logout`, `GET /auth/verify`
- [ ] `backend/controllers/auth_controller.py`: handles request/response shape for all three routes
- [ ] `backend/services/auth_service.py`: `login(username, password, device_id)`, `logout(device_id)`, `verify_token(token)` — all DB logic lives here
- [ ] `backend/app.py`: register auth blueprint
- [ ] Protect `GET /products` from Phase 1 with `@require_auth` — any logged-in role can access it

### Socratic Task Spec
**Objective:** Build the full auth flow — login validates credentials, issues a JWT, records the active device. Logout invalidates it. Every protected route runs through the `require_auth` decorator before the controller is reached.

**Constraints:**
- JWT logic lives in `jwt_utils.py` only — no other file imports PyJWT directly
- `auth_service.py` accepts a session as a parameter — it never opens its own session
- `get_db()` uses `flask.g` for request-scoped session management
- `shutdown_session` closes via `flask.g`, not a new session
- Decorator returns proper HTTP status codes — `401` for missing/expired token, `403` for wrong role

**Required Documentation:**
- PyJWT docs
- Flask `g` object and request context docs
- Flask decorator pattern docs

**Expected Output:** `POST /auth/login` with valid credentials returns a JWT. The same token passed to `GET /auth/verify` returns the user's role. `GET /products` without a token returns `401`.

**Guiding questions for Covenant:**
1. The `require_auth` decorator needs to pass the decoded user into the route function — what are the two ways to do this in Flask, and which one keeps your route functions cleanest?
2. When a user logs in from a new device, the old device session must be invalidated — where exactly in the service layer does this happen, and what DB change makes it true?

---

## 👤 Goodness — Login UI + Token Storage + Session Persistence

### Execution Checklist
- [ ] `frontend/pages/login.html`: complete login form — username + password fields, submit button, error state display
- [ ] `frontend/modules/auth.js`: `login(username, password)` — calls `POST /auth/login`, stores JWT in `localStorage` on success, redirects based on role
- [ ] `frontend/modules/auth.js`: `logout()` — calls `POST /auth/logout`, clears `localStorage`, redirects to login
- [ ] `frontend/modules/auth.js`: `getToken()` — retrieves token from `localStorage` for use in API calls
- [ ] `frontend/modules/auth.js`: `isAuthenticated()` — checks token exists and is not expired (decode without verifying signature client-side)
- [ ] `frontend/services/api.js`: update fetch wrapper to attach `Authorization: Bearer <token>` header on every request
- [ ] `frontend/pages/dashboard.html`: redirect to login if `isAuthenticated()` returns false
- [ ] Role-based redirect after login: Admin → admin dashboard, Manager → manager dashboard, Employee → sales dashboard
- [ ] Show logged-in user's name and role in the UI header

### Socratic Task Spec
**Objective:** Build the login page, wire it to Covenant's endpoint, store the JWT in localStorage, and use it on every subsequent API call — with automatic redirect to login if the token is missing or expired.

**Constraints:**
- Vanilla JS only — no framework
- Token stored in `localStorage` only — no cookies, no sessionStorage
- `auth.js` is the single module responsible for everything token-related — no other file reads or writes `localStorage` directly
- Never store the user's password anywhere on the client after the login call completes

**Required Documentation:**
- MDN: localStorage API
- MDN: fetch API — specifically the `headers` option
- JWT structure (header.payload.signature) — understand what you can safely decode client-side without a library

**Expected Output:** Logging in stores the token and redirects to the correct dashboard based on role. Refreshing the page stays logged in. Manually clearing localStorage and refreshing redirects back to login.

**Guiding questions for Goodness:**
1. A JWT has three parts separated by dots — the middle part (payload) is just base64. How do you decode it in vanilla JS without a library, and what does that tell you about what you should and shouldn't trust client-side?
2. Your fetch wrapper needs to add the auth header to every request — how do you structure `api.js` so that every call automatically includes the token without repeating the header logic in every function?

---

## ✅ Definition of Done — Phase 2 (whole team)

A Phase 2 feature is **only** done if:
- [ ] `POST /auth/login` returns a valid JWT for correct credentials
- [ ] `POST /auth/login` returns `401` for wrong credentials
- [ ] `GET /auth/verify` confirms a valid token and returns user role
- [ ] `POST /auth/logout` invalidates the device session
- [ ] `GET /products` returns `401` without a token
- [ ] `GET /products` returns data with a valid token
- [ ] Login page submits, stores token, and redirects by role
- [ ] Page refresh keeps the user logged in
- [ ] Clearing localStorage logs the user out on next page load
- [ ] Seeded users (one per role) can all log in successfully
- [ ] Passwords are hashed in DB — no plain text anywhere

**Out of scope this phase:** sales creation, inventory editing, sync logic, reports, PIN login. Do not touch these.

---

## 🗓️ Day-by-Day

| Day | ENJ | Covenant | Goodness |
|---|---|---|---|
| 1 | `User` model, `Device` model | `jwt_utils.py`, `requirements.txt` update | `login.html` static layout |
| 2 | **Ship models** (unblocks Covenant), `security.py` | `auth_service.py` skeleton, `get_db()` session scope | `auth.js` — `getToken()`, `isAuthenticated()` |
| 3 | `schema.sql` updates, seed users with hashed passwords | **Ship `POST /auth/login`** (unblocks Goodness), `POST /auth/logout` | `api.js` Bearer header, wire login form |
| 4 | `cli.py reset` update, buffer | `GET /auth/verify`, `require_auth` decorator, protect `/products` | Role-based redirect, session persistence |
| 5 | Buffer / help unblock | `require_role` decorator, buffer | User name/role in header, buffer |

---

## 🚨 Non-negotiable team rules
1. JWT payload shape and API response contracts above are locked — do not change field names without a team decision
2. `security.py` is the only file that imports bcrypt
3. `jwt_utils.py` is the only file that imports PyJWT
4. Services accept session as a parameter — they never open their own session
5. Log what shipped each day in `CHANGELOG.md`
6. Blockers stated explicitly: *"I cannot proceed because X is missing"*
7. No sales, inventory, or sync work this phase
