# backend/app.py
from flask import Flask, g
from backend.config import Config
from backend.routes.sales import sales_bp
from backend.routes.auth import auth_bp
from backend.routes.products import products_bp
from backend.models.database import get_session


def create_app(config_class=Config):
    """Initializes and configures the core Flask application framework."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        session = g.pop('db', None)
        if session is not None:
            session.close()

    @app.route('/health', methods=['GET'])
    def health_check():
        return {"status": "healthy"}, 200

    # Register all functional domain routes
    app.register_blueprint(sales_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)

    return app