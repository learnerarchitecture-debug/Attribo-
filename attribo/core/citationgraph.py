"""
Citation integrity toolkit.

Offline:
  - two-way citation graph: cited-but-missing / uncited / duplicate references
  - quoted-material audit: quotations without attribution, block-quote needs

Network (on demand, best-effort):
  - citation support check: fetch the cited work's abstract (OpenAlex by DOI)
    and compare it with the in-text sentence - embeddings when the local
    semantic model is installed, stem overlap otherwise

Heuristic signals, not verdicts - always review the flagged pairs.

(c) 2026 Ayush Gupta (Attribo). All rights reserved.
"""
import difflib
import re

from .citation import CITATION_RE
from .matching import content_stems, tokenize_spans
from .segmenter import split_sentences_with_spans

AUTHOR_YEAR_RE = re.compile(
    r"([A-Z][A-Za-z'\-]{1,30})(?:\s+et\s+al\.?)?\s*,?\s*\(?(\d{4}[a-z]?)\)?"
)
NUMERIC_RE = re.compile(r"\[(\d{1,3}(?:\s*[,\u2013\u2014-]\s*\d{1,3})*)\]")
QUOTE_RE = re.compile(r"[\u201c\"]([^\u201d\"]{12,600})[\u201d\"]")
ATTRIBUTION_RE = re.compile(
    r"according to|as (?:noted|stated|argued|observed|reported|written|described)|"
    r"(?:wrote|stated|noted|argued|observed|reported|concluded|explained|quoted)\b|"
    r"cited in|quoted in|in the words of",
    re.IGNORECASE,
)
SKIP_WORDS = {
    "figure", "table", "section", "chapter", "equation", "appendix", "page",
    "vol", "no", "e.g", "i.e", "the", "this", "these",
}


def _cited_keys(text: str):
    authors, years, numeric = set(), set(), set()
    for match in AUTHOR_YEAR_RE.finditer(text or ""):
        word = match.group(1)
        if word.lower() in SKIP_WORDS:
            continue
        authors.add(word.lower())
        years.add(match.group(2))
    for match in NUMERIC_RE.finditer(text or ""):
        for part in re.split(r"\s*[,\u2013\u2014-]\s*", match.group(1)):
            if part.strip().isdigit():
                numeric.add(int(part))
    return authors, years, numeric


def build_citation_graph(text: str, entries: list) -> dict:
    """Two-way check between in-text citations and the bibliography."""
    text = text or ""
    text_low = text.lower()
    norm_entries = [
        re.sub(r"\s+", " ", str(entry)).strip()
        for entry in (entries or [])
        if str(entry).strip()
    ]
    authors, years, numeric = _cited_keys(text)

    missing = []
    for author in sorted(authors):
        if not any(author in entry.lower() for entry in norm_entries):
            missing.append(author.title())

    uncited = []
    for entry in norm_entries:
        words = re.findall(r"[A-Za-z'\-]{3,}", entry)
        surname = words[0].lower() if words else ""
        entry_years = re.findall(r"\b(?:19|20)\d{2}\b", entry)
        mentioned = (surname and surname in text_low) or any(
            year in text for year in entry_years
        )
        if not mentioned:
            uncited.append(entry[:220])

    duplicates = []
    seen_pairs = set()
    for i in range(len(norm_entries)):
        for j in range(i + 1, len(norm_entries)):
            ratio = difflib.SequenceMatcher(
                None, norm_entries[i].lower(), norm_entries[j].lower()
            ).ratio()
            if ratio >= 0.90 and (i, j) not in seen_pairs:
                seen_pairs.add((i, j))
                duplicates.append(norm_entries[j][:220])

    numeric_note = ""
    if numeric and norm_entries:
        top = max(numeric)
        if top > len(norm_entries):
            numeric_note = (
                f"Numeric markers go up to [{top}] but only {len(norm_entries)} "
                f"reference(s) were parsed."
            )

    return {
        "missing": missing[:20],
        "uncited": uncited[:20],
        "duplicates": duplicates[:20],
        "numeric_note": numeric_note,
        "entries": len(norm_entries),
    }


def audit_quotes(full_text: str, min_words: int = 6, block_words: int = 40) -> list:
    """Quotations and whether attribution sits close by."""
    issues = []
    for match in QUOTE_RE.finditer(full_text or ""):
        quote = re.sub(r"\s+", " ", match.group(1)).strip()
        words = len(quote.split())
        if words < min_words:
            continue
        start, end = match.start(1), match.end(1)
        window = (full_text or "")[max(0, start - 220): min(len(full_text), end + 220)]
        has_cite = bool(CITATION_RE.search(window)) or bool(ATTRIBUTION_RE.search(window))
        issues.append(
            {
                "quote": quote[:300],
                "words": words,
                "attributed": has_cite,
                "needs_block": words > block_words,
            }
        )
    issues.sort(key=lambda item: (item["attributed"], -item["words"]))
    return issues[:40]


def _reconstruct_abstract(inverted_index) -> str:
    if not inverted_index:
        return ""
    positions = {}
    for word, indexes in inverted_index.items():
        for index in indexes:
            positions[index] = word
    return " ".join(positions[key] for key in sorted(positions))


def _similarity(sentence: str, abstract: str):
    """Returns (score, method). Embeddings when the local model exists."""
    try:
        from . import semantic

        ok, _message = semantic.model_available()
        if ok and len(sentence.split()) >= 6 and len(abstract.split()) >= 30:
            import numpy as np

            vec_a = semantic.embed([sentence])[0]
            vec_b = semantic.embed([abstract[:1200]])[0]
            denominator = float(np.linalg.norm(vec_a) * np.linalg.norm(vec_b)) + 1e-9
            return float(vec_a @ vec_b / denominator), "embeddings"
    except Exception:  # noqa: BLE001
        pass
    stems_a = content_stems([t[0] for t in tokenize_spans(sentence)])
    stems_b = content_stems([t[0] for t in tokenize_spans(abstract)])
    return len(stems_a & stems_b) / max(len(stems_a), 1), "stems"


def citation_support(entries: list, text: str, settings: dict) -> list:
    """Check whether each cited work plausibly supports the citing sentence."""
    import requests

    timeout = int(settings.get("fetch_timeout", 12) or 12)
    mailto = "attribo@attribo.local"

    sentences = []
    for para in (text or "").split("\n\n"):
        for _start, _end, sent in split_sentences_with_spans(para):
            sentences.append(sent)

    results = []
    for entry in (entries or [])[:20]:
        entry = re.sub(r"\s+", " ", str(entry)).strip()
        if not entry:
            continue
        words = re.findall(r"[A-Za-z'\-]{3,}", entry)
        surname = words[0] if words else ""
        doi_match = re.search(r"10\.\d{4,9}/[^\s,;]+", entry)
        doi = doi_match.group(0).rstrip(".") if doi_match else ""
        if not doi:
            results.append(
                {
                    "entry": entry[:160],
                    "verdict": "skipped",
                    "detail": "No DOI in the reference - add one to enable the abstract check.",
                }
            )
            continue

        abstract = ""
        try:
            response = requests.get(
                f"https://api.openalex.org/works/doi:{doi}",
                params={"mailto": mailto},
                timeout=timeout,
            )
            if response.status_code == 200:
                abstract = _reconstruct_abstract(
                    response.json().get("abstract_inverted_index")
                )
        except Exception:  # noqa: BLE001
            abstract = ""
        if not abstract:
            results.append(
                {
                    "entry": entry[:160],
                    "verdict": "unavailable",
                    "detail": "No abstract found (offline, or the work is not indexed with one).",
                }
            )
            continue

        best_score, best_sentence, best_method = 0.0, "", "stems"
        for sentence in sentences:
            if surname and surname.lower() not in sentence.lower():
                continue
            score, method = _similarity(sentence, abstract)
            if score > best_score:
                best_score, best_sentence, best_method = score, sentence, method
        if not best_sentence:
            results.append(
                {
                    "entry": entry[:160],
                    "verdict": "no-cite",
                    "detail": f"No in-text sentence mentioning \u201c{surname}\u201d was found.",
                }
            )
            continue

        # thresholds differ between methods
        cutoff = 0.42 if best_method == "embeddings" else 0.20
        verdict = "supported" if best_score >= cutoff else "weak"
        results.append(
            {
                "entry": entry[:160],
                "verdict": verdict,
                "detail": (
                    f"Term overlap {best_score:.0%} with the abstract "
                    f"- \u201c{best_sentence[:140]}\u201d"
                    if verdict == "supported"
                    else f"Low overlap ({best_score:.0%}) between the citing sentence "
                    f"and the work abstract - verify the claim."
                ),
            }
        )
    return results
