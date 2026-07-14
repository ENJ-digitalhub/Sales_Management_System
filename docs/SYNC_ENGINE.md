# 📡 SYNC ENGINE — Sales Management System (Offline-First)

> 🚧 **Status: Not yet implemented.** This document describes a planned
> future capability. The current system is single-device, real-time,
> and has no sync engine. See `ARCHITECTURE_CURRENT.md`.

---

# 📚 DOCUMENT STRUCTURE

1. Core Purpose
2. High-Level Architecture
3. Sync Queue Structure (Client)
4. Idempotency System
5. Time System
6. Sync Trigger System
7. Sync Batching Strategy
8. Retry Engine
9. Conflict Resolution Engine
10. Sync Process Flow
11. Server → Client Sync (Pull)
12. Device Authentication
13. Offline Behavior
14. Partial Sync Failure
15. WebSocket System
16. Failure Escalation Rule
17. Final System Guarantee

---

# 1. 🧠 CORE PURPOSE

The Sync Engine is responsible for:

* Synchronizing offline client actions with the server
* Ensuring the server remains the single source of truth
* Resolving conflicts via structured rules and manager intervention
* Guaranteeing idempotent and lossless transaction processing

---

# 2. 🏗️ HIGH-LEVEL ARCHITECTURE

```
Client (Offline First)
    ↓
Local SQLite Sync Queue
    ↓
Sync Dispatcher (Background + Reconnect Trigger)
    ↓
Batch API (POST /sync)
    ↓
Server Sync Engine
    ↓
Validation Layer
    ↓
Conflict Resolution Engine
    ↓
Database Commit (Source of Truth)
    ↓
WebSocket Broadcast (Live Update)
```

---

# 3. 📦 SYNC QUEUE STRUCTURE (CLIENT)

Each offline action is stored as:

```json
{
  "id": "local_uuid",
  "transaction_id": "global_uuid_v4",
  "entity_type": "sale | product | purchase | user",
  "operation": "CREATE | UPDATE | DELETE",
  "payload": { "...full request body..." },
  "status": "PENDING | SYNCED | FAILED | CONFLICT",
  "retry_count": 0,
  "last_attempt_at": null,
  "created_at": "device_timestamp"
}
```

Rules:

* Stored in SQLite
* Survives app reload and restart
* Fully persistent — no memory-only data allowed

---

# 4. 🆔 IDEMPOTENCY SYSTEM

Strategy:

* Each transaction uses UUID v4 generated on the client at creation time
* Server enforces uniqueness using `transaction_id`

Behavior:

* If `transaction_id` already exists in the database → silently ignore
* If new → process normally

This prevents duplicate transactions from retry storms or network lag.

---

# 5. 🕒 TIME SYSTEM

Rules:

* Server timestamp is authoritative for all business logic
* Device timestamp is stored for reference only — never used for ordering or edit window calculations

Purpose:

* Prevents clock manipulation
* Avoids ordering bugs
* Eliminates sync inconsistencies from misconfigured device clocks

---

# 6. 🔁 SYNC TRIGGER SYSTEM

Sync is triggered by:

Primary:

* Immediate reconnect detection

Secondary:

* Background interval retry loop

Interval continues until:

* All pending items are synced, OR
* Max retries reached (5 attempts per item)

---

# 7. 📡 SYNC BATCHING STRATEGY

* Batch size: 10–20 transactions per request
* Endpoint: `POST /sync`

Purpose:

* Reduce network overhead
* Improve throughput
* Prevent server overload from large backlogs

---

# 8. 🔄 RETRY ENGINE

Exponential backoff strategy:

* Retry 1 → 1s
* Retry 2 → 2s
* Retry 3 → 4s
* Retry 4 → 8s
* Retry 5 → STOP

After max failure:

* Mark transaction as `FAILED`
* Notify user and manager dashboard
* Require manual retry — no automatic re-queuing

---

# 9. ⚖️ CONFLICT RESOLUTION ENGINE

Conflicts are **never auto-overwritten**. They are isolated and escalated.

## 9.1 Conflict Types

### A. Stock Conflict

Scenario: offline sale quantity exceeds available server stock.

Behavior:

* Reject the affected sale entirely (all-or-nothing rule applies)
* Flag for manager decision

---

### B. Soft-Deleted Product Conflict

Scenario: product was soft-deleted on server while device was offline.

Behavior:

* Server rejects transactions referencing `is_active = false` products
* Flag for manager resolution
* Device refreshes product list on reconnect

---

### C. Duplicate Transaction

Scenario: same `transaction_id` submitted more than once.

Behavior:

* Server ignores duplicate silently
* No error returned — idempotent by design

---

### D. Purchase Conflict

Scenario: purchase entry synced but product was soft-deleted before admin approves it.

Behavior:

* Server rejects the approval
* Flag for manager resolution

---

### E. General Conflict

Behavior:

* Isolate, flag, and escalate

---

## 9.2 Conflict Flow

```
Detect Conflict
    ↓
Mark as CONFLICT
    ↓
Store in Conflict Queue
    ↓
Notify Manager (WebSocket)
    ↓
Manager Decision UI
    ↓
Apply Resolution
    ↓
Re-sync or Commit
```

---

# 10. 🔁 SYNC PROCESS FLOW

## 10.1 Push Flow

```
Client sends batch
    ↓
Server validates JWT + device whitelist
    ↓
For each transaction:
    ↓
Idempotency check (transaction_id)
    ↓
Validation (stock, product is_active, etc.)
    ↓
Conflict detection
    ↓
Commit OR Flag
    ↓
Return per-item result
```

## 10.2 Partial Failure Rule

* Process ALL items in the batch
* Never stop mid-batch on a single failure
* Return individual result per item: `success | failed | conflict`

---

# 11. 📥 SERVER → CLIENT SYNC (PULL)

Endpoint:

* `GET /sync/pull`

Data includes:

* Active products (is_active = true only)
* Stock updates
* Price changes
* Soft-deleted product IDs (so client removes them from local cache)
* User updates

Transport:

* WebSocket (primary)
* REST fallback

---

# 12. 🔐 DEVICE AUTHENTICATION

Rules:

* JWT required on every request
* `device_id` must match admin whitelist
* Only ONE active device session per user

If new login occurs on a different device:

* Old device session is invalidated immediately

---

# 13. ⚠️ OFFLINE BEHAVIOR

Stock Handling:

* Client applies optimistic stock deduction locally on offline sales
* Server validates and corrects the actual stock during sync
* If server rejects: local stock delta is reversed and manager is notified

---

# 14. 🔄 PARTIAL SYNC FAILURE

If an item fails at any position in the batch:

* Continue processing all remaining items
* Retry only the failed items on next sync cycle
* Successfully synced items are not re-sent

---

# 15. 📡 WEBSOCKET SYSTEM

Used for:

* Real-time stock updates after sales and purchase approvals
* Sync completion notifications
* Conflict alerts to manager dashboard
* Dashboard refresh triggers

---

# 16. 🚨 FAILURE ESCALATION RULE

If a transaction fails after max retries:

* Mark as FAILED
* Notify user immediately via in-app alert
* Send to manager dashboard
* Temporarily block affected operations if critical (e.g. further sales of conflicting product)

---

# 17. 🧠 FINAL SYSTEM GUARANTEE

This Sync Engine guarantees:

* No duplicate transactions (idempotency via UUID v4)
* No silent data loss (persistent SQLite queue)
* Controlled offline operation (optimistic local, validated on sync)
* Deterministic server reconciliation
* Manager-controlled conflict resolution — no auto-overwrite