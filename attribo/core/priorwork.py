"""
Prior-work positioning: the closest existing works to your abstract.

Uses OpenAlex (free, no key) and Crossref on the most distinctive sentences
of the extracted abstract. Network only; nothing else leaves the machine.

(c) 2026 Ayush Gupta (Attribo). All rights reserved.
"""
import re
import time

import requests

from .matching import STOPWORDS, tokenize_spans

MAILTO = "attribo@attribo.local"


def extract_abstract(text: str) -> str:
    text = text or ""
    if not text.strip():
        return ""
    labelled = re.search(
        r"(?im)^\s*(?:abstract|summary)\b[:.\s-]*"
        r"(.{200,4000}?)"
        r"(?:\n\s*\n|\n\s*(?:keywords?|introduction|1[\.\s])\b)",
        text,
    )
    if labelled:
        return labelled.group(1).strip()
    for para in re.split(r"\n\s*\n", text):
        para = para.strip()
        if len(para) >= 400:
            return para[:2500]
    return text.strip()[:1200]


def _distinctive(abstract: str, count: int = 3) -> list:
    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", abstract)
        if len(sentence.strip()) > 60
    ]

    def rarity(sentence: str) -> float:
        words = [t[0] for t in tokenize_spans(sentence) if t[0] not in STOPWORDS]
        return sum(1 for word in words if len(word) >= 6) + 0.01 * len(words)

    sentences.sort(key=rarity, reverse=True)
    phrases = []
    for sentence in sentences[:count]:
        words = [t[0] for t in tokenize_spans(sentence) if t[0] not in STOPWORDS]
        if len(words) < 5:
            continue
        phrases.append(" ".join(words)[:220])
    return phrases


def find_prior_works(text: str, settings: dict, limit: int = 8) -> list:
    abstract = extract_abstract(text)
    phrases = _distinctive(abstract)
    if not phrases:
        return []
    timeout = int(settings.get("fetch_timeout", 12) or 12)

    works, seen = [], set()

    def absorb(items):
        for item in items:
            key = (item.get("title") or "").lower()[:80]
            if key and key not in seen:
                seen.add(key)
                works.append(item)

    for phrase in phrases:
        absorb(_openalex(phrase, timeout))
        time.sleep(0.12)
    if len(works) < 4:
        for phrase in phrases[:2]:
            absorb(_crossref(phrase, timeout))
            time.sleep(0.12)
    works.sort(key=lambda work: (-(work.get("year") or 0), -(work.get("citations") or 0)))
    return works[: int(limit)]


def _openalex(phrase: str, timeout: int) -> list:
    out = []
    try:
        response = requests.get(
            "https://api.openalex.org/works",
            params={"search": phrase, "per-page": 6, "mailto": MAILTO},
            timeout=timeout,
        )
        if response.status_code == 200:
            for work in response.json().get("results", []) or []:
                title = (work.get("display_name") or "").strip()
                if not title:
                    continue
                out.append(
                    {
                        "title": title[:200],
                        "url": work.get("doi") or work.get("id") or "",
                        "year": work.get("publication_year") or 0,
                        "citations": work.get("cited_by_count") or 0,
                        "source": "OpenAlex",
                    }
                )
    except Exception:  # noqa: BLE001
        pass
    return out


def _crossref(phrase: str, timeout: int) -> list:
    out = []
    try:
        response = requests.get(
            "https://api.crossref.org/works",
            params={"query.bibliographic": phrase, "rows": 4},
            headers={"User-Agent": f"Attribo (mailto:{MAILTO})"},
            timeout=timeout,
        )
        if response.status_code == 200:
            for item in (response.json().get("message", {}) or {}).get("items", []) or []:
                titles = item.get("title") or []
                title = (titles[0] if titles else "").strip()
                if not title:
                    continue
                year = 0
                parts = (item.get("issued") or {}).get("date-parts") or [[]]
                if parts and parts[0]:
                    year = parts[0][0] or 0
                out.append(
                    {
                        "title": title[:200],
                        "url": item.get("URL", ""),
                        "year": year,
                        "citations": item.get("is-referenced-by-count") or 0,
                        "source": "Crossref",
                    }
                )
    except Exception:  # noqa: BLE001
        pass
    return out
