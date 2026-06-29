-- ============================================================
-- Sales Management System — Database Schema
-- Offline-First | SQLite
-- Author: Ekwere Noble / Swingle Noble
-- ============================================================

-- Enable foreign key enforcement (REQUIRED in SQLite)
PRAGMA foreign_keys = ON;


-- ============================================================
-- 1. USERS
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id                  TEXT PRIMARY KEY,           -- UUID v4
    name                TEXT NOT NULL,
    username            TEXT NOT NULL UNIQUE,
    password_hash       TEXT NOT NULL,
    role                TEXT NOT NULL CHECK (role IN ('admin', 'manager', 'employee')),
    phone_or_email      TEXT,
    account_name        TEXT,                       -- Bank account name (nullable)
    bank_name           TEXT,                       -- Bank name (nullable)
    account_number      TEXT,                       -- Bank account number (nullable)
    pin_hash            TEXT,                       -- Optional PIN for fast login
    is_active           INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Notes:
-- Only one true admin — enforced at application level via env config
-- PIN is optional; set by user after first login
-- is_active = 0 means deactivated (not deleted)


-- ============================================================
-- 2. PRODUCTS
-- ============================================================
CREATE TABLE IF NOT EXISTS products (
    id              TEXT PRIMARY KEY,               -- UUID v4
    name            TEXT NOT NULL,
    category        TEXT,                           -- Optional
    selling_price   NUMERIC(10, 2) NOT NULL CHECK (selling_price >= 0),
    cost_price      NUMERIC(10, 2) NOT NULL CHECK (cost_price >= 0),
    stock_quantity  INTEGER NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    is_active       INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))  -- updated at application level
);

-- Notes:
-- SOFT DELETE only — set is_active = 0, never DELETE rows
-- This preserves historical sale references
-- stock_quantity can NEVER go below 0 (enforced by CHECK + service layer)
-- updated_at must be updated manually on every PATCH


-- ============================================================
-- 3. SALES
-- ============================================================
CREATE TABLE IF NOT EXISTS sales (
    id              TEXT PRIMARY KEY,               -- UUID v4
    receipt_number  TEXT NOT NULL UNIQUE,           -- Human-readable receipt ID
    user_id         TEXT NOT NULL,
    total_amount    NUMERIC(10, 2) NOT NULL CHECK (total_amount >= 0),
    profit_at_sale  NUMERIC(10, 2) NOT NULL DEFAULT 0,        -- Snapshot of profit at time of sale
    payment_method  TEXT NOT NULL CHECK (payment_method IN ('cash', 'transfer', 'pos')),
    status          TEXT NOT NULL DEFAULT 'completed' CHECK (status IN ('completed', 'edited', 'cancelled')),
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    editable_until  TEXT NOT NULL DEFAULT (datetime('now', '+20 minutes'))
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT
);

-- Notes:
-- editable_until is NOT stored — computed dynamically as created_at + 20 minutes
-- After 20 minutes, edits require manager approval (enforced in service layer)
-- profit_at_sale is snapshotted to avoid recalculation issues if prices change later


-- ============================================================
-- 4. SALE ITEMS
-- ============================================================
CREATE TABLE IF NOT EXISTS sale_items (
    id                  TEXT PRIMARY KEY,           -- UUID v4
    sale_id             TEXT NOT NULL,
    product_id          TEXT NOT NULL,
    quantity            INTEGER NOT NULL CHECK (quantity > 0),
    unit_price          NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0),      -- Price at time of sale
    cost_price_at_sale  NUMERIC(10, 2) NOT NULL CHECK (cost_price_at_sale >= 0), -- Snapshot for profit tracking
    total_price         NUMERIC(10, 2) NOT NULL CHECK (total_price >= 0),

    FOREIGN KEY (sale_id)    REFERENCES sales(id)    ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
);

-- Notes:
-- product_id uses RESTRICT (not CASCADE) — deleted products must be soft-deleted
-- cost_price_at_sale is snapshotted at time of sale for accurate profit history


-- ============================================================
-- 5. PURCHASES (RESTOCKING)
-- ============================================================
CREATE TABLE IF NOT EXISTS purchases (
    id              TEXT PRIMARY KEY,               -- UUID v4
    user_id         TEXT NOT NULL,                  -- Who created the purchase entry
    status          TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    total_cost      NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (total_cost >= 0),
    notes           TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    approved_by     TEXT,                           -- Admin user_id who approved (nullable)
    approved_at     TEXT,                           -- Timestamp of approval (nullable)

    FOREIGN KEY (user_id)     REFERENCES users(id) ON DELETE RESTRICT,
    FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Notes:
-- Purchases only affect inventory AFTER admin approval
-- All roles can create a purchase entry


-- ============================================================
-- 6. PURCHASE ITEMS
-- ============================================================
CREATE TABLE IF NOT EXISTS purchase_items (
    id          TEXT PRIMARY KEY,                   -- UUID v4
    purchase_id TEXT NOT NULL,
    product_id  TEXT NOT NULL,
    quantity    INTEGER NOT NULL CHECK (quantity > 0),
    cost_price  NUMERIC(10, 2) NOT NULL CHECK (cost_price >= 0),
    total_cost  NUMERIC(10, 2) NOT NULL CHECK (total_cost >= 0),

    FOREIGN KEY (purchase_id) REFERENCES purchases(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id)  REFERENCES products(id)  ON DELETE RESTRICT
);


-- ============================================================
-- 7. INVENTORY LOGS
-- ============================================================
CREATE TABLE IF NOT EXISTS inventory_logs (
    id              TEXT PRIMARY KEY,               -- UUID v4
    product_id      TEXT NOT NULL,
    change_type     TEXT NOT NULL CHECK (change_type IN ('sale', 'restock', 'adjustment', 'cancellation')),
    quantity_change INTEGER NOT NULL,               -- Negative for sale/removal, positive for restock
    reference_id    TEXT,                           -- sale_id or purchase_id (nullable)
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
);

-- Notes:
-- Every stock movement MUST produce a log entry
-- quantity_change is negative for deductions (sales), positive for additions (restock)


-- ============================================================
-- 8. AUDIT LOGS
-- ============================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id          TEXT PRIMARY KEY,                   -- UUID v4
    user_id     TEXT,                               -- Nullable — system actions may have no user
    action_type TEXT NOT NULL CHECK (action_type IN ('create_sale', 'edit_sale', 'cancel_sale', 'delete_sale','create_product', 'edit_product', 'delete_product','create_user', 'edit_user', 'deactivate_user','login', 'logout','approve_purchase', 'create_purchase','sync_push', 'sync_conflict')),
    entity_type TEXT NOT NULL CHECK (entity_type IN ('sale', 'product', 'user', 'purchase', 'system')),
    entity_id   TEXT,                               -- ID of the affected record
    log_metadata    TEXT,                               -- JSON string with extra context
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Notes:
-- IMMUTABLE — rows are NEVER updated or deleted
-- Logs every system action without exception
-- metadata stores JSON (serialized in application layer)


-- ============================================================
-- 9. SYNC QUEUE
-- ============================================================
CREATE TABLE IF NOT EXISTS sync_queue (
    id              TEXT PRIMARY KEY,               -- Local UUID (device-generated)
    transaction_id  TEXT NOT NULL UNIQUE,           -- UUID v4 — idempotency key, globally unique
    device_id       TEXT NOT NULL,
    entity_type     TEXT NOT NULL,                  -- 'sale', 'product', 'user', etc.
    operation       TEXT NOT NULL CHECK (operation IN ('CREATE', 'UPDATE', 'DELETE')),
    payload         TEXT NOT NULL,                  -- Full JSON request body
    status          TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'synced', 'failed', 'conflict')),
    retry_count     INTEGER NOT NULL DEFAULT 0,
    last_attempt_at TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))

    FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE SET NULL
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE SET NULL
);

-- Notes:
-- transaction_id is the idempotency key — server rejects duplicates using this
-- Stored in SQLite — survives app restart
-- Max retries: 5 (enforced in sync engine, not here)
-- Batch size: 10–20 per sync push


-- ============================================================
-- 10. DEVICES
-- ============================================================
CREATE TABLE IF NOT EXISTS devices (
    id           TEXT PRIMARY KEY,                  -- UUID v4
    user_id      TEXT NOT NULL,
    device_name  TEXT,
    is_active    INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    last_seen_at TEXT NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Notes:
-- One active device per user — enforced in auth service
-- New login sets previous device is_active = 0 immediately


-- ============================================================
-- INDEXES (Performance)
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_sales_user_id        ON sales(user_id);
CREATE INDEX IF NOT EXISTS idx_sales_created_at     ON sales(created_at);
CREATE INDEX IF NOT EXISTS idx_sale_items_sale_id   ON sale_items(sale_id);
CREATE INDEX IF NOT EXISTS idx_sale_items_product_id ON sale_items(product_id);
CREATE INDEX IF NOT EXISTS idx_inventory_logs_product ON inventory_logs(product_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id   ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity    ON audit_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_sync_queue_status    ON sync_queue(status);
CREATE INDEX IF NOT EXISTS idx_sync_queue_device    ON sync_queue(device_id);
CREATE INDEX IF NOT EXISTS idx_devices_user_id      ON devices(user_id);
CREATE INDEX IF NOT EXISTS idx_purchases_user_id    ON purchases(user_id);