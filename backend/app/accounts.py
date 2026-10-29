"""Accounts, profile, shelves, liked/avoided ingredients, analysis history, personal match score,
product contributions and the admin approval queue. All routes live under /api and are registered
by register(app, db) from main.py.

Security notes (also in the README):
* Passwords are hashed with scrypt; tokens are signed JWTs sent in an "Authorization: Bearer" header.
* Every query uses ? placeholders (no SQL injection); every user-owned row is filtered by the token's user id.
* Login attempts are throttled per email. Admin-only routes check users.is_admin on the server.
"""
import json
import re
import time
from functools import wraps

from flask import jsonify, request

from app import auth
from app import match as match_mod
from app import recommend as rec
from app.analyzer import load_catalog, match_ingredient
from app.normalize import split_ingredient_list

EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]+\.[^@\s]{2,}$")
SHELVES = ("own", "want", "used")
CONTRIB_CATEGORIES = ["lipstick", "foundation", "moisturiser", "sunscreen", "serum", "cleanser", "shampoo", "mascara"]
MAX_PENDING_PER_USER = 5
MAX_HISTORY = 50
_fails = {}  # email -> list of failed-login timestamps (in memory; resets when the server restarts)


def err(message, status=400):
    return jsonify({"error": message}), status


def user_json(u):
    return {"id": u["id"], "email": u["email"], "display_name": u["display_name"], "is_admin": bool(u["is_admin"])}


def profile_json(u):
    return {"skin_type": u["skin_type"] or "", "concerns": json.loads(u["concerns"] or "[]"),
            "allergies": json.loads(u["allergies"] or "[]"), "avoid_text": u["avoid_text"] or "", "pregnant": bool(u["pregnant"])}


def save_history(conn, user_id, text, result):
    """Store one analysis for a user and keep only their newest MAX_HISTORY."""
    v = result.get("verdict") or {}
    conn.execute("INSERT INTO analyses (user_id, text, verdict, total, recognised) VALUES (?,?,?,?,?)",
                 (user_id, text[:8000], v.get("label") if isinstance(v, dict) else str(v),
                  result.get("total"), result.get("recognised_count")))
    conn.execute("DELETE FROM analyses WHERE user_id=? AND id NOT IN (SELECT id FROM analyses WHERE user_id=? ORDER BY id DESC LIMIT ?)",
                 (user_id, user_id, MAX_HISTORY))
    conn.commit()


def user_from_request(conn):
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    uid = auth.read_token(header[7:].strip())
    if uid is None:
        return None
    return conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()


def register(app, db):
    def needs_login(admin=False):
        """Decorator: opens a connection, finds the user, and passes (conn, user) to the view."""
        def deco(fn):
            @wraps(fn)
            def wrapper(*args, **kwargs):
                conn = db()
                try:
                    user = user_from_request(conn)
                    if not user:
                        return err("Please log in.", 401)
                    if admin and not user["is_admin"]:
                        return err("Admins only.", 403)
                    return fn(conn, user, *args, **kwargs)
                finally:
                    conn.close()
            return wrapper
        return deco

    # ------------------------------------------------------------ signup / login
    @app.post("/api/auth/signup")
    def signup():
        d = request.get_json(silent=True) or {}
        email = str(d.get("email") or "").strip().lower()
        name = str(d.get("display_name") or "").strip()
        password = str(d.get("password") or "")
        if not EMAIL_RE.match(email) or len(email) > 254:
            return err("Enter a valid email address.")
        if not 1 <= len(name) <= 40:
            return err("Enter a display name (up to 40 characters).")
        if not 8 <= len(password) <= 128:
            return err("Password must be 8 to 128 characters.")
        conn = db()
        try:
            if conn.execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone():
                return err("An account with this email already exists.", 409)
            cur = conn.execute("INSERT INTO users (email, display_name, password_hash) VALUES (?,?,?)",
                               (email, name, auth.hash_password(password)))
            conn.commit()
            user = conn.execute("SELECT * FROM users WHERE id=?", (cur.lastrowid,)).fetchone()
            return {"token": auth.create_token(user["id"]), "user": user_json(user)}, 201
        finally:
            conn.close()

    @app.post("/api/auth/login")
    def login():
        d = request.get_json(silent=True) or {}
        email = str(d.get("email") or "").strip().lower()
        password = str(d.get("password") or "")
        now = time.time()
        recent = [t for t in _fails.get(email, []) if now - t < 600]
        if len(recent) >= 5:
            return err("Too many failed attempts. Try again in 10 minutes.", 429)
        conn = db()
        try:
            user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
            ok = auth.verify_password(password, user["password_hash"] if user else auth.DUMMY_HASH)
            if not user or not ok:
                _fails[email] = recent + [now]
                return err("Wrong email or password.", 401)
            _fails.pop(email, None)
            return {"token": auth.create_token(user["id"]), "user": user_json(user)}
        finally:
            conn.close()

    @app.get("/api/me")
    @needs_login()
    def me(conn, user):
        return {"user": user_json(user), "profile": profile_json(user)}

    @app.delete("/api/me")
    @needs_login()
    def delete_me(conn, user):
        d = request.get_json(silent=True) or {}
        if not auth.verify_password(str(d.get("password") or ""), user["password_hash"]):
            return err("Password is incorrect.", 403)
        conn.execute("DELETE FROM products WHERE submitted_by=? AND status!='approved'", (user["id"],))
        conn.execute("DELETE FROM product_ingredients WHERE product_id NOT IN (SELECT id FROM products)")
        conn.execute("UPDATE products SET submitted_by=NULL WHERE submitted_by=?", (user["id"],))
        conn.execute("DELETE FROM users WHERE id=?", (user["id"],))
        conn.commit()
        return {"deleted": True}

    # ------------------------------------------------------------ profile
    @app.put("/api/me/profile")
    @needs_login()
    def update_profile(conn, user):
        d = request.get_json(silent=True) or {}
        skin = str(d.get("skin_type") or "").strip().lower()
        concerns = [str(c).strip().lower() for c in (d.get("concerns") or [])]
        allergies = list(d.get("allergies") or [])
        avoid_text = str(d.get("avoid_text") or "")[:300]
        valid = {r["name"] for r in conn.execute("SELECT name FROM concerns")}
        if skin and skin not in rec.SKIN_TYPES:
            return err("Choose a skin type from: " + ", ".join(rec.SKIN_TYPES) + ".")
        if any(c not in valid for c in concerns) or len(set(concerns)) > 4:
            return err("Choose up to 4 valid concerns.")
        if any(a not in rec.ALLERGY_OPTIONS for a in allergies):
            return err("Unknown avoid option.")
        conn.execute("UPDATE users SET skin_type=?, concerns=?, allergies=?, avoid_text=?, pregnant=? WHERE id=?",
                     (skin, json.dumps(list(dict.fromkeys(concerns))), json.dumps(list(dict.fromkeys(allergies))),
                      avoid_text, 1 if d.get("pregnant") else 0, user["id"]))
        conn.commit()
        return {"profile": profile_json(conn.execute("SELECT * FROM users WHERE id=?", (user["id"],)).fetchone())}

    # ------------------------------------------------------------ shelves
    @app.get("/api/me/shelves")
    @needs_login()
    def get_shelves(conn, user):
        out = {s: [] for s in SHELVES}
        for r in conn.execute("""SELECT p.id, p.name, p.brand, p.category, p.price, up.shelf FROM user_products up
                                 JOIN products p ON p.id = up.product_id WHERE up.user_id=? AND p.status='approved'
                                 ORDER BY up.created_at DESC""", (user["id"],)):
            out[r["shelf"]].append({k: r[k] for k in ("id", "name", "brand", "category", "price")})
        return out

    @app.put("/api/me/shelves/<int:pid>")
    @needs_login()
    def set_shelf(conn, user, pid):
        shelf = (request.get_json(silent=True) or {}).get("shelf")
        if shelf not in SHELVES:
            return err("Shelf must be own, want or used.")
        if not conn.execute("SELECT 1 FROM products WHERE id=? AND status='approved'", (pid,)).fetchone():
            return err("Product not found.", 404)
        conn.execute("INSERT INTO user_products (user_id, product_id, shelf) VALUES (?,?,?) "
                     "ON CONFLICT(user_id, product_id) DO UPDATE SET shelf=excluded.shelf", (user["id"], pid, shelf))
        conn.commit()
        return {"product_id": pid, "shelf": shelf}

    @app.delete("/api/me/shelves/<int:pid>")
    @needs_login()
    def remove_shelf(conn, user, pid):
        conn.execute("DELETE FROM user_products WHERE user_id=? AND product_id=?", (user["id"], pid))
        conn.commit()
        return {"removed": True}

    # ------------------------------------------------------------ liked / avoided ingredients
    @app.get("/api/me/ingredients")
    @needs_login()
    def get_ingredients(conn, user):
        out = {"liked": [], "avoided": []}
        for r in conn.execute("""SELECT i.id, i.inci_name, ui.kind FROM user_ingredients ui JOIN ingredients i ON i.id = ui.ingredient_id
                                 WHERE ui.user_id=? ORDER BY i.inci_name""", (user["id"],)):
            out[r["kind"]].append({"id": r["id"], "inci_name": r["inci_name"]})
        return out

    @app.put("/api/me/ingredients/<int:iid>")
    @needs_login()
    def set_ingredient(conn, user, iid):
        kind = (request.get_json(silent=True) or {}).get("kind")
        if kind not in ("liked", "avoided"):
            return err("Kind must be liked or avoided.")
        if not conn.execute("SELECT 1 FROM ingredients WHERE id=?", (iid,)).fetchone():
            return err("Ingredient not found.", 404)
        conn.execute("INSERT INTO user_ingredients (user_id, ingredient_id, kind) VALUES (?,?,?) "
                     "ON CONFLICT(user_id, ingredient_id) DO UPDATE SET kind=excluded.kind", (user["id"], iid, kind))
        conn.commit()
        return {"ingredient_id": iid, "kind": kind}

    @app.delete("/api/me/ingredients/<int:iid>")
    @needs_login()
    def remove_ingredient(conn, user, iid):
        conn.execute("DELETE FROM user_ingredients WHERE user_id=? AND ingredient_id=?", (user["id"], iid))
        conn.commit()
        return {"removed": True}

    # ------------------------------------------------------------ analysis history
    @app.get("/api/me/history")
    @needs_login()
    def history(conn, user):
        rows = conn.execute("SELECT id, substr(text,1,120) AS preview, verdict, total, recognised, created_at FROM analyses "
                            "WHERE user_id=? ORDER BY id DESC", (user["id"],))
        return {"history": [dict(r) for r in rows]}

    @app.get("/api/me/history/<int:hid>")
    @needs_login()
    def history_one(conn, user, hid):
        r = conn.execute("SELECT * FROM analyses WHERE id=? AND user_id=?", (hid, user["id"])).fetchone()
        return dict(r) if r else err("Not found.", 404)

    @app.delete("/api/me/history/<int:hid>")
    @needs_login()
    def history_delete(conn, user, hid):
        conn.execute("DELETE FROM analyses WHERE id=? AND user_id=?", (hid, user["id"]))
        conn.commit()
        return {"removed": True}

    # ------------------------------------------------------------ personal match score
    @app.get("/api/products/<int:pid>/match")
    @needs_login()
    def product_match(conn, user, pid):
        if not conn.execute("SELECT 1 FROM products WHERE id=? AND status='approved'", (pid,)).fetchone():
            return err("Product not found.", 404)
        ings = {"liked": set(), "avoided": set()}
        for r in conn.execute("SELECT ingredient_id, kind FROM user_ingredients WHERE user_id=?", (user["id"],)):
            ings[r["kind"]].add(r["ingredient_id"])
        return match_mod.match_score(conn, profile_json(user), ings["liked"], ings["avoided"], pid)

    # ------------------------------------------------------------ contributions
    def resolve_rows(catalog, text):
        out = []
        for pos, raw in enumerate(split_ingredient_list(text)[:200], start=1):
            ing, _how, _s, _m = match_ingredient(raw, catalog)
            out.append((pos, ing["id"] if ing else None, raw[:100]))
        return out

    @app.post("/api/contributions")
    @needs_login()
    def contribute(conn, user):
        d = request.get_json(silent=True) or {}
        name, brand = str(d.get("name") or "").strip(), str(d.get("brand") or "").strip()
        category, size = str(d.get("category") or "").strip().lower(), str(d.get("size") or "").strip()[:20]
        text = str(d.get("ingredients") or "").strip()
        if not 3 <= len(name) <= 80 or not 2 <= len(brand) <= 60:
            return err("Enter the product name (3-80 characters) and brand (2-60 characters).")
        if category not in CONTRIB_CATEGORIES:
            return err("Choose a product type from the list.")
        if len(text) > 8000 or len(split_ingredient_list(text)) < 3:
            return err("Paste the full ingredient list (at least 3 ingredients, separated by commas).")
        price = d.get("price")
        if price not in (None, ""):
            try:
                price = float(price)
                if not 0 <= price <= 100000:
                    raise ValueError
            except (TypeError, ValueError):
                return err("Price must be a number between 0 and 100000.")
        else:
            price = None
        if conn.execute("SELECT 1 FROM products WHERE lower(name)=lower(?) AND lower(brand)=lower(?) AND status!='rejected'", (name, brand)).fetchone():
            return err("This product is already in the database or waiting for review.", 409)
        if conn.execute("SELECT COUNT(*) FROM products WHERE submitted_by=? AND status='pending'", (user["id"],)).fetchone()[0] >= MAX_PENDING_PER_USER:
            return err(f"You already have {MAX_PENDING_PER_USER} submissions waiting for review.", 429)
        catalog = load_catalog(conn)
        cur = conn.execute("INSERT INTO products (name, brand, category, size, price, image, is_sample_data, status, submitted_by) "
                           "VALUES (?,?,?,?,?,?,0,'pending',?)", (name, brand, category, size, price, category, user["id"]))
        for pos, iid, raw in resolve_rows(catalog, text):
            conn.execute("INSERT INTO product_ingredients VALUES (?,?,?,?)", (cur.lastrowid, pos, iid, raw))
        conn.commit()
        return {"id": cur.lastrowid, "status": "pending", "message": "Thank you! An admin will review it soon."}, 201

    @app.get("/api/me/contributions")
    @needs_login()
    def my_contributions(conn, user):
        prods = [dict(r) for r in conn.execute("SELECT id, name, brand, category, status FROM products WHERE submitted_by=? ORDER BY id DESC", (user["id"],))]
        sugg = [dict(r) for r in conn.execute("""SELECT s.id, s.product_id, p.name AS product_name, s.message, s.status FROM edit_suggestions s
                                                 JOIN products p ON p.id = s.product_id WHERE s.user_id=? ORDER BY s.id DESC""", (user["id"],))]
        return {"products": prods, "suggestions": sugg}

    @app.post("/api/products/<int:pid>/suggest-edit")
    @needs_login()
    def suggest_edit(conn, user, pid):
        d = request.get_json(silent=True) or {}
        message = str(d.get("message") or "").strip()
        new_ing = str(d.get("ingredients") or "").strip()
        if not 5 <= len(message) <= 500:
            return err("Describe the problem in 5 to 500 characters.")
        if len(new_ing) > 8000 or (new_ing and len(split_ingredient_list(new_ing)) < 3):
            return err("If you add a corrected ingredient list, include at least 3 ingredients.")
        if not conn.execute("SELECT 1 FROM products WHERE id=? AND status='approved'", (pid,)).fetchone():
            return err("Product not found.", 404)
        if conn.execute("SELECT COUNT(*) FROM edit_suggestions WHERE user_id=? AND status='pending'", (user["id"],)).fetchone()[0] >= 10:
            return err("You have too many suggestions waiting for review.", 429)
        cur = conn.execute("INSERT INTO edit_suggestions (user_id, product_id, message, new_ingredients) VALUES (?,?,?,?)",
                           (user["id"], pid, message, new_ing))
        conn.commit()
        return {"id": cur.lastrowid, "status": "pending"}, 201

    # ------------------------------------------------------------ admin queue
    @app.get("/api/admin/pending")
    @needs_login(admin=True)
    def admin_pending(conn, user):
        products = []
        for p in conn.execute("""SELECT p.*, u.display_name AS who FROM products p LEFT JOIN users u ON u.id = p.submitted_by
                                 WHERE p.status='pending' ORDER BY p.id"""):
            ing = [r["raw_name"] for r in conn.execute("SELECT raw_name FROM product_ingredients WHERE product_id=? ORDER BY position", (p["id"],))]
            unknown = [r["raw_name"] for r in conn.execute("SELECT raw_name FROM product_ingredients WHERE product_id=? AND ingredient_id IS NULL", (p["id"],))]
            products.append({"id": p["id"], "name": p["name"], "brand": p["brand"], "category": p["category"], "price": p["price"],
                             "submitted_by": p["who"], "ingredients": ing, "unrecognised": unknown})
        sugg = [dict(r) for r in conn.execute("""SELECT s.id, s.product_id, p.name AS product_name, s.message, s.new_ingredients, u.display_name AS who
                                                 FROM edit_suggestions s JOIN products p ON p.id = s.product_id JOIN users u ON u.id = s.user_id
                                                 WHERE s.status='pending' ORDER BY s.id""")]
        return {"products": products, "suggestions": sugg}

    @app.post("/api/admin/products/<int:pid>/<action>")
    @needs_login(admin=True)
    def admin_product(conn, user, pid, action):
        if action not in ("approve", "reject"):
            return err("Unknown action.", 404)
        cur = conn.execute("UPDATE products SET status=? WHERE id=? AND status='pending'",
                           ("approved" if action == "approve" else "rejected", pid))
        conn.commit()
        return ({"id": pid, "status": "approved" if action == "approve" else "rejected"}) if cur.rowcount else err("No pending product with that id.", 404)

    @app.post("/api/admin/suggestions/<int:sid>/<action>")
    @needs_login(admin=True)
    def admin_suggestion(conn, user, sid, action):
        if action not in ("approve", "reject"):
            return err("Unknown action.", 404)
        s = conn.execute("SELECT * FROM edit_suggestions WHERE id=? AND status='pending'", (sid,)).fetchone()
        if not s:
            return err("No pending suggestion with that id.", 404)
        if action == "approve" and s["new_ingredients"]:
            catalog = load_catalog(conn)
            conn.execute("DELETE FROM product_ingredients WHERE product_id=?", (s["product_id"],))
            for pos, iid, raw in resolve_rows(catalog, s["new_ingredients"]):
                conn.execute("INSERT INTO product_ingredients VALUES (?,?,?,?)", (s["product_id"], pos, iid, raw))
        conn.execute("UPDATE edit_suggestions SET status=? WHERE id=?", ("approved" if action == "approve" else "rejected", sid))
        conn.commit()
        return {"id": sid, "status": "approved" if action == "approve" else "rejected"}
