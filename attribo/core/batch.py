"""
Folder batch scanning: run scans across many documents and write per-file
findings plus a master index report.

(c) 2026 Attribo. All rights reserved.
"""
from html import escape
from pathlib import Path

from .pipeline import run_scan
from ..report.findings import build_findings_html

SUPPORTED = {".docx", ".pdf", ".txt", ".md", ".rtf", ".odt"}


def collect_documents(folder) -> list:
    folder = Path(folder)
    files = [
        p
        for p in sorted(folder.rglob("*"))
        if p.is_file() and p.suffix.lower() in SUPPORTED and not p.name.startswith("~$")
    ]
    return files


def _build_index(results: list, out_dir: Path) -> str:
    rows = []
    for item in results:
        if isinstance(item, tuple):  # (error, path, message)
            rows.append(
                f"<tr><td>{escape(Path(item[1]).name)}</td><td colspan='4' class='bad'>"
                f"Error: {escape(item[2])}</td></tr>"
            )
            continue
        link = f"{escape(Path(item.file_path).stem)}_{escape(item.report_id)}.html"
        rows.append(
            "<tr>"
            f"<td><a href='{link}'>{escape(item.file_name)}</a></td>"
            f"<td>{item.similarity}%</td>"
            f"<td>{item.paraphrase_risk}%</td>"
            f"<td>{item.ai_likelihood}%</td>"
            f"<td>{item.integrity}%</td>"
            f"<td>{len(item.matches)}</td>"
            "</tr>"
        )
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Attribo batch report</title>
<style>
  body {{ background:#0B0E13; color:#E8EDF4; font-family:"Segoe UI",sans-serif; margin:40px; }}
  table {{ border-collapse:collapse; width:100%; margin-top:16px; }}
  th, td {{ border:1px solid #232B3A; padding:8px 10px; text-align:left; font-size:14px; }}
  th {{ background:#121722; color:#8A94A6; }}
  tr:nth-child(even) td {{ background:#0F141E; }}
  a {{ color:#5B8CFF; }}
  .bad {{ color:#FF5B5B; }}
  .muted {{ color:#8A94A6; }}
</style></head><body>
<h1>Batch screening report</h1>
<div class="muted">Files: {len(results)} · Output folder: {escape(str(out_dir))}</div>
<table>
<tr><th>Document</th><th>Similarity</th><th>Paraphrase</th><th>AI</th><th>Integrity</th><th>Flags</th></tr>
{''.join(rows)}
</table>
<footer class="muted" style="margin-top:26px;">(c) 2026 Attribo. All rights reserved. Advisory screening only.</footer>
</body></html>"""


def run_batch(paths, settings: dict, out_dir, progress=None, cancel=None) -> list:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    results = []
    total = max(len(paths), 1)
    for i, path in enumerate(paths):
        if cancel and cancel():
            break
        if progress:
            progress(i, total, Path(path).name)
        try:
            result = run_scan(path, settings)
            results.append(result)
            try:
                build_findings_html(
                    result, str(out / f"{Path(path).stem}_{result.report_id}.html")
                )
            except Exception:  # noqa: BLE001
                pass
        except Exception as exc:  # noqa: BLE001
            results.append(("error", str(path), str(exc)))
    if progress:
        progress(total, total, "writing index...")
    (out / "index.html").write_text(_build_index(results, out), encoding="utf-8")
    return results
