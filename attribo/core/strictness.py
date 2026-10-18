"""
Scan strictness profiles.

One dial ("strictness" in Settings) scales the detection parameters together:

  balanced  - the v0.11 defaults: fewer flags, fewer false positives
  strict    - default in v2.0: shorter minimum matches, more queries,
              lower semantic threshold, higher paraphrase sensitivity
  maximum   - everything on: flags even short overlaps; expect more
              false positives - always review before acting on a flag

Custom values from Settings keep working: strictness scales them rather
than replacing them.

(c) 2026 Ayush Gupta (Attribo). All rights reserved.
"""
LEVELS = ("balanced", "strict", "maximum")
LEVEL_LABELS = {
    "balanced": "Balanced - fewer flags, fewer false positives",
    "strict": "Strict (recommended) - catches shorter and looser overlaps",
    "maximum": "Maximum - flags even small overlaps; expect false positives",
}


def profile(settings: dict) -> dict:
    level = str(settings.get("strictness", "strict")).lower()
    if level not in LEVELS:
        level = "strict"

    base_min = max(5, int(settings.get("min_match_words", 8)))
    base_queries = max(2, int(settings.get("max_queries", 12)))
    base_fetch = max(1, int(settings.get("max_fetch_per_query", 4)))
    base_sem = float(settings.get("semantic_threshold", 0.70))

    if level == "maximum":
        return {
            "level": level,
            "min_words": max(5, base_min - 3),
            "max_queries": base_queries + 10,
            "max_fetch": base_fetch + 3,
            "max_per_domain": 4,
            "semantic_threshold": round(max(0.55, base_sem - 0.08), 2),
            "para_min_content": 6,
            "para_min_shared": 4,
            "para_min_ratio": 0.38,
            "para_min_rare": 3,
            "tfidf_min_cosine": 0.26,
            "tfidf_min_shared": 4,
            "min_query_terms": 5,
            "academic_all": True,
            "near_budget": 4,
        }
    if level == "strict":
        return {
            "level": level,
            "min_words": max(5, base_min - 2),
            "max_queries": base_queries + 6,
            "max_fetch": base_fetch + 2,
            "max_per_domain": 3,
            "semantic_threshold": round(max(0.58, base_sem - 0.05), 2),
            "para_min_content": 7,
            "para_min_shared": 5,
            "para_min_ratio": 0.45,
            "para_min_rare": 3,
            "tfidf_min_cosine": 0.29,
            "tfidf_min_shared": 4,
            "min_query_terms": 5,
            "academic_all": True,
            "near_budget": 3,
        }
    return {
        "level": "balanced",
        "min_words": base_min,
        "max_queries": base_queries,
        "max_fetch": base_fetch,
        "max_per_domain": 2,
        "semantic_threshold": round(base_sem, 2),
        "para_min_content": 8,
        "para_min_shared": 6,
        "para_min_ratio": 0.50,
        "para_min_rare": 4,
        "tfidf_min_cosine": 0.32,
        "tfidf_min_shared": 5,
        "min_query_terms": 6,
        "academic_all": False,
        "near_budget": None,
    }
