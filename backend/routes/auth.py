<<<<<<< HEAD
=======

>>>>>>> a9333a422bf619f612b4742acd01eac2428da808
from flask import Blueprint
from backend.controllers.auth_controller import AuthController
from backend.utils.auth_middleware import require_auth

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

auth_bp.route("/login", methods=["POST"])(AuthController.login)
auth_bp.route("/logout", methods=["POST"])(require_auth(AuthController.logout))
<<<<<<< HEAD
auth_bp.route("/verify", methods=["GET"])(require_auth(AuthController.verify))
=======
auth_bp.route("/verify", methods=["GET"])(require_auth(AuthController.verify))
>>>>>>> a9333a422bf619f612b4742acd01eac2428da808
