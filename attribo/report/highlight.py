"""
Highlighted document export: a full copy of the screened text with every
flagged span color-coded and linked to numbered source notes.

(c) 2026 Attribo. All rights reserved.
"""
from html import escape

from .. import APP_NAME, COPYRIGHT

TYPE_ORDER = {"verbatim": 0, "near": 1, "semantic": 2, "paraphrase": 3, "duplicate": 4}
TYPE_LABEL = {
    "verbatim": "Verbatim",
    "near": "Near-match",
    "semantic": "Semantic paraphrase",
    "paraphrase": "Paraphrase",
    "duplicate": "Internal duplicate",
}


def build_highlight_html(result, path) -> None:
    text = result.full_text or ""
    candidates = [
        m for m in result.matches if m.span_start >= 0 and m.span_end > m.span_start
    ]
    candidates.sort(key=lambda m: (TYPE_ORDER.get(m.match_type, 9), m.span_start))

    placed = []  # (start, end, match)
    for m in candidates:
        overlaps = any(not (m.span_end <= s or m.span_start >= e) for s, e, _mm in placed)
        if not overlaps:
            placed.append((m.span_start, m.span_end, m))
    placed.sort(key=lambda item: item[0])

    chunks = []
    notes = []
    cursor = 0
    for index, (start, end, m) in enumerate(placed, start=1):
        cursor = max(cursor, 0)
        if start > cursor:
            chunks.append(escape(text[cursor:start]))
        cls = m.match_type if m.match_type in TYPE_ORDER else "paraphrase"
        chunks.append(
            f'<mark class="{cls}" id="m{index}">{escape(text[start:end])}</mark>'
            f'<sup class="ref"><a href="#note{index}">{index}</a></sup>'
        )
        notes.append((index, m))
        cursor = max(cursor, end)
    if cursor < len(text):
        chunks.append(escape(text[cursor:]))

    legend = " ".join(
        f'<span class="lg"><mark class="{cls}">{label}</mark></span>'
        for cls, label in (
            ("verbatim", "Verbatim"),
            ("near", "Near-match"),
            ("semantic", "Semantic"),
            ("paraphrase", "Paraphrase"),
            ("duplicate", "Internal duplicate"),
        )
    )

    note_rows = []
    for index, m in notes:
        link = (
            f'<a href="{escape(m.source_url)}">{escape(m.source_title or m.source_url)}</a>'
            if m.source_url
            else escape(m.source_title or "This document")
        )
        note_rows.append(
            f"""
        <div class="note" id="note{index}">
          <div class="nhead"><b>#{index} · {TYPE_LABEL.get(m.match_type, m.match_type)}</b>
            · {int(m.tokens)} tokens · <a class="back" href="#m{index}">back</a></div>
          <div class="nsrc">Source: {link}</div>
          {f'<blockquote>{escape(m.source_snippet[:400])}</blockquote>' if m.source_snippet else ""}
          <p class="fix">{escape(m.suggestion)}</p>
        </div>"""
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{escape(APP_NAME)} - Highlighted copy {escape(result.report_id)}</title>
<style>
  body {{ background:#0B0E13; color:#E8EDF4; font-family:"Segoe UI",sans-serif; margin:40px; line-height:1.75; max-width:960px; }}
  h1 {{ font-size:22px; margin:0 0 2px 0; }}
  .muted {{ color:#8A94A6; }}
  .doc {{ background:#121722; border:1px solid #232B3A; border-radius:12px; padding:22px 26px; white-space:pre-wrap; font-size:15px; }}
  .legend {{ margin:14px 0; }}
  .lg {{ margin-right:14px; font-size:13px; }}
  mark {{ border-radius:4px; padding:1px 2px; color:inherit; }}
  mark.verbatim {{ background:rgba(255,91,91,.32); box-shadow:inset 0 -2px 0 #FF5B5B; }}
  mark.near {{ background:rgba(255,159,64,.30); box-shadow:inset 0 -2px 0 #FF9F40; }}
  mark.semantic {{ background:rgba(77,163,255,.30); box-shadow:inset 0 -2px 0 #4DA3FF; }}
  mark.paraphrase {{ background:rgba(250,204,21,.26); box-shadow:inset 0 -2px 0 #FACC15; }}
  mark.duplicate {{ background:rgba(192,132,252,.30); box-shadow:inset 0 -2px 0 #C084FC; }}
  sup.ref a {{ color:#5B8CFF; text-decoration:none; font-weight:600; }}
  .note {{ background:#121722; border:1px solid #232B3A; border-radius:12px; padding:12px 16px; margin:10px 0; font-size:14px; line-height:1.5; }}
  .nhead {{ color:#8A94A6; }}
  .back {{ color:#8A94A6; font-size:12px; }}
  blockquote {{ background:#10161F; border-left:3px solid #5B8CFF; margin:8px 0; padding:8px 12px; border-radius:6px; white-space:pre-wrap; }}
  .fix {{ color:#34D399; margin:6px 0 0 0; }}
  a {{ color:#5B8CFF; }}
  @media print {{
    body {{ background:#fff; color:#111; margin:14mm; }}
    .doc, .note {{ background:#fff; border-color:#ccc; }}
    mark {{ background:#f6f6f8; box-shadow:none; }}
    mark.verbatim {{ border-bottom:2px solid #FF5B5B; }}
    mark.near {{ border-bottom:2px solid #FF9F40; }}
    mark.semantic {{ border-bottom:2px solid #4DA3FF; }}
    mark.paraphrase {{ border-bottom:2px solid #FACC15; }}
    mark.duplicate {{ border-bottom:2px solid #C084FC; }}
    blockquote {{ background:#f4f4f6; }}
    .fix {{ color:#0a7a4f; }}
    a {{ color:#2451d8; }}
  }}
</style>
</head>
<body>
<h1>{escape(APP_NAME)} - Highlighted copy</h1>
<div class="muted">Report {escape(result.report_id)} · {escape(result.file_name)} ·
Similarity {result.similarity}% · Integrity {result.integrity}% ·
{len(placed)} highlighted passage(s) · Strictness: {escape(str(getattr(result, "strictness", "balanced")))}</div>
<div class="legend">{legend}</div>
<div class="doc">{''.join(chunks)}</div>
<h2>Source notes</h2>
{''.join(note_rows) or '<p class="muted">No flagged passages.</p>'}
<footer class="muted" style="margin-top:30px;">{escape(COPYRIGHT)} · Advisory screening only.</footer>
</body>
</html>"""

    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html)
