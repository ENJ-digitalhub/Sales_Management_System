
import jwt
from datetime import datetime, timedelta, timezone
from backend.config import Config

class JWTUtils:
    @staticmethod
    def generate_token(user_id: str, role: str, device_id: str) -> str:
        """Generates a JWT token with a 24-hour expiry."""
        payload = {
            "sub": user_id,
            "role": role,
            "device_id": device_id,
            "exp": datetime.now(timezone.utc) + timedelta(hours=24)
        }
        return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm="HS256")

    @staticmethod
    def decode_token(token: str) -> dict:
        """Decodes a JWT token and returns its payload."""
        try:
            return jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return {"error": "Token expired"}
        except jwt.InvalidTokenError:
            return {"error": "Invalid token"}


# Backwards-compatible top-level functions
def generate_token(user_id: str, role: str, device_id: str) -> str:
    return JWTUtils.generate_token(user_id, role, device_id)


def decode_token(token: str) -> dict:
    return JWTUtils.decode_token(token)
