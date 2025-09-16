# backend/main.py (VERSÃO FINAL COM TAREFAS EM SEGUNDO PLANO)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importa todos os roteadores, incluindo o novo para relatórios
from routers import binance, tradingview, alphavantage, polygon, reports

app = FastAPI(
    title="API de Análise e Extração de Dados",
    description="Uma API modular com funções para Binance, TradingView, Alpha Vantage e Polygon.io, com suporte a tarefas em segundo plano."
)

# Defina as origens permitidas (seu frontend local e em produção)
origins = [
    "https://nextjs-extrator-binance-frontend.vercel.app",
    "http://localhost:3000",
]

# Configuração do CORS para permitir todos os métodos, essencial para as requisições 'OPTIONS'
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
 )

@app.get("/", tags=["Root"])
def read_root():
    """Endpoint principal para verificar se a API está online."""
    return {"status": "API modular online."}

# --- REGISTRO DE TODOS OS ROTEADORES ---
# O aplicativo principal delega as rotas para os módulos específicos.

app.include_router(binance.router)
app.include_router(tradingview.router)
app.include_router(alphavantage.router)
app.include_router(polygon.router)

# Inclui o novo roteador para listar e baixar relatórios gerados
app.include_router(reports.router)

