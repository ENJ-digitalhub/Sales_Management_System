# backend/routes/products.py
from flask import Blueprint
from backend.controllers.products_controller import ProductsController
from backend.utils.auth_middleware import require_auth, require_role

products_bp = Blueprint("products", __name__, url_prefix="/products")

products_bp.route("", methods=["GET"])(
    require_auth(ProductsController.list_products)
)

products_bp.route("/<product_id>", methods=["PATCH"])(
    require_auth(require_role("admin", "manager")(ProductsController.update_product))
)