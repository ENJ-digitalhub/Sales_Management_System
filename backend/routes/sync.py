<<<<<<< HEAD
from flask import Blueprint, g
from backend.middleware.auth_middleware import require_auth, require_role
from backend.controllers.sync_controller import SyncController

sync_bp = Blueprint("sync", __name__, url_prefix="/sync")
sync_controller = SyncController()


@sync_bp.route("", methods=["POST"])
@require_auth
def push_sync():
    return sync_controller.push_sync(g.current_user)


@sync_bp.route("/pull", methods=["GET"])
@require_auth
def pull_sync():
    return sync_controller.pull_sync()


@sync_bp.route("/resolve", methods=["POST"])
@require_auth
@require_role("manager", "admin")
def resolve_conflict():
    return sync_controller.resolve_conflict(g.current_user)
=======

from flask import Blueprint
from backend.controllers.sync_controller import SyncController
from backend.utils.auth_middleware import require_auth, require_role

sync_bp = Blueprint("sync", __name__, url_prefix="/sync")

sync_bp.route("", methods=["POST"])(require_auth(SyncController.push_changes))
sync_bp.route("/pull", methods=["GET"])(require_auth(SyncController.pull_changes))
sync_bp.route("/resolve", methods=["POST"])(require_auth(require_role("manager", "admin")(SyncController.resolve_conflict)))
>>>>>>> a9333a422bf619f612b4742acd01eac2428da808
