from sqlalchemy.orm import Session
from models.db import User
from core.security import get_password_hash
from core.config import settings

def seed_admin(db: Session):
    admin = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
    if admin:
        return

    user = User(
        email=settings.ADMIN_EMAIL,
        hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
        role="admin",
        is_active=True,
    )

    db.add(user)
    db.commit()
