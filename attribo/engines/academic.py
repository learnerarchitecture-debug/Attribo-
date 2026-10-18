"""
Academic connectors: OpenAlex + Crossref (both free, no API key required).

(c) 2026 Attribo. All rights reserved.
"""
import time
from dataclasses import dataclass

import requests


@dataclass
class AcademicHit:
    title: str = ""
    url: str = ""
    text: str = ""
    doi: str = ""


class AcademicChecker:
    def __init__(self, settings: dict):
        self.timeout = int(settings.get("fetch_timeout", 12))

    @staticmethod
    def available() -> bool:
        return True

    def search(self, phrase: str) -> list:
        hits = self._search_openalex(phrase)
        if len(hits) < 2:
            hits.extend(self._search_crossref(phrase))
        # deduplicate by title
        seen = set()
        unique = []
        for hit in hits:
            key = hit.title.lower()[:80]
            if key and key not in seen:
                seen.add(key)
                unique.append(hit)
        return unique[:5]

    def _search_openalex(self, phrase: str) -> list:
        hits = []
        try:
            response = requests.get(
                "https://api.openalex.org/works",
                params={
                    "search": phrase,
                    "per-page": 3,
                    "mailto": "attribo@attribo.local",
                },
                timeout=self.timeout,
            )
            if response.status_code == 200:
                for work in response.json().get("results", []) or []:
                    title = (work.get("display_name") or "").strip()
                    if not title:
                        continue
                    doi = work.get("doi") or ""
                    url = doi or work.get("id") or ""
                    abstract = self._reconstruct_abstract(work.get("abstract_inverted_index"))
                    text = (title + ". " + (abstract or "")).strip()
                    hits.append(AcademicHit(title=title[:200], url=url, text=text, doi=doi))
        except Exception:
            pass
        time.sleep(0.15)
        return hits

    def _search_crossref(self, phrase: str) -> list:
        hits = []
        try:
            response = requests.get(
                "https://api.crossref.org/works",
                params={"query.bibliographic": phrase, "rows": 3},
                headers={"User-Agent": "Attribo/0.9 (mailto:attribo@attribo.local)"},
                timeout=self.timeout,
            )
            if response.status_code == 200:
                items = (response.json().get("message", {}) or {}).get("items", []) or []
                for item in items:
                    titles = item.get("title") or []
                    title = (titles[0] if titles else "").strip()
                    if not title:
                        continue
                    url = item.get("URL", "")
                    hits.append(AcademicHit(title=title[:200], url=url, text=title))
        except Exception:
            pass
        time.sleep(0.15)
        return hits

    @staticmethod
    def _reconstruct_abstract(inverted_index) -> str:
        if not inverted_index:
            return ""
        positions = {}
        for word, indexes in inverted_index.items():
            for index in indexes:
                positions[index] = word
        return " ".join(positions[k] for k in sorted(positions))
