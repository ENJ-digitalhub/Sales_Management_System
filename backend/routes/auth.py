from flask import Blueprint
from backend.controllers.auth_controller import AuthController
from backend.utils.auth_middleware import require_auth

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

auth_bp.route("/login", methods=["POST"])(AuthController.login)
auth_bp.route("/logout", methods=["POST"])(require_auth(AuthController.logout))
auth_bp.route("/verify", methods=["GET"])(require_auth(AuthController.verify))