from flask import request, jsonify, g
from backend.services.auth_service import AuthService

class AuthController:

    @staticmethod
    def login():
        """Handles POST /auth/login payload verification."""
        data = request.get_json() or {}
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({"success": False, "error": "Invalid credentials"}), 401

        try:
            result = AuthService.authenticate_user(username, password)
        except ValueError:
            # Keep error payload matching locked contract exactly
            return jsonify({"success": False, "error": "Invalid credentials"}), 401

        # Match exact locked payload contract for 200 OK
        return jsonify({
            "success": True,
            "token": result["token"],
            "user": result["user"]
        }), 200

    @staticmethod
    def get_me():
        """Handles GET /auth/me payload response."""
        if not hasattr(g, 'current_user') or not g.current_user:
            return jsonify({"success": False, "error": "Token missing or invalid"}), 401

        return jsonify({
            "success": True,
            "user": g.current_user
        }), 200