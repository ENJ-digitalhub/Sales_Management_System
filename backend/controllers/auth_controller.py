# backend/controllers/auth_controller.py
from flask import request, jsonify, g
from backend.database import get_db
from backend.services.auth_service import AuthService


class AuthController:

    @staticmethod
    def login():
        """Handles POST /auth/login."""
        data = request.get_json() or {}
        username = data.get("username")
        password = data.get("password")
        device_id = data.get("device_id")

        try:
            session = get_db()
            result = AuthService.login(session, username, password, device_id)
        except ValueError as e:
            return jsonify({"success": False, "message": str(e)}), 401

        return jsonify({"success": True, **result}), 200

    @staticmethod
    def logout():
        """Handles POST /auth/logout."""
        data = request.get_json() or {}
        device_id = data.get("device_id")

        try:
            session = get_db()
            AuthService.logout(session, device_id, g.current_user["id"])
        except ValueError as e:
            return jsonify({"success": False, "message": str(e)}), 403

        return jsonify({"success": True}), 200

    @staticmethod
    def verify():
        """Handles GET /auth/verify. g.current_user was already populated
        and DB-verified by require_auth."""
        return jsonify({"valid": True, "user": g.current_user}), 200