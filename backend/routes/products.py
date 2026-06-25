from flask import Blueprint
from backend.controllers.products_controller import ProductsController
from backend.utils.auth_decorators import login_required, roles_allowed

products_bp = Blueprint("products", __name__, url_prefix="/products")

products_bp.route("", methods=["GET"])(
    login_required(ProductsController.list_products)
)

products_bp.route("/<int:product_id>", methods=["PATCH"])(
    login_required(roles_allowed("admin", "manager")(ProductsController.update_product))
)