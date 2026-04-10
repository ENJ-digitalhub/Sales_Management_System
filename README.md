# Sales Management System

A Flask-based web application for managing store operations including sales tracking, inventory management, and employee administration.

## Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL (for production) or SQLite (included for development)

### Installation

1. **Clone and setup:**
```bash
cd Sales_Management_System
pip install -r requirements.txt
```

2. **Environment Configuration:**

Create a`.env` file in the project root. For development (SQLite), you can leave it empty:
```bash
# .env (development - uses SQLite)
FLASK_SECRET_KEY=your_secret_key_here
MAIN_ADMIN_USERNAME=admin
MAIN_ADMIN_PASSWORD=password
```

For production (PostgreSQL), add:
```bash
# .env (production - uses PostgreSQL)
DATABASE_URL=postgresql://username:password@hostname:5432/dbname
ENVIRONMENT=production
FLASK_SECRET_KEY=your_secret_key_here
```

3. **Run the application:**

**Development (SQLite):**
```bash
python app.py
```

**Production (with Gunicorn):**
```bash
gunicorn --bind 0.0.0.0:$PORT --timeout 300 app:app
```

Visit `http://localhost:10000` (or your $PORT)

---

## Project Structure

```
sales_management/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── Procfile              # Deployment configuration (Render/Railway)
├── runtime.txt           # Python version specification
├── config/               # Configuration files
├── data/                 # SQLite database (development only)
├── src/                  # Core application modules
│   ├── __init__.py
│   ├── database.py       # Database abstraction layer (PostgreSQL/SQLite)
│   ├── user.py           # User authentication & management
│   ├── commands.py       # Command-line utilities
├── static/               # Frontend assets
│   ├── css/              # Stylesheets (base, dashboard, forms, etc.)
│   ├── js/               # JavaScript files (navigation, forms, charts)
│   ├── img/              # Images and icons
│   └── uploads/          # User uploads (products, profiles, transactions)
└── templates/            # HTML templates (Jinja2)
    ├── base.html         # Base template layout
    ├── index.html        # Dashboard/home page
    ├── admin_dashboard.html
    ├── employee_dashboard.html
    └── ...
```

---

## Database

### Automatic Schema Setup

The database schema is created automatically on first startup. No manual migrations needed.

### Tables

1. **users** - Employee and admin accounts
2. **product** - Inventory items
3. **transactions** - Sales and purchase records

### Database Engine Selection

```
Has DATABASE_URL env variable?
  YES → PostgreSQL (Production)
  NO  → SQLite: database.db (Development)
```

### Example Queries

```python
# Using database.py
from src.database import Database

db = Database()

# Insert record
db.run(
    "INSERT INTO users (first_name, last_name, username, password) VALUES (?, ?, ?, ?)",
    ("John", "Doe", "john_doe", "hashed_password")
)

# Query records (returns list of dictionaries)
users = db.query("SELECT * FROM users WHERE role = ?", ("admin",))
for user in users:
    print(user["username"])

# Check if user exists
exists = db.user_exists("john_doe")
```

---

## Features

### Current
- User authentication (login/register)
- Admin dashboard for inventory monitoring
- Employee dashboard for recording daily operations
- Product management (add/view products)
- Transaction recording (sales/purchases)
- User profiles and settings

### Database Engines
- **SQLite** - Development (automatic, no setup needed)
- **PostgreSQL** - Production (Neon, AWS, or self-hosted)

---

## Code Standards

### Naming Conventions
- **Variables/Functions:** `snake_case` - e.g., `user_count`, `get_user_by_id`
- **Classes:** `PascalCase` - e.g., `Database`, `User`
- **Constants:** `UPPER_SNAKE_CASE` - e.g., `MAX_RETRIES`

### Code Style
- Follow PEP 8 Python style guide
- Use type hints for function parameters and returns
- Add docstrings to all functions and classes
- Comment "why" not "what":
  ```python
  # Good: Explains purpose
  # Reset counter to ensure accurate daily totals on new day
  daily_counter = 0
  
  # Bad: States the obvious
  # Set daily_counter to 0
  daily_counter = 0
  ```

### Docstring Template
```python
def get_user_by_username(username: str) -> Optional[Dict]:
    """
    Find a user account by username.
    
    Case-insensitive search for username.
    
    Example:
        user = get_user_by_username("john_doe")
        if user:
            print(user["first_name"])
    
    Args:
        username (str): The username to search for
        
    Returns:
        Dict: User data if found, None otherwise
    """
    pass
```

---

## Deployment

### Render
1. Push code to GitHub
2. Connect GitHub repo to Render
3. Set environment variables:
   - `DATABASE_URL` - PostgreSQL connection string
   - `ENVIRONMENT` - Set to "production"
   - `FLASK_SECRET_KEY` - Generate secure key
4. Deploy (uses Procfile automatically)

### Environment Variables Required
```
DATABASE_URL=postgresql://...  # Production DB
ENVIRONMENT=production          # Enable production mode (optional)
FLASK_SECRET_KEY=...           # Flask session secret
MAIN_ADMIN_USERNAME=...        # Default admin username
MAIN_ADMIN_PASSWORD=...        # Default admin password
```

---

## Troubleshooting

### 502 Bad Gateway
- Check `DATABASE_URL` is set correctly
- Verify database connection: `psycopg connection timeout`
- Increase gunicorn timeout: Already set to 300s in Procfile
- Check app is binding to `0.0.0.0:$PORT`

### Database Connection Fails
- PostgreSQL: Verify `DATABASE_URL` format
- SQLite: Check `database.db` file permissions
- Password issues: Ensure special characters are URL-encoded

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

---

## Development Workflow

### Adding New Database Tables
1. Add SQL to `src/database.py` in `create_tables_if_not_exist()`
2. Restart app (schema auto-creates)

### Adding New Routes
1. Create route handler in `app.py`
2. Add docstring explaining purpose
3. Return appropriate response (HTML or JSON)
4. Add link in template if needed

### Testing Locally
```bash
# Run with SQLite (no DATABASE_URL needed)
python app.py

# Test registration
# Visit http://localhost:10000/signin

# Admin login (from .env)
# Username: MAIN_ADMIN_USERNAME
# Password: MAIN_ADMIN_PASSWORD
```

---

## Technology Stack
- **Backend:** Python 3.8+ + Flask
- **Database:** PostgreSQL (prod) / SQLite (dev)
- **Frontend:** HTML + CSS (Flexbox, Glassmorphism) + JavaScript
- **Authentication:** SHA256 password hashing
- **Hosting:** Render / Railway

---

## License
Private project for internal use. See LICENSE for details.

---

## Contact & Support
This is a learning project. For questions or improvement suggestions, contact the maintainer.

Last updated: April 2026

---

## Project Structure

```

shop-app/
├── app.py                # Main Flask application
├── templates/            # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── admin_dashboard.html
│   ├── employee_dashboard.html
│   ├── products.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
├── database/
│   └── db.sqlite3
└── README.md

```

---

## Workflow / Steps

1. Design wireframes for login and dashboards
2. Build the login page (UI + Flask backend)
3. Implement user authentication (admin & employee)
4. Build admin dashboard (inventory overview)
5. Build employee dashboard (daily reports & sales)
6. Connect database (products, transactions, users)
7. Add product management functionality
8. Style pages with CSS (blurred background, centered card)
9. Deploy on free hosting (Render/Railway)
10. Test with real users and improve
11. Add future features (ordering, analytics, team communication)

---

## Notes / Reminders
- Only backend routes enforce security; front-end alone cannot protect data
- Keep CSS meaningful and maintainable
- Start simple, add fancy UI effects later
- Document each step with code comments
- Use semantic CSS classes instead of too many utility classes (avoid `.red`, `.bold`, etc.)
- Focus on working functionality first, then polish design

---

## Progress Tracking
Use checkboxes to track your progress:

- [ ] Wireframes completed
- [ ] Login page built
- [ ] User authentication implemented
- [ ] Admin dashboard built
- [ ] Employee dashboard built
- [ ] Product management functional
- [ ] CSS styling complete
- [ ] Deployment done
- [ ] Future features added

