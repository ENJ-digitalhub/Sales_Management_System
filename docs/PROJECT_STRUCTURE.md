# 🧱 PROJECT_STRUCTURE.md

## 1. 📂 Project Structure

```
/sales-management-system
│
├── .env.example
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── database.py
│   ├── extensions.py
│   ├── init_db.py
│   ├── controllers/
│   │   ├── _init_.py
│   │   └── sales_controller.py
│   ├── models/
│   │   ├── _init_.py
│   │   └── models.py
│   ├── routes/
│   │   ├── _init_.py
│   │   └── sales.py
│   ├── services/
│   │   ├── _init_.py
│   │   └── sales_service.py
│   ├── sync/
│   │   ├── __init__.py
│   │   └── queue.py
│   └── utils/
│       ├── _init_.py
│       └── validators.py
│
├── cli/
│   ├── __init__.py
│   └── cli.py
│
├── database/
│   ├── db.py
│   ├── erd.diagram.drawio
│   ├── schema.sql
│   ├── seed.sql
│   └── shop.db
│
├── docs/
│   ├── __init__.py
│   ├── API_SPEC.md
│   ├── CHANGELOG.md
│   ├── DATABASE_SCHEMA.md
│   ├── EDGE_CASE.md
│   ├── FRONTEND_SPEC.md
│   ├── QUICKSTART.md
│   ├── SYNC_ENGINE.md
│   ├── SYSTEM_DESIGN.md
│   ├── TEST_PLAN.md
│   ├── PROJECT_STRUCTURE.md
│   └── plan/
│
├── frontend/
│   ├── __init__.py
│   ├── index.html
│   ├── assets/
│   │   ├── __init__.py
│   │   └── styles.css
│   ├── components/
│   │   ├── __init__.py
│   │   └── button.js
│   ├── modules/
│   │   ├── __init__.py
│   │   └── auth.js
│   ├── pages/
│   │   ├── __init__.py
│   │   ├── dashboard.html
│   │   └── login.html
│   └── services/
│       ├── __init__.py
│       └── api.js
│
├── landing-page/
│   ├── index.html
│   ├── script.js
│   ├── style.css
│   └── img/
│
├── main.py
├── README.md
└── requirements.txt
```

> Note: generated `__pycache__` folders are not shown.

---

## 2. 📦 Backend Structure

### `/backend`

Core backend functionality lives here. It contains API wiring and application services.

#### `/controllers`

Children:

* `_init_.py`
* `sales_controller.py`

Handles request orchestration and delegates business logic to services.

#### `/models`

Children:

* `_init_.py`
* `models.py`

Defines data models and database interaction logic.

#### `/routes`

Children:

* `_init_.py`
* `sales.py`

Defines API endpoints and request paths.

#### `/services`

Children:

* `_init_.py`
* `sales_service.py`

Contains business logic such as sales processing, inventory updates, and reporting.

#### `/sync`

Children:

* `__init__.py`
* `queue.py`

Handles synchronization logic and background queue processing.

#### `/utils`

Children:

* `_init_.py`
* `validators.py`

Shared helper utilities, validators, and formatting logic.

#### `app.py`

Initializes the backend app, middleware, and route registration.

#### `config.py`

Loads environment configuration and application settings.

#### `database.py`

Encapsulates database connection setup and helpers.

#### `extensions.py`

Registers Flask extensions and shared application resources.

#### `init_db.py`

Provides database initialization and seeding helpers.

---

## 3. 🎨 Frontend Structure

### `/frontend`

Implements the main UI and client-side application logic.

#### `/assets`

Children:

* `__init__.py`
* `styles.css`

Contains static assets such as stylesheets and images used by the frontend.

#### `/components`

Children:

* `__init__.py`
* `button.js`

Contains reusable UI components and widgets.

#### `/modules`

Children:

* `__init__.py`
* `auth.js`

Contains feature-specific JavaScript logic.

#### `/pages`

Children:

* `__init__.py`
* `dashboard.html`
* `login.html`

Contains page templates for the app views.

#### `/services`

Children:

* `__init__.py`
* `api.js`

Manages API calls between the frontend and backend.

#### `index.html`

The main frontend entry point.

---

## 4. 🌐 Landing Page

### `/landing-page`

Contains a separate static marketing or landing page.

#### Files

* `index.html`
* `script.js`
* `style.css`

#### `/img`

Contains the Inmage asset we need.

---

## 5. 🗄️ Database Structure

### `/database`

Children:

* `db.py`
* `erd.diagram.drawio`
* `schema.sql`
* `seed.sql`
* `shop.db`

Manages the local database schema, seed data, and development database file.

---

## 6. 📚 Documentation

### `/docs`

Contains project documentation and planning artifacts.

#### Files

* `__init__.py`
* `API_SPEC.md`
* `CHANGELOG.md`
* `DATABASE_SCHEMA.md`
* `EDGE_CASE.md`
* `FRONTEND_SPEC.md`
* `QUICKSTART.md`
* `SYNC_ENGINE.md`
* `SYSTEM_DESIGN.md`
* `TEST_PLAN.md`
* `PROJECT_STRUCTURE.md`

#### `/plan`

Contains the plans to build the project.

---

## 7. ⚙️ CLI Tools

### `/cli`

Children:

* `__init__.py`
* `cli.py`

Contains developer CLI utilities.

---

## 8. 🚀 Root Files

Children:

* `main.py`
* `README.md`
* `requirements.txt`

---

## 🧠 Final Note

This structure enforces:

* separation of concerns
* scalability
* maintainability

Each folder now has the real children listed for easy navigation.

No logic should exist outside its designated layer.
