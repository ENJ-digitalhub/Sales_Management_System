# backend/app.py
from flask import Flask, g
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


from backend.database import get_db
        
def create_app():
    """Initializes and configures the core Flask application framework."""
    app = Flask(__name__)
    app.config.from_object(Config)

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        session = g.pop('db', None)
        if session is not None:
            session.close()

    @app.route('/health', methods=['GET'])
    def health_check():
        return {"status": "healthy"}, 200
        
    # Register blueprints
    app.register_blueprint(sales_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(inventory_bp, url_prefix='/api')
    return app