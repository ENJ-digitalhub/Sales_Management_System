<<<<<<< HEAD
import os
import logging
import flask
=======
# backend\app.py
from flask import Flask, jsonify, g
>>>>>>> a9333a422bf619f612b4742acd01eac2428da808
from flask_cors import CORS
from backend.config import Config
from backend.database import create_all_tables, set_database_uri
from backend.routes.auth import auth_bp
<<<<<<< HEAD
from backend.routes.products import products_bp
from backend.routes.purchase import purchases_bp
from backend.routes.reports import reports_bp
from backend.routes.sync import sync_bp
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')


def create_app(config_class=Config):
    """Initializes and configures the core Flask application."""
    app = flask.Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='/')
=======
from backend.routes.sales import sales_bp
from backend.routes.products import products_bp
from backend.routes.sync import sync_bp
from backend.routes.purchases import purchases_bp
from backend.routes.reports import reports_bp
from backend.extensions import limiter

# conflict routes may be registered later if present
try:
    from backend.routes.conflicts import conflicts_bp
except ImportError:
    conflicts_bp = None


def create_app(config_class=Config):
    import os
    # Point to the frontend directory relative to this file
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
    app = Flask(__name__, static_folder=frontend_dir, static_url_path="")
>>>>>>> a9333a422bf619f612b4742acd01eac2428da808
    app.config.from_object(config_class)
    app.url_map.strict_slashes = False

<<<<<<< HEAD
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)

    # Configure CORS
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
=======
    set_database_uri(app.config["SQLALCHEMY_DATABASE_URI"])
    CORS(app, supports_credentials=True)

    # Initialize database
    with app.app_context():
        create_all_tables()

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(purchases_bp)
    app.register_blueprint(sync_bp)
    app.register_blueprint(reports_bp)
    if conflicts_bp is not None:
        app.register_blueprint(conflicts_bp)

    @app.teardown_appcontext
    def teardown_db(exception):
        db = g.pop("db", None)
        if db is not None:
            db.close()
>>>>>>> a9333a422bf619f612b4742acd01eac2428da808

    @app.route("/health", methods=["GET"])
    def health_check():
<<<<<<< HEAD
        return flask.jsonify({"status": "healthy", "success": True}), 200

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        session = flask.g.pop('db', None)
        if session is not None:
            try:
                session.close()
            except Exception:
                app.logger.exception("Error closing DB session")

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return flask.jsonify({"success": False, "message": "Resource not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return flask.jsonify({"success": False, "message": "Method not allowed"}), 405

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error("Server Error", exc_info=error)
        return flask.jsonify({"success": False, "message": "Internal server error"}), 500

    # Blueprint Alignment Fix
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(sales_bp)  # Relies cleanly on the '/sales' prefix inside sales.py
    app.register_blueprint(products_bp)  # Relies cleanly on the '/products' prefix inside products.py
    app.register_blueprint(purchases_bp)  # Relies cleanly on the '/purchases' prefix inside purchase.py
    app.register_blueprint(reports_bp)  # Relies cleanly on the '/reports' prefix inside reports.py
    app.register_blueprint(sync_bp)  # Relies cleanly on the '/sync' prefix inside sync.py
    return app
=======
        return jsonify({"status": "healthy"}), 200

    @app.route("/")
    def index():
        return app.send_static_file("index.html")

    @app.route("/frontend/<path:path>")
    def serve_frontend(path):
        return app.send_static_file(path)
    
    limiter.init_app(app)
    return app
>>>>>>> a9333a422bf619f612b4742acd01eac2428da808
