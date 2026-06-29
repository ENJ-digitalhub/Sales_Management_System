# backend/util/security.py
import bcrypt

class Security:
    @staticmethod
    def hash_password(password: str ) -> str:
        """Hashes password using bcrypt"""
        password_byte = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hash_password = bcrypt.hashpw(password_byte, salt)
        return hash_password.decode('utf-8')
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """verifier for hashed password"""
        password_byte = password.encode('utf-8')
        hashed_byte = hashed.encode('utf-8')
        status = bcrypt.checkpw(password_byte, hashed_byte)
        return status