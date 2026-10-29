"""Milestone 1 tests: seed data integrity, normalisation and API endpoints."""
import os
import tempfile

import pytest

from app.main import create_app
from app.normalize import normalize, split_ingredient_list
from seed.ingredients_data import parse, CATEGORIES
from seed.load import load


@pytest.fixture(scope="module")
def client():
    path = os.path.join(tempfile.mkdtemp(), "t.db")
    counts, unknown = load(path, quiet=True)
    assert unknown == [], f"Seed products use unknown ingredients: {unknown}"
    app = create_app(path)
    return app.test_client()


def test_normalize():
    assert normalize("Aqua / Water ") == "aqua / water"
    assert normalize("Sodium  Hyaluronate.") == "sodium hyaluronate"
    assert normalize("Titanium Dioxide (nano)") == "titanium dioxide"
    assert normalize("Parfum") == normalize("PARFUM")


def test_split():
    assert split_ingredient_list("Ingredients: Water, Glycerin; Niacinamide.") == ["Water", "Glycerin", "Niacinamide"]


def test_ingredient_data_valid():
    items = parse()
    assert len(items) >= 150
    names = [i["inci_name"] for i in items]
    assert len(names) == len(set(names)), "duplicate INCI names"
    known = {c for c, _ in CATEGORIES}
    for i in items:
        assert set(i["categories"]) <= known, i["inci_name"]
        assert 0 <= i["irritancy"] <= 5 and 0 <= i["comedogenic"] <= 5
        if i["typical_min"] is not None and i["typical_max"] is not None:
            assert i["typical_min"] <= i["typical_max"], i["inci_name"]


def test_health(client):
    assert client.get("/api/health").json == {"status": "ok"}


def test_search_product_and_brand(client):
    r = client.get("/api/search?q=niacinamide").json
    assert any("Niacinamide" in p["name"] for p in r["products"])
    r = client.get("/api/search?q=Dermis").json
    assert "Dermis Daily" in r["brands"] and r["products"]
    assert client.get("/api/search?q=").json == {"products": [], "brands": []}


def test_product_detail_has_ingredients_and_links(client):
    pid = client.get("/api/search?q=Vitamin C").json["products"][0]["id"]
    p = client.get(f"/api/products/{pid}").json
    assert p["ingredients"][0]["raw_name"] == "Water"
    assert [i["position"] for i in p["ingredients"]] == list(range(1, len(p["ingredients"]) + 1))
    assert all(i["recognised"] for i in p["ingredients"])
    assert len(p["where_to_buy"]) >= 2 and p["is_sample_data"] is True
    assert client.get("/api/products/99999").status_code == 404


def test_category_basics_have_ranges(client):
    cats = {c["name"] for c in client.get("/api/categories").json["categories"]}
    assert {"lipstick", "foundation", "moisturiser", "sunscreen", "serum", "cleanser", "shampoo", "mascara"} <= cats
    d = client.get("/api/categories/lipstick").json
    assert d["basic_ingredients"] and d["products"]
    for b in d["basic_ingredients"]:
        assert b["typical_min"] is not None and b["typical_max"] >= b["typical_min"]
    assert "typical" in d["range_note"].lower()
    assert client.get("/api/categories/nonexistent").status_code == 404


def test_ingredient_endpoints(client):
    r = client.get("/api/ingredients?q=glycolic").json["ingredients"]
    assert r and "Exfoliant" in r[0]["categories"]
    one = client.get(f"/api/ingredients/{r[0]['id']}").json
    assert "range_note" in one and one["is_sample_data"] is True
    hum = client.get("/api/ingredients?category=Humectant").json["ingredients"]
    assert any(i["inci_name"] == "Glycerin" for i in hum)


def test_frontend_is_served(client):
    r = client.get("/")
    assert r.status_code == 200 and b"DermaLens" in r.data
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/static/style.css").status_code == 200


def test_static_files_are_not_cached(client):
    assert client.get("/static/app.js").headers["Cache-Control"] == "no-cache"
    assert client.get("/").headers["Cache-Control"] == "no-cache"
