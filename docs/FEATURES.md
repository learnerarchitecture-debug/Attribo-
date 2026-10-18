# Features — Attribo

> © 2026 Attribo. All rights reserved.

Legend: ✅ implemented in v0.9–0.10 · ⌛ planned · 💡 idea bank

## Ingest & parsing

| Status | Feature |
|---|---|
| ✅ | Drag & drop one file onto the window |
| ✅ | Formats: `.docx`, `.pdf`, `.txt`, `.md`, `.rtf`, `.odt` (basic) |
| ✅ | Scanned-PDF detection with warning (OCR not yet included) |
| ⌛ | OCR pipeline (Tesseract / ocrmypdf) for scanned PDFs |
| ⌛ | Legacy `.doc` conversion via LibreOffice headless when installed |
| ✅ | Batch mode: scan a whole folder (per-file findings + master index.html) |
| ✅ | Watch folder: auto-scan new files + system-tray notification |

## Checking engines

| Status | Feature |
|---|---|
| ✅ | Web check via Google Custom Search JSON API |
| ✅ | Web check via Brave Search API |
| ✅ | Web check via Serper.dev (2,500 free credits, no card) |
| ✅ | Web check via Tavily (1,000 free credits/month, no card) |
| ✅ | Web check via Exa (free credits, no card) |
| ✅ | SearXNG support: self-hosted meta-search (unlimited, private, no account) |
| ✅ | Cross-check mode: query all configured providers, merge + dedupe by URL |
| ✅ | Evidence verification: every hit fetched and matched against the real page text |
| ✅ | "Test search APIs" button: live per-provider key check in Settings |
| ✅ | Academic check via OpenAlex (free, no key) |
| ✅ | Academic check via Crossref (free, no key) |
| ✅ | Query builder: picks the most distinctive sentences, caps query count |
| ✅ | Quoted search with automatic unquoted fallback (better recall) |
| ✅ | Source diversity cap: max 2 results per domain per scan |
| ✅ | Evidence cache in SQLite (repeat scans are faster and stay reproducible) |
| ⌛ | CORE API connector (millions of OA full texts) |
| ⌛ | Semantic Scholar / arXiv / PubMed connectors |
| ⌛ | Optional "premium scan" toggle via a licensed commercial API (BYO key) |
| ✅ | Internal archive scan: compare against a folder of prior submissions (self-plagiarism) |

## Matching analysis

| Status | Feature |
|---|---|
| ✅ | Verbatim detection: winnowing k-gram runs (default ≥ 8 words) |
| ✅ | Near-match detection: edit-tolerant alignment (a few changed words still count) |
| ✅ | Global token-stream matching: catches matches across paragraph boundaries |
| ✅ | Character-accurate span highlighting (token offsets preserved) |
| ✅ | Paraphrase-risk heuristic with light stemming (word-family overlap) |
| ✅ | TF-IDF rarity-weighted paraphrase pass (second, independent signal) |
| ✅ | Optional semantic layer: local ONNX MiniLM embeddings (one-time ~90 MB download, then offline) |
| ✅ | Evidence viewer: your passage side-by-side with the source passage |
| ✅ | Internal duplication detector (repeats inside your own document) |
| ✅ | References section auto-excluded from scoring |
| ⌛ | Cross-lingual matching (translated plagiarism via multilingual embeddings) |
| ✅ | Self-plagiarism mode (compare against your own earlier documents via local archive) |

## AI-likelihood (beta)

| Status | Feature |
|---|---|
| ✅ | Burstiness (sentence-length variance) |
| ✅ | Lexical diversity (type-token ratio) |
| ✅ | Formulaic-phrase density (curated AI-lexicon list) |
| ✅ | Discourse-marker density (transition-word usage) |
| ✅ | Sentence-opener repetition |
| ✅ | Top AI-suspicious sentences listed in the Summary (light heatmap) |
| ✅ | Reported as 0–100 heuristic **signal** with sub-metric breakdown |
| ✅ | Stylometry version stamped in results (currently `stylometry-1.5`) |
| ⌛ | Pluggable ONNX classifier model (bundle small, updateable) |
| ⌛ | Full per-sentence heatmap view |

## Scoring & reporting

| Status | Feature |
|---|---|
| ✅ | Similarity %, Originality %, Paraphrase Risk %, AI-Likelihood %, composite Integrity % |
| ✅ | Deduplicated scoring: each token counted once, at its strongest class (no double counting) |
| ✅ | Per-source contribution table |
| ✅ | Full PDF report with matched passages and links |
| ✅ | Findings export: styled HTML list of every flag + Fix & Cite suggestion |
| ✅ | Highlighted copy export: full document, color-coded flags + numbered source footnotes (HTML, print-to-PDF) |
| ✅ | Word comment export: flags pushed into a .docx copy as inline comments |
| ✅ | Internal duplication reported separately (not counted as external similarity) |
| ✅ | Certificate PDF: report ID, SHA-256 hash, timestamp, score table, QR code |
| ✅ | "Unregistered" watermark note when no license key is active |
| ✅ | Report ID verifier against local scan history (Certificate tab) |
| ⌛ | Draft revision tracker (scan Draft I→III, score-over-time graph) |
| ⌛ | Online verification page (hosted lookup of report ID — QR works offline meanwhile) |
| 💡 | Supervisor mode: one-page summary for committees |
| 💡 | Integrity statement generator for thesis appendix |

## Fix & Cite (attribution-first remediation)

| Status | Feature |
|---|---|
| ✅ | Per-flag suggestion: quote correctly / add citation / rewrite with attribution |
| ✅ | Ready-to-copy reference line (title + URL + accessed date) |
| ✅ | Open-source link per flag |
| ✅ | Citation gap finder: uncited claim sentences (Cite Assist tab) |
| ✅ | One-click candidate sources per gap (OpenAlex / Crossref) |
| ✅ | Reference validator: bibliography → Crossref/OpenAlex (DOI check, retraction status) |
| ⌛ | Auto-formatted citations (APA / MLA / IEEE via CSL) |

## App platform

| Status | Feature |
|---|---|
| ✅ | Dark modern UI (custom QSS, gradient accents, custom score rings) |
| ✅ | Background scanning thread with live progress and Cancel button |
| ✅ | Settings dialog: keys, thresholds, query caps |
| ✅ | SQLite history of past scans |
| ✅ | Offline friend-license keys (`tools/license_generator.py` GUI + CLI) |
| ✅ | PyInstaller + Inno Setup packaging scripts → `Setup.exe` |
| ⌛ | Auto-update check (simple version ping) |
| ⌛ | Multi-language UI (Arabic/RTL first) |
| 💡 | Moodle/Microsoft Word add-in for institutions |

---
*© 2026 Attribo. All rights reserved.*
