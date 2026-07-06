
from sqlalchemy.orm import Session
from backend.models.models import User, Device
from backend.utils.security import Security
from backend.utils.jwt_utils import JWTUtils
from datetime import datetime, timezone
import uuid

class AuthService:
    @staticmethod
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

        user = session.query(User).filter_by(id=data["sub"]).first()
        device = session.query(Device).filter_by(id=data["device_id"], user_id=user.id, is_active=True).first()

        if not user or not device:
            return None, "Invalid token or inactive device"

        # Update last_seen_at for the device
        device.last_seen_at = datetime.now(timezone.utc)
        session.add(device)
        session.commit()

        return {"id": user.id, "role": user.role, "device_id": device.id}, None
