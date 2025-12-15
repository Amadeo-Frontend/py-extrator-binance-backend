# utils/admin_seed.py

import bcrypt
from psycopg2.extras import RealDictCursor

from core.config import settings
from models.db import get_sync_conn


def seed_admin():
    """
    Cria o usuário admin automaticamente na inicialização.
    Não recria se já existir.
    """

    admin_email = settings.ADMIN_EMAIL
    admin_password = settings.ADMIN_PASSWORD

    if not admin_email or not admin_password:
        print("[ADMIN SEED] ADMIN_EMAIL ou ADMIN_PASSWORD não definidos")
        return

    conn = None

    try:
        conn = get_sync_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Verifica se admin já existe
        cursor.execute(
            "SELECT id FROM users WHERE email = %s",
            (admin_email,)
        )

        existing = cursor.fetchone()
        if existing:
            print("[ADMIN SEED] Admin já existe, pulando seed")
            return

        # Gera hash seguro
        password_hash = bcrypt.hashpw(
            admin_password.encode("utf-8"),
            bcrypt.gensalt(12)
        ).decode("utf-8")

        # Cria admin
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
        print(f"[ADMIN SEED ERROR] {e}")
        if conn:
            conn.rollback()

    finally:
        if conn:
            conn.close()
