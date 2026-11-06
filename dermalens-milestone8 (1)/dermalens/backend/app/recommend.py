"""Skin-concern recommendations: which ingredients help, and which products contain them.

Everything here is rule-based and deterministic, so each recommendation can be explained:

  ingredient weight  = sum, over the chosen concerns, of that ingredient's priority (3 first-line,
                       2 good option, 1 supporting); lowered by 1 for sensitive skin when the
                       ingredient is a known irritant.
  position factor    = 1.0 if the ingredient is in the first 5 on the label, 0.7 if in 6-10, else 0.4
                       (an ingredient listed earlier is present in a larger amount).
  product score      = sum(weight x position factor)  -  1.0 for each irritant/fragrance ingredient
                       the product has that was NOT recommended (only for sensitive users).
Products are dropped if they contain anything the user is allergic to, avoids, or (when pregnant)
ingredients flagged for pregnancy caution.
"""
from app.analyzer import load_catalog, match_ingredient, find_conflicts
from app.normalize import normalize

SKIN_TYPES = ["normal", "dry", "oily", "combination", "sensitive"]
SKINCARE_CATEGORIES = ["serum", "moisturiser", "sunscreen", "cleanser"]

# allergy / avoid choices shown in the UI: key -> (label, how to detect)
ALLERGY_OPTIONS = {
    "fragrance": ("Fragrance / parfum", {"flags": ["fragrance"]}),
    "essential_oils": ("Essential oils", {"flags": ["essential_oil"]}),
    "parabens": ("Parabens", {"flags": ["paraben"]}),
    "sulfates": ("Sulfates", {"flags": ["sulfate"]}),
    "silicones": ("Silicones", {"flags": ["silicone"]}),
    "drying_alcohol": ("Drying alcohol", {"flags": ["drying_alcohol"]}),
    "lanolin": ("Lanolin", {"names": ["Lanolin"]}),
    "nut_oils": ("Nut and coconut oils", {"names": ["Prunus Amygdalus Dulcis Oil", "Cocos Nucifera Oil", "Argania Spinosa Kernel Oil"]}),
}

DISCLAIMER = ("General educational guidance, not medical advice or a diagnosis. Patch-test new products, "
              "introduce one active at a time, and see a dermatologist for persistent or severe skin problems.")


class InputError(ValueError):
    pass


def position_factor(pos):
    return 1.0 if pos <= 5 else 0.7 if pos <= 10 else 0.4


def is_irritant(ing):
    return ing["irritancy"] >= 3 or any(f in ing["flags"] for f in ("fragrance", "essential_oil", "sensitive_caution"))


def fits_skin_type(ing, skin_type):
    """Return a short note if the ingredient is usually aimed at other skin types, else ''."""
    types = ing["skin_types"]
    if not skin_type or not types or "all" in types:
        return ""
    ok = {skin_type}
    if skin_type == "combination":
        ok |= {"normal", "oily"}
    if skin_type == "sensitive":
        ok |= {"sensitive"}
    if ok & set(types):
        return ""
    return "Usually aimed at " + ", ".join(types) + " skin; go gently on " + skin_type + " skin."


def _concern_rows(conn):
    out = {}
    for r in conn.execute("SELECT * FROM concerns ORDER BY label"):
        out[r["name"]] = {"name": r["name"], "label": r["label"], "description": r["description"],
                          "ingredients": [], "avoid": [], "tips": []}
    for r in conn.execute("SELECT * FROM concern_ingredients ORDER BY priority DESC, rowid"):
        out[r["concern"]]["ingredients"].append(dict(r))
    for r in conn.execute("SELECT * FROM concern_avoid"):
        out[r["concern"]]["avoid"].append({"item": r["item"], "why": r["why"]})
    for r in conn.execute("SELECT * FROM concern_tips"):
        out[r["concern"]]["tips"].append(r["tip"])
    return out


def list_concerns(conn):
    return [{"name": c["name"], "label": c["label"], "description": c["description"]}
            for c in _concern_rows(conn).values()]


def build_exclusions(catalog, allergies, avoid_text, pregnant):
    """Return ({ingredient_id: reason}, [avoid-text names we could not match])."""
    excluded, unmatched = {}, []
    by_name = {i["inci_name"]: i for i in catalog["ingredients"].values()}
    for key in allergies:
        label, rule = ALLERGY_OPTIONS[key]
        for ing in catalog["ingredients"].values():
            if any(f in ing["flags"] for f in rule.get("flags", [])) or ing["inci_name"] in rule.get("names", []):
                excluded.setdefault(ing["id"], f"You avoid: {label}")
    for raw in [x.strip() for x in avoid_text.replace(";", ",").split(",") if x.strip()][:20]:
        ing, how, _score, _m = match_ingredient(raw, catalog)
        if ing:
            excluded.setdefault(ing["id"], f"You avoid: {ing['inci_name']}")
        else:
            unmatched.append(raw)
    if pregnant:
        for ing in by_name.values():
            if "pregnancy_caution" in ing["flags"]:
                excluded.setdefault(ing["id"], "Check with a doctor first if pregnant or breastfeeding")
    return excluded, unmatched


def recommend(conn, params):
    skin_type = (params.get("skin_type") or "").strip().lower()
    concerns = [c.strip().lower() for c in (params.get("concerns") or [])]
    allergies = list(params.get("allergies") or [])
    avoid_text = (params.get("avoid_text") or "")[:300]
    pregnant = bool(params.get("pregnant"))
    category = (params.get("category") or "").strip().lower()
    fragrance_free = bool(params.get("fragrance_free"))
    max_price = params.get("max_price")
    limit = min(int(params.get("limit") or 12), 30)

    all_concerns = _concern_rows(conn)
    if skin_type and skin_type not in SKIN_TYPES:
        raise InputError("Choose a skin type from: " + ", ".join(SKIN_TYPES) + ".")
    if not concerns:
        raise InputError("Pick at least one skin concern.")
    bad = [c for c in concerns if c not in all_concerns]
    if bad:
        raise InputError("Unknown concern: " + ", ".join(bad))
    if len(set(concerns)) > 4:
        raise InputError("Pick up to 4 concerns at a time for focused advice.")
    concerns = list(dict.fromkeys(concerns))
    bad = [a for a in allergies if a not in ALLERGY_OPTIONS]
    if bad:
        raise InputError("Unknown avoid option: " + ", ".join(bad))
    if max_price not in (None, ""):
        try:
            max_price = float(max_price)
        except (TypeError, ValueError):
            raise InputError("Maximum price must be a number.")
    else:
        max_price = None

    catalog = load_catalog(conn)
    ings = catalog["ingredients"]
    excluded, unmatched = build_exclusions(catalog, allergies, avoid_text, pregnant)

    # ---- per-concern ingredient advice
    weights, helps, excluded_report = {}, {}, {}
    concern_out = []
    for cname in concerns:
        c = all_concerns[cname]
        items = []
        for row in c["ingredients"]:
            ing = ings[row["ingredient_id"]]
            if ing["id"] in excluded:
                excluded_report[ing["inci_name"]] = excluded[ing["id"]]
                continue
            prio = row["priority"]
            caution = row["caution"] or ""
            if skin_type == "sensitive" and is_irritant(ing):
                prio = max(1, prio - 1)
                caution = (caution + " " if caution else "") + "Sensitive skin: start once a week and build slowly."
            note = fits_skin_type(ing, skin_type)
            weights[ing["id"]] = weights.get(ing["id"], 0) + prio
            helps.setdefault(ing["id"], []).append(cname)
            items.append({"id": ing["id"], "inci_name": ing["inci_name"], "priority": prio, "categories": ing["categories"],
                          "why": row["why"], "how_to_use": row["how_to_use"], "caution": caution.strip(), "skin_note": note,
                          "typical_min": ing["typical_min"], "typical_max": ing["typical_max"]})
        items.sort(key=lambda x: -x["priority"])
        concern_out.append({"name": cname, "label": c["label"], "description": c["description"],
                            "ingredients": items, "avoid": c["avoid"], "tips": c["tips"]})

    # ---- combined tips: sunscreen reminder, clashes, general
    rec_ings = [ings[i] for i in weights]
    tips = []
    if any(i["categories"] and ({"Exfoliant", "Retinoid", "Brightening agent"} & set(i["categories"])) for i in rec_ings):
        tips.append("Use a broad-spectrum SPF 30+ sunscreen every morning: acids, retinoids and vitamin C make skin more sun-sensitive.")
    for cf in find_conflicts(rec_ings):
        tips.append(f"{cf['a']} and {cf['b']} can irritate together. Use them on different nights or at different times of day.")
    tips.append("Add one new active at a time and wait 2 to 4 weeks before judging results.")

    # ---- products
    sensitive_mode = skin_type == "sensitive" or {"sensitivity", "redness"} & set(concerns)
    wanted_categories = [category] if category else SKINCARE_CATEGORIES
    prods = {}
    for r in conn.execute("""SELECT p.id, p.name, p.brand, p.category, p.price, pi.position, pi.ingredient_id
                             FROM products p JOIN product_ingredients pi ON pi.product_id = p.id
                             WHERE p.status = 'approved' ORDER BY p.id, pi.position"""):
        d = prods.setdefault(r["id"], {"id": r["id"], "name": r["name"], "brand": r["brand"], "category": r["category"],
                                       "price": r["price"], "rows": []})
        d["rows"].append((r["position"], r["ingredient_id"]))
    results = []
    for p in prods.values():
        if p["category"] not in wanted_categories:
            continue
        if max_price is not None and p["price"] is not None and p["price"] > max_price:
            continue
        members = [(pos, ings[iid]) for pos, iid in p["rows"] if iid in ings]
        if any(i["id"] in excluded for _, i in members):
            continue
        if fragrance_free and any(("fragrance" in i["flags"] or "essential_oil" in i["flags"]) for _, i in members):
            continue
        score, matched, breakdown = 0.0, [], []
        for pos, i in members:
            if i["id"] in weights:
                pts = round(weights[i["id"]] * position_factor(pos), 1)
                score += pts
                matched.append({"inci_name": i["inci_name"], "position": pos, "concerns": helps[i["id"]], "points": pts})
                breakdown.append(f"+{pts} {i['inci_name']} (#{pos} on the label)")
        warnings = []
        if sensitive_mode:
            for pos, i in members:
                if i["id"] not in weights and is_irritant(i):
                    score -= 1.0
                    breakdown.append(f"-1.0 {i['inci_name']} (possible irritant)")
                    warnings.append(f"Contains {i['inci_name']}, which can irritate sensitive skin.")
        for pos, i in members:  # heads-up for strong actives the user did not ask for
            if i["id"] not in weights and i["irritancy"] >= 4:
                note = f"Also contains {i['inci_name']}, a strong active."
                if note not in warnings and not any(i["inci_name"] in w for w in warnings):
                    warnings.append(note)
        if not matched or score <= 0:
            continue
        results.append({"id": p["id"], "name": p["name"], "brand": p["brand"], "category": p["category"], "price": p["price"],
                        "score": round(score, 1), "matched": matched, "breakdown": breakdown, "warnings": warnings})
    results.sort(key=lambda x: (-x["score"], x["price"] or 0, x["name"]))

    combined = sorted(({"id": iid, "inci_name": ings[iid]["inci_name"], "weight": w, "concerns": helps[iid]}
                       for iid, w in weights.items()), key=lambda x: (-x["weight"], x["inci_name"]))
    return {
        "skin_type": skin_type or None, "concerns": concern_out, "combined_ingredients": combined,
        "excluded": [{"inci_name": k, "reason": v} for k, v in excluded_report.items()],
        "unmatched_avoid": unmatched, "tips": tips,
        "products": results[:limit], "product_count": len(results),
        "scoring_note": "Score = sum of (ingredient weight x label-position factor). Earlier on the label means more of it.",
        "disclaimer": DISCLAIMER,
    }


def options():
    return {"skin_types": SKIN_TYPES,
            "allergies": [{"key": k, "label": v[0]} for k, v in ALLERGY_OPTIONS.items()],
            "categories": ["all skincare"] + SKINCARE_CATEGORIES + ["foundation", "lipstick", "mascara", "shampoo"]}
