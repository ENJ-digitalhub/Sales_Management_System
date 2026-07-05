from flask import request, jsonify, g
from backend.database import get_db
from backend.services.auth_service import AuthService, AuthenticationError


class AuthController:

    @staticmethod
    def login():
        """Handles POST /auth/login."""
        data = request.get_json() or {}
        username = data.get("username")
        password = data.get("password")
        device_id = data.get("device_id")

        session = get_db()
        try:
            result = AuthService.login(session, username, password, device_id)
            session.commit()  # <-- COMMIT the device changes and token generation
        except AuthenticationError as e:
            session.rollback()
            return jsonify({"success": False, "message": str(e)}), 401
        except Exception as e:
            session.rollback()
            # Log the real error for debugging
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": "Internal server error"}), 500

        return jsonify({"success": True, **result}), 200

    @staticmethod
    def logout():
        """Handles POST /auth/logout."""
        data = request.get_json() or {}
        device_id = data.get("device_id")

        session = get_db()
        try:
            AuthService.logout(session, device_id, g.current_user["id"])
            session.commit()
        except AuthenticationError as e:
            session.rollback()
            return jsonify({"success": False, "message": str(e)}), 403
        except Exception as e:
            session.rollback()
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": "Internal server error"}), 500

        return jsonify({"success": True}), 200

    @staticmethod
    def verify():
        """Handles GET /auth/verify. g.current_user was already populated
        and DB-verified by require_auth."""
        return jsonify({"valid": True, "user": g.current_user}), 200