import bcrypt
from backend.database import SessionLocal, engine
from backend.models.models import Base, User  # Explicitly importing User registers its table details

def seed():
    print("Forcing table definitions initialization...")
    # This now catches the User model correctly because it's actively imported above
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as session:
        try:
            existing = session.query(User).filter_by(username="admin").first()
            if existing:
                print("User 'admin' already exists inside the database engine.")
                return
        except Exception as e:
            print(f"Metadata generation failed or table missing context. Details: {e}")
            return

        # Securely hash the password 'password123'
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw("password123".encode('utf-8'), salt).decode('utf-8')

        test_user = User(
            username="admin",
            password_hash=hashed_password,
            role="admin",
            is_active=True
        )
        session.add(test_user)
        session.commit()
        print("🎉 Success! Database seeded with user: 'admin' / password: 'password123'")

if __name__ == "__main__":
    seed()