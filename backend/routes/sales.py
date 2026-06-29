# backend/routes/sales.py
from flask import Blueprint
from backend.controllers.sales_controller import get_products_controller
from backend.utils.auth_middleware import require_auth

sales_bp = Blueprint('sales', __name__)

# Route registration points directly to the controller function
sales_bp.route('/products', methods=['GET'])(require_auth(get_products_controller))