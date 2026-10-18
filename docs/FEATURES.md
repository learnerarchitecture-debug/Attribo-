# Features — Attribo

> © 2026 Ayush Gupta (Attribo). All rights reserved.

Legend: ✅ implemented (through v2.0) · ⌛ planned · 💡 idea bank

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
| ✅ | **Scan strictness profiles**: Balanced / **Strict (default)** / Maximum — scales match length, query count, provider fetch limits, semantic threshold and paraphrase sensitivity together |
| ✅ | Quoted search with automatic unquoted fallback (better recall) |
| ✅ | Source diversity cap: 2–4 results per domain depending on strictness |
| ✅ | Evidence cache in SQLite (repeat scans are faster and stay reproducible) |
| ⌛ | CORE API connector (millions of OA full texts) |
| ⌛ | Semantic Scholar / arXiv / PubMed connectors |
| ⌛ | Optional "premium scan" toggle via a licensed commercial API (BYO key) |
| ✅ | Internal archive scan: compare against a folder of prior submissions (self-plagiarism) |

## Matching analysis

| Status | Feature |
|---|---|
| ✅ | Verbatim detection: winnowing k-gram runs (6–8 words minimum, by strictness) |
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
| ✅ | **Corpus Vault**: persistent opt-in index of your scanned documents — every scan is also compared against your own history (Vault tab: list / remove / wipe) |

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
| ✅ | Sub-signal **agreement line** ("N of 6 sub-signals raised") + "Explain AI signals" dialog with per-metric reasoning |
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
| ✅ | **Colour-coded match highlighting, dark-mode friendly**: verbatim red · near-match orange · semantic blue · paraphrase yellow · internal duplicate violet (tables, detail view, exports) |
| ✅ | Word comment export: flags pushed into a .docx copy as inline comments |
| ✅ | Internal duplication reported separately (not counted as external similarity) |
| ✅ | Certificate PDF: report ID, SHA-256 hash, timestamp, score table, QR code |
| ✅ | "Unregistered" watermark note when no license key is active |
| ✅ | Report ID verifier + **signature re-check** against the stored scan row (Certificate tab) |
| ✅ | **Tamper-evident signature** (HMAC-SHA256, `SIG-…`) in the certificate PDF, QR payload and verifier |
| ✅ | **Revision diff report** (HTML): Draft I vs II — fixed / persisting / new findings + score deltas |
| ✅ | **Supervisor review packet** (PDF): score summary, method & limits, findings, evidence extracts, revision history, signature |
| ✅ | **Redacted shareable report** (HTML): findings + sources without your draft text |
| ⌛ | Score-over-time graph (scan Draft I→III; the pairwise diff report ships meanwhile) |
| ⌛ | Online verification page (hosted lookup of report ID — QR works offline meanwhile) |
| 💡 | Integrity statement generator for thesis appendix |

## Fix & Cite (attribution-first remediation)

| Status | Feature |
|---|---|
| ✅ | Per-flag suggestion: quote correctly / add citation / rewrite with attribution |
| ✅ | **Fix & Cite worklist export (.docx)**: numbered flags with type badge, source, excerpt, suggested fix + read-and-replace table (ORIGINAL → REPLACEMENT with citation placeholder) |
| ✅ | **Natural attribution frames** per flag: deterministic reporting templates to adapt ("According to …, …") |
| ✅ | **Copy fix for selected flag**: fix + replacement + frames to the clipboard in one click |
| ✅ | **Verified quotes**: "word-for-word" marker only when the passage is confirmed against the captured source excerpt |
| ✅ | **One-click compliant rewrite**: `.docx` copy with every flag replaced by its compliant version (original never modified; paragraph text only) |
| ✅ | **Fix checklist**: "Done" column with live "fixed N of M" counter; ticked flags are skipped in worklist exports |
| ✅ | Ready-to-copy reference line (title + URL + accessed date) |
| ✅ | Open-source link per flag |
| ✅ | Citation gap finder: uncited claim sentences (Cite Assist tab) |
| ✅ | **Citation cross-check** (offline): cited-but-missing / uncited / duplicate reference entries |
| ✅ | **Quoted-material audit** (offline): quotes ≥ 6 words without nearby attribution; block-quote formatting needs |
| ✅ | **Citation support check** (network): citing sentence vs. the cited work's abstract (embeddings or term overlap) |
| ✅ | One-click candidate sources per gap (OpenAlex / Crossref) |
| ✅ | Reference validator: bibliography → Crossref/OpenAlex (DOI check, retraction status) |
| ✅ | **Retraction warnings** surfaced in the Summary tab after validation |
| ⌛ | Auto-formatted citations (APA / MLA / IEEE via CSL) |

## App platform

| Status | Feature |
|---|---|
| ✅ | Dark modern UI (custom QSS, gradient accents, custom score rings) |
| ✅ | **Light theme** (Settings → Scanning → Appearance) |
| ✅ | Background scanning thread with live progress and Cancel button |
| ✅ | Settings dialog: keys, thresholds, query caps |
| ✅ | SQLite history of past scans |
| ✅ | **Privacy tab**: data location + mode, "what leaves this machine", zip backup/restore, per-item wipe (history / vault / cache) |
| ✅ | **Portable mode**: marker file beside the exe → all data in `AttriboData\` |
| ✅ | **CLI**: `python -m attribo.cli scan file.docx --json` |
| ✅ | **Explorer integration**: right-click `.docx` / `.pdf` / `.txt` → "Scan with Attribo" |
| ✅ | **Prior-work positioning** (Prior work tab: closest works to your abstract) |
| ✅ | Offline friend-license keys (`tools/license_generator.py` GUI + CLI) |
| ✅ | PyInstaller + Inno Setup packaging scripts → `Setup.exe` |
| ✅ | GitHub update check: startup detection, header banner, one-click download & install (Settings → Updates) |
| ⌛ | Multi-language UI (Arabic/RTL first) |
| 💡 | Moodle/Microsoft Word add-in for institutions |

---
*© 2026 Ayush Gupta (Attribo). All rights reserved.*
