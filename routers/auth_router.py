import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import timedelta
from core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


class LoginSchema(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(data: LoginSchema):
    if not ADMIN_EMAIL or not ADMIN_PASSWORD:
        raise HTTPException(status_code=500, detail="Admin credentials not configured")

    if data.email != ADMIN_EMAIL or data.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(
        data={"sub": data.email},
        expires_delta=timedelta(days=1),
    )

    return {
        "access_token": token,
        "user": {
            "id": 1,
            "email": ADMIN_EMAIL,
            "name": "Admin",
            "role": "admin",
        },
    }
