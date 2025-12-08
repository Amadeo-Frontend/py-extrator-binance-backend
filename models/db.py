import psycopg2
from psycopg2.extras import RealDictCursor
from core.config import settings


def get_sync_conn():
    """
    Conexão síncrona (psycopg2) — usada em routers mais antigos.
    """
    return psycopg2.connect(
        settings.NEON_DATABASE_URL,
        cursor_factory=RealDictCursor
    )
