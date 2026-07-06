
import bcrypt

class Security:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hashes a password using bcrypt."""
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verifies a password against a hashed password."""
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def hash_password(password: str) -> str:
    """Hashes a password using bcrypt."""
    return Security.hash_password(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verifies a password against a hashed password."""
    return Security.verify_password(password, hashed_password)
