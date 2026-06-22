# 🗄️ DATABASE SCHEMA — Sales Management System (Offline-First)

## 🧠 Design Principles

* Server is the only source of truth
* All transactions are immutable after allowed edit window
* Auditability over convenience
* Offline data is temporary until synced

---

# 👥 1. USERS TABLE

```
users
- id (PK)
- name
- username (UNIQUE)
- password_hash
- role (admin | manager | employee)
- phone_or_email
- account_name (nullable)
- bank_name (nullable)
- account_number (nullable)
- pin_hash (nullable)
- is_active (boolean, default true)
- created_at
```

### Notes:

* Only one "true admin" exists via environment config
* PIN is optional (set after first login)
* No sensitive banking credentials stored
* Users are deactivated, never deleted

---

# 📦 2. PRODUCTS TABLE

```
products
- id (PK)
- name
- category (nullable)
- selling_price
- cost_price
- stock_quantity
- version (integer, default 1)        ← incremented on every update for conflict resolution
- is_active (boolean, default true)   ← soft delete: false = hidden, not removed
- created_at
- updated_at
```

### Rules:

* Stock can NEVER go below zero
* Products are SOFT DELETED (is_active = false), never permanently removed
* Historical sales retain full references to soft-deleted products
* Version field enables conflict detection when admin edits product while devices are offline

---

# 🧾 3. SALES TABLE

```
sales
- id (PK)
- receipt_number (UNIQUE)
- user_id (FK → users.id)
- total_amount
- profit_at_sale
- payment_method (cash | transfer | pos)
- status (completed | edited | cancelled)
- created_at
- editable_until (timestamp)
```

### Rules:

* Editable only within 20 minutes by the creating employee
* After 20 minutes → requires manager authorization
* Cancellation restores stock and is logged in audit_logs
* All edits are logged regardless of who makes them

---

# 🧾 4. SALE_ITEMS TABLE

```
sale_items
- id (PK)
- sale_id (FK → sales.id)
- product_id (FK → products.id)
- quantity
- unit_price
- cost_price_at_sale
- total_price
```

### Notes:

* Each sale contains one or more items
* Cost price is snapshotted at time of sale to preserve profit history
* References product even if product is later soft-deleted

---

# 📊 5. INVENTORY_LOGS TABLE

```
inventory_logs
- id (PK)
- product_id (FK → products.id)
- change_type (sale | restock | adjustment | cancellation)
- quantity_change
- reference_id (sale_id or purchase_id)
- created_at
```

### Purpose:

* Track every stock movement
* Enables full audit and debugging of stock history

---

# 🧾 6. AUDIT_LOGS TABLE

```
audit_logs
- id (PK)
- user_id (FK → users.id)
- action_type
- entity_type (sale | product | user | purchase | system)
- entity_id
- metadata (JSON)
- created_at
```

### Rules:

* Immutable — cannot be edited or deleted by anyone
* Logs ALL critical actions: sales, edits, cancellations, product changes, user changes, purchase approvals

---

# 🛒 7. PURCHASES TABLE

```
purchases
- id (PK)
- created_by (FK → users.id)
- approved_by (FK → users.id, nullable)
- status (pending | approved | rejected)
- total_cost
- notes (nullable)
- created_at
- approved_at (nullable)
```

### Rules:

* Any role can create a purchase entry
* Only admin can approve a purchase
* Stock is only updated AFTER approval
* Rejected purchases do not affect inventory

---

# 🛒 8. PURCHASE_ITEMS TABLE

```
purchase_items
- id (PK)
- purchase_id (FK → purchases.id)
- product_id (FK → products.id)
- quantity
- cost_price
- total_cost
```

### Notes:

* Each purchase contains one or more items
* Cost price recorded at time of purchase entry

---

# 🔁 9. SYNC_QUEUE TABLE (CRITICAL)

```
sync_queue
- id (PK)
- device_id (FK → devices.id)
- transaction_id (FK → transactions.id, UNIQUE)             ← idempotency key, UUID v4 generated on client
- entity_type (sales | product | user)
- operation (create | update | delete)
- payload (JSON)
- status (pending | synced | failed | conflict)
- retry_count (default 0)
- last_attempt_at (nullable)
- created_at
```

### Behavior:

* Stored in SQLite on the client device
* Retries up to 5 times with exponential backoff
* Uses transaction_id to prevent duplicate processing
* Conflicts are isolated and escalated to manager — never auto-overwritten

---

# 📱 10. DEVICES TABLE

```
devices
- id (PK)
- user_id (FK → users.id)
- device_name
- is_active (boolean)
- last_seen_at
```

### Rules:

* One active session per user at any time
* New login invalidates previous device session immediately

---

# ⚙️ SYSTEM GUARANTEES

* No negative stock allowed — enforced at DB and service layer
* Server validates all incoming data — client data is never trusted
* Duplicate transactions prevented via unique transaction_id (idempotency)
* Offline data must pass full validation before commit
* All actions are logged in audit_logs
* Products are soft-deleted — historical integrity is preserved

---

# 🚀 FUTURE EXTENSION READY

Prepared for:

* Multi-store architecture
* Cloud sync
* Distributed systems
* Supplier management (purchase module expansion)

Without breaking current schema