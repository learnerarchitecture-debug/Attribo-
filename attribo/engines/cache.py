"""
SQLite evidence cache for fetched source pages.

Stored in the same database file as scan history. Pruned after 30 days by default.

(c) 2026 Attribo. All rights reserved.
"""
import datetime
import sqlite3

from ..storage.settings import APP_DIR

DB_FILE = APP_DIR / "attribo.db"


def _conn() -> sqlite3.Connection:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(DB_FILE))
    con.execute(
        "CREATE TABLE IF NOT EXISTS source_cache ("
        "url TEXT PRIMARY KEY, title TEXT, text TEXT, fetched_at TEXT)"
    )
    return con


def get(url: str):
    con = _conn()
    try:
        row = con.execute("SELECT text FROM source_cache WHERE url = ?", (url,)).fetchone()
        return row[0] if row else None
    finally:
        con.close()


def put(url: str, text: str, title: str = "") -> None:
    con = _conn()
    try:
        con.execute(
            "INSERT OR REPLACE INTO source_cache (url, title, text, fetched_at) VALUES (?, ?, ?, ?)",
            (url, title, text, datetime.datetime.now().isoformat(timespec="seconds")),
        )
        con.commit()
    finally:
        con.close()


def prune(days: int = 30) -> None:
    cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat(timespec="seconds")
    con = _conn()
    try:
        con.execute("DELETE FROM source_cache WHERE fetched_at < ?", (cutoff,))
        con.commit()
    finally:
        con.close()
