from fastapi import APIRouter, BackgroundTasks
from models.forex_schemas import RequestData
from services.polygon_service import run_extraction, run_analysis

router = APIRouter(
    prefix="/api/v1/polygon",
    tags=["Polygon"]
)


@router.post("/download-data")
async def polygon_extract(data: RequestData, bg: BackgroundTasks):
    bg.add_task(run_extraction, data)
    return {"message": f"Extração Polygon iniciada para {len(data.assets)} ativos."}


@router.post("/analysis")
async def polygon_analysis(data: RequestData, bg: BackgroundTasks):
    bg.add_task(run_analysis, data)
    return {"message": f"Análise Polygon iniciada para {data.assets[0]}."}
