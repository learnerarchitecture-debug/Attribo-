# Roadmap — Attribo

> © 2026 Attribo. All rights reserved.

## v0.10.0 — Trust, automation & AI update (current)

- Evidence viewer: your passage side-by-side with the source passage (context snippets on every match)
- Highlighted copy export (HTML, print-to-PDF): color-coded flags + numbered source footnotes
- Word review copy export: flags as inline comments in a `.docx` copy
- Internal duplication detector (repeats within your own document, reported separately)
- Cite Assist tab: uncited claim sentences + one-click candidate sources (OpenAlex / Crossref)
- References tab: bibliography validation (existence, DOI correctness, retractions)
- Batch mode: scan a folder → per-file findings + master index.html
- Watch folder automation with system-tray notifications
- Optional semantic layer: local ONNX MiniLM embeddings (one-time ~90 MB download, offline afterwards)
- TF-IDF rarity-weighted paraphrase pass
- AI detector upgraded to stylometry-1.5 (discourse-marker + opener-repetition metrics)

## v1.0 — Trust release (next)

- Benchmarks run on PAN corpora; results published in `docs/ACCURACY_AND_LIMITS.md`
- ONNX AI-classifier bundled (offscreen, small) alongside stylometry
- CORE API connector (OA full texts)
- OCR for scanned PDFs (Tesseract bundled optional install)
- Report page in-app (HTML preview) matching the PDF design

## v1.2 — Author workflow

- Draft revision tracker (scan I→III, score-over-time chart)
- Citation auto-formatting (APA / MLA / IEEE)
- Supervisor one-pager report mode

## v1.5 — Coverage & languages

- Cross-lingual matching (translated plagiarism; multilingual embeddings)
- Arabic-first UI localization (RTL) + Arabic tokenizer tuning
- Full per-sentence heatmap view

## v2.0 — Institution option (only if desired)

- Department dashboard (batch scans, cohort reports)
- Verification page for certificate IDs (hosted, optional)
- Moodle/Word add-in
- Self-hosted mode for universities (data sovereignty pitch)

## Idea bank (uncommitted)

- Integrity statement generator (appendix text with certificate ID)
- Premium scan toggle via licensed commercial API (user's own key)
- Auto-update check (signed manifest)
- Mac/Linux builds (PySide6 is cross-platform; packaging differs)

## Explicit non-goals

- Detecting "100% of plagiarism" — impossible; we ship honest coverage instead
- Any feature meant to evade institutional checks without attribution
- Storing, uploading, or analyzing user documents on any server

---
*© 2026 Attribo. All rights reserved.*
