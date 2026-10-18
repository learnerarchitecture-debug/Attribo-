"""
Local archive checking: compare the document against a folder of previous
documents (self-plagiarism / internal department archive).

(c) 2026 Attribo. All rights reserved.
"""
from pathlib import Path

from ..core.parser import SUPPORTED_EXTENSIONS, parse_document

MAX_FILES = 40
MAX_CHARS = 150_000
MIN_CHARS = 100


class ArchiveChecker:
    def __init__(self, settings: dict):
        self.folder = str(settings.get("archive_folder", "") or "")
        self.enabled = bool(settings.get("enable_archive", False))

    def available(self) -> bool:
        return self.enabled and bool(self.folder) and Path(self.folder).is_dir()

    def sources(self, exclude_path: str = "") -> list:
        folder = Path(self.folder)
        try:
            exclude = Path(exclude_path).resolve() if exclude_path else None
        except OSError:
            exclude = None

        files = [
            p
            for p in sorted(folder.rglob("*"))
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
        ][:MAX_FILES]

        results = []
        for path in files:
            try:
                if exclude is not None and path.resolve() == exclude:
                    continue
                parsed = parse_document(str(path))
                text = (parsed.full_text or "").strip()
                if len(text) < MIN_CHARS:
                    continue
                results.append(
                    {
                        "title": path.name,
                        "url": path.as_uri(),
                        "text": text[:MAX_CHARS],
                        "kind": "archive",
                        "fetched": True,
                    }
                )
            except Exception:
                continue
        return results
