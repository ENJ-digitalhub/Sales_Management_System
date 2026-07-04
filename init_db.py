from backend.app import create_app
from backend.database import init_db

app = create_app()

with app.app_context():
    init_db()
    print("Database initialized successfully.")