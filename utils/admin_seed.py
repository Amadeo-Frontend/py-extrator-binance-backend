import bcrypt
from core.config import settings

def seed_admin(conn):
    email = settings.ADMIN_EMAIL
    password = settings.ADMIN_PASSWORD

    if not email or not password:
        print("[ADMIN SEED] ADMIN_EMAIL ou ADMIN_PASSWORD não definidos")
        return

    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE email = %s",
        (email,)
    )
    exists = cursor.fetchone()

    if exists:
        print("[ADMIN SEED] Admin já existe")
        return

    hashed = bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    ).decode()

    cursor.execute(
        """
        INSERT INTO users (email, password_hash, role)
        VALUES (%s, %s, 'admin')
        """,
        (email, hashed),
    )

    conn.commit()
    print("[ADMIN SEED] Admin criado com sucesso")
