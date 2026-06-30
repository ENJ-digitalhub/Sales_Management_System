from flask import Blueprint
from backend.controllers.sales_controller import get_products_controller, update_product_controller
from backend.utils.auth_middleware import require_auth, require_role

sales_bp = Blueprint('sales', __name__)

sales_bp.route('/products', methods=['GET'])(require_auth(get_products_controller))
sales_bp.route('/products/<product_id>', methods=['PATCH'])(
    require_auth(require_role('admin', 'manager')(update_product_controller))
)