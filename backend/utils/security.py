import os
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt

# Load secret key from configuration/environment variables
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-fallback-super-secret-key-change-this")
ALGORITHM = "HS256"

def hash_password(plain: str) -> str:
    """Hashes a plain text password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain: str, hashed: str) -> bool:
    """Verifies a plain text password against its hashed variant."""
    try:
        return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False

def generate_token(user_id: str, role: str) -> str:
    """Generates a JWT access token valid for 24 hours."""
    payload = {
        "user_id": str(user_id),
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    """
    Decodes and validates a JWT token.
    Returns the payload dictionary if valid, or raises an error.
    """
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        raise ValueError("Token missing or invalid")