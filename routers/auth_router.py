from datetime import timedelta
from fastapi import APIRouter, HTTPException
import bcrypt

from models.db import get_sync_conn
from core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login")
def login(payload: dict):
    email = payload.get("email")
    password = payload.get("password")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Dados inválidos")

    conn = get_sync_conn()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, email, password_hash, role FROM users WHERE email = %s",
        (email,)
    )
    user = cursor.fetchone()
    conn.close()

    if not user or not bcrypt.checkpw(
        password.encode("utf-8"),
        user["password_hash"].encode("utf-8")
    ):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    token = create_access_token(
        {
            "sub": str(user["id"]),
            "email": user["email"],
            "role": user["role"],
        },
        expires_delta=timedelta(hours=8),
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "role": user["role"],
        },
    }
