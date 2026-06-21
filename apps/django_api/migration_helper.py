import os
import psycopg

env_file = '../../.env'
db_url = 'postgresql://postgres:postgres@127.0.0.1:5432/alignment_checker'
if os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            if line.startswith('DATABASE_URL='):
                db_url = line.strip().split('=', 1)[1]
                db_url = db_url.replace('localhost', '127.0.0.1')

if db_url and db_url.startswith('postgresql+asyncpg://'):
    db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')

print(f"Connecting to {db_url}")

with psycopg.connect(db_url) as conn:
    with conn.cursor() as cur:
        # Check if users table exists
        cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')")
        exists = cur.fetchone()[0]
        if exists:
            print("Renaming users to users_old...")
            cur.execute("ALTER TABLE users RENAME TO users_old")
            conn.commit()
            print("Renamed successfully.")
        else:
            print("users table does not exist or already renamed.")
