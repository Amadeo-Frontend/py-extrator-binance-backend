from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import SessionLocal
from healthcheck import healthcheck

from core.config import settings
from core.exceptions import add_exception_handlers

from utils.admin_seed import seed_admin

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

# --------------------------------------------------
# APP
# --------------------------------------------------
app = FastAPI(
    title="API de Análise e Extração de Dados",
    description=(
        "API modular para análises e extrações de dados "
        "(Binance, Polygon, Alpha Vantage, TradingView), "
        "geração de relatórios e analytics."
    ),
    version="1.0.0",
)

# --------------------------------------------------
# CORS
# --------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# EXCEPTION HANDLERS GLOBAIS
# --------------------------------------------------
add_exception_handlers(app)

# --------------------------------------------------
# STARTUP (SEED ADMIN)
# --------------------------------------------------
@app.on_event("startup")
def on_startup():
    """
    Cria o usuário admin automaticamente
    caso não exista.
    """
    db = SessionLocal()
    try:
        seed_admin(db)
    finally:
        db.close()

# --------------------------------------------------
# ROOT + HEALTHCHECK
# --------------------------------------------------
@app.get("/", tags=["Root"])
def root():
    return {
        "status": "API online",
        "service": "extrator-binance-backend",
        "version": "1.0.0",
    }


@app.get("/health", tags=["Health"])
def health_route():
    return healthcheck()

# --------------------------------------------------
# ROTAS
# --------------------------------------------------
app.include_router(auth_router.router)
app.include_router(binance_router.router)
app.include_router(polygon_router.router)
app.include_router(alphavantage_router.router)
app.include_router(tradingview_router.router)
app.include_router(reports_router.router)
app.include_router(tracking_router.router)
app.include_router(analytics_router.router)
