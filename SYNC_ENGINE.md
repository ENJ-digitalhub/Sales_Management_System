# 📡 SYNC ENGINE — Sales Management System (Offline-First)

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
Batch API (/sync/push)
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
  "entity_type": "sale | product | user | etc",
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
* Fully persistent queue
* No memory-only data allowed

---

# 4. 🆔 IDEMPOTENCY SYSTEM

Strategy:

* Each transaction uses UUID v4 generated on the client
* Server enforces uniqueness using `transaction_id`

Behavior:

* If `transaction_id` exists → ignore duplicate
* If new → process normally

---

# 5. 🕒 TIME SYSTEM

Rules:

* Server timestamp is authoritative
* Device timestamp is for display only

Purpose:

* Prevents clock manipulation
* Avoids ordering bugs
* Eliminates sync inconsistencies

---

# 6. 🔁 SYNC TRIGGER SYSTEM

Sync is triggered by:

Primary:

* Immediate reconnect detection

Secondary:

* Background interval retry loop

Interval continues until:

* Success OR
* Max retry reached (5 attempts)

---

# 7. 📡 SYNC BATCHING STRATEGY

* Batch size: 10–20 transactions per request
* Endpoint: `POST /sync/push`

Purpose:

* Reduce network overhead
* Improve throughput
* Prevent server overload

---

# 8. 🔄 RETRY ENGINE

Exponential backoff strategy:

* Retry 1 → 1s
* Retry 2 → 2s
* Retry 3 → 4s
* Retry 4 → 8s
* Retry 5 → STOP

After max failure:

* Mark as `FAILED`
* Notify user/manager
* Require manual retry

---

# 9. ⚖️ CONFLICT RESOLUTION ENGINE

Conflicts are **never auto-overwritten**. They are isolated and escalated.

## 9.1 Conflict Types

### A. Stock Conflict

Example: offline sale exceeds available stock

Behavior:

* Reject affected items
* Flag for manager decision

---

### B. Deleted Product Conflict

Behavior:

* Flag for manager resolution

---

### C. Duplicate Transaction

Behavior:

* Server ignores duplicate via `transaction_id`

---

### D. General Conflict

Behavior:

* Isolate and flag

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
Server validates JWT
    ↓
For each transaction:
    ↓
Idempotency check
    ↓
Validation (stock, product, etc.)
    ↓
Conflict detection
    ↓
Commit OR Flag
    ↓
Return per-item result
```

## 10.2 Partial Failure Rule

* Process ALL items in batch
* Never stop mid-batch
* Return individual results

---

# 11. 📥 SERVER → CLIENT SYNC (PULL)

Endpoint:

* `GET /sync/pull`

Data includes:

* Products
* Stock updates
* Price changes
* Deleted products
* User updates

Transport:

* WebSocket (primary)
* REST fallback

---

# 12. 🔐 DEVICE AUTHENTICATION

Rules:

* JWT required
* `device_id` must match whitelist
* Only ONE active device per user

If new login occurs:

* Old device is invalidated immediately

---

# 13. ⚠️ OFFLINE BEHAVIOR

Stock Handling:

* Client is allowed to proceed offline
* Server validates and corrects during sync

---

# 14. 🔄 PARTIAL SYNC FAILURE

If item fails at position N:

* Continue processing remaining items
* Retry only failed items later

---

# 15. 📡 WEBSOCKET SYSTEM

Used for:

* Real-time stock updates
* Sync completion notifications
* Conflict alerts
* Dashboard refresh triggers

---

# 16. 🚨 FAILURE ESCALATION RULE

If a transaction fails after max retries:

* Notify user immediately
* Send to manager dashboard
* Temporarily block affected operations if critical

---

# 17. 🧠 FINAL SYSTEM GUARANTEE

This Sync Engine guarantees:

* No duplicate transactions
* No silent data loss
* Controlled offline operation
* Deterministic server reconciliation
* Manager-controlled conflict resolution

---
