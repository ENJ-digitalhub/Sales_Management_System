🚀 Phase 2 — Authentication + Inventory Week

Sales Management System (Offline-First POS)

Stack confirmed: Flask (latest, app factory pattern) · Raw SQLAlchemy 2.0 (no Flask-SQLAlchemy extension) · SQLite · Vanilla JS frontend · JWT (access tokens only)

Team:

Person| Owns
Obinna| "frontend/", auth UI, session persistence, inventory UI
Covenant| "backend/app.py", "routes/", "controllers/", "services/", "utils/", auth + inventory APIs
ENJ| "backend/models/", "database/", "cli/cli.py", auth tables

---

🎯 Phase 2 Goal (one sentence)

By end of week: users can authenticate, protected endpoints work, products become manageable, and inventory rules exist — while preserving clean layering and avoiding business logic leakage into routes.

⚠️ Critical dependency

Covenant cannot finish protected APIs until ENJ ships the "User" model and session integration. Obinna cannot wire login persistence until Covenant exposes a stable login response shape. Lock the auth payload contract before implementation.

---

👤 ENJ — Database + Auth Foundation

Execution Checklist

- [ ] "backend/models/user.py": create "User" model using "Mapped/mapped_column"
- [ ] Fields:
  - "id"
  - "username"
  - "password_hash"
  - "role"
  - "is_active"
  - "created_at"
  - "updated_at"
- [ ] Add indexes:
  - "username"
  - "role"
- [ ] Update "database/schema.sql"
- [ ] Extend "cli/cli.py seed"
  - create admin
  - create manager
  - create employee
- [ ] Add helper:
  - "get_session()"

Socratic Task Spec

Objective: Introduce authentication persistence and ensure database setup supports secure user retrieval.

Constraints:

- No plaintext passwords
- Username uniqueness enforced in DB
- Session lifecycle remains consistent with Phase 1

Required Documentation:

- SQLAlchemy 2.0 ORM relationships
- SQLAlchemy Session lifecycle
- Password hashing basics

Expected Output:
Running:

python cli/cli.py setup
python cli/cli.py seed

creates users and products successfully.

Guiding questions for ENJ (don't answer yet — sit with these):

1. Should password hashing happen inside the model, service, or seed layer?
2. If a user becomes inactive, should deletion or soft-disable preserve auditability?

---

👤 Covenant — Backend API + Business Logic

Execution Checklist

- [X] "requirements.txt"
  - PyJWT
  - bcrypt
- [X] "backend/routes/auth.py"
- [ ] "backend/controllers/auth_controller.py"
- [ ] "backend/services/auth_service.py"
- [ ] "backend/utils/security.py"
- [ ] Implement:
  - "POST /auth/login"
  - "GET /auth/me"
- [ ] Add JWT verification middleware
- [ ] Add role utility:
  - admin
  - manager
  - employee
- [ ] Create inventory endpoints:
  - "GET /products"
  - "PATCH /products/{id}"

Socratic Task Spec

Objective: Implement authentication and authorization using route → controller → service separation.

Constraints:

- No SQL in routes
- Controllers handle request/response only
- Services contain auth rules
- No Flask-SQLAlchemy extension

Required Documentation:

- Flask Blueprints
- Flask request lifecycle
- JWT fundamentals
- SQLAlchemy Session scope

Expected Output:
Authenticated requests return user-aware responses and protected routes reject unauthorized access.

Guiding questions for Covenant (don't answer yet — sit with these):

1. Where should token creation happen — route, controller, or service?
2. Should role enforcement happen before or after business logic executes?

---

👤 Obinna — Frontend + Auth Experience

Execution Checklist

- [ ] "frontend/pages/login.html"
- [ ] "frontend/pages/dashboard.html"
- [ ] "frontend/services/auth.js"
- [ ] Build:
  - login form
  - logout
  - session persistence
- [ ] Store JWT locally
- [ ] Redirect unauthenticated users
- [ ] Product inventory display
- [ ] Loading states
- [ ] Error states

Socratic Task Spec

Objective: Build authentication UX and connect it to the real backend.

Constraints:

- Vanilla JS only
- No framework router
- No hardcoded user state

Required Documentation:

- Fetch API
- Browser Storage APIs
- MDN Authentication patterns

Expected Output:
User logs in and remains authenticated after refresh.

Guiding questions for Obinna (don't answer yet — sit with these):

1. Where should token expiration handling live?
2. What should happen if refresh occurs mid-session?

---

✅ Definition of Done — Phase 2 (whole team)

A Phase 2 feature is only done if:

- [ ] Login succeeds using seeded users
- [ ] JWT generated and validated
- [ ] Protected routes reject invalid tokens
- [ ] Product inventory updates persist
- [ ] Frontend stores and uses session
- [ ] Layer chain remains:
  route → controller → service → model

Out of scope this week (do not touch):
sales processing, sync retries, reports, analytics, conflict resolution

---

🗓️ Suggested Day-by-Day

Day| ENJ| Covenant| Obinna
1| User model| Auth skeleton| Login page
2| Seed users| JWT service| Auth form
3| Session helpers| Login endpoint| API integration
4| DB polish| Protected routes| Session persistence
5| Buffer| Inventory protection| Inventory rendering

---

🚨 Non-negotiable team rules (carried over)

1. API contracts are agreed before frontend integration.
2. Passwords are never stored raw.
3. Routes never contain business rules.
4. No sales or sync work this week — scope creep kills Phase 2.