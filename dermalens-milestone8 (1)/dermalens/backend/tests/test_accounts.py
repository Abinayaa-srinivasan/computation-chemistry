"""Milestone 7 tests: signup/login, tokens, profile, shelves, history, match score, contributions, admin."""
import os
import tempfile

import pytest

from app import auth
from app.db import connect
from app.main import create_app
from seed.load import load

ING = "Water, Glycerin, Niacinamide, Sodium Hyaluronate, Panthenol, Phenoxyethanol"


@pytest.fixture(scope="module")
def env():
    path = os.path.join(tempfile.mkdtemp(), "t.db")
    load(path, quiet=True)
    os.environ["DERMALENS_SECRET"] = "test-secret"
    yield {"client": create_app(path).test_client(), "path": path}


def signup(c, email, name="Test", pw="password123"):
    r = c.post("/api/auth/signup", json={"email": email, "display_name": name, "password": pw})
    return r


def hdr(tok):
    return {"Authorization": "Bearer " + tok}


@pytest.fixture(scope="module")
def users(env):
    c = env["client"]
    a = signup(c, "admin@example.com").get_json()["token"]
    conn = connect(env["path"])
    conn.execute("UPDATE users SET is_admin=1 WHERE email='admin@example.com'")
    conn.commit()
    conn.close()
    b = signup(c, "user@example.com").get_json()["token"]
    return {"admin": a, "user": b}


def test_password_hash_and_token():
    h = auth.hash_password("hello12345")
    assert "hello12345" not in h and auth.verify_password("hello12345", h) and not auth.verify_password("nope", h)
    os.environ["DERMALENS_SECRET"] = "s"
    t = auth.create_token(7)
    assert auth.read_token(t) == 7
    assert auth.read_token(t + "x") is None
    assert auth.read_token(auth.create_token(7, now=1)) is None  # expired long ago


def test_token_rejects_none_algorithm():
    import base64, json
    b = lambda d: base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=").decode()
    fake = b({"alg": "none"}) + "." + b({"sub": "1", "exp": 9999999999}) + "."
    assert auth.read_token(fake) is None


def test_signup_validation_and_duplicates(env, users):
    c = env["client"]
    assert signup(c, "bad").status_code == 400
    assert signup(c, "x@example.com", pw="short").status_code == 400
    assert signup(c, "user@example.com").status_code == 409
    assert signup(c, "USER@example.com").status_code == 409  # case-insensitive


def test_login_and_wrong_password(env, users):
    c = env["client"]
    ok = c.post("/api/auth/login", json={"email": "user@example.com", "password": "password123"})
    assert ok.status_code == 200 and ok.get_json()["token"]
    bad = c.post("/api/auth/login", json={"email": "user@example.com", "password": "wrongwrong"})
    assert bad.status_code == 401
    assert "password_hash" not in ok.get_data(as_text=True)


def test_login_throttle(env, users):
    c = env["client"]
    for _ in range(5):
        c.post("/api/auth/login", json={"email": "throttle@example.com", "password": "x"})
    assert c.post("/api/auth/login", json={"email": "throttle@example.com", "password": "x"}).status_code == 429


def test_requires_login(env):
    c = env["client"]
    assert c.get("/api/me").status_code == 401
    assert c.get("/api/me", headers=hdr("garbage")).status_code == 401
    assert c.get("/api/admin/pending").status_code == 401


def test_profile_roundtrip_and_validation(env, users):
    c, h = env["client"], hdr(users["user"])
    r = c.put("/api/me/profile", headers=h, json={"skin_type": "oily", "concerns": ["acne"], "allergies": ["fragrance"], "pregnant": False})
    assert r.status_code == 200
    assert c.get("/api/me", headers=h).get_json()["profile"]["skin_type"] == "oily"
    assert c.put("/api/me/profile", headers=h, json={"skin_type": "purple"}).status_code == 400
    assert c.put("/api/me/profile", headers=h, json={"concerns": ["nonsense"]}).status_code == 400


def test_shelves_are_private(env, users):
    c = env["client"]
    assert c.put("/api/me/shelves/1", headers=hdr(users["user"]), json={"shelf": "own"}).status_code == 200
    assert c.put("/api/me/shelves/1", headers=hdr(users["user"]), json={"shelf": "bogus"}).status_code == 400
    assert c.put("/api/me/shelves/99999", headers=hdr(users["user"]), json={"shelf": "own"}).status_code == 404
    mine = c.get("/api/me/shelves", headers=hdr(users["user"])).get_json()
    other = c.get("/api/me/shelves", headers=hdr(users["admin"])).get_json()
    assert len(mine["own"]) == 1 and other["own"] == []
    assert c.delete("/api/me/shelves/1", headers=hdr(users["user"])).status_code == 200


def test_history_saved_only_when_asked_and_private(env, users):
    c, h = env["client"], hdr(users["user"])
    c.post("/api/analyze", headers=h, json={"text": ING})  # not saved
    assert c.get("/api/me/history", headers=h).get_json()["history"] == []
    c.post("/api/analyze", headers=h, json={"text": ING, "save": True})
    hist = c.get("/api/me/history", headers=h).get_json()["history"]
    assert len(hist) == 1 and hist[0]["verdict"]
    hid = hist[0]["id"]
    assert c.get(f"/api/me/history/{hid}", headers=hdr(users["admin"])).status_code == 404  # not theirs
    assert c.get(f"/api/me/history/{hid}", headers=h).get_json()["text"] == ING
    assert c.delete(f"/api/me/history/{hid}", headers=h).status_code == 200


def test_match_score(env, users):
    c = env["client"]
    # admin has no profile yet
    r = c.get("/api/products/1/match", headers=hdr(users["admin"])).get_json()
    assert r["needs_profile"] is True
    c.put("/api/me/profile", headers=hdr(users["admin"]), json={"skin_type": "dry", "concerns": ["dryness"]})
    r = c.get("/api/products/1/match", headers=hdr(users["admin"])).get_json()
    assert 0 <= r["score"] <= 100 and r["breakdown"]


def test_match_zero_for_avoided_ingredient(env, users):
    c = env["client"]
    h = hdr(users["user"])
    conn = connect(env["path"])
    row = conn.execute("""SELECT pi.product_id, pi.ingredient_id FROM product_ingredients pi
                          WHERE pi.ingredient_id IS NOT NULL AND pi.position=2 LIMIT 1""").fetchone()
    conn.close()
    c.put("/api/me/profile", headers=h, json={"skin_type": "oily", "concerns": ["acne"]})
    assert c.put(f"/api/me/ingredients/{row['ingredient_id']}", headers=h, json={"kind": "avoided"}).status_code == 200
    r = c.get(f"/api/products/{row['product_id']}/match", headers=h).get_json()
    assert r["score"] == 0 and r["reasons"]
    c.delete(f"/api/me/ingredients/{row['ingredient_id']}", headers=h)


def test_contribution_flow_and_admin_queue(env, users):
    c = env["client"]
    u, a = hdr(users["user"]), hdr(users["admin"])
    body = {"name": "Test Serum Zed", "brand": "Nobrand", "category": "serum", "ingredients": ING}
    assert c.post("/api/contributions", json=body).status_code == 401
    assert c.post("/api/contributions", headers=u, json={**body, "category": "weapon"}).status_code == 400
    assert c.post("/api/contributions", headers=u, json={**body, "ingredients": "Water"}).status_code == 400
    r = c.post("/api/contributions", headers=u, json=body)
    assert r.status_code == 201
    pid = r.get_json()["id"]
    assert c.post("/api/contributions", headers=u, json=body).status_code == 409  # duplicate
    # pending products are hidden from the public
    assert c.get(f"/api/products/{pid}").status_code == 404
    assert "Test Serum Zed" not in c.get("/api/search?q=Zed").get_data(as_text=True)
    # normal users cannot use the admin queue
    assert c.get("/api/admin/pending", headers=u).status_code == 403
    assert c.post(f"/api/admin/products/{pid}/approve", headers=u).status_code == 403
    pend = c.get("/api/admin/pending", headers=a).get_json()["products"]
    assert any(p["id"] == pid for p in pend)
    assert c.post(f"/api/admin/products/{pid}/approve", headers=a).status_code == 200
    assert c.get(f"/api/products/{pid}").status_code == 200
    assert c.post(f"/api/admin/products/{pid}/approve", headers=a).status_code == 404  # already handled


def test_reject_keeps_product_hidden(env, users):
    c = env["client"]
    u, a = hdr(users["user"]), hdr(users["admin"])
    pid = c.post("/api/contributions", headers=u, json={"name": "Rejected Thing", "brand": "Nobrand", "category": "serum", "ingredients": ING}).get_json()["id"]
    c.post(f"/api/admin/products/{pid}/reject", headers=a)
    assert c.get(f"/api/products/{pid}").status_code == 404


def test_pending_limit(env, users):
    c = env["client"]
    h = hdr(signup(env["client"], "spam@example.com").get_json()["token"])
    codes = [c.post("/api/contributions", headers=h, json={"name": f"Spam item {i}", "brand": "Spamco", "category": "serum", "ingredients": ING}).status_code for i in range(7)]
    assert codes[:5] == [201] * 5 and codes[5] == 429


def test_suggest_edit_updates_ingredients_on_approval(env, users):
    c = env["client"]
    u, a = hdr(users["user"]), hdr(users["admin"])
    assert c.post("/api/products/1/suggest-edit", headers=u, json={"message": "no"}).status_code == 400
    r = c.post("/api/products/1/suggest-edit", headers=u, json={"message": "Label changed", "ingredients": "Water, Glycerin, Squalane, Panthenol"})
    sid = r.get_json()["id"]
    assert c.post(f"/api/admin/suggestions/{sid}/approve", headers=u).status_code == 403
    assert c.post(f"/api/admin/suggestions/{sid}/approve", headers=a).status_code == 200
    names = [i["raw_name"] for i in c.get("/api/products/1").get_json()["ingredients"]]
    assert names == ["Water", "Glycerin", "Squalane", "Panthenol"]


def test_delete_account(env, users):
    c = env["client"]
    tok = signup(c, "gone@example.com").get_json()["token"]
    assert c.delete("/api/me", headers=hdr(tok), json={"password": "wrong"}).status_code == 403
    assert c.delete("/api/me", headers=hdr(tok), json={"password": "password123"}).status_code == 200
    assert c.get("/api/me", headers=hdr(tok)).status_code == 401
