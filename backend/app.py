from flask import Flask
from backend.config import Config
from backend.extensions import jwt

# Explicitly ensure these point to your routes
from backend.routes.sales import sales_bp
from backend.routes.auth import auth_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    app.config["JWT_SECRET_KEY"] = "super-secret-pos-key"
    jwt.init_app(app)

    # Register your Blueprints
    app.register_blueprint(sales_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")

    return app