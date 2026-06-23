from functools import wraps
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt

def secure():
    """Custom wrapper decorator combining Flask-JWT authentication requirements."""
    return jwt_required()

def roles_required(*allowed_roles: str):
    """Decorator to restrict access to specific user classifications (e.g., 'admin')."""
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            # Intercept custom claims dictionary mapped during token generation
            if claims.get("role") not in allowed_roles:
                return jsonify({"error": "Unauthorized Access. Insufficient privileges."}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator