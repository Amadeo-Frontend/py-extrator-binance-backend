# backend/main.py (VERSÃO MODULARIZADA)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importa os roteadores que criamos
from routers import binance, tradingview

app = FastAPI(
    title="API de Análise e Extração de Dados",
    description="Uma API modular com funções para Binance e TradingView."
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
# Inclui todos os endpoints do arquivo binance.py na aplicação principal
app.include_router(binance.router)

# Inclui todos os endpoints do arquivo tradingview.py
app.include_router(tradingview.router)
