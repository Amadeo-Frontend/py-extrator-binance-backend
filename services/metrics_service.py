from fastapi import APIRouter, Request
import psycopg2
import os

router = APIRouter()
NEON_URL = os.getenv("NEON_DATABASE_URL")

def db():
    return psycopg2.connect(NEON_URL)

@router.post("/track/session")
def track_session(data: dict, request: Request):
    email = data.get("email")
    ip = request.client.host

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO sessions (user_email, ip)
        VALUES (%s, %s)
    """, (email, ip))

    conn.commit()
    cur.close()
    conn.close()
    return {"ok": True}
