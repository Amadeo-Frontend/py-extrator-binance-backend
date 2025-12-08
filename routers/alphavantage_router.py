from fastapi import APIRouter, BackgroundTasks
from models.forex_schemas import RequestData
from services.alphavantage_service import run_extraction, run_analysis

router = APIRouter(
    prefix="/api/v1/alphavantage",
    tags=["AlphaVantage"]
)


@router.post("/download-data")
async def av_extract(data: RequestData, bg: BackgroundTasks):
    bg.add_task(run_extraction, data)
    return {"message": "Extração AlphaVantage iniciada."}


@router.post("/analysis")
async def av_analysis(data: RequestData, bg: BackgroundTasks):
    bg.add_task(run_analysis, data)
    return {"message": f"Análise AlphaVantage iniciada para {data.assets[0]}."}
