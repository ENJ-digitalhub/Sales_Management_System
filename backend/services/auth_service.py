from backend.models.database import get_session
from backend.models.user import User
from backend.utils.security import verify_password, generate_token, decode_token

class AuthService:
    @staticmethod
    def authenticate_user(username: str, password: str) -> dict:
        """Validates credentials and yields user data along with an access token."""
        if not username or not password:
            raise ValueError("Invalid credentials")

        with get_session() as session:
            user = session.query(User).filter(User.username == username, User.is_active == True).first()
            
            if not user or not verify_password(password, user.password_hash):
                raise ValueError("Invalid credentials")
            
            # Extract attributes before the session closes
            token = generate_token(user.id, user.role)
            user_data = {
                "id": str(user.id),
                "name": user.name, # Assuming your schema has a display name
                "username": user.username,
                "role": user.role
            }
            
        return {"token": token, "user": user_data}

    @staticmethod
    def verify_current_user(token: str) -> dict:
        """Decodes token and verifies that the payload represents an active user."""
        try:
            payload = decode_token(token)
            user_id = payload.get("user_id")
            
            with get_session() as session:
                user = session.query(User).filter(User.id == user_id, User.is_active == True).first()
                if not user:
                    raise ValueError("Token missing or invalid")
                
                return {
                    "id": str(user.id),
                    "name": user.name,
                    "username": user.username,
                    "role": user.role
                }
        except Exception:
            raise ValueError("Token missing or invalid")