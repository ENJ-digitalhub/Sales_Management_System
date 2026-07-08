
from flask import Blueprint
from backend.controllers.sync_controller import SyncController
from backend.utils.auth_middleware import require_auth, require_role

sync_bp = Blueprint("sync", __name__, url_prefix="/sync")

sync_bp.route("", methods=["POST"])(require_auth(SyncController.push_changes))
sync_bp.route("/pull", methods=["GET"])(require_auth(SyncController.pull_changes))
sync_bp.route("/resolve", methods=["POST"])(require_auth(require_role("manager", "admin")(SyncController.resolve_conflict)))
