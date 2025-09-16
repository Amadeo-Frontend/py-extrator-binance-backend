# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import binance, tradingview, alphavantage, polygon

app = FastAPI(
    title="API de Análise e Extração de Dados",
    description="Uma API modular com funções para Binance, TradingView, Alpha Vantage e Polygon.io."
)

# Defina as origens permitidas (seu frontend local e em produção)
origins = [
    "https://nextjs-extrator-binance-frontend.vercel.app",
    "http://localhost:3000",
]

# --- CORREÇÃO APLICADA AQUI ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    # Permita todos os métodos (GET, POST, OPTIONS, etc. )
    allow_methods=["*"], 
    allow_headers=["*"],
)

@app.get("/", tags=["Root"])
def read_root():
    return {"status": "API modular online."}

# Inclui todos os seus roteadores
app.include_router(binance.router)
app.include_router(tradingview.router)
app.include_router(alphavantage.router)
app.include_router(polygon.router)
