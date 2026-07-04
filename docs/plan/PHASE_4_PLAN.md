# 🚀 Phase 4 — Inventory Management
## Sales Management System (Offline-First POS)

**Stack:** Flask · Raw SQLAlchemy 2.0 · SQLite · Vanilla JS

**Team:**
| Person | Owns |
|---|---|
| **Goodness** | `frontend/` — inventory UI, product CRUD, low-stock display, purchase/restock UI |
| **Covenant** | `backend/routes/`, `controllers/`, `services/`, `utils/` — product endpoints, purchase flow, approval logic |
| **ENJ** | `backend/models/` — Purchase, PurchaseItem models, `database/schema.sql`, `cli/cli.py` |

---

## 🎯 Phase 4 Goal (one sentence)

By end of phase: admins and managers can add, edit, and soft-delete products, create purchase/restock entries, and approve them — with every stock movement logged in `InventoryLog` and visible in the UI.

### ⚠️ Critical dependencies
- Covenant's purchase routes are blocked on ENJ's `Purchase` and `PurchaseItem` models — **ENJ ships both by Day 2**
- Goodness's inventory UI is blocked on Covenant's product endpoints — **Covenant ships `GET /products`, `POST /products`, `PATCH /products/{id}` by Day 3**
- All field names and contracts locked below — agree before coding

---

## 🔒 Locked Contracts (agree before coding)

### POST /products — Request
```json
{
  "name": "string",
  "category": "string (optional)",
  "selling_price": "number",
  "cost_price": "number",
  "stock_quantity": "number"
}
```

### POST /products — Response (success)
```json
{
  "success": true,
  "product": {
    "id": "uuid",
    "name": "string",
    "category": "string",
    "selling_price": "number",
    "cost_price": "number",
    "stock_quantity": "number",
    "is_active": true,
    "created_at": "timestamp",
    "updated_at": "timestamp"
  }
}
```

### PATCH /products/{id} — Request
```json
{
  "name": "string (optional)",
  "category": "string (optional)",
  "selling_price": "number (optional)",
  "cost_price": "number (optional)",
  "stock_quantity": "number (optional)"
}
```

### DELETE /products/{id} — Response
```json
{
  "success": true,
  "message": "Product deactivated"
}
```

### POST /purchases — Request
```json
{
  "items": [
    {
      "product_id": "uuid",
      "quantity": "number",
      "cost_price": "number"
    }
  ],
  "supplier": "string (optional)"
}
```

### POST /purchases — Response (success)
```json
{
  "success": true,
  "purchase": {
    "id": "uuid",
    "status": "pending",
    "total_cost": "number",
    "created_by": "uuid",
    "created_at": "timestamp",
    "items": []
  }
}
```

### POST /purchases/{id}/approve — Response
```json
{
  "success": true,
  "message": "Purchase approved. Stock updated.",
  "purchase_id": "uuid"
}
```

### GET /products — Response
```json
{
  "success": true,
  "products": [
    {
      "id": "uuid",
      "name": "string",
      "category": "string",
      "selling_price": "number",
      "cost_price": "number",
      "stock_quantity": "number",
      "is_active": true,
      "created_at": "timestamp",
      "updated_at": "timestamp"
    }
  ]
}
```

---

## 📋 Business Rules (non-negotiable)

- `DELETE /products/{id}` is a **soft delete** — sets `is_active = false`, never removes the row
- `GET /products` returns only `is_active = true` products by default
- Stock can **never go below zero** — enforced at the service layer
- Purchase entries require **admin approval** before stock is incremented
- Stock is only incremented after approval — never on purchase creation
- Every stock movement (sale deduction, restock approval, manual adjustment) creates an `InventoryLog` entry
- Product price edits are logged in `AuditLog`
- All product CRUD is restricted to **admin and manager** roles
- Employees can view products but cannot create, edit, or delete them
- `cost_price` on a `PurchaseItem` is the price paid at time of purchase — snapshotted, not linked to product's current `cost_price`

---

## 👤 ENJ — Models + Schema + CLI

### Execution Checklist
- [x] `backend/models/models.py`: add `Purchase` model — fields: `id, created_by, supplier, status, total_cost, created_at, approved_by, approved_at`
- [x] `backend/models/models.py`: add `PurchaseItem` model — fields: `id, purchase_id, product_id, quantity, cost_price`
- [x] `database/schema.sql`: add `purchases` and `purchase_items` tables matching ORM models
- [x] `cli/cli.py`: extend `seed` to insert 2–3 demo purchases (one approved, one pending)
- [x] `cli/cli.py`: extend `reset` to clear `purchases` and `purchase_items` in FK-safe order

### Socratic Task Spec
**Objective:** Define `Purchase` and `PurchaseItem` models with correct foreign keys, status constraints, and nullable approval fields — matching the approval flow in the business rules.

**Constraints:**
- `Mapped` / `mapped_column` only
- `Numeric(10, 2)` for `total_cost` and `cost_price`
- `status` constrained to `pending | approved | rejected`
- `approved_by` and `approved_at` are nullable — they only populate on approval
- `created_by` is a FK to `users.id`
- `approved_by` is a FK to `users.id`

**Required Documentation:**
- SQLAlchemy 2.0 — nullable fields and constraints
- SQLAlchemy 2.0 — multiple FK relationships to the same table

**Expected Output:** `setup` creates both tables. `seed` inserts one pending and one approved purchase with items. `reset` clears them without FK errors.

**Guiding questions for ENJ:**
1. `Purchase` has two foreign keys pointing to `users.id` — `created_by` and `approved_by`. How does SQLAlchemy handle two relationships to the same table, and what do you need to specify to avoid an ambiguity error?
2. `approved_by` and `approved_at` are null until approval happens — what does that tell you about the approval flow, and how would you write a query that finds all purchases still waiting for approval?

---

## 👤 Covenant — Product + Purchase Endpoints

### Execution Checklist
- [X] `backend/routes/products.py`: Blueprint with routes — `GET /products`, `POST /products`, `PATCH /products/{id}`, `DELETE /products/{id}`
- [X] `backend/routes/purchases.py`: Blueprint with routes — `POST /purchases`, `GET /purchases/{id}`, `GET /purchases/history`, `POST /purchases/{id}/approve`
- [X] `backend/controllers/products_controller.py`: request/response for all product routes
- [X] `backend/controllers/purchases_controller.py`: request/response for all purchase routes
- [X] `backend/services/products_service.py`:
  - `get_all_products(session)` — active only
  - `create_product(data, session)` — validates, creates, logs audit
  - `edit_product(product_id, data, session)` — validates, updates, logs audit
  - `deactivate_product(product_id, session)` — soft delete, logs audit
- [X] `backend/services/purchases_service.py`:
  - `create_purchase(user_id, items, supplier, session)` — creates pending purchase
  - `approve_purchase(purchase_id, admin_id, session)` — increments stock, logs inventory, logs audit
  - `get_purchase(purchase_id, session)`
  - `get_purchase_history(session)`
- [X] `backend/utils/validators.py`: validate product payload, validate purchase payload
- [X] All product write routes protected with `@require_role('admin', 'manager')`
- [X] `POST /purchases/{id}/approve` protected with `@require_role('admin')`
- [X] `backend/app.py`: register both new blueprints

### Socratic Task Spec
**Objective:** Build full product CRUD with soft delete and full purchase flow with admin approval — every stock change goes through `InventoryLog`, every sensitive action goes through `AuditLog`.

**Constraints:**
- Services accept session as parameter — never open their own
- Soft delete sets `is_active = false` — never `DELETE FROM products`
- Stock increment happens **only** inside `approve_purchase()` — not in `create_purchase()`
- `InventoryLog` entry created on every stock movement — change_type: `restock` on approval
- `AuditLog` entry created on product create, edit, deactivate, and purchase approval

**Required Documentation:**
- SQLAlchemy 2.0 — update patterns
- SQLAlchemy 2.0 — transactions

**Expected Output:** `POST /products` creates a product visible in `GET /products`. `DELETE /products/{id}` hides it from `GET /products` but it still exists in the DB. `POST /purchases/{id}/approve` increments stock and creates an `InventoryLog` entry.

**Guiding questions for Covenant:**
1. `approve_purchase()` needs to increment stock for every item in the purchase — what happens if one item's product has been deactivated between purchase creation and approval? Does the approval succeed, fail, or partially succeed?
2. `GET /products` should only return active products by default — how would you add an optional `include_inactive=true` query param for admin use without breaking the default behaviour?

---

## 👤 Goodness — Inventory UI + Purchase UI

### Execution Checklist
- [X] `frontend/pages/inventory.html`: inventory page
- [X] Product list — name, selling price, stock quantity, low-stock highlight (amber) for stoXk ≤ 5
- [X] Add product form — name, category, selling price, cost price, stock quantity
- [X] Edit product inline or modal — all fields editable
- [X] Soft delete — confirmation prompt before deactivating
- [X] `frontend/pages/purchases.html`: purchase/restock page
- [X] Purchase entry form — select product, quantity, cost price per item
- [X] Purchase history list — show status (pending / approved)
- [X] Admin-only: approve button visible only to admin role
- [X] Hide add/edit/delete controls from employees — show read-only view only
- [X] Low-stock alert banner — shown when any product stock ≤ 5

### Socratic Task Spec
**Objective:** Build the inventory and purchase pages with role-aware controls — employees see read-only, managers can CRUD products, admins can approve purchases.

**Constraints:**
- Vanilla JS only
- Role is read from the JWT payload stored in localStorage — use `auth.js` from Phase 2
- Never show admin/manager controls to employees — check role before rendering, not after
- Low-stock threshold is 5 units — highlight in amber, never green

**Required Documentation:**
- `FRONTEND_SPEC.md` §§6, 7
- MDN: fetch API

**Expected Output:** Inventory page loads live products, highlights low stock, and shows add/edit/delete only to admin and manager. Purchase page allows restock entries and shows approve button to admin only.

**Guiding questions for Goodness:**
1. Role-based UI — you have the role from the JWT in localStorage. At what point in the page lifecycle do you check the role and show/hide controls — on page load, after fetch, or both? What breaks if you only do it in one place?
2. The low-stock highlight needs to update every time the product list re-renders — how do you structure your render function so the amber highlight is applied automatically without a separate pass over the list?

---

## ✅ Definition of Done — Phase 4 (whole team)

A Phase 4 feature is **only** done if:
- [X] `POST /products` creates a product visible in `GET /products`
- [X] `PATCH /products/{id}` updates the product and logs the change
- [X] `DELETE /products/{id}` soft deletes — product hidden from list but exists in DB
- [X] Employees cannot access product write endpoints — `403` returned
- [X] `POST /purchases` creates a pending purchase with no stock change
- [X] `POST /purchases/{id}/approve` increments stock and creates `InventoryLog` entry
- [X] Non-admin cannot approve a purchase — `403` returned
- [X] Stock never goes below zero
- [X] Every stock movement has a corresponding `InventoryLog` entry
- [X] Every sensitive action has a corresponding `AuditLog` entry
- [X] Inventory page shows live products with low-stock highlighting
- [X] Add/edit/delete controls hidden from employees
- [X] Purchase history shows correct status per entry
- [X] Approve button visible to admin only

**Out of scope this phase:** reports, sync engine, conflict resolution.

---

## 🗓️ Day-by-Day

| Day | ENJ | Covenant | Goodness |
|---|---|---|---|
| 1 | `Purchase` + `PurchaseItem` models | Product route stubs + Blueprint | `inventory.html` shell, product list fetch |
| 2 | **Ship both models** (unblocks Covenant), `schema.sql` updates | `products_service.py` — get, create, edit, soft delete | Add product form, edit modal |
| 3 | Seed demo purchases, extend `reset` | **Ship product endpoints** (unblocks Goodness), purchase Blueprint stubs | Wire add/edit/delete to endpoints, role-based controls |
| 4 | Buffer / help unblock | `purchases_service.py` — create, approve, history | `purchases.html`, purchase entry form, history list |
| 5 | Buffer | `InventoryLog` + `AuditLog` on all actions, buffer | Approve button (admin only), low-stock banner, buffer |

---

## 🚨 Non-negotiable team rules
1. All contracts above are locked — no field name changes without team decision
2. Soft delete only — never hard delete a product
3. Stock increment happens only on purchase approval — never on creation
4. `Numeric(10, 2)` for every money field
5. `InventoryLog` entry on every stock movement — no exceptions
6. Services accept session as parameter — never open their own
7. Log what shipped each day in `CHANGELOG.md`
8. Blockers stated explicitly
9. No reports, sync, or conflict resolution work this phase
>>>>>>> a42e0680ca5389a118a3e26d2010d39f54282c44
