from functools import wraps
from flask import request, jsonify, g
from backend.services.auth_service import AuthService

def login_required(f):
    """
    Decorator to verify valid JWT presence in the Authorization Header.
    Protects routes from unauthenticated requests.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        # Check if header exists and follows the 'Bearer <token>' format
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"success": False, "error": "Token missing or invalid"}), 401
            
        # Extract the token string
        token = auth_header.split(" ")[1]
        user_data = AuthService.get_current_user_by_token(token)
        
        # If token is expired, invalid, or user doesn't exist anymore
        if not user_data:
            return jsonify({"success": False, "error": "Token missing or invalid"}), 401
            
        # Store user context globally in Flask 'g' for this request scope
        g.current_user = user_data
        return f(*args, **kwargs)
        
    return decorated_function

def roles_allowed(*roles):
    """
    Decorator to restrict access based on user role.
    Must always be placed beneath @login_required.
    Usage: @roles_allowed('admin', 'manager')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Assumes @login_required ran first and populated g.current_user
            if not hasattr(g, 'current_user') or g.current_user.get('role') not in roles:
                return jsonify({"success": False, "error": "Unauthorized action"}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator