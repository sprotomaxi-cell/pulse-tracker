"""Database setup and helpers."""
import sqlite3
from config import Config


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS posts (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            source          TEXT NOT NULL,
            external_id     TEXT NOT NULL,
            title           TEXT,
            body            TEXT,
            author          TEXT,
            url             TEXT,
            subreddit       TEXT,
            score           INTEGER DEFAULT 0,
            num_comments    INTEGER DEFAULT 0,
            created_at      TEXT,
            ingested_at     TEXT NOT NULL,
            UNIQUE(source, external_id)
        );

        CREATE TABLE IF NOT EXISTS sentiments (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id         INTEGER NOT NULL REFERENCES posts(id),
            sentiment       TEXT NOT NULL,
            confidence      REAL,
            topics          TEXT,
            summary         TEXT,
            analyzed_at     TEXT NOT NULL,
            UNIQUE(post_id)
        );

        CREATE TABLE IF NOT EXISTS topics (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL UNIQUE,
            first_seen      TEXT NOT NULL,
            post_count      INTEGER DEFAULT 0
        );

        CREATE INDEX IF NOT EXISTS idx_posts_source ON posts(source);
        CREATE INDEX IF NOT EXISTS idx_posts_created ON posts(created_at);
        CREATE INDEX IF NOT EXISTS idx_sentiments_sentiment ON sentiments(sentiment);
    """)
    conn.close()
