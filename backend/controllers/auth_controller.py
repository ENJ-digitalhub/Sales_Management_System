
from flask import request, jsonify, g
from backend.services.auth_service import AuthService
from backend.database import get_db
from backend.extensions import limiter

class AuthController:
    @staticmethod
    @limiter.limit("10 per minute")
    def login():
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")
        device_name = data.get("device_name", "Unknown Device")

        if not username or not password:
            return jsonify({"success": False, "message": "Username and password are required"}), 400

        session = get_db()
        try:
            result, error = AuthService.login(session, username, password, device_name)
            if error or result is None:
                return jsonify({"success": False, "message": error or "Login failed"}), 401
            session.commit()
            return jsonify({"success": True, "token": result["token"], "user": result["user"]}), 200
        except Exception as e:
            session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def logout():
        # device_id is set by require_auth middleware, but logout can also be called without it
        # If called without require_auth, device_id needs to be passed in the request body
        device_id = None
        if hasattr(g, 'device_id'):
            device_id = g.device_id
        else:
            data = request.get_json()
            device_id = data.get("device_id")

        if not device_id:
            return jsonify({"success": False, "message": "Device ID is required for logout"}), 400

        session = get_db()
        try:
            success, error = AuthService.logout(session, device_id)
            if error:
                return jsonify({"success": False, "message": error}), 400
            session.commit()
            return jsonify({"success": True, "message": "Logged out successfully"}), 200
        except Exception as e:
            session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def verify():
        # If we reach here, require_auth has already validated the token and set g.user
        if not hasattr(g, 'user'):
            return jsonify({"valid": False, "message": "User not authenticated"}), 401
        return jsonify({"valid": True, "user": {"id": g.user.id, "role": g.user.role}}), 200
