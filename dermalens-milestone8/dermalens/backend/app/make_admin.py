"""Make an existing user an admin:  python -m app.make_admin you@example.com"""
import sys

from app.db import init_db

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python -m app.make_admin you@example.com")
    conn = init_db()
    cur = conn.execute("UPDATE users SET is_admin=1 WHERE email=?", (sys.argv[1].strip().lower(),))
    conn.commit()
    print("Done: admin enabled." if cur.rowcount else "No user with that email. Sign up on the site first.")
