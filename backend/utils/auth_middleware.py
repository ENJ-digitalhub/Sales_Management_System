<<<<<<< HEAD
=======

>>>>>>> a9333a422bf619f612b4742acd01eac2428da808
from functools import wraps
from flask import request, jsonify, g
from backend.utils.jwt_utils import decode_token
import backend.database as database
from backend.models.models import User
from backend.database import get_db
<<<<<<< HEAD
from backend.services.auth_service import AuthService, AuthenticationError
=======
>>>>>>> a9333a422bf619f612b4742acd01eac2428da808


def require_auth(f):
    @wraps(f)
<<<<<<< HEAD
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

        g.current_user = {
            "id": user_data["user_id"],
            "role": user_data["role"],
            "device_id": user_data.get("device_id"),
        }
        return f(*args, **kwargs)

    return decorated_function
=======
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            try:
                token = request.headers["Authorization"].split(" ")[1]
            except IndexError:
                return jsonify({"message": "Malformed Authorization header!"}), 401

        if not token:
            return jsonify({"message": "Authentication Token is missing!"}), 401

        try:
            data = decode_token(token)
            if "error" in data:
                return jsonify({"message": data["error"]}), 401

            # Use the current database session factory for request auth
            session = get_db()
            user = session.query(User).filter_by(id=data["sub"]).first()
            session.close()

            if not user:
                return jsonify({"message": "User not found!"}), 401
            g.user = user
            g.device_id = data["device_id"]
        except Exception as e:
            return jsonify({"message": "Token is invalid!", "error": str(e)}), 401

        return f(*args, **kwargs)
>>>>>>> a9333a422bf619f612b4742acd01eac2428da808

    return decorated

def require_role(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
<<<<<<< HEAD
            current_user = getattr(g, "current_user", None)
            if not current_user or current_user.get("role") not in roles:
                return jsonify({"success": False, "message": "Insufficient role"}), 403
=======
            if not hasattr(g, "user") or g.user.role not in roles:
                return jsonify({"message": "Permission denied: Insufficient role"}), 403
>>>>>>> a9333a422bf619f612b4742acd01eac2428da808
            return f(*args, **kwargs)

        return decorated_function
<<<<<<< HEAD

    return decorator
=======
    return decorator
>>>>>>> a9333a422bf619f612b4742acd01eac2428da808
