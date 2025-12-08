# db_init.py
import os
import asyncio
import asyncpg
import bcrypt
from dotenv import load_dotenv

load_dotenv()

NEON_URL = os.getenv("NEON_DATABASE_URL")
if not NEON_URL:
    raise SystemExit("NEON_DATABASE_URL not set")

USERS = [
    ("user1@exemplo.com", "Senha1!"),
    ("user2@exemplo.com", "Senha2!"),
    ("user3@exemplo.com", "Senha3!"),
]

SQL = """
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email text UNIQUE NOT NULL,
  password_hash text NOT NULL,
  role text NOT NULL DEFAULT 'user',
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NULL REFERENCES users(id) ON DELETE CASCADE,
  started_at timestamptz DEFAULT now(),
  last_active timestamptz DEFAULT now(),
  ip text,
  user_agent text
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);

CREATE TABLE IF NOT EXISTS events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NULL REFERENCES users(id) ON DELETE SET NULL,
  event_type text NOT NULL,
  meta jsonb NULL,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_events_event_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at);
"""

async def main():
    conn = await asyncpg.connect(NEON_URL)
    try:
        await conn.execute(SQL)
        print("Schemas created/checked")

        for email, plain in USERS:
            row = await conn.fetchrow("SELECT id FROM users WHERE email=$1", email)
            if row:
                print(f"{email} exists — skipping")
                continue
            hashed = bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()
            await conn.execute(
                "INSERT INTO users (email, password_hash, role) VALUES ($1, $2, $3)",
                email, hashed, "admin" if email == USERS[0][0] else "user"
            )
            print(f"Inserted user: {email}")

    finally:
        await conn.close()
        print("Done")

if __name__ == "__main__":
    asyncio.run(main())
