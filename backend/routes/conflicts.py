from flask import Blueprint
from backend.controllers.conflicts_controller import ConflictsController
from backend.utils.auth_middleware import require_auth, require_role

conflicts_bp = Blueprint("conflicts", __name__, url_prefix="/conflicts")

conflicts_bp.route("", methods=["GET"])(require_auth(require_role("manager", "admin")(ConflictsController.get_conflicts)))
conflicts_bp.route("/<string:transaction_id>", methods=["GET"])(require_auth(require_role("manager", "admin")(ConflictsController.get_conflict)))
conflicts_bp.route("/<string:transaction_id>/resolve", methods=["POST"])(require_auth(require_role("manager", "admin")(ConflictsController.resolve_conflict)))
