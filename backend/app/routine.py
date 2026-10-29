"""Routine builder: check an AM/PM routine for clashes, build a weekly schedule, and share it.

All checks are fixed rules over the ingredient table (the same `incompatible_with` data the Analyzer
uses), so each warning can be traced to the ingredients that caused it.

Rules:
* CLASH: two products in the SAME slot (AM or PM) whose ingredients are listed as incompatible
  (e.g. retinol with glycolic acid). Different slots only get a friendly note: AM/PM separation works.
* SCHEDULE: products used less than daily are placed on days that avoid clashing partners where possible
  (for example alternate nights). If a clash cannot be avoided (one product is daily), it is reported.
* SUNSCREEN: acids, retinoids and brightening actives raise sun sensitivity, so the AM should end with sunscreen.
* OVER-EXFOLIATION: two or more strong exfoliating products used daily.
* RETINOID IN THE MORNING: retinol is usually used at night.
"""
import itertools
import json
import secrets
from datetime import datetime, timezone

from app.analyzer import load_catalog
from app.compare import CompareError, resolve_side
from app.normalize import normalize

SLOTS = ("am", "pm")
FREQ = {"daily": 7, "3x_week": 3, "2x_week": 2, "weekly": 1}
FREQ_LABEL = {"daily": "Every day", "3x_week": "3 times a week", "2x_week": "2 times a week", "weekly": "Once a week"}
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
ORDER = ["cleanser", "serum", "moisturiser", "sunscreen", "foundation", "mascara", "lipstick", "shampoo"]
CUSTOM_CATEGORIES = ["cleanser", "serum", "moisturiser", "sunscreen", "other"]
MAX_PER_SLOT = 10
SUN_SENSITISING = {"Exfoliant", "Retinoid", "Brightening agent"}
BORING = {"Water", "Glycerin", "Phenoxyethanol", "Panthenol"}
ACTIVE_GROUPS = {"Exfoliant", "Retinoid", "Brightening agent", "Antioxidant", "Peptide"}


class RoutineError(ValueError):
    pass


# ------------------------------------------------------------------ resolving
def resolve_items(conn, catalog, spec):
    """spec = {"am": [...], "pm": [...]}.  Returns {slot: [item dict]}."""
    if not isinstance(spec, dict):
        raise RoutineError("Send the routine as JSON.")
    out = {}
    for slot in SLOTS:
        raw = spec.get(slot) or []
        if not isinstance(raw, list):
            raise RoutineError(f"The {slot.upper()} routine must be a list.")
        if len(raw) > MAX_PER_SLOT:
            raise RoutineError(f"Up to {MAX_PER_SLOT} products per routine.")
        items = []
        for n, it in enumerate(raw):
            if not isinstance(it, dict):
                raise RoutineError("Each routine step must be an object.")
            freq = it.get("frequency", "daily")
            if freq not in FREQ:
                raise RoutineError("Frequency must be one of: " + ", ".join(FREQ))
            try:
                side = resolve_side(conn, catalog, it, f"{slot.upper()} step {n + 1}")
            except CompareError as e:
                raise RoutineError(str(e))
            category = side["category"]
            if not category:
                category = it.get("category") if it.get("category") in CUSTOM_CATEGORIES else "serum"
            ings = list({i["id"]: i for _p, i, _r in side["rows"] if i}.values())
            items.append({"key": f"{slot}{n}", "slot": slot, "title": side["title"], "brand": side["brand"],
                          "category": category, "product_id": side["product_id"], "frequency": freq,
                          "ingredients": ings, "unknown": [r for _p, i, r in side["rows"] if not i]})
        out[slot] = items
    if not out["am"] and not out["pm"]:
        raise RoutineError("Add at least one product to your routine.")
    return out


# ------------------------------------------------------------------ clashes
def clash_pairs(a, b):
    """Ingredient pairs (from product a, from product b) that should not be combined."""
    def names(ings):
        m = {}
        for i in ings:
            for n in [i["inci_name"]] + i["aliases"]:
                m[normalize(n)] = i
        return m
    na, nb = names(a["ingredients"]), names(b["ingredients"])
    found = {}
    for ing in a["ingredients"]:
        for other in ing["incompatible_with"]:
            hit = nb.get(normalize(other))
            if hit:
                found[(ing["inci_name"], hit["inci_name"])] = True
    for ing in b["ingredients"]:
        for other in ing["incompatible_with"]:
            hit = na.get(normalize(other))
            if hit:
                found[(hit["inci_name"], ing["inci_name"])] = True
    return list(found)


# ------------------------------------------------------------------ schedule
def build_schedule(items, conflicts):
    """Choose days for each product, avoiding clashing partners where possible.
    conflicts: set of frozenset({key1, key2}) for products in this slot that clash."""
    placed = {}
    for it in items:
        if it["frequency"] == "daily":
            placed[it["key"]] = set(range(7))
    rest = sorted((i for i in items if i["frequency"] != "daily"), key=lambda i: -FREQ[i["frequency"]])
    for it in rest:
        k = FREQ[it["frequency"]]
        partners = [p for p in placed if frozenset((it["key"], p)) in conflicts]
        best = None
        for combo in itertools.combinations(range(7), k):
            overlap = sum(1 for p in partners for d in combo if d in placed[p])
            adjacent = sum(1 for d in combo if (d + 1) % 7 in combo) if k > 1 else 0
            cand = (overlap, adjacent, combo)
            if best is None or cand < best:
                best = cand
        placed[it["key"]] = set(best[2])
    overlaps = []
    for pair in conflicts:
        a, b = sorted(pair)
        if a in placed and b in placed:
            days = sorted(placed[a] & placed[b])
            if days:
                overlaps.append({"items": [a, b], "days": days})
    rows = [{"key": it["key"], "title": it["title"], "frequency": it["frequency"],
             "frequency_label": FREQ_LABEL[it["frequency"]], "days": sorted(placed[it["key"]])} for it in items]
    return {"rows": rows, "overlaps": overlaps, "day_names": DAYS}


# ------------------------------------------------------------------ the check
def check(conn, spec):
    catalog = load_catalog(conn)
    slots = resolve_items(conn, catalog, spec)
    warnings = []

    def w(level, title, detail, keys=()):
        warnings.append({"level": level, "title": title, "detail": detail, "items": list(keys)})

    titles = {it["key"]: it["title"] for s in SLOTS for it in slots[s]}
    slot_out = {}
    all_items = [it for s in SLOTS for it in slots[s]]

    for slot in SLOTS:
        items = slots[slot]
        conflicts, pair_info = set(), {}
        for a, b in itertools.combinations(items, 2):
            pairs = clash_pairs(a, b)
            if pairs:
                conflicts.add(frozenset((a["key"], b["key"])))
                pair_info[frozenset((a["key"], b["key"]))] = (a, b, "; ".join(f"{x} with {y}" for x, y in pairs[:3]))
        sched = build_schedule(items, conflicts)
        unavoidable = {frozenset(ov["items"]): ov for ov in sched["overlaps"]}
        days_of = {r["key"]: r["days"] for r in sched["rows"]}
        for pair, (a, b, names) in pair_info.items():
            if pair in unavoidable:
                ov = unavoidable[pair]
                w("warn", f"{a['title']} and {b['title']} clash in your {slot.upper()} routine",
                  f"{names}. They would be used together on {', '.join(DAYS[d] for d in ov['days'])}. "
                  "Move one to the other time of day or make it less frequent.", (a["key"], b["key"]))
            else:
                w("info", f"Use {a['title']} and {b['title']} on different days",
                  f"{names}. In your {slot.upper()} routine: {a['title']} on {', '.join(DAYS[d] for d in days_of[a['key']])}; "
                  f"{b['title']} on {', '.join(DAYS[d] for d in days_of[b['key']])}.", (a["key"], b["key"]))
        ordered = sorted(items, key=lambda i: (ORDER.index(i["category"]) if i["category"] in ORDER else 9, i["key"]))
        slot_out[slot] = {"items": [{"key": i["key"], "title": i["title"], "brand": i["brand"], "category": i["category"],
                                     "product_id": i["product_id"], "frequency": i["frequency"],
                                     "frequency_label": FREQ_LABEL[i["frequency"]], "unknown_count": len(i["unknown"])} for i in items],
                          "suggested_order": [{"key": i["key"], "title": i["title"], "category": i["category"]} for i in ordered],
                          "schedule": sched}
        # same active repeated across products in this slot
        seen = {}
        for it in items:
            for ing in it["ingredients"]:
                if ing["inci_name"] not in BORING and ACTIVE_GROUPS & set(ing["categories"]):
                    seen.setdefault(ing["inci_name"], []).append(it["title"])
        for name, who in seen.items():
            if len(who) > 1:
                w("info", f"{name} appears in {len(who)} products", f"{', '.join(who)} all contain {name} in the {slot.upper()}. That is not harmful, but you may not need all of them.")

    # clashes that are fine because they are in different slots
    for a in slots["am"]:
        for b in slots["pm"]:
            pairs = clash_pairs(a, b)
            if pairs and not (a["product_id"] is not None and a["product_id"] == b["product_id"]):
                x, y = pairs[0]
                w("good", "Good: clashing products are kept apart", f"{a['title']} (AM) and {b['title']} (PM) contain {x} and {y}. Using them at different times of day works well.", (a["key"], b["key"]))

    def has(item, groups, min_irritancy=0):
        return any(set(i["categories"]) & groups and i["irritancy"] >= min_irritancy for i in item["ingredients"])

    am_sun = any(it["category"] == "sunscreen" for it in slots["am"])
    sensitising = [it for it in all_items if has(it, SUN_SENSITISING, 2)]
    if not am_sun:
        if sensitising:
            w("warn", "Add a sunscreen to your morning routine",
              ", ".join(dict.fromkeys(i["title"] for i in sensitising)) + " can make skin more sun-sensitive. Finish your AM routine with SPF 30+.")
        elif slots["am"]:
            w("info", "No sunscreen in your morning routine", "Sunscreen is the most important daily step for most skin concerns.")
    if any(it["category"] == "sunscreen" for it in slots["pm"]):
        w("info", "Sunscreen in your evening routine", "Sunscreen is meant for daytime. At night, a moisturiser is usually enough.")
    for it in slots["am"]:
        if has(it, {"Retinoid"}, 3):
            w("warn", f"{it['title']} is a retinoid in your morning routine", "Retinol is usually used at night because sunlight breaks it down and it raises sun sensitivity.", (it["key"],))
    strong = [it for it in all_items if it["frequency"] == "daily" and has(it, {"Exfoliant"}, 3)]
    if len(strong) >= 2:
        w("warn", "Possible over-exfoliation", ", ".join(i["title"] for i in strong) + " all contain strong exfoliants and are used daily. Too much exfoliation damages the skin barrier.",
          [i["key"] for i in strong])

    levels = [x["level"] for x in warnings]
    if "warn" in levels:
        status, summary = "warn", f"{levels.count('warn')} thing(s) to fix in your routine."
    else:
        status, summary = "good", "No clashes found. Your routine looks well put together."
    return {"status": status, "summary": summary, "warnings": warnings, "slots": slot_out,
            "disclaimer": "Educational guidance, not medical advice. Introduce one new product at a time and patch-test."}


# ------------------------------------------------------------------ sharing
def save_shared(conn, name, spec):
    name = (name or "My routine").strip()[:60] or "My routine"
    check(conn, spec)  # validates everything, raises RoutineError
    clean = {s: [{k: v for k, v in it.items() if k in ("product_id", "text", "name", "frequency", "category")}
                 for it in (spec.get(s) or [])] for s in SLOTS}
    for s in SLOTS:
        for it in clean[s]:
            if isinstance(it.get("text"), str):
                it["text"] = it["text"][:2000]
            if isinstance(it.get("name"), str):
                it["name"] = it["name"][:60]
    token = secrets.token_urlsafe(8)
    conn.execute("INSERT INTO routines (token, name, data, created_at) VALUES (?,?,?,?)",
                 (token, name, json.dumps(clean), datetime.now(timezone.utc).isoformat(timespec="seconds")))
    conn.commit()
    return token


def load_shared(conn, token):
    r = conn.execute("SELECT * FROM routines WHERE token=?", (token,)).fetchone()
    if not r:
        return None
    data = json.loads(r["data"])
    return {"token": r["token"], "name": r["name"], "am": data["am"], "pm": data["pm"], "created_at": r["created_at"]}
