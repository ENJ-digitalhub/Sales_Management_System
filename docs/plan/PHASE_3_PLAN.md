<<<<<<< HEAD
🚀 Phase 3 — Sales Processing + Transaction Integrity Week

Sales Management System (Offline-First POS)

Stack confirmed: Flask (latest, app factory pattern) · Raw SQLAlchemy 2.0 (no Flask-SQLAlchemy extension) · SQLite · Vanilla JS frontend · JWT

Team:

Person| Owns
Obinna| "frontend/", sales UI, cart flow, receipt rendering
Covenant| "backend/routes/", "controllers/", "services/", transaction logic, permissions
ENJ| "backend/models/", "database/", "cli/cli.py", transaction persistence

---

🎯 Phase 3 Goal (one sentence)

By end of week: users can create real sales, inventory updates correctly, transactions remain consistent, and duplicate sales are prevented.

⚠️ Critical dependency

Covenant cannot finish sales logic until ENJ ships "Sale" and "SaleItem" models. Obinna cannot finish checkout until Covenant stabilizes the sales payload and response contract.

Agree on sale payload shape before coding.

---

👤 ENJ — Database + Transaction Foundation

Execution Checklist

- [ ] "backend/models/sale.py"
- [ ] "backend/models/sale_item.py"
- [ ] "backend/models/inventory_log.py"

Fields:

Sale:

- "id"
- "transaction_id"
- "user_id"
- "subtotal"
- "discount"
- "tax"
- "total"
- "status"
- "created_at"

SaleItem:

- "id"
- "sale_id"
- "product_id"
- "quantity"
- "unit_price"
- "subtotal"

InventoryLog:

- "id"

- "product_id"

- "change"

- "reason"

- "created_at"

- [ ] Update "database/schema.sql"

- [ ] Update CLI:
  
  - seed sales data
  - reset support

Socratic Task Spec

Objective: Create transaction entities that support complete sales while preserving inventory consistency.

Constraints:

- No inventory updates inside models
- Foreign keys enforced
- Transaction IDs unique

Required Documentation:

- SQLAlchemy relationships
- SQLAlchemy transaction handling

Expected Output:

python cli/cli.py setup
python cli/cli.py seed

creates products + users + sales tables successfully.

Guiding questions for ENJ (don't answer yet — sit with these):

1. If inventory changes later, should historical sales change too?
2. Which values should be snapshots versus live references?

---

👤 Covenant — Backend API + Sales Business Logic

Execution Checklist

- [ ] "backend/routes/sales.py"
- [ ] "backend/controllers/sales_controller.py"
- [ ] "backend/services/sales_service.py"
- [ ] "backend/services/inventory_service.py"
- [ ] "backend/utils/transactions.py"

Implement:

- [ ] "POST /sales"
- [ ] "GET /sales"
- [ ] "GET /sales/{id}"
- [ ] "POST /sales/{id}/cancel"

Business Rules:

- [ ] Validate stock before sale
- [ ] Deduct inventory
- [ ] Calculate totals
- [ ] Apply discount
- [ ] Generate transaction ID
- [ ] Prevent duplicate submissions
- [ ] Transaction rollback
- [ ] Audit inventory changes

Validation split:

Controller →

- payload shape
- request validation

Service →

- stock rules
- transaction logic
- inventory updates

Socratic Task Spec

Objective: Build a safe sales engine where every sale either completes fully or fails fully.

Constraints:

- No SQL in routes
- Controllers never update DB
- Inventory updates occur inside services only
- Sales and inventory commit together

Required Documentation:

- SQLAlchemy transaction scope
- Flask request lifecycle
- Idempotency fundamentals

Expected Output:

Submitting:

POST /sales

creates:

- sale
- sale items
- inventory updates

or creates nothing if validation fails.

Guiding questions for Covenant (don't answer yet — sit with these):

1. If stock deduction succeeds but sale creation fails, what should the customer see?
2. Should duplicate requests create duplicate sales?

---

👤 Obinna — Frontend + Checkout Experience

Execution Checklist

- [ ] "frontend/pages/sales.html"
- [ ] "frontend/components/cart.js"
- [ ] "frontend/services/sales.js"

Build:

- [ ] Product selection
- [ ] Cart state
- [ ] Quantity controls
- [ ] Total calculation
- [ ] Checkout confirmation
- [ ] Receipt page
- [ ] Error states
- [ ] Empty cart state

UI Flow:

Products
→ Add to Cart
→ Review
→ Checkout
→ Receipt

Socratic Task Spec

Objective: Build the full sales experience using real API responses.

Constraints:

- Vanilla JS only
- No local sales persistence yet
- UI totals are display only — backend is source of truth

Required Documentation:

- Fetch API
- Browser state management basics

Expected Output:

User can:

- add products
- checkout
- view receipt

with real backend data.

Guiding questions for Obinna (don't answer yet — sit with these):

1. If frontend total differs from backend total, which wins?
2. Should the cart survive page refresh?

---

✅ Definition of Done — Phase 3 (whole team)

A Phase 3 feature is only done if:

- [ ] Sales can be created
- [ ] Inventory decreases correctly
- [ ] Duplicate requests do not duplicate sales
- [ ] Failed sales rollback cleanly
- [ ] Receipt displays real data
- [ ] Layer chain remains:
  route → controller → service → model

Out of scope this week (do not touch):
offline sync, queue retries, reports, analytics

---

🗓️ Suggested Day-by-Day

Day| ENJ| Covenant| Obinna
1| Sale model| Sales blueprint| Sales page
2| Sale items| Transaction service| Cart
3| Inventory logs| Stock validation| Checkout
4| Schema updates| Rollback handling| Receipt
5| Buffer| Duplicate prevention| Polish

---

🚨 Non-negotiable team rules (carried over)

1. Inventory never updates outside services.
2. Duplicate submissions must not create duplicate sales.
3. Transactions commit together or fail together.
4. No sync implementation this week — scope creep kills Phase 3.
=======
# 🚀 Phase 3 — Sales Creation
## Sales Management System (Offline-First POS)

**Stack:** Flask · Raw SQLAlchemy 2.0 · SQLite · Vanilla JS

**Team:**
| Person | Owns |
|---|---|
| **Goodness** | `frontend/` — sales UI, cart, payment method, offline queue wiring |
| **Covenant** | `backend/routes/`, `controllers/`, `services/`, `utils/` — sales endpoints, business logic |
| **ENJ** | `backend/models/` — Sale, SaleItem, InventoryLog, AuditLog models, `database/schema.sql`, `cli/cli.py` |

---

## 🎯 Phase 3 Goal (one sentence)

By end of phase: a logged-in employee can add items to a cart, complete a sale, and have it recorded against their account — with stock deducted, an audit log entry created, and the sale locked after 20 minutes.

### ⚠️ Critical dependencies
- Covenant's sales routes are blocked on ENJ's `Sale`, `SaleItem`, `InventoryLog`, and `AuditLog` models — **ENJ ships all four models by Day 2**
- Goodness's cart UI is blocked on Covenant's `POST /sales` endpoint — **Covenant ships it by Day 3**
- All field names and response contracts are locked below — agree before coding

---

## 🔒 Locked Contracts (agree before coding)

### POST /sales — Request
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

### POST /sales — Response (success)
```json
{
  "success": true,
  "sale": {
    "id": "uuid",
    "receipt_number": "string",
    "total_amount": "number",
    "profit_at_sale": "number",
    "payment_method": "string",
    "status": "completed",
    "created_at": "timestamp",
    "editable_until": "timestamp",
    "items": [
      {
        "product_id": "uuid",
        "quantity": 2,
        "unit_price": "number",
        "total_price": "number"
      }
    ]
  }
}
```

### POST /sales — Response (failure — insufficient stock)
```json
{
  "success": false,
  "message": "Insufficient stock for product: {name}",
  "product_id": "uuid"
}
```

### PATCH /sales/{id} — Request
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

### PATCH /sales/{id} — Response (outside edit window)
```json
{
  "success": false,
  "message": "Edit window has closed. Manager approval required.",
  "requires_approval": true
}
```

### GET /sales/{id} — Response
```json
{
  "success": true,
  "sale": {
    "id": "uuid",
    "receipt_number": "string",
    "user_id": "uuid",
    "total_amount": "number",
    "profit_at_sale": "number",
    "payment_method": "string",
    "status": "completed | edited | cancelled",
    "created_at": "timestamp",
    "editable_until": "timestamp",
    "items": []
  }
}
```

---

## 📋 Business Rules (non-negotiable)

- Stock is checked **before** the sale is committed — if any item has insufficient stock, the **entire sale is rejected** (no partial sales)
- Stock is deducted **only after** the full sale is validated and committed
- `editable_until` = `created_at + 20 minutes` — calculated server-side, never client-side
- Employees can edit within 20 minutes — after that the endpoint returns `requires_approval: true`
- Managers can edit any sale without time restriction — all edits are logged
- Every sale edit triggers an `AuditLog` entry
- `profit_at_sale` = sum of `(selling_price - cost_price) * quantity` per item — snapshotted at sale time, never recalculated later
- `cost_price_at_sale` per `SaleItem` is snapshotted from the product at the time of sale
- `receipt_number` is unique and generated server-side
- Same product cannot appear twice in one sale — quantities must be aggregated before submission

---

## 👤 ENJ — Models + Schema + CLI

### Execution Checklist
- [ ] `backend/models/models.py`: add `Sale` model — fields: `id, receipt_number, user_id, total_amount, profit_at_sale, payment_method, status, created_at, editable_until`
- [ ] `backend/models/models.py`: add `SaleItem` model — fields: `id, sale_id, product_id, quantity, unit_price, cost_price_at_sale, total_price`
- [ ] `backend/models/models.py`: add `InventoryLog` model — fields: `id, product_id, change_type, quantity_change, reference_id, created_at`
- [ ] `backend/models/models.py`: add `AuditLog` model — fields: `id, user_id, action_type, entity_type, entity_id, metadata, created_at`
- [ ] `database/schema.sql`: add all four tables matching ORM models
- [ ] `cli/cli.py`: extend `seed` to insert 3–5 demo sales with items against seeded products and users
- [ ] `cli/cli.py`: extend `reset` to clear all four new tables safely and in correct FK order

### Socratic Task Spec
**Objective:** Define all four models using SQLAlchemy 2.0 declarative syntax, with correct foreign keys, relationships, and field types — paying special attention to money fields and snapshot fields.

**Constraints:**
- `Mapped` / `mapped_column` only
- `Numeric(10, 2)` for all money fields — `total_amount`, `profit_at_sale`, `unit_price`, `cost_price_at_sale`, `total_price`
- `AuditLog` has no `updated_at` — it is immutable by design
- `metadata` field in `AuditLog` uses `JSON` type
- `reset` must drop/clear tables in FK-safe order — children before parents
- `editable_until` is a `DateTime` field — calculated in the service layer, not the model

**Required Documentation:**
- SQLAlchemy 2.0 — Column types (Numeric, JSON, DateTime)
- SQLAlchemy 2.0 — Relationships and foreign keys

**Expected Output:** All four tables exist after `setup`. `seed` inserts demo sales with items and logs visible in the DB. `reset` clears everything cleanly without FK errors.

**Guiding questions for ENJ:**
1. `SaleItem` holds `cost_price_at_sale` — this is a snapshot of the product's cost price at the moment of sale. Why is this stored separately instead of just reading from the `Product` table, and what would break if you didn't snapshot it?
2. `AuditLog` is immutable — what does that mean at the database level, and how would you enforce it in SQLAlchemy if someone tried to update a log entry?

---

## 👤 Covenant — Sales Endpoints + Business Logic

### Execution Checklist
- [ ] `backend/routes/sales.py`: add routes — `POST /sales`, `GET /sales/{id}`, `PATCH /sales/{id}`, `POST /sales/{id}/cancel`
- [ ] `backend/controllers/sales_controller.py`: handle request/response shape for all four routes
- [ ] `backend/services/sales_service.py`: implement:
  - `create_sale(user_id, items, payment_method, session)` — full validation + commit
  - `get_sale(sale_id, session)` — fetch with items
  - `edit_sale(sale_id, user_id, role, items, payment_method, session)` — edit window check + role check
  - `cancel_sale(sale_id, user_id, role, session)` — manager/admin only, restores stock
- [ ] `backend/utils/validators.py`: validate sale payload — items not empty, payment method is valid enum, quantities are positive integers, no duplicate product IDs
- [ ] All routes protected with `@require_auth` from Phase 2
- [ ] `POST /sales/{id}/cancel` protected with `@require_role('manager', 'admin')`
- [ ] Stock check happens inside a DB transaction — no partial commits
- [ ] `AuditLog` entry created on every sale creation, edit, and cancellation

### Socratic Task Spec
**Objective:** Build the full sales flow — creation validates stock, deducts it atomically, snapshots prices, and locks the sale after 20 minutes. Edits check the window and role before allowing changes.

**Constraints:**
- Services accept session as a parameter — never open their own session
- Stock check and deduction happen in the same transaction — if deduction fails, the whole sale rolls back
- `editable_until` calculated as `datetime.utcnow() + timedelta(minutes=20)` — server-side only
- Edit endpoint checks `datetime.utcnow() < sale.editable_until` before allowing employee edits
- Managers bypass the edit window but their edits are still logged
- `profit_at_sale` calculated in the service layer before commit

**Required Documentation:**
- SQLAlchemy 2.0 — transactions and rollback
- Python `datetime` and `timedelta`
- Flask `g` object — accessing current user in service calls

**Expected Output:** `POST /sales` with valid stock returns a completed sale with correct totals and profit. `POST /sales` with insufficient stock returns a clear error and makes no DB changes. `PATCH /sales/{id}` after 20 minutes returns `requires_approval: true` for employees but succeeds for managers.

**Guiding questions for Covenant:**
1. Stock check and deduction must be atomic — what happens if you check stock, find it sufficient, but then another request deducts it before you commit? How does a DB transaction protect against this?
2. When an employee edits a sale, the stock delta needs to be recalculated — if they had 3 units and now want 5, you need to deduct 2 more. Where exactly in the service layer does this delta calculation live, and what are the steps?

---

## 👤 Goodness — Sales UI + Cart + Payment

### Execution Checklist
- [ ] `frontend/pages/sales.html`: sales dashboard page
- [ ] Product search bar and category filter (fetches from `GET /products`)
- [ ] Cart component — add product, edit quantity, remove item, running total
- [ ] Payment method selector — Cash, Transfer, POS buttons
- [ ] "Complete Sale" button with confirmation modal before submission
- [ ] On success: cart resets, show success toast "Sale completed"
- [ ] On stock error: show clear error message per product, do not reset cart
- [ ] Edit sale UI — show edit button only within 20 minutes, hide after
- [ ] After 20 minutes: show "Requires manager approval" state instead of edit button
- [ ] Add sale to offline queue (IndexedDB) if server is unreachable — mark as `PENDING_SYNC`
- [ ] Show `PENDING_SYNC` label on unsynced sales in transaction history

### Socratic Task Spec
**Objective:** Build the sales flow from product selection to completed sale — with cart management, payment method selection, and offline queue fallback when the server is unreachable.

**Constraints:**
- Vanilla JS only
- Cart state lives in memory — not localStorage, not IndexedDB
- Offline queue uses IndexedDB — not localStorage (this was the Phase 1 question Goodness answered)
- Edit button visibility is controlled by comparing `Date.now()` to `editable_until` from the sale response
- Never trust the server's `editable_until` blindly — display it, but the server enforces it

**Required Documentation:**
- MDN: IndexedDB API
- MDN: Date and time in JS
- `FRONTEND_SPEC.md` §§4, 5, 10, 11
- `SYNC_ENGINE.md` §3 — offline queue record shape

**Expected Output:** A logged-in employee can search products, build a cart, complete a sale, and see it confirmed. If the server is unreachable, the sale goes into the IndexedDB queue marked `PENDING_SYNC`. The edit button disappears after 20 minutes.

**Guiding questions for Goodness:**
1. The cart holds items in memory — what data structure best represents a cart where the same product cannot appear twice but quantities can be updated?
2. When a sale goes into the offline queue, it needs a `transaction_id` generated client-side. What property makes a good `transaction_id`, and why does it need to be generated before the server ever sees the request?

---

## ✅ Definition of Done — Phase 3 (whole team)

A Phase 3 feature is **only** done if:
- [ ] `POST /sales` with valid stock returns a completed sale
- [ ] `POST /sales` with insufficient stock rejects the entire sale with no DB changes
- [ ] Stock levels are correctly deducted after a successful sale
- [ ] `profit_at_sale` is correctly calculated and stored
- [ ] `editable_until` is 20 minutes after `created_at` on every sale
- [ ] `PATCH /sales/{id}` within 20 minutes succeeds for employees
- [ ] `PATCH /sales/{id}` after 20 minutes returns `requires_approval: true` for employees
- [ ] `PATCH /sales/{id}` after 20 minutes succeeds for managers
- [ ] `POST /sales/{id}/cancel` restores stock correctly
- [ ] Every sale action creates an `AuditLog` entry
- [ ] Cart builds correctly — no duplicate products, quantities editable
- [ ] Successful sale resets cart and shows toast
- [ ] Stock error shows per-product message without resetting cart
- [ ] Edit button disappears after 20 minutes on the frontend
- [ ] Offline sale goes into IndexedDB queue marked `PENDING_SYNC`

**Out of scope this phase:** inventory editing, purchase/restock flow, sync engine, reports, conflict resolution.

---

## 🗓️ Day-by-Day

| Day | ENJ | Covenant | Goodness |
|---|---|---|---|
| 1 | `Sale` + `SaleItem` models | Route stubs, validator skeleton | `sales.html` shell, product search UI |
| 2 | **Ship all 4 models** (unblocks Covenant), `schema.sql` updates | `create_sale()` service — stock check + deduction | Cart component — add, edit, remove |
| 3 | Seed demo sales, extend `reset` | **Ship `POST /sales`** (unblocks Goodness), `get_sale()` | Wire cart to `POST /sales`, success/error states |
| 4 | Buffer / help unblock | `edit_sale()` — edit window + role check, `cancel_sale()` | Payment method selector, confirmation modal |
| 5 | Buffer | `AuditLog` entries on all actions, buffer | Edit button 20-min logic, offline queue fallback |

---

## 🚨 Non-negotiable team rules
1. All field names and contracts above are locked — no freelancing
2. `Numeric(10, 2)` for every money field — no `Float`, no `Real`
3. Stock check and deduction are always in the same transaction
4. Services accept session as a parameter — never open their own
5. `AuditLog` entries are created for every sale action — no exceptions
6. Log what shipped each day in `CHANGELOG.md`
7. Blockers stated explicitly
8. No inventory editing, sync, or reports work this phase
>>>>>>> a42e0680ca5389a118a3e26d2010d39f54282c44
