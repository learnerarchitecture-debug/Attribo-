"""
Stylometric AI-likelihood heuristic (stylometry-1.5).

This is a *signal*, not a verdict. See docs/ACCURACY_AND_LIMITS.md.

Sub-metrics: burstiness, formulaic density, lexical diversity, trigram
repetition, discourse-marker density, sentence-opener repetition.

(c) 2026 Attribo. All rights reserved.
"""
import re
import statistics

from .matching import TOKEN_RE

AI_LEXICON = [
    "delve into",
    "it is worth noting",
    "in the realm of",
    "furthermore",
    "moreover",
    "in conclusion",
    "plays a crucial role",
    "plays a vital role",
    "a testament to",
    "in today's world",
    "it is important to note",
    "navigating the",
    "landscape of",
    "underscores the",
    "pivotal",
    "holistic approach",
    "comprehensive understanding",
    "leverage",
    "seamless",
    "robust framework",
    "foster",
    "myriad of",
    "tapestry",
    "elevate",
    "unlock the potential",
    "empower",
    "cutting-edge",
    "state-of-the-art",
    "paradigm shift",
    "multifaceted",
    "intricate",
    "meticulous",
    "in essence",
    "additionally",
    "significant implications",
    "unprecedented",
    "diverse range",
    "wide array",
    "due to the fact that",
]

TRANSITIONS = [
    "firstly",
    "first and foremost",
    "secondly",
    "thirdly",
    "in addition",
    "additionally",
    "consequently",
    "as a result",
    "nevertheless",
    "on the other hand",
    "for instance",
    "for example",
    "in other words",
    "in summary",
    "ultimately",
    "notably",
    "specifically",
    "overall",
    "to sum up",
    "it should be noted",
]

VERSION = "stylometry-1.5"


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def analyze_ai(text: str) -> dict:
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", text or "") if s.strip()]
    lengths = [len(TOKEN_RE.findall(s)) for s in sentences]
    lengths = [n for n in lengths if n > 0]
    tokens = [t.lower() for t in TOKEN_RE.findall(text or "")]

    details = {
        "version": VERSION,
        "sentences": len(sentences),
        "tokens": len(tokens),
        "burstiness": 0.0,
        "ttr": 0.0,
        "formulaic_per_1k": 0.0,
        "transitions_per_1k": 0.0,
        "opener_uniqueness": 0.0,
        "trigram_repetition": 0.0,
        "score": None,
        "note": "",
        "flagged": [],
    }

    if len(lengths) < 10 or len(tokens) < 120:
        details["note"] = "Text too short for a reliable signal."
        return details

    mean = sum(lengths) / len(lengths)
    stdev = statistics.pstdev(lengths)
    burst = stdev / mean if mean else 0.0
    details["burstiness"] = round(burst, 3)
    burst_score = _clamp(100.0 * (0.70 - burst) / (0.70 - 0.20))

    ttr = len(set(tokens)) / len(tokens)
    details["ttr"] = round(ttr, 3)
    ttr_score = _clamp(100.0 * (1.0 - abs(ttr - 0.42) / 0.30))

    low = (text or "").lower()
    hits = sum(low.count(phrase) for phrase in AI_LEXICON)
    per_1k = 1000.0 * hits / len(tokens)
    details["formulaic_per_1k"] = round(per_1k, 2)
    formulaic_score = _clamp(100.0 * per_1k / 3.0)

    transition_hits = sum(low.count(phrase) for phrase in TRANSITIONS)
    transitions_per_1k = 1000.0 * transition_hits / len(tokens)
    details["transitions_per_1k"] = round(transitions_per_1k, 2)
    transition_score = _clamp(100.0 * transitions_per_1k / 6.0)

    openers = []
    for sentence in sentences:
        words = TOKEN_RE.findall(sentence)
        if words:
            openers.append(words[0].lower())
    opener_uniqueness = len(set(openers)) / len(openers) if openers else 1.0
    details["opener_uniqueness"] = round(opener_uniqueness, 3)
    opener_score = _clamp(100.0 * (0.85 - opener_uniqueness) / 0.35)

    flagged = []
    for sentence in sentences:
        low_s = sentence.lower()
        hits_s = [p for p in AI_LEXICON if p in low_s]
        if hits_s:
            flagged.append((len(hits_s), sentence.strip()[:160]))
    flagged.sort(key=lambda x: -x[0])
    details["flagged"] = [f[1] for f in flagged[:5]]

    trigrams = list(zip(tokens, tokens[1:], tokens[2:]))
    tri_ratio = 0.0
    if trigrams:
        tri_ratio = 1.0 - (len(set(trigrams)) / len(trigrams))
    details["trigram_repetition"] = round(tri_ratio, 3)
    rep_score = _clamp(100.0 * (tri_ratio - 0.02) / 0.08)

    score = (
        0.35 * burst_score
        + 0.18 * formulaic_score
        + 0.15 * transition_score
        + 0.12 * opener_score
        + 0.10 * ttr_score
        + 0.10 * rep_score
    )
    details["score"] = round(_clamp(score), 1)
    return details
