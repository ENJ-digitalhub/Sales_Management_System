# 🚀 Phase 2 — Authentication + Inventory Week

**Sales Management System (Offline-First POS)**

Stack confirmed: Flask (latest, app factory pattern) · Raw SQLAlchemy 2.0 (no Flask-SQLAlchemy extension) · SQLite · Vanilla JS frontend · JWT (access tokens only, 24hr expiry)

---

## 👥 Team Ownership

| Person | Owns |
|--------|------|
| Goodness | `frontend/`, auth UI, session persistence, inventory UI |
| Covenant | `backend/app.py`, `routes/`, `controllers/`, `services/`, `utils/`, auth + inventory APIs |
| ENJ | `backend/models/`, `database/`, `cli/cli.py`, auth tables |

---

## 🎯 Phase 2 Goal

By end of week: users can authenticate, protected endpoints work, products become manageable, and inventory rules exist — while preserving clean layering and avoiding business logic leakage into routes.

---

## ⚠️ Critical Dependency Chain

```
ENJ ships User model
        ↓
Covenant implements auth service + JWT
        ↓
Goodness wires login + session persistence
```

Covenant cannot finish protected APIs until ENJ ships the `User` model and session integration.
Goodness cannot wire login persistence until Covenant exposes a stable login response.

**Auth payload contract is locked below. No deviations without team agreement.**

---

## 🔐 Auth Payload Contract (Locked)

### POST /auth/login — Success (200)

```json
{
  "success": true,
  "token": "jwt_string_here",
  "user": {
    "id": "uuid",
    "name": "string",
    "username": "string",
    "role": "admin | manager | employee"
  }
}
```

### POST /auth/login — Failure (401)

```json
{
  "success": false,
  "error": "Invalid credentials"
}
```

### GET /auth/me — Success (200)

```json
{
  "success": true,
  "user": {
    "id": "uuid",
    "name": "string",
    "username": "string",
    "role": "admin | manager | employee"
  }
}
```

### GET /auth/me — Unauthorized (401)

```json
{
  "success": false,
  "error": "Token missing or invalid"
}
```

### Generic Error Shape (all protected routes)

```json
{
  "success": false,
  "error": "string describing the problem"
}
```

---

## 🔑 JWT Rules

- **Expiry:** 24 hours from issue
- **Algorithm:** HS256
- **Payload fields:** `user_id`, `role`, `exp`
- **Storage (frontend):** `localStorage`
  - Rationale: system runs on a private LAN, not a public web app. Persistence across tabs and browser restarts outweighs XSS risk in this context.
- **Header format:** `Authorization: Bearer <token>`

---

## 🔒 Password Hashing Strategy

- **Library:** `bcrypt`
- **Location:** `backend/utils/security.py` — single source of truth
- **Rule:** both ENJ (seed layer) and Covenant (auth service) import hashing utilities from `security.py`
- Passwords are **never stored raw, never logged, never returned in any response**

```python
# backend/utils/security.py (interface)
def hash_password(plain: str) -> str: ...
def verify_password(plain: str, hashed: str) -> bool: ...
```

---

## 🗄️ get_session() — Interface Definition

Pattern: **context manager**

```python
# backend/models/database.py
from contextlib import contextmanager

@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

**Usage (in services):**

```python
with get_session() as session:
    user = session.query(User).filter_by(username=username).first()
```

- Services own the `with` block
- Routes and controllers never touch sessions directly
- No session leaks between requests

---

## 👤 ENJ — Database + Auth Foundation

### Execution Checklist

- [ ] `backend/models.py` — create `User` model using `Mapped/mapped_column`
- [ ] Fields:
  - `id` — primary key
  - `username` — unique, indexed
  - `password_hash` — string, never nullable
  - `role` — `admin | manager | employee`, indexed
  - `is_active` — boolean, default `True`
  - `created_at` — `default=datetime.now`
  - `updated_at` — `default=datetime.now`, `onupdate=datetime.now`
- [ ] Add indexes: `username`, `role`
- [ ] Update `database/schema.sql`
- [ ] Extend `cli/cli.py seed`:
  - create one admin
  - create one manager
  - create one employee
  - use `security.hash_password()` from `backend/utils/security.py` — do not hash inline
- [ ] Implement `get_session()` context manager in `backend/models/database.py`

### Socratic Task Spec

**Objective:** Introduce authentication persistence and ensure database setup supports secure user retrieval.

**Constraints:**
- No plaintext passwords
- Username uniqueness enforced at DB level
- Session lifecycle consistent with Phase 1 patterns
- `updated_at` uses `onupdate=datetime.now` (without parentheses)

**Required Documentation:**
- SQLAlchemy 2.0 `Mapped` / `mapped_column`
- SQLAlchemy Session lifecycle
- `contextlib.contextmanager`

**Expected Output:**

```bash
python cli/cli.py setup
python cli/cli.py seed
```

Creates users and products without error. Seeded users have hashed passwords.

**Guiding questions (sit with these, don't answer yet):**

1. Should password hashing happen inside the model, service, or seed layer?
2. If a user becomes inactive, should deletion or soft-disable preserve auditability better?

---

## ⚙️ Covenant — Backend API + Business Logic

### Execution Checklist

- [ ] Add to `requirements.txt`: `PyJWT`, `bcrypt`
- [ ] `backend/routes/auth.py` — Blueprint, routes only
- [ ] `backend/controllers/auth_controller.py` — request/response handling only
- [ ] `backend/services/auth_service.py` — all auth logic lives here
- [ ] `backend/utils/security.py` — `hash_password()`, `verify_password()`, JWT encode/decode
- [ ] Implement:
  - `POST /auth/login`
  - `GET /auth/me`
- [ ] JWT middleware — verify token on protected routes
- [ ] Role utility — decorator or helper for `admin`, `manager`, `employee` enforcement
- [ ] Inventory endpoints:
  - `GET /products` — protected
  - `PATCH /products/{id}` — protected, admin/manager only

### JWT Implementation Rules

- Token expiry: `24 hours` (`exp = datetime.utcnow() + timedelta(hours=24)`)
- Algorithm: `HS256`
- Secret key: loaded from environment config, never hardcoded
- Decode errors return `401` with `{ "success": false, "error": "Token missing or invalid" }`

### Socratic Task Spec

**Objective:** Implement authentication and authorization using strict route → controller → service separation.

**Constraints:**
- No SQL in routes
- Controllers handle request/response only
- Services contain all auth rules and token logic
- No Flask-SQLAlchemy extension
- Token creation happens in the service layer, not the controller

**Required Documentation:**
- Flask Blueprints
- Flask request lifecycle
- PyJWT documentation
- SQLAlchemy Session scope

**Expected Output:**
Authenticated requests return user-aware responses. Protected routes reject missing or invalid tokens with correct error shape.

**Guiding questions (sit with these, don't answer yet):**

1. Where should token creation happen — route, controller, or service?
2. Should role enforcement happen before or after business logic executes?

---

## 🎨 Goodness — Frontend + Auth Experience

### Execution Checklist

- [ ] `frontend/pages/login.html` — login form
- [ ] `frontend/pages/dashboard.html` — role-aware landing page
- [ ] `frontend/services/auth.js` — all API calls and token handling
- [ ] Login form — username + password, submits to `POST /auth/login`
- [ ] On success: store JWT in `localStorage` under key `sms_token`
- [ ] On failure: show inline error message (no blocking modal)
- [ ] Logout: clear `localStorage`, redirect to login
- [ ] On every page load: check `localStorage` for token, redirect to login if missing
- [ ] Product inventory display — fetch from `GET /products` with token in header
- [ ] Loading states — show while requests are in flight
- [ ] Error states — show on failed requests using response `error` field

### Token Storage Rules

- Key: `sms_token`
- Location: `localStorage`
- On expiry (24hr): next protected request returns `401` → clear token → redirect to login
- Token expiry is handled reactively (on failed request), not proactively

### Auth Header Format

```javascript
headers: {
  "Authorization": `Bearer ${localStorage.getItem("sms_token")}`,
  "Content-Type": "application/json"
}
```

### Socratic Task Spec

**Objective:** Build authentication UX and connect it to the real backend using the locked payload contract.

**Constraints:**
- Vanilla JS only
- No framework router
- No hardcoded user state
- All API calls go through `frontend/services/auth.js`

**Required Documentation:**
- Fetch API (MDN)
- Browser Storage APIs (MDN)
- MDN Authentication patterns

**Expected Output:**
User logs in, JWT is stored, and session persists after browser refresh. Unauthenticated users are redirected to login.

**Guiding questions (sit with these, don't answer yet):**

1. Where should token expiration handling live — every fetch call, or a central wrapper?
2. What should happen if a page refresh occurs while a fetch is mid-flight?

---

## ✅ Definition of Done — Phase 2

A Phase 2 feature is only done if:

- [ ] Login succeeds using seeded users
- [ ] JWT generated with 24hr expiry and validated on protected routes
- [ ] Protected routes reject missing or invalid tokens with correct error shape
- [ ] Product inventory updates persist to database
- [ ] Frontend stores token in `localStorage` and attaches it to requests
- [ ] Session survives browser refresh
- [ ] Layer chain enforced: `route → controller → service → model`

---

## 🗓️ Suggested Day-by-Day

| Day | ENJ | Covenant | Goodness |
|-----|-----|----------|--------|
| 1 | User model | Auth skeleton + `security.py` | Login page HTML |
| 2 | Seed users with hashed passwords | JWT service | Auth form JS |
| 3 | `get_session()` context manager | Login endpoint | API integration |
| 4 | DB polish + schema.sql | Protected routes + role utility | Session persistence |
| 5 | Buffer / review | Inventory protection | Inventory rendering |

---

## 🚨 Non-Negotiable Team Rules

1. Auth payload contract is locked. No changes without full team agreement.
2. Passwords are never stored raw, logged, or returned in responses.
3. Routes never contain business rules or SQL.
4. Token creation lives in the service layer only.
5. `security.py` is the single source for hashing and JWT utilities — no duplicating logic.
6. No sales or sync work this week — scope creep kills Phase 2.

---

## ❌ Out of Scope This Week

- Sales processing
- Sync retries
- Reports and analytics
- Conflict resolution
- PIN login (Phase 3)
- Refresh tokens (not in scope — access tokens only)
-