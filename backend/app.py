from flask import Flask
from backend.config import Config
from backend.routes.sales import sales_bp
from backend.routes.auth import auth_bp  # <--- Step 1: Import the newly committed blueprint

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Register all functional domain routes
    app.register_blueprint(sales_bp)
    app.register_blueprint(auth_bp)   # <--- Step 2: Register the blueprint here

    return app