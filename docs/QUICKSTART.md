# Sales Management System Setup Guide

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
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
