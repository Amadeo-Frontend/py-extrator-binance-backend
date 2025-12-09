# services/tracking_service.py

from models.db import get_sync_conn


def track_session(email: str, ip: str):
    conn = get_sync_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO sessions (user_email, ip)
        VALUES (%s, %s)
    """, (email, ip))

    conn.commit()
    cur.close()
    conn.close()


def track_event(email: str, event: str):
    conn = get_sync_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO events (user_email, event)
        VALUES (%s, %s)
    """, (email, event))

    conn.commit()
    cur.close()
    conn.close()
