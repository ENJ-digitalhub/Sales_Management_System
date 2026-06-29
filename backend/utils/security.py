import bcrypt


def hash_password(plain: str) -> str:
    """Hashes a plain text password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain.encode('utf-8'), salt).decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    """Verifies a plain text password against its hashed variant."""
    try:
        return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False


def hash_pin(plain_pin: str) -> str:
    """Hashes a plain text PIN using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain_pin.encode('utf-8'), salt).decode('utf-8')


def verify_pin(plain_pin: str, hashed_pin: str) -> bool:
    """Verifies a plain text PIN against its hashed variant."""
    try:
        return bcrypt.checkpw(plain_pin.encode('utf-8'), hashed_pin.encode('utf-8'))
    except Exception:
        return False
