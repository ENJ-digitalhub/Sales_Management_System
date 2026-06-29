from functools import wraps
from flask import request, jsonify, g
from backend.database import get_db
from backend.services.auth_service import AuthService, AuthenticationError


def require_auth(f):
    """Extracts the Bearer token, verifies it against the DB (never trusts the
    token's embedded role claim), and attaches the verified user/role to flask.g.
    Returns 401 if the token is missing, malformed, invalid, expired, or the
    device session is no longer active."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"success": False, "message": "Token missing or invalid"}), 401

        token = auth_header.split(" ")[1]
        try:
            # Use get_db() directly — do NOT use 'with' since it returns g-scoped session
            session = get_db()
            user_data = AuthService.verify_token(session, token)
        except (ValueError, AuthenticationError):
            return jsonify({"success": False, "message": "Token missing or invalid"}), 401

        g.current_user = user_data
        return f(*args, **kwargs)
    return decorated_function


def require_role(*roles):
    """Restricts access to the given roles, using the DB-verified role
    attached by require_auth. Must be used after require_auth."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'current_user') or g.current_user.get('role') not in roles:
                return jsonify({"success": False, "message": "Insufficient role"}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator