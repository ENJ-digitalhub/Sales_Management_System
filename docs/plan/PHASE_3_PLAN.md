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