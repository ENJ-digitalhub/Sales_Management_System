# backend\app.py
from flask import Flask, jsonify, g
from flask_cors import CORS
from backend.config import Config
from backend.database import create_all_tables, set_database_uri, SessionLocal
from backend.utils.default_user import ensure_default_user
from backend.routes.auth import auth_bp
from backend.routes.sales import sales_bp
from backend.routes.items import items_bp
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
    app.config.from_object(config_class)
    app.url_map.strict_slashes = False

    set_database_uri(app.config["SQLALCHEMY_DATABASE_URI"])
    CORS(app, supports_credentials=True)

    # Initialize database
    with app.app_context():
        create_all_tables()
        # First-run bootstrap: create the default user from .env, if configured
        # and not already present. Idempotent — safe to run on every startup.
        bootstrap_session = SessionLocal()
        try:
            ensure_default_user(bootstrap_session)
        except Exception as e:
            bootstrap_session.rollback()
            print(f"[bootstrap] Failed to ensure default user: {e}")
        finally:
            bootstrap_session.close()

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(items_bp)
    app.register_blueprint(purchases_bp)
    app.register_blueprint(reports_bp)

    if app.config.get("SYNC_ENABLED"):
        app.register_blueprint(sync_bp)
        if conflicts_bp is not None:
            app.register_blueprint(conflicts_bp)

    @app.teardown_appcontext
    def teardown_db(exception):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "healthy"}), 200

    @app.route("/")
    def index():
        return app.send_static_file("index.html")

    @app.route("/frontend/<path:path>")
    def serve_frontend(path):
        return app.send_static_file(path)
    
    limiter.init_app(app)
    return app
