"""
JSON settings storage.

Location: %APPDATA%\\Attribo\\settings.json
(c) 2026 Attribo. All rights reserved.
"""
import json
import os
import shutil
from pathlib import Path

APP_DIR = Path(os.environ.get("APPDATA", str(Path.home()))) / "Attribo"
SETTINGS_FILE = APP_DIR / "settings.json"

_LEGACY_DIR = Path(os.environ.get("APPDATA", str(Path.home()))) / "Archinsights" / "PlagCheck"


def _migrate_legacy_data() -> None:
    """One-time move of pre-rename data (settings, history, model, license)."""
    try:
        if _LEGACY_DIR.exists() and not APP_DIR.exists():
            shutil.move(str(_LEGACY_DIR), str(APP_DIR))
        old_db = APP_DIR / "plagcheck.db"
        new_db = APP_DIR / "attribo.db"
        if old_db.exists() and not new_db.exists():
            old_db.rename(new_db)
            for suffix in ("-wal", "-shm"):
                side = APP_DIR / f"plagcheck.db{suffix}"
                if side.exists():
                    side.rename(APP_DIR / f"attribo.db{suffix}")
        try:
            _LEGACY_DIR.parent.rmdir()  # remove empty "Archinsights" shell
        except OSError:
            pass
    except OSError:
        pass


_migrate_legacy_data()

DEFAULTS = {
    "google_api_key": "",
    "google_cx": "",
    "brave_api_key": "",
    "serper_api_key": "",
    "tavily_api_key": "",
    "exa_api_key": "",
    "searxng_url": "",
    "cross_verify_providers": True,
    "min_match_words": 8,
    "max_queries": 12,
    "max_fetch_per_query": 4,
    "enable_web": True,
    "enable_academic": True,
    "enable_ai": True,
    "exclude_quotes": False,
    "enable_archive": False,
    "archive_folder": "",
    "enable_semantic": False,
    "semantic_threshold": 0.70,
    "duplicate_check": True,
    "citation_check": True,
    "watch_enabled": False,
    "watch_folder": "",
    "fetch_timeout": 12,
    "license_key": "",
}


def load_settings() -> dict:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    data = dict(DEFAULTS)
    if SETTINGS_FILE.exists():
        try:
            data.update(json.loads(SETTINGS_FILE.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            pass
    return data


def save_settings(data: dict) -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
