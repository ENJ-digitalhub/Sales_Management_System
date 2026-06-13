# 🗄️ SYSTEM DESIGN — Sales Management System (Offline-First)

## 1. 🧠 SYSTEM OVERVIEW

The Sales Management System is an offline-first retail platform designed for provision stores and supermarkets operating in low or unstable internet environments.

It runs on a single-store-per-installation model in offline mode, where one PC acts as the central server and source of truth.

In future cloud mode, the architecture expands to multi-store SaaS where a centralized server hosts multiple store instances.

### Core Principles

* Server is the only source of truth
* Clients are execution layers, not data owners
* Offline operations are supported via queued synchronization
* All critical business logic is validated server-side

---

## 2. 🏗️ SYSTEM ARCHITECTURE

### 2.1 Offline Architecture (Current Phase)

```
Mobile / PC Clients
        ↓
Local Network (WiFi)
        ↓
Python Backend Server (Host PC)
        ↓
SQLite Database (Local Storage)
```

### Communication Model

* REST API handles all data operations
* WebSockets handle live updates only (UI synchronization)

### 2.2 Hybrid Communication Model

#### REST (Primary System Backbone)

Used for:

* Sales creation
* Inventory updates
* Authentication
* Purchases (create, approve, reject)
* Reports

#### WebSockets (Real-Time Layer)

Used for:

* Live stock updates
* Sales notifications
* Purchase approval alerts
* Dashboard synchronization
* UI refresh triggers

### 2.3 Offline Sync Architecture

```
Client Offline Queue
        ↓
Sync Engine (Server)
        ↓
Validation + Conflict Resolution
        ↓
Database Commit
        ↓
Broadcast Updates (WebSocket)
```

---

## 3. 🧩 SYSTEM MODULE ARCHITECTURE

### 3.1 Authentication Module

* User login/logout
* JWT-based session management
* Role-based access control (RBAC)
* Device whitelist enforcement (admin-approved devices only)
* One active session per user — new login invalidates previous session

### 3.2 Sales Engine

* Transaction creation (all-or-nothing — no partial commits)
* Cart processing
* Price calculation (backend recalculates regardless of frontend input)
* Inventory deduction
* Receipt generation
* Edit window enforcement (20-minute rule)

### 3.3 Inventory Engine

* Product lifecycle management (soft delete only — `is_active = false`)
* Stock tracking
* Low-stock alerts
* Stock validation on every sale and sync commit

### 3.4 Purchase (Restocking) Module

Supports inventory replenishment with an admin approval gate.

#### Structure:

* Purchase entries with one or more items
* Cost price tracking per item
* Status flow: `pending` → `approved` | `rejected`

#### Behavior:

* Any role can create a purchase entry
* Only admin can approve a purchase
* Stock is updated ONLY after approval
* Every approval and rejection is logged in audit_logs

### 3.5 Sync Engine (Offline Core)

Handles all offline-first behavior.

#### Responsibilities:

* Queue ingestion from clients
* Idempotency enforcement via UUID v4 transaction_id
* Conflict detection and isolation
* Retry management (max 5, exponential backoff)
* Event ordering correction using server timestamps

#### Sync Strategy:

* Exponential backoff: 1s → 2s → 4s → 8s → stop
* Batch processing: 10–20 transactions per request
* Manual resolution required for all unresolved conflicts

### 3.6 Reporting Engine

* Daily sales reports
* Monthly and yearly summaries
* Employee performance reports
* Live computed from committed database state (no precompute dependency)
* Reports exclude unsynced or pending data

### 3.7 Audit Logger (Critical System Component)

* Logs every system action
* Immutable records — no edits or deletions allowed
* Tracks: sales, edits, cancellations, inventory changes, purchases, user actions, conflicts

---

## 4. 🔌 API DESIGN (SYSTEM ENTRY POINTS)

### 4.1 Authentication

* POST /auth/login
* POST /auth/pin-login
* POST /auth/logout
* GET /auth/verify

### 4.2 Sales

* POST /sales
* GET /sales/{id}
* PATCH /sales/{id}
* POST /sales/{id}/cancel
* POST /sales/{id}/request-edit
* GET /sales/daily

### 4.3 Inventory

* GET /products
* POST /products
* PATCH /products/{id}
* DELETE /products/{id} ← soft delete only

### 4.4 Purchases (Restocking)

* POST /purchases
* GET /purchases/{id}
* GET /purchases/history
* PATCH /purchases/{id}/approve ← admin only
* PATCH /purchases/{id}/reject  ← admin only

### 4.5 Sync Engine

* POST /sync
* GET /sync/pull

### 4.6 Reports

* GET /reports/daily
* GET /reports/monthly
* GET /reports/employee/{id}

### 4.7 Audit

* GET /audit/logs
* GET /audit/user/{id}

### 4.8 Users

* POST /users
* PATCH /users/{id}
* PATCH /users/{id}/role
* PATCH /users/{id}/deactivate ← no hard delete

---

## 5. 🔁 DATA FLOW DESIGN

### 5.1 Sales Flow

```
Client → POST /sales → Auth Check → Stock Validation (all-or-nothing)
→ Database Write → Inventory Log → Audit Log → WebSocket Broadcast → Response
```

### 5.2 Purchase Flow

```
Any role → POST /purchases → Create with status=pending
Admin → PATCH /purchases/{id}/approve
→ Stock update → Inventory log → Audit log → WebSocket broadcast
```

### 5.3 Offline Sync Flow

```
Client Queue → POST /sync
→ JWT + device whitelist check
→ For each transaction:
    - Idempotency check (transaction_id)
    - Stock validation
    - Conflict detection
    - Commit or flag conflict
→ Return per-item result
→ WebSocket broadcast for committed items
```

---

## 6. ⚠️ SYSTEM GUARANTEES

### 6.1 Data Integrity Rules

* Server is absolute authority
* No client-side data is trusted
* No silent failure allowed
* Sales are all-or-nothing — no partial commits

### 6.2 Consistency Model

Strict consistency for:

* Sales
* Inventory
* Purchases

Eventual consistency allowed for:

* Reports
* Analytics

### 6.3 Sync Rules

* Retry with exponential backoff (max 5 attempts)
* Manual resolution required for unresolved conflicts
* Server timestamp is always authoritative — device time is display-only

### 6.4 Security Rules

* JWT authentication required
* Device whitelist enforced by admin
* Unauthorized devices rejected at connection level

### 6.5 Reporting Rules

* Live computed from committed database state
* Always reflects latest synced state
* Unsynced transactions are excluded

### 6.6 Product Lifecycle Rule

* Products are SOFT DELETED only (`is_active = false`)
* Hard deletes are not permitted
* Historical sales retain full integrity through soft-deleted references

---

## 7. 📱 CLIENT ARCHITECTURE

### Mobile / PC Clients

#### Mode 1: Online

* Direct REST calls
* WebSocket subscription active

#### Mode 2: Offline

* Local queue storage (SQLite)
* Sync engine pushes on reconnect

#### Cache Strategy

* Full product cache (refreshed on every reconnect)
* Full sales history cache
* Offline queue stored persistently — survives app restart

---

## 8. 🚀 FUTURE SCALING DESIGN

### Phase 2 (Hybrid Cloud)

* Multi-store support
* Central server
* Remote monitoring
* Optional offline mode per store

### Phase 3 (SaaS Platform)

* Full SaaS architecture
* Store isolation (multi-tenant)
* Subscription system
* Global analytics dashboard

---

## 🧭 FINAL ARCHITECTURAL SUMMARY

This system is designed as:

* Offline-first transactional system
* REST-driven backend core
* WebSocket-enhanced real-time layer
* Strong consistency for all business-critical data
* Expandable into full SaaS platform