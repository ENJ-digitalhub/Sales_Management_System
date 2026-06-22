from flask import request, jsonify
from backend.utils.validators import validate_pagination_params
from backend.services.sales_service import SalesService

def get_products_controller():
    """Handles the request/response shape—completely separate from route registration."""
    page_param = request.args.get('page')
    per_page_param = request.args.get('per_page')
    
    # 1. Run structural validation
    validation = validate_pagination_params(page_param, per_page_param)
    if validation["error"]:
        return jsonify({"error": validation["error"]}), 400
        
    # 2. Execute business logic via service
    result = SalesService.get_paginated_products(
        page=validation["page"], 
        per_page=validation["per_page"]
    )
    
    return jsonify(result), 200