from flask_jwt_extended import create_access_token

class AuthService:
    @staticmethod
    def issue_token(user) -> str:
        """Generates a secure JWT access token embedding the user's role claim."""
        return create_access_token(
            identity=str(user.id),
            additional_claims={"role": user.role}
        )