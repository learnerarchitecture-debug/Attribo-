"""
Revision diff report (Draft I vs Draft II) - HTML.

Built from core.diffcheck.compare_results: fixed / persisting / new findings
plus score deltas between two scans of the same document.

(c) 2026 Ayush Gupta (Attribo). All rights reserved.
"""
from html import escape
from pathlib import Path

from .. import APP_NAME, COPYRIGHT
from ..core import fixcite
from ..core.diffcheck import compare_results
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
  h2 {{ font-size:16px; margin:26px 0 10px; color:#ffffff; }}
  .meta {{ color:#9aa3b5; font-size:13px; margin-bottom:18px; }}
  table {{ border-collapse:collapse; width:100%; margin:10px 0 4px; font-size:13px; }}
  th, td {{ border:1px solid #262d3f; padding:7px 10px; text-align:left;
            vertical-align:top; }}
  th {{ background:#151926; color:#9aa3b5; font-weight:600; }}
  .good {{ color:#34d399; font-weight:600; }}
  .bad {{ color:#ff7b7b; font-weight:600; }}
  .flat {{ color:#9aa3b5; }}
  .flag {{ background:#12151f; border:1px solid #262d3f; border-radius:10px;
           padding:12px 14px; margin-bottom:10px; }}
  .tag {{ border:1px solid; border-radius:6px; padding:1px 8px; font-size:11px;
          font-weight:600; text-transform:uppercase; letter-spacing:.5px; }}
  .meta2 {{ color:#9aa3b5; font-size:12px; margin-left:8px; }}
  .excerpt {{ font-size:13px; margin-top:6px; color:#c8d0e0; }}
  .src {{ font-size:12px; color:#9aa3b5; margin-top:4px; }}
  .empty {{ color:#5f6980; font-size:13px; }}
  .footer {{ margin-top:26px; color:#5f6980; font-size:12px; }}
</style>
</head>
<body>
<h1>{app} - Revision diff report</h1>
<div class="meta">Document: <b>{doc}</b><br>
Draft I: {old_id} ({old_ts}) &middot; {old_flags} flag(s)<br>
Draft II: {new_id} ({new_ts}) &middot; {new_flags} flag(s)</div>
<h2>Score deltas (Draft I &rarr; Draft II)</h2>
<table>
  <tr><th>Metric</th><th>Draft I</th><th>Draft II</th><th>Change</th></tr>
  {score_rows}
</table>
<h2>Fixed ({n_fixed})</h2>
{fixed}
<h2>Persisting ({n_persisting})</h2>
{persisting}
<h2>New ({n_new})</h2>
{new}
<div class="footer">{copyright} - Advisory diff; verify each item in context.</div>
</body>
</html>
"""


def _delta_class(value: float) -> str:
    if value <= -0.05:
        return "good"
    if value >= 0.05:
        return "bad"
    return "flat"


def _score_rows(diff: dict) -> str:
    old, new, deltas = diff["old_meta"], diff["new_meta"], diff["deltas"]
    rows = []
    pairs = (
        ("Similarity", "similarity"),
        ("Paraphrase risk", "paraphrase"),
        ("AI-likelihood", "ai"),
        ("Integrity", "integrity"),
    )
    for label, key in pairs:
        old_value = float(old.get(key) or 0)
        new_value = float(new.get(key) or 0)
        change = float(deltas.get(key) or 0)
        sign = "+" if change > 0 else ""
        note = (
            "improved" if _delta_class(change) == "good"
            else "worse" if _delta_class(change) == "bad"
            else "unchanged"
        )
        rows.append(
            f"<tr><td>{label}</td><td>{old_value:.1f}%</td><td>{new_value:.1f}%</td>"
            f'<td class="{_delta_class(change)}">{sign}{change:.1f} pts ({note})</td></tr>'
        )
    return "\n  ".join(rows)


def _flag_cards(matches: list, limit: int = 40) -> str:
    if not matches:
        return '<p class="empty">None.</p>'
    cards = []
    for match in matches[:limit]:
        mtype = getattr(match, "match_type", "")
        color = MATCH_COLORS.get(mtype, "#5B8CFF")
        label = MATCH_LABELS.get(mtype, mtype)
        excerpt = escape(fixcite.clean_text(getattr(match, "text", ""))[:220])
        source = escape(str(getattr(match, "source_title", "") or "internal comparison"))
        cards.append(
            f"""<div class="flag">
  <span class="tag" style="color:{color};border-color:{color}">{escape(label)}</span>
  <span class="meta2">{int(getattr(match, 'tokens', 0))} tokens</span>
  <div class="excerpt">&ldquo;{excerpt}&hellip;&rdquo;</div>
  <div class="src">Source: {source}</div>
</div>"""
        )
    if len(matches) > limit:
        cards.append(f'<p class="empty">... and {len(matches) - limit} more.</p>')
    return "\n".join(cards)


def build_diff_html(old_result, new_result, path) -> dict:
    """Writes the diff HTML. Returns the diff dict from compare_results."""
    diff = compare_results(old_result, new_result)
    html = PAGE.format(
        title=f"{APP_NAME} - Revision diff - {escape(new_result.file_name)}",
        app=escape(APP_NAME),
        doc=escape(new_result.file_name),
        old_id=escape(str(diff["old_meta"]["report_id"])),
        old_ts=escape(str(diff["old_meta"]["timestamp"])),
        old_flags=diff["old_meta"]["flags"],
        new_id=escape(str(diff["new_meta"]["report_id"])),
        new_ts=escape(str(diff["new_meta"]["timestamp"])),
        new_flags=diff["new_meta"]["flags"],
        score_rows=_score_rows(diff),
        n_fixed=len(diff["fixed"]),
        n_persisting=len(diff["persisting"]),
        n_new=len(diff["new"]),
        fixed=_flag_cards(diff["fixed"]),
        persisting=_flag_cards(diff["persisting"]),
        new=_flag_cards(diff["new"]),
        copyright=escape(COPYRIGHT),
    )
    Path(path).write_text(html, encoding="utf-8")
    return diff
