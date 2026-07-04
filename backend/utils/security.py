import bcrypt

class Security:
    @staticmethod
    def hash_password(password: str) -> str:
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