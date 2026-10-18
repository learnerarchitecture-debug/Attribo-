"""
Corpus Vault: an opt-in local index of your own scanned documents.

- with vault enabled, every successful scan is stored (name, hash, text)
- later scans are compared against the stored documents as extra sources
  (offline, no network) - instant self-plagiarism / reuse detection
- stored in the same SQLite file as scan history (%APPDATA%\\Attribo\\attribo.db)

Privacy: nothing leaves the machine; you can view, remove and wipe every
stored document from Settings -> Privacy.

(c) 2026 Ayush Gupta (Attribo). All rights reserved.
"""
MAX_SOURCES = 10        # newest N vault documents compared per scan
MAX_STORED_CHARS = 400_000
MAX_COMPARE_CHARS = 200_000


def _conn():
    from ..storage import db

    return db._conn()


def enabled(settings: dict) -> bool:
    return bool(settings.get("vault_enabled", False))


def index_result(result) -> int:
    """Store/refresh this scan in the vault. Returns 1 when stored, else 0."""
    text = (result.full_text or "")[:MAX_STORED_CHARS].strip()
    if not text or not result.doc_hash:
        return 0
    con = _conn()
    try:
        con.execute("DELETE FROM vault WHERE doc_hash = ?", (result.doc_hash,))
        con.execute(
            "INSERT INTO vault (ts, doc_name, doc_hash, char_count, text) "
            "VALUES (?, ?, ?, ?, ?)",
            (result.timestamp, result.file_name, result.doc_hash, len(text), text),
        )
        con.commit()
    finally:
        con.close()
    return 1


def vault_sources(exclude_hash: str = "") -> list:
    """Source dicts usable by the scan pipeline (kind='vault')."""
    con = _conn()
    try:
        rows = con.execute(
            "SELECT doc_name, doc_hash, text FROM vault ORDER BY id DESC LIMIT 200"
        ).fetchall()
    finally:
        con.close()

    out = []
    seen = set()
    for name, doc_hash, text in rows:
        if not text:
            continue
        if exclude_hash and doc_hash == exclude_hash:
            continue
        if doc_hash in seen:
            continue
        seen.add(doc_hash)
        out.append(
            {
                "title": f"Vault: {name}",
                "url": f"vault://{str(doc_hash)[:16]}",
                "text": text[:MAX_COMPARE_CHARS],
                "kind": "vault",
            }
        )
        if len(out) >= MAX_SOURCES:
            break
    return out


def list_docs() -> list:
    con = _conn()
    try:
        rows = con.execute(
            "SELECT id, ts, doc_name, char_count, doc_hash FROM vault ORDER BY id DESC"
        ).fetchall()
    finally:
        con.close()
    return [
        {"id": r[0], "ts": r[1], "name": r[2], "chars": r[3], "hash": r[4]}
        for r in rows
    ]


def remove_doc(doc_id: int) -> None:
    con = _conn()
    try:
        con.execute("DELETE FROM vault WHERE id = ?", (int(doc_id),))
        con.commit()
    finally:
        con.close()


def clear() -> int:
    con = _conn()
    try:
        count = con.execute("SELECT COUNT(*) FROM vault").fetchone()[0]
        con.execute("DELETE FROM vault")
        con.commit()
    finally:
        con.close()
    return int(count or 0)
