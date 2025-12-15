from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.exceptions import add_exception_handlers

from healthcheck import healthcheck
from utils.admin_seed import seed_admin
from models.db import get_sync_conn

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
        "API modular para análises e extrações de dados "
        "(Binance, Polygon, Alpha Vantage, TradingView)"
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
# EXCEPTIONS
# --------------------------------------------------
add_exception_handlers(app)

# --------------------------------------------------
# STARTUP (seed admin)
# --------------------------------------------------
@app.on_event("startup")
def startup():
    conn = get_sync_conn()
    try:
        seed_admin(conn)
    finally:
        conn.close()

# --------------------------------------------------
# ROOT + HEALTH
# --------------------------------------------------
@app.get("/", tags=["Root"])
def root():
    return {"status": "API online", "version": "1.0.0"}

@app.get("/health", tags=["Health"])
def health():
    return healthcheck()

# --------------------------------------------------
# ROUTERS
# --------------------------------------------------
app.include_router(auth_router.router)
app.include_router(binance_router.router)
app.include_router(polygon_router.router)
app.include_router(alphavantage_router.router)
app.include_router(tradingview_router.router)
app.include_router(reports_router.router)
app.include_router(tracking_router.router)
app.include_router(analytics_router.router)
