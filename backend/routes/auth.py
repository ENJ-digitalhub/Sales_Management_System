from flask import Blueprint, jsonify
from backend.api.auth.auth_controller import login_controller
from backend.utils.auth import secure, roles_required

auth_bp = Blueprint("auth", __name__)

# Core authentication endpoint
auth_bp.post("/login")(login_controller)

# Protected test route: Requires a valid token
@auth_bp.get("/dashboard")
@secure()
def dashboard_test():
    return jsonify({"ok": True, "message": "Welcome to the protected dashboard!"}), 200

# Role restricted test route: Requires admin role explicitly
@auth_bp.get("/admin-only")
@roles_required("admin")
def admin_test():
    return jsonify({"ok": True, "message": "Access granted: Admin space verified."}), 200