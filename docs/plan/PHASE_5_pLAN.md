🚀 Phase 5 — Reporting + Audit + Operational Visibility Week

Sales Management System (Offline-First POS)

Stack confirmed: Flask (latest, app factory pattern) · Raw SQLAlchemy 2.0 (no Flask-SQLAlchemy extension) · SQLite · Vanilla JS frontend · JWT · Offline Queue

Team:

Person| Owns
Obinna| "frontend/", reports UI, dashboard rendering, export experience
Covenant| "backend/routes/", "controllers/", "services/", reports APIs, audit enforcement
ENJ| "backend/models/", "database/", report queries, audit persistence

---

🎯 Phase 5 Goal (one sentence)

By end of week: the system becomes observable — users can view reports, trace actions, inspect business activity, and trust that every important change is auditable.

⚠️ Critical dependency

Covenant cannot expose reports until ENJ defines report sources and audit structures. Obinna cannot build dashboards until Covenant finalizes response contracts and aggregation shapes.

Agree on report fields before coding.

---

👤 ENJ — Database + Audit Foundation

Execution Checklist

- [ ] Create "backend/models/audit_log.py"

Fields:

- "id"

- "entity_type"

- "entity_id"

- "action"

- "performed_by"

- "old_value"

- "new_value"

- "created_at"

- [ ] Create "backend/models/report_snapshot.py"

Fields:

- "id"

- "report_type"

- "generated_at"

- "payload"

- [ ] Add indexes:
  
  - "created_at"
  - "entity_type"
  - "performed_by"

- [ ] Update "database/schema.sql"

- [ ] Extend CLI:
  
  - report inspection
  - audit inspection

- [ ] Add reusable query helpers

Socratic Task Spec

Objective: Create persistent reporting and auditing infrastructure that supports operational visibility.

Constraints:

- Audit data must be append-only
- Historical records remain unchanged
- Reporting queries must not mutate state

Required Documentation:

- SQLAlchemy aggregate queries
- SQL indexing basics
- Audit logging patterns

Expected Output:

Running:

python cli/cli.py setup

creates reporting and audit tables successfully.

Guiding questions for ENJ (don't answer yet — sit with these):

1. Should reports calculate live every request or use snapshots?
2. What information is required to reconstruct a business event?

---

👤 Covenant — Backend API + Reporting Logic

Execution Checklist

- [ ] "backend/routes/reports.py"
- [ ] "backend/controllers/report_controller.py"
- [ ] "backend/services/report_service.py"
- [ ] "backend/services/audit_service.py"

Implement:

- [ ] "GET /reports/sales"
- [ ] "GET /reports/inventory"
- [ ] "GET /reports/summary"
- [ ] "GET /audit/logs"

Reports:

- [ ] Daily sales
- [ ] Product performance
- [ ] Revenue totals
- [ ] Inventory movement
- [ ] User activity

Audit:

- [ ] Track mutations
- [ ] Store actor
- [ ] Preserve timestamps

Validation split:

Controller →

- request shape
- filters
- response formatting

Service →

- calculations
- audit generation
- aggregation

Socratic Task Spec

Objective: Build reliable reporting and audit APIs while preserving clean separation.

Constraints:

- No SQL in routes
- Reports are read-only
- Audit generation stays in services
- Aggregation logic is centralized

Required Documentation:

- SQLAlchemy aggregation
- Flask request handling
- Reporting design patterns

Expected Output:

Calling:

GET /reports/sales

returns business summaries derived from real data.

Guiding questions for Covenant (don't answer yet — sit with these):

1. If two endpoints compute revenue differently, which one becomes trusted?
2. Which events deserve audit records and which do not?

---

👤 Obinna — Frontend + Dashboard Experience

Execution Checklist

- [ ] "frontend/pages/dashboard.html"
- [ ] "frontend/pages/reports.html"
- [ ] "frontend/services/reports.js"

Build:

- [ ] Dashboard layout
- [ ] Report cards
- [ ] Filters
- [ ] Report table
- [ ] Empty states
- [ ] Error states
- [ ] Loading indicators
- [ ] Audit viewer

Dashboard Metrics:

sales
inventory
transactions
sync status

Socratic Task Spec

Objective: Build operational visibility for users without duplicating backend calculations.

Constraints:

- Frontend displays data only
- No business calculations in UI
- Reports remain responsive

Required Documentation:

- Fetch API
- Table rendering
- Browser performance basics

Expected Output:

Users can:

- open dashboard
- inspect reports
- filter results
- view audit history

using live backend data.

Guiding questions for Obinna (don't answer yet — sit with these):

1. Should the UI cache reports?
2. What should happen when reports are empty?

---

✅ Definition of Done — Phase 5 (whole team)

A Phase 5 feature is only done if:

- [ ] Reports load successfully
- [ ] Audit records exist
- [ ] Aggregations are consistent
- [ ] Dashboard reflects live data
- [ ] Audit remains immutable
- [ ] Layer chain remains:
  route → controller → service → model

Out of scope this week (do not touch):
deployment, load testing, production rollout

---

🗓️ Suggested Day-by-Day

Day| ENJ| Covenant| Obinna
1| Audit models| Reports blueprint| Dashboard shell
2| Report queries| Sales reports| Report UI
3| Snapshot support| Audit service| Filters
4| Schema polish| Aggregation refinement| Audit viewer
5| Buffer| Buffer| Polish

---

🚨 Non-negotiable team rules (carried over)

1. Reports never mutate data.
2. Audit history cannot be edited.
3. Backend calculations are source of truth.
4. No deployment or production optimization this week — scope creep kills Phase 5.