from fastapi import APIRouter, Request
from models.tracking_schemas import SessionPayload, EventPayload
from services.tracking_service import track_session, track_event

router = APIRouter(
    prefix="/api/v1/tracking",
    tags=["Tracking"]
)


@router.post("/session")
def session_track(data: SessionPayload, request: Request):
    email = data.user_id
    ip = data.ip or request.client.host
    track_session(email, ip)
    return {"ok": True}


@router.post("/event")
def event_track(data: EventPayload):
    track_event(data.user_id, data.event_type)
    return {"ok": True}
