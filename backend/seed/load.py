"""Load sample data into the database.

Usage (from the backend folder):  python -m seed.load
To use REAL data later, write another loader that fills the same tables
(see README, section "Replacing sample data").
"""
import json
import random
import sys
import urllib.parse

from app.db import init_db, DB_PATH
from app.normalize import normalize, split_ingredient_list
from seed.ingredients_data import parse, CATEGORIES
from seed.products_data import PRODUCTS, CATEGORY_BASICS, RETAILERS
from seed.concerns_data import CONCERNS


def load(path=None, quiet=False):
    conn = init_db(path)
    cur = conn.cursor()
    for t in ("user_products", "user_ingredients", "edit_suggestions", "concern_tips", "concern_avoid", "concern_ingredients", "concerns", "category_ingredients", "retailer_links", "product_ingredients", "products",
              "alias_index", "ingredients", "categories"):
        cur.execute(f"DELETE FROM {t}")
    cur.execute("DELETE FROM sqlite_sequence")  # restart ids at 1 so product links stay stable after re-seeding

    for name, meaning in CATEGORIES:
        cur.execute("INSERT INTO categories VALUES (?,?)", (name, meaning))

    lookup = {}
    for ing in parse():
        cur.execute(
            """INSERT INTO ingredients (inci_name, norm_name, aliases, categories, description,
               irritancy, comedogenic, flags, skin_types, incompatible_with,
               typical_min, typical_max, range_source, is_sample_data)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,1)""",
            (ing["inci_name"], normalize(ing["inci_name"]), json.dumps(ing["aliases"]),
             json.dumps(ing["categories"]), ing["description"], ing["irritancy"],
             ing["comedogenic"], json.dumps(ing["flags"]), json.dumps(ing["skin_types"]),
             json.dumps(ing["incompatible_with"]), ing["typical_min"], ing["typical_max"],
             ing["range_source"]))
        iid = cur.lastrowid
        for n in [ing["inci_name"]] + ing["aliases"]:
            lookup.setdefault(normalize(n), iid)
    for alias, iid in lookup.items():
        cur.execute("INSERT INTO alias_index VALUES (?,?)", (alias, iid))

    unknown = []
    rng = random.Random(42)  # deterministic demo prices
    for name, brand, cat, size, price, image, ing_text in PRODUCTS:
        cur.execute("INSERT INTO products (name, brand, category, size, price, image) VALUES (?,?,?,?,?,?)",
                    (name, brand, cat, size, price, image))
        pid = cur.lastrowid
        for pos, raw in enumerate(split_ingredient_list(ing_text), start=1):
            iid = lookup.get(normalize(raw))
            if iid is None:
                unknown.append((name, raw))
            cur.execute("INSERT INTO product_ingredients VALUES (?,?,?,?)", (pid, pos, iid, raw))
        for retailer in RETAILERS:
            q = urllib.parse.quote_plus(f"{brand} {name}")
            url = f"https://www.{retailer.lower()}.com/search?q={q}"  # DEMO search link, not a real listing
            cur.execute("INSERT INTO retailer_links (product_id, retailer, url, price) VALUES (?,?,?,?)",
                        (pid, retailer, url, round(price * rng.uniform(0.92, 1.08))))

    for cat, rows in CATEGORY_BASICS.items():
        for ing_name, role, mn, mx, why in rows:
            iid = lookup.get(normalize(ing_name))
            if iid is None:
                unknown.append((f"category:{cat}", ing_name))
                continue
            cur.execute("INSERT INTO category_ingredients VALUES (?,?,?,?,?,?)",
                        (cat, iid, role, mn, mx, why))
    for cname, c in CONCERNS.items():
        cur.execute("INSERT INTO concerns VALUES (?,?,?)", (cname, c["label"], c["description"]))
        for ing_name, prio, why, how, caution in c["ingredients"]:
            iid = lookup.get(normalize(ing_name))
            if iid is None:
                unknown.append((f"concern:{cname}", ing_name)); continue
            cur.execute("INSERT INTO concern_ingredients VALUES (?,?,?,?,?,?)", (cname, iid, prio, why, how, caution))
        for item, why in c["avoid"]:
            cur.execute("INSERT INTO concern_avoid VALUES (?,?,?)", (cname, item, why))
        for tip in c["tips"]:
            cur.execute("INSERT INTO concern_tips VALUES (?,?)", (cname, tip))
    conn.commit()
    counts = {t: cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
              for t in ("ingredients", "products", "retailer_links", "category_ingredients", "concerns", "concern_ingredients")}
    conn.close()
    if not quiet:
        print("Loaded:", counts)
        if unknown:
            print("Ingredients not found in the ingredient table:", unknown)
    return counts, unknown


if __name__ == "__main__":
    counts, unknown = load()
    print("Database:", DB_PATH)
    sys.exit(1 if unknown else 0)
