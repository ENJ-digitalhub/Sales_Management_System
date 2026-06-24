from flask import Flask
from backend.config import Config
from backend.routes.sales import sales_bp
from backend.routes.auth import auth_bp
from backend.routes.inventory import inventory_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Register all functional domain routes
    app.register_blueprint(sales_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(inventory_bp)

    return app