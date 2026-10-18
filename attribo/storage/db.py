"""
SQLite scan history.

Location: %APPDATA%\\Attribo\\attribo.db
(c) 2026 Attribo. All rights reserved.
"""
import sqlite3

from .settings import APP_DIR

DB_FILE = APP_DIR / "attribo.db"


def _conn() -> sqlite3.Connection:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(DB_FILE))
    con.execute("PRAGMA journal_mode=WAL")
    return con


def init_db() -> None:
    con = _conn()
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT,
            doc_name TEXT,
            doc_hash TEXT,
            report_id TEXT,
            words INTEGER,
            similarity REAL,
            originality REAL,
            paraphrase REAL,
            ai REAL,
            integrity REAL,
            n_matches INTEGER,
            n_sources INTEGER,
            licensed INTEGER
        );
        """
    )
    con.commit()
    con.close()


def save_scan(result) -> None:
    """result: core.pipeline.ScanResult (duck-typed)."""
    con = _conn()
    con.execute(
        """INSERT INTO scans
           (ts, doc_name, doc_hash, report_id, words, similarity, originality,
            paraphrase, ai, integrity, n_matches, n_sources, licensed)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            result.timestamp,
            result.file_name,
            result.doc_hash,
            result.report_id,
            int(result.words),
            float(result.similarity),
            float(result.originality),
            float(result.paraphrase_risk),
            float(result.ai_likelihood),
            float(result.integrity),
            len(result.matches),
            len(result.sources),
            1 if result.licensed else 0,
        ),
    )
    con.commit()
    con.close()


def recent_scans(limit: int = 50):
    con = _conn()
    rows = con.execute(
        """SELECT ts, doc_name, report_id, similarity, integrity, n_matches
           FROM scans ORDER BY id DESC LIMIT ?""",
        (int(limit),),
    ).fetchall()
    con.close()
    return rows
