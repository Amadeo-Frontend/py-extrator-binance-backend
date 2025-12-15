# utils/admin_seed.py

import bcrypt
from core.config import settings


def hash_password(password: str) -> str:
    """
    Gera hash seguro da senha usando bcrypt.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def seed_admin(conn):
    """
    Cria o usuário ADMIN automaticamente se não existir.
    Usa conexão síncrona psycopg2 (compatível com Neon / Render).
    """

    admin_email = settings.ADMIN_EMAIL
    admin_password = settings.ADMIN_PASSWORD

    if not admin_email or not admin_password:
        raise ValueError("ADMIN_EMAIL ou ADMIN_PASSWORD não definidos nas envs")

    cursor = conn.cursor()

    # Verifica se já existe admin
    cursor.execute(
        "SELECT id FROM users WHERE role = %s LIMIT 1",
        ("admin",),
    )
    exists = cursor.fetchone()

    if exists:
        print("[SEED] Admin já existe. Nenhuma ação necessária.")
        return

    password_hash = hash_password(admin_password)

    cursor.execute(
        """
        INSERT INTO users (email, password, role, is_active)
        VALUES (%s, %s, %s, %s)
        """,
        (
            admin_email,
            password_hash,
            "admin",
            True,
        ),
    )

    conn.commit()
    print(f"[SEED] Admin criado com sucesso: {admin_email}")
