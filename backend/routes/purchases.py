from flask import Blueprint
from backend.controllers.purchases_controller import PurchasesController
from backend.utils.auth_middleware import require_auth, require_role

purchases_bp = Blueprint("purchases", __name__, url_prefix="/purchases")

purchases_bp.route("/", methods=["POST"])(require_auth(PurchasesController.create_purchase))
purchases_bp.route("/<string:purchase_id>", methods=["GET"])(require_auth(PurchasesController.get_purchase))
purchases_bp.route("/history", methods=["GET"])(require_auth(PurchasesController.get_purchase_history))
purchases_bp.route("/<string:purchase_id>/approve", methods=["POST"])(require_auth(require_role("admin")(PurchasesController.approve_purchase)))
