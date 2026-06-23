from flask import Blueprint
from backend.controllers.products_controller import get_products_controller

products_bp = Blueprint("products", __name__)

# Single responsibility: Bind the network route directly to the HTTP handler
products_bp.get("/products")(get_products_controller)