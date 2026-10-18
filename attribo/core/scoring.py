"""
Score computation (deduplicated).

Spans are counted once for the overall similarity, using the highest-priority
class that covers them: verbatim (1.00) > near-match (0.85) > paraphrase (0.60).
Per-source percentages remain raw indicator sums.

See docs/SCORING.md for the full methodology.

(c) 2026 Attribo. All rights reserved.
"""
from dataclasses import dataclass


@dataclass
class MatchItem:
    match_type: str = ""      # "verbatim" | "near" | "semantic" | "paraphrase" | "duplicate"
    tokens: int = 0
    weight: float = 1.0
    text: str = ""
    source_title: str = ""
    source_url: str = ""
    suggestion: str = ""
    span_start: int = -1      # character offsets in the ORIGINAL document text
    span_end: int = -1
    source_snippet: str = ""  # surrounding source context (evidence view)


@dataclass
class SourceInfo:
    title: str = ""
    url: str = ""
    kind: str = "web"         # "web" | "academic" | "archive"
    fetched: bool = False
    matched_tokens: int = 0
    pct: float = 0.0


def compute_scores(content_tokens: int, weighted_tokens: float, paraphrase_tokens: int, ai_score) -> dict:
    total = max(int(content_tokens), 1)
    similarity = min(100.0, 100.0 * weighted_tokens / total)
    paraphrase = min(100.0, 100.0 * paraphrase_tokens / total)

    ai = float(ai_score) if ai_score is not None else 0.0
    integrity = max(0.0, 100.0 - (0.50 * similarity + 0.30 * ai + 0.20 * paraphrase))

    return {
        "similarity": round(similarity, 1),
        "originality": round(100.0 - similarity, 1),
        "paraphrase": round(paraphrase, 1),
        "ai": round(ai, 1),
        "integrity": round(integrity, 1),
    }
