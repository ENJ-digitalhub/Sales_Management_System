🚀 Phase 7 — Launch + Deployment + Team Handover Week

Sales Management System (Offline-First POS)

Stack confirmed: Flask (latest, app factory pattern) · Raw SQLAlchemy 2.0 (no Flask-SQLAlchemy extension) · SQLite · Vanilla JS frontend · JWT · Offline Queue

Team:

Person| Owns
Obinna| "frontend/", deployment UI verification, user acceptance
Covenant| "backend/", production configuration, API readiness
ENJ| "database/", deployment data setup, operational recovery

---

🎯 Phase 7 Goal (one sentence)

By end of week: the system is packaged, documented, verified in a production-like environment, and handed over with deployment, recovery, and operational procedures.

⚠️ Critical dependency

Deployment cannot begin until the team freezes features and signs off on Phase 6. Obinna cannot complete acceptance testing until Covenant freezes API contracts. Covenant cannot finalize deployment until ENJ confirms backup and restore procedures.

No feature development this phase.

---

👤 ENJ — Database Release + Operations

Execution Checklist

- [ ] Freeze schema
- [ ] Validate migrations
- [ ] Create production DB initialization process
- [ ] Produce backup package
- [ ] Produce restore package
- [ ] Verify seeded production setup
- [ ] Create operational runbook
- [ ] Add recovery checklist

Create:

database/
├── backups/
├── recovery/
├── release/

Deliver:

- [ ] Deployment SQL
- [ ] Backup instructions
- [ ] Recovery instructions

Socratic Task Spec

Objective: Deliver a database that can be deployed, recovered, and maintained safely.

Constraints:

- No schema changes after freeze
- Recovery must be tested
- Release setup must be reproducible

Required Documentation:

- SQLite deployment guidance
- Operational readiness basics
- Backup verification practices

Expected Output:

Running:

python cli/cli.py setup

creates a production-ready database.

Guiding questions for ENJ (don't answer yet — sit with these):

1. If the deployment machine dies tomorrow, how long until recovery?
2. What information must exist for someone new to operate the system?

---

👤 Covenant — Backend Release + Production Configuration

Execution Checklist

Build:

- [ ] Production config
- [ ] Environment separation
- [ ] Secret handling
- [ ] Error logging
- [ ] Health verification
- [ ] Release checklist
- [ ] API documentation
- [ ] Startup verification

Create:

backend/
├── config/
├── docs/
├── release/

Implement:

- [ ] Production startup
- [ ] Config validation
- [ ] Environment loading
- [ ] API readiness checks
- [ ] Endpoint verification

Validate:

- [ ] Auth
- [ ] Products
- [ ] Sales
- [ ] Sync
- [ ] Reports

Socratic Task Spec

Objective: Deliver a backend that starts reliably and behaves consistently after deployment.

Constraints:

- No hardcoded configuration
- No debug configuration in release
- Startup must fail clearly if misconfigured

Required Documentation:

- Flask deployment concepts
- Environment configuration
- Logging fundamentals

Expected Output:

Running:

python main.py

starts successfully under release configuration.

Guiding questions for Covenant (don't answer yet — sit with these):

1. If deployment succeeds but requests fail, what would reveal that fastest?
2. Which configuration mistakes should block startup?

---

👤 Obinna — Frontend Release + Acceptance

Execution Checklist

Build:

- [ ] Production build verification
- [ ] Final responsive pass
- [ ] Browser compatibility check
- [ ] Navigation verification
- [ ] Error UX review
- [ ] Acceptance testing
- [ ] Release screenshots
- [ ] User walkthrough

Create:

frontend/
├── release/
├── docs/
├── screenshots/

Validate:

- [ ] Login
- [ ] Products
- [ ] Sales
- [ ] Sync
- [ ] Reports
- [ ] Offline behavior

Socratic Task Spec

Objective: Ensure users can operate the system confidently after release.

Constraints:

- No visual redesign
- No new workflows
- Validation uses real backend

Required Documentation:

- Browser testing
- Accessibility checks
- Acceptance testing basics

Expected Output:

Users can complete the entire flow:

Login
→ Products
→ Sale
→ Offline
→ Sync
→ Reports
→ Logout

without guidance.

Guiding questions for Obinna (don't answer yet — sit with these):

1. What makes a release feel unfinished even when features work?
2. Which user actions are least tested but most risky?

---

✅ Definition of Done — Phase 7 (whole team)

A Phase 7 feature is only done if:

- [ ] Application starts cleanly
- [ ] Full workflow completes
- [ ] Backups restore correctly
- [ ] APIs remain stable
- [ ] Frontend passes acceptance testing
- [ ] Documentation exists
- [ ] Team handover completed

Out of scope this week (do not touch):
new features, refactors, redesigns, architecture changes

---

🗓️ Suggested Day-by-Day

Day| ENJ| Covenant| Obinna
1| Schema freeze| Release config| Acceptance prep
2| Backup package| API verification| Browser testing
3| Recovery testing| Logging review| Flow testing
4| Deployment prep| Startup validation| Final fixes
5| Handover| Handover| Handover

---

🚨 Non-negotiable team rules (carried over)

1. Nothing new ships after release freeze.
2. Every deployment step must be documented.
3. Recovery is tested, not assumed.
4. Release only happens after full-team signoff.