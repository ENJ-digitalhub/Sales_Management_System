from datetime import datetime, timezone
from sqlalchemy import select
from backend.models.models import User
from backend.utils.security import verify_password
from backend.utils.jwt_utils import generate_token, decode_token


class AuthenticationError(ValueError):
    """Raised when authentication fails (bad credentials, invalid token, etc.)."""
    pass


class AuthService:

    @staticmethod
    def _now():
        """Get current UTC time. Use timezone-aware datetime."""
        return datetime.now(timezone.utc)

    @staticmethod
    def login(session, username: str, password: str, device_id: str) -> dict:
        if not username or not password or not device_id:
            raise AuthenticationError("Invalid username or password")

        # Fetch user (Note: using integer check for is_active matching ENJ's model default=1)
        user = session.execute(
            select(User).where(
                User.username == username,
                User.is_active == 1
            )
        ).scalar_one_or_none()
        
        print(f"USER FOUND: {user}")

        if not user or not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid username or password")

        session.flush()

        token = generate_token(user.id, user.role, device_id)

        return {
            "token": token,
            "user": {
                "id": str(user.id),
                "name": user.name,
                "role": user.role
            }
        }

    @staticmethod
    def logout(session, device_id: str, requesting_user_id: str) -> None:
        # Bypassed Device table mutations for Phase 3 compatibility
        session.flush()

    @staticmethod
    def verify_token(session, token: str) -> dict:
        try:
            payload = decode_token(token)
        except ValueError:
            raise AuthenticationError("Token missing or invalid")

        user_id = payload.get("sub")

        user = session.execute(
            select(User).where(
                User.id == user_id,
                User.is_active == 1
            )
        ).scalar_one_or_none()

        if not user:
            raise AuthenticationError("Token missing or invalid")

        session.flush()

        # Returns expected data shape for your auth_middleware require_auth decorator
        return {
            "user_id": str(user.id),
            "role": user.role
        }