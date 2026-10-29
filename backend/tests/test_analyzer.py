"""Milestone 3 tests: matching, classification, verdicts, conflicts and the analyze/OCR endpoints."""
import io
import os
import tempfile

import pytest

from app import analyzer as az
from app.db import connect
from app.main import create_app
from app.normalize import split_ingredient_list
from seed.load import load


@pytest.fixture(scope="module")
def env():
    path = os.path.join(tempfile.mkdtemp(), "t.db")
    load(path, quiet=True)
    conn = connect(path)
    yield {"conn": conn, "catalog": az.load_catalog(conn), "client": create_app(path).test_client()}
    conn.close()


def run(env, text):
    return az.analyze(env["conn"], text, env["catalog"])


def test_split_handles_ocr_line_wraps():
    text = "INGREDIENTS: Aqua, Sodium Hyalu-\nronate, Glyc\nerin,\nNiacinamide."
    assert split_ingredient_list(text) == ["Aqua", "Sodium Hyaluronate", "Glyc erin", "Niacinamide"]
    assert split_ingredient_list("Water\nGlycerin\nNiacinamide") == ["Water", "Glycerin", "Niacinamide"]


def test_exact_alias_and_slash_matching(env):
    r = run(env, "Aqua, Vitamin C, Aqua / Water")
    assert [i["inci_name"] for i in r["ingredients"]] == ["Water", "Ascorbic Acid", "Water"]
    assert all(i["match"] == "exact" for i in r["ingredients"])


def test_fuzzy_fixes_typos_but_not_nonsense(env):
    r = run(env, "Niacinamid, Glycerinn, Xyzzy Blorp")
    a, b, c = r["ingredients"]
    assert (a["inci_name"], a["match"]) == ("Niacinamide", "fuzzy") and a["corrected_from"] == "Niacinamid"
    assert b["inci_name"] == "Glycerin" and b["match"] == "fuzzy"
    assert c["recognised"] is False


def test_unknown_ingredient_gets_suggestion(env):
    r = run(env, "Sodium Cocoamphoacetate, Hydrolyzed Wheat Protein")
    first = r["unrecognised"][0]["suggestion"]
    assert first["category"] == "Surfactant" and first["method"] == "keyword rule"
    for u in r["unrecognised"]:
        assert 0 <= u["suggestion"]["confidence"] <= 1


def test_verdict_safe_for_simple_gentle_list(env):
    r = run(env, "Water, Glycerin, Panthenol, Sodium Hyaluronate, Allantoin, Phenoxyethanol")
    assert r["verdict"]["level"] == "good" and r["verdict"]["label"] == "Generally safe"


def test_verdict_caution_for_fragrance(env):
    r = run(env, "Water, Glycerin, Parfum, Linalool")
    assert r["verdict"]["level"] == "warn"
    assert "Parfum" in r["flags"]["fragrance"]


def test_verdict_not_suitable_for_retinol_with_reasons(env):
    r = run(env, "Water, Retinol, Squalane")
    assert r["verdict"]["level"] == "bad"
    assert any("pregnant" in x for x in r["verdict"]["reasons"])
    assert r["flags"]["pregnancy_caution"] == ["Retinol"]


def test_conflict_detected_once(env):
    r = run(env, "Water, Retinol, Glycolic Acid, Salicylic Acid")
    pairs = {(c["a"], c["b"]) for c in r["conflicts"]}
    assert ("Glycolic Acid", "Retinol") in pairs and ("Retinol", "Salicylic Acid") in pairs
    assert len(r["conflicts"]) == len(pairs)


def test_key_groups_and_summary(env):
    r = run(env, "Water, Glycolic Acid, Sodium Hyaluronate, Tocopherol")
    groups = {g["group"] for g in r["key_groups"]}
    assert {"Exfoliant", "Humectant", "Antioxidant"} <= groups
    assert "exfoliating" in r["summary"]


def test_many_unknowns_lower_certainty(env):
    r = run(env, "Water, Foo One, Foo Two, Foo Three")
    assert any("not recognised" in x for x in r["verdict"]["reasons"])


def test_same_input_same_output(env):
    t = "Water, Retinol, Parfum, Niacinamid"
    assert run(env, t) == run(env, t)


def test_analyze_endpoint(env):
    c = env["client"]
    r = c.post("/api/analyze", json={"text": "Water, Glycerin"})
    assert r.status_code == 200 and r.json["total"] == 2 and "disclaimer" in r.json
    assert c.post("/api/analyze", json={"text": "  "}).status_code == 400
    assert c.post("/api/analyze", json={"text": "x" * 9000}).status_code == 400
    assert c.post("/api/analyze", data="notjson").status_code == 400


def test_ocr_endpoint_errors(env):
    c = env["client"]
    assert c.post("/api/ocr").status_code == 400
    r = c.post("/api/ocr", data={"image": (io.BytesIO(b"not an image"), "x.png")}, content_type="multipart/form-data")
    assert r.status_code in (400, 501)


def test_ocr_reads_a_generated_label(env):
    pytest.importorskip("pytesseract")
    from PIL import Image, ImageDraw, ImageFont
    import shutil
    if not shutil.which("tesseract"):
        pytest.skip("Tesseract program not installed")
    img = Image.new("RGB", (1400, 260), "white")
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 40)
    except OSError:
        font = ImageFont.load_default()
    d.text((30, 30), "INGREDIENTS: Water, Glycerin, Niacinamide,", fill="black", font=font)
    d.text((30, 110), "Panthenol, Sodium Hyaluronate, Phenoxyethanol", fill="black", font=font)
    buf = io.BytesIO(); img.save(buf, "PNG"); buf.seek(0)
    r = env["client"].post("/api/ocr", data={"image": (buf, "label.png")}, content_type="multipart/form-data")
    assert r.status_code == 200
    names = [i["inci_name"] for i in run(env, r.json["text"])["ingredients"] if i["recognised"]]
    assert {"Water", "Glycerin", "Niacinamide", "Panthenol"} <= set(names)
