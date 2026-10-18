# Changelog — Attribo

> © 2026 Attribo. All rights reserved.
> Format: Keep a Changelog style. Versioning: semver.

## [0.11.0] — 2026-10-18

### Changed — Rebrand: Attribo

- Renamed from "Archinsights PlagCheck" to simply **Attribo** — window, tray, reports,
  certificates, exports, installer and docs all carry the new name.
- Existing data (settings, API keys, scan history, semantic model, license) is moved
  automatically to `%APPDATA%\Attribo` on first launch of the new version.
- License keys issued earlier remain valid (format unchanged: `AI-<SLUG>-<date>-<sig>`).

### Added

- **Offline license generator** (`tools/license_generator.py`): dark-themed GUI + CLI to
  issue single or batch friend keys and verify any key offline; `AttriboKeygen.exe` build
  for running it without Python.

---

## [0.10.2] — 2026-10-18

### Changed — UI

- **Settings dialog redesigned into a compact tabbed layout** — Search APIs / Scanning /
  AI & Semantic / License. The dialog is now ~600×435 px instead of overflowing small
  laptop screens, and its maximum size is clamped to the available screen area.

---

## [0.10.1] — 2026-10-18

### Added — more free search providers, no card required

- **Serper.dev, Tavily, Exa connectors** (all with card-free free tiers) plus
  **SearXNG** support for a self-hosted, unlimited, fully private search instance
- **Cross-check mode** (default on): every query goes to *all* configured providers;
  results are merged and de-duplicated by URL, then every hit is fetched and verified
  against the actual page text — provider-independent evidence
- **"Test search APIs" button** in Settings: live probe of each configured provider
  with per-provider OK/FAIL status (uses one query per provider)

### Changed

- Provider order/fallback logic: when cross-check is off, the first provider that
  returns results wins (Google → Brave → Serper → Tavily → Exa → SearXNG)
- `docs/API_KEYS.md` rewritten: no-card comparison table, signup steps, quota math

---

## [0.10.0] — 2026-10-18

### Added — trust, automation & AI update

- **Evidence viewer 2.0**: the Matches tab now shows *your passage* side-by-side with the actual
  *source passage* (context snippet captured for every match)
- **Highlighted copy export** (HTML, print-to-PDF): the full document with color-coded flags
  (red = verbatim, orange = near-match, blue = semantic, cyan = paraphrase, violet = internal
  duplicate) and numbered source footnotes
- **Word review copy export**: a `.docx` copy of your document with every flag inserted as an
  inline Word comment (comment ranges + `comments.xml` written at the OOXML level)
- **Cite Assist tab**: finds sentences that make claims without a citation nearby; one-click
  search of OpenAlex/Crossref for candidate sources; ready-to-copy reference lines
- **References tab**: parses your bibliography and validates it on demand against
  Crossref/OpenAlex — existence, DOI correctness, DOI mismatch, retraction status (OpenAlex)
- **Batch mode**: scan an entire folder (button or drag a folder onto the window); writes
  per-file findings HTML plus a master `index.html` overview
- **Watch folder automation**: auto-scans new documents dropped into a chosen folder, with
  system-tray notifications and automatic findings export
- **Semantic matching layer (optional)**: local ONNX sentence embeddings (all-MiniLM-L6-v2,
  ~90 MB one-time download from Hugging Face, then fully offline). Catches synonym-level
  paraphrase with cosine ≥ 0.70 — weight 0.70
- **TF-IDF rarity-weighted paraphrase signal**: a second paraphrase detector using
  IDF-weighted cosine similarity (cosine ≥ 0.32, ≥ 5 shared content words)
- **Internal duplication detector**: flags passages repeated within your own document
  (reported separately; not counted in external similarity)

### Changed

- AI-likelihood detector upgraded to **stylometry-1.5**: new discourse-marker density and
  sentence-opener repetition metrics, re-weighted formula; version stamped in reports
- Match classes and weights now: verbatim **1.00** > near **0.85** > semantic **0.70** >
  paraphrase **0.60** — still deduplicated per token, strongest class wins
- `requirements.txt` gains optional semantic-layer dependencies (onnxruntime, tokenizers, numpy)

---

## [0.9.1] — 2026-10-16

### Added — accuracy & workflow update

- **Near-match class** (edit-distance tolerant): copied passages with a few swapped/inserted/deleted
  words (light edits, typos) are now caught — weight 0.85
- **Local folder comparison ("archive")**: compare against a folder of previous documents
  (self-plagiarism / internal department archive); checkbox + folder picker in the scan panel
- **Cancel button** for long scans
- **Findings export (styled HTML)** from the Fix & Cite tab — opens in the browser, printable to PDF
- **Report ID verifier** (Certificate tab → Verify report ID) checks the ID against local scan history
- **AI-suspicious sentences** list (top formulaic passages) in the Summary
- "Exclude quoted blocks" checkbox surfaced directly in the scan panel
- Web search: automatic quoted → unquoted fallback when a quoted query returns no results
- Source diversity cap: maximum 2 results per domain per scan

### Changed — accuracy

- Matching now runs on a **single global token stream** of the document body — matches that span
  paragraph boundaries are found
- Similarity scoring is **deduplicated**: each token counted once, at its strongest class
  (verbatim 1.00 > near 0.85 > paraphrase 0.60) — no inflation when several sources mirror the
  same passage
- Paraphrase matching uses **light stemming**, improving recall without loosening thresholds
- Sources with very little text (< 25 tokens) are skipped to reduce junk matches

---

## [0.9.0] — 2026-10-16

### Added — initial MVP

- Dark modern UI (custom QSS theme, gradient accents, custom-painted score rings)
- Drag & drop intake with format detection (docx, pdf, txt, md, rtf, odt)
- Parsing + normalization pipeline (zero-width stripping, de-hyphenation, NFKC)
- Section detection: references excluded from scoring; quote-line handling toggle
- Query builder: most distinctive sentences, capped query count (default 12)
- Web engine: Google Custom Search JSON API + Brave Search API providers
- Academic engine: OpenAlex + Crossref connectors (no key required)
- Evidence cache (SQLite) with 30-day pruning
- Matching: winnowing k-gram verbatim runs (≥8 words) with character-accurate spans
- Paraphrase-risk heuristic (content-word overlap, conservative thresholds)
- AI-Likelihood stylometric signal (burstiness, lexical diversity, formulaic density, repetition)
- Scoring: Similarity / Originality / Paraphrase Risk / AI / composite Integrity
- Results UI: Summary rings, Matches table, Fix & Cite tab, Certificate tab, History tab
- Fix & Cite: attribution-first guidance + ready-to-copy reference lines + open-source links
- Report PDF (sources + passages) and Certificate PDF (report ID, SHA-256, timestamp, QR)
- Settings dialog (API keys, thresholds, license key) + local settings storage
- Offline friend licenses: HMAC key generation (`tools/genkey.py`) and verification
- Packaging: PyInstaller onedir recipe + Inno Setup script + build script
- Documentation set: README, ARCHITECTURE, FEATURES, SCORING, ACCURACY_AND_LIMITS,
  API_KEYS, PRIVACY, BUILD_WINDOWS, ROADMAP, COPYRIGHT
- Smoke test (offline): pipeline end-to-end + PDF generation + offscreen UI instantiation

### Known limitations

- AI detection is heuristic-only (no ML model bundled yet)
- No OCR for scanned PDFs
- No near-match (edit-distance) class yet
- English-optimized tokenization/language lists

---
*© 2026 Attribo. All rights reserved.*
