"""
Offline friend-license keys (HMAC-signed, verified locally).

Key format:  AI-<SLUG>-<YYYY-MM-DD>-<SIG10>
Example:     AI-ALICE-2027-12-31-1A2B3C4D5E

Generate keys with:  python tools/license_generator.py  (GUI + CLI)
                     python tools/genkey.py "Name" 2027-12-31  (scriptable one-liner)

(c) 2026 Attribo. All rights reserved.
"""
import datetime
import hashlib
import hmac
import re

_SECRET = b"Archinsights-PlagCheck-2026-friends-circle"


def _sign(payload: str) -> str:
    return hmac.new(_SECRET, payload.encode("utf-8"), hashlib.sha256).hexdigest()[:10].upper()


def make_key(name: str, expires: str = "2027-12-31") -> str:
    slug = re.sub(r"[^A-Za-z0-9]", "", name.upper())[:12] or "FRIEND"
    return f"AI-{slug}-{expires}-{_sign(f'{slug}|{expires}')}"


def verify_key(key: str):
    """Returns {'name', 'expires', 'expired'} for a valid key, otherwise None."""
    if not key:
        return None
    key = key.strip().upper()
    parts = key.split("-")
    if len(parts) != 6 or parts[0] != "AI":
        return None
    slug = parts[1]
    expires = "-".join(parts[2:5])
    signature = parts[5]
    if _sign(f"{slug}|{expires}") != signature:
        return None
    try:
        expiry = datetime.date.fromisoformat(expires)
    except ValueError:
        return None
    return {"name": slug, "expires": expires, "expired": expiry < datetime.date.today()}
