🚀 Phase 4 — Offline Sync + Conflict Prevention Week

Sales Management System (Offline-First POS)

Stack confirmed: Flask (latest, app factory pattern) · Raw SQLAlchemy 2.0 (no Flask-SQLAlchemy extension) · SQLite · Vanilla JS frontend · JWT · Offline Queue

Team:

Person| Owns
Obinna| "frontend/", offline queue (client-side), sync UI, queue recovery
Covenant| "backend/routes/", "controllers/", "services/", sync processing, idempotency
ENJ| "backend/models/", "backend/sync/", "database/", queue persistence

---

🎯 Phase 4 Goal (one sentence)

By end of week: the system works offline, stores pending operations safely, reconnects automatically, and synchronizes without duplicates or data corruption.

⚠️ Critical dependency

Covenant cannot process sync safely until ENJ ships the final "SyncQueue" persistence structure and status lifecycle. Obinna cannot implement queue recovery until Covenant defines the sync contract and response structure.

Agree on queue states and sync payload format before coding.

---

👤 ENJ — Database + Queue Persistence

Execution Checklist

- [ ] Expand "backend/models/sync_queue.py"

Fields:

- "id"
- "transaction_id"
- "device_id"
- "entity_type"
- "operation"
- "payload"
- "status"
- "retry_count"
- "last_attempt_at"
- "created_at"
- "updated_at"

Statuses:

pending
processing
synced
failed
conflict

- [ ] Create "sync_logs.py"

Fields:

- "id"

- "queue_id"

- "result"

- "created_at"

- [ ] Update "database/schema.sql"

- [ ] Extend CLI:
  
  - queue reset
  - queue inspection

- [ ] Create queue repository helpers

Socratic Task Spec

Objective: Persist offline operations safely and create recoverable sync infrastructure.

Constraints:

- Queue survives restart
- Payload remains immutable
- Queue entries never disappear silently

Required Documentation:

- SQLAlchemy transaction handling
- Queue architecture basics
- SQLite locking behavior

Expected Output:

python cli/cli.py setup

creates queue infrastructure and sync tables.

Guiding questions for ENJ (don't answer yet — sit with these):

1. If sync fails halfway, which state should remain?
2. Should queue records be deleted or archived?

---

👤 Covenant — Backend API + Sync Engine

Execution Checklist

- [ ] "backend/routes/sync.py"
- [ ] "backend/controllers/sync_controller.py"
- [ ] "backend/services/sync_service.py"
- [ ] "backend/services/idempotency_service.py"
- [ ] "backend/utils/conflict_resolution.py"

Implement:

- [ ] "POST /sync"
- [ ] "GET /sync/status"
- [ ] "POST /sync/retry"

Business Rules:

- [ ] Queue processing
- [ ] Idempotency validation
- [ ] Duplicate prevention
- [ ] Retry handling
- [ ] Partial failure recovery
- [ ] Conflict detection
- [ ] Atomic processing
- [ ] Transaction-safe commits

Validation split:

Controller →

- request validation
- response formatting

Service →

- sync rules
- retries
- queue updates

Socratic Task Spec

Objective: Synchronize queued operations safely and guarantee identical requests never process twice.

Constraints:

- No SQL in routes
- No direct queue mutation in controllers
- Sync must be resumable
- Queue updates occur in one transaction

Required Documentation:

- Idempotency design
- SQLAlchemy transaction scope
- Distributed retry patterns

Expected Output:

Submitting:

POST /sync

results in:

success
or
recoverable failure

never corrupted state.

Guiding questions for Covenant (don't answer yet — sit with these):

1. If the same sale arrives three times, how does the system recognize it?
2. What happens if sync succeeds but acknowledgment fails?

---

👤 Obinna — Frontend + Offline Experience

Execution Checklist

- [ ] "frontend/services/sync.js"
- [ ] "frontend/storage/queue.js"
- [ ] "frontend/components/sync-status.js"

Build:

- [ ] Offline detection
- [ ] Queue creation
- [ ] Queue persistence
- [ ] Retry button
- [ ] Queue indicator
- [ ] Sync progress
- [ ] Conflict banner
- [ ] Reconnect recovery

Queue Record Shape:

transaction_id
entity_type
operation
payload
status
retry_count
created_at

Socratic Task Spec

Objective: Build a reliable offline experience while treating backend sync as source of truth.

Constraints:

- IndexedDB only
- No silent queue deletion
- Queue survives refresh

Required Documentation:

- IndexedDB
- Browser offline events
- Queue processing concepts

Expected Output:

User can:

- disconnect
- create actions
- reconnect
- sync successfully

without losing data.

Guiding questions for Obinna (don't answer yet — sit with these):

1. Should users see queued items immediately?
2. What information is necessary to retry intelligently?

---

✅ Definition of Done — Phase 4 (whole team)

A Phase 4 feature is only done if:

- [ ] Offline actions persist
- [ ] Sync completes after reconnect
- [ ] Duplicate sync requests do not duplicate data
- [ ] Failed sync can retry safely
- [ ] Queue survives restart
- [ ] Layer chain remains:
  route → controller → service → model

Out of scope this week (do not touch):
analytics, reports, exports, dashboards

---

🗓️ Suggested Day-by-Day

Day| ENJ| Covenant| Obinna
1| Queue model expansion| Sync blueprint| Queue storage
2| Sync logs| Idempotency| Offline detection
3| Queue helpers| Retry engine| Queue UI
4| Schema updates| Conflict handling| Reconnect recovery
5| Buffer| Buffer| Polish

---

🚨 Non-negotiable team rules (carried over)

1. Same operation must never execute twice.
2. Queue entries are immutable after creation.
3. Sync must recover after interruption.
4. No reports or analytics this week — scope creep kills Phase 4.