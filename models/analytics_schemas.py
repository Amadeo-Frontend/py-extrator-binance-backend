from pydantic import BaseModel
from typing import List


class EventStats(BaseModel):
    event_type: str
    count: int


class AdminStats(BaseModel):
    active_sessions: int
    visits_today: int
    total_events: int
    tool_usage: int
    users_total: int
    per_event: List[EventStats]
