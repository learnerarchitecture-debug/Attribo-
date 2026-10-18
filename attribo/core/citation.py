"""
Citation gap finder: sentences that make claims but carry no citation nearby.
Candidate sources to cite come from OpenAlex / Crossref (on demand).

(c) 2026 Attribo. All rights reserved.
"""
import re

from .matching import STOPWORDS, tokenize_spans
from .segmenter import split_sentences_with_spans

CITATION_RE = re.compile(
    r"\(\s*[A-Z][A-Za-z'\-]+(?:\s+et\s+al\.?)?(?:\s*(?:,|&|and)\s*[A-Z][A-Za-z'\-]+)*\s*,?\s*\d{4}[a-z]?\s*\)"  # (Author, 2019)
    r"|[A-Z][A-Za-z'\-]+(?:\s+(?:and|&)\s+[A-Z][A-Za-z'\-]+)?\s+et\s+al\.?\s*,?\s*\(?\s*\d{4}"  # Author et al. (2019)
    r"|\[\d{1,3}(?:\s*[,\u2013\u2014-]\s*\d{1,3})*\]"  # [12]
    r"|\bdoi:\s*10\.\S+|\bhttps?://\S+"  # doi / url
)

CLAIM_RE = re.compile(
    r"\b(?:shows?|shown|found|findings?|demonstrat\w+|reveal\w+|indicat\w+|suggest\w*|"
    r"increase[sd]?|decrease[sd]?|significant\w*|correlat\w+|proves?|proven|concludes?|"
    r"established|according to|report(?:s|ed)?|studies|research)\b",
    re.IGNORECASE,
)

NUMBER_RE = re.compile(r"\d")


def find_citation_gaps(content_paras: list, max_gaps: int = 8) -> list:
    """Returns [{text, para, reason, phrase}] sorted by importance."""
    gaps = []
    for p_index, para in enumerate(content_paras):
        sentences = split_sentences_with_spans(para)
        prev_had_citation = True  # paragraph starts are treated leniently
        for _s, _e, sent in sentences:
            has_citation = bool(CITATION_RE.search(sent))
            words = [t[0] for t in tokenize_spans(sent) if t[0] not in STOPWORDS]
            if (
                not has_citation
                and not prev_had_citation
                and len(words) >= 8
                and (NUMBER_RE.search(sent) or CLAIM_RE.search(sent))
            ):
                phrase = " ".join(words[:12])
                reasons = []
                if NUMBER_RE.search(sent):
                    reasons.append("contains data/numbers")
                if CLAIM_RE.search(sent):
                    reasons.append("assertive claim")
                gaps.append(
                    {
                        "text": sent[:400],
                        "para": p_index,
                        "reason": ", ".join(reasons) or "claim without citation",
                        "phrase": phrase,
                    }
                )
            prev_had_citation = has_citation
    gaps.sort(key=lambda g: (NUMBER_RE.search(g["text"]) is not None, len(g["text"])), reverse=True)
    return gaps[:max_gaps]


def suggest_for_sentence(sentence: str, settings: dict, limit: int = 3) -> list:
    """Query academic APIs for candidate sources for a sentence."""
    from ..engines.academic import AcademicChecker

    words = [t[0] for t in tokenize_spans(sentence) if t[0] not in STOPWORDS][:12]
    if len(words) < 4:
        return []
    checker = AcademicChecker(settings)
    hits = checker.search(" ".join(words))
    return [
        {"title": h.title, "url": h.url, "doi": h.doi, "text": h.text}
        for h in hits[:limit]
    ]
