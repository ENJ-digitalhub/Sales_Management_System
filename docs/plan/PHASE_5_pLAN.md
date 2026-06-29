# 🚀 Phase 5 — Reports
## Sales Management System (Offline-First POS)

**Stack:** Flask · Raw SQLAlchemy 2.0 · SQLite · Vanilla JS

**Team:**
| Person | Owns |
|---|---|
| **Goodness** | `frontend/` — reports UI, daily/monthly/yearly views, employee performance display |
| **Covenant** | `backend/routes/`, `controllers/`, `services/` — report endpoints, data aggregation |
| **ENJ** | No new models this phase — buffer, help unblock, review queries for correctness |

---

## 🎯 Phase 5 Goal (one sentence)

By end of phase: admins and managers can view real-time daily, monthly, and yearly sales reports — including total revenue, profit, transaction count, and employee performance — all computed live from the DB with no precomputed cache.

### ⚠️ Critical dependencies
- Goodness's report UI is blocked on Covenant's report endpoints — **Covenant ships all three report endpoints by Day 3**
- Reports must never include unsynced data — only committed DB records count
- All response contracts locked below — agree before coding

---

## 🔒 Locked Contracts (agree before coding)

### GET /reports/daily — Response
```json
{
  "success": true,
  "report": {
    "date": "YYYY-MM-DD",
    "total_sales": "number",
    "total_profit": "number",
    "transaction_count": "number",
    "payment_breakdown": {
      "cash": "number",
      "transfer": "number",
      "pos": "number"
    },
    "top_products": [
      {
        "product_id": "uuid",
        "name": "string",
        "quantity_sold": "number",
        "revenue": "number"
      }
    ],
    "employee_performance": [
      {
        "user_id": "uuid",
        "name": "string",
        "transaction_count": "number",
        "total_sales": "number"
      }
    ]
  }
}
```

### GET /reports/monthly — Response
```json
{
  "success": true,
  "report": {
    "month": "YYYY-MM",
    "total_sales": "number",
    "total_profit": "number",
    "transaction_count": "number",
    "payment_breakdown": {
      "cash": "number",
      "transfer": "number",
      "pos": "number"
    },
    "top_products": [],
    "employee_performance": []
  }
}
```

### GET /reports/yearly — Response
```json
{
  "success": true,
  "report": {
    "year": "YYYY",
    "total_sales": "number",
    "total_profit": "number",
    "transaction_count": "number",
    "payment_breakdown": {
      "cash": "number",
      "transfer": "number",
      "pos": "number"
    },
    "monthly_breakdown": [
      {
        "month": "YYYY-MM",
        "total_sales": "number",
        "total_profit": "number",
        "transaction_count": "number"
      }
    ]
  }
}
```

### GET /reports/employee/{id} — Response
```json
{
  "success": true,
  "report": {
    "user_id": "uuid",
    "name": "string",
    "period": "YYYY-MM-DD to YYYY-MM-DD",
    "transaction_count": "number",
    "total_sales": "number",
    "total_profit": "number",
    "sales": []
  }
}
```

---

## 📋 Business Rules (non-negotiable)

- Reports are **always live-computed** — no caching, no precomputed tables
- Reports only include sales with `status = completed | edited` — never `cancelled`
- Only **admin and manager** can access any report endpoint — employees get `403`
- `total_profit` uses `profit_at_sale` snapshotted at sale time — never recalculated from current prices
- `top_products` returns top 5 by quantity sold for the period
- `employee_performance` covers all active employees for the period — zero counts included
- Daily report defaults to today if no `?date=` query param provided
- Monthly report defaults to current month if no `?month=` param provided
- Yearly report defaults to current year if no `?year=` param provided
- Employee report accepts optional `?from=` and `?to=` date range params

---

## 👤 ENJ — Buffer + Query Review

### Execution Checklist
- [ ] Review Covenant's aggregation queries for correctness — specifically profit calculation and date filtering
- [ ] Verify `InventoryLog` and `AuditLog` data from Phases 3 and 4 is sufficient to support report queries
- [ ] Extend `seed` to insert enough demo sales across multiple days, months, and employees to make reports meaningful during testing
- [ ] Help unblock either teammate if needed

### Socratic Task Spec
**Objective:** Ensure the seeded data is rich enough to make every report endpoint return non-trivial results — multiple employees, multiple days, multiple payment methods.

**Constraints:**
- Seed data must span at least 3 different dates
- At least 2 employees must have sales in the seed data
- All three payment methods must appear in seed data

**Expected Output:** Every report endpoint returns meaningful data when hit against the seeded DB — no zero-result responses during development.

**Guiding questions for ENJ:**
1. The yearly report needs a `monthly_breakdown` — what does your seed data need to look like to test this properly, and what's the minimum number of sales across different months you need?
2. `profit_at_sale` is snapshotted — if you change a product's cost price after seeding sales, does that affect the report? Why or why not?

---

## 👤 Covenant — Report Endpoints + Aggregation

### Execution Checklist
- [ ] `backend/routes/reports.py`: Blueprint with routes — `GET /reports/daily`, `GET /reports/monthly`, `GET /reports/yearly`, `GET /reports/employee/{id}`
- [ ] `backend/controllers/reports_controller.py`: request/response for all four routes — parse query params, pass to service
- [ ] `backend/services/reports_service.py`:
  - `get_daily_report(date, session)` — aggregates sales for a single day
  - `get_monthly_report(month, year, session)` — aggregates sales for a month
  - `get_yearly_report(year, session)` — aggregates sales for a year with monthly breakdown
  - `get_employee_report(user_id, from_date, to_date, session)` — aggregates by employee and date range
- [ ] All routes protected with `@require_role('admin', 'manager')`
- [ ] `backend/app.py`: register reports blueprint
- [ ] Query params validated and defaulted in controller — never trusted raw

### Socratic Task Spec
**Objective:** Build four report endpoints that aggregate live data from the DB — using SQLAlchemy queries, not Python loops over full table fetches.

**Constraints:**
- Aggregation happens in SQL — use SQLAlchemy `func.sum()`, `func.count()`, `group_by()` — never fetch all rows and sum in Python
- Services accept session as parameter — never open their own
- Only `completed` and `edited` sales count — filter by status in every query
- `profit_at_sale` from `Sale` table — never recalculate from current product prices
- Date filtering uses `Sale.created_at` — server timezone only
- `top_products` requires joining `SaleItem` and `Product` tables — plan the join before writing

**Required Documentation:**
- SQLAlchemy 2.0 — `func`, `group_by`, `order_by`
- SQLAlchemy 2.0 — joins
- Python `datetime` — date range construction

**Expected Output:** `GET /reports/daily` returns correct totals matching the seeded sales for today. `GET /reports/employee/{id}` returns only that employee's sales in the date range. Changing the `?date=` param changes the result correctly.

**Guiding questions for Covenant:**
1. `top_products` requires summing `quantity` across all `SaleItem` rows for a product in the period, then ordering by that sum descending and taking the top 5 — write the SQLAlchemy query in pseudocode before you write real code. What tables do you need and what do you group by?
2. `employee_performance` should include employees with zero sales in the period — a standard join would exclude them. What type of join do you need, and how do you express that in SQLAlchemy?

---

## 👤 Goodness — Reports UI

### Execution Checklist

- [ ] `frontend/pages/reports.html`: reports page — hidden from employees via role check
- [ ] Daily report view — total sales, total profit, transaction count, payment breakdown
- [ ] Monthly report view — same summary fields, tabbed or toggled from daily
- [ ] Yearly report view — summary + monthly breakdown table
- [ ] Employee performance table — name, transaction count, total sales per employee
- [ ] Date/month/year picker — defaults to current period, allows navigation to previous periods
- [ ] Simple bar chart for daily sales trend (last 7 days) — vanilla JS canvas or inline SVG, no charting library
- [ ] Reports page redirects to login if not authenticated
- [ ] Reports page shows `403` message if role is employee

### Socratic Task Spec
**Objective:** Build the reports page with period navigation and a simple bar chart — fetching live data from Covenant's endpoints on every period change.

**Constraints:**
- Vanilla JS only — no charting library
- Role check on page load — redirect or show `403` message if employee
- Every period change triggers a fresh fetch — no local caching of report data
- Bar chart uses canvas or inline SVG — built from scratch

**Required Documentation:**
- `FRONTEND_SPEC.md` §8
- MDN: Canvas API or SVG basics
- MDN: fetch API

**Expected Output:** Reports page loads daily report for today on arrival. Changing the date picker fetches and renders the correct period. Employee performance table shows all employees. Bar chart renders correctly from the last 7 days of daily report data.

**Guiding questions for Goodness:**
1. The bar chart needs 7 data points — one `GET /reports/daily` call per day. How do you fire 7 fetch calls efficiently and wait for all of them to complete before rendering the chart?
2. The reports page must be completely hidden from employees — you check the role on page load. What happens if an employee manually navigates to `reports.html` directly in the browser? Where exactly must the role check happen to prevent this?

---

## ✅ Definition of Done — Phase 5 (whole team)

A Phase 5 feature is **only** done if:
- [ ] `GET /reports/daily` returns correct totals for today
- [ ] `GET /reports/daily?date=YYYY-MM-DD` returns correct totals for that date
- [ ] `GET /reports/monthly` returns correct totals for current month
- [ ] `GET /reports/yearly` returns correct totals and monthly breakdown
- [ ] `GET /reports/employee/{id}` returns correct totals for that employee
- [ ] Cancelled sales are excluded from all reports
- [ ] Employee role gets `403` on all report endpoints
- [ ] Reports page hidden from employees on the frontend
- [ ] Date picker changes fetch and re-render correctly
- [ ] Employee performance table shows all employees including zero-sale employees
- [ ] Bar chart renders from live data
- [ ] Profit figures use snapshotted `profit_at_sale` — not recalculated

**Out of scope this phase:** sync engine, conflict resolution, deployment.

---

## 🗓️ Day-by-Day

| Day | ENJ | Covenant | Goodness |
|---|---|---|---|
| 1 | Extend seed data — multiple dates, employees, payment methods | `reports.py` Blueprint, route stubs | `reports.html` shell, period toggle UI |
| 2 | Verify seed data covers all report scenarios | `get_daily_report()` + `get_monthly_report()` | Daily report view wired to endpoint |
| 3 | Review Covenant's profit queries | **Ship all report endpoints** (unblocks Goodness) | Monthly + yearly views, date picker |
| 4 | Buffer / help unblock | `get_employee_report()`, register blueprint | Employee performance table |
| 5 | Buffer | Buffer | Bar chart (last 7 days), role check + `403` state |

---

## 🚨 Non-negotiable team rules
1. All contracts above are locked
2. Aggregation in SQL — never fetch all rows and sum in Python
3. Only `completed` and `edited` sales in reports — always filter by status
4. `profit_at_sale` is never recalculated — always read from the `Sale` table
5. Services accept session as parameter — never open their own
6. Log what shipped each day in `CHANGELOG.md`
7. Blockers stated explicitly
8. No sync, conflict resolution, or deployment work this phase