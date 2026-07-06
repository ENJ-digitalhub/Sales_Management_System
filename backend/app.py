
from flask import Flask, jsonify, g
from flask_cors import CORS
from backend.config import Config
from backend.database import create_all_tables, SessionLocal
from backend.routes.auth import auth_bp
from backend.routes.sales import sales_bp
from backend.routes.products import products_bp
from backend.routes.sync import sync_bp
from backend.routes.purchases import purchases_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.url_map.strict_slashes = False

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

    return app
