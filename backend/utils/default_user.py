# backend/utils/default_user.py
"""
Ensures a default (first-run) user exists, sourced entirely from .env.

This is intentionally simple and local-only (MVP scope):
- No remote auth, no multi-user sync.
- Runs once per app start; does nothing if the user already exists.
- If APP_DEFAULT_USERNAME / APP_DEFAULT_PASSWORD aren't set, it's a no-op
  (so existing installs / CI without these vars are unaffected).
"""

import os
from sqlalchemy.orm import Session

from backend.models.models import User
from backend.utils.security import Security

VALID_ROLES = ("admin", "manager", "employee")


def ensure_default_user(session: Session):
    """
    Idempotently creates the default user from environment variables.

    Reads:
        APP_DEFAULT_USERNAME
        APP_DEFAULT_PASSWORD
        APP_DEFAULT_ROLE (defaults to "admin" if missing/invalid)

    Returns the existing or newly-created User, or None if no default
    credentials were configured.
    """
    username = os.getenv("APP_DEFAULT_USERNAME")
    password = os.getenv("APP_DEFAULT_PASSWORD")
    role = os.getenv("APP_DEFAULT_ROLE", "admin")

    if not username or not password:
        # Nothing configured in .env — skip silently. This keeps the
        # feature opt-in and safe for existing databases/installs.
        return None

    if role not in VALID_ROLES:
        print(f"[bootstrap] Invalid APP_DEFAULT_ROLE '{role}', falling back to 'admin'.")
        role = "admin"

    existing = session.query(User).filter_by(username=username).first()
    if existing:
        # Already provisioned — do nothing (idempotent).
        return existing

    user = User(
        name=username,
        username=username,
        password_hash=Security.hash_password(password),
        role=role,
    )
    session.add(user)
    session.commit()
    print(f"[bootstrap] Default user '{username}' created with role '{role}'.")
    return user