<<<<<<< HEAD
=======

>>>>>>> a9333a422bf619f612b4742acd01eac2428da808
import jwt
from datetime import datetime, timezone, timedelta
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

<<<<<<< HEAD
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
=======
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
>>>>>>> a9333a422bf619f612b4742acd01eac2428da808
