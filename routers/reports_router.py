import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from services.reports_service import list_reports

router = APIRouter(
    prefix="/api/v1/reports",
    tags=["Reports"]
)


@router.get("/")
def get_reports():
    return {"files": list_reports()}


@router.get("/{filename}")
def download_file(filename: str):
    path = os.path.join("reports", filename)

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado.")

    return FileResponse(path, filename=filename, media_type="application/zip")
