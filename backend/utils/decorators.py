from functools import wraps
from flask import request, jsonify, g
from backend.services.auth_service import AuthService

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"success": False, "error": "Token missing or invalid"}), 401
        
        token = auth_header.split(" ")[1]
        try:
            g.current_user = AuthService.verify_current_user(token)
        except ValueError as e:
            return jsonify({"success": False, "error": str(e)}), 401
            
        return f(*args, **kwargs)
    return decorated

def require_roles(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(g, 'current_user') or g.current_user.get('role') not in roles:
                return jsonify({"success": False, "error": "Unauthorized access privilege"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator