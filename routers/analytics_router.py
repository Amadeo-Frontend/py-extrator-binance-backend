from fastapi import APIRouter
from services.analytics_service import admin_stats

router = APIRouter(
    prefix="/api/v1/analytics",
    tags=["Analytics"]
)


@router.get("/admin/stats")
async def stats_admin():
    return await admin_stats()
