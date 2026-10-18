"""
Thesis mode: treat a folder scan as chapters of one thesis.

- per-chapter score table
- aggregate scores across chapters
- cross-chapter overlap detection (verbatim runs between your own chapters),
  reported separately from external similarity so internal reuse is visible
  instead of being mixed into the external score

(c) 2026 Ayush Gupta (Attribo). All rights reserved.
"""
import statistics
from html import escape
from pathlib import Path

from .matching import find_verbatim_runs, tokenize_spans

MIN_WORDS = 8
MAX_CHAPTERS = 24
MAX_PAIRS_REPORTED = 40
MAX_CHARS = 120_000

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
  .overlap {{ background:#12151f; border:1px solid #262d3f; border-radius:10px;
              padding:12px 14px; margin-bottom:10px; }}
  .pair {{ font-size:12px; color:#9aa3b5; margin-bottom:5px; }}
  .words {{ color:#f9c74f; font-weight:600; }}
  .snip {{ font-size:13px; color:#c8d0e0; }}
  .note {{ margin-top:26px; padding:14px 16px; border-left:3px solid #4f6bff;
           background:#12151f; border-radius:6px; font-size:13px; color:#9aa3b5; }}
  .footer {{ margin-top:26px; color:#5f6980; font-size:12px; }}
</style>
</head>
<body>
<h1>{app} - Thesis summary</h1>
<div class="meta">Folder: <b>{folder}</b> &middot; {chapters} chapter(s) &middot;
{words:,} words &middot; generated {ts}</div>
<div class="scores">
  <table>
    <tr><th>Metric</th><th>Mean</th><th>Worst chapter</th></tr>
    <tr><td>Similarity</td><td>{sim_mean}%</td><td>{sim_max}%</td></tr>
    <tr><td>Integrity</td><td>{integ_mean}%</td><td>&ndash;</td></tr>
    <tr><td>AI-likelihood</td><td>{ai_mean}%</td><td>&ndash;</td></tr>
    <tr><td>Flagged passages</td><td>{flags}</td><td>&ndash;</td></tr>
  </table>
</div>
<h2>Per-chapter results</h2>
<table>
  <tr><th>Chapter</th><th>Words</th><th>Similarity</th><th>Paraphrase</th>
      <th>AI</th><th>Integrity</th><th>Flags</th></tr>
  {rows}
</table>
<h2>Cross-chapter overlaps ({n_overlaps})</h2>
{overlaps}
<div class="note"><b>How to read this:</b> cross-chapter overlaps are text shared
between your own chapters (for example, a methods paragraph repeated in the
results). They are internal reuse, not external similarity - either vary the
wording or add a cross-reference ("see Section 2.3"). Per-chapter scores above
measure external similarity as usual.</div>
<div class="footer">{copyright} - Advisory summary; verify each item in context.</div>
</body>
</html>
"""


def cross_chapter_overlaps(results: list, min_words: int = MIN_WORDS) -> list:
    chapters = []
    for result in results[:MAX_CHAPTERS]:
        text = str(getattr(result, "full_text", "") or "")[:MAX_CHARS]
        if not text.strip():
            continue
        tokens = tokenize_spans(text)
        if len(tokens) < min_words:
            continue
        chapters.append(
            (str(getattr(result, "file_name", "chapter")), text, tokens, [t[0] for t in tokens])
        )

    overlaps = []
    for i in range(len(chapters)):
        for j in range(i + 1, len(chapters)):
            name_a, text_a, toks_a, _words_a = chapters[i]
            name_b, _text_b, _toks_b, words_b = chapters[j]
            seen = set()
            for run in find_verbatim_runs(toks_a, words_b, min_words):
                start_tok, end_tok = int(run[0]), int(run[1])
                if (start_tok, end_tok) in seen:
                    continue
                seen.add((start_tok, end_tok))
                snippet = text_a[toks_a[start_tok][1]: toks_a[end_tok - 1][2]]
                overlaps.append(
                    {
                        "chapter_a": name_a,
                        "chapter_b": name_b,
                        "words": end_tok - start_tok,
                        "snippet": snippet[:300],
                    }
                )
    overlaps.sort(key=lambda item: -item["words"])
    return overlaps[:MAX_PAIRS_REPORTED]


def build_thesis_summary(results, out_dir) -> dict:
    """Writes thesis_summary.html; returns {'path', 'overlaps', 'aggregate'}."""
    from .. import APP_NAME, COPYRIGHT

    results = [r for r in results if hasattr(r, "similarity")]
    if not results:
        raise RuntimeError("No chapter results to summarise.")

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "thesis_summary.html"

    import datetime

    sims = [float(getattr(r, "similarity", 0) or 0) for r in results]
    integ = [float(getattr(r, "integrity", 0) or 0) for r in results]
    ai = [float(getattr(r, "ai_likelihood", 0) or 0) for r in results]
    flags = sum(len(getattr(r, "matches", []) or []) for r in results)
    words = sum(int(getattr(r, "words", 0) or 0) for r in results)
    aggregate = {
        "chapters": len(results),
        "words": words,
        "similarity_mean": round(statistics.mean(sims), 1) if sims else 0.0,
        "similarity_max": round(max(sims), 1) if sims else 0.0,
        "integrity_mean": round(statistics.mean(integ), 1) if integ else 0.0,
        "ai_mean": round(statistics.mean(ai), 1) if ai else 0.0,
        "flags": flags,
    }

    rows = []
    for result in results:
        rows.append(
            "<tr><td>{name}</td><td>{words:,}</td><td>{sim}%</td><td>{para}%</td>"
            "<td>{ai}%</td><td>{integ}%</td><td>{flags}</td></tr>".format(
                name=escape(str(getattr(result, "file_name", "unnamed"))),
                words=int(getattr(result, "words", 0) or 0),
                sim=float(getattr(result, "similarity", 0) or 0),
                para=float(getattr(result, "paraphrase_risk", 0) or 0),
                ai=float(getattr(result, "ai_likelihood", 0) or 0),
                integ=float(getattr(result, "integrity", 0) or 0),
                flags=len(getattr(result, "matches", []) or []),
            )
        )

    overlaps = cross_chapter_overlaps(results)
    overlap_html = []
    for overlap in overlaps:
        overlap_html.append(
            f"""<div class="overlap">
  <div class="pair">{escape(overlap['chapter_a'])} &harr; {escape(overlap['chapter_b'])}
    &middot; <span class="words">{overlap['words']} words</span></div>
  <div class="snip">&ldquo;{escape(overlap['snippet'])}&hellip;&rdquo;</div>
</div>"""
        )
    if not overlap_html:
        overlap_html.append(
            '<p style="color:#5f6980;font-size:13px">No verbatim overlaps between '
            "chapters were found.</p>"
        )

    folder = Path(str(getattr(results[0], "file_path", ""))).parent
    html = PAGE.format(
        title=f"{APP_NAME} - Thesis summary",
        app=escape(APP_NAME),
        folder=escape(folder.name or str(folder)),
        chapters=aggregate["chapters"],
        words=aggregate["words"],
        ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        sim_mean=aggregate["similarity_mean"],
        sim_max=aggregate["similarity_max"],
        integ_mean=aggregate["integrity_mean"],
        ai_mean=aggregate["ai_mean"],
        flags=aggregate["flags"],
        rows="\n  ".join(rows),
        n_overlaps=len(overlaps),
        overlaps="\n".join(overlap_html),
        copyright=escape(COPYRIGHT),
    )
    path.write_text(html, encoding="utf-8")
    return {"path": str(path), "overlaps": len(overlaps), "aggregate": aggregate}
