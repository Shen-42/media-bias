"""SQLite schema and connection helper. One database file: config [corpus].db."""

import sqlite3

from common import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS discovered_urls (
    url TEXT PRIMARY KEY,
    outlet TEXT NOT NULL,
    lastmod TEXT,
    url_date TEXT,
    source TEXT,
    topic_hint TEXT,          -- crash | bike_lane | transit (from URL slug)
    status TEXT DEFAULT 'new' -- new | fetched | failed | skipped
);

CREATE TABLE IF NOT EXISTS articles (
    id TEXT PRIMARY KEY,
    outlet TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    title TEXT,
    published TEXT,
    fetched_at TEXT,
    raw_path TEXT,
    text TEXT,
    topic_tags TEXT,          -- JSON list
    is_toronto INTEGER,
    is_crash INTEGER,
    severity TEXT,
    road_users TEXT,          -- JSON list
    hit_and_run INTEGER,
    article_type TEXT,
    crash_id TEXT,
    wire_group TEXT,
    is_canonical INTEGER DEFAULT 1,
    release_id INTEGER,
    release_score REAL
);

CREATE TABLE IF NOT EXISTS police_releases (
    id INTEGER PRIMARY KEY,
    url TEXT,
    wayback_ts TEXT,
    title TEXT,
    published TEXT,
    text TEXT,
    is_collision INTEGER,
    fetch_status TEXT
);

CREATE TABLE IF NOT EXISTS sentences (
    id TEXT PRIMARY KEY,      -- <article_id>:<h|b>:<idx>
    article_id TEXT NOT NULL,
    part TEXT NOT NULL,       -- headline | body
    idx INTEGER NOT NULL,
    text TEXT NOT NULL,
    is_crash INTEGER,
    is_vru INTEGER,
    quoted INTEGER,
    attributed INTEGER,
    release_sim REAL,
    release_char REAL,
    text_source TEXT
);
CREATE INDEX IF NOT EXISTS sentences_article ON sentences(article_id);

CREATE TABLE IF NOT EXISTS labels (
    sentence_id TEXT NOT NULL,
    label TEXT NOT NULL,
    source TEXT NOT NULL,     -- rule | lf:<name> | snorkel | setfit | nli
    value TEXT,               -- NULL = abstain
    score REAL,
    evidence TEXT,
    PRIMARY KEY (sentence_id, label, source)
);

CREATE TABLE IF NOT EXISTS article_labels (
    article_id TEXT NOT NULL,
    label TEXT NOT NULL,
    source TEXT NOT NULL,
    value TEXT,
    evidence TEXT,
    PRIMARY KEY (article_id, label, source)
);
"""


def connect(db_path: str | None = None) -> sqlite3.Connection:
    p = config.path(db_path or config.load()["corpus"]["db"])
    con = sqlite3.connect(p, timeout=60)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.executescript(SCHEMA)
    return con
