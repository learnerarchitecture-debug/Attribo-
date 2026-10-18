"""
Redacted shareable report: findings + sources WITHOUT your draft text.

Safe to hand to a supervisor or advisor before you are ready to share the
draft itself: each flag keeps its type, size, source and suggested fix, while
the passage itself is replaced by a marker (word count only).

(c) 2026 Ayush Gupta (Attribo). All rights reserved.
"""
import datetime
from html import escape
from pathlib import Path

from .. import APP_NAME, COPYRIGHT
from ..core import fixcite
from ..theme import MATCH_COLORS, MATCH_LABELS

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
  body {{ background:#0d0f14; color:#e6e9f0; font-family:'Segoe UI',Arial,sans-serif;
         margin:0; padding:36px 42px; line-height:1.5; }}
  h1 {{ font-size:24px; margin:0 0 4px; color:#ffffff; }}
  .meta {{ color:#9aa3b5; font-size:13px; margin-bottom:22px; }}
  .scores {{ display:flex; gap:14px; flex-wrap:wrap; margin:18px 0 26px; }}
  .score {{ background:#151926; border:1px solid #262d3f; border-radius:10px;
            padding:10px 16px; min-width:110px; }}
  .score b {{ display:block; font-size:20px; color:#ffffff; }}
  .score span {{ font-size:11px; color:#9aa3b5; text-transform:uppercase;
                 letter-spacing:.6px; }}
  .flag {{ background:#12151f; border:1px solid #262d3f; border-radius:10px;
           padding:14px 16px; margin-bottom:12px; }}
  .head {{ display:flex; align-items:center; gap:10px; margin-bottom:6px; }}
  .tag {{ border:1px solid; border-radius:6px; padding:1px 8px; font-size:11px;
          font-weight:600; text-transform:uppercase; letter-spacing:.5px; }}
  .meta2 {{ color:#9aa3b5; font-size:12px; }}
  .src {{ font-size:13px; margin-bottom:6px; }}
  .src a {{ color:#7aa2ff; text-decoration:none; }}
  .fix {{ font-size:13px; color:#c8d0e0; }}
  .note {{ margin-top:26px; padding:14px 16px; border-left:3px solid #4f6bff;
           background:#12151f; border-radius:6px; font-size:13px; color:#9aa3b5; }}
  .footer {{ margin-top:26px; color:#5f6980; font-size:12px; }}
</style>
</head>
<body>
<h1>{app} - Redacted findings report</h1>
<div class="meta">Document: <b>{doc}</b> &middot; Report ID: {report_id} &middot; {ts}<br>
Scan strictness: {strictness} &middot; {flags} flag(s) &middot; passages deliberately omitted</div>
<div class="scores">{scores}</div>
{body}
<div class="note"><b>Why passages are missing:</b> this redacted copy lists what was
found and how to fix it, without quoting your draft. The full report and the
in-app worklist contain the passages themselves.</div>
<div class="footer">{copyright} - Advisory report; not a legal determination of
plagiarism or AI use.</div>
</body>
</html>
"""


def build_redacted_html(result, path) -> int:
    """Writes the redacted HTML. Returns the number of flags included."""
    matches = [m for m in result.matches if (getattr(m, "text", "") or "").strip()]

    rows = []
    for index, match in enumerate(matches, start=1):
        mtype = getattr(match, "match_type", "")
        words = len(fixcite.clean_text(getattr(match, "text", "")).split())
        color = MATCH_COLORS.get(mtype, "#5B8CFF")
        label = MATCH_LABELS.get(mtype, mtype)
        source = escape(str(getattr(match, "source_title", "") or "internal comparison"))
        url = str(getattr(match, "source_url", "") or "")
        source_html = f'<a href="{escape(url)}">{source}</a>' if url else source
        suggestion = escape(
            str(getattr(match, "suggestion", "") or fixcite.suggestion_for(mtype))
        )
        rows.append(
            f"""<div class="flag">
  <div class="head">
    <span class="tag" style="color:{color};border-color:{color}">{escape(label)}</span>
    <span class="meta2">Flag {index} &middot; {int(getattr(match, 'tokens', 0))} tokens
      &middot; {words} words &middot; passage redacted</span>
  </div>
  <div class="src">Source: {source_html}</div>
  <div class="fix"><b>Suggested fix:</b> {suggestion}</div>
</div>"""
        )

    scores = "".join(
        f'<div class="score"><b>{value}%</b><span>{label}</span></div>'
        for label, value in (
            ("Similarity", result.similarity),
            ("Paraphrase risk", result.paraphrase_risk),
            ("AI-likelihood", result.ai_likelihood),
            ("Integrity", result.integrity),
            ("Originality", result.originality),
        )
    )

    html = PAGE.format(
        title=f"{APP_NAME} - Redacted findings - {escape(result.file_name)}",
        app=escape(APP_NAME),
        doc=escape(result.file_name),
        report_id=escape(str(result.report_id)),
        ts=escape(str(result.timestamp)),
        strictness=escape(str(getattr(result, "strictness", "balanced"))),
        flags=len(matches),
        scores=scores,
        body="\n".join(rows) if rows else "<p>No flags were recorded for this scan.</p>",
        copyright=escape(COPYRIGHT),
    )
    Path(path).write_text(html, encoding="utf-8")
    return len(matches)
