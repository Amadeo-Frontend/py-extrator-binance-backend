from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


security_scheme = HTTPBearer(auto_error=False)


async def get_current_user_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
) -> str | None:
    """
    Placeholder para futura autenticação via Bearer Token (JWT ou similar).
    Hoje não é obrigatório e não interfere nas rotas existentes.
    """
    if credentials is None:
        # Retorna None ao invés de levantar erro, para não quebrar nada existente
        return None

    token = credentials.credentials
    # Aqui futuramente você pode validar o token (JWT, etc.)
    return token


def require_admin_token(token: str | None = Depends(get_current_user_token)) -> None:
    """
    Exemplo de guard de admin.
    Hoje não valida nada, mas já deixa o gancho para o futuro.
    """
    # Exemplo futuro:
    # if not token or not is_admin(token): raise HTTPException(...)
    return
