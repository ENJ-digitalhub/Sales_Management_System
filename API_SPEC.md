# 📡 API Specification

## Sales Management System

---

## 🔐 1. AUTHENTICATION

### POST /auth/login

Authenticate user with username and password.

**Request**

```json
{
  "username": "string",
  "password": "string"
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

  * browser is closed
  * user logs out

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

### DELETE /users/{id}

Remove user (Admin only)

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

List all active products

---

### PATCH /products/{id}

Edit product

* Price editable anytime
* All changes logged

---

### DELETE /products/{id}

* Soft delete
* Product hidden from system
* Still exists in historical sales

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

* Stock is reduced automatically
* If stock is insufficient → **reject entire sale**

---

### PATCH /sales/{id}

Edit sale

**Allowed within 20 minutes:**

* items
* quantity
* payment method

After 20 minutes:

* Requires **manager authorization**

---

### DELETE /sales/{id}

* Admin only

---

### POST /sales/{id}/cancel

* Manager or Admin
* Restores stock

---

## 📊 5. REPORTS

### GET /reports/daily

### GET /reports/monthly

### GET /reports/yearly

### GET /reports/employee-performance

---

### RULES

* Accessible by:

  * Admin
  * Manager
* Reports are:

  * Strict
  * Downloadable

---

## 🔁 6. OFFLINE SYNC

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

* Accept valid records
* Reject invalid ones
* Return per-item status

---

### RESPONSE

```json
{
  "results": [
    {
      "id": "local_id",
      "status": "success | failed | conflict"
    }
  ]
}
```

---

### RULES

* Auto-sync on reconnect
* Retry up to 5 times
* Conflicts → flagged for review

---

## 📡 7. DEVICE MANAGEMENT

* device_id generated on frontend
* Used for sync tracking

---

## 🔐 8. SECURITY

* JWT authentication
* Server validates ALL data
* Client is NEVER trusted

---

## 🧾 9. AUDIT LOGGING

System logs:

* Sales creation
* Sales edits
* Product actions
* User actions
* Conflict events

---

## ⚙️ 10. SYSTEM RULES

* No partial sales allowed
* All invalid operations rejected
* Duplicate transactions detected via transaction_id

---

## 📡 11. REAL-TIME (FUTURE)

* Live stock updates
* Live sales notifications

---

## 🧠 12. CORE DESIGN PRINCIPLES

* Offline-first system
* LAN-based communication (same WiFi)
* Mobile-first UI
* Strict reporting accuracy
* Flexible correction flow via Manager

---

## 🚨 ADMIN PRIVILEGES

* Delete store
* Remove users
* Override transactions
* View full audit logs

---

## 🔐 MANAGER PRIVILEGES

* Approve late edits
* Cancel sales
* Review conflicts

---

## 👷 EMPLOYEE PRIVILEGES

* Create sales
* Limited editing (within 20 mins)

---

## 🧩 SYSTEM GOAL

To replace manual bookkeeping with a reliable, auditable, and offline-capable sales and inventory system for small retail stores.

---
