# Sales Management System Setup Guide

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env

Open `.env` and set:

```env
APP_DEFAULT_USERNAME=admin
APP_DEFAULT_PASSWORD=your-secure-password
APP_DEFAULT_ROLE=admin
```

**These three values control the account that is automatically created the first time the app runs.** You don't need to run any seed script — as soon as the backend starts (`python main.py`, `python start_server.py`, or the packaged `.exe`), it checks whether a user with `APP_DEFAULT_USERNAME` already exists in the database, and if not, creates it with the given password (hashed with bcrypt) and role.

This is idempotent: if you restart the app, or if that user already exists, nothing happens — no duplicate accounts are created.

To hand this system to a **new** owner/store, just change `APP_DEFAULT_USERNAME` / `APP_DEFAULT_PASSWORD` in `.env` before the very first run against a fresh database. If a database already exists with a default user in it, changing `.env` afterwards will **not** retroactively change that user's credentials — it only creates the account if it's
missing. 
```

### 3. Initialize Database
```bash
python cli/cli.py setup
python cli/cli.py seed
```

### 4. Run the Application
```bash
python main.py
```

The application will be available at `http://localhost:5000`

## Project Structure

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed breakdown of the project organization.

## Development

### CLI Commands
- `python cli/cli.py setup` - Initialize database
- `python cli/cli.py seed` - Seed with demo data
- `python cli/cli.py reset` - Reset database

### Testing
```bash
pytest
```

### Code Quality
```bash
black .
flake8 .
pylint backend/
```

## Documentation

- [System Design](SYSTEM_DESIGN.md)
- [Database Schema](DATABASE_SCHEMA.md)
- [API Specification](API_SPEC.md)
- [Sync Engine](SYNC_ENGINE.md)
- [Edge Cases](EDGE_CASE.md)
- [Test Plan](TEST_PLAN.md)
