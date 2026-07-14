# 📦 Sales Management System (Offline Retail Management)

![Status](https://img.shields.io/badge/Status-Active-green)
![Backend](https://img.shields.io/badge/Backend-Python-blue)
![Frontend](https://img.shields.io/badge/Frontend-HTML%20%7C%20CSS%20%7C%20JS-orange)
![Database](https://img.shields.io/badge/Database-SQLite-lightgrey)
![Architecture](https://img.shields.io/badge/Mode-Offline--First-important)
![Network](https://img.shields.io/badge/Network-Local%20WiFi-blueviolet)
![Interface](https://img.shields.io/badge/Access-PC%20%2B%20Mobile-success)

## Overview

The Sales Management System is an **offline-first retail** management platform designed for provision stores, supermarkets, and small-to-large retail shops.

It replaces manual record-keeping methods such as notebooks, Excel sheets, and loosely structured POS usage with a structured, reliable system that runs on a store’s PC and connects to mobile devices over a local network.

## 🧠 Core Concept

TX RetailOS runs on a single central system — one server, one database,
one source of truth. Every action (sales, stock updates, reports) writes
directly to the database and is reflected instantly everywhere else in
the app. There is nothing to configure, sync, or link between devices.

**Offline Mode & Sync — Coming Soon.** A future version will let staff
keep working without a connection and sync automatically once reconnected.
This is not available yet.

---

## 👥 User Roles

### Admin (Store Owner)

- Full control over the system
- Manages products, pricing, employees, and reports
- Access to audit logs and system analytics

### Manager

- Oversees sales and inventory
- Reviews reports and employee performance
- Operates under admin-defined permissions

### Employee

- Records sales transactions
- Limited to operational tasks
- Cannot modify system configurations

> Note: Roles are independent of device.
Any authorized user can access the system from either PC or mobile depending on permissions.

---

## ⚙️ Key Features (Phase 1)

### 🧾 Sales Management

- Fast transaction recording
- Product selection and quantity handling
- Automatic total calculation

### 📦 Inventory Management

- Add, edit, delete products
- Track stock levels
- Low-stock alerts

### 💰 Profit Tracking

- Cost price vs selling price tracking
- Automatic profit calculation
- Daily, weekly, and monthly summaries

### 👨‍💼 Employee Accountability

- Individual login IDs
- Sales tracking per employee
- Performance visibility for managers/admins

### 📊 Reporting System

- Daily sales reports
- Monthly and yearly summaries
- Employee-based performance reports

### 🧾 Audit Trail

- Tracks all transactions and key actions
- Logs edits and deletions
- Ensures transparency and accountability

### 📱 Mobile Interface

- Responsive interface built with HTML, CSS, and JavaScript
- Optimized for mobile usage
- Simple navigation for non-technical users

---

## 🧱 System Architecture

### Local Server Model

- Backend runs on a store PC using Python
- Database is stored locally (SQLite or similar)
- Devices connect via local WiFi network

### How It Works

1. The PC starts the server
2. Other devices connect using the PC’s IP address
3. All requests are processed locally
4. Data is stored instantly in the local database

Think of it as a mini internal network system inside the shop.

---

## 🗄️ Database Strategy (Phase 1)

- Single store per installation
- All data stored locally on the PC
- No multi-store support in this phase

## Future Upgrade

- Multi-tenant system
- Cloud synchronization
- Remote access

---

## 🔐 Authentication & Security

- Login required for all users
- Role-based access control (RBAC)
- Activity logging for accountability
- Admin-controlled permissions

### Security Focus

- Prevent unauthorized changes
- Maintain data integrity
- Track all user actions transparently

---

## 🖥️ CLI Developer Tools

Developer-only tools for system control:

- "setup" → Initialize system
- "reset-db" → Reset database
- "seed-demo" → Populate demo data

These tools are restricted to developers only.

---

## 📲 Getting Started

1. Open the app in your browser (or install it as a PWA)
2. Log in with your account
3. Start using it immediately — no sync setup, no device linking

---

## 📡 Local Network Setup

1. Connect PC and mobile devices to the same WiFi network
2. Get PC IP address (e.g. 192.168.1.10)
3. Open on mobile browser:

```
http://192.168.1.10:PORT
```

---

## 🧩 Frontend Structure

### Built using:

- HTML
- CSS
- JavaScript

### Modules

- Login
- Sales dashboard
- Inventory
- Reports
- Employee panel

### Design Focus

- Speed
- Simplicity
- Ease of use for older users

---

## ⚙️ Backend Structure

### Built using:

- Python
- SQLite (for storage)
- Local server (offline-first)

### Modules

- Product management
- Sales processing
- Inventory tracking
- System controls (reset, seed, setup)

### Features

- Runs on local network (WiFi)
- Accessible from PC and mobile browser
- CLI support for system management

### Design Focus

- Reliability (works without internet)
- Simplicity (easy to maintain)
- Clear separation of logic

## 🧪 Data Integrity Philosophy

- Human error is expected
- Accountability reduces fraud
- Logs are more valuable than assumptions

### Therefore:

- Every action is traceable
- Edits and deletions are recorded
- Reports reflect actual system data

---

## 🚀 Future Roadmap

### Phase 2 (Hybrid)

- Optional internet sync
- Cloud backup
- Remote monitoring

### Phase 3 (SaaS Platform)

- Multi-store system
- Global access
- Central dashboards
- Subscription model

---

## 🤝 Development Roles

### Backend

- API design
- Database structure
- CLI tools
- Security

### Frontend

- Mobile UI
- Admin dashboard
- UX optimization

### Shared

- Feature design
- System flow
- API contracts

---

## ⚠️ Design Constraints

- Must work offline
- Must be simple to use
- Must be fast
- Must ensure data integrity

---

## 👤 Authors

**Ekwere Noble**

**Covenant Johnson**

---

## 🧭 Closing Vision

This system begins as a local store management tool and evolves into a full retail platform.

The priority is not complexity.

It is reliability inside real stores with real users.