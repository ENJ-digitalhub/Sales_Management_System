# 📡 API Specification

## Sales Management System

---

## 🔐 1. AUTHENTICATION

### POST /auth/login

Authenticate user with username, password, and device metadata.

**Request**

```json
{
  "username": "string",
  "password": "string",
  "device_name": "string"
}
```

**Response**

```json
{
  "success": true,
  "token": "jwt_token",
  "user": {
    "id": "uuid",
    "name": "string",
    "role": "admin | manager | employee"
  }
}
```

---

### POST /auth/pin-login

Fast re-authentication using PIN.

```json
{
  "user_id": "uuid",
  "pin": "string"
}
```

---

### POST /auth/logout

Logs out user and invalidates session.

---

## 🔒 SESSION RULES

* Only **one active session per user**
* New login **invalidates previous session**
* Session ends when:

  * user logs out
  * token expires due to inactivity

---

## 👥 2. USER MANAGEMENT

### Roles

* Admin
* Manager
* Employee

---

### POST /users

Create user (Admin only)

---

### PATCH /users/{id}

Edit user (Admin only)

---

### PATCH /users/{id}/deactivate

Deactivate user account (Admin only)

* Sets `is_active = false`
* User cannot log in while deactivated
* User record and history are preserved

---

### PATCH /users/{id}/role

Assign role (Admin only)

---

## 📦 3. PRODUCTS

### POST /products

Create product

```json
{
  "name": "string",
  "selling_price": "number",
  "cost_price": "number",
  "stock_quantity": "number",
  "category": "string (optional)"
}
```

---

### GET /products

List all active products (is_active = true)

---

### PATCH /products/{id}

Edit product

* Price and details editable anytime by admin
* All changes logged in audit_logs
* Version field incremented on every update

---

### DELETE /products/{id}

**Soft delete only.**

* Sets `is_active = false`
* Product is hidden from active product list
* Product record is preserved in the database
* All historical sale_items referencing this product remain intact

---

## 🧾 4. SALES

### POST /sales

Create sale (multi-item)

```json
{
  "items": [
    {
      "product_id": "uuid",
      "quantity": 2
    }
  ],
  "payment_method": "cash | transfer | pos"
}
```

---

### RULES

* Stock is reduced automatically on successful sale
* If ANY item has insufficient stock → **reject the entire sale** (all-or-nothing)
* No partial sale commits allowed
* Backend recalculates totals regardless of any frontend input

---

### PATCH /sales/{id}

Edit sale

**Allowed within 20 minutes (employee or above):**

* items
* quantity
* payment method

**After 20 minutes:**

* Requires manager authorization via `POST /sales/{id}/request-edit`

**On any edit:**

* Stock delta is recalculated correctly
* Edit is logged in audit_logs
* Admin is notified

---

### DELETE /sales/{id}

* Admin only
* Logged in audit_logs

---

### POST /sales/{id}/cancel

* Manager or Admin
* Restores stock for all sale items
* Logged in audit_logs

---

### POST /sales/{id}/request-edit

Request manager approval for a late edit (after 20-minute window).

```json
{
  "reason": "string",
  "proposed_changes": {}
}
```

---

## 📊 5. REPORTS

### GET /reports/daily

### GET /reports/monthly

### GET /reports/yearly

### GET /reports/employee-performance

---

### RULES

* Accessible by Admin and Manager only
* Reports reflect only synced, committed data
* Unsynced offline transactions are excluded until sync completes
* Reports are downloadable

---

## 🛒 6. PURCHASES (RESTOCKING)

### POST /purchases

Create a purchase entry (any role)

```json
{
  "items": [
    {
      "product_id": "uuid",
      "quantity": 10,
      "cost_price": 500
    }
  ],
  "notes": "string (optional)"
}
```

* Creates purchase with status = `pending`
* Does NOT affect inventory until approved

---

### GET /purchases/{id}

View purchase details

---

### GET /purchases/history

List all purchases with status

---

### PATCH /purchases/{id}/approve

Approve a purchase (Admin only)

* Sets status = `approved`
* Updates stock for all items in the purchase
* Logs inventory change in inventory_logs
* Logs action in audit_logs

---

### PATCH /purchases/{id}/reject

Reject a purchase (Admin only)

* Sets status = `rejected`
* No stock change occurs

---

## 🔁 7. OFFLINE SYNC

### POST /sync

Bulk sync endpoint

```json
{
  "device_id": "string",
  "transactions": []
}
```

---

### BEHAVIOR

Server will:

* Validate JWT and device whitelist
* Check idempotency via transaction_id (ignore duplicates)
* Accept valid records and commit to database
* Reject invalid records (insufficient stock, deleted products, etc.)
* Return per-item result

---

### RESPONSE

```json
{
  "results": [
    {
      "id": "local_transaction_id",
      "status": "success | failed | conflict"
    }
  ]
}
```

---

### RULES

* Auto-sync triggers on reconnect
* Retry up to 5 times with exponential backoff
* Conflicts are flagged for manager review — never auto-resolved
* Reports exclude unsynced data

---

## 📡 8. DEVICE MANAGEMENT

* `device_id` generated on first app install
* Used for sync tracking and session control
* Admin manages whitelisted devices

---

## 🔐 9. SECURITY

* JWT authentication required for all endpoints
* Server validates ALL data — client is never trusted
* Device whitelist enforced — unknown devices rejected at connection

---

## 🧾 10. AUDIT LOGGING

System automatically logs:

* Sales creation, edits, cancellations
* Product create, update, soft-delete
* User create, role change, deactivation
* Purchase creation, approval, rejection
* Conflict events and sync failures

---

## ⚙️ 11. SYSTEM RULES

* No partial sales allowed — all-or-nothing
* Products are soft-deleted, never hard-deleted
* All invalid operations are rejected with clear error response
* Duplicate transactions detected via transaction_id and silently ignored

---

## 📡 12. REAL-TIME (WEBSOCKET)

* Live stock updates after sales and purchase approvals
* Live sales notifications for dashboard
* Sync completion and conflict alerts

---

## 🧠 13. CORE DESIGN PRINCIPLES

* Offline-first system
* LAN-based communication (same WiFi)
* Mobile-first UI
* Strict reporting accuracy
* Server is the only source of truth

---

## 🚨 ADMIN PRIVILEGES

* Approve and reject purchases
* Soft-delete products
* Deactivate users
* Override transactions
* View full audit logs

---

## 🔐 MANAGER PRIVILEGES

* Authorize late sale edits
* Cancel sales
* Review and resolve conflicts

---

## 👷 EMPLOYEE PRIVILEGES

* Create sales
* Edit own sales within 20-minute window
* Create purchase entries (pending approval)