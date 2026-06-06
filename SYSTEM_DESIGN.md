# 🗄️ SYSTEM DESIGN — Sales Management System (Offline-First)
## 1. 🧠 SYSTEM OVERVIEW

The Sales Management System is an offline-first retail platform designed for provision stores and supermarkets operating in low or unstable internet environments.

It runs on a single-store-per-installation model in offline mode, where one PC acts as the central server and source of truth.

In future cloud mode, the architecture expands to multi-store SaaS where a centralized server hosts multiple store instances.

### Core Principles
- Server is the only source of truth
- Clients are execution layers, not data owners
- Offline operations are supported via queued synchronization
- All critical business logic is validated server-side
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
- REST API handles all data operations
- WebSockets handle live updates only (UI synchronization)
### 2.2 Hybrid Communication Model
#### REST (Primary System Backbone)

Used for:

- Sales creation
- Inventory updates
- Authentication
- Purchases
- Reports
#### WebSockets (Real-Time Layer)

Used for:

- Live stock updates
- Sales notifications
- Dashboard synchronization
- UI refresh triggers
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
## 3. 🧩 SYSTEM MODULE ARCHITECTURE
### 3.1 Authentication Module
- User login/logout
- JWT-based session management
- Role-based access control (RBAC)
- Device whitelist enforcement (admin approved devices only)
### 3.2 Sales Engine
- Transaction creation
- Cart processing
- Price calculation
- Inventory deduction
- Receipt generation
### 3.3 Inventory Engine
- Product lifecycle management
- Stock tracking
- Low-stock alerts
- Stock validation on every sale
### 3.4 Purchase (Restocking) Module 📦

Supports inventory replenishment.

#### Structure:
- Supplier (optional in Phase 1 extension-ready design)
- Purchase entries
- Cost price tracking
- Stock increment logic
#### Behavior:
- Manual entry supported (Phase 1)
- Designed for expansion into supplier-based system later
- Every purchase updates inventory + audit log
### 3.5 Sync Engine (Offline Core)

Handles all offline-first behavior.

#### Responsibilities:
- Queue ingestion from clients
- Idempotency enforcement
- Conflict detection
- Retry management
- Event ordering correction
#### Sync Strategy:
- Exponential backoff retry
- Limited retry attempts
- Batch processing per device
### 3.6 Reporting Engine
- Daily sales reports
- Monthly summaries
- Employee performance reports
- Live computed analytics (no heavy precompute dependency)
### 3.7 Audit Logger (Critical System Component)
- Logs every system action
- Immutable records (no edits allowed)
- Tracks:
    - sales
    - inventory changes
    - purchases
    - user actions
## 4. 🔌 API DESIGN (SYSTEM ENTRY POINTS)
### 4.1 Authentication
- POST /auth/login
- POST /auth/logout
- GET /auth/verify
### 4.2 Sales
- POST /sales/create
- GET /sales/{id}
- GET /sales/daily
### 4.3 Inventory
- GET /products
- POST /products
- PATCH /products/{id}
- DELETE /products/{id}
### 4.4 Purchases (Restocking)
- POST /purchases/create
- GET /purchases/{id}
- GET /purchases/history
### 4.5 Sync Engine
- POST /sync/push
- GET /sync/pull
- POST /sync/resolve
### 4.6 Reports
- GET /reports/daily
- GET /reports/monthly
- GET /reports/employee/{id}
### 4.7 Audit
- GET /audit/logs
- GET /audit/user/{id}
## 5. 🔁 DATA FLOW DESIGN
### 5.1 Sales Flow

Client → REST API → Auth Check → Inventory Validation
→ Database Write → Audit Log → WebSocket Broadcast → Response

### 5.2 Purchase Flow

Admin → /purchases/create
- Validate supplier + cost
- Increase inventory
- Log audit event
- Broadcast stock update

### 5.3 Offline Sync Flow

Client Queue → /sync/push
- Server validates:

    - idempotency
    - stock availability
    - event order

- Commit or reject
- return sync result per item
- trigger WebSocket updates

## 6. ⚠️ SYSTEM GUARANTEES
### 6.1 Data Integrity Rules
- Server is absolute authority
- No client-side data is trusted
- No silent failure allowed
### 6.2 Consistency Model
- Strict consistency for:
- sales
- inventory
- purchases
- Eventual consistency allowed for:
- reports
- analytics
### 6.3 Sync Rules
- Retry with exponential backoff
- Limited retry attempts
- Manual resolution only for unresolved conflicts
- Timestamp is always server-controlled
### 6.4 Security Rules
- JWT authentication required
- Device whitelist enforced by admin
- Unauthorized devices rejected at connection level
### 6.5 Reporting Rules
- Live computed reports (no precompute dependency)
- Always reflect latest DB state
## 7. 📱 CLIENT ARCHITECTURE
### Mobile / PC Clients
#### Mode 1: Online
- Direct REST calls
- WebSocket subscription active
#### Mode 2: Offline
- Local queue storage (IndexedDB / SQLite)
- Sync engine pushes when reconnected
#### Cache Strategy
- Full product cache
- Full sales history cache
- Full UI state cache (medium-heavy offline model)
## 8. 🚀 FUTURE SCALING DESIGN
### Phase 2 (Hybrid Cloud)
- Multi-store support
- Central server
- Remote monitoring
- Optional offline mode per store
### Phase 3 (SaaS Platform)
- Full SaaS architecture
- Store isolation (multi-tenant)
- Subscription system
- Global analytics dashboard
## 🧭 FINAL ARCHITECTURAL SUMMARY

This system is designed as:

- Offline-first transactional system
- REST-driven backend core
- WebSocket-enhanced real-time layer
- Strong consistency for business data
- Expandable into full SaaS platform