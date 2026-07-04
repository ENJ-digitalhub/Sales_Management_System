import uuid

from backend.app import create_app
from backend.database import get_db
from backend.models.models import User
from backend.utils.security import hash_password

app = create_app()

with app.app_context():
    session = get_db()

    username = "admin"

    existing = session.query(User).filter_by(username=username).first()

    if existing:
        print("Admin user already exists.")
    else:
        user = User(
            id=str(uuid.uuid4()),
            name="Administrator",
            username="admin",
            password_hash=hash_password("Admin@123"),
            role="admin",
            phone_or_email="admin@trexave.com",
            is_active=1
        )

        session.add(user)
        session.commit()

        print("Admin user created successfully.")
        print("Username: admin")
        print("Password: Admin@123")