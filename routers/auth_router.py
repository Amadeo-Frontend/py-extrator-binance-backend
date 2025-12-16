from fastapi import APIRouter, HTTPException
from psycopg2.extras import RealDictCursor
import bcrypt
from datetime import timedelta

from models.db import get_sync_conn
from core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login")
def login(payload: dict):
    email = payload.get("email")
    password = payload.get("password")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Credenciais inválidas")

    conn = get_sync_conn()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute(
        "SELECT id, email, password_hash, role FROM users WHERE email = %s",
        (email,)
    )
    user = cursor.fetchone()

    conn.close()

    if not user or not bcrypt.checkpw(
        password.encode(),
        user["password_hash"].encode()
    ):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")

    access_token = create_access_token(
        data={"sub": str(user["id"]), "role": user["role"]},
        expires_delta=timedelta(hours=12)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "role": user["role"],
        },
    }
