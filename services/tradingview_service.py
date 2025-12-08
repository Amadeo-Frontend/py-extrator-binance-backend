from datetime import datetime
from fastapi import HTTPException
from tradingview_ta import TA_Handler, Interval

from models.forex_schemas import TVForexQuery


COMMON_FOREX = [
    "EURUSD","USDJPY","GBPUSD","USDCHF","USDCAD",
    "AUDUSD","NZDUSD","EURGBP","EURJPY","GBPJPY","USDBRL"
]


def search_forex(query: str):
    q = query.replace("/", "").upper().strip()
    return [x for x in COMMON_FOREX if q in x]


def get_forex_summary(data: TVForexQuery):
    symbol = data.symbol.replace("/", "").upper()
    exchanges = [data.exchange] if data.exchange else ["FX_IDC", "OANDA"]

    last_error = None

    for ex in exchanges:
        try:
            handler = TA_Handler(
                symbol=symbol,
                exchange=ex,
                screener="forex",
                interval=Interval.INTERVAL_1_MINUTE
            )
            analysis = handler.get_analysis()

            return {
                "symbol": symbol,
                "exchange": ex,
                "time": datetime.utcnow().isoformat() + "Z",
                "summary": analysis.summary,
                "oscillators": analysis.oscillators,
                "moving_averages": analysis.moving_averages,
                "indicators": analysis.indicators,
            }

        except Exception as e:
            last_error = str(e)
            continue

    raise HTTPException(status_code=400,
        detail=f"Erro ao obter dados TradingView ({symbol}): {last_error}"
    )
