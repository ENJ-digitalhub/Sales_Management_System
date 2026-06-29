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
- is_active (boolean)
- created_at
```

### Notes:

* Only one “true admin” exists via environment config
* PIN is optional (set after first login)
* No sensitive banking credentials stored

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
- is_active (boolean)
- created_at
- updated_at
```

### Rules:

* Stock can NEVER go below zero
* Deleted products are permanently removed
* Historical sales remain unaffected

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

* Editable only within 20 minutes
* After that → locked permanently

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

* Each sale contains multiple items
* Cost price is snapshotted to preserve profit history

---

# 📊 5. INVENTORY_LOGS TABLE

```
inventory_logs
- id (PK)
- product_id (FK → products.id)
- change_type (sale | restock | adjustment)
- quantity_change
- reference_id (sale_id or purchase_id)
- created_at
```

### Purpose:

* Track every stock movement
* Enables audit + debugging

---

# 🧾 6. AUDIT_LOGS TABLE

```
audit_logs
- id (PK)
- user_id (FK → users.id)
- action_type
- entity_type (sale | product | user )
- entity_id
- metadata (JSON)
- created_at
```

### Rules:

* Immutable (cannot be deleted)
* Logs ALL actions

---

# 🔁 7. SYNC_QUEUE TABLE (CRITICAL)

```
sync_queue
- id (PK)
- device_id
- entity_type
- operation (CREATE | UPDATE | DELETE)
- payload (JSON)
- status (pending | synced | failed | conflict)
- retry_count
- last_attempt_at
- created_at
```

### Behavior:

* Stores offline actions
* Retries up to 5 times
* Uses idempotency keys to prevent duplicates

---

# 📱 8. DEVICES TABLE

```
devices
- id (PK)
- user_id (FK → users.id)
- device_name
- is_active
- last_seen_at
```

### Rules:

* One active session per user
* New login invalidates previous device

---

# ⚙️ SYSTEM GUARANTEES

* No negative stock allowed
* Server validates all incoming data
* Duplicate transactions prevented via unique IDs
* Offline data must pass validation before commit
* All actions are logged

---

# 🚀 FUTURE EXTENSION READY

Prepared for:

* Multi-store architecture
* Cloud sync
* Distributed systems

Without breaking current schema