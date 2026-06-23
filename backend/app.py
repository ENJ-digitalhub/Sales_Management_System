from flask import Flask
from backend.config import Config
from backend.routes.sales import sales_bp
from backend.routes.products import products_bp  # <--- Make sure this is imported

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Register all application domains
    app.register_blueprint(sales_bp)
    app.register_blueprint(products_bp)  # <--- Register the blueprint here

    return app