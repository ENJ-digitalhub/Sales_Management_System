
from functools import wraps
from flask import request, jsonify, g
from backend.utils.jwt_utils import decode_token
import backend.database as database
from backend.models.models import User
from backend.database import get_db


def require_auth(f):
    @wraps(f)
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

    return decorated

def require_role(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, "user") or g.user.role not in roles:
                return jsonify({"message": "Permission denied: Insufficient role"}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator
