import jwt
from datetime import datetime, timedelta, timezone
from backend.config import Config


def generate_token(user_id: str, role: str, device_id: str) -> str:
    """Generates a JWT with the locked payload shape: sub, role, device_id, exp."""
    payload = {
        "sub": str(user_id),
        "role": role,
        "device_id": str(device_id),
        "exp": datetime.now(timezone.utc) + timedelta(hours=24)
    }
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> dict:
    """Decodes and validates a JWT. Raises ValueError on any failure."""
    try:
        return jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise ValueError("Token missing or invalid")