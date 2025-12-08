from fastapi import APIRouter, HTTPException
from models.auth_schemas import AuthPayload, AuthResponse
from services.analytics_service import validate_user
import bcrypt

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Auth"]
)


@router.post("/login", response_model=AuthResponse)
async def login(data: AuthPayload):
    """
    Login oficial integrado ao banco (tabela users)
    via analytics_service.validate_user.
    """
    user = await validate_user(
        email=data.email,
        password_hash=data.password,
        checkpw_fn=bcrypt.checkpw
    )

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return user
