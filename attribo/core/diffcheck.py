"""
Revision diff: Draft I vs Draft II.

Compares two scans of the same document by fuzzy-matching flagged passages:
fixed / persisting / new, plus score deltas (similarity, paraphrase, AI,
integrity). Offline; pure logic.

(c) 2026 Ayush Gupta (Attribo). All rights reserved.
"""
from difflib import SequenceMatcher


def _norm(text: str) -> str:
    return " ".join(str(text or "").lower().split())


def _same(a, b) -> bool:
    na, nb = _norm(getattr(a, "text", "")), _norm(getattr(b, "text", ""))
    if not na or not nb:
        return False
    if na[:160] == nb[:160]:
        return True
    return SequenceMatcher(None, na[:200], nb[:200]).ratio() >= 0.72


def compare_results(old, new) -> dict:
    old_matches = list(old.matches)
    new_matches = list(new.matches)
    used = [False] * len(old_matches)

    persisting, new_flags = [], []
    for match in new_matches:
        hit = -1
        for index, old_match in enumerate(old_matches):
            if used[index]:
                continue
            if _same(old_match, match):
                hit = index
                break
        if hit >= 0:
            used[hit] = True
            persisting.append(match)
        else:
            new_flags.append(match)

    fixed = [match for index, match in enumerate(old_matches) if not used[index]]
    return {
        "fixed": fixed,
        "persisting": persisting,
        "new": new_flags,
        "deltas": {
            "similarity": round(new.similarity - old.similarity, 1),
            "paraphrase": round(new.paraphrase_risk - old.paraphrase_risk, 1),
            "ai": round(new.ai_likelihood - old.ai_likelihood, 1),
            "integrity": round(new.integrity - old.integrity, 1),
        },
        "old_meta": {
            "report_id": old.report_id,
            "timestamp": old.timestamp,
            "similarity": old.similarity,
            "integrity": old.integrity,
            "ai": old.ai_likelihood,
            "flags": len(old_matches),
        },
        "new_meta": {
            "report_id": new.report_id,
            "timestamp": new.timestamp,
            "similarity": new.similarity,
            "integrity": new.integrity,
            "ai": new.ai_likelihood,
            "flags": len(new_matches),
        },
    }
