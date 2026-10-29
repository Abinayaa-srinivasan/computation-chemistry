"""DermaLens API (Flask + sqlite3). Milestone 1: search, product, category and ingredient endpoints."""
import json
import os

from flask import Flask, jsonify, request, abort
from app.db import connect, init_db
from app import analyzer as az
from app import recommend as rec
from app import compare as cmp
from app import routine as rt
from app import accounts

# Fields stored as JSON text in the database
JSON_FIELDS = ("aliases", "categories", "flags", "skin_types", "incompatible_with")


def ingredient_row(r):
    d = dict(r)
    for f in JSON_FIELDS:
        if f in d:
            d[f] = json.loads(d[f])
    d.pop("norm_name", None)
    d["is_sample_data"] = bool(d.get("is_sample_data", 1))
    if d.get("typical_min") is not None or d.get("typical_max") is not None:
        d["range_note"] = "typical range (not the exact amount in any specific product)"
    return d


def create_app(db_path=None):
    static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
    app = Flask(__name__, static_folder=static_dir, static_url_path="/static")

    def db():
        return connect(db_path)

    @app.after_request
    def headers(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        # Always re-check site files, so after you replace the project folder the browser never
        # mixes an old app.js with a new page.
        if request.path == "/" or request.path.startswith("/static/"):
            resp.headers["Cache-Control"] = "no-cache"
        return resp

    @app.get("/")
    def index():
        return app.send_static_file("index.html")

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/search")
    def search():
        """Search products by name/brand, plus matching brands."""
        q = (request.args.get("q") or "").strip()
        limit = min(int(request.args.get("limit", 20)), 50)
        if not q:
            return {"products": [], "brands": []}
        like = f"%{q}%"
        conn = db()
        products = [dict(r) for r in conn.execute(
            """SELECT id, name, brand, category, price, image FROM products
               WHERE status='approved' AND (name LIKE ? OR brand LIKE ?) ORDER BY name LIMIT ?""",
            (like, like, limit))]
        brands = [r[0] for r in conn.execute(
            "SELECT DISTINCT brand FROM products WHERE status='approved' AND brand LIKE ? ORDER BY brand", (like,))]
        conn.close()
        return {"products": products, "brands": brands}

    @app.get("/api/products")
    def list_products():
        category = request.args.get("category")
        brand = request.args.get("brand")
        sql, args = "SELECT id, name, brand, category, price, image FROM products WHERE status='approved'", []
        if category:
            sql += " AND category=?"; args.append(category)
        if brand:
            sql += " AND brand=?"; args.append(brand)
        conn = db()
        rows = [dict(r) for r in conn.execute(sql + " ORDER BY name", args)]
        conn.close()
        return {"products": rows}

    @app.get("/api/products/<int:pid>")
    def product(pid):
        conn = db()
        p = conn.execute("SELECT * FROM products WHERE id=? AND status='approved'", (pid,)).fetchone()
        if not p:
            conn.close(); abort(404)
        ings = []
        for r in conn.execute(
                """SELECT pi.position, pi.raw_name, i.* FROM product_ingredients pi
                   LEFT JOIN ingredients i ON i.id = pi.ingredient_id
                   WHERE pi.product_id=? ORDER BY pi.position""", (pid,)):
            if r["id"] is None:
                ings.append({"position": r["position"], "raw_name": r["raw_name"], "recognised": False})
            else:
                d = ingredient_row(r)
                d["position"], d["raw_name"], d["recognised"] = r["position"], r["raw_name"], True
                ings.append(d)
        links = [dict(r) for r in conn.execute(
            "SELECT retailer, url, price FROM retailer_links WHERE product_id=? ORDER BY price", (pid,))]
        conn.close()
        out = dict(p)
        out["is_sample_data"] = bool(out["is_sample_data"])
        out["ingredients"] = ings
        out["where_to_buy"] = links
        out["cost_note"] = "Demo prices and links; replace with real retailer data."
        return out

    @app.get("/api/categories")
    def categories():
        conn = db()
        rows = [dict(r) for r in conn.execute(
            "SELECT category AS name, COUNT(*) AS product_count FROM products WHERE status='approved' GROUP BY category ORDER BY category")]
        conn.close()
        return {"categories": rows}

    @app.get("/api/categories/<name>")
    def category_detail(name):
        """Basic ingredients for a product type, with typical min/max concentration."""
        conn = db()
        basics = [dict(r) for r in conn.execute(
            """SELECT i.id, i.inci_name, ci.role, ci.typical_min, ci.typical_max, ci.why
               FROM category_ingredients ci JOIN ingredients i ON i.id=ci.ingredient_id
               WHERE ci.category=? ORDER BY ci.typical_max DESC""", (name,))]
        if not basics:
            conn.close(); abort(404)
        prods = [dict(r) for r in conn.execute(
            "SELECT id, name, brand, price, image FROM products WHERE category=? AND status='approved' ORDER BY name", (name,))]
        conn.close()
        return {"category": name, "basic_ingredients": basics, "products": prods,
                "range_note": "Typical ranges for this product type; not the exact amount in any specific product."}

    @app.get("/api/ingredients")
    def ingredients():
        q = (request.args.get("q") or "").strip()
        cat = request.args.get("category")
        sql, args = "SELECT * FROM ingredients WHERE 1=1", []
        if q:
            sql += " AND (inci_name LIKE ? OR aliases LIKE ?)"; args += [f"%{q}%", f"%{q}%"]
        if cat:
            sql += " AND categories LIKE ?"; args.append(f'%"{cat}"%')
        conn = db()
        rows = [ingredient_row(r) for r in conn.execute(sql + " ORDER BY inci_name LIMIT 300", args)]
        conn.close()
        return {"ingredients": rows}

    @app.get("/api/ingredients/<int:iid>")
    def ingredient(iid):
        conn = db()
        r = conn.execute("SELECT * FROM ingredients WHERE id=?", (iid,)).fetchone()
        conn.close()
        if not r:
            abort(404)
        return ingredient_row(r)

    @app.get("/api/ingredient-categories")
    def ingredient_categories():
        conn = db()
        rows = [dict(r) for r in conn.execute("SELECT name, meaning FROM categories ORDER BY name")]
        conn.close()
        return {"categories": rows}

    # ---------------- analyzer ----------------
    @app.post("/api/analyze")
    def analyze_endpoint():
        data = request.get_json(silent=True) or {}
        text = (data.get("text") or "").strip()
        if not text:
            return {"error": "Paste an ingredient list first."}, 400
        if len(text) > 8000:
            return {"error": "That text is too long. Paste just the ingredient list."}, 400
        conn = db()
        try:
            result = az.analyze(conn, text)
            # Logged-in users can ask for the analysis to be saved to their history.
            if data.get("save"):
                user = accounts.user_from_request(conn)
                if user:
                    accounts.save_history(conn, user["id"], text, result)
            return result
        finally:
            conn.close()

    @app.post("/api/ocr")
    def ocr_endpoint():
        f = request.files.get("image")
        if not f:
            return {"error": "No image received."}, 400
        data = f.read(8 * 1024 * 1024 + 1)
        if len(data) > 8 * 1024 * 1024:
            return {"error": "Image is larger than 8 MB. Try a smaller photo."}, 413
        try:
            text = az.ocr_image(data)
        except az.OcrUnavailable as e:
            return {"error": str(e), "hint": "You can still type or paste the ingredient list."}, 501
        except ValueError as e:
            return {"error": str(e)}, 400
        return {"text": text.strip(),
                "note": "OCR can make mistakes. Check the text before analysing."}

    # ---------------- skin-concern recommendations ----------------
    @app.get("/api/concerns")
    def concerns_list():
        conn = db()
        try:
            return {"concerns": rec.list_concerns(conn), **rec.options()}
        finally:
            conn.close()

    @app.post("/api/recommend")
    def recommend_endpoint():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return {"error": "Send the form as JSON."}, 400
        conn = db()
        try:
            return rec.recommend(conn, data)
        except rec.InputError as e:
            return {"error": str(e)}, 400
        finally:
            conn.close()

    # ---------------- compare and dupes ----------------
    @app.post("/api/compare")
    def compare_endpoint():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return {"error": "Send the form as JSON."}, 400
        conn = db()
        try:
            return cmp.compare(conn, data.get("a"), data.get("b"))
        except cmp.CompareError as e:
            return {"error": str(e)}, 400
        finally:
            conn.close()

    @app.get("/api/products/<int:pid>/dupes")
    def dupes_endpoint(pid):
        conn = db()
        try:
            return cmp.find_dupes(conn, pid, cheaper_only=request.args.get("cheaper") in ("1", "true"),
                                  limit=min(int(request.args.get("limit", 10)), 30))
        except cmp.CompareError:
            abort(404)
        finally:
            conn.close()

    # ---------------- routine builder ----------------
    @app.post("/api/routine/check")
    def routine_check():
        data = request.get_json(silent=True)
        conn = db()
        try:
            return rt.check(conn, data)
        except rt.RoutineError as e:
            return {"error": str(e)}, 400
        finally:
            conn.close()

    @app.post("/api/routines")
    def routine_share():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return {"error": "Send the routine as JSON."}, 400
        conn = db()
        try:
            token = rt.save_shared(conn, data.get("name"), data)
            return {"token": token, "path": "#/routine/" + token}, 201
        except rt.RoutineError as e:
            return {"error": str(e)}, 400
        finally:
            conn.close()

    @app.get("/api/routines/<token>")
    def routine_get(token):
        conn = db()
        try:
            r = rt.load_shared(conn, token)
        finally:
            conn.close()
        if not r:
            abort(404)
        return r

    accounts.register(app, db)
    return app


if __name__ == "__main__":
    init_db()
    create_app().run(port=8000, debug=True)
