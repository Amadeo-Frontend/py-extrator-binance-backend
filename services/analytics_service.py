import asyncpg
from core.config import settings


async def get_conn():
    return await asyncpg.connect(settings.NEON_DATABASE_URL)


async def validate_user(email: str, password_hash: str, checkpw_fn):
    conn = await get_conn()
    try:
        row = await conn.fetchrow(
            "SELECT id, email, password_hash, role FROM users WHERE email = $1",
            email
        )
        if not row:
            return None

        ok = checkpw_fn(password_hash.encode(), row["password_hash"].encode())
        if not ok:
            return None

        return {
            "id": str(row["id"]),
            "email": row["email"],
            "role": row["role"],
        }
    finally:
        await conn.close()


async def admin_stats():
    conn = await get_conn()

    try:
        active = await conn.fetchval(
            "SELECT count(*) FROM sessions WHERE last_active > (now() - interval '15 minutes')"
        )
        visits = await conn.fetchval(
            "SELECT count(*) FROM events WHERE created_at >= date_trunc('day', now()) AND event_type LIKE 'page:%'"
        )
        total = await conn.fetchval("SELECT count(*) FROM events")
        tool = await conn.fetchval("SELECT count(*) FROM events WHERE event_type = 'tool_used'")
        users_total = await conn.fetchval("SELECT count(*) FROM users")

        per_event_rows = await conn.fetch(
            "SELECT event_type, count(*) AS cnt FROM events GROUP BY event_type ORDER BY cnt DESC"
        )
        per_event = [{"event_type": r["event_type"], "count": r["cnt"]} for r in per_event_rows]

        return {
            "active_sessions": active,
            "visits_today": visits,
            "total_events": total,
            "tool_usage": tool,
            "users_total": users_total,
            "per_event": per_event,
        }

    finally:
        await conn.close()
