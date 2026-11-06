"""Personal match score: how well a product fits one user's saved profile.

Transparent formula (every part is shown to the user):
  start at 50
  + concern fit   up to +30   = min(30, 3 x sum(weight x label-position factor)) over the user's concerns
  + liked         up to +9    = +3 for each ingredient the user marked as liked
  + safety        -20..+10    = (safety score - 70) / 3, 1.5x harsher below zero for sensitive skin
  - skin type     -5          if the product's rules say it is less suitable for the user's skin type
A product that contains anything the user avoids (allergy options, typed names, avoided ingredients, or
pregnancy-flagged ingredients) scores 0 and the reasons are listed.
Labels: 75+ Great match, 55-74 Good match, 35-54 Okay, below 35 Poor match.
"""
from app.analyzer import load_catalog
from app.compare import profile as product_profile, load_concern_table
from app.recommend import build_exclusions, position_factor, is_irritant


def label_for(score):
    return "Great match" if score >= 75 else "Good match" if score >= 55 else "Okay" if score >= 35 else "Poor match"


def match_score(conn, user_profile, liked_ids, avoided_ids, product_id):
    """user_profile: dict(skin_type, concerns[list], allergies[list], avoid_text, pregnant)."""
    skin, concerns = user_profile.get("skin_type") or "", user_profile.get("concerns") or []
    if not skin and not concerns:
        return {"needs_profile": True, "message": "Add your skin type or concerns in your profile to see a personal match score."}
    catalog = load_catalog(conn)
    rows = [(r["position"], catalog["ingredients"].get(r["ingredient_id"]), r["raw_name"]) for r in conn.execute(
        "SELECT position, ingredient_id, raw_name FROM product_ingredients WHERE product_id=? ORDER BY position", (product_id,))]
    members = [(pos, ing) for pos, ing, _ in rows if ing]

    excluded, _unmatched = build_exclusions(catalog, user_profile.get("allergies") or [], user_profile.get("avoid_text") or "",
                                            bool(user_profile.get("pregnant")))
    for iid in avoided_ids:
        if iid in catalog["ingredients"]:
            excluded.setdefault(iid, "You marked this ingredient as one to avoid")
    hits = [(ing["inci_name"], excluded[ing["id"]]) for _, ing in members if ing["id"] in excluded]
    if hits:
        reasons = list(dict.fromkeys(f"{n}: {why}" for n, why in hits))
        return {"needs_profile": False, "score": 0, "label": "Not a match", "reasons": reasons, "breakdown": ["Contains something you avoid, so the score is 0."]}

    table, _labels = load_concern_table(conn)
    weights = {}
    for c in concerns:
        for iid, prio in (table.get(c) or {}).items():
            ing = catalog["ingredients"][iid]
            if skin == "sensitive" and is_irritant(ing):
                prio = max(1, prio - 1)
            weights[iid] = weights.get(iid, 0) + prio
    raw = sum(weights[i["id"]] * position_factor(pos) for pos, i in members if i["id"] in weights)
    concern_pts = round(min(30.0, 3 * raw), 1)
    helpful = [i["inci_name"] for pos, i in members if i["id"] in weights]
    liked_hits = [i["inci_name"] for _, i in members if i["id"] in liked_ids]
    liked_pts = min(9, 3 * len(liked_hits))
    prof = product_profile(rows, table)
    adj = (prof["safety"] - 70) / 3
    if adj < 0 and skin == "sensitive":
        adj *= 1.5
    safety_pts = round(max(-20.0, min(10.0, adj)), 1)
    fit = {f["skin_type"]: f for f in prof["skin_fit"]}
    skin_pts = 0
    skin_note = ""
    if skin in fit and not fit[skin]["suitable"]:
        skin_pts = -5
        skin_note = fit[skin]["reason"]
    score = int(max(0, min(100, round(50 + concern_pts + liked_pts + safety_pts + skin_pts))))

    breakdown = ["Start at 50"]
    if concerns:
        breakdown.append(f"{concern_pts:+} for your concerns" + (f" ({', '.join(dict.fromkeys(helpful))})" if helpful else " (no matching ingredients)"))
    if liked_hits:
        breakdown.append(f"{liked_pts:+} for ingredients you like ({', '.join(liked_hits)})")
    breakdown.append(f"{safety_pts:+} for ingredient safety (product safety score {prof['safety']})")
    if skin_pts:
        breakdown.append(f"{skin_pts:+} less suitable for {skin} skin: {skin_note}")
    return {"needs_profile": False, "score": score, "label": label_for(score), "reasons": [], "breakdown": breakdown,
            "helpful_ingredients": list(dict.fromkeys(helpful)), "liked_ingredients": liked_hits}
