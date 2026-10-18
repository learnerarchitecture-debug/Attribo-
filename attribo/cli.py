"""
Attribo CLI - scripting and batch automation.

Examples:
    python -m attribo.cli scan thesis.docx --json
    python -m attribo.cli scan chapter.pdf --html findings.html --strictness maximum
    python -m attribo.cli scan draft.txt --offline --vault

Exit codes: 0 = success, 2 = error.
(c) 2026 Ayush Gupta (Attribo). All rights reserved.
"""
import argparse
import json
import sys
from pathlib import Path


def _build_settings(args):
    from .storage.settings import load_settings

    settings = load_settings()
    if args.strictness:
        settings["strictness"] = args.strictness
    if args.offline:
        settings["enable_web"] = False
        settings["enable_academic"] = False
    if args.vault:
        settings["vault_enabled"] = True
    return settings


def _summary(result) -> dict:
    return {
        "file": result.file_name,
        "report_id": result.report_id,
        "timestamp": result.timestamp,
        "words": result.words,
        "strictness": getattr(result, "strictness", "balanced"),
        "scores": {
            "similarity": result.similarity,
            "originality": result.originality,
            "paraphrase_risk": result.paraphrase_risk,
            "ai_likelihood": result.ai_likelihood,
            "integrity": result.integrity,
        },
        "queries_run": result.queries_run,
        "sources": len(result.sources),
        "citation_gaps": len(result.citation_gaps),
        "warnings": list(result.warnings),
        "flags": [
            {
                "type": match.match_type,
                "tokens": match.tokens,
                "source": match.source_title,
                "url": match.source_url,
                "text": match.text,
                "suggestion": match.suggestion,
                "span": [match.span_start, match.span_end],
            }
            for match in result.matches
        ],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="attribo", description="Attribo CLI")
    parser.add_argument("--version", action="store_true", help="print version and exit")
    sub = parser.add_subparsers(dest="command")

    scan = sub.add_parser("scan", help="scan a single document")
    scan.add_argument("file")
    scan.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    scan.add_argument("--html", metavar="OUT", default="", help="write a findings HTML")
    scan.add_argument(
        "--strictness",
        choices=["balanced", "strict", "maximum"],
        default="",
        help="override the scan strictness",
    )
    scan.add_argument(
        "--offline",
        action="store_true",
        help="local analysis only - disables web and academic sources",
    )
    scan.add_argument(
        "--vault",
        action="store_true",
        help="check against (and index into) the corpus vault",
    )
    args = parser.parse_args(argv)

    from . import APP_NAME, __version__

    if args.version and not args.command:
        print(f"{APP_NAME} {__version__}")
        return 0
    if args.command != "scan":
        parser.print_help()
        return 2

    from .core.pipeline import run_scan
    from .storage import db

    path = Path(args.file)
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        return 2

    db.init_db()
    settings = _build_settings(args)

    def progress(pct, message):
        print(f"[{pct:3d}%] {message}", file=sys.stderr)

    try:
        result = run_scan(str(path), settings, progress=progress)
    except Exception as exc:  # noqa: BLE001
        print(f"Scan failed: {exc}", file=sys.stderr)
        return 2

    try:
        db.save_scan(result)
    except Exception:  # noqa: BLE001
        pass

    if args.html:
        from .report.findings import build_findings_html

        build_findings_html(result, args.html)
        print(f"Findings written to {args.html}", file=sys.stderr)

    if args.json:
        print(json.dumps(_summary(result), indent=2, ensure_ascii=False))
    else:
        data = _summary(result)
        print(f"{APP_NAME} scan: {data['file']}")
        print(
            f"Report ID: {data['report_id']} | strictness: {data['strictness']} | "
            f"queries: {data['queries_run']}"
        )
        print(
            f"Similarity {data['scores']['similarity']}% | "
            f"Integrity {data['scores']['integrity']}% | "
            f"Flags {len(data['flags'])}"
        )
        for flag in data["flags"][:15]:
            print(f"  - [{flag['type']}] {flag['tokens']} tokens :: {flag['source'][:70]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
