# backend/routes/sales.py
from flask import Blueprint
from backend.controllers.sales_controller import get_products_controller

sales_bp = Blueprint('sales', __name__)

# Route registration points directly to the controller function
sales_bp.route('/products', methods=['GET'])(get_products_controller)