from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.exceptions import add_exception_handlers

from routers import (
    auth_router,
    binance_router,
    polygon_router,
    alphavantage_router,
    tradingview_router,
    reports_router,
    tracking_router,
    analytics_router,
)


app = FastAPI(
    title="API de Análise e Extração de Dados",
    description=(
        "API modular para análises e extrações de dados (Binance, Polygon, "
        "Alpha Vantage, TradingView), geração de relatórios e analytics."
    ),
    version="1.0.0",
)


# -------------------------------------------------------------------
# CORS
# -------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------------
# EXCEPTION HANDLERS GLOBAIS
# -------------------------------------------------------------------
add_exception_handlers(app)


# -------------------------------------------------------------------
# ROOT + HEALTHCHECK
# -------------------------------------------------------------------
@app.get("/", tags=["Root"])
def root():
    return {"status": "API online", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}


# -------------------------------------------------------------------
# REGISTRO DE ROTEADORES (todos em /api/v1/...)
# -------------------------------------------------------------------
app.include_router(auth_router.router)
app.include_router(binance_router.router)
app.include_router(polygon_router.router)
app.include_router(alphavantage_router.router)
app.include_router(tradingview_router.router)
app.include_router(reports_router.router)
app.include_router(tracking_router.router)
app.include_router(analytics_router.router)
