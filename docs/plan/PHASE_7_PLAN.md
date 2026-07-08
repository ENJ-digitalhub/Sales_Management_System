# 🚀 Phase 7 — Conflict Resolution
## Sales Management System (Offline-First POS)

**Stack:** Flask · Raw SQLAlchemy 2.0 · SQLite · Vanilla JS

**Team:**
| Person | Owns |
|---|---|
| **Goodness** | `frontend/` — conflict dashboard, manager review UI, resolution actions |
| **Covenant** | `backend/routes/`, `controllers/`, `services/` — conflict endpoints, resolution logic |
| **ENJ** | `backend/sync/queue.py` — conflict queue, resolution application, audit logging |

---

## 🎯 Phase 7 Goal (one sentence)

By end of phase: every sync conflict is isolated, flagged for manager review, visible in a dedicated dashboard, and resolvable with a single approve or reject action — with the outcome logged in `AuditLog` and the affected transaction updated accordingly.

### ⚠️ Critical dependencies
- Covenant's conflict endpoints are blocked on ENJ's `resolve_conflict()` being fully implemented — **ENJ ships it by Day 2**
- Goodness's conflict UI is blocked on Covenant's `GET /conflicts` endpoint — **Covenant ships it by Day 3**
- Phase 6 sync engine already detects and flags conflicts — this phase builds the resolution layer on top
- All contracts locked below — agree before coding

---

## 🔒 Locked Contracts (agree before coding)

### GET /conflicts — Response
```json
{
  "success": true,
  "conflicts": [
    {
      "transaction_id": "uuid",
      "device_id": "string",
      "entity_type": "sale",
      "operation": "CREATE",
      "conflict_type": "stock | deleted_product | duplicate",
      "payload": {},
      "created_at": "timestamp",
      "status": "conflict"
    }
  ]
}
```

### POST /conflicts/{transaction_id}/resolve — Request
```json
{
  "resolution": "approve | reject",
  "note": "string (optional)"
}
```

### POST /conflicts/{transaction_id}/resolve — Response (success)
```json
{
  "success": true,
  "transaction_id": "uuid",
  "resolution": "approve | reject",
  "resolved_by": "uuid",
  "resolved_at": "timestamp"
}
```

### POST /conflicts/{transaction_id}/resolve — Response (failure)
```json
{
  "success": false,
  "message": "string"
}
```

### GET /conflicts/{transaction_id} — Response
```json
{
  "success": true,
  "conflict": {
    "transaction_id": "uuid",
    "device_id": "string",
    "conflict_type": "stock | deleted_product | duplicate",
    "payload": {},
    "created_at": "timestamp",
    "status": "conflict",
    "resolution_note": "string (optional)"
  }
}
```

---

## 📋 Business Rules (non-negotiable)

- Only **managers and admins** can view and resolve conflicts
- Employees are never shown the conflict dashboard — `403` on all conflict endpoints
- **Approve** — commits the conflicted transaction as-is, deducts stock if applicable, creates sale record
- **Reject** — marks transaction as `failed`, no DB changes, notifies originating device on next pull
- A conflict can only be resolved **once** — attempting to resolve an already-resolved conflict returns `400`
- Every resolution creates an `AuditLog` entry — `resolved_by`, `resolution`, `note`, `resolved_at`
- Stock re-validation happens at approval time — not at conflict detection time
- If stock is still insufficient at approval time — return `failed` with clear message, do not force-commit
- `conflict_type` must be one of: `stock`, `deleted_product`, `duplicate`
- System continues operating normally while conflicts are pending — conflicts never block new sales
- Unresolved conflicts are visible until explicitly resolved — no auto-expiry

---

## 👤 ENJ — Conflict Queue + Resolution Engine

### Execution Checklist
- [ ] `backend/sync/queue.py`: implement `get_conflicts(session)` — returns all `SyncQueue` rows with `status = conflict`
- [ ] `backend/sync/queue.py`: implement `get_conflict(transaction_id, session)` — returns single conflict row
- [ ] `backend/sync/queue.py`: update `resolve_conflict(transaction_id, resolution, user_id, note, session)` — full implementation:
  - `approve` → re-validate stock → commit sale → update `SyncQueue.status` to `synced`
  - `reject` → update `SyncQueue.status` to `failed`
  - Both → create `AuditLog` entry
- [ ] Guard against double resolution — check current status before applying, return error if already resolved
- [ ] `conflict_type` stored in `SyncQueue` metadata or a dedicated field — must be queryable
- [ ] Stock re-validation on approve reuses `sales_service.py` logic — no duplication

### Socratic Task Spec
**Objective:** Implement the full resolution engine — fetching conflicts, validating stock at resolution time, committing or rejecting, and logging every outcome.

**Constraints:**
- `resolve_conflict()` is the single function that applies any resolution — Covenant never writes resolution logic directly
- Stock re-validation on approve must happen inside the same transaction as the sale commit — if validation fails, nothing commits
- Double resolution guard: check `SyncQueue.status != 'conflict'` before proceeding — return a clear error if already resolved
- `AuditLog` entry created regardless of approve or reject outcome

**Required Documentation:**
- SQLAlchemy 2.0 — transactions and savepoints
- `SYNC_ENGINE.md` §9 — conflict resolution flow
- `EDGE_CASE.md` §§2, 4

**Expected Output:** Calling `resolve_conflict()` with `approve` on a stock conflict re-validates stock and either commits the sale or returns a stock error. Calling it with `reject` marks the transaction `failed`. Calling it a second time on the same `transaction_id` returns a clear error.

**Guiding questions for ENJ:**
1. Stock re-validation happens at approval time — the product's stock may have changed since the conflict was flagged. How do you ensure the re-validation reads the current stock level and not a cached value from when the conflict was first detected?
2. Double resolution guard — you check the status before resolving. What's the race condition risk if two managers try to resolve the same conflict simultaneously, and how does a DB transaction protect against it?

---

## 👤 Covenant — Conflict Endpoints

### Execution Checklist
- [ ] `backend/routes/conflicts.py`: Blueprint with routes — `GET /conflicts`, `GET /conflicts/{transaction_id}`, `POST /conflicts/{transaction_id}/resolve`
- [ ] `backend/controllers/conflicts_controller.py`: request/response for all three routes
- [ ] `backend/services/conflicts_service.py`:
  - `get_all_conflicts(session)` — calls ENJ's `get_conflicts()`
  - `get_conflict(transaction_id, session)` — calls ENJ's `get_conflict()`
  - `resolve_conflict(transaction_id, resolution, user_id, note, session)` — calls ENJ's `resolve_conflict()`
- [ ] All routes protected with `@require_role('manager', 'admin')`
- [ ] `backend/app.py`: register conflicts blueprint
- [ ] `resolution` field validated — must be exactly `approve` or `reject`, nothing else
- [ ] `note` field optional — pass `None` if not provided

### Socratic Task Spec
**Objective:** Build the conflict endpoints that surface flagged transactions to managers and pass resolution decisions to ENJ's engine — with strict role enforcement and input validation.

**Constraints:**
- Services accept session as parameter — never open their own
- `resolution` validated in controller before reaching service — invalid value returns `400`
- `resolved_by` populated from `flask.g.user.id` — never from request body
- Service layer calls ENJ's functions — no resolution logic in the service itself

**Required Documentation:**
- Flask Blueprints
- `SYNC_ENGINE.md` §9.2 — conflict flow

**Expected Output:** `GET /conflicts` returns all pending conflicts. `POST /conflicts/{id}/resolve` with `approve` triggers the full resolution flow. Employee hitting any conflict endpoint gets `403`.

**Guiding questions for Covenant:**
1. `resolved_by` comes from the authenticated user in `flask.g` — why should it never come from the request body, even if the client sends it?
2. `GET /conflicts` could return a large number of rows in a busy store — what simple addition to the endpoint would make it more useful for managers without changing the contract significantly?

---

## 👤 Goodness — Conflict Dashboard UI

### Execution Checklist
- [ ] `frontend/pages/conflicts.html`: conflict dashboard — manager/admin only
- [ ] Conflict list — transaction ID (short), conflict type, device, timestamp, status
- [ ] Conflict detail view — full payload, conflict type explanation, product name if applicable
- [ ] Approve button — confirm prompt before submitting
- [ ] Reject button — optional note input, confirm prompt before submitting
- [ ] After resolution — remove conflict from list, show success toast
- [ ] If approve fails due to stock — show clear error: "Stock still insufficient. Sale rejected."
- [ ] Empty state — "No pending conflicts" when list is empty
- [ ] Conflict count badge in navigation — shows number of unresolved conflicts
- [ ] Page hidden from employees — redirect to dashboard with `403` message
- [ ] Conflict list auto-refreshes every 30 seconds — no manual refresh needed

### Socratic Task Spec
**Objective:** Build the conflict dashboard where managers can review flagged transactions, understand what went wrong, and approve or reject with a single action.

**Constraints:**
- Vanilla JS only
- Role check on page load — employee sees `403` message, not the dashboard
- Approve and reject both require a confirmation prompt before submitting
- Auto-refresh uses `setInterval` — clears and re-renders the list every 30 seconds
- Conflict count badge in nav fetches `GET /conflicts` on page load and on every resolution

**Required Documentation:**
- `FRONTEND_SPEC.md` §10 — role permissions
- MDN: fetch API
- `SYNC_ENGINE.md` §9.2 — conflict flow

**Expected Output:** Conflict dashboard loads all pending conflicts. Approving one removes it from the list and shows a toast. Rejecting one with a note removes it and shows a toast. If approve fails due to stock the error is shown clearly without removing the conflict from the list.

**Guiding questions for Goodness:**
1. Auto-refresh runs every 30 seconds — what happens to the auto-refresh timer if the manager navigates away from the page? How do you clean it up to avoid memory leaks?
2. The conflict detail view needs to explain what went wrong in plain language — "Stock conflict" means nothing to a non-technical manager. How do you map `conflict_type` values to human-readable explanations in the UI?

---

## ✅ Definition of Done — Phase 7 (whole team)

A Phase 7 feature is **only** done if:
- [ ] `GET /conflicts` returns all pending conflicts
- [ ] `GET /conflicts/{id}` returns single conflict detail
- [ ] `POST /conflicts/{id}/resolve` with `approve` commits the sale if stock is sufficient
- [ ] `POST /conflicts/{id}/resolve` with `approve` returns stock error if stock is now insufficient
- [ ] `POST /conflicts/{id}/resolve` with `reject` marks transaction `failed`
- [ ] Double resolution attempt returns `400`
- [ ] Every resolution creates an `AuditLog` entry
- [ ] Employee hitting any conflict endpoint gets `403`
- [ ] Conflict dashboard loads and displays all pending conflicts
- [ ] Approve and reject both require confirmation prompt
- [ ] Successful resolution removes conflict from list and shows toast
- [ ] Stock-insufficient approval shows clear error without removing conflict
- [ ] Conflict count badge shows correct number in navigation
- [ ] Auto-refresh updates list every 30 seconds
- [ ] Empty state shown when no conflicts pending
- [ ] Page hidden from employees

**Out of scope this phase:** testing suite, deployment.

---

## 🗓️ Day-by-Day

| Day | ENJ | Covenant | Goodness |
|---|---|---|---|
| 1 | `get_conflicts()`, `get_conflict()`, conflict_type storage | `conflicts.py` Blueprint, route stubs | `conflicts.html` shell, conflict list fetch |
| 2 | **Ship `resolve_conflict()`** full implementation (unblocks Covenant) | `conflicts_service.py` — all three functions | Conflict detail view, approve/reject buttons |
| 3 | Double resolution guard, stock re-validation | **Ship all conflict endpoints** (unblocks Goodness) | Wire approve/reject to endpoints, confirmation prompts |
| 4 | `AuditLog` on all resolutions, buffer | Register blueprint, input validation, buffer | Toast messages, error states, empty state |
| 5 | Buffer / help unblock | Buffer | Conflict count badge, auto-refresh, role check |

---

## 🚨 Non-negotiable team rules
1. All contracts above are locked
2. Stock re-validation happens at approval time — never trust the stale conflict payload
3. Double resolution is always blocked — check status before applying
4. `resolved_by` always comes from `flask.g` — never from request body
5. `AuditLog` entry on every resolution — no exceptions
6. Services accept session as parameter — never open their own
7. System never blocks new sales due to pending conflicts
8. Log what shipped each day in `CHANGELOG.md`
9. Blockers stated explicitly
10. No testing suite or deployment work this phase