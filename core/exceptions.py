from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def add_exception_handlers(app: FastAPI) -> None:
    """
    Registra handlers globais de exceções.
    Não muda sua lógica, só organiza a resposta de erro.
    """

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "status_code": exc.status_code,
                "path": request.url.path,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        # Aqui você pode logar de forma mais completa depois
        return JSONResponse(
            status_code=500,
            content={
                "error": "Erro interno no servidor",
                "detail": str(exc),
                "path": request.url.path,
            },
        )
