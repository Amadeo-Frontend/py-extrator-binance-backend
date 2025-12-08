from fastapi import APIRouter, BackgroundTasks
from models.forex_schemas import RequestData
from services.binance_service import run_extraction, run_analysis

router = APIRouter(
    prefix="/api/v1/binance",
    tags=["Binance"]
)


@router.post("/download-data")
async def download_binance(data: RequestData, bg: BackgroundTasks):
    bg.add_task(run_extraction, data)
    return {"message": f"Extração para {len(data.assets)} ativo(s) iniciada."}


@router.post("/analysis")
async def analysis_binance(data: RequestData, bg: BackgroundTasks):
    bg.add_task(run_analysis, data)
    return {"message": f"Análise iniciada para {data.assets[0]}."}
