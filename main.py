# main.py
import os
from backend.app import create_app
from backend.config import Config, ProductionConfig

env = os.getenv("FLASK_ENV", "development")
config_class = ProductionConfig if env == "production" else Config
app = create_app(config_class)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=(env != "production"))