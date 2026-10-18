"""
Reference list validation: parse bibliography entries and check them against
Crossref / OpenAlex — existence, DOI correctness, retraction status.

Network calls happen only when the user explicitly runs "Validate references".

(c) 2026 Attribo. All rights reserved.
"""
import re
import time

import requests

from .matching import tokenize_spans

DOI_RE = re.compile(r"10\.\d{4,9}/[^\s,;\"'<>()\[\]]+", re.IGNORECASE)
YEAR_PAREN_RE = re.compile(r"\((?:19|20)\d{2}[a-z]?\)")

USER_AGENT = "Attribo/0.10 (mailto:attribo@attribo.local)"


def split_entries(ref_paras: list) -> list:
    """Join wrapped lines and split a bibliography into entries."""
    lines = []
    for para in ref_paras:
        for line in (para or "").splitlines():
            line = line.strip()
            if line:
                lines.append(line)
    entries = []
    for line in lines:
        starts_new = bool(re.match(r"^(\[\d+\]|\d{1,3}[.)])\s+", line)) or bool(
            re.match(r"^[A-Z][A-Za-z'\-]+,\s*(?:[A-Z]\.|[A-Z][a-z])", line)
        )
        if starts_new or not entries:
            entries.append(line)
        else:
            entries[-1] = entries[-1] + " " + line
    return [e for e in entries if len(e) >= 25]


def _tokens(text: str) -> set:
    return {t[0] for t in tokenize_spans(text or "") if len(t[0]) > 2}


def _overlap(guessed_title: str, returned_title: str) -> float:
    guess = _tokens(guessed_title)
    if not guess:
        return 0.0
    returned = _tokens(returned_title)
    return len(guess & returned) / len(guess)


def _guess_title(entry: str) -> str:
    match = YEAR_PAREN_RE.search(entry)
    if match:
        tail = entry[match.end() :].lstrip(" .,")
        chunk = re.split(r"\.\s|\.$", tail, maxsplit=1)[0]
        if chunk:
            return chunk[:180]
    # fallback: longest digit-free word run
    best = ""
    for run in re.findall(r"[A-Za-z][A-Za-z'\- ]{12,120}", entry):
        run = run.strip()
        if len(run) > len(best):
            best = run
    return best[:180]


def _crossref_by_doi(doi: str, timeout: int):
    try:
        response = requests.get(
            f"https://api.crossref.org/works/{doi}",
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
        )
        if response.status_code == 200:
            message = response.json().get("message", {}) or {}
            titles = message.get("title") or []
            return (titles[0] if titles else "").strip()
    except Exception:  # noqa: BLE001
        pass
    return None


def _crossref_search(phrase: str, timeout: int):
    try:
        response = requests.get(
            "https://api.crossref.org/works",
            params={"query.bibliographic": phrase, "rows": 3},
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
        )
        if response.status_code == 200:
            items = (response.json().get("message", {}) or {}).get("items", []) or []
            for item in items:
                titles = item.get("title") or []
                title = (titles[0] if titles else "").strip()
                if title:
                    return title, item.get("URL", "")
    except Exception:  # noqa: BLE001
        pass
    return None, ""


def _is_retracted(doi: str, timeout: int) -> bool:
    try:
        response = requests.get(
            f"https://api.openalex.org/works/doi:{doi}",
            params={"mailto": "attribo@attribo.local"},
            timeout=timeout,
        )
        if response.status_code == 200:
            return bool(response.json().get("is_retracted"))
    except Exception:  # noqa: BLE001
        pass
    return False


def check_entry(entry: str, timeout: int = 12) -> dict:
    """Returns {entry, status, note, matched, url, doi}."""
    doi_match = DOI_RE.search(entry)
    doi = doi_match.group(0).rstrip(".").rstrip(")") if doi_match else ""
    title_guess = _guess_title(entry)
    result = {
        "entry": entry[:300],
        "status": "not_found",
        "note": "",
        "matched": "",
        "url": "",
        "doi": doi,
    }

    if doi:
        matched_title = _crossref_by_doi(doi, timeout)
        result["url"] = f"https://doi.org/{doi}"
        if matched_title is None:
            result["status"] = "doi_not_found"
            result["note"] = "DOI does not resolve in Crossref - possible fake reference."
            return result
        result["matched"] = matched_title[:200]
        similarity = _overlap(title_guess, matched_title) if title_guess else 1.0
        if _is_retracted(doi, timeout):
            result["status"] = "retracted"
            result["note"] = "This work is flagged as RETRACTED (OpenAlex)."
        elif title_guess and similarity < 0.30:
            result["status"] = "doi_mismatch"
            result["note"] = "DOI resolves to a different work than the entry text."
        else:
            result["status"] = "verified"
            result["note"] = "DOI resolves and matches the entry."
        return result

    if not title_guess:
        result["status"] = "skipped"
        result["note"] = "Could not extract a title to search."
        return result

    matched_title, url = _crossref_search(title_guess, timeout)
    if not matched_title:
        result["note"] = "No Crossref match (service unreachable or no results)."
        return result
    similarity = _overlap(title_guess, matched_title)
    result["matched"] = matched_title[:200]
    result["url"] = url
    if similarity >= 0.6:
        result["status"] = "verified_no_doi"
        result["note"] = "Found in Crossref (entry has no DOI)."
    elif similarity >= 0.4:
        result["status"] = "possible_match"
        result["note"] = "Partial title match - verify manually."
    else:
        result["status"] = "not_found"
        result["note"] = "No close title match in Crossref - verify this reference."
    return result


def validate_entries(entries: list, timeout: int = 12, progress=None, cancel=None, max_entries: int = 25):
    entries = entries[:max_entries]
    results = []
    for index, entry in enumerate(entries):
        if cancel and cancel():
            break
        if progress:
            progress(index, len(entries), entry[:80])
        results.append(check_entry(entry, timeout=timeout))
        time.sleep(0.2)
    if progress:
        progress(len(entries), len(entries), "done")
    return results


STATUS_LABELS = {
    "verified": "Verified (DOI)",
    "verified_no_doi": "Verified (no DOI in entry)",
    "possible_match": "Possible match",
    "not_found": "Not found",
    "doi_not_found": "DOI not found (suspicious)",
    "doi_mismatch": "DOI mismatch (suspicious)",
    "retracted": "RETRACTED",
    "skipped": "Skipped",
}
