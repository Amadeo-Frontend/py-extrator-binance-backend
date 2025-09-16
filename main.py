# backend/main.py (VERSÃO COM ALPHA VANTAGE)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 1. Importe o novo roteador junto com os outros
from routers import binance, tradingview, alphavantage

app = FastAPI(
    title="API de Análise e Extração de Dados",
    description="Uma API modular com funções para Binance, TradingView e Alpha Vantage."
)

# Configuração do CORS (continua igual)
origins = [
    "https://nextjs-extrator-binance-frontend.vercel.app",
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
 )

@app.get("/", tags=["Root"])
def read_root():
    return {"status": "API modular online."}

# --- JUNTA TUDO AQUI ---
app.include_router(binance.router)
app.include_router(tradingview.router)
# 2. Inclua o roteador da Alpha Vantage
app.include_router(alphavantage.router)
