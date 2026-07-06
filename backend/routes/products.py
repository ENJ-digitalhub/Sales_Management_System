
from flask import Blueprint
from backend.controllers.products_controller import ProductController
from backend.utils.auth_middleware import require_auth, require_role

products_bp = Blueprint("products", __name__, url_prefix="/products")

products_bp.route("/", methods=["POST"])(require_auth(require_role("admin", "manager")(ProductController.create_product)))
products_bp.route("/<string:product_id>", methods=["GET"])(require_auth(ProductController.get_product))
products_bp.route("/", methods=["GET"])(require_auth(ProductController.get_all_products))
products_bp.route("/<string:product_id>", methods=["PATCH"])(require_auth(require_role("admin", "manager")(ProductController.update_product)))
products_bp.route("/<string:product_id>", methods=["DELETE"])(require_auth(require_role("admin", "manager")(ProductController.delete_product)))