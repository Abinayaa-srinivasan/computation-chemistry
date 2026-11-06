"""Ingredient Analyzer.

Pipeline:  text -> split -> normalise -> match (exact alias, then fuzzy) -> classify -> verdict

Design choices (explain these in your viva):
* The verdict and ratings come from a DETERMINISTIC rule set over the ingredient table, so the same
  list always gives the same answer and every point can be traced to a reason.
* Unknown ingredients get a SUGGESTED category from a small ML model (TF-IDF character n-grams +
  logistic regression) or keyword rules, always shown with a confidence and labelled "suggested".
* An ingredient list shows order, not exact amounts, so nothing here claims exact concentrations.
"""
import difflib
import json
import re

from app.normalize import normalize, split_ingredient_list

DISCLAIMER = ("Educational information, not medical advice. Ratings are rough estimates. "
              "Patch-test new products and ask a doctor or dermatologist if you are pregnant, "
              "have a skin condition or are unsure.")

FUZZY_CUTOFF = 0.88  # similarity needed to accept a typo-corrected match

FLAG_TEXT = {
    "allergen": "common allergen", "fragrance": "fragrance", "drying_alcohol": "drying alcohol",
    "paraben": "paraben", "sulfate": "sulfate", "essential_oil": "essential oil",
    "silicone": "silicone", "pregnancy_caution": "check with a doctor if pregnant",
    "sensitive_caution": "can irritate sensitive skin",
}
JOB_TEXT = {
    "Humectant": "hydrating (pulls in moisture)", "Emollient": "softening", "Occlusive": "sealing in moisture",
    "Exfoliant": "exfoliating", "Retinoid": "boosting skin renewal", "Antioxidant": "antioxidant protection",
    "Brightening agent": "brightening and evening tone", "Soothing agent": "soothing",
    "Peptide": "firming (peptides)", "UV filter": "sun protection", "Skin-identical lipid": "repairing the skin barrier",
    "Surfactant": "cleansing",
}
KEY_GROUPS = ["Exfoliant", "Retinoid", "Brightening agent", "Antioxidant", "Peptide", "UV filter",
              "Humectant", "Soothing agent", "Skin-identical lipid", "Emollient", "Occlusive", "Surfactant"]

# keyword rules for unknown ingredients: (substring in normalised name, category)
KEYWORD_RULES = [
    ("peptide", "Peptide"), ("ceramide", "Skin-identical lipid"), ("hyaluron", "Humectant"),
    ("retin", "Retinoid"), ("tocopher", "Antioxidant"), ("ascorb", "Antioxidant"),
    ("paraben", "Preservative"), ("isothiazolinone", "Preservative"), ("benzoate", "Preservative"),
    ("sorbate", "Preservative"), ("parfum", "Fragrance"), ("fragrance", "Fragrance"),
    ("polysorbate", "Emulsifier"), ("ceteareth", "Emulsifier"), ("peg-", "Emulsifier"),
    ("glucoside", "Surfactant"), ("sulfate", "Surfactant"), ("sulfosuccinate", "Surfactant"),
    ("isethionate", "Surfactant"), ("sarcosinate", "Surfactant"), ("betaine", "Surfactant"),
    ("amphoacetate", "Surfactant"), ("glycol", "Humectant"), ("glycerin", "Humectant"),
    ("methicone", "Emollient"), ("siloxane", "Emollient"), ("dimethicone", "Emollient"),
    ("seed oil", "Emollient"), (" oil", "Emollient"), ("butter", "Emollient"),
    ("cellulose", "Thickener"), ("gum", "Thickener"), ("carbomer", "Thickener"), (" wax", "Thickener"),
    ("ci ", "Colorant/Pigment"), ("mica", "Colorant/Pigment"),
]


# ------------------------------------------------------------------ catalog and matching
def load_catalog(conn):
    """Read the ingredient table into memory: list of dicts + normalised-name lookup."""
    ingredients, lookup = {}, {}
    for r in conn.execute("SELECT * FROM ingredients"):
        d = dict(r)
        for f in ("aliases", "categories", "flags", "skin_types", "incompatible_with"):
            d[f] = json.loads(d[f])
        ingredients[d["id"]] = d
    for r in conn.execute("SELECT alias_norm, ingredient_id FROM alias_index"):
        lookup[r["alias_norm"]] = r["ingredient_id"]
    return {"ingredients": ingredients, "lookup": lookup}


def match_ingredient(raw, catalog):
    """Return (ingredient or None, how, score, matched_name)."""
    norm = normalize(raw)
    if not norm:
        return None, "none", 0.0, None
    lookup = catalog["lookup"]
    if norm in lookup:
        ing = catalog["ingredients"][lookup[norm]]
        return ing, "exact", 1.0, ing["inci_name"]
    # "aqua / water" style: try each side of a slash
    if "/" in norm:
        for part in norm.split("/"):
            part = part.strip()
            if part in lookup:
                ing = catalog["ingredients"][lookup[part]]
                return ing, "exact", 1.0, ing["inci_name"]
    # fuzzy: fixes OCR errors and typos ("niacinamid", "glycerln")
    close = difflib.get_close_matches(norm, lookup.keys(), n=1, cutoff=FUZZY_CUTOFF)
    if close:
        ing = catalog["ingredients"][lookup[close[0]]]
        score = difflib.SequenceMatcher(None, norm, close[0]).ratio()
        return ing, "fuzzy", round(score, 2), ing["inci_name"]
    return None, "none", 0.0, None


# ------------------------------------------------------------------ classifier for unknowns
_model_cache = {}


def _train_model(catalog):
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import make_pipeline
    except ImportError:
        return None
    names, labels = [], []
    for ing in catalog["ingredients"].values():
        if ing["categories"]:
            names.append(ing["norm_name"]); labels.append(ing["categories"][0])
    model = make_pipeline(TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4)),
                          LogisticRegression(max_iter=3000, C=20))
    model.fit(names, labels)
    return model


def get_model(catalog):
    key = len(catalog["ingredients"])
    if key not in _model_cache:
        _model_cache[key] = _train_model(catalog)
    return _model_cache[key]


def suggest_category(raw, catalog):
    """Suggest a category for an ingredient we do not know. Returns dict or None."""
    norm = normalize(raw)
    padded = " " + norm
    for key, cat in KEYWORD_RULES:
        if key in padded:
            return {"category": cat, "confidence": 0.8, "method": "keyword rule"}
    model = get_model(catalog)
    if model is None:
        return None
    probs = model.predict_proba([norm])[0]
    best = probs.argmax()
    return {"category": str(model.classes_[best]), "confidence": round(float(probs[best]), 2),
            "method": "ML model"}


# ------------------------------------------------------------------ ratings and verdict
def safety_level(ing):
    """good / warn / bad for a recognised ingredient (deterministic)."""
    if ing["irritancy"] >= 3:
        return "bad"
    if ing["irritancy"] == 2 or any(f in ing["flags"] for f in ("fragrance", "sensitive_caution", "pregnancy_caution")):
        return "warn"
    return "good"


def reason_for(ing):
    lvl = safety_level(ing)
    bits = [FLAG_TEXT[f] for f in ing["flags"] if f in FLAG_TEXT]
    if lvl == "good":
        return ing["description"]
    return f"{ing['description']} Note: " + ", ".join(bits or [f"irritation potential {ing['irritancy']}/5"]) + "."


def find_conflicts(recognised):
    """Pairs in the same list that the ingredient table says should not be combined."""
    by_norm = {}
    for ing in recognised:
        for n in [ing["inci_name"]] + ing["aliases"]:
            by_norm[normalize(n)] = ing
    seen, out = set(), []
    for ing in recognised:
        for other_name in ing["incompatible_with"]:
            other = by_norm.get(normalize(other_name))
            if other and other["id"] != ing["id"]:
                key = tuple(sorted((ing["inci_name"], other["inci_name"])))
                if key not in seen:
                    seen.add(key)
                    out.append({"a": key[0], "b": key[1],
                                "message": f"{key[0]} and {key[1]} are usually not combined in one routine step; together they may irritate."})
    return out


def build_verdict(recognised, conflicts, unknown_count, total):
    not_suitable, caution = [], []
    for ing in recognised:
        n = ing["inci_name"]
        if "pregnancy_caution" in ing["flags"]:
            not_suitable.append(f"{n}: ask a doctor first if pregnant or breastfeeding.")
        if ing["irritancy"] >= 4:
            not_suitable.append(f"{n} has high irritation potential, so it is not for sensitive skin.")
        elif ing["irritancy"] == 3 and not any(f in ing["flags"] for f in ("fragrance", "essential_oil", "drying_alcohol")):
            caution.append(f"{n} can irritate, so introduce it slowly.")
        for f, txt in (("fragrance", "contains fragrance"), ("essential_oil", "is an essential oil"),
                       ("drying_alcohol", "is a drying alcohol")):
            if f in ing["flags"] and ing["irritancy"] < 4:
                caution.append(f"{n} {txt}, which bothers some skin.")
        if ing["comedogenic"] >= 4:
            caution.append(f"{n} may clog pores for acne-prone skin.")
    caution += [c["message"] for c in conflicts]
    if total and unknown_count / total >= 0.3:
        caution.append(f"{unknown_count} of {total} ingredients were not recognised, so this verdict is less certain.")
    dedupe = lambda xs: list(dict.fromkeys(xs))
    not_suitable, caution = dedupe(not_suitable), dedupe(caution)
    if not_suitable:
        return {"label": "Not suitable for some people", "level": "bad", "reasons": not_suitable + caution}
    if caution:
        return {"label": "Use with caution", "level": "warn", "reasons": caution}
    return {"label": "Generally safe", "level": "good",
            "reasons": ["No major concerns found among the recognised ingredients."]}


# ------------------------------------------------------------------ main entry point
def analyze(conn, text, catalog=None):
    catalog = catalog or load_catalog(conn)
    names = split_ingredient_list(text or "")[:200]
    rows, recognised = [], []
    for pos, raw in enumerate(names, start=1):
        ing, how, score, matched = match_ingredient(raw, catalog)
        row = {"position": pos, "raw_name": raw, "match": how, "match_score": score}
        if ing:
            recognised.append(ing)
            lvl = safety_level(ing)
            row.update(recognised=True, inci_name=ing["inci_name"], categories=ing["categories"],
                       level=lvl, reason=reason_for(ing), flags=ing["flags"],
                       irritancy=ing["irritancy"], comedogenic=ing["comedogenic"],
                       typical_min=ing["typical_min"], typical_max=ing["typical_max"],
                       ingredient_id=ing["id"])
            if how == "fuzzy":
                row["corrected_from"] = raw
        else:
            row.update(recognised=False, inci_name=raw, categories=[], level="unk",
                       reason="Not in our database.", flags=[], suggestion=suggest_category(raw, catalog))
        rows.append(row)

    unknown = [r for r in rows if not r["recognised"]]
    conflicts = find_conflicts(recognised)
    verdict = build_verdict(recognised, conflicts, len(unknown), len(rows))

    def names_with(pred):
        return list(dict.fromkeys(i["inci_name"] for i in recognised if pred(i)))
    flags = {
        "allergens": names_with(lambda i: "allergen" in i["flags"]),
        "irritants": names_with(lambda i: i["irritancy"] >= 3),
        "comedogenic": names_with(lambda i: i["comedogenic"] >= 4),
        "pregnancy_caution": names_with(lambda i: "pregnancy_caution" in i["flags"]),
        "sensitive_skin_caution": names_with(lambda i: "sensitive_caution" in i["flags"]),
        "fragrance": names_with(lambda i: "fragrance" in i["flags"] or "essential_oil" in i["flags"]),
    }
    groups = []
    for g in KEY_GROUPS:
        members = names_with(lambda i, g=g: g in i["categories"])
        if members:
            groups.append({"group": g, "ingredients": members})
    jobs = [JOB_TEXT[g["group"]] for g in groups if g["group"] in JOB_TEXT][:5]
    if not rows:
        summary = "No ingredients found in the text."
    elif jobs:
        summary = "This formula appears to focus on: " + ", ".join(jobs) + "."
    else:
        summary = "No clear active ingredient groups were found; this looks like a basic formula."
    return {
        "total": len(rows), "recognised_count": len(rows) - len(unknown),
        "fuzzy_count": sum(1 for r in rows if r["match"] == "fuzzy"),
        "verdict": verdict, "flags": flags, "key_groups": groups, "summary": summary,
        "conflicts": conflicts, "ingredients": rows,
        "unrecognised": [{"raw_name": r["raw_name"], "suggestion": r["suggestion"]} for r in unknown],
        "disclaimer": DISCLAIMER,
    }


# ------------------------------------------------------------------ OCR
class OcrUnavailable(Exception):
    pass


def ocr_image(data: bytes) -> str:
    """Read ingredient text from an image. Needs Pillow, pytesseract AND the Tesseract program."""
    try:
        import io
        from PIL import Image, ImageOps
        import pytesseract
    except ImportError as e:
        raise OcrUnavailable("Image reading needs Pillow and pytesseract (pip install pillow pytesseract).") from e
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except Exception as e:
        raise ValueError("That file is not a readable image.") from e
    img = ImageOps.exif_transpose(img).convert("L")
    if img.width < 1200:  # small photos OCR badly; upscale
        scale = 1200 / img.width
        img = img.resize((int(img.width * scale), int(img.height * scale)))
    img = ImageOps.autocontrast(img)
    try:
        return pytesseract.image_to_string(img, config="--psm 6")
    except pytesseract.TesseractNotFoundError as e:
        raise OcrUnavailable("The Tesseract OCR program is not installed on this computer.") from e
