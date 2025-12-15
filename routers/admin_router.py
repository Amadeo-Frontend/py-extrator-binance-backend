from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt

from database import get_db
from models import User

router = APIRouter(prefix="/auth", tags=["auth"])
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "seu_jwt_secret"
ALGORITHM = "HS256"

@router.post("/login")
def login(data: dict, db: Session = Depends(get_db)):
    email = data.get("email")
    password = data.get("password")

    user = db.query(User).filter(User.email == email).first()

    if not user or not pwd.verify(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = jwt.encode(
        {"id": user.id, "email": user.email, "role": user.role},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
        },
        "access_token": token,
    }
