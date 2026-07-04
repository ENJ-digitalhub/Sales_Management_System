from flask import Blueprint, g
from backend.middleware.auth_middleware import require_auth, require_role
from backend.controllers.products_controller import ProductsController

products_bp = Blueprint("products", __name__, url_prefix="/products")
products_controller = ProductsController()


@products_bp.route("", methods=["GET"])
@require_auth
def get_products():
    return products_controller.get_products()


@products_bp.route("", methods=["POST"])
@require_auth
@require_role("admin", "manager")
def create_product():
    return products_controller.create_product(g.current_user)


@products_bp.route("/<product_id>", methods=["PATCH"])
@require_auth
@require_role("admin", "manager")
def edit_product(product_id):
    return products_controller.edit_product(product_id, g.current_user)


@products_bp.route("/<product_id>", methods=["DELETE"])
@require_auth
@require_role("admin", "manager")
def delete_product(product_id):
    return products_controller.deactivate_product(product_id, g.current_user)