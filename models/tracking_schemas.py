from pydantic import BaseModel
from typing import Optional, Dict, Any


class SessionPayload(BaseModel):
    user_id: Optional[str] = None
    ip: Optional[str] = None
    user_agent: Optional[str] = None


class EventPayload(BaseModel):
    user_id: Optional[str] = None
    event_type: str
    meta: Optional[Dict[str, Any]] = None
