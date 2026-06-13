# TEST_PLAN.md

## 1. Overview

This document defines the test strategy for validating the POS system covering sales, inventory, offline sync, authentication, and conflict resolution.

---

## 2. Test Scope

### Included

* Sales processing (online + offline)
* Inventory consistency
* Sync engine reliability
* Authentication & session control
* Conflict resolution
* Audit logging
* Purchase approval flow

### Excluded

* UI/UX validation
* Performance benchmarking (handled separately)

---

## 3. Sales Tests

### 3.1 Sale Creation

* Verify sale supports multiple items
* Verify same product cannot appear twice (quantity aggregation enforced)
* Validate all-or-nothing behavior:

  * If ANY item has insufficient stock, the **entire sale is rejected**
  * No partial commits allowed
  * Rejected items and reason are clearly reported in the response
* Backend must recalculate totals regardless of frontend input

### 3.2 Pricing

* Verify price can be edited during sale
* Backend must recalculate totals regardless of frontend input

### 3.3 Stock Validation

* Validate stock check occurs before sale commit
* If any item stock = 0 or insufficient:

  * **Reject entire sale in online mode**
  * Allow sale in offline mode (validation deferred to sync)
  * On sync: server rejects conflicting items and flags for manager review

---

## 4. Edit Window Tests

* Verify employee edits are allowed within 20 minutes
* After 20 minutes:

  * Requires manager authorization
  * `POST /sales/{id}/request-edit` must be submitted
* On edit (any role):

  * Stock delta is recalculated correctly (not a full recount — delta only)
  * Edit is logged in audit_logs
  * Admin is notified

---

## 5. Inventory Tests

* Ensure stock never goes negative in the database
* Product deletion:

  * Must be **soft delete** (is_active = false)
  * Product must NOT appear in active product list after soft delete
  * Product record must still exist in database
* Historical sales:

  * Must retain references to soft-deleted products
  * sale_items must remain fully intact after product is soft-deleted

---

## 6. Authentication & Session Tests

* Only one active session per user allowed
* New login invalidates previous session immediately
* Token expiry:

  * Triggered on inactivity or explicit logout
  * Forces re-authentication

---

## 7. Offline & Sync Engine Tests

### 7.1 Offline Behavior

* Sales can be created fully offline
* Offline sales reduce local stock immediately (optimistic update)

### 7.2 Sync Execution

* Batch size: 10–20 transactions per request
* Max retries: 5 with exponential backoff
* After 5 failures:

  * Mark transaction as FAILED
  * Notify user and manager
  * Do not retry automatically — require manual retry

### 7.3 Conflict Handling

#### Stock Conflict

* Offline sale exceeds actual server stock
* Behavior: reject affected sale, flag for manager decision

#### Duplicate Transactions

* Detected by matching `transaction_id` (UUID v4)
* Behavior: silently ignore duplicate — do not process twice

#### Deleted Product Conflict

* Product was soft-deleted on server while device was offline
* Behavior: reject transaction, escalate to manager resolution

#### Out-of-Order Events

* Reject out-of-order transactions based on server timestamp

---

## 8. Device & Storage Tests

* Offline queue stored in SQLite on device
* Queue persists across app restarts (not memory-only)
* Queue does NOT persist after app reinstall
* No enforced queue size limit (monitor for overflow in future)

---

## 9. Network Failure Tests

* If network drops mid-sale:

  * Save transaction locally with status = PENDING_SYNC
* If server unavailable:

  * Allow all offline operations
  * Display persistent "Offline Mode" banner to user

---

## 10. Reporting Tests

* Reports are real-time computed from committed database state
* Reports must NOT include unsynced or pending transactions
* Reports accessible by Admin and Manager only

---

## 11. Purchase Tests

* Any role can create a purchase entry (status = pending)
* Purchase does NOT affect inventory when created
* Only admin can approve a purchase
* On approval: inventory is updated and logged in inventory_logs
* On rejection: no stock change occurs
* Approval and rejection are both logged in audit_logs

---

## 12. Security Tests

* Device whitelist enforced
* Unknown device:

  * Blocked immediately at connection
* PIN login:

  * Optional (user-enabled fast login after first full login)

---

## 13. Audit & Logging

* Audit logs are immutable — cannot be edited or deleted
* All failed sync attempts must be logged
* All sale edits must be logged with editor identity

---

## 14. Conflict Strategy

* Unresolvable conflicts:

  * System continues operating normally
  * Conflict flagged for manager review in manager dashboard
  * Manager makes final decision — system applies it

---

## 15. Retry Policy

* Automatic retries limited to sync failures only
* No retry for:

  * Logical conflicts (stock mismatch, deleted products)
  * Authorization failures

---

## 16. Critical Edge Cases

* Offline sale exceeds real stock → conflict on sync → manager review
* Multiple devices selling same stock offline → first valid sync wins, rest conflict
* Product soft-deleted while offline sales reference it → manager resolution
* Duplicate submissions due to retry storms → idempotency via transaction_id
* Session invalidated during active sync → sync fails, user re-authenticates and retries
* All-or-nothing sale: one item out of stock → entire sale rejected, no partial commit

---

## 17. Exit Criteria

System is considered stable when:

* No data corruption occurs under offline/online transitions
* All conflicts are either auto-resolved (duplicates) or escalated correctly (stock/delete conflicts)
* No negative stock observed in database
* Sync engine reaches deterministic final state
* Product soft-delete preserves all historical sale references
* Purchase approval correctly gates all stock updates

---

## 18. Future Considerations

* Define hard limits for offline queue size
* Introduce conflict preview UI before sync commit
* Improve duplicate detection beyond transaction_id (add hash of payload as secondary check)
* Load testing for simultaneous multi-device sync scenarios