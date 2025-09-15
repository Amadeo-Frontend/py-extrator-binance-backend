# backend/routers/tradingview.py

from datetime import datetime
from fastapi import APIRouter, HTTPException

# Importe os modelos de dados e funções auxiliares que este roteador precisa
from .common import TVForexQuery

# --- VERIFICAÇÃO E IMPORTAÇÃO DE DEPENDÊNCIAS OPCIONAIS ---
try:
    from tradingview_ta import TA_Handler, Interval # type: ignore
    _TV_AVAILABLE = True
except ImportError:
    _TV_AVAILABLE = False

router = APIRouter(
    prefix="/tradingview",
    tags=["TradingView"]
)

# --- ENDPOINTS TRADINGVIEW (APENAS OS FUNCIONAIS) ---
COMMON_FOREX = ["EURUSD", "USDJPY", "GBPUSD", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY", "USDBRL"]

@router.get("/forex/search", summary="Busca simples por pares forex (lista interna)")
def tv_search_forex(q: str):
    q = q.replace("/", "").upper().strip()
    results = [s for s in COMMON_FOREX if q in s]
    return {"query": q, "matches": results}

@router.post("/forex/summary", summary="Resumo do TradingView para um par forex")
def tv_forex_summary(data: TVForexQuery):
    if not _TV_AVAILABLE:
        raise HTTPException(status_code=501, detail="A biblioteca 'tradingview-ta' não está instalada no ambiente.")
    symbol = data.symbol.replace("/", "").upper()
    exchanges = [data.exchange] if data.exchange else ["FX_IDC", "OANDA"]
    last_error = None
    for ex in exchanges:
        try:
            handler = TA_Handler(symbol=symbol, exchange=ex, screener="forex", interval=Interval.INTERVAL_1_MINUTE)
            analysis = handler.get_analysis()
            return {
                "symbol": symbol, "exchange": ex, "time": datetime.utcnow().isoformat() + "Z",
                "summary": analysis.summary, "oscillators": analysis.oscillators,
                "moving_averages": analysis.moving_averages, "indicators": analysis.indicators,
            }
        except Exception as e:
            last_error = str(e)
            continue
    raise HTTPException(status_code=400, detail=f"Não foi possível obter dados do TradingView para {symbol}. Último erro: {last_error}")
