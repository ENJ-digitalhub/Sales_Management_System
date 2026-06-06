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

### Excluded

* UI/UX validation
* Performance benchmarking (handled separately)

---

## 3. Sales Tests

### 3.1 Sale Creation

* Verify sale supports multiple items
* Verify same product cannot appear twice (quantity aggregation enforced)
* Validate partial success behavior:

  * If one item fails (e.g. insufficient stock), other items still process
  * Failed items are clearly reported

### 3.2 Pricing

* Verify price can be edited during sale
* Backend must recalculate totals regardless of frontend input

### 3.3 Stock Validation

* Validate stock check occurs:

  * Before sale
  * After sale commit
* If stock = 0:

  * Allow sale in offline mode
  * Reject in online mode if enforced

---

## 4. Edit Window Tests

* Verify edits allowed within 20 minutes
* After 20 minutes:

  * Requires manager approval
* On edit:

  * Stock must be recalculated correctly (delta adjustment)

---

## 5. Inventory Tests

* Ensure stock never goes negative in DB
* Product deletion:

  * Must be soft delete
* Historical sales:

  * Must retain references to deleted products

---

## 6. Authentication & Session Tests

* Only one active session per user allowed
* New login invalidates previous session immediately
* Token expiry:

  * Triggered on inactivity or app exit
  * Forces logout

---

## 7. Offline & Sync Engine Tests

### 7.1 Offline Behavior

* Sales can be created fully offline
* Offline sales reduce local stock immediately

### 7.2 Sync Execution

* Batch size: 10–20 transactions
* Max retries: 5
* After 5 failures:

  * Mark transaction as FAILED
  * Do not retry automatically

### 7.3 Conflict Handling

#### Stock Conflict

* Requires manager decision

#### Duplicate Transactions

* Defined as identical timestamp
* Behavior:

  * Log घटना
  * Ignore duplicate

#### Deleted Product Conflict

* Escalate to manager resolution

#### Out-of-Order Events

* Reject out-of-order transactions

---

## 8. Device & Storage Tests

* Offline queue stored in SQLite
* Queue does NOT persist after reinstall
* No enforced queue size limit

---

## 9. Network Failure Tests

* If network drops mid-sale:

  * Save locally
* If server unavailable:

  * Allow operations
  * Notify user

---

## 10. Reporting Tests

* Reports are real-time computed
* Reports must NOT include unsynced data

---

## 11. Security Tests

* Device whitelist enforced
* Unknown device:

  * Block immediately
* PIN login:

  * Optional (user-enabled fast login)

---

## 12. Audit & Logging

* Audit logs:

  * Editable only by admin
* All failed sync attempts must be logged

---

## 13. Conflict Strategy

* Unresolvable conflicts:

  * System continues operating
  * Flag for manager review

---

## 14. Retry Policy

* Automatic retries limited to sync failures only
* No retry for:

  * Logical conflicts (stock mismatch, deleted products)
  * Authorization failures

---

## 15. Critical Edge Cases

* Offline sale exceeds real stock → conflict on sync
* Multiple devices selling same stock offline
* Product deleted while offline sales exist
* Duplicate submissions due to retry storms
* Session invalidation during sync
* Partial sale success integrity

---

## 16. Exit Criteria

System is considered stable when:

* No data corruption occurs under offline/online transitions
* All conflicts are either auto-resolved or escalated correctly
* No negative stock observed
* Sync engine reaches deterministic final state

---

## 17. Future Considerations

* Define hard limits for offline queue
* Introduce conflict preview before sync
* Add idempotency keys beyond timestamp
* Improve duplicate detection robustness

---