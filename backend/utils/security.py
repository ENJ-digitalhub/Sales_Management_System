<<<<<<< HEAD
=======

>>>>>>> a9333a422bf619f612b4742acd01eac2428da808
import bcrypt

class Security:
    @staticmethod
    def hash_password(password: str) -> str:
<<<<<<< HEAD
        """Hashes password using bcrypt"""
        password_byte = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password_byte, salt)
        return hashed_password.decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """verifier for hashed password"""
        password_byte = password.encode('utf-8')
        hashed_byte = hashed.encode('utf-8')
        status = bcrypt.checkpw(password_byte, hashed_byte)
        return status

# Expose functions directly at the module level for direct imports
hash_password = Security.hash_password
verify_password = Security.verify_password
=======
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
>>>>>>> a9333a422bf619f612b4742acd01eac2428da808
