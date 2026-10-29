"""Milestone 4 tests: concern recommendations, exclusions, scoring and the API."""
import os
import tempfile

import pytest

from app.db import connect
from app.main import create_app
from app import recommend as rec
from seed.concerns_data import CONCERNS
from seed.load import load


@pytest.fixture(scope="module")
def env():
    path = os.path.join(tempfile.mkdtemp(), "t.db")
    counts, unknown = load(path, quiet=True)
    assert unknown == []
    conn = connect(path)
    yield {"conn": conn, "client": create_app(path).test_client()}
    conn.close()


def go(env, **kw):
    return rec.recommend(env["conn"], kw)


def names(r, concern_index=0):
    return [i["inci_name"] for i in r["concerns"][concern_index]["ingredients"]]


def test_concern_data_complete(env):
    assert len(CONCERNS) == 10
    for name, c in CONCERNS.items():
        assert len(c["ingredients"]) >= 4 and c["avoid"] and c["tips"], name
        assert all(1 <= p <= 3 for _, p, *_ in c["ingredients"])


def test_pigmentation_recommends_glycolic_first_line(env):
    r = go(env, skin_type="normal", concerns=["pigmentation"])
    assert "Glycolic Acid" in names(r)
    top = {i["inci_name"]: i["priority"] for i in r["concerns"][0]["ingredients"]}
    assert top["Glycolic Acid"] == 3 and top["Niacinamide"] == 3
    assert any("SPF 30" in t for t in r["tips"])


def test_products_ranked_and_explained(env):
    r = go(env, concerns=["pigmentation"])
    scores = [p["score"] for p in r["products"]]
    assert scores == sorted(scores, reverse=True) and scores[0] > 0
    top = r["products"][0]
    assert top["matched"] and top["breakdown"]
    assert round(sum(m["points"] for m in top["matched"]), 1) == top["score"]
    assert top["name"] == "Pigment Fade Tranexamic Serum"


def test_default_category_is_skincare_only(env):
    r = go(env, concerns=["dryness"], limit=30)
    assert {p["category"] for p in r["products"]} <= set(rec.SKINCARE_CATEGORIES)
    r = go(env, concerns=["dryness"], category="foundation", limit=30)
    assert {p["category"] for p in r["products"]} <= {"foundation"}


def test_pregnancy_removes_flagged_ingredients_and_products(env):
    r = go(env, concerns=["acne", "ageing"], pregnant=True, limit=30)
    all_names = {n for i in range(len(r["concerns"])) for n in names(r, i)}
    assert "Retinol" not in all_names and "Salicylic Acid" not in all_names
    assert {x["inci_name"] for x in r["excluded"]} >= {"Retinol", "Salicylic Acid"}
    for p in r["products"]:
        assert "Retinol" not in {m["inci_name"] for m in p["matched"]}
        assert "Retinol Renewal Cream" != p["name"] and "Pore Clear BHA Serum" != p["name"]


def test_fragrance_avoidance_excludes_fragranced_products(env):
    r = go(env, concerns=["pigmentation", "dullness"], allergies=["fragrance"], limit=30)
    assert r["products"]
    assert "Glow AHA Exfoliating Serum" not in {p["name"] for p in r["products"]}  # contains Parfum


def test_free_text_avoid_uses_fuzzy_matching(env):
    r = go(env, concerns=["oiliness"], avoid_text="Niacinamid, Totally Unknown Thing", limit=30)
    assert "Niacinamide" not in names(r)
    assert r["unmatched_avoid"] == ["Totally Unknown Thing"]
    assert all("Niacinamide" not in {m["inci_name"] for m in p["matched"]} for p in r["products"])


def test_sensitive_skin_lowers_priority_and_adds_caution(env):
    normal = {i["inci_name"]: i for i in go(env, skin_type="normal", concerns=["ageing"])["concerns"][0]["ingredients"]}
    sens = {i["inci_name"]: i for i in go(env, skin_type="sensitive", concerns=["ageing"])["concerns"][0]["ingredients"]}
    assert sens["Retinol"]["priority"] == normal["Retinol"]["priority"] - 1
    assert "Sensitive skin" in sens["Retinol"]["caution"]


def test_clash_tip_when_retinol_and_acid_both_recommended(env):
    r = go(env, concerns=["ageing", "dullness"])
    assert any("Retinol" in t and "Glycolic Acid" in t for t in r["tips"])


def test_filters(env):
    r = go(env, concerns=["dryness"], fragrance_free=True, max_price=600, limit=30)
    assert r["products"] and all(p["price"] <= 600 for p in r["products"])
    full = go(env, concerns=["dryness"], limit=30)
    assert "Rich Shea Night Cream" in {p["name"] for p in full["products"]}
    assert "Rich Shea Night Cream" not in {p["name"] for p in r["products"]}  # has Parfum and costs 899


def test_strong_active_warning(env):
    r = go(env, concerns=["dryness"], limit=30)
    cream = next(p for p in r["products"] if p["name"] == "Retinol Renewal Cream")
    assert any("Retinol" in w for w in cream["warnings"])


def test_input_validation(env):
    for bad in ({"concerns": []}, {"concerns": ["nonsense"]}, {"concerns": ["acne"], "skin_type": "purple"},
                {"concerns": ["acne"], "allergies": ["gluten"]},
                {"concerns": ["acne", "ageing", "dryness", "oiliness", "redness"]},
                {"concerns": ["acne"], "max_price": "abc"}):
        with pytest.raises(rec.InputError):
            go(env, **bad)


def test_deterministic(env):
    a = go(env, skin_type="oily", concerns=["acne", "oiliness"])
    assert a == go(env, skin_type="oily", concerns=["acne", "oiliness"])


def test_api(env):
    c = env["client"]
    d = c.get("/api/concerns").json
    assert len(d["concerns"]) == 10 and "sensitive" in d["skin_types"] and d["allergies"]
    r = c.post("/api/recommend", json={"concerns": ["pigmentation"], "skin_type": "dry"})
    assert r.status_code == 200 and r.json["products"] and r.json["disclaimer"]
    assert c.post("/api/recommend", json={"concerns": []}).status_code == 400
    assert c.post("/api/recommend", data="x").status_code == 400
