# 🚀 Phase 8 — Testing & Hardening
## Sales Management System (Offline-First POS)

**Stack:** Flask · Raw SQLAlchemy 2.0 · SQLite · Vanilla JS · pytest

**Team:**
| Person | Owns |
|---|---|
| **Goodness** | Frontend tests — manual test scripts, offline simulation, UI edge cases |
| **Covenant** | Backend API tests — pytest, endpoint coverage, auth tests, edge cases |
| **ENJ** | Unit tests — models, sync engine, conflict resolution, CLI, database integrity |

---

## 🎯 Phase 8 Goal (one sentence)

By end of phase: every critical path in the system has test coverage, all edge cases from `EDGE_CASE.md` are verified, no negative stock can occur under any condition, and the system reaches a deterministic final state after any offline/online transition.

### ⚠️ Critical dependencies
- All Phases 2–7 must be fully complete before testing begins
- ENJ's unit tests are independent — can start Day 1
- Covenant's API tests depend on ENJ's seeded test DB being available — **ENJ ships test fixtures by Day 2**
- Goodness's frontend tests depend on Covenant's endpoints being stable — no moving contracts during this phase

---

## 📋 Test Scope (from TEST_PLAN.md)

### In scope
- Authentication & session control
- Sales processing (online + offline)
- Inventory consistency
- Sync engine reliability
- Conflict resolution
- Audit logging
- Security

### Out of scope
- UI/UX validation
- Performance benchmarking

---

## 📋 Exit Criteria (non-negotiable)

System is stable when:
- No data corruption occurs under offline/online transitions
- All conflicts are either auto-resolved or escalated correctly
- No negative stock observed under any test condition
- Sync engine reaches deterministic final state after every test
- All critical API endpoints return correct status codes
- Auth enforcement verified on every protected route

---

## 👤 ENJ — Unit Tests + Fixtures + DB Integrity

### Execution Checklist

#### Test Fixtures
- [ ] `tests/conftest.py`: pytest fixtures — in-memory SQLite test DB, session factory, seeded test data (users, products, sales)
- [ ] Fixture provides one user per role (admin, manager, employee)
- [ ] Fixture provides 10 products with varying stock levels including stock = 0 and stock = 1
- [ ] Fixture provides 5 completed sales, 1 edited sale, 1 cancelled sale
- [ ] Fixture provides 2 pending sync queue items and 1 conflict item

#### Model Tests — `tests/test_models.py`
- [ ] `User` — password hash is never plain text
- [ ] `User` — role constrained to `admin | manager | employee`
- [ ] `Product` — stock never goes below zero (DB constraint test)
- [ ] `Sale` — `editable_until` is always 20 minutes after `created_at`
- [ ] `SaleItem` — `cost_price_at_sale` is snapshotted correctly
- [ ] `AuditLog` — cannot be updated after creation
- [ ] `SyncQueue` — `transaction_id` is unique

#### Sync Engine Tests — `tests/test_sync.py`
- [ ] `push_to_queue()` — valid transaction is queued correctly
- [ ] `push_to_queue()` — duplicate `transaction_id` is ignored, returns `synced`
- [ ] `process_queue()` — valid sale commits correctly, stock deducted
- [ ] `process_queue()` — stock conflict flagged, DB unchanged
- [ ] `process_queue()` — deleted product conflict flagged, DB unchanged
- [ ] `process_queue()` — batch of 5: one failure does not abort remaining 4
- [ ] `resolve_conflict()` — approve re-validates stock, commits if sufficient
- [ ] `resolve_conflict()` — approve fails if stock now insufficient
- [ ] `resolve_conflict()` — reject marks transaction `failed`
- [ ] `resolve_conflict()` — double resolution attempt returns error

#### CLI Tests — `tests/test_cli.py`
- [ ] `setup` — creates all tables, safe to run twice
- [ ] `seed` — inserts expected demo data
- [ ] `reset` — clears all tables in FK-safe order, setup works after reset

#### DB Integrity Tests — `tests/test_db_integrity.py`
- [ ] Stock never goes negative under concurrent sale simulation
- [ ] FK constraints enforced — orphaned `SaleItem` rows impossible
- [ ] `AuditLog` rows cannot be deleted
- [ ] Soft-deleted products excluded from `GET /products`

### Socratic Task Spec
**Objective:** Write pytest unit tests for every model, the sync engine, and the CLI — with a shared fixture file that gives Covenant a stable test DB to build API tests against.

**Constraints:**
- Use in-memory SQLite for all tests — never touch `shop.db`
- Every test is independent — no test relies on another test's side effects
- Fixtures use `pytest` scope correctly — `session` scope for DB setup, `function` scope for data that mutates
- All sync engine tests call the actual functions — no mocking of ENJ's own code

**Required Documentation:**
- pytest docs — fixtures and conftest
- SQLAlchemy 2.0 — in-memory DB setup
- `TEST_PLAN.md` — full reference
- `EDGE_CASE.md` — §§2, 4, 6

**Expected Output:** Running `pytest tests/test_models.py tests/test_sync.py tests/test_cli.py tests/test_db_integrity.py` passes with zero failures. Covenant can import fixtures from `conftest.py` without any setup.

**Guiding questions for ENJ:**
1. Your sync engine tests need to simulate a batch where one item fails — how do you construct a test transaction that will definitely fail stock validation without hardcoding fragile data?
2. `AuditLog` immutability — SQLAlchemy doesn't enforce this automatically. How do you test that an `AuditLog` row cannot be updated, and where should the enforcement actually live?

---

## 👤 Covenant — API Tests + Auth Tests + Edge Cases

### Execution Checklist

#### Auth Tests — `tests/test_auth.py`
- [ ] `POST /auth/login` — correct credentials returns JWT
- [ ] `POST /auth/login` — wrong password returns `401`
- [ ] `POST /auth/login` — unknown username returns `401`
- [ ] `POST /auth/login` — new login invalidates previous device session
- [ ] `GET /auth/verify` — valid token returns user role
- [ ] `GET /auth/verify` — expired token returns `401`
- [ ] `POST /auth/logout` — invalidates device session

#### Sales Tests — `tests/test_sales_api.py`
- [ ] `POST /sales` — valid sale returns `completed` with correct totals
- [ ] `POST /sales` — insufficient stock rejects entire sale, no DB changes
- [ ] `POST /sales` — stock exactly at quantity — succeeds and deducts to zero
- [ ] `POST /sales` — duplicate product IDs in request returns `400`
- [ ] `PATCH /sales/{id}` — within 20 minutes succeeds for employee
- [ ] `PATCH /sales/{id}` — after 20 minutes returns `requires_approval` for employee
- [ ] `PATCH /sales/{id}` — after 20 minutes succeeds for manager
- [ ] `POST /sales/{id}/cancel` — restores stock correctly
- [ ] `POST /sales/{id}/cancel` — employee gets `403`

#### Inventory Tests — `tests/test_inventory_api.py`
- [ ] `POST /products` — admin creates product successfully
- [ ] `POST /products` — employee gets `403`
- [ ] `DELETE /products/{id}` — soft delete, product still in DB
- [ ] `GET /products` — soft-deleted product excluded
- [ ] `POST /purchases/{id}/approve` — stock incremented correctly
- [ ] `POST /purchases/{id}/approve` — non-admin gets `403`

#### Sync Tests — `tests/test_sync_api.py`
- [ ] `POST /sync` — valid batch returns per-item `synced` results
- [ ] `POST /sync` — duplicate `transaction_id` returns `synced`, no second write
- [ ] `POST /sync` — stock conflict returns `conflict` for that item, others succeed
- [ ] `POST /sync` — batch > 20 items returns `400`
- [ ] `POST /sync` — device_id mismatch returns `403`
- [ ] `GET /sync/pull` — returns current products and server timestamp
- [ ] `POST /sync/resolve` — approve commits conflicted transaction
- [ ] `POST /sync/resolve` — reject marks transaction `failed`
- [ ] `POST /sync/resolve` — double resolution returns `400`
- [ ] `POST /sync/resolve` — employee gets `403`

#### Conflict Tests — `tests/test_conflicts_api.py`
- [ ] `GET /conflicts` — returns all pending conflicts
- [ ] `GET /conflicts/{id}` — returns correct conflict detail
- [ ] `POST /conflicts/{id}/resolve` — approve with sufficient stock succeeds
- [ ] `POST /conflicts/{id}/resolve` — approve with insufficient stock returns error
- [ ] `POST /conflicts/{id}/resolve` — reject marks transaction `failed`
- [ ] `POST /conflicts/{id}/resolve` — employee gets `403`

#### Report Tests — `tests/test_reports_api.py`
- [ ] `GET /reports/daily` — returns correct totals for seeded data
- [ ] `GET /reports/daily` — cancelled sales excluded
- [ ] `GET /reports/monthly` — correct aggregation
- [ ] `GET /reports/employee/{id}` — correct totals for that employee only
- [ ] `GET /reports/daily` — employee gets `403`

#### Security Tests — `tests/test_security.py`
- [ ] Every protected route returns `401` without token
- [ ] Every protected route returns `401` with expired token
- [ ] Every role-restricted route returns `403` for insufficient role
- [ ] `resolved_by` cannot be spoofed via request body
- [ ] `editable_until` cannot be extended via request body

### Socratic Task Spec
**Objective:** Write pytest API tests for every endpoint — using ENJ's fixtures, a test Flask client, and covering both happy paths and critical edge cases from `TEST_PLAN.md` and `EDGE_CASE.md`.

**Constraints:**
- Use Flask test client — `app.test_client()`
- Import fixtures from ENJ's `conftest.py` — do not duplicate setup
- Every test asserts both the HTTP status code and the response body shape
- Security tests run against every protected route — not just a sample
- No test touches `shop.db` — in-memory only

**Required Documentation:**
- Flask testing docs — test client
- pytest docs — parametrize for security tests
- `TEST_PLAN.md` — full reference
- `EDGE_CASE.md` — full reference

**Expected Output:** Running `pytest tests/test_auth.py tests/test_sales_api.py tests/test_inventory_api.py tests/test_sync_api.py tests/test_conflicts_api.py tests/test_reports_api.py tests/test_security.py` passes with zero failures.

**Guiding questions for Covenant:**
1. Security tests need to hit every protected route — there are 20+ routes. How do you use `pytest.mark.parametrize` to test all of them with a single test function instead of writing 20 separate tests?
2. The `POST /sales` stock-exactly-at-quantity test needs the product stock to be exactly equal to the requested quantity — how do you set this up in a test without depending on the seed fixture having the right stock level?

---

## 👤 Goodness — Frontend Manual Tests + Offline Simulation

### Execution Checklist

#### Auth Flow Tests
- [ ] Login with correct credentials — JWT stored, redirect to correct dashboard by role
- [ ] Login with wrong credentials — error message shown, no redirect
- [ ] Page refresh — stays logged in
- [ ] Clear localStorage — redirected to login on next page load
- [ ] Token expiry simulation — manually set expired token in localStorage, verify redirect

#### Sales Flow Tests
- [ ] Build cart with 3 products — totals correct
- [ ] Complete sale — cart resets, success toast shown
- [ ] Complete sale with insufficient stock — error shown, cart not reset
- [ ] Edit sale within 20 minutes — edit button visible, edit succeeds
- [ ] Wait 20 minutes (or manipulate `editable_until`) — edit button hidden, approval message shown

#### Offline Queue Tests
- [ ] Disconnect from server (stop backend) — offline banner shown
- [ ] Complete sale while offline — queued in IndexedDB, marked `Not Synced`
- [ ] Reconnect server — sync triggers automatically, status updates to `Synced`
- [ ] Complete 5 sales offline — all 5 sync on reconnect
- [ ] Simulate 5 retry failures — item marked `Failed`, stops retrying

#### Inventory UI Tests
- [ ] Employee sees read-only inventory — no add/edit/delete controls
- [ ] Manager sees full controls — add, edit, delete all work
- [ ] Low-stock product highlighted in amber
- [ ] Soft-deleted product disappears from list

#### Conflict UI Tests
- [ ] Employee cannot access conflict dashboard — `403` shown
- [ ] Manager sees pending conflicts
- [ ] Approve conflict — removed from list, success toast
- [ ] Reject conflict with note — removed from list, success toast
- [ ] Approve conflict with insufficient stock — error shown, conflict stays in list

#### Report UI Tests
- [ ] Daily report loads correct totals
- [ ] Date picker changes fetch and re-render
- [ ] Employee performance table shows all employees
- [ ] Bar chart renders from live data
- [ ] Employee role redirected away from reports page

### Socratic Task Spec
**Objective:** Manually verify every frontend flow against the live backend — documenting pass/fail per test case and logging any UI bugs found.

**Constraints:**
- Test against live backend running on localhost — not mocked responses
- Every test case documented with: test name, steps, expected result, actual result, pass/fail
- Offline tests use browser DevTools network throttling or stopping the backend process
- All three roles tested separately — log in as each role for role-based tests

**Required Documentation:**
- `FRONTEND_SPEC.md` — full reference
- `EDGE_CASE.md` — §§1, 2, 3, 5
- Chrome DevTools — network tab, offline simulation

**Expected Output:** A completed test report document covering every checklist item above — with pass/fail per case and bug notes for any failures.

**Guiding questions for Goodness:**
1. Offline simulation using DevTools "Offline" mode cuts all network — but your backend is on localhost. How do you simulate the server being unreachable without cutting your own machine's network entirely?
2. Token expiry testing — JWT expiry is 24 hours. How do you test the expiry redirect without waiting 24 hours?

---

## 📁 New Files This Phase

```

/tests
├── conftest.py          ← ENJ
├── test_models.py       ← ENJ
├── test_sync.py         ← ENJ
├── test_cli.py          ← ENJ
├── test_db_integrity.py ← ENJ
├── test_auth.py         ← Covenant
├── test_sales_api.py    ← Covenant
├── test_inventory_api.py← Covenant
├── test_sync_api.py     ← Covenant
├── test_conflicts_api.py← Covenant
├── test_reports_api.py  ← Covenant
└── test_security.py     ← Covenant
```

Goodness produces a `docs/TEST_REPORT.md` document — not code.

---

## ✅ Definition of Done — Phase 8 (whole team)

A Phase 8 feature is **only** done if:
- [ ] `pytest` runs with zero failures across all test files
- [ ] No negative stock observed under any test condition
- [ ] No data corruption under offline/online transition tests
- [ ] All conflicts resolve to deterministic final state
- [ ] Every protected route returns `401` without token
- [ ] Every role-restricted route returns `403` for wrong role
- [ ] Frontend test report completed with pass/fail per case
- [ ] All bugs found during testing are logged and fixed before Phase 9

**Out of scope this phase:** deployment, installer, store owner documentation.

---

## 🗓️ Day-by-Day

| Day | ENJ | Covenant | Goodness |
|---|---|---|---|
| 1 | `conftest.py` fixtures, `test_models.py` | `test_auth.py`, `test_security.py` skeleton | Auth flow manual tests |
| 2 | **Ship `conftest.py`** (unblocks Covenant), `test_sync.py` | `test_sales_api.py`, `test_inventory_api.py` | Sales flow manual tests, offline queue tests |
| 3 | `test_cli.py`, `test_db_integrity.py` | `test_sync_api.py`, `test_conflicts_api.py` | Inventory + conflict UI tests |
| 4 | Fix bugs found by Covenant's tests | `test_reports_api.py`, security parametrize | Report UI tests, compile test report |
| 5 | Buffer / fix remaining bugs | Fix bugs found in testing, buffer | Finalize `TEST_REPORT.md` |

---

## 🚨 Non-negotiable team rules
1. All tests use in-memory SQLite — never `shop.db`
2. Every test is independent — no shared mutable state between tests
3. Every bug found is logged before being fixed — not silently patched
4. Zero pytest failures before Phase 9 begins — no exceptions
5. Goodness documents every manual test — pass or fail
6. Log what shipped each day in `CHANGELOG.md`
7. Blockers stated explicitly
8. No deployment work this phase