from sqlalchemy.orm import Session
from passlib.context import CryptContext
from models.user import User
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def seed_admin(db: Session):
    email = os.getenv("ADMIN_EMAIL")
    password = os.getenv("ADMIN_PASSWORD")

    if not email or not password:
        return

    admin = db.query(User).filter(User.email == email).first()
    if admin:
        return

    hashed_password = pwd_context.hash(password)

    admin = User(
        email=email,
        name="Admin",
        hashed_password=hashed_password,
        role="admin",
        is_active=True,
    )

    db.add(admin)
    db.commit()
