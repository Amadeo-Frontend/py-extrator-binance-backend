import bcrypt
from psycopg2.extras import RealDictCursor

from core.config import settings
from models.db import get_sync_conn


def seed_admin():
    """
    Cria o usuário admin automaticamente.
    Executa apenas se não existir.
    """

    admin_email = settings.ADMIN_EMAIL
    admin_password = settings.ADMIN_PASSWORD

    if not admin_email or not admin_password:
        print("[ADMIN SEED] Variáveis ADMIN_EMAIL ou ADMIN_PASSWORD ausentes")
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
            admin_password.encode("utf-8"),
            bcrypt.gensalt(12)
        ).decode("utf-8")

        cursor.execute(
            """
            INSERT INTO users (email, password_hash, role)
            VALUES (%s, %s, 'admin')
            """,
            (admin_email, password_hash)
        )

        conn.commit()
        print("[ADMIN SEED] Admin criado com sucesso")

    except Exception as e:
        conn.rollback()
        print(f"[ADMIN SEED ERROR] {e}")

    finally:
        conn.close()
