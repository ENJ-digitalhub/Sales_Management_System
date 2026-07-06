
from flask import Flask, jsonify, g
from flask_cors import CORS
from backend.config import Config
from backend.database import create_all_tables, set_database_uri
from backend.routes.auth import auth_bp
from backend.routes.sales import sales_bp
from backend.routes.products import products_bp
from backend.routes.sync import sync_bp
from backend.routes.purchases import purchases_bp
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# conflict routes may be registered later if present
try:
    from backend.routes.conflicts import conflicts_bp
except ImportError:
    conflicts_bp = None


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.url_map.strict_slashes = False

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
        return jsonify({"message": "Welcome to Sales Management System API"})
    
    limiter.init_app(app)
    limiter.limit("10 per minute")(app.view_functions.get("auth.login"))
    return app
