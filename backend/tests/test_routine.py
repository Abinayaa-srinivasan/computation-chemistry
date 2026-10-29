"""Milestone 6 tests: routine checks, weekly schedule, sharing and validation."""
import os
import tempfile

import pytest

from app import routine as rt
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


def item(env, name, freq="daily"):
    return {"product_id": env["ids"][name], "frequency": freq}


def titles(r, level=None):
    return [w["title"] for w in r["warnings"] if level is None or w["level"] == level]


def test_daily_clash_in_same_slot_is_a_warning(env):
    spec = {"am": [item(env, "Daily Shield Mineral SPF 50")],
            "pm": [item(env, "Retinol Renewal Cream"), item(env, "Glow AHA Exfoliating Serum")]}
    r = rt.check(env["conn"], spec)
    assert r["status"] == "warn"
    assert any("clash in your PM routine" in t for t in titles(r, "warn"))
    ov = r["slots"]["pm"]["schedule"]["overlaps"]
    assert ov and len(ov[0]["days"]) == 7


def test_non_daily_clash_is_scheduled_on_different_days(env):
    spec = {"am": [item(env, "Daily Shield Mineral SPF 50")],
            "pm": [item(env, "Retinol Renewal Cream", "3x_week"), item(env, "Glow AHA Exfoliating Serum", "2x_week")]}
    r = rt.check(env["conn"], spec)
    rows = {x["title"]: set(x["days"]) for x in r["slots"]["pm"]["schedule"]["rows"]}
    assert len(rows["Retinol Renewal Cream"]) == 3 and len(rows["Glow AHA Exfoliating Serum"]) == 2
    assert rows["Retinol Renewal Cream"].isdisjoint(rows["Glow AHA Exfoliating Serum"])
    assert r["status"] == "good" and any("different days" in t for t in titles(r, "info"))


def test_clash_across_am_and_pm_is_a_good_note(env):
    spec = {"am": [item(env, "Vitamin C Brightening Serum"), item(env, "Daily Shield Mineral SPF 50")],
            "pm": [item(env, "Retinol Renewal Cream")]}
    r = rt.check(env["conn"], spec)
    assert "Good: clashing products are kept apart" in titles(r, "good")
    assert not any("clash in your" in t for t in titles(r, "warn"))


def test_sunscreen_missing_with_actives_warns(env):
    r = rt.check(env["conn"], {"am": [item(env, "Glow AHA Exfoliating Serum")], "pm": []})
    assert "Add a sunscreen to your morning routine" in titles(r, "warn")
    ok = rt.check(env["conn"], {"am": [item(env, "Glow AHA Exfoliating Serum"), item(env, "Daily Shield Mineral SPF 50")], "pm": []})
    assert "Add a sunscreen to your morning routine" not in titles(ok)


def test_retinoid_in_morning_and_sunscreen_at_night(env):
    r = rt.check(env["conn"], {"am": [item(env, "Retinol Renewal Cream")], "pm": [item(env, "Daily Shield Mineral SPF 50")]})
    assert any("retinoid in your morning routine" in t for t in titles(r, "warn"))
    assert "Sunscreen in your evening routine" in titles(r, "info")


def test_over_exfoliation(env):
    r = rt.check(env["conn"], {"am": [item(env, "Daily Shield Mineral SPF 50")],
                               "pm": [item(env, "Glow AHA Exfoliating Serum"), item(env, "Pore Clear BHA Serum")]})
    assert "Possible over-exfoliation" in titles(r, "warn")


def test_suggested_order(env):
    spec = {"am": [item(env, "Daily Shield Mineral SPF 50"), item(env, "Barrier Repair Moisturiser"),
                   item(env, "10% Niacinamide Clarifying Serum"), item(env, "Gentle Hydrating Cleanser")], "pm": []}
    order = [x["category"] for x in rt.check(env["conn"], spec)["slots"]["am"]["suggested_order"]]
    assert order == ["cleanser", "serum", "moisturiser", "sunscreen"]


def test_duplicate_active_info(env):
    spec = {"am": [item(env, "10% Niacinamide Clarifying Serum"), item(env, "Pigment Fade Tranexamic Serum"), item(env, "Daily Shield Mineral SPF 50")], "pm": []}
    assert "Niacinamide appears in 2 products" in titles(rt.check(env["conn"], spec), "info")


def test_pasted_custom_product(env):
    spec = {"am": [{"text": "Water, Retinol, Squalane", "name": "My night oil", "category": "serum", "frequency": "daily"}],
            "pm": [{"text": "Water, Glycolic Acid, Glycerin", "name": "My toner", "category": "serum", "frequency": "daily"}]}
    r = rt.check(env["conn"], spec)
    assert r["slots"]["am"]["items"][0]["title"] == "My night oil"
    assert "Good: clashing products are kept apart" in titles(r, "good")


def test_validation(env):
    bad = [None, {}, {"am": "x"}, {"am": [{"product_id": 9999}]}, {"am": [{"product_id": env["ids"]["Daily Shield Mineral SPF 50"], "frequency": "hourly"}]},
           {"am": [item(env, "Daily Shield Mineral SPF 50")] * 11}, {"pm": [{"text": "Water"}]}, {"am": [5]}]
    for spec in bad:
        with pytest.raises(rt.RoutineError):
            rt.check(env["conn"], spec)


def test_schedule_is_deterministic_and_valid(env):
    spec = {"am": [], "pm": [item(env, "Retinol Renewal Cream", "3x_week"), item(env, "Glow AHA Exfoliating Serum", "weekly"),
                             item(env, "Pore Clear BHA Serum", "2x_week")]}
    a, b = rt.check(env["conn"], spec), rt.check(env["conn"], spec)
    assert a == b
    for row in a["slots"]["pm"]["schedule"]["rows"]:
        assert all(0 <= d <= 6 for d in row["days"]) and len(row["days"]) == rt.FREQ[row["frequency"]]


def test_api_check_share_and_load(env):
    c = env["client"]
    spec = {"name": "Evening plan", "am": [item(env, "Daily Shield Mineral SPF 50")], "pm": [item(env, "Barrier Repair Moisturiser", "3x_week")]}
    assert c.post("/api/routine/check", json=spec).json["status"] in ("good", "warn")
    r = c.post("/api/routines", json=spec)
    assert r.status_code == 201
    token = r.json["token"]
    got = c.get(f"/api/routines/{token}").json
    assert got["name"] == "Evening plan" and got["pm"][0]["frequency"] == "3x_week"
    assert c.get("/api/routines/nope").status_code == 404
    assert c.post("/api/routines", json={"am": [], "pm": []}).status_code == 400
    assert c.post("/api/routine/check", data="x").status_code == 400
    long = c.post("/api/routines", json={**spec, "name": "x" * 500}).json["token"]
    assert len(c.get(f"/api/routines/{long}").json["name"]) == 60


def test_shared_routines_survive_reseeding(env):
    path = os.path.join(tempfile.mkdtemp(), "keep.db")
    load(path, quiet=True)
    c = create_app(path).test_client()
    conn = connect(path)
    pid = conn.execute("SELECT id FROM products LIMIT 1").fetchone()[0]
    conn.close()
    token = c.post("/api/routines", json={"am": [{"product_id": pid}], "pm": []}).json["token"]
    load(path, quiet=True)
    assert c.get(f"/api/routines/{token}").status_code == 200
