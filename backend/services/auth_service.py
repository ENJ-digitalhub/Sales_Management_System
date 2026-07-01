from datetime import datetime, timezone
from sqlalchemy import select, update
from backend.models.models import User, Device
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

        # Fetch user
        user = session.execute(
            select(User).where(
                User.username == username,
                User.is_active == True
            )
        ).scalar_one_or_none()
        
        print(f"USER FOUND: {user}")  # ← add this

        if not user or not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid username or password")

        # Invalidate all other active devices for this user
        session.execute(
            update(Device)
            .where(Device.user_id == user.id, Device.is_active == True)
            .values(is_active=False)
        )

        # Find or create device
        device = session.execute(
            select(Device).where(
                Device.user_id == user.id,
                Device.device_name == device_id
            )
        ).scalar_one_or_none()

        if device:
            device.is_active = True
            device.last_seen_at = AuthService._now()
        else:
            device = Device(
                user_id=user.id,
                device_name=device_id,
                is_active=True,
                last_seen_at=AuthService._now()
            )
            session.add(device)

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
        device = session.execute(
            select(Device).where(
                Device.device_name == device_id,
                Device.user_id == requesting_user_id
            )
        ).scalar_one_or_none()

        if not device:
            raise AuthenticationError("Device not found or not owned by this user")

        device.is_active = False
        session.flush()

    @staticmethod
    def verify_token(session, token: str) -> dict:
        try:
            payload = decode_token(token)
        except ValueError:
            raise AuthenticationError("Token missing or invalid")

        user_id = payload.get("sub")
        device_id = payload.get("device_id")

        user = session.execute(
            select(User).where(
                User.id == user_id,
                User.is_active == True
            )
        ).scalar_one_or_none()

        if not user:
            raise AuthenticationError("Token missing or invalid")

        device = session.execute(
            select(Device).where(
                Device.user_id == user.id,
                Device.device_name == device_id,
                Device.is_active == True
            )
        ).scalar_one_or_none()

        if not device:
            raise AuthenticationError("Token missing or invalid")

        device.last_seen_at = AuthService._now()
        session.flush()

        return {
            "id": str(user.id),
            "role": user.role
        }