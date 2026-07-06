
from flask import Blueprint
from backend.controllers.sync_controller import SyncController
from backend.utils.auth_middleware import require_auth

sync_bp = Blueprint("sync", __name__, url_prefix="/sync")

sync_bp.route("/push", methods=["POST"])(require_auth(SyncController.push_changes))
sync_bp.route("/pull", methods=["GET"])(require_auth(SyncController.pull_changes))
sync_bp.route("/resolve-conflict", methods=["POST"])(require_auth(SyncController.resolve_conflict))
