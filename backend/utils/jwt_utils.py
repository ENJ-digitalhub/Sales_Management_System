import jwt
from datetime import datetime, timezone, timedelta
from backend.config import Config


def generate_token(user_id, role, device_id):
    """Generate a JWT token with 24-hour expiry."""
    payload = {
        "sub": str(user_id),
        "role": role,
        "device_id": device_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm="HS256")


def decode_token(token):
    """Decode and validate a JWT token. Returns the payload dict."""
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")
