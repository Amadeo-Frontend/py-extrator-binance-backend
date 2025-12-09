# models/db.py
import psycopg2
from psycopg2.extras import RealDictCursor

import asyncpg
from core.config import settings


# ===========================
# 🔹 Conexão Síncrona (psycopg2)
# ===========================
def get_sync_conn():
    """
    Conexão síncrona com Postgres (Neon + Render).
    """
    if not settings.NEON_DATABASE_URL:
        raise ValueError("NEON_DATABASE_URL não está definido!")

    try:
        conn = psycopg2.connect(
            settings.NEON_DATABASE_URL,
            sslmode="require",  
            cursor_factory=RealDictCursor,
        )
        return conn

    except Exception as e:
        print(f"[DB ERROR] Sync connection failed: {e}")
        raise


# ===========================
# 🔹 Conexão Assíncrona (asyncpg)
# ===========================
async def get_async_conn():
    """
    Conexão assíncrona com Neon.
    """
    try:
        conn = await asyncpg.connect(
            settings.NEON_DATABASE_URL,
            ssl="require",
        )
        return conn
    except Exception as e:
        print(f"[DB ERROR] Async connection failed: {e}")
        raise


# ===========================
# 🔹 Pool Assíncrono (recomendado)
# ===========================
async def get_async_pool():
    """
    Pool de conexões assíncronas para alta performance.
    """
    try:
        pool = await asyncpg.create_pool(
            settings.NEON_DATABASE_URL,
            ssl="require",
            min_size=1,
            max_size=5,
        )
        return pool
    except Exception as e:
        print(f"[DB ERROR] Failed to create async pool: {e}")
        raise
