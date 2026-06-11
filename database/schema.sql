PRAGMA foreign_keys = ON;

-- USERS TABLE
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin','manager','employee')),
    phone TEXT,
    email TEXT,
    account_name TEXT,
    bank_name TEXT,
    account_number TEXT,
    pin_hash TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- PRODUCTS TABLE
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT,
    selling_price REAL NOT NULL CHECK(selling_price >= 0),
    cost_price REAL NOT NULL CHECK(cost_price >= 0),
    stock_quantity INTEGER NOT NULL DEFAULT 0 CHECK(stock_quantity >= 0),
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- SALES TABLE
CREATE TABLE sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_number TEXT NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    total_amount REAL NOT NULL CHECK(total_amount >= 0),
    profit_at_sale REAL NOT NULL DEFAULT 0,
    payment_method TEXT NOT NULL CHECK(payment_method IN ('cash','transfer','pos')),
    status TEXT NOT NULL CHECK(status IN ('completed','edited','cancelled')),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    editable_until DATETIME NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE RESTRICT
);

-- SALE ITEMS TABLE
CREATE TABLE sale_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    unit_price REAL NOT NULL CHECK(unit_price >= 0),
    cost_price_at_sale REAL NOT NULL CHECK(cost_price_at_sale >= 0),
    profit_at_sale REAL NOT NULL DEFAULT 0,
    total_price REAL NOT NULL CHECK(total_price >= 0),
    FOREIGN KEY(sale_id) REFERENCES sales(id) ON DELETE CASCADE,
    FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE RESTRICT
);

-- PURCHASES TABLE
CREATE TABLE purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_number TEXT NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    total_cost REAL NOT NULL CHECK(total_cost >= 0),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE RESTRICT
);

-- PURCHASE ITEMS TABLE
CREATE TABLE purchase_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    purchase_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    unit_cost REAL NOT NULL CHECK(unit_cost >= 0),
    total_cost REAL NOT NULL CHECK(total_cost >= 0),
    FOREIGN KEY(purchase_id) REFERENCES purchases(id) ON DELETE CASCADE,
    FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE RESTRICT
);

-- INVENTORY LOGS TABLE
CREATE TABLE inventory_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    change_type TEXT NOT NULL CHECK(change_type IN ('sale','restock','adjustment')),
    quantity_change INTEGER NOT NULL,
    reference_type TEXT NOT NULL CHECK(reference_type IN ('sale','purchase','adjustment')),
    reference_id INTEGER,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE RESTRICT
);

-- AUDIT LOGS TABLE
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action_type TEXT NOT NULL CHECK(action_type IN ('CREATE','UPDATE','DELETE','VIEW','LOGIN','LOGOUT','REGISTER','APPROVE','REJECT','CANCEL','RESTORE')),
    entity_type TEXT NOT NULL CHECK(entity_type IN ('sale','product','user','system')),
    entity_id INTEGER,
    metadata JSON,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- SYNC QUEUE TABLE
CREATE TABLE sync_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    entity_type TEXT NOT NULL,
    payload JSON NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pending','synced','failed')),
    retry_count INTEGER NOT NULL DEFAULT 0 CHECK(retry_count >= 0),
    last_attempt_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(device_id) REFERENCES devices(id) ON DELETE CASCADE
);

-- DEVICES TABLE
CREATE TABLE devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    device_name TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    last_seen_at DATETIME,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);