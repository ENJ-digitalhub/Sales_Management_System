# backend/services/auth_service.py
from datetime import datetime
from backend.models.user import User
from backend.models.device import Device
from backend.utils.security import verify_password
from backend.utils.jwt_utils import generate_token, decode_token


class AuthenticationError(ValueError):
    """Raised for any authentication/authorization failure. Subclasses
    ValueError so existing `except ValueError` call sites keep working."""
    pass


class AuthService:

    @staticmethod
    def login(session, username: str, password: str, device_id: str) -> dict:
        """Validates credentials, invalidates the user's previous active device,
        marks/creates the current device as active, and issues a JWT."""
        if not username or not password or not device_id:
            raise AuthenticationError("Invalid username or password")

        user = session.query(User).filter(
            User.username == username, User.is_active == True
        ).first()

        if not user or not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid username or password")

        # One active session per user — invalidate any other active devices
        session.query(Device).filter(
            Device.user_id == user.id, Device.is_active == True
        ).update({"is_active": False})

        device = session.query(Device).filter(
            Device.user_id == user.id, Device.device_name == device_id
        ).first()

        if device:
            device.is_active = True
            device.last_seen_at = datetime.now()
        else:
            device = Device(user_id=user.id, device_name=device_id, is_active=True)
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
        """Invalidates the given device session — only if it belongs to the
        authenticated user making the request."""
        device = session.query(Device).filter(
            Device.device_name == device_id,
            Device.user_id == requesting_user_id
        ).first()

        if not device:
            raise AuthenticationError("Device not found or not owned by this user")

        device.is_active = False
        session.flush()

    @staticmethod
    def verify_token(session, token: str) -> dict:
        """Decodes the token, then re-fetches the user's role from the DB
        (never trusts the role claim embedded in the token itself)."""
        try:
            payload = decode_token(token)
        except ValueError:
            raise AuthenticationError("Token missing or invalid")

        user_id = payload.get("sub")
        device_id = payload.get("device_id")

        user = session.query(User).filter(
            User.id == user_id, User.is_active == True
        ).first()

        if not user:
            raise AuthenticationError("Token missing or invalid")

        device = session.query(Device).filter(
            Device.user_id == user.id,
            Device.device_name == device_id,
            Device.is_active == True
        ).first()

        if not device:
            raise AuthenticationError("Token missing or invalid")

        device.last_seen_at = datetime.now()
        session.flush()

        return {
            "id": str(user.id),
            "role": user.role
        }