🚀 Phase 6 — Stabilization + Testing + Production Readiness Week

Sales Management System (Offline-First POS)

Stack confirmed: Flask (latest, app factory pattern) · Raw SQLAlchemy 2.0 (no Flask-SQLAlchemy extension) · SQLite · Vanilla JS frontend · JWT · Offline Queue

Team:

Person| Owns
Obinna| "frontend/", UX polish, performance, production readiness
Covenant| "backend/routes/", "controllers/", "services/", testing, hardening
ENJ| "backend/models/", "database/", migrations, backup + recovery

---

🎯 Phase 6 Goal (one sentence)

By end of week: the system becomes launch-ready — tested, recoverable, stable under failure, and safe to hand to real users.

⚠️ Critical dependency

Covenant cannot finalize API reliability until ENJ stabilizes database lifecycle and recovery strategy. Obinna cannot complete polish until Covenant freezes endpoint behavior and response contracts.

No new features this phase — only stabilization.

---

👤 ENJ — Database Reliability + Recovery

Execution Checklist

- [ ] Review all models for consistency
- [ ] Verify indexes
- [ ] Create migration process
- [ ] Add backup strategy
- [ ] Add restore strategy
- [ ] Validate schema integrity
- [ ] Add health-check query
- [ ] Create DB diagnostics CLI

Extend CLI:

- [ ] "backup"
- [ ] "restore"
- [ ] "verify"

Create:

database/
├── migrations/
├── backups/

Validation:

- [ ] Seed verification
- [ ] Foreign key validation
- [ ] Transaction validation

Socratic Task Spec

Objective: Make the database safe to recover, maintain, and trust.

Constraints:

- No destructive migration without backup
- Backups must restore successfully
- Database validation must be rerunnable

Required Documentation:

- SQLAlchemy migration concepts
- SQLite backup mechanisms
- Database integrity concepts

Expected Output:

Running:

python cli/cli.py verify

confirms DB health successfully.

Guiding questions for ENJ (don't answer yet — sit with these):

1. If the DB file becomes corrupted, what is recovery?
2. How do you prove a backup actually works?

---

👤 Covenant — Backend Testing + Hardening

Execution Checklist

Create:

tests/
├── routes/
├── controllers/
├── services/
├── integration/

Build:

- [ ] Unit tests
- [ ] Integration tests
- [ ] API tests
- [ ] Transaction tests
- [ ] Sync tests
- [ ] Validation tests
- [ ] Error handling
- [ ] Logging
- [ ] Global exception handling
- [ ] Health endpoint

Implement:

- [ ] "GET /health"
- [ ] Error middleware
- [ ] Request logging
- [ ] Service monitoring

Testing Targets:

- [ ] Auth
- [ ] Products
- [ ] Sales
- [ ] Sync
- [ ] Reports

Socratic Task Spec

Objective: Prove the backend behaves correctly before release.

Constraints:

- No manual-only testing
- Services tested independently
- Tests cannot depend on execution order

Required Documentation:

- pytest
- Flask testing
- SQLAlchemy testing
- Error handling patterns

Expected Output:

Running:

pytest

passes consistently.

Guiding questions for Covenant (don't answer yet — sit with these):

1. If a bug cannot be reproduced manually, how do you protect against regression?
2. Which failures should crash loudly versus fail gracefully?

---

👤 Obinna — Frontend Polish + Launch Readiness

Execution Checklist

Build:

- [ ] Loading improvements
- [ ] Empty states
- [ ] Responsive layout
- [ ] Error UX
- [ ] Offline messaging
- [ ] Accessibility review
- [ ] Performance review
- [ ] Browser compatibility
- [ ] Navigation cleanup

Create:

frontend/
├── assets/
├── pages/
├── components/

Validate:

- [ ] Mobile
- [ ] Desktop
- [ ] Offline
- [ ] Reconnect
- [ ] Accessibility

Socratic Task Spec

Objective: Turn working screens into usable product experiences.

Constraints:

- No new business features
- No duplicated API logic
- Frontend remains stateless where possible

Required Documentation:

- Browser DevTools
- Accessibility basics
- Performance profiling

Expected Output:

Users can:

- navigate smoothly
- recover from errors
- operate confidently

without confusion.

Guiding questions for Obinna (don't answer yet — sit with these):

1. Which UX problems are invisible during development?
2. What breaks first on slower devices?

---

✅ Definition of Done — Phase 6 (whole team)

A Phase 6 feature is only done if:

- [ ] Tests pass
- [ ] Health checks succeed
- [ ] Backups restore correctly
- [ ] Errors are recoverable
- [ ] Frontend is responsive
- [ ] No major regressions exist

Out of scope this week (do not touch):
new features, redesigns, architecture rewrites

---

🗓️ Suggested Day-by-Day

Day| ENJ| Covenant| Obinna
1| DB validation| Test setup| UX audit
2| Backup tools| Route tests| Responsive fixes
3| Restore flow| Service tests| Error states
4| Verification| Integration tests| Accessibility
5| Buffer| Final stabilization| Polish

---

🚨 Non-negotiable team rules (carried over)

1. No feature additions.
2. Every critical bug gets a test.
3. Backups are tested, not assumed.
4. Release only if the whole team signs off.