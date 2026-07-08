# 🚀 Phase 6 — Sync Engine
## Sales Management System (Offline-First POS)

**Stack:** Flask · Raw SQLAlchemy 2.0 · SQLite · Vanilla JS · IndexedDB

**Team:**
| Person | Owns |
|---|---|
| **Goodness** | `frontend/` — sync dispatcher, retry logic, sync status UI, reconnect detection |
| **Covenant** | `backend/routes/`, `controllers/`, `services/` — sync endpoints, validation, conflict detection |
| **ENJ** | `backend/sync/queue.py` — full sync engine implementation, `SyncQueue` model wiring |

---

## 🎯 Phase 6 Goal (one sentence)

By end of phase: offline sales queued in IndexedDB are automatically pushed to the server on reconnect, validated, committed or flagged, and the client receives a per-item result — with retry logic, idempotency enforcement, and batch processing all working correctly.

### ⚠️ Critical dependencies
- Covenant's `POST /sync` endpoint is blocked on ENJ's `queue.py` sync engine being functional — **ENJ ships core sync engine by Day 2**
- Goodness's sync dispatcher is blocked on Covenant's endpoint contract — **Covenant ships `POST /sync` by Day 3**
- `SyncQueue` model already exists from Phase 1 stub — ENJ now implements the real logic
- All contracts locked below — agree before coding

---

## 🔒 Locked Contracts (agree before coding)

### POST /sync — Request
```json
{
  "device_id": "string",
  "transactions": [
    {
      "transaction_id": "uuid_v4",
      "entity_type": "sale",
      "operation": "CREATE",
      "payload": {
        "items": [],
        "payment_method": "cash | transfer | pos"
      },
      "created_at": "device_timestamp"
    }
  ]
}
```

### POST /sync — Response
```json
{
  "success": true,
  "results": [
    {
      "transaction_id": "uuid_v4",
      "status": "synced | failed | conflict",
      "message": "string (optional)",
      "server_id": "uuid (if synced)"
    }
  ]
}
```

### GET /sync/pull — Response
```json
{
  "success": true,
  "data": {
    "products": [],
    "users": [],
    "deleted_product_ids": []
  },
  "server_timestamp": "timestamp"
}
```

---

## 📋 Business Rules (non-negotiable)

- Batch size: **10–20 transactions per push request**
- Max retries: **5** — after 5 failures mark as `FAILED`, stop retrying automatically
- Retry strategy: **exponential backoff** — 1s, 2s, 4s, 8s, stop
- Idempotency: if `transaction_id` already exists in DB — ignore silently, return `synced`
- Server timestamp is authoritative — device `created_at` is stored but never used for ordering
- Process **all items in a batch** — never stop mid-batch on a single failure
- Return per-item result for every transaction in the batch
- Stock validation happens server-side on sync — offline sales that exceed real stock are flagged as `conflict`
- Deleted product references are flagged as `conflict`
- Duplicate `transaction_id` is ignored — not an error
- Sync queue on client is IndexedDB — not localStorage
- `GET /sync/pull` is called on every reconnect before pushing — client refreshes local cache first

---

## 👤 ENJ — Sync Engine Implementation

### Execution Checklist
- [ ] `backend/sync/queue.py`: implement `push_to_queue(transactions, device_id, session)` — ingests batch, checks idempotency, queues valid transactions
- [ ] `backend/sync/queue.py`: implement `process_queue(session)` — processes queued transactions in order, validates each, commits or flags
- [ ] `backend/sync/queue.py`: implement `validate_transaction(transaction, session)` — stock check, product existence check, idempotency check
- [ ] `backend/sync/queue.py`: implement `resolve_conflict(transaction_id, resolution, session)` — applies manager resolution to a flagged conflict
- [ ] `SyncQueue` model: update `status` correctly — `pending → synced | failed | conflict`
- [ ] `retry_count` and `last_attempt_at` updated on every attempt
- [ ] All sync operations wrapped in transactions — partial commits never happen
- [ ] `AuditLog` entry created for every sync commit and every conflict flag

### Socratic Task Spec
**Objective:** Implement the full sync engine — ingestion, validation, idempotency enforcement, conflict detection, and status tracking — so Covenant's endpoint can call it and get deterministic per-item results.

**Constraints:**
- `process_queue()` processes all items — never stops on a single failure
- Idempotency check: query `SyncQueue` by `transaction_id` before processing
- Stock validation reuses the same logic from `sales_service.py` — do not duplicate it
- `resolve_conflict()` accepts `resolution: "approve" | "reject"` — approve commits the transaction, reject marks it `failed`
- All DB writes inside a single transaction per batch item — if one item's commit fails, only that item rolls back

**Required Documentation:**
- SQLAlchemy 2.0 — nested transactions and savepoints
- `SYNC_ENGINE.md` — full reference
- `EDGE_CASE.md` — §§1, 2, 6

**Expected Output:** Calling `process_queue()` with a batch of 5 transactions returns 5 individual results. A duplicate `transaction_id` returns `synced` without a second DB write. A sale that exceeds stock returns `conflict` and leaves DB unchanged.

**Guiding questions for ENJ:**
1. `process_queue()` must process all items even if one fails — how do you structure the loop so a failed item's exception doesn't abort the entire batch, and what SQLAlchemy construct lets you roll back just one item without rolling back the whole session?
2. Idempotency check queries `SyncQueue` by `transaction_id` — at what point in the process do you check this, and what exactly do you return if the ID already exists?

---

## 👤 Covenant — Sync Endpoints

### Execution Checklist
- [ ] `backend/routes/sync.py`: Blueprint with routes — `POST /sync`, `GET /sync/pull`, `POST /sync/resolve`
- [ ] `backend/controllers/sync_controller.py`: request/response for all three routes
- [ ] `backend/services/sync_service.py`:
  - `push_sync(device_id, transactions, session)` — calls ENJ's `push_to_queue()` and `process_queue()`, returns per-item results
  - `pull_sync(session)` — returns current products, active users, deleted product IDs
  - `resolve_conflict(transaction_id, resolution, user_id, session)` — calls ENJ's `resolve_conflict()`, logs audit
- [ ] All sync routes protected with `@require_auth`
- [ ] `POST /sync/resolve` protected with `@require_role('manager', 'admin')`
- [ ] `backend/app.py`: register sync blueprint
- [ ] Validate `device_id` matches authenticated user's device from JWT
- [ ] Batch size enforced — reject if `transactions` array exceeds 20 items

### Socratic Task Spec
**Objective:** Build the sync endpoints that receive client batches, pass them to ENJ's engine, and return deterministic per-item results — with device validation and batch size enforcement.

**Constraints:**
- Services accept session as parameter — never open their own
- `device_id` in request body must match `device_id` in JWT — reject with `403` if mismatch
- Batch size > 20 returns `400` with clear message
- `pull_sync()` returns server timestamp — use `datetime.utcnow()`, never client time
- `resolve_conflict()` creates `AuditLog` entry on every resolution

**Required Documentation:**
- `SYNC_ENGINE.md` §§10, 11
- SQLAlchemy 2.0 — session handling

**Expected Output:** `POST /sync` with 3 valid transactions returns 3 `synced` results. `POST /sync` with a duplicate `transaction_id` returns `synced` for that item without a second write. `GET /sync/pull` returns current product list and server timestamp.

**Guiding questions for Covenant:**
1. `device_id` validation — the JWT contains a `device_id` and the request body also contains one. Where exactly in the controller or service do you compare these, and what do you return if they don't match?
2. `pull_sync()` needs to return deleted product IDs so the client can remove them from local cache — how do you get a list of inactive product IDs without returning the full soft-deleted product rows?

---

## 👤 Goodness — Sync Dispatcher + Retry Logic + UI

### Execution Checklist
- [ ] `frontend/modules/sync.js`: new module — owns all sync logic
- [ ] `getQueuedTransactions()` — reads pending items from IndexedDB
- [ ] `pushBatch(transactions)` — sends batch of up to 20 to `POST /sync`, returns per-item results
- [ ] `processSyncResults(results)` — updates IndexedDB status per item: `synced | failed | conflict`
- [ ] `retryFailed()` — retries only `failed` items, respects exponential backoff, stops after 5 attempts
- [ ] `pullAndRefresh()` — calls `GET /sync/pull` on reconnect, updates local product cache
- [ ] Reconnect detection — listen for `window.addEventListener('online', ...)` — trigger sync automatically
- [ ] `frontend/modules/sync.js`: `syncNow()` — manual trigger, callable from UI button
- [ ] Sync status UI — persistent banner: "Offline Mode" when disconnected
- [ ] "Sync Now" button — visible when online, shows pending count
- [ ] Per-transaction sync status in history — `Synced ✓` (green), `Not Synced` (amber), `Failed` (red), `Conflict` (flagged)
- [ ] After successful sync — refresh product list from local cache updated by `pullAndRefresh()`

### Socratic Task Spec
**Objective:** Build the full client-side sync dispatcher — reading from IndexedDB, batching, pushing, handling per-item results, retrying with backoff, and updating UI state on every status change.

**Constraints:**
- Vanilla JS only
- Sync logic lives entirely in `sync.js` — no other module touches IndexedDB sync state directly
- Batch size hard cap: 20 transactions per push
- Exponential backoff: 1s, 2s, 4s, 8s — implemented with `setTimeout`, not `setInterval`
- Green is reserved for `synced` state only — per design system
- `window.online` event triggers `pullAndRefresh()` first, then `pushBatch()`

**Required Documentation:**
- MDN: IndexedDB API
- MDN: online/offline events
- `SYNC_ENGINE.md` §§6, 7, 8
- `EDGE_CASE.md` §§1, 2, 3

**Expected Output:** Going offline queues a sale in IndexedDB. Coming back online triggers automatic sync. The transaction history updates from `Not Synced` to `Synced` after successful push. After 5 failed retries the item shows `Failed` and stops retrying.

**Guiding questions for Goodness:**
1. Exponential backoff uses `setTimeout` — how do you implement 5 retries with increasing delays without nesting 5 `setTimeout` calls inside each other? Think recursion or a loop with a delay counter.
2. `processSyncResults()` receives per-item results and needs to update each item's status in IndexedDB — what's the correct IndexedDB operation to update an existing record, and how do you match the result's `transaction_id` to the right IndexedDB entry?

---

## ✅ Definition of Done — Phase 6 (whole team)

A Phase 6 feature is **only** done if:
- [ ] `POST /sync` with valid transactions returns per-item `synced` results
- [ ] `POST /sync` with duplicate `transaction_id` returns `synced` without second DB write
- [ ] `POST /sync` with stock conflict returns `conflict` for that item, others process normally
- [ ] `POST /sync` with deleted product returns `conflict` for that item
- [ ] `GET /sync/pull` returns current products and server timestamp
- [ ] `POST /sync/resolve` with `approve` commits the conflicted transaction
- [ ] `POST /sync/resolve` with `reject` marks it `failed`
- [ ] Batch size > 20 returns `400`
- [ ] Going offline queues sale in IndexedDB
- [ ] Coming online triggers automatic sync
- [ ] Exponential backoff works — retries at 1s, 2s, 4s, 8s
- [ ] After 5 failures item is marked `FAILED` and stops retrying
- [ ] Transaction history shows correct sync status per item
- [ ] "Offline Mode" banner shows when disconnected
- [ ] "Sync Now" button triggers manual sync

**Out of scope this phase:** conflict resolution UI, deployment.

---

## 🗓️ Day-by-Day

| Day | ENJ | Covenant | Goodness |
|---|---|---|---|
| 1 | `validate_transaction()`, idempotency check | `sync.py` Blueprint, route stubs | `sync.js` module skeleton, `getQueuedTransactions()` |
| 2 | **Ship `push_to_queue()` + `process_queue()`** (unblocks Covenant) | `push_sync()` service, batch size enforcement | `pushBatch()`, `processSyncResults()` |
| 3 | `resolve_conflict()`, status tracking | **Ship `POST /sync`** (unblocks Goodness), `pull_sync()` | Wire reconnect detection, `pullAndRefresh()` |
| 4 | `AuditLog` on sync events, buffer | `POST /sync/resolve`, register blueprint | `retryFailed()` with exponential backoff |
| 5 | Buffer / help unblock | Buffer | Sync status UI, offline banner, Sync Now button |

---

## 🚨 Non-negotiable team rules
1. All contracts above are locked
2. Process all batch items — never abort mid-batch
3. Idempotency enforced on every transaction — no exceptions
4. Server timestamp is authoritative — never use device time for ordering
5. Green reserved for synced state only — amber for pending, red for failed
6. Services accept session as parameter — never open their own
7. Log what shipped each day in `CHANGELOG.md`
8. Blockers stated explicitly
9. No conflict resolution UI or deployment work this phase