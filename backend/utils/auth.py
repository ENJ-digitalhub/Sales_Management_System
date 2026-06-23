import jwt
import datetime
from functools import wraps
from flask import request, jsonify

# Shared verification config matching your system security architecture
JWT_SECRET = "super-secret-pos-key"
JWT_ALGORITHM = "HS256"

def generate_token(user_id: str, role: str) -> str:
    """Generates a raw PyJWT access token containing identity and role claims."""
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2),
        "iat": datetime.datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def secure():
    """Custom JWT verification middleware using raw PyJWT decoding rules."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return jsonify({"error": "Missing or invalid authorization header"}), 401
            
            # Split out the token string from the Bearer prefix
            token = auth_header.split(" ")[1]
            try:
                # Manually decode claims using pure PyJWT parameters
                decoded_claims = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
                # Attach the identity context to the Flask request object lifestyle
                request.user_claims = decoded_claims
            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token has expired"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"error": "Invalid token assignment"}), 401
                
            return fn(*args, **kwargs)
        return wrapper
    def_decorator = decorator
    return def_decorator

def roles_required(*allowed_roles: str):
    """Role enforcement utility matching token claim signatures."""
    def decorator(fn):
        @wraps(fn)
        @secure()  # Automatically execute token validation checks first
        def wrapper(*args, **kwargs):
            claims = getattr(request, "user_claims", {})
            if claims.get("role") not in allowed_roles:
                return jsonify({"error": "Unauthorized Access. Insufficient privileges."}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator