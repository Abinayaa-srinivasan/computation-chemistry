"""Milestone 5 tests: compare scoring and verdicts, dupes, and the API."""
import os
import tempfile

import pytest

from app import compare as cmp
from app.db import connect
from app.main import create_app
from seed.load import load


@pytest.fixture(scope="module")
def env():
    path = os.path.join(tempfile.mkdtemp(), "t.db")
    load(path, quiet=True)
    conn = connect(path)
    ids = {r["name"]: r["id"] for r in conn.execute("SELECT id, name FROM products")}
    yield {"conn": conn, "ids": ids, "client": create_app(path).test_client()}
    conn.close()


def two(env, a, b):
    return cmp.compare(env["conn"], a, b)


def test_gentle_beats_harsh_cleanser_with_reasons(env):
    ids = env["ids"]
    r = two(env, {"product_id": ids["Gentle Hydrating Cleanser"]}, {"product_id": ids["Deep Clean Foaming Face Wash"]})
    assert r["winner"] == "a" and "Gentle Hydrating Cleanser" in r["headline"]
    assert r["a"]["profile"]["safety"] > r["b"]["profile"]["safety"]
    text = " ".join(r["reasons"])
    assert "Methylisothiazolinone" in text and "Sodium Laureth Sulfate" in text
    assert any(p["inci_name"] == "Methylisothiazolinone" and p["points"] == 12 for p in r["b"]["profile"]["penalties"])


def test_winner_flips_when_sides_swap(env):
    ids = env["ids"]
    a, b = {"product_id": ids["Gentle Hydrating Cleanser"]}, {"product_id": ids["Deep Clean Foaming Face Wash"]}
    assert two(env, a, b)["winner"] == "a" and two(env, b, a)["winner"] == "b"


def test_pasted_lists_and_penalty_math(env):
    r = two(env, {"text": "Water, Glycerin, Niacinamide, Panthenol"}, {"text": "Water, Parfum, Sodium Lauryl Sulfate, Alcohol Denat."})
    pa, pb = r["a"]["profile"], r["b"]["profile"]
    assert pa["safety"] == 100
    assert pb["safety"] == 100 - 7 - 12 - 7  # Parfum (irritancy 3), SLS (4), Alcohol Denat. (3)
    assert pa["overall"] == round(0.6 * pa["safety"] + 0.4 * pa["benefit"], 1)
    assert r["winner"] == "a" and r["shared"] == ["Water"]


def test_identical_lists_are_a_tie(env):
    t = "Water, Glycerin, Niacinamide"
    r = two(env, {"text": t}, {"text": t})
    assert r["winner"] == "tie" and "close" in r["headline"].lower()


def test_unknown_ingredients_reported_not_scored(env):
    r = two(env, {"text": "Water, Foo One, Foo Two, Foo Three"}, {"text": "Water, Glycerin"})
    assert r["a"]["profile"]["unknown"] == ["Foo One", "Foo Two", "Foo Three"]
    assert r["a"]["profile"]["safety"] == 100
    assert any("not recognised" in n for n in r["notes"])


def test_different_categories_get_a_note(env):
    ids = env["ids"]
    r = two(env, {"product_id": ids["Velvet Bloom Matte Lipstick"]}, {"product_id": ids["10% Niacinamide Clarifying Serum"]})
    assert any("different product types" in n for n in r["notes"])


def test_skin_fit_and_concerns(env):
    ids = env["ids"]
    r = two(env, {"product_id": ids["Barrier Repair Moisturiser"]}, {"product_id": ids["Matte Control Foundation"]})
    fit = {f["skin_type"]: f for f in r["a"]["profile"]["skin_fit"]}
    assert fit["dry"]["suitable"] and fit["sensitive"]["suitable"]
    bfit = {f["skin_type"]: f for f in r["b"]["profile"]["skin_fit"]}
    assert not bfit["sensitive"]["suitable"] and not bfit["dry"]["suitable"]
    assert any(c["concern"] == "dryness" for c in r["a"]["profile"]["helps_concerns"])


def test_compare_input_errors(env):
    ids = env["ids"]
    one = {"product_id": ids["Gentle Hydrating Cleanser"]}
    for a, b in ((one, one), (one, {}), (one, {"text": "Water"}), (one, {"product_id": 99999}), (one, {"product_id": "abc"}),
                 (one, {"text": "x, y" * 5000}), (None, one)):
        with pytest.raises(cmp.CompareError):
            two(env, a, b)


def test_dupes_same_category_sorted_and_bounded(env):
    d = cmp.find_dupes(env["conn"], env["ids"]["10% Niacinamide Clarifying Serum"])
    assert d["dupes"] and all(x["category"] == "serum" for x in d["dupes"])
    sims = [x["similarity"] for x in d["dupes"]]
    assert sims == sorted(sims, reverse=True)
    for x in d["dupes"]:
        assert 0 <= x["ingredient_match"] <= 100 and 0 <= x["attribute_match"] <= 100 and 0 <= x["similarity"] <= 100
        assert x["id"] != env["ids"]["10% Niacinamide Clarifying Serum"]
        assert x["shared_count"] == len(x["shared"]) and "Water" not in x["shared"]


def test_dupes_cheaper_filter(env):
    d = cmp.find_dupes(env["conn"], env["ids"]["Pigment Fade Tranexamic Serum"], cheaper_only=True)
    assert d["dupes"] and all(x["price_difference"] < 0 and x["price_difference_pct"] < 0 for x in d["dupes"])


def test_api(env):
    c, ids = env["client"], env["ids"]
    r = c.post("/api/compare", json={"a": {"product_id": ids["Gentle Hydrating Cleanser"]}, "b": {"text": "Water, Parfum, Linalool"}})
    assert r.status_code == 200 and r.json["headline"] and r.json["disclaimer"]
    assert c.post("/api/compare", json={"a": {}, "b": {}}).status_code == 400
    assert c.post("/api/compare", data="x").status_code == 400
    d = c.get(f"/api/products/{ids['Hydra Plump Hyaluronic Serum']}/dupes")
    assert d.status_code == 200 and d.json["dupes"]
    assert c.get("/api/products/99999/dupes").status_code == 404
