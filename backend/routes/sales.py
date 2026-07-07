# backend\routes\sales.py
from flask import Blueprint
from backend.controllers.sales_controller import SalesController
from backend.utils.auth_middleware import require_auth, require_role

sales_bp = Blueprint("sales", __name__, url_prefix="/sales")

sales_bp.route("/", methods=["POST"])(require_auth(SalesController.create_sale))
sales_bp.route("/", methods=["GET"])(require_auth(SalesController.get_all_sales))
sales_bp.route("/<string:sale_id>", methods=["GET"])(require_auth(SalesController.get_sale))
sales_bp.route("/<string:sale_id>", methods=["PATCH", "PUT"])(require_auth(SalesController.edit_sale))
sales_bp.route("/<string:sale_id>", methods=["DELETE"])(require_auth(require_role("admin")(SalesController.delete_sale)))
sales_bp.route("/<string:sale_id>/cancel", methods=["POST"])(require_auth(require_role("admin", "manager")(SalesController.cancel_sale)))
sales_bp.route("/<string:sale_id>/request-edit", methods=["POST"])(require_auth(require_role("admin", "manager")(SalesController.request_edit)))
