# 🚀 Phase 1 — Foundation Week
## Sales Management System (Offline-First POS)

**Stack confirmed:** Flask (latest, app factory pattern) · Raw SQLAlchemy 2.0 (no Flask-SQLAlchemy extension) · SQLite · Vanilla JS frontend

**Team:**
| Person | Owns |
|---|---|
| **Obinna** | `frontend/`, offline queue (client-side) |
| **Covenant** | `backend/app.py`, `config.py`, `routes/`, `controllers/`, `services/`, `utils/`, `main.py` |
| **ENJ** | `backend/models/`, `backend/sync/`, `database/`, `cli/cli.py` |

---

## 🎯 Phase 1 Goal (one sentence)

By end of week: server boots, **one real model** exists, **one real endpoint** (`GET /products`) flows route → controller → service → model → DB, and the frontend can fetch and render it. Nothing else. No auth, no sales flow, no sync logic yet — just a working skeleton with the correct layering.

### ⚠️ Critical dependency
Covenant's route work is blocked on ENJ's `Product` model existing. **ENJ ships a working (even minimal) `Product` model by Day 2** so Covenant isn't stalled. Agree on the model's field names *before* either of you writes code — pull them straight from `DATABASE_SCHEMA.md §2`, don't improvise.

---

## 👤 ENJ — Database + Sync Foundation

### Execution Checklist
- [ ] `backend/models/models.py`: set up `Engine` + `sessionmaker` + `DeclarativeBase`
- [ ] `Product` model (Mapped/mapped_column syntax) — fields: `id, name, category, selling_price, cost_price, stock_quantity, is_active, created_at, updated_at` (per `DATABASE_SCHEMA.md §2`)
- [ ] `SyncQueue` model — fields: `id, device_id, entity_type, payload (JSON), status, retry_count, last_attempt_at, created_at` (per `DATABASE_SCHEMA.md §7`) — model only, no logic yet
- [ ] `database/schema.sql`: hand-written reference schema matching the ORM models
- [ ] `cli/cli.py`: implement `setup` (create tables), `seed` (insert 5–10 demo products), `reset` (drop + recreate) — must be idempotent, safe to rerun
- [ ] `backend/sync/queue.py`: stub only — function signatures `push_to_queue()`, `process_queue()` with docstrings, no real implementation yet

### Socratic Task Spec
**Objective:** Define `Product` and `SyncQueue` using SQLAlchemy 2.0's modern declarative syntax, establish the Engine/Session lifecycle, and get `python cli/cli.py setup && python cli/cli.py seed` producing a populated SQLite database.

**Constraints:**
- `Mapped` / `mapped_column` only — no legacy `Column()` style
- One `Engine`, created once at startup (CLI and app share the same pattern) — not re-created per call
- `setup` must be safe to run twice without erroring

**Required Documentation:**
- SQLAlchemy 2.0 declarative mapping docs
- SQLAlchemy 2.0 Engine configuration docs

**Expected Output:** Running `setup` then `seed` results in a populated `products` table you can verify with a quick query. `SyncQueue` table exists but stays empty this week.

**Guiding questions for ENJ (don't answer yet — sit with these):**
1. Should the `Engine` live in `models.py` itself, or get created in `cli.py`/`app.py` and passed in? What breaks if two different places create their own `Engine`?
2. Your `seed` command needs a `Session` to insert rows — where does that session get opened and closed, and what happens if `seed` is interrupted halfway?

---

## 👤 Covenant — Backend API + Business Logic

### Execution Checklist
- [*] `requirements.txt`: Flask, SQLAlchemy>=2.0, python-dotenv, pytest
- [*] `backend/config.py`: `Config` class reading from `.env` (DB path, `SECRET_KEY`, `DEBUG`)
- [*] `backend/app.py`: `create_app()` factory — initializes Flask, registers blueprints, hooks into ENJ's session setup
- [*] `main.py`: imports `create_app()`, runs the dev server
- [*] `backend/routes/sales.py`: Blueprint with **one** route — `GET /products` (no auth, no other routes yet)
- [*] `backend/controllers/sales_controller.py`: handles the request/response shape for that route — separate from the route registration itself
- [*] `backend/services/sales_service.py`: `get_all_products()` — the actual business logic / DB query lives here, not in the controller
- [*] `backend/utils/validators.py`: at least one real validator (e.g. pagination params) wired into the controller

### Socratic Task Spec
**Objective:** Build the Flask application factory and wire `GET /products` through the **full layer chain**: route → controller → service → model, using ENJ's `Session`.

**Constraints:**
- No Flask-SQLAlchemy extension — manage `Session` yourself
- Blueprint pattern from day one, not a single monolithic `app.py`
- The route function should NOT contain a SQL query directly — if it does, your layering is wrong

**Required Documentation:**
- Flask application factory pattern (official docs)
- Flask Blueprints (official docs)
- SQLAlchemy 2.0 Session basics — specifically session scope per-request

**Expected Output:** Hitting `GET /products` on the running server returns valid JSON built from real seeded DB rows, and you can point to three distinct functions (route, controller, service) each doing one job in that chain.

**Guiding questions for Covenant (don't answer yet — sit with these):**
1. If `routes/sales.py` calls `controllers/sales_controller.py` which calls `services/sales_service.py` — who opens the `Session`, and who's responsible for closing it?
2. What's the actual difference between what the **controller** does and what the **service** does, in your own words — not the doc's words?

---

## 👤 Obinna — Frontend + Offline Engine

### Execution Checklist
- [ ] `frontend/index.html` shell + `frontend/assets/styles.css` base styles
- [ ] `frontend/pages/login.html` — static layout only, no real auth wiring yet (per `FRONTEND_SPEC.md §1`)
- [ ] `frontend/services/api.js` — fetch wrapper that calls `GET /products`
- [ ] A page that renders the product list returned from that call (name, price, stock — per `FRONTEND_SPEC.md §6.1`)
- [ ] Local offline-queue storage scaffold (IndexedDB, or localStorage as a Week-1 placeholder) with a record shape matching `SYNC_ENGINE.md §3` (`transaction_id`, `entity_type`, `operation`, `payload`, `status`, `retry_count`, `created_at`)
- [ ] No sync/dispatch logic yet — just confirm you can write a record into the store and read it back

### Socratic Task Spec
**Objective:** Build the page shell, the API fetch layer, and the client-side offline queue *storage shape* — without implementing any real sync logic yet.

**Constraints:**
- Vanilla JS only, no framework
- Offline queue records must match the schema in `SYNC_ENGINE.md §3` exactly, even though nothing writes to it for real yet

**Required Documentation:**
- MDN: IndexedDB API (or `localStorage` if using it as a placeholder)
- `FRONTEND_SPEC.md` §§1–2, 11

**Expected Output:** Loading the page fetches and displays the live product list from Covenant's endpoint. Separately, you can manually push a fake offline-queue record into your local store and read it back out, proving the storage shape works.

**Guiding questions for Obinna (don't answer yet — sit with these):**
1. `localStorage` is synchronous and string-only; `IndexedDB` is async and structured. Given this queue will eventually hold hundreds of pending sales, which one actually fits — and why does that matter for Phase 2?
2. What does your queue record need that a normal "create sale" request doesn't?

---

## ✅ Definition of Done — Phase 1 (whole team)

A Phase 1 feature is **only** done if:
- [ ] Server boots with zero errors (`python main.py`)
- [ ] `GET /products` returns real seeded data, not a hardcoded stub
- [ ] The call path visibly passes through route → controller → service → model (not route → model directly)
- [ ] Frontend renders that live data, not mock JSON
- [ ] `cli.py setup` / `seed` / `reset` all run cleanly and are rerunnable

**Out of scope this week (do not touch):** auth, sales creation, sync push/pull, conflict resolution, reports. Per the team's own rule — scope creep kills Phase 1.

---

## 🗓️ Suggested Day-by-Day

| Day | ENJ | Covenant | Obinna |
|---|---|---|---|
| 1 | Engine/Session setup, start `Product` model | `requirements.txt`, `config.py` skeleton | `index.html` shell, CSS base |
| 2 | **Ship `Product` model** (unblocks Covenant), start `SyncQueue` model | `app.py` factory, blueprint skeleton | `login.html` static |
| 3 | `cli.py setup` + `seed` working | Wire `GET /products` route → controller → service | `api.js` fetch wrapper |
| 4 | `database/schema.sql`, `sync/queue.py` stub | Validator in `utils/`, polish endpoint | Render product list from live API |
| 5 | Buffer / help unblock others | Buffer / help unblock others | Offline queue storage scaffold |

---

## 🚨 Non-negotiable team rules (carried over)
1. Field names and types are agreed **before** coding — pull from `DATABASE_SCHEMA.md`, don't freelance.
2. Use `CHANGELOG.md` — log what shipped each day.
3. Blockers are stated explicitly: *"I cannot proceed because X is missing."*
4. No analytics, reporting, or auth work this week — that's not Phase 1.