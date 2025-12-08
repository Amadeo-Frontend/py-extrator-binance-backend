from pydantic import BaseModel, Field
from typing import List, Optional


class RequestData(BaseModel):
    """
    Dados enviados para extração/análise de Forex (Polygon, Binance, Alpha Vantage)
    """
    assets: List[str] = Field(..., min_length=1)
    intervals: List[str] = Field(..., min_length=1)
    start_date: str
    end_date: str


class TVForexQuery(BaseModel):
    """
    Consulta para TradingView Forex
    """
    symbol: str = Field(..., description="Par forex como 'EURUSD'")
    exchange: Optional[str] = Field(
        default=None,
        description="Exchange do TradingView como 'FX_IDC' ou 'OANDA'"
    )
