"""
Web search providers + page fetching + text extraction.

Providers (all optional, all with card-free tiers):
  - Google Custom Search JSON API (100 queries/day free)
  - Brave Search API (free plan, ~2,000 queries/month)
  - Serper.dev (2,500 free credits, no card)
  - Tavily (1,000 free credits/month, no card)
  - Exa (free credits on signup, no card)
  - SearXNG (self-hosted meta-search, unlimited, no card/account)

Cross-verification: with "cross_verify_providers" enabled, every search
phrase is sent to ALL configured providers; results are merged and
deduplicated by URL — and every hit is then fetched and matched against the
*actual page text*, so a match only counts when the source page itself
confirms it (provider-independent evidence).

(c) 2026 Attribo. All rights reserved.
"""
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup

from . import cache

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Attribo/0.10"
MAX_PAGE_BYTES = 400_000
MAX_TEXT_CHARS = 200_000


@dataclass
class SearchHit:
    title: str = ""
    url: str = ""
    snippet: str = ""


def _norm_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    try:
        parts = urlsplit(url)
        path = parts.path.rstrip("/")
        return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, parts.query, ""))
    except ValueError:
        return url


def dedupe_hits(hits: list) -> list:
    """Keep the first hit per normalized URL (no empty URLs)."""
    seen = set()
    unique = []
    for hit in hits:
        key = _norm_url(hit.url)
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(hit)
    return unique


class WebChecker:
    def __init__(self, settings: dict):
        self.google_key = str(settings.get("google_api_key", "")).strip()
        self.google_cx = str(settings.get("google_cx", "")).strip()
        self.brave_key = str(settings.get("brave_api_key", "")).strip()
        self.serper_key = str(settings.get("serper_api_key", "")).strip()
        self.tavily_key = str(settings.get("tavily_api_key", "")).strip()
        self.exa_key = str(settings.get("exa_api_key", "")).strip()
        self.searxng_url = str(settings.get("searxng_url", "")).strip()
        self.cross_verify = bool(settings.get("cross_verify_providers", True))
        self.timeout = int(settings.get("fetch_timeout", 12))

    # -- provider inventory --------------------------------------------------
    def configured_providers(self) -> list:
        names = []
        if self.google_key and self.google_cx:
            names.append("google")
        if self.brave_key:
            names.append("brave")
        if self.serper_key:
            names.append("serper")
        if self.tavily_key:
            names.append("tavily")
        if self.exa_key:
            names.append("exa")
        if self.searxng_url:
            names.append("searxng")
        return names

    def available(self) -> bool:
        return bool(self.configured_providers())

    def _provider_calls(self) -> dict:
        return {
            "google": self._search_google,
            "brave": self._search_brave,
            "serper": self._search_serper,
            "tavily": self._search_tavily,
            "exa": self._search_exa,
            "searxng": self._search_searxng,
        }

    def _provider_search(self, name: str, phrase: str) -> list:
        """Quoted phrase first (precise); fall back to unquoted (recall)."""
        call = self._provider_calls().get(name)
        if call is None:
            return []
        hits = call(phrase, True)
        if not hits:
            hits = call(phrase, False)
        return hits

    # -- search --------------------------------------------------------------
    def search(self, phrase: str) -> list:
        providers = self.configured_providers()
        if not providers:
            return []
        if self.cross_verify:
            hits = []
            for name in providers:
                hits.extend(self._provider_search(name, phrase))
            return dedupe_hits(hits)
        # Legacy mode: first provider that returns results wins.
        for name in providers:
            hits = self._provider_search(name, phrase)
            if hits:
                return hits
        return []

    def probe(self, phrase: str = "climate change research impacts", progress=None) -> list:
        """Test every configured provider with one live query.

        Returns [{"provider", "ok", "message"}] for the Settings test button.
        """
        names = self.configured_providers()
        results = []
        for index, name in enumerate(names):
            if progress:
                progress(int(100 * index / max(len(names), 1)), f"Testing {name}...")
            call = self._provider_calls().get(name)
            if call is None:
                continue
            try:
                hits = call(phrase, False)
            except Exception as exc:  # noqa: BLE001
                results.append({"provider": name, "ok": False, "message": str(exc)})
                continue
            if hits:
                results.append(
                    {"provider": name, "ok": True, "message": f"{len(hits)} result(s)"}
                )
            else:
                results.append(
                    {
                        "provider": name,
                        "ok": False,
                        "message": "no results - check the key/URL (quota may be used up)",
                    }
                )
        if progress:
            progress(100, "Done")
        return results

    # -- individual providers -------------------------------------------------
    def _search_google(self, phrase: str, quoted: bool = True) -> list:
        query = f'"{phrase}"' if quoted else phrase
        try:
            response = requests.get(
                "https://www.googleapis.com/customsearch/v1",
                params={
                    "key": self.google_key,
                    "cx": self.google_cx,
                    "q": query,
                    "num": 5,
                },
                timeout=self.timeout,
            )
            if response.status_code == 200:
                items = response.json().get("items", []) or []
                return [
                    SearchHit(
                        title=item.get("title", ""),
                        url=item.get("link", ""),
                        snippet=item.get("snippet", ""),
                    )
                    for item in items
                ]
        except Exception:
            pass
        return []

    def _search_brave(self, phrase: str, quoted: bool = True) -> list:
        query = f'"{phrase}"' if quoted else phrase
        try:
            response = requests.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": query, "count": 5},
                headers={
                    "X-Subscription-Token": self.brave_key,
                    "Accept": "application/json",
                },
                timeout=self.timeout,
            )
            if response.status_code == 200:
                results = (response.json().get("web", {}) or {}).get("results", []) or []
                return [
                    SearchHit(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        snippet=item.get("description", ""),
                    )
                    for item in results
                ]
        except Exception:
            pass
        return []

    def _search_serper(self, phrase: str, quoted: bool = True) -> list:
        query = f'"{phrase}"' if quoted else phrase
        try:
            response = requests.post(
                "https://google.serper.dev/search",
                json={"q": query, "num": 5},
                headers={
                    "X-API-KEY": self.serper_key,
                    "Content-Type": "application/json",
                },
                timeout=self.timeout,
            )
            if response.status_code == 200:
                items = response.json().get("organic", []) or []
                return [
                    SearchHit(
                        title=item.get("title", ""),
                        url=item.get("link", ""),
                        snippet=item.get("snippet", ""),
                    )
                    for item in items
                ]
        except Exception:
            pass
        return []

    def _search_tavily(self, phrase: str, quoted: bool = True) -> list:
        query = f'"{phrase}"' if quoted else phrase
        try:
            response = requests.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": self.tavily_key,
                    "query": query,
                    "max_results": 5,
                    "search_depth": "basic",
                },
                timeout=self.timeout,
            )
            if response.status_code == 200:
                items = response.json().get("results", []) or []
                return [
                    SearchHit(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        snippet=str(item.get("content", ""))[:300],
                    )
                    for item in items
                ]
        except Exception:
            pass
        return []

    def _search_exa(self, phrase: str, quoted: bool = True) -> list:
        query = f'"{phrase}"' if quoted else phrase
        try:
            response = requests.post(
                "https://api.exa.ai/search",
                json={
                    "query": query,
                    "numResults": 5,
                    "type": "auto",
                    "contents": {"text": {"maxCharacters": 300}},
                },
                headers={"x-api-key": self.exa_key, "Content-Type": "application/json"},
                timeout=self.timeout,
            )
            if response.status_code == 200:
                items = response.json().get("results", []) or []
                return [
                    SearchHit(
                        title=item.get("title", "") or "",
                        url=item.get("url", ""),
                        snippet=str(item.get("text", "") or "")[:300],
                    )
                    for item in items
                ]
        except Exception:
            pass
        return []

    def _search_searxng(self, phrase: str, quoted: bool = True) -> list:
        query = f'"{phrase}"' if quoted else phrase
        base = self.searxng_url.rstrip("/")
        if not base.lower().startswith(("http://", "https://")):
            base = "http://" + base
        try:
            response = requests.get(
                f"{base}/search",
                params={"q": query, "format": "json"},
                headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
                timeout=self.timeout,
            )
            if response.status_code == 200:
                items = response.json().get("results", []) or []
                return [
                    SearchHit(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        snippet=str(item.get("content", ""))[:300],
                    )
                    for item in items[:5]
                ]
        except Exception:
            pass
        return []

    # -- fetch -------------------------------------------------------------
    def fetch_text(self, url: str):
        if not url.lower().startswith(("http://", "https://")):
            return None
        cached = cache.get(url)
        if cached:
            return cached
        try:
            response = requests.get(
                url,
                headers={"User-Agent": USER_AGENT},
                timeout=self.timeout,
                stream=True,
            )
            content_type = response.headers.get("Content-Type", "")
            if not any(kind in content_type for kind in ("text", "html", "xml")):
                return None
            raw = response.raw.read(MAX_PAGE_BYTES, decode_content=True)
            html = raw.decode(response.encoding or "utf-8", errors="ignore")
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "form"]):
                tag.decompose()
            text = soup.get_text(" ", strip=True)
            if len(text) < 200:
                return None
            text = text[:MAX_TEXT_CHARS]
            cache.put(url, text)
            return text
        except Exception:
            return None
