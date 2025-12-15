from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.exceptions import add_exception_handlers
from healthcheck import healthcheck
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

app = FastAPI(
    title="API de Análise e Extração de Dados",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

add_exception_handlers(app)


@app.on_event("startup")
def startup():
    seed_admin()


@app.get("/")
def root():
    return {"status": "API online"}


@app.get("/health")
def health():
    return healthcheck()


app.include_router(auth_router.router)
app.include_router(binance_router.router)
app.include_router(polygon_router.router)
app.include_router(alphavantage_router.router)
app.include_router(tradingview_router.router)
app.include_router(reports_router.router)
app.include_router(tracking_router.router)
app.include_router(analytics_router.router)
