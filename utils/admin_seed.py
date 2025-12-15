import bcrypt
from psycopg2.extras import RealDictCursor

from core.config import settings
from models.db import get_sync_conn


def seed_admin():
    """
    Cria o usuário admin automaticamente na inicialização.
    Idempotente (não recria se já existir).
    """

    if not settings.ADMIN_EMAIL or not settings.ADMIN_PASSWORD:
        print("[ADMIN SEED] ADMIN_EMAIL ou ADMIN_PASSWORD não definidos")
        return

    conn = None

    try:
        conn = get_sync_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            "SELECT id FROM users WHERE email = %s",
            (settings.ADMIN_EMAIL,)
        )

        if cursor.fetchone():
            print("[ADMIN SEED] Admin já existe")
            return

        password_hash = bcrypt.hashpw(
            settings.ADMIN_PASSWORD.encode(),
            bcrypt.gensalt(12)
        ).decode()

        cursor.execute(
            """
            INSERT INTO users (email, password_hash, role)
            VALUES (%s, %s, 'admin')
            """,
            (settings.ADMIN_EMAIL, password_hash)
        )

        conn.commit()
        print("[ADMIN SEED] Admin criado com sucesso")

    except Exception as e:
        print(f"[ADMIN SEED ERROR] {e}")
        if conn:
            conn.rollback()

    finally:
        if conn:
            conn.close()
