# 🚀 Phase 9 — Deployment
## Sales Management System (Offline-First POS)

**Stack:** Flask · SQLite · Vanilla JS · Python installer script

**Team:**
| Person | Owns |
|---|---|
| **Goodness** | Frontend packaging — static file bundling, mobile browser testing, offline mode verification |
| **Covenant** | Backend packaging — production config, server hardening, startup script |
| **ENJ** | Installer script — one-command setup, PC detection, store owner documentation |

---

## 🎯 Phase 9 Goal (one sentence)

By end of phase: a non-technical store owner can set up RetailOS on their store PC by following a single document, running one command, and accessing the system from any phone on their shop Wi-Fi — with no developer present.

### ⚠️ Critical dependencies
- Phase 8 must be fully complete with zero test failures before deployment begins
- Covenant's production config is needed before ENJ writes the installer — **Covenant ships production config by Day 2**
- ENJ's installer is needed before store owner documentation is written — **ENJ ships installer by Day 3**
- All three must coordinate on the exact setup steps before any documentation is written

---

## 📋 Deployment Architecture

```

Store PC (Windows / Linux)
    ↓
Python backend (Flask — production WSGI server)
    ↓
SQLite database (local file — shop.db)
    ↓
Local WiFi network
    ↓
Staff Android phones (browser — no app install required)
```

---

## 📋 Deployment Rules (non-negotiable)

- System must work with **zero internet** after initial install
- Initial install may use internet to download Python dependencies — one time only
- Staff phones access the system via browser — no app store, no APK install
- Store owner accesses admin dashboard from PC browser or phone browser
- System must survive PC restart — server starts automatically on boot
- SQLite database file must be backed up automatically — daily, to a separate folder
- No cloud dependency in production — ever
- Production server is **Waitress** (Windows-compatible WSGI) — not Flask dev server
- Default port: `5000` — configurable in `.env`
- PC firewall must allow inbound connections on port `5000` from local network

---

## 👤 ENJ — Installer Script + Store Owner Documentation

### Execution Checklist

#### Installer Script — `installer/setup.py`
- [ ] Detect operating system — Windows or Linux
- [ ] Check Python version — require 3.10+, exit with clear message if not met
- [ ] Install dependencies — `pip install -r requirements.txt` programmatically
- [ ] Run `python cli/cli.py setup` — create all DB tables
- [ ] Run `python cli/cli.py seed` — optional, prompt user
- [ ] Generate `.env` file from `.env.example` — prompt for `SECRET_KEY`, auto-generate if skipped
- [ ] Detect local IP address — display it clearly so owner knows what URL to give staff
- [ ] Create startup script — `start.bat` (Windows) or `start.sh` (Linux) that runs the production server
- [ ] Register startup script with OS — startup on boot (Windows: Task Scheduler, Linux: systemd)
- [ ] Run daily backup script — `installer/backup.py` backs up `shop.db` to `backups/shop_YYYY-MM-DD.db`
- [ ] Schedule daily backup — Windows Task Scheduler or Linux cron
- [ ] Print success message with: local IP, port, admin login credentials from seed

#### Store Owner Documentation — `docs/STORE_OWNER_GUIDE.md`
- [ ] Written in plain English — no technical jargon
- [ ] Step 1: What you need (PC, phones, same WiFi)
- [ ] Step 2: How to install (one command)
- [ ] Step 3: How to give staff access (share the URL)
- [ ] Step 4: How to log in (default admin credentials)
- [ ] Step 5: How to add products
- [ ] Step 6: How to add staff accounts
- [ ] Step 7: What to do if the PC restarts
- [ ] Step 8: How to find your backup files
- [ ] Troubleshooting section — common problems and plain-English fixes
- [ ] Contact section — how to reach KAVE for support

### Socratic Task Spec
**Objective:** Build a single installer script that a developer can hand to a store owner — it sets up the entire system, detects the local IP, and tells the owner exactly what URL to share with staff.

**Constraints:**
- Installer must work on Windows — primary target
- Linux support is a bonus — not required for beta
- All prompts use plain English — no technical terms
- IP detection uses `socket` — `socket.gethostbyname(socket.gethostname())`
- `SECRET_KEY` auto-generated using `secrets.token_hex(32)` if owner skips it
- Installer is idempotent — safe to run twice without breaking existing data
- Backup script never deletes old backups — only adds new ones

**Required Documentation:**
- Python `subprocess` docs — running shell commands
- Python `socket` docs — IP detection
- Python `secrets` docs — key generation
- Windows Task Scheduler — `schtasks` command line
- Python `shutil` docs — file copying for backup

**Expected Output:** Running `python installer/setup.py` on a fresh Windows PC produces a working system, a `start.bat` file, a scheduled daily backup, and prints the URL staff should use to access the system.

**Guiding questions for ENJ:**
1. IP detection with `socket.gethostbyname(socket.gethostname())` sometimes returns `127.0.0.1` on some machines — what's the fallback strategy to get the real LAN IP, and how do you display it clearly to a non-technical owner?
2. The installer is idempotent — if it's run twice, what checks do you need to avoid overwriting an existing `.env` file with a new `SECRET_KEY`, which would invalidate all existing JWTs and log everyone out?

---

## 👤 Covenant — Production Config + Server Hardening

### Execution Checklist

#### Production Config — `backend/config.py`
- [ ] Add `ProductionConfig` class — separate from `DevelopmentConfig`
- [ ] `ProductionConfig`: `DEBUG = False`, `TESTING = False`
- [ ] `ProductionConfig`: `SECRET_KEY` read from `.env` — error if missing
- [ ] `ProductionConfig`: `DATABASE_URL` read from `.env`
- [ ] `ProductionConfig`: `MAX_CONTENT_LENGTH = 16 * 1024 * 1024` — 16MB request limit
- [ ] `main.py`: detect environment from `.env` `FLASK_ENV` variable — use `ProductionConfig` in production

#### Production Server — `start_server.py`
- [ ] Use **Waitress** as WSGI server — `from waitress import serve`
- [ ] Read host and port from `.env`
- [ ] Bind to `0.0.0.0` — accepts connections from all devices on local network
- [ ] Log startup message — port, local IP, environment
- [ ] `requirements.txt`: add `waitress`

#### Security Hardening
- [ ] Set `SESSION_COOKIE_SECURE = False` in production config — HTTP only (no HTTPS on LAN)
- [ ] Set `SESSION_COOKIE_HTTPONLY = True`
- [ ] Add rate limiting on `POST /auth/login` — max 10 attempts per minute per IP
- [ ] Return generic error messages on auth failure — never reveal whether username or password was wrong
- [ ] Add `X-Content-Type-Options: nosniff` response header
- [ ] Add `X-Frame-Options: DENY` response header
- [ ] Ensure no debug stack traces leak in production responses

#### Error Handling
- [ ] Global `404` handler — returns JSON `{"success": false, "message": "Not found"}`
- [ ] Global `500` handler — returns JSON `{"success": false, "message": "Server error"}` — never leaks traceback
- [ ] Global `401` handler — returns JSON `{"success": false, "message": "Unauthorised"}`
- [ ] Global `403` handler — returns JSON `{"success": false, "message": "Forbidden"}`

### Socratic Task Spec
**Objective:** Harden the Flask backend for production — production config, Waitress WSGI server, security headers, rate limiting, and clean error handling with no information leakage.

**Constraints:**
- Waitress binds to `0.0.0.0` — required for LAN access from staff phones
- `DEBUG = False` in production — no exceptions
- Auth failure messages are always generic — never say "wrong password" vs "unknown user"
- All error handlers return JSON — never HTML
- Rate limiting uses `flask-limiter` — add to `requirements.txt`

**Required Documentation:**
- Waitress docs — `serve()` configuration
- flask-limiter docs
- Flask error handler docs — `@app.errorhandler`
- Flask security headers

**Expected Output:** Running `python start_server.py` starts Waitress on port 5000, bound to all interfaces. A staff phone on the same WiFi can reach the system via the PC's IP. Auth failure always returns the same generic message regardless of whether the username or password was wrong.

**Guiding questions for Covenant:**
1. Waitress binds to `0.0.0.0` — what does this actually mean for LAN access, and why would binding to `127.0.0.1` break staff phone access even if the server is running?
2. Rate limiting on `POST /auth/login` — what's the risk of rate limiting by IP on a LAN where all staff phones may share the same router NAT IP, and how do you mitigate it?

---

## 👤 Goodness — Frontend Packaging + Mobile Testing

### Execution Checklist

#### Frontend Packaging
- [ ] Verify all JS modules load correctly when served from Flask's static file handler
- [ ] Verify all pages work with no `localhost` hardcoded — all API calls use relative URLs or configurable base URL
- [ ] Verify offline banner shows correctly on mobile browser
- [ ] Verify sync triggers correctly on mobile browser reconnect
- [ ] Add `<meta name="theme-color" content="#0B0D10">` — matches dark UI on mobile browser chrome
- [ ] Add `<meta name="mobile-web-app-capable" content="yes">` — allows adding to home screen
- [ ] Add `<meta name="apple-mobile-web-app-capable" content="yes">` — iOS home screen support
- [ ] Verify all pages redirect to login correctly when token is missing

#### Mobile Browser Testing — Android
- [ ] Test on at least 2 Android phones — different screen sizes
- [ ] Sales flow — complete a sale end to end on mobile
- [ ] Offline queue — queue a sale, reconnect, verify sync
- [ ] Inventory — add a product on mobile
- [ ] Reports — view daily report on mobile
- [ ] Conflict dashboard — approve a conflict on mobile

#### Cross-Device Testing
- [ ] Admin logs in on PC browser — full dashboard accessible
- [ ] Employee logs in on Android phone — sales dashboard only
- [ ] Both active simultaneously — sale on phone appears in PC report

### Socratic Task Spec
**Objective:** Verify the frontend works correctly when served from the production Flask server and accessed from real Android phones on a local WiFi network — not localhost.

**Constraints:**
- All tests on real devices — not browser DevTools mobile emulation
- All API calls use relative URLs — never hardcoded `localhost:5000`
- Test on the actual LAN IP — e.g. `http://192.168.1.10:5000`
- Document every mobile test with: device, browser version, test case, result

**Required Documentation:**
- `FRONTEND_SPEC.md` — full reference
- MDN: Web App Manifest — for home screen icon (optional bonus)

**Expected Output:** Two Android phones can access the system via the store PC's LAN IP, complete sales, queue offline sales, and sync — all without any developer intervention.

**Guiding questions for Goodness:**
1. All API calls must use relative URLs — what breaks if you hardcode `localhost:5000` in `api.js`, and how do you structure the base URL so it works both on `localhost` during development and on `192.168.1.x` in production?
2. Adding the app to the Android home screen gives a near-native feel — what's the minimum you need to add to `index.html` to enable this, and what does the user experience look like when they open it from the home screen?

---

## 📁 New Files This Phase

```

/installer
├── setup.py          ← ENJ
└── backup.py         ← ENJ

/docs
└── STORE_OWNER_GUIDE.md  ← ENJ

start_server.py           ← Covenant
```

---

## ✅ Definition of Done — Phase 9 (whole team)

A Phase 9 feature is **only** done if:
- [ ] `python installer/setup.py` runs on a fresh Windows PC without errors
- [ ] `python start_server.py` starts Waitress on port 5000
- [ ] Staff phone on same WiFi can reach system via LAN IP
- [ ] Admin can log in from PC browser
- [ ] Employee can complete a sale from Android phone
- [ ] Offline sale queues and syncs correctly on mobile
- [ ] PC restart — server restarts automatically
- [ ] Daily backup runs and creates `backups/shop_YYYY-MM-DD.db`
- [ ] `DEBUG = False` in production — no stack traces in responses
- [ ] Auth failure returns generic message — no information leakage
- [ ] `404`, `500`, `401`, `403` all return clean JSON
- [ ] Rate limiting active on login endpoint
- [ ] `STORE_OWNER_GUIDE.md` complete — readable by non-technical owner
- [ ] Two Android phones tested — all critical flows pass
- [ ] Cross-device test — phone sale appears in PC report

**The system is beta-ready when every item above is checked.**

---

## 🗓️ Day-by-Day

| Day | ENJ | Covenant | Goodness |
|---|---|---|---|
| 1 | `installer/setup.py` skeleton, OS detection, dependency install | `ProductionConfig`, Waitress setup in `start_server.py` | Verify relative URLs across all JS modules |
| 2 | IP detection, `.env` generation, startup script | Security headers, rate limiting, global error handlers | Mobile meta tags, verify offline banner on Android |
| 3 | **Ship installer** — DB setup, boot registration, backup schedule | **Ship `start_server.py`** — production-ready | Mobile testing — sales flow, offline queue on real device |
| 4 | `backup.py`, begin `STORE_OWNER_GUIDE.md` | Fix any production bugs found by mobile testing | Cross-device testing — phone + PC simultaneously |
| 5 | Complete `STORE_OWNER_GUIDE.md`, buffer | Buffer / fix remaining issues | Compile mobile test report, buffer |

---

## 🚨 Non-negotiable team rules
1. Phase 8 must be fully passing before any deployment work begins
2. `DEBUG = False` in production — no exceptions
3. Waitress only — never Flask dev server in production
4. All API calls use relative URLs — no hardcoded localhost
5. Installer is idempotent — safe to run twice
6. `STORE_OWNER_GUIDE.md` uses plain English — no jargon
7. Test on real Android devices — not emulators
8. Log what shipped each day in `CHANGELOG.md`
9. Blockers stated explicitly