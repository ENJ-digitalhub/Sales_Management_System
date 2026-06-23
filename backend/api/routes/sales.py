from flask import Blueprint
from backend.api.controllers.sales_controller import get_products_controller

sales_bp = Blueprint('sales', __name__)

# Route registration points directly to the controller function
sales_bp.route('/products', methods=['GET'])(get_products_controller)