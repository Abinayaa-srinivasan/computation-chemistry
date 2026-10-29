"""Compare two products (from the database or pasted ingredient lists) and find dupes.

The scoring is deterministic and fully explainable:

SAFETY SCORE (0-100) = 100 minus one penalty per ingredient (the largest that applies):
    12 high irritation (irritancy 4-5)   7 can irritate (irritancy 3)   6 fragrance / essential oil
     5 drying alcohol                     5 may clog pores (comedogenic 4-5)   5 pregnancy caution
     4 sulfate cleanser                   4 common allergen                    3 paraben
    Penalties do not depend on label position: allergens and irritants act at low amounts.
BENEFIT SCORE (0-100) = 2 x the weight points of useful ingredient groups present
    (Skin-identical lipid 10, UV filter 10, Humectant 8, Antioxidant 8, Soothing agent 8, Peptide 6,
     Brightening agent 6, Exfoliant 6, Retinoid 6, Emollient 4), capped at 100.
OVERALL = 0.6 x safety + 0.4 x benefit.  A gap under 4 points is reported as "too close to call".

Ingredients we do not recognise are NOT scored; the result says how many were missed.
"""
from app.analyzer import (KEY_GROUPS, load_catalog, match_ingredient)
from app.normalize import normalize, split_ingredient_list
from app.recommend import position_factor, is_irritant

BENEFIT_WEIGHTS = {"Skin-identical lipid": 10, "UV filter": 10, "Humectant": 8, "Antioxidant": 8, "Soothing agent": 8,
                   "Peptide": 6, "Brightening agent": 6, "Exfoliant": 6, "Retinoid": 6, "Emollient": 4}
TIE_MARGIN = 4.0
HEAVY_OCCLUSIVES = {"Petrolatum", "Mineral Oil", "Cocos Nucifera Oil", "Lanolin"}
OIL_CONTROL = {"Niacinamide", "Salicylic Acid", "Zinc PCA", "Silica", "Kaolin", "Benzoyl Peroxide"}


class CompareError(ValueError):
    pass


# ------------------------------------------------------------------ resolving the two sides
def resolve_side(conn, catalog, spec, label):
    """spec = {"product_id": n} or {"text": "..."}.  Returns {"title", "rows"} with rows = [(pos, ing|None, raw)]."""
    if not isinstance(spec, dict):
        raise CompareError(f"Choose a product or paste a list for product {label}.")
    if spec.get("product_id") not in (None, ""):
        try:
            pid = int(spec["product_id"])
        except (TypeError, ValueError):
            raise CompareError(f"Product {label}: invalid product.")
        p = conn.execute("SELECT * FROM products WHERE id=? AND status='approved'", (pid,)).fetchone()
        if not p:
            raise CompareError(f"Product {label} was not found.")
        rows = [(r["position"], catalog["ingredients"].get(r["ingredient_id"]), r["raw_name"]) for r in conn.execute(
            "SELECT position, ingredient_id, raw_name FROM product_ingredients WHERE product_id=? ORDER BY position", (pid,))]
        return {"title": p["name"], "brand": p["brand"], "category": p["category"], "price": p["price"],
                "product_id": pid, "rows": rows}
    text = (spec.get("text") or "").strip()
    if not text:
        raise CompareError(f"Choose a product or paste an ingredient list for product {label}.")
    if len(text) > 8000:
        raise CompareError(f"The list for product {label} is too long.")
    names = split_ingredient_list(text)[:200]
    if len(names) < 2:
        raise CompareError(f"Product {label}: the list needs at least 2 ingredients separated by commas.")
    rows = []
    for pos, raw in enumerate(names, start=1):
        ing, _how, _s, _m = match_ingredient(raw, catalog)
        rows.append((pos, ing, raw))
    return {"title": spec.get("name") or f"Pasted list {label}", "brand": None, "category": None, "price": None,
            "product_id": None, "rows": rows}


# ------------------------------------------------------------------ scoring one product
def ingredient_penalty(ing):
    """(points, reason) for the single biggest concern about an ingredient, or (0, '')."""
    options = []
    if ing["irritancy"] >= 4:
        options.append((12, "high irritation potential"))
    elif ing["irritancy"] == 3:
        options.append((7, "can irritate skin"))
    if "fragrance" in ing["flags"] or "essential_oil" in ing["flags"]:
        options.append((6, "fragrance or essential oil"))
    if "drying_alcohol" in ing["flags"]:
        options.append((5, "drying alcohol"))
    if ing["comedogenic"] >= 4:
        options.append((5, "may clog pores"))
    if "pregnancy_caution" in ing["flags"]:
        options.append((5, "pregnancy caution"))
    if "sulfate" in ing["flags"]:
        options.append((4, "sulfate cleanser"))
    if "allergen" in ing["flags"]:
        options.append((4, "common allergen"))
    if "paraben" in ing["flags"]:
        options.append((3, "paraben"))
    return max(options) if options else (0, "")


def skin_type_fit(members, concern_scores):
    """Rule-based suitability for each skin type, with a one-line reason."""
    ings = [i for _, i in members]
    names = {i["inci_name"] for i in ings}
    irritants = [i["inci_name"] for i in ings if is_irritant(i) or "drying_alcohol" in i["flags"]]
    clog = [i["inci_name"] for i in ings if i["comedogenic"] >= 4]
    heavy = [i["inci_name"] for pos, i in members if i["inci_name"] in HEAVY_OCCLUSIVES and pos <= 10]
    hydrating = [i["inci_name"] for i in ings if {"Humectant", "Emollient", "Skin-identical lipid"} & set(i["categories"])
                 and i["inci_name"] != "Water"]
    drying = [i["inci_name"] for i in ings if "drying_alcohol" in i["flags"] or "sulfate" in i["flags"]]
    oil_ctrl = sorted(names & OIL_CONTROL)
    out = []

    def add(t, ok, why):
        out.append({"skin_type": t, "suitable": ok, "reason": why})
    add("sensitive", not irritants, "No fragrance, drying alcohol or strong irritants found." if not irritants
        else "Contains " + ", ".join(irritants[:3]) + ", which can bother sensitive skin.")
    add("dry", len(hydrating) >= 2 and not drying,
        ("Has hydrating ingredients (" + ", ".join(hydrating[:3]) + ") and nothing drying.") if len(hydrating) >= 2 and not drying
        else ("Contains drying ingredients: " + ", ".join(drying[:3]) + ".") if drying else "Few hydrating ingredients.")
    add("oily", not clog and not heavy,
        ("Light formula" + (" with oil control (" + ", ".join(oil_ctrl[:2]) + ")." if oil_ctrl else "."))
        if not clog and not heavy else "May feel heavy or clog pores: " + ", ".join(dict.fromkeys(clog + heavy)) + ".")
    add("combination", not clog and not heavy and bool(hydrating), "Balanced: not heavy, with some hydration." if not clog and not heavy and hydrating
        else "Too heavy or too plain for combination skin.")
    add("acne-prone", not clog, "No high pore-clogging ingredients found." if not clog else "Contains pore-clogging ingredients: " + ", ".join(clog[:3]) + ".")
    return out


def profile(rows, concern_table):
    members = [(pos, ing) for pos, ing, _raw in rows if ing]
    unknown = [raw for _pos, ing, raw in rows if not ing]
    penalties = []
    for pos, ing in members:
        pts, why = ingredient_penalty(ing)
        if pts:
            penalties.append({"inci_name": ing["inci_name"], "points": pts, "reason": why, "position": pos})
    safety = max(0, 100 - sum(p["points"] for p in penalties))
    groups = {}
    for _, ing in members:
        for c in ing["categories"]:
            groups.setdefault(c, []).append(ing["inci_name"])
    for g in groups:
        groups[g] = list(dict.fromkeys(groups[g]))
    benefit_pts = sum(w for g, w in BENEFIT_WEIGHTS.items() if g in groups)
    benefit = min(100, benefit_pts * 2)
    overall = round(0.6 * safety + 0.4 * benefit, 1)
    # how well it fits each concern: priority x position factor, summed
    concern_scores = {}
    for concern, prios in concern_table.items():
        s = sum(prios[i["id"]] * position_factor(pos) for pos, i in members if i["id"] in prios)
        if s:
            concern_scores[concern] = round(s, 1)
    top_concerns = sorted(((c, s) for c, s in concern_scores.items() if s >= 3), key=lambda x: -x[1])[:3]
    return {
        "safety": safety, "benefit": benefit, "overall": overall, "penalties": sorted(penalties, key=lambda p: -p["points"]),
        "groups": {g: groups[g] for g in KEY_GROUPS if g in groups}, "category_counts": {g: len(v) for g, v in sorted(groups.items())},
        "irritant_count": sum(1 for _, i in members if i["irritancy"] >= 3),
        "allergen_count": sum(1 for _, i in members if "allergen" in i["flags"]),
        "fragrance_count": sum(1 for _, i in members if "fragrance" in i["flags"] or "essential_oil" in i["flags"]),
        "comedogenic_high": [i["inci_name"] for _, i in members if i["comedogenic"] >= 4],
        "max_comedogenic": max([i["comedogenic"] for _, i in members] or [0]),
        "recognised": len(members), "total": len(rows), "unknown": unknown,
        "skin_fit": skin_type_fit(members, concern_scores),
        "best_for_skin": [f["skin_type"] for f in skin_type_fit(members, concern_scores) if f["suitable"]],
        "helps_concerns": [{"concern": c, "score": s} for c, s in top_concerns],
    }


def load_concern_table(conn):
    table, labels = {}, {}
    for r in conn.execute("SELECT name, label FROM concerns"):
        labels[r["name"]] = r["label"]
    for r in conn.execute("SELECT concern, ingredient_id, priority FROM concern_ingredients"):
        table.setdefault(r["concern"], {})[r["ingredient_id"]] = r["priority"]
    return table, labels


# ------------------------------------------------------------------ comparing
def _names(rows):
    """label name -> display name for every ingredient (recognised ones by INCI name)."""
    out = {}
    for _pos, ing, raw in rows:
        key = ("i", ing["id"]) if ing else ("u", normalize(raw))
        out.setdefault(key, ing["inci_name"] if ing else raw)
    return out


def _explain(a, b, pa, pb):
    ta, tb = a["title"], b["title"]
    reasons = []
    diff_safety = pa["safety"] - pb["safety"]
    if abs(diff_safety) >= 3:
        worse, pw, better = (tb, pb, ta) if diff_safety > 0 else (ta, pa, tb)
        top = pw["penalties"][:3]
        reasons.append(f"Safety: {better} scores {max(pa['safety'], pb['safety'])} vs {min(pa['safety'], pb['safety'])}. "
                       f"{worse} loses points for " + "; ".join(f"{p['inci_name']} ({p['reason']})" for p in top) + ".")
    else:
        reasons.append(f"Safety is about equal ({pa['safety']} vs {pb['safety']}).")
    only_a = [g for g in BENEFIT_WEIGHTS if g in pa["groups"] and g not in pb["groups"]]
    only_b = [g for g in BENEFIT_WEIGHTS if g in pb["groups"] and g not in pa["groups"]]
    if only_a:
        reasons.append(f"{ta} has benefits that {tb} lacks: " + ", ".join(f"{g.lower()} ({', '.join(pa['groups'][g][:2])})" for g in only_a[:4]) + ".")
    if only_b:
        reasons.append(f"{tb} has benefits that {ta} lacks: " + ", ".join(f"{g.lower()} ({', '.join(pb['groups'][g][:2])})" for g in only_b[:4]) + ".")
    if not only_a and not only_b:
        reasons.append("Both cover the same kinds of useful ingredients.")
    return reasons


def compare(conn, spec_a, spec_b):
    catalog = load_catalog(conn)
    a = resolve_side(conn, catalog, spec_a, "A")
    b = resolve_side(conn, catalog, spec_b, "B")
    if a["product_id"] and a["product_id"] == b["product_id"]:
        raise CompareError("Pick two different products.")
    table, labels = load_concern_table(conn)
    pa, pb = profile(a["rows"], table), profile(b["rows"], table)
    for p in (pa, pb):
        for h in p["helps_concerns"]:
            h["label"] = labels[h["concern"]]

    na, nb = _names(a["rows"]), _names(b["rows"])
    shared = [na[k] for k in na if k in nb]
    only_a = [na[k] for k in na if k not in nb]
    only_b = [nb[k] for k in nb if k not in na]

    gap = round(pa["overall"] - pb["overall"], 1)
    if abs(gap) < TIE_MARGIN:
        winner, headline = "tie", "Too close to call: both score about the same."
    elif gap > 0:
        winner, headline = "a", f"Better overall: {a['title']}"
    else:
        winner, headline = "b", f"Better overall: {b['title']}"
    notes = []
    if a["category"] and b["category"] and a["category"] != b["category"]:
        notes.append(f"These are different product types ({a['category']} vs {b['category']}), so the comparison is only a rough guide.")
    for side, p in (("A", pa), ("B", pb)):
        if p["total"] and len(p["unknown"]) / p["total"] >= 0.3:
            notes.append(f"{len(p['unknown'])} of {p['total']} ingredients in product {side} were not recognised, so its score is less certain.")
    def choose(t, p, other):
        parts = []
        if len(p["best_for_skin"]) == 5:
            parts.append("you have any skin type, including sensitive")
        elif p["best_for_skin"]:
            parts.append("your skin is " + ", ".join(p["best_for_skin"]))
        if p["helps_concerns"]:
            parts.append("you want help with " + ", ".join(h["label"].lower() for h in p["helps_concerns"]))
        return f"Choose {t} if " + (" and ".join(parts) if parts else "you want a basic formula") + "."
    return {
        "winner": winner, "headline": headline, "score_gap": gap, "reasons": _explain(a, b, pa, pb), "notes": notes,
        "choose": [choose(a["title"], pa, pb), choose(b["title"], pb, pa)],
        "a": {k: a[k] for k in ("title", "brand", "category", "price", "product_id")} | {"profile": pa},
        "b": {k: b[k] for k in ("title", "brand", "category", "price", "product_id")} | {"profile": pb},
        "shared": shared, "only_a": only_a, "only_b": only_b,
        "method": "Overall = 0.6 x safety + 0.4 x benefit. Safety starts at 100 and loses points per ingredient of concern; "
                  "benefit rewards useful ingredient groups. Gaps under 4 points are called a tie.",
        "disclaimer": "Educational comparison, not medical advice. Ingredient lists do not show exact amounts.",
    }


# ------------------------------------------------------------------ dupes
TAGS = ["fragrance", "essential_oil", "sulfate", "paraben", "silicone", "drying_alcohol"]


def _tag_set(members):
    present = set()
    for _, i in members:
        present |= set(i["flags"]) & set(TAGS)
    return present


def _jaccard(x, y):
    return len(x & y) / len(x | y) if (x | y) else 0.0


def find_dupes(conn, product_id, cheaper_only=False, limit=10):
    catalog = load_catalog(conn)
    base = conn.execute("SELECT * FROM products WHERE id=? AND status='approved'", (product_id,)).fetchone()
    if not base:
        raise CompareError("Product not found.")
    rows_by = {}
    for r in conn.execute("""SELECT product_id, position, ingredient_id, raw_name FROM product_ingredients ORDER BY product_id, position"""):
        rows_by.setdefault(r["product_id"], []).append((r["position"], catalog["ingredients"].get(r["ingredient_id"]), r["raw_name"]))

    def keyset(rows):  # ingredient identity, ignoring water (every product has it)
        out = set()
        for _p, ing, raw in rows:
            name = ing["inci_name"] if ing else normalize(raw)
            if name != "Water":
                out.add(name)
        return out

    def info(pid):
        rows = rows_by[pid]
        members = [(p, i) for p, i, _ in rows if i]
        groups = {g for _, i in members for g in i["categories"] if g in KEY_GROUPS}
        return keyset(rows), groups, _tag_set(members)
    b_keys, b_groups, b_tags = info(product_id)
    out = []
    for p in conn.execute("SELECT * FROM products WHERE status='approved' AND category=? AND id<>?", (base["category"], product_id)):
        keys, groups, tags = info(p["id"])
        ing_match = _jaccard(b_keys, keys)
        tag_agree = sum(1 for t in TAGS if (t in b_tags) == (t in tags)) / len(TAGS)
        attr = 0.5 * _jaccard(b_groups, groups) + 0.5 * tag_agree
        combined = 0.6 * ing_match + 0.4 * attr
        diff = None if base["price"] is None or p["price"] is None else p["price"] - base["price"]
        if cheaper_only and not (diff is not None and diff < 0):
            continue
        out.append({"id": p["id"], "name": p["name"], "brand": p["brand"], "category": p["category"], "price": p["price"],
                    "price_difference": diff, "price_difference_pct": None if not diff or not base["price"] else round(100 * diff / base["price"]),
                    "ingredient_match": round(100 * ing_match), "attribute_match": round(100 * attr), "similarity": round(100 * combined),
                    "shared_count": len(b_keys & keys), "shared": sorted(b_keys & keys), "missing_vs_original": sorted(b_keys - keys)[:6],
                    "extra_vs_original": sorted(keys - b_keys)[:6],
                    "shared_groups": sorted(b_groups & groups), "missing_groups": sorted(b_groups - groups)})
    out.sort(key=lambda x: (-x["similarity"], x["price"] or 0))
    return {"product": {"id": base["id"], "name": base["name"], "brand": base["brand"], "category": base["category"], "price": base["price"]},
            "dupes": out[:limit],
            "method": "Similarity = 60% ingredient match + 40% attribute match. Ingredient match = shared ingredients / all ingredients "
                      "(water ignored). Attribute match = half key-ingredient-group overlap, half agreement on fragrance, sulfates, "
                      "parabens, silicones, alcohol and essential oils. Only products of the same type are compared.",
            "note": "A high match means similar ingredients, not an identical formula: label order shows amounts only roughly."}
