from flask import Blueprint, request, jsonify
from backend.utils.validators import validate_pagination_params
from backend.services.sales_service import SalesService

sales_bp = Blueprint('sales', __name__)

@sales_bp.route('/products', methods=['GET'])
def get_products():
    """Handles parsing, validation, execution, and JSON delivery."""
    page_param = request.args.get('page')
    per_page_param = request.args.get('per_page')
    
    # Run structural validation
    validation = validate_pagination_params(page_param, per_page_param)
    if validation["error"]:
        return jsonify({"error": validation["error"]}), 400
        
    # Execute database transactions via service wrapper
    result = SalesService.get_paginated_products(
        page=validation["page"], 
        per_page=validation["per_page"]
    )
    
    return jsonify(result), 200