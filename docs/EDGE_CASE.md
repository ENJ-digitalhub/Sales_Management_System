# ⚠️ Edge Cases — Sales Management System (Offline-First POS)

> 🚧 **Status: Not yet implemented.** This document describes a planned
> future capability. The current system is single-device, real-time,
> and has no sync engine. See `ARCHITECTURE_CURRENT.md`.

This document outlines critical edge cases that can occur in the system due to offline-first architecture, local networking, and multi-device usage.

The goal is to ensure data integrity, prevent silent failures, and define predictable system behavior under real-world conditions.

---

# 🧠 Core Principle

The system follows a single rule:

> The server (PC or local host) is the only source of truth.

All mobile devices act as clients with temporary local storage and sync capability.

---

# 📡 1. Network & Connectivity Edge Cases

## 1.1 Admin/server goes offline

**Scenario:**
Server PC is shut down or hotspot is disabled.

**Impact:**
Clients cannot sync data. Sales continue in offline queue mode.

**Handling:**
- Enable offline queue storage on mobile
- Show "Disconnected from server" UI banner
- Prevent operations that require server confirmation (e.g. purchase approval)

---

## 1.2 Device disconnects mid-transaction

**Scenario:**
Network drops while sending a sale request.

**Impact:**
Partial or failed transaction submission.

**Handling:**
- Mark transaction as `PENDING_SYNC`
- Retry automatically with exponential backoff when connection returns
- Prevent duplicate submission using unique transaction_id (UUID v4)

---

## 1.3 Wrong network connection

**Scenario:**
Phone connects to a different WiFi network or mobile data instead of the store network.

**Impact:**
Cannot reach local server.

**Handling:**
- Detect server unreachable state
- Prompt user to reconnect to correct network

---

# 🔁 2. Data Consistency Edge Cases

## 2.1 Duplicate transactions

**Scenario:**
Same sale is submitted twice due to retry or network lag.

**Impact:**
Inventory becomes inaccurate.

**Handling:**
- Each transaction carries a UUID v4 `transaction_id` generated on the client
- Server rejects any transaction with a previously seen `transaction_id`

---

## 2.2 Conflicting offline sales

**Scenario:**
Two devices sell the same stock while both offline.

**Impact:**
Stock may go negative or become inconsistent on sync.

**Handling:**
- Server validates stock availability before accepting each offline transaction
- First valid sync wins; remaining conflicting sales are rejected and flagged for manager review

---

## 2.3 Out-of-order sync events

**Scenario:**
Device sends queued events in the wrong order after reconnecting.

**Impact:**
Inventory calculations become incorrect.

**Handling:**
- Server uses its own timestamp (never device timestamp) plus event ordering to validate sequence

---

## 2.4 Partial sync failure

**Scenario:**
Only part of a queued batch is successfully synced.

**Impact:**
Incomplete data state on the server.

**Handling:**
- Each item in the batch is tracked independently:
  - `pending`
  - `synced`
  - `failed`
  - `conflict`
- Only failed items are retried — successfully synced items are not re-sent

---

# 📱 3. Device Storage Edge Cases

## 3.1 App crash before sync

**Scenario:**
Phone shuts down or crashes before sending queued data.

**Impact:**
Risk of losing unsynced transactions.

**Handling:**
- Use persistent storage (SQLite) for the offline queue
- Never rely on memory-only queues — all queue items are written to disk immediately

---

## 3.2 Cache becomes outdated

**Scenario:**
Device stays offline for an extended period.

**Impact:**
Wrong stock levels displayed to user.

**Handling:**
- Force full sync on reconnection
- Refresh local product cache from server before resuming normal operations

---

## 3.3 Storage overflow

**Scenario:**
Large number of offline transactions stored locally.

**Impact:**
App slows down or fails.

**Handling:**
- Monitor queue size
- Auto-sync when a threshold is reached
- Queue size limits to be defined in a future iteration

---

# 🧾 4. Inventory & Business Logic Edge Cases

## 4.1 Insufficient stock at sale time

**Scenario:**
Any item in a sale has insufficient stock.

**Impact:**
Invalid inventory state if partial commits are allowed.

**Handling:**
- Online mode: reject the ENTIRE sale — no partial commits allowed
- Offline mode: allow sale optimistically, validate on sync
- On sync rejection: flag for manager review, restore local stock delta

---

## 4.2 Simultaneous product updates

**Scenario:**
Admin edits a product (price, stock) while employees are offline.

**Impact:**
Mismatched product state on sync.

**Handling:**
- Products have a `version` field incremented on every update
- Server resolves conflicts by comparing version numbers and applying admin-side changes as authoritative

---

## 4.3 Deleted product used offline

**Scenario:**
Product is soft-deleted on server but still used in an offline sale.

**Impact:**
Sync failure or orphaned transaction.

**Handling:**
- Server rejects transactions referencing soft-deleted products
- Conflict is escalated to manager for resolution
- Device refreshes product list on reconnect

---

# 🛒 5. Purchase Approval Edge Cases

## 5.1 Purchase created while server offline

**Scenario:**
Employee creates a purchase entry while disconnected.

**Impact:**
Purchase exists locally but not on server.

**Handling:**
- Purchase is queued like any other offline transaction
- Synced when connection is restored
- Status remains `pending` until admin explicitly approves

## 5.2 Purchase approved before sync completes

**Scenario:**
Admin approves a purchase from another device before the original purchase entry has finished syncing.

**Impact:**
Race condition on inventory update.

**Handling:**
- Server processes queue sequentially using transaction locking
- Approval can only be granted against a committed purchase record

---

# 🔐 6. Security Edge Cases

## 6.1 Unauthorized device access

**Scenario:**
Unknown device connects to the store network.

**Impact:**
Unauthorized sales or data access.

**Handling:**
- All devices require valid JWT authentication
- Admin manages device whitelist — unknown devices are rejected at connection

---

## 6.2 Token reuse or tampering

**Scenario:**
Stolen or modified authentication token.

**Impact:**
Unauthorized API access.

**Handling:**
- Server-side token validation on every request
- Token expiration and session invalidation on new login

---

# 🔄 7. Sync Behavior Edge Cases

## 7.1 Infinite retry loop

**Scenario:**
Device keeps retrying failed sync requests.

**Impact:**
Server overload.

**Handling:**
- Exponential backoff: 1s → 2s → 4s → 8s → stop
- Maximum 5 retries, then mark as FAILED and notify manager

---

## 7.2 Multiple devices syncing large backlog simultaneously

**Scenario:**
Multiple devices reconnect and push large transaction backlogs at the same time.

**Impact:**
Race conditions on the server.

**Handling:**
- Server processes queue sequentially per device
- Transaction locking prevents simultaneous writes to the same record

---

# ⚠️ 8. Time & Ordering Edge Cases

## 8.1 Device time mismatch

**Scenario:**
Phone clock is set incorrectly.

**Impact:**
Wrong transaction ordering and incorrect edit window calculations.

**Handling:**
- Server timestamp is always authoritative
- Device timestamp is used for display only, never for business logic

---

# 🧠 Final System Rule

All edge cases resolve to one principle:

> The server must validate, correct, or reject all client-provided data.

Clients are not trusted sources of truth.

---

# 🚀 Summary

This system is resilient only if:

* Every transaction is uniquely identified with a UUID v4 transaction_id
* Server is authoritative on all timestamps and stock values
* Offline data is treated as temporary and unconfirmed
* Sync is always validated before commit
* Products are soft-deleted to preserve historical integrity
* Sales are all-or-nothing — no partial commits

Without these rules, offline-first systems silently corrupt data over time.