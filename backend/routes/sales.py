# backend/routes/sales.py
from flask import Blueprint, request, g
from backend.middleware.auth_middleware import require_auth, require_role
from backend.controllers.sales_controller import SalesController

sales_bp = Blueprint("sales", __name__, url_prefix="/sales")
sales_controller = SalesController()


# --- Products ---
@sales_bp.route("/products", methods=["GET"])
@require_auth
def get_products():
    return sales_controller.get_products()


@sales_bp.route("/products/<product_id>", methods=["PATCH"])
@require_auth
@require_role("admin", "manager")
def update_product(product_id):
    return sales_controller.update_product(product_id)


# --- Sales ---
@sales_bp.route("", methods=["POST"])
@require_auth
def create_sale():
    return sales_controller.create_sale(request.get_json(), g.current_user)


@sales_bp.route("/<sale_id>", methods=["GET"])
@require_auth
def get_sale(sale_id):
    return sales_controller.get_sale(sale_id, g.current_user)


@sales_bp.route("/<sale_id>", methods=["PATCH"])
@require_auth
def edit_sale(sale_id):
    return sales_controller.edit_sale(sale_id, request.get_json(), g.current_user)


@sales_bp.route("/<sale_id>/cancel", methods=["POST"])
@require_auth
@require_role("manager", "admin")
def cancel_sale(sale_id):
    return sales_controller.cancel_sale(sale_id, g.current_user)