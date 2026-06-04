# ⚠️ Edge Cases — Sales Management System (Offline-First POS)

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
- PC server is shut down or hotspot is disabled.

**Impact:**
- Clients cannot sync data.
- Sales may continue in offline queue mode (if enabled).

**Handling:**
- Enable offline queue storage on mobile.
- Show “Disconnected from server” UI state.
- Prevent critical operations like final stock confirmation if sync is required.

---

## 1.2 Device disconnects mid-transaction

**Scenario:**
- Network drops while sending a sale request.

**Impact:**
- Partial or failed transaction submission.

**Handling:**
- Mark transaction as `PENDING_SYNC`
- Retry automatically when connection returns
- Prevent duplicate submission using transaction IDs

---

## 1.3 Wrong network connection

**Scenario:**
- Phone connects to different WiFi or mobile data.

**Impact:**
- Cannot reach local server.

**Handling:**
- Detect server unreachable state
- Prompt user to reconnect to correct network

---

# 🔁 2. Data Consistency Edge Cases

## 2.1 Duplicate transactions

**Scenario:**
- Same sale is submitted twice due to retry or lag.

**Impact:**
- Inventory becomes inaccurate.

**Handling:**
- Use unique transaction IDs (idempotency keys)
- Server rejects duplicates automatically

---

## 2.2 Conflicting offline sales

**Scenario:**
- Two devices sell same stock while offline.

**Impact:**
- Stock may go negative or inconsistent on sync.

**Handling:**
- Server validates stock before accepting offline sync
- Reject or partially accept conflicting sales

---

## 2.3 Out-of-order sync events

**Scenario:**
- Device sends events in wrong order after reconnect.

**Impact:**
- Inventory calculations become incorrect.

**Handling:**
- Server uses timestamps + event IDs to reorder or validate logic

---

## 2.4 Partial sync failure

**Scenario:**
- Only part of queued transactions are successfully synced.

**Impact:**
- Incomplete data state.

**Handling:**
- Track sync status per item:
  - `pending`
  - `synced`
  - `failed`
- Retry only failed items

---

# 📱 3. Device Storage Edge Cases

## 3.1 App crash before sync

**Scenario:**
- Phone shuts down before sending queued data.

**Impact:**
- Loss of unsynced transactions.

**Handling:**
- Use persistent storage (SQLite / IndexedDB)
- Never rely on memory-only queues

---

## 3.2 Cache becomes outdated

**Scenario:**
- Device stays offline for long period.

**Impact:**
- Wrong stock displayed to user.

**Handling:**
- Force full sync on reconnection
- Refresh local cache from server

---

## 3.3 Storage overflow

**Scenario:**
- Large number of offline transactions stored.

**Impact:**
- App slows or fails.

**Handling:**
- Implement queue size limits
- Auto-sync when threshold is reached

---

# 🧾 4. Inventory & Business Logic Edge Cases

## 4.1 Negative stock prevention failure

**Scenario:**
- Offline sales exceed actual stock.

**Impact:**
- Inventory becomes invalid.

**Handling:**
- Server enforces stock validation on sync
- Reject invalid sales or flag for review

---

## 4.2 Simultaneous product updates

**Scenario:**
- Admin edits product while employees are offline.

**Impact:**
- Mismatched product state on sync.

**Handling:**
- Versioning system for products
- Server resolves conflicts using latest version or admin priority

---

## 4.3 Deleted product used offline

**Scenario:**
- Product deleted on server but still used offline.

**Impact:**
- Sync failure or orphaned transaction.

**Handling:**
- Server rejects invalid product references
- Device refreshes product list on reconnect

---

# 🔐 5. Security Edge Cases

## 5.1 Unauthorized device access

**Scenario:**
- Unknown device connects to network.

**Impact:**
- Unauthorized sales or data access.

**Handling:**
- Require authentication (JWT)
- Whitelist allowed devices or users

---

## 5.2 Token reuse or tampering

**Scenario:**
- Stolen or modified authentication token.

**Impact:**
- Unauthorized API access.

**Handling:**
- Server-side token validation
- Expiration + refresh mechanism

---

# 🔄 6. Sync Behavior Edge Cases

## 6.1 Infinite retry loop

**Scenario:**
- Device keeps retrying failed sync requests.

**Impact:**
- Server overload.

**Handling:**
- Exponential backoff retry system
- Max retry limits

---

## 6.2 Conflicting reconciliation after reconnect

**Scenario:**
- Multiple devices sync large backlog at once.

**Impact:**
- Race conditions on server.

**Handling:**
- Server processes queue sequentially per device or transaction locking

---

# ⚠️ 7. Time & Ordering Edge Cases

## 7.1 Device time mismatch

**Scenario:**
- Phone clock is incorrect.

**Impact:**
- Wrong transaction ordering.

**Handling:**
- Always trust server timestamp, never device time

---

# 🧠 Final System Rule

All edge cases resolve to one principle:

> The server must validate, correct, or reject all client-provided data.

Clients are not trusted sources of truth.

---

# 🚀 Summary

This system is resilient only if:

- Every transaction is uniquely identified
- Server is authoritative
- Offline data is treated as temporary
- Sync is always validated and reversible

Without these rules, offline-first systems silently corrupt data over time.