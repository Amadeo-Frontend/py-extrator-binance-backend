from fastapi import APIRouter
import psycopg2
import os

router = APIRouter()
NEON_URL = os.getenv("NEON_DATABASE_URL")

def db():
    return psycopg2.connect(NEON_URL)

@router.post("/track/event")
def track_event(data: dict):
    email = data.get("email")
    event = data.get("event")

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO events (user_email, event)
        VALUES (%s, %s)
    """, (email, event))

    conn.commit()
    cur.close()
    conn.close()

    return {"ok": True}
