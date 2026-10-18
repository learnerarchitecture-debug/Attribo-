"""
Fix & Cite text helpers - attribution-first remediation.

Everything here is template-based on purpose: it only uses the matched
passage and the source metadata found during the scan. No facts are
invented. Placeholders (AUTHOR, YEAR) are left for the writer to replace
with the real citation.

These helpers are not detector-evasion tools: the goal is correct quoting,
correct attribution and clearer writing.

(c) 2026 Ayush Gupta (Attribo). All rights reserved.
"""
import re
from urllib.parse import urlparse

TYPE_LABELS = {
    "verbatim": "Verbatim",
    "near": "Near-match",
    "semantic": "Semantic paraphrase",
    "paraphrase": "Paraphrase",
    "duplicate": "Internal duplicate",
}


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _lower_first(text: str) -> str:
    """'The study ...' -> 'the study ...' so reporting frames read naturally."""
    match = re.match(r"([A-Z][a-z]{3,})\b(.*)", text)
    return match.group(1).lower() + match.group(2) if match else text


def short_source(title: str = "", url: str = "") -> str:
    title = clean_text(title)
    if title and title.lower() != "this document (earlier passage)":
        return f'"{title[:70]}"'
    try:
        host = urlparse(url or "").netloc.replace("www.", "")
    except ValueError:
        host = ""
    return host or "the source"


def suggestion_for(match_type: str) -> str:
    """The 'what to do' action line shown per flag (app + every export)."""
    if match_type == "verbatim":
        return (
            "Verbatim match: this passage appears word-for-word in the source. "
            "Option 1 - quote it: put the passage in quotation marks and add the full "
            "citation. Option 2 - rewrite it: express the same idea in your own words, "
            "with different structure, and cite the source of the idea."
        )
    if match_type == "near":
        return (
            "Near-match (minor edits only): still too close to the source to count as "
            "a rewrite. Fix: quote and cite it, or rewrite substantially - change the "
            "sentence structure, not just a few words - and cite the source."
        )
    if match_type == "semantic":
        return (
            "Semantic overlap: the meaning mirrors the source without word-for-word "
            "copying. Fix: add an in-text citation right after the idea; if you "
            "followed the source closely, quote its most distinctive phrase instead."
        )
    if match_type == "duplicate":
        return (
            "Internal repeat: this text already appears earlier in your own document. "
            "Fix: keep the stronger instance and replace this one with a "
            "cross-reference ('see Section ...'), or delete it."
        )
    return (
        "Paraphrase risk: several word families are shared with the source. Fix: add "
        "a citation after the idea, and quote the most distinctive phrase directly "
        "instead of approximating it."
    )


def attribution_frames(text: str, source_title: str = "", source_url: str = "") -> list:
    """Natural reporting frames the writer can adapt (templates, not final prose)."""
    body = clean_text(text)[:400]
    if not body:
        return []
    src = short_source(source_title, source_url)
    lower = _lower_first(body)
    frames = [
        f"According to {src}, {lower}",
        f"{src} documents that {lower}",
        f"Research reported by {src} shows that {lower}",
    ]
    return [f if f.endswith((".", "!", "?")) else f + "." for f in frames]


def replacement_for(match) -> str:
    """A concrete REPLACEABLE line for the .docx worklist (placeholders kept)."""
    text = clean_text(getattr(match, "text", ""))
    mtype = getattr(match, "match_type", "")
    if not text:
        return ""
    if mtype in ("verbatim", "near"):
        return f'"{text}" (AUTHOR, YEAR)'
    if mtype == "duplicate":
        return "[cross-reference: see the earlier passage on this topic - or delete this one]"
    return f"{text} (AUTHOR, YEAR)"


def replacement_note(match) -> str:
    mtype = getattr(match, "match_type", "")
    if mtype in ("verbatim", "near"):
        return (
            "Quote the exact wording, then replace AUTHOR, YEAR with the real "
            "citation (in APA the period goes after the closing parenthesis)."
        )
    if mtype == "duplicate":
        return "Point the reader to the other instance instead of repeating the text."
    return (
        "Keep your own wording and add the citation; replace AUTHOR, YEAR. If the "
        "sentence still reads like a thesaurus swap of the source, quote its "
        "distinctive phrase instead."
    )


def copy_block(match) -> str:
    """Clipboard text for 'Copy fix for selected flag'."""
    mtype = getattr(match, "match_type", "")
    lines = [
        f"[{TYPE_LABELS.get(mtype, mtype)}] {int(getattr(match, 'tokens', 0))} tokens",
        clean_text(getattr(match, "text", ""))[:600],
    ]
    if getattr(match, "source_title", ""):
        lines.append("Source: " + clean_text(getattr(match, "source_title", "")))
    if getattr(match, "source_url", ""):
        lines.append(str(match.source_url))
    suggestion = clean_text(getattr(match, "suggestion", ""))
    if suggestion:
        lines.append("Fix: " + suggestion)
    replacement = replacement_for(match)
    if replacement:
        lines.append("Suggested replacement: " + replacement)
        lines.append("(" + replacement_note(match) + ")")
    frames = attribution_frames(
        getattr(match, "text", ""),
        getattr(match, "source_title", ""),
        getattr(match, "source_url", ""),
    )
    if frames:
        lines.append("Attribution frames you can adapt:")
        lines.extend("- " + frame for frame in frames)
    return "\n".join(lines)
