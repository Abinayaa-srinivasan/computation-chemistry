"""SQLite helpers. Uses only the standard library (sqlite3) so setup stays simple."""
import os
import sqlite3

DB_PATH = os.environ.get(
    "DERMALENS_DB", os.path.join(os.path.dirname(__file__), "..", "dermalens.db")
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS categories (
    name TEXT PRIMARY KEY, meaning TEXT
);
CREATE TABLE IF NOT EXISTS ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inci_name TEXT UNIQUE NOT NULL,
    norm_name TEXT NOT NULL,
    aliases TEXT NOT NULL,            -- JSON list
    categories TEXT NOT NULL,         -- JSON list
    description TEXT,
    irritancy INTEGER DEFAULT 0,      -- 0-5 rough educational estimate
    comedogenic INTEGER DEFAULT 0,    -- 0-5 rough educational estimate
    flags TEXT NOT NULL,              -- JSON list
    skin_types TEXT NOT NULL,         -- JSON list
    incompatible_with TEXT NOT NULL,  -- JSON list
    typical_min REAL, typical_max REAL,
    range_source TEXT,
    is_sample_data INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS alias_index (
    alias_norm TEXT PRIMARY KEY,
    ingredient_id INTEGER NOT NULL REFERENCES ingredients(id)
);
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL, brand TEXT NOT NULL, category TEXT NOT NULL,
    size TEXT, price REAL, image TEXT,
    is_sample_data INTEGER DEFAULT 1,
    status TEXT DEFAULT 'approved'    -- pending / approved / rejected (contributions)
);
CREATE TABLE IF NOT EXISTS product_ingredients (
    product_id INTEGER NOT NULL REFERENCES products(id),
    position INTEGER NOT NULL,        -- label order, 1 = highest concentration
    ingredient_id INTEGER REFERENCES ingredients(id),
    raw_name TEXT NOT NULL,
    PRIMARY KEY (product_id, position)
);
CREATE TABLE IF NOT EXISTS retailer_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id),
    retailer TEXT NOT NULL, url TEXT NOT NULL, price REAL
);
CREATE TABLE IF NOT EXISTS category_ingredients (
    category TEXT NOT NULL, ingredient_id INTEGER NOT NULL REFERENCES ingredients(id),
    role TEXT, typical_min REAL, typical_max REAL, why TEXT,
    PRIMARY KEY (category, ingredient_id)
);
CREATE TABLE IF NOT EXISTS concerns (
    name TEXT PRIMARY KEY, label TEXT NOT NULL, description TEXT
);
CREATE TABLE IF NOT EXISTS concern_ingredients (
    concern TEXT NOT NULL REFERENCES concerns(name),
    ingredient_id INTEGER NOT NULL REFERENCES ingredients(id),
    priority INTEGER NOT NULL,        -- 3 first-line, 2 good option, 1 supporting
    why TEXT, how_to_use TEXT, caution TEXT,
    PRIMARY KEY (concern, ingredient_id)
);
CREATE TABLE IF NOT EXISTS concern_avoid (
    concern TEXT NOT NULL REFERENCES concerns(name), item TEXT NOT NULL, why TEXT
);
CREATE TABLE IF NOT EXISTS concern_tips (
    concern TEXT NOT NULL REFERENCES concerns(name), tip TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    is_admin INTEGER DEFAULT 0,
    skin_type TEXT DEFAULT '',
    concerns TEXT DEFAULT '[]',        -- JSON list
    allergies TEXT DEFAULT '[]',       -- JSON list of avoid-option keys
    avoid_text TEXT DEFAULT '',
    pregnant INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS user_products (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    shelf TEXT NOT NULL CHECK (shelf IN ('own','want','used')),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, product_id)
);
CREATE TABLE IF NOT EXISTS user_ingredients (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ingredient_id INTEGER NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
    kind TEXT NOT NULL CHECK (kind IN ('liked','avoided')),
    PRIMARY KEY (user_id, ingredient_id)
);
CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    text TEXT NOT NULL, verdict TEXT, total INTEGER, recognised INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS edit_suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    message TEXT NOT NULL, new_ingredients TEXT DEFAULT '',
    status TEXT DEFAULT 'pending',     -- pending / approved / rejected
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS routines (      -- shared routine links (not wiped when re-seeding)
    token TEXT PRIMARY KEY, name TEXT NOT NULL, data TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
"""


def connect(path=None):
    conn = sqlite3.connect(path or os.environ.get("DERMALENS_DB") or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(path=None):
    conn = connect(path)
    conn.executescript(SCHEMA)
    # light migration: databases created by older milestones lack products.submitted_by
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(products)")}
    if "submitted_by" not in cols:
        conn.execute("ALTER TABLE products ADD COLUMN submitted_by INTEGER")
    conn.commit()
    return conn
