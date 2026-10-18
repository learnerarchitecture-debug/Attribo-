"""
Findings export: a styled, self-contained HTML file that lists every flagged
passage with its source and a Fix & Cite suggestion. Opens in any browser and
can be printed to PDF or attached to an email.

(c) 2026 Attribo. All rights reserved.
"""
from html import escape

from .. import APP_NAME, COPYRIGHT


def _h(value) -> str:
    return escape(str(value or ""))


def build_findings_html(result, path) -> None:
    flags = []
    for index, m in enumerate(result.matches, 1):
        flags.append(
            f"""
        <div class="flag">
          <div class="meta">#{index} &middot; <b>{_h(m.match_type)}</b> &middot; {int(m.tokens)} tokens &middot; weight {m.weight:.2f}
            <div class="src">Source: {_h(m.source_title)} &mdash;
              <a href="{_h(m.source_url)}">{_h(m.source_url)}</a></div>
          </div>
          <blockquote>{_h(m.text)}</blockquote>
          <p class="fix">{_h(m.suggestion)}</p>
        </div>"""
        )
    flags_html = "".join(flags) or "<p>No flagged passages.</p>"

    sources_html = "".join(
        f"<li>{_h(s.title)} &mdash; <b>{s.pct:.1f}%</b> "
        f"<span class='muted'>({_h(s.kind)})</span></li>"
        for s in result.sources[:50]
    ) or "<li>None retrieved.</li>"

    warnings_html = "".join(f"<li>{_h(w)}</li>" for w in result.warnings) or "<li>None</li>"

    flagged_ai = (result.ai_details or {}).get("flagged", [])
    ai_html = "".join(f"<li>{_h(s)}</li>" for s in flagged_ai) or "<li>None detected</li>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{_h(APP_NAME)} - Findings {_h(result.report_id)}</title>
<style>
  body {{ background:#0B0E13; color:#E8EDF4; font-family:"Segoe UI",sans-serif; margin:40px; line-height:1.5; }}
  h1 {{ margin:0 0 4px 0; font-size:26px; }}
  h2 {{ margin-top:30px; font-size:18px; border-bottom:1px solid #232B3A; padding-bottom:6px; }}
  .muted {{ color:#8A94A6; }}
  .cards {{ display:flex; gap:14px; flex-wrap:wrap; margin:18px 0 6px; }}
  .card {{ background:#121722; border:1px solid #232B3A; border-radius:12px; padding:12px 20px; min-width:110px; }}
  .card .v {{ font-size:22px; font-weight:700; }}
  .flag {{ background:#121722; border:1px solid #232B3A; border-radius:12px; padding:14px 18px; margin:12px 0; }}
  .flag .meta {{ color:#8A94A6; font-size:13px; }}
  .flag .src {{ margin-top:4px; }}
  blockquote {{ background:#10161F; border-left:3px solid #5B8CFF; margin:10px 0; padding:10px 14px; border-radius:6px; }}
  .fix {{ color:#34D399; margin:6px 0 0 0; font-size:13.5px; }}
  a {{ color:#5B8CFF; word-break:break-all; }}
  ul {{ line-height:1.8; }}
  footer {{ margin-top:40px; color:#8A94A6; font-size:12px; }}
</style>
</head>
<body>
<h1>{_h(APP_NAME)} - Findings</h1>
<div class="muted">Report {_h(result.report_id)} &middot; {_h(result.file_name)} &middot; {_h(result.timestamp)}<br>
SHA-256: {_h(result.doc_hash)}</div>
<div class="cards">
  <div class="card"><div class="muted">Similarity</div><div class="v">{result.similarity}%</div></div>
  <div class="card"><div class="muted">Originality</div><div class="v">{result.originality}%</div></div>
  <div class="card"><div class="muted">Paraphrase</div><div class="v">{result.paraphrase_risk}%</div></div>
  <div class="card"><div class="muted">AI-likelihood</div><div class="v">{result.ai_likelihood}%</div></div>
  <div class="card"><div class="muted">Integrity</div><div class="v">{result.integrity}%</div></div>
</div>
<h2>Sources checked ({len(result.sources)})</h2>
<ul>{sources_html}</ul>
<h2>AI-suspicious sentences</h2>
<ul>{ai_html}</ul>
<h2>Coverage notes</h2>
<ul>{warnings_html}</ul>
<h2>Flagged passages ({len(result.matches)})</h2>
{flags_html}
<footer>{_h(COPYRIGHT)} &middot; Advisory screening only - not a legal determination.</footer>
</body>
</html>"""

    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html)
