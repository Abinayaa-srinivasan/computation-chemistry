"""Authentication helpers using only the Python standard library.

* Passwords: scrypt (a memory-hard password hash) with a random salt per user. We never store passwords.
* Tokens: JWT, algorithm HS256 = HMAC-SHA256 over "header.payload". We reject any other algorithm,
  check the signature with a constant-time comparison, and check the expiry time.
* The signing secret comes from the DERMALENS_SECRET environment variable, or a random one is created
  once and saved in backend/.secret (keep that file private; never commit it).
"""
import base64
import hashlib
import hmac
import json
import os
import secrets
import time

TOKEN_LIFETIME = 7 * 24 * 3600  # 7 days
_SCRYPT = dict(n=2 ** 14, r=8, p=1, dklen=32)
_secret_cache = None


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def get_secret() -> bytes:
    global _secret_cache
    env = os.environ.get("DERMALENS_SECRET")
    if env:
        return env.encode()
    if _secret_cache is None:
        path = os.path.join(os.path.dirname(__file__), "..", ".secret")
        if os.path.exists(path):
            _secret_cache = open(path, "rb").read().strip()
        else:
            _secret_cache = secrets.token_hex(32).encode()
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "wb") as f:
                f.write(_secret_cache)
    return _secret_cache


# ---------------------------------------------------------------- passwords
def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    h = hashlib.scrypt(password.encode(), salt=salt, **_SCRYPT)
    return "scrypt$%d$%d$%d$%s$%s" % (_SCRYPT["n"], _SCRYPT["r"], _SCRYPT["p"], _b64(salt), _b64(h))


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt, expected = stored.split("$")
        if scheme != "scrypt":
            return False
        h = hashlib.scrypt(password.encode(), salt=_unb64(salt), n=int(n), r=int(r), p=int(p), dklen=len(_unb64(expected)))
        return hmac.compare_digest(h, _unb64(expected))
    except (ValueError, TypeError):
        return False


DUMMY_HASH = hash_password("not-a-real-password")  # lets login take the same time for unknown emails


# ---------------------------------------------------------------- JWT
def create_token(user_id: int, now=None) -> str:
    now = int(now or time.time())
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = _b64(json.dumps({"sub": str(user_id), "iat": now, "exp": now + TOKEN_LIFETIME}, separators=(",", ":")).encode())
    sig = hmac.new(get_secret(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
    return f"{header}.{payload}.{_b64(sig)}"


def read_token(token: str, now=None):
    """Return the user id if the token is valid and unexpired, else None."""
    try:
        header_b, payload_b, sig_b = token.split(".")
        header = json.loads(_unb64(header_b))
        if header.get("alg") != "HS256":  # never trust the token to choose its own algorithm
            return None
        expected = hmac.new(get_secret(), f"{header_b}.{payload_b}".encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _unb64(sig_b)):
            return None
        payload = json.loads(_unb64(payload_b))
        if int(payload["exp"]) < int(now or time.time()):
            return None
        return int(payload["sub"])
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return None
