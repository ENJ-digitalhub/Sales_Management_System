from flask import Flask
from backend.config import Config
from backend.api.routes.sales import sales_bp

def create_app():
    """Initializes and configures the core Flask application framework."""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Register blueprints
    app.register_blueprint(sales_bp, url_prefix='/api')
    
    @app.route('/health', methods=['GET'])
    def health_check():
        return {"status": "healthy"}, 200
        
    return app