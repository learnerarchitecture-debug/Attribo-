"""
Offline smoke test for Attribo.

Run from the project root:
    C:\\apcvenv\\Scripts\\python.exe tests\\smoke_test.py

No network access required.

(c) 2026 Attribo. All rights reserved.
"""
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> int:
    from attribo.storage import db

    db.init_db()
    print("[ok] database init")

    # -- matching ------------------------------------------------------
    from attribo.core.matching import (
        content_stems,
        find_near_runs,
        find_verbatim_runs,
        paraphrase_check,
        tokenize_spans,
    )

    a = "The quick brown fox jumps over the lazy dog near the river bank in the morning light"
    b = "The quick brown fox jumps over the lazy dog and then it went home"
    runs = find_verbatim_runs(tokenize_spans(a), [t[0] for t in tokenize_spans(b)], 8)
    assert runs and runs[0][3] >= 8, "verbatim detection failed"
    print("[ok] verbatim matching")

    a2 = (
        "urban planning policies strongly influence residential development "
        "patterns across large metropolitan regions"
    )
    b2 = (
        "urban planning strategies strongly influence residential development "
        "patterns across large metropolitan regions"
    )
    near = find_near_runs(tokenize_spans(a2), [t[0] for t in tokenize_spans(b2)], 8)
    assert near and near[0][3] >= 8, "near-match detection failed"
    print("[ok] near-match matching")

    from attribo.core.matching import (
        TfidfIndex,
        content_stem_list,
        find_internal_duplicates,
    )

    part = "alpha bravo charlie delta echo foxtrot golf hotel india juliet kilo lima"
    filler = " ".join(f"filler{i:02d}" for i in range(35))
    dups = find_internal_duplicates(tokenize_spans(f"{part} {filler} {part}"), 8, 30)
    assert dups and dups[0][3] >= 8, "internal duplicate detection failed"
    print("[ok] internal duplicate detection")

    src_a = content_stem_list(
        [t[0] for t in tokenize_spans(
            "finite element modelling software was used to carry out structural analysis of tall buildings"
        )]
    )
    src_b = content_stem_list(
        [t[0] for t in tokenize_spans(
            "soil mechanics foundations retaining walls lateral earth pressure design methods"
        )]
    )
    tfidf = TfidfIndex([src_a, src_b])
    query = content_stem_list(
        [t[0] for t in tokenize_spans(
            "structural analysis was performed using finite element modelling techniques for buildings"
        )]
    )
    hit = tfidf.best_cosine(query, min_cosine=0.2, min_shared=3)
    assert hit and hit[1] == 0, "tf-idf index picked the wrong source"
    print("[ok] TF-IDF paraphrase index")

    # -- web engine provider selection (offline) ---------------------------
    from attribo.engines.web_engine import (
        SearchHit,
        WebChecker,
        dedupe_hits,
    )

    checker = WebChecker({"brave_api_key": "x", "serper_api_key": "y"})
    assert checker.available(), "provider detection failed"
    assert checker.configured_providers() == ["brave", "serper"], "provider order wrong"
    assert WebChecker({}).search("phrase") == [], "empty checker returned hits"
    merged = dedupe_hits(
        [
            SearchHit("a", "https://example.com/x/", ""),
            SearchHit("b", "https://example.com/x", ""),
            SearchHit("c", "https://other.org/", ""),
        ]
    )
    assert [h.title for h in merged] == ["a", "c"], "URL dedupe failed"
    print("[ok] web engine provider selection")

    sentence = "structural analysis was performed using finite element modelling software"
    source = content_stems(
        [
            t[0]
            for t in tokenize_spans(
                "finite element modelling software was used to carry out structural analysis"
            )
        ]
    )
    assert paraphrase_check([t[0] for t in tokenize_spans(sentence)], source) is not None, (
        "paraphrase heuristic failed"
    )
    print("[ok] paraphrase heuristic (stemmed)")

    # -- AI heuristic --------------------------------------------------
    from attribo.core.ai_detect import analyze_ai

    ai = analyze_ai("The system was designed carefully. " * 40)
    assert "score" in ai and ai.get("version") == "stylometry-1.5"
    print("[ok] ai heuristic (stylometry-1.5)")

    # -- citation gaps / references -------------------------------------
    from attribo.core.citation import find_citation_gaps

    gaps = find_citation_gaps(
        [
            "Concrete production contributes approximately eight percent of global carbon "
            "emissions. This figure increased sharply between 2010 and 2020 across many "
            "developing regions."
        ]
    )
    assert gaps, "citation gap detection failed"
    no_gaps = find_citation_gaps(
        [
            "Concrete production contributes 8% of emissions (Smith, 2019). "
            "This figure increased between 2010 and 2020 (Jones, 2021)."
        ]
    )
    assert not no_gaps, "cited sentences were wrongly flagged"
    print("[ok] citation gap finder")

    from attribo.core.references import _guess_title, split_entries

    refs = split_entries(
        [
            "[1] Smith, J. (2019). Structural analysis of tall buildings. "
            "Journal of Structures, 12(3), 45-67.\n"
            "[2] Jones, A. and Lee, B. (2021). Concrete creep in high-rise "
            "construction. Cement and Concrete Research, 8(1), 1-20."
        ]
    )
    assert len(refs) == 2, f"reference split failed: {len(refs)}"
    assert "Structural analysis" in _guess_title(refs[0]), "title guess failed"
    print("[ok] reference parsing")

    # -- pipeline (local mode) ------------------------------------------
    tmp = Path(tempfile.mkdtemp(prefix="attribo_"))
    doc = tmp / "sample.txt"
    doc.write_text(
        "This is a sample thesis paragraph about structural engineering and "
        "construction methods.\n\n"
        + "Urban planning policies influence residential development patterns "
        "across metropolitan regions worldwide. " * 4,
        encoding="utf-8",
    )
    settings = {
        "enable_web": False,
        "enable_academic": False,
        "enable_ai": True,
        "max_queries": 5,
        "min_match_words": 8,
        "exclude_quotes": False,
        "google_api_key": "",
        "google_cx": "",
        "brave_api_key": "",
        "license_key": "",
        "fetch_timeout": 5,
        "max_fetch_per_query": 2,
    }
    from attribo.core.pipeline import run_scan

    result = run_scan(str(doc), settings)
    assert result.report_id and result.doc_hash and result.words > 0
    print("[ok] pipeline (local mode)")

    # -- local archive ----------------------------------------------------
    archive_dir = tmp / "archive"
    archive_dir.mkdir()
    (archive_dir / "previous_thesis.txt").write_text(
        "Urban planning policies influence residential development patterns "
        "across metropolitan regions worldwide. " * 4,
        encoding="utf-8",
    )
    archive_settings = dict(settings)
    archive_settings.update({"enable_archive": True, "archive_folder": str(archive_dir)})
    archive_result = run_scan(str(doc), archive_settings)
    assert any(s.kind == "archive" for s in archive_result.sources), "archive source missing"
    assert any(m.match_type in ("verbatim", "near") for m in archive_result.matches), (
        "archive match missing"
    )
    assert archive_result.similarity > 0, "archive similarity should be > 0"
    print("[ok] local archive comparison")

    # -- findings HTML -----------------------------------------------------
    from attribo.report.findings import build_findings_html

    findings_file = tmp / "findings.html"
    build_findings_html(archive_result, str(findings_file))
    assert "Attribo" in findings_file.read_text(encoding="utf-8")
    print("[ok] findings HTML export")

    # -- highlighted copy ---------------------------------------------------
    from attribo.report.highlight import build_highlight_html

    highlight_file = tmp / "highlighted.html"
    build_highlight_html(archive_result, str(highlight_file))
    assert "Highlighted copy" in highlight_file.read_text(encoding="utf-8")
    print("[ok] highlighted copy export")

    # -- docx scan + Word review copy ---------------------------------------
    from docx import Document as DocxDocument

    from attribo.report.word_export import export_docx_with_comments

    docx_path = tmp / "chapter.docx"
    d = DocxDocument()
    d.add_paragraph(
        "Urban planning policies influence residential development patterns "
        "across metropolitan regions worldwide. " * 4
    )
    d.add_paragraph(
        "This paragraph is original writing about design studio pedagogy and "
        "contains no copied material whatsoever in this sentence."
    )
    d.save(str(docx_path))
    docx_result = run_scan(str(docx_path), archive_settings)
    review_path = tmp / "review.docx"
    added, skipped = export_docx_with_comments(docx_result, str(review_path))
    assert added >= 1, "word comment export added no comments"
    import zipfile as _zip

    with _zip.ZipFile(review_path) as zf:
        assert "word/comments.xml" in zf.namelist(), "comments part missing"
    print(f"[ok] word review copy ({added} comments, {skipped} skipped)")

    # -- batch folder scan ----------------------------------------------------
    from attribo.core.batch import run_batch

    second_doc = tmp / "second.txt"
    second_doc.write_text(
        "A short note on architectural history and modernism. " * 6, encoding="utf-8"
    )
    batch_settings = {
        "enable_web": False,
        "enable_academic": False,
        "enable_ai": True,
        "max_queries": 3,
        "min_match_words": 8,
        "exclude_quotes": False,
        "enable_archive": False,
        "fetch_timeout": 5,
        "max_fetch_per_query": 2,
        "license_key": "",
    }
    batch_out = tmp / "batch_out"
    batch_results = run_batch(
        [str(doc), str(second_doc)], batch_settings, str(batch_out)
    )
    assert len(batch_results) == 2, "batch run failed"
    assert (batch_out / "index.html").exists(), "batch index missing"
    print("[ok] batch folder scan")

    # -- PDFs ------------------------------------------------------------
    from attribo.report import pdf_builder

    report_pdf = tmp / "report.pdf"
    cert_pdf = tmp / "certificate.pdf"
    pdf_builder.build_report(result, str(report_pdf))
    pdf_builder.build_certificate(result, str(cert_pdf), licensed=False)
    assert report_pdf.stat().st_size > 2000, "report pdf too small"
    assert cert_pdf.stat().st_size > 2000, "certificate pdf too small"
    print("[ok] report + certificate PDFs")

    # -- licensing -------------------------------------------------------
    from attribo.licensing.keycheck import make_key, verify_key

    key = make_key("Test User", "2030-01-01")
    info = verify_key(key)
    assert info and info["expired"] is False
    assert verify_key("AI-BOGUS-2030-01-01-DEADBEEF00") is None
    print("[ok] licensing")

    # -- v2.0: strictness profiles -----------------------------------------
    from attribo.core.strictness import profile as strictness_profile

    balanced = strictness_profile({"strictness": "balanced"})
    maximum = strictness_profile({"strictness": "maximum"})
    assert maximum["min_words"] < balanced["min_words"], "strictness did not tighten"
    assert maximum["semantic_threshold"] < balanced["semantic_threshold"]
    assert maximum["max_queries"] > balanced["max_queries"]
    assert archive_result.strictness == "strict", "default strictness is not strict"
    print("[ok] strictness profiles (default: strict)")

    # -- v2.0: Fix & Cite helpers ------------------------------------------
    from attribo.core import fixcite

    sample = next(m for m in archive_result.matches if m.match_type in ("verbatim", "near"))
    assert "quote" in fixcite.suggestion_for("verbatim").lower()
    frames = fixcite.attribution_frames(sample.text, sample.source_title, sample.source_url)
    assert len(frames) == 3, "attribution frames missing"
    assert fixcite.replacement_for(sample), "replacement text missing"
    block = fixcite.copy_block(sample)
    assert "Suggested replacement:" in block and "AUTHOR, YEAR" in block
    from attribo.theme import MATCH_COLORS

    assert set(MATCH_COLORS) == {"verbatim", "near", "semantic", "paraphrase", "duplicate"}
    print("[ok] Fix & Cite helpers + colour palette")

    # -- v2.0: update checker (pure logic, offline) -------------------------
    from attribo.core.updater import is_newer

    assert is_newer("2.0.1", "2.0.0")
    assert is_newer("v2.1.0", "2.0.9")
    assert not is_newer("2.0.0", "2.0.0")
    assert not is_newer("1.9.9", "2.0.0")
    print("[ok] update checker version logic")

    # -- v2.0: Fix & Cite worklist (.docx) ----------------------------------
    from attribo.report.word_export import build_worklist_docx

    worklist_path = tmp / "worklist.docx"
    exported = build_worklist_docx(archive_result, str(worklist_path))
    assert exported >= 1, "worklist exported no rows"
    assert worklist_path.stat().st_size > 3000, "worklist docx too small"
    print(f"[ok] Fix & Cite worklist ({exported} flags)")

    # -- v2.0: tamper-evident signing ----------------------------------------
    from attribo.core import signing

    signature = signing.sign_result(archive_result)
    assert signature.startswith("SIG-"), "signature prefix missing"
    assert signing.verify(
        archive_result.report_id,
        archive_result.doc_hash,
        archive_result.similarity,
        archive_result.integrity,
        archive_result.ai_likelihood,
        archive_result.timestamp,
        signature,
    ), "signature roundtrip failed"
    assert not signing.verify(
        archive_result.report_id,
        archive_result.doc_hash,
        0.0,
        0.0,
        0.0,
        archive_result.timestamp,
        signature,
    ), "tampered payload verified"
    print("[ok] tamper-evident signing (HMAC)")

    # -- v2.0: corpus vault (offline) -----------------------------------------
    from attribo.core import vault

    vault.clear()
    vault_settings = dict(settings)
    vault_settings.update({"vault_enabled": True, "enable_archive": False})
    vault_first = run_scan(str(doc), vault_settings)
    assert vault.list_docs(), "vault list empty after scan"
    vault_second = run_scan(str(docx_path), vault_settings)
    assert any(s.kind == "vault" for s in vault_second.sources), "vault source missing"
    assert any(m.match_type in ("verbatim", "near") for m in vault_second.matches), (
        "vault self-plagiarism match missing"
    )
    assert vault.clear() >= 1, "vault clear failed"
    print("[ok] corpus vault (index + self-plagiarism)")

    # -- v2.0: citation graph + quote audit (offline) --------------------------
    from attribo.core import citationgraph

    graph = citationgraph.build_citation_graph(
        "Concrete creep matters (Smith, 2019). The theory (Jones, 2021) disagrees.",
        [
            "[1] Smith, J. (2019). Structural analysis of tall buildings.",
            "[2] Smith, J. (2019). Structural analysis of tall buildings.",
            "[3] Lee, K. (2018). Uncited work about soil mechanics.",
        ],
    )
    assert graph["entries"] == 3, "citation graph entry count wrong"
    assert any("lee" in item.lower() for item in graph["uncited"]), "uncited ref not found"
    assert graph["duplicates"], "duplicate reference not found"
    quotes = citationgraph.audit_quotes(
        'He wrote: "this specific quoted passage has no citation anywhere near it at all".'
    )
    assert quotes and quotes[0]["attributed"], "attribution detection failed"
    print("[ok] citation graph + quote audit")

    # -- v2.0: revision diff (offline) -----------------------------------------
    from attribo.core import diffcheck

    diff = diffcheck.compare_results(archive_result, vault_second)
    assert set(("fixed", "persisting", "new", "deltas")) <= set(diff)
    print("[ok] revision diff logic")

    # -- v2.0: thesis cross-chapter overlaps ------------------------------------
    from attribo.core import thesis

    shared = (
        "The methodology section repeats this exact shared passage about "
        "survey sampling and validation procedures across chapters. "
    )
    thesis_files = []
    for index in range(2):
        thesis_doc = tmp / f"thesis_ch{index}.txt"
        thesis_doc.write_text(shared * 2 + f"chapter{index} " * 30, encoding="utf-8")
        thesis_files.append(str(thesis_doc))
    thesis_out = tmp / "thesis_out"
    thesis_results = run_batch(thesis_files, batch_settings, str(thesis_out))
    summary = thesis.build_thesis_summary(
        [r for r in thesis_results if not isinstance(r, tuple)], str(thesis_out)
    )
    assert summary["overlaps"] >= 1, "cross-chapter overlap not detected"
    assert Path(summary["path"]).exists(), "thesis summary missing"
    print(f"[ok] thesis mode ({summary['overlaps']} cross-chapter overlaps)")

    # -- v2.0: reports (redacted, diff HTML, packet, fixed copy) ----------------
    from attribo.report import diff_report, packet, redacted

    redacted_file = tmp / "redacted.html"
    redacted_count = redacted.build_redacted_html(archive_result, str(redacted_file))
    redacted_text = redacted_file.read_text(encoding="utf-8")
    assert redacted_count >= 1 and "passage redacted" in redacted_text
    assert sample.text[:40] not in redacted_text, "redacted report leaked draft text"
    diff_file = tmp / "diff.html"
    diff_report.build_diff_html(archive_result, vault_second, str(diff_file))
    assert "Revision diff" in diff_file.read_text(encoding="utf-8")
    packet_pdf = tmp / "packet.pdf"
    packet_signature = packet.build_packet_pdf(
        archive_result, db.recent_scans(5), str(packet_pdf)
    )
    assert packet_signature.startswith("SIG-") and packet_pdf.stat().st_size > 3000
    from attribo.report.word_export import build_fixed_copy_docx

    fixed_path = tmp / "fixed_copy.docx"
    applied, _skipped = build_fixed_copy_docx(docx_result, str(fixed_path))
    assert applied >= 1 and fixed_path.stat().st_size > 3000, "fixed copy missing"
    print(f"[ok] v2.0 reports (redacted/diff/packet/fixed copy: {applied} replaced)")

    # -- v2.0: light theme + CLI entry ------------------------------------------
    from attribo.theme import stylesheet

    assert "light theme overrides" in stylesheet("light")
    from attribo.cli import _summary as cli_summary

    cli_data = cli_summary(archive_result)
    assert cli_data["report_id"] == archive_result.report_id
    assert cli_data["scores"]["similarity"] == archive_result.similarity
    print("[ok] light theme + CLI summary")

    # -- UI (offscreen) --------------------------------------------------
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    from attribo.ui.main_window import MainWindow

    window = MainWindow(dict(settings))
    window.show()
    app.processEvents()
    window.close()
    print("[ok] UI instantiates (offscreen)")

    print("")
    print("SMOKE TEST PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
