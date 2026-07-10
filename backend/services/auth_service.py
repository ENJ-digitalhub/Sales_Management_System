<<<<<<< HEAD
from datetime import datetime, timezone
from sqlalchemy import select
from backend.models.models import User
from backend.utils.security import verify_password
from backend.utils.jwt_utils import generate_token, decode_token


class AuthenticationError(ValueError):
    """Raised when authentication fails (bad credentials, invalid token, etc.)."""
    pass

=======

from sqlalchemy.orm import Session
from backend.models.models import User, Device
from backend.utils.security import Security
from backend.utils.jwt_utils import JWTUtils
from datetime import datetime, timezone
import uuid
>>>>>>> a9333a422bf619f612b4742acd01eac2428da808

class AuthService:
    @staticmethod
<<<<<<< HEAD
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
        device_id = payload.get("device_id")

        user = session.execute(
            select(User).where(
                User.id == user_id,
                User.is_active == 1
            )
        ).scalar_one_or_none()
=======
    def login(session: Session, username, password, device_name):
        user = session.query(User).filter_by(username=username).first()
        if not user or not Security.verify_password(password, user.password_hash):
            return None, "Invalid username or password"

        # Invalidate previous active devices for this user
        session.query(Device).filter_by(user_id=user.id, is_active=True).update({"is_active": False})

        # Create new device entry
        device = Device(user_id=user.id, device_name=device_name, is_active=True, last_seen_at=datetime.now(timezone.utc))
        session.add(device)
        session.flush() # To get device.id

        token = JWTUtils.generate_token(user.id, user.role, device.id)
        return {"token": token, "user": {"id": user.id, "name": user.name, "role": user.role}}, None

    @staticmethod
    def logout(session: Session, device_id):
        device = session.query(Device).filter_by(id=device_id).first()
        if device:
            device.is_active = False
            session.add(device)
            session.commit()
            return True, None
        return False, "Device not found"

    @staticmethod
    def verify_token(session: Session, token: str):
        data = JWTUtils.decode_token(token)
        if "error" in data:
            return None, data["error"]
>>>>>>> a9333a422bf619f612b4742acd01eac2428da808

        user = session.query(User).filter_by(id=data["sub"]).first()
        if not user:
<<<<<<< HEAD
            raise AuthenticationError("Token missing or invalid")

        session.flush()

        # Returns expected data shape for your auth_middleware require_auth decorator
        return {
            "user_id": str(user.id),
            "role": user.role,
            "device_id": device_id,
        }
=======
            return None, "Invalid token"

        device = session.query(Device).filter_by(id=data["device_id"], user_id=user.id, is_active=True).first()
        if not device:
            return None, "Invalid token or inactive device"

        # Update last_seen_at for the device
        device.last_seen_at = datetime.now(timezone.utc)
        session.add(device)
        session.commit()

        return {"id": user.id, "role": user.role, "device_id": device.id}, None
>>>>>>> a9333a422bf619f612b4742acd01eac2428da808
