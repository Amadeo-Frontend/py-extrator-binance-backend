import bcrypt
from psycopg2.extras import RealDictCursor

from core.config import settings
from models.db import get_sync_conn


def seed_admin():
    admin_email = settings.ADMIN_EMAIL
    admin_password = settings.ADMIN_PASSWORD

    if not admin_email or not admin_password:
        print("[ADMIN SEED] ADMIN_EMAIL ou ADMIN_PASSWORD não definidos")
        return

    conn = get_sync_conn()

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            "SELECT id FROM users WHERE email = %s",
            (admin_email,)
        )

        if cursor.fetchone():
            print("[ADMIN SEED] Admin já existe")
            return

        password_hash = bcrypt.hashpw(
            admin_password.encode(),
            bcrypt.gensalt(12)
        ).decode()

        cursor.execute(
            """
            INSERT INTO users (email, password_hash, role)
            VALUES (%s, %s, %s)
            """,
            (admin_email, password_hash, "admin")
        )

        conn.commit()
        print("[ADMIN SEED] Admin criado com sucesso")

    except Exception as e:
        conn.rollback()
        print(f"[ADMIN SEED ERROR] {e}")

    finally:
        conn.close()
