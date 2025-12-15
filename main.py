from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.exceptions import add_exception_handlers

from models.db import SessionLocal
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

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------- EXCEPTIONS --------------
add_exception_handlers(app)

# ----------- STARTUP -----------------
@app.on_event("startup")
def startup():
    db = SessionLocal()
    try:
        seed_admin(db)
    finally:
        db.close()

# ----------- ROOT --------------------
@app.get("/")
def root():
    return {"status": "API online"}

@app.get("/health")
def health():
    return {"status": "ok"}

# ----------- ROUTERS -----------------
app.include_router(auth_router.router)
app.include_router(binance_router.router)
app.include_router(polygon_router.router)
app.include_router(alphavantage_router.router)
app.include_router(tradingview_router.router)
app.include_router(reports_router.router)
app.include_router(tracking_router.router)
app.include_router(analytics_router.router)
