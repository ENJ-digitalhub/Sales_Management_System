from flask import Blueprint, g
from backend.middleware.auth_middleware import require_auth, require_role
from backend.controllers.purchases_controller import PurchasesController

purchases_bp = Blueprint("purchases", __name__, url_prefix="/purchases")
purchases_controller = PurchasesController()


@purchases_bp.route("", methods=["POST"])
@require_auth
@require_role("admin", "manager")
def create_purchase():
    return purchases_controller.create_purchase(g.current_user)


@purchases_bp.route("/history", methods=["GET"])
@require_auth
def get_purchase_history():
    return purchases_controller.get_purchase_history()


@purchases_bp.route("/<purchase_id>", methods=["GET"])
@require_auth
def get_purchase(purchase_id):
    return purchases_controller.get_purchase(purchase_id)


@purchases_bp.route("/<purchase_id>/approve", methods=["POST"])
@require_auth
@require_role("admin")
def approve_purchase(purchase_id):
    return purchases_controller.approve_purchase(purchase_id, g.current_user)