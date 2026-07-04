from functools import wraps
from flask import request, jsonify, g
from backend.database import get_db
from backend.services.auth_service import AuthService, AuthenticationError


def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"success": False, "message": "Token missing or invalid"}), 401

        token = auth_header.split(" ", 1)[1].strip()

        try:
            session = get_db()
            user_data = AuthService.verify_token(session, token)
        except (ValueError, AuthenticationError):
            return jsonify({"success": False, "message": "Token missing or invalid"}), 401

        g.current_user = {"id": user_data["user_id"], "role": user_data["role"]}
        return f(*args, **kwargs)

    return decorated_function


def require_role(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_user = getattr(g, "current_user", None)
            if not current_user or current_user.get("role") not in roles:
                return jsonify({"success": False, "message": "Insufficient role"}), 403
            return f(*args, **kwargs)

        return decorated_function

    return decorator