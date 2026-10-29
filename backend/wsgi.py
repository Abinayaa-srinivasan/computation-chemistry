"""Production entry point:  gunicorn --preload wsgi:app

On the very first start the database is empty, so the sample data is loaded automatically.
Accounts, routines and submissions are kept (the seed is only run when there are no ingredients)."""
from app.db import init_db
from app.main import create_app

_conn = init_db()
if _conn.execute("SELECT COUNT(*) FROM ingredients").fetchone()[0] == 0:
    from seed.load import load
    load(quiet=True)
import os
_admin = os.environ.get("DERMALENS_ADMIN_EMAIL", "").strip().lower()
if _admin:  # makes this user an admin on every start (after they have signed up)
    _conn.execute("UPDATE users SET is_admin=1 WHERE email=?", (_admin,))
    _conn.commit()
_conn.close()

app = create_app()
