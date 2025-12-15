from sqlalchemy.orm import Session
from sqlalchemy import text
from core.config import settings
from core.security import get_password_hash

def seed_admin(db: Session):
    email = settings.ADMIN_EMAIL
    password = settings.ADMIN_PASSWORD

    if not email or not password:
        return

    exists = db.execute(
        text("SELECT 1 FROM users WHERE email = :email"),
        {"email": email},
    ).fetchone()

    if exists:
        return

    hashed = get_password_hash(password)

    db.execute(
        text("""
            INSERT INTO users (email, hashed_password, role, is_active)
            VALUES (:email, :password, 'admin', true)
        """),
        {
            "email": email,
            "password": hashed,
        },
    )

    db.commit()
