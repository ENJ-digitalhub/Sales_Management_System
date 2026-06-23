from functools import wraps
from flask import request, jsonify
import jwt
from backend.config import Config

def secure(allowed_roles=None):  # <--- Make sure it accepts this argument!
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            if "Authorization" in request.headers:
                auth_header = request.headers["Authorization"]
                if auth_header.startswith("Bearer "):
                    token = auth_header.split(" ")[1]

            if not token:
                return jsonify({"error": "Authorization token is missing"}), 401

            try:
                # Decode the user's incoming payload token safely
                payload = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
                current_user = payload
                
                # Verify if the user's role has permission to access the route
                if allowed_roles and current_user.get("role") not in allowed_roles:
                    return jsonify({"error": "Unauthorized access level"}), 403
                    
            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token has expired"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"error": "Invalid validation token"}), 401

            # Pass the verified current user payload context along to the route logic
            return f(current_user, *args, **kwargs)
        return decorated
    return decorator