# utils/admin_seed.py
import bcrypt
from psycopg2.extras import RealDictCursor
from core.config import settings

def seed_admin(conn):
    admin_email = settings.ADMIN_EMAIL
    admin_password = settings.ADMIN_PASSWORD

    if not admin_email or not admin_password:
        print("[ADMIN SEED] Variáveis não definidas")
        return

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
        VALUES (%s, %s, 'admin')
        """,
        (admin_email, password_hash)
    )

    conn.commit()
    print("[ADMIN SEED] Admin criado com sucesso")
