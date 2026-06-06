# 📡 SYNC ENGINE — Sales Management System (Offline-First)
## 1. 🧠 CORE PURPOSE

The Sync Engine is responsible for:

synchronizing offline client actions with the server
ensuring server remains the single source of truth
resolving conflicts via structured rules + manager intervention
guaranteeing idempotent, lossless transaction processing
## 2. 🏗️ HIGH-LEVEL ARCHITECTURE
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
## 3. 📦 SYNC QUEUE STRUCTURE (CLIENT)

Each offline action is stored as:

{
  "id": "local_uuid",
  "transaction_id": "global_uuid_v4",
  "entity_type": "sale | product | user | etc",
  "operation": "CREATE | UPDATE | DELETE",
  "payload": { ...full request body... },
  "status": "PENDING | SYNCED | FAILED | CONFLICT",
  "retry_count": 0,
  "last_attempt_at": null,
  "created_at": "device_timestamp"
}
Rules:
Stored in SQLite
Survives app reload + restart
Fully persistent queue
No memory-only data allowed
## 4. 🆔 IDEMPOTENCY SYSTEM
Strategy:
Each transaction uses UUID v4 generated on client
Server enforces uniqueness using transaction_id
Behavior:
If transaction_id exists → IGNORE duplicate
If new → process normally
## 5. 🕒 TIME SYSTEM
Rules:
Server timestamp = authoritative
Device timestamp = display only
Why:

Prevents:

clock manipulation
ordering bugs
sync inconsistencies
## 6. 🔁 SYNC TRIGGER SYSTEM

Sync is triggered by:

Primary:
immediate reconnect detection
Secondary:
background interval retry loop
Interval behavior:
active until:
success OR
max retry reached (5)
## 7. 📡 SYNC BATCHING STRATEGY
Batch size:
10–20 transactions per request
Endpoint:
POST /sync/push
Why batching:
reduces network overhead
improves throughput
prevents server overload
## 8. 🔄 RETRY ENGINE
Strategy:

Exponential backoff:

Retry 1 → 1s
Retry 2 → 2s
Retry 3 → 4s
Retry 4 → 8s
Retry 5 → STOP
After failure:
mark as FAILED
notify user/manager
require manual retry
## 9. ⚖️ CONFLICT RESOLUTION ENGINE

All conflicts are isolated and escalated, not auto-overwritten.

9.1 Conflict Types
A. Stock Conflict

Example: offline sale exceeds stock

✔ Behavior:

reject affected items
flag for manager decision
B. Deleted Product Conflict

✔ Behavior:

flag for manager resolution
C. Duplicate Transaction

✔ Behavior:

server ignores duplicate via transaction_id
D. General Conflict

✔ Behavior:

isolate + flag
9.2 Conflict Flow
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
## 10. 🔁 SYNC PROCESS FLOW
10.1 Push Flow
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
10.2 Partial Failure Rule
Process ALL items in batch
Never stop mid-batch
Return individual results
## 11. 📥 SERVER → CLIENT SYNC (PULL)
Endpoint:
GET /sync/pull
Data included:
products
stock updates
price changes
deleted products
user updates
Transport:
WebSocket (primary)
REST fallback
## 12. 🔐 DEVICE AUTHENTICATION
Rules:
JWT required
device_id must match whitelist
only ONE active device per user
If new login occurs:
old device is invalidated immediately
## 13. ⚠️ OFFLINE BEHAVIOR
Stock Handling Offline:
client is allowed to proceed (no strict enforcement)
server corrects during sync
## 14. 🔄 PARTIAL SYNC FAILURE

If item fails at position N:

✔ Behavior:

continue processing remaining items
retry only failed ones later
## 15. 📡 WEBSOCKET SYSTEM

Used for:

real-time stock updates
sync completion notifications
conflict alerts
dashboard refresh triggers
## 16. 🚨 FAILURE ESCALATION RULE

If transaction fails after max retries:

✔ Behavior:

notify user immediately
send to manager dashboard
temporarily block affected operation types if critical
## 17. 🧠 FINAL SYSTEM GUARANTEE

This sync engine guarantees:

no duplicate transactions
no silent data loss
controlled offline operation
deterministic server reconciliation
manager-controlled conflict resolution