from fastapi import APIRouter
from models.forex_schemas import TVForexQuery
from services.tradingview_service import search_forex, get_forex_summary

router = APIRouter(
    prefix="/api/v1/tradingview",
    tags=["TradingView"]
)


@router.get("/forex/search")
def tv_search(q: str):
    return {"query": q, "matches": search_forex(q)}


@router.post("/forex/summary")
def tv_summary(data: TVForexQuery):
    return get_forex_summary(data)
