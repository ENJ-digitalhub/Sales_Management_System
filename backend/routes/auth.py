from flask import Blueprint
from backend.controllers.auth_controller import login_controller, me_controller
from backend.utils.auth import secure

auth_bp = Blueprint("auth", __name__)

# Route Registration
auth_bp.post("/login")(login_controller)
auth_bp.get("/me")(secure()(me_controller))  # Protected with our custom PyJWT middleware wrapper