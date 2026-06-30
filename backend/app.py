from flask import Flask, g, send_from_directory
from flask_cors import CORS
from backend.config import Config
from backend.routes.sales import sales_bp
from backend.routes.auth import auth_bp
import os


def create_app(config_class=Config):
    """Initializes and configures the core Flask application framework."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Allow the frontend (served separately, e.g. via Live Server on a
    # different port) to call this API across origins during development.
    CORS(app, resources={
        r"/*": {
            "origins": [
                "http://127.0.0.1:5500",
                "http://localhost:5500",
                "http://127.0.0.1:5000",
                "http://localhost:5000"
            ],
            "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })

    @app.route('/')
    def index():
        return send_from_directory(
            os.path.join(os.path.dirname(__file__), '..', 'frontend'),
            'index.html'
        )
        
    @app.route('/<path:filename>')
    def serve_frontend(filename):
        return send_from_directory(
            os.path.join(os.path.dirname(__file__), '..', 'frontend'),
            filename
        )

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        """Close the request-scoped DB session if one was created."""
        session = g.pop('db', None)
        if session is not None:
            session.close()

    @app.route('/health', methods=['GET'])
    def health_check():
        return {"status": "healthy"}, 200

    # Register all functional domain routes
    app.register_blueprint(sales_bp)
    app.register_blueprint(auth_bp)

    return app