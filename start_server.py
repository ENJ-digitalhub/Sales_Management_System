# start_server.py
import os
from waitress import serve
from backend.app import create_app
from backend.config import Config, ProductionConfig

env = os.getenv("FLASK_ENV", "production")
config_class = ProductionConfig if env == "production" else Config
app = create_app(config_class)

if __name__ == "__main__":
    host = getattr(config_class, "WAITRESS_HOST", "0.0.0.0")
    port = getattr(config_class, "WAITRESS_PORT", 5000)
    print(f"Starting production server on {host}:{port} (env={env})", flush=True)
    serve(app, host=host, port=port)