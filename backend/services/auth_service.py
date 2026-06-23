from sqlalchemy import select
from backend.database import SessionLocal
from backend.models.models import User  # Make sure this points to your User/Employee model
from backend.utils.security import verify_password
from backend.utils.auth import generate_token

class AuthService:
    @staticmethod
    def authenticate_user(username: str, password_raw: str) -> str | None:
        """Validates database user credentials and returns a signed PyJWT token."""
        # Single responsibility: Manage the data query and verification check
        with SessionLocal() as session:
            stmt = select(User).where(User.username == username)
            user = session.scalars(stmt).first()
            
            # Check if user exists and verify password hash match securely
            if user and verify_password(password_raw, user.password_hash):
                # Return raw string token using our custom PyJWT utility
                return generate_token(user_id=str(user.id), role=user.role)
                
        return None

    @staticmethod
    def get_profile_data(user_id: str) -> dict | None:
        """Retrieves raw user details from the database layer by unique ID identifier."""
        with SessionLocal() as session:
            stmt = select(User).where(User.id == user_id)
            user = session.scalars(stmt).first()
            
            if user:
                return {
                    "id": str(user.id),
                    "username": user.username,
                    "role": user.role,
                    "is_active": user.is_active
                }
        return None