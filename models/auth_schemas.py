from pydantic import BaseModel


class AuthPayload(BaseModel):
    """
    Payload usado tanto para login quanto para validação Analytics.
    """
    email: str
    password: str


class AuthResponse(BaseModel):
    """
    Retorno padronizado de autenticação.
    """
    id: str
    email: str
    role: str
