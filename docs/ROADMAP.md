# Roadmap — Attribo

> © 2026 Ayush Gupta (Attribo). All rights reserved.

## v2.0.0 — Shipped (2026-10-18)

- **Scan strictness profiles** — Balanced / **Strict (default)** / Maximum: one dial that
  shortens the minimum match, adds queries, widens provider fetch limits, lowers the semantic
  threshold and raises paraphrase sensitivity (stricter checking out of the box)
- **Colour-coded highlighting for dark mode** — verbatim red, near-match orange, semantic blue,
  paraphrase yellow, internal duplicate violet; applied to the Matches and Fix & Cite tables,
  the detail viewer, the highlighted copy export and its print stylesheet
- **Fix & Cite worklist (`.docx`)** — numbered flags, each with source, excerpt, suggested fix
  and a read-and-replace table (ORIGINAL ↔ REPLACEMENT)
- **Natural attribution frames** — deterministic reporting templates per flag
- **GitHub auto-update** — update detector + optional download & install (GitHub Releases
  first, `version.json` fallback; silent when offline)
- Author: **Ayush Gupta**

## v0.10 – v0.11 — Trust & automation update (released)

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
- v0.11: rebrand to **Attribo** (package, data folder, installer) + offline license generator
  (`tools/license_generator.py`, `AttriboKeygen.exe`)

## v1.0 — Trust release (next)

- Benchmarks run on PAN corpora; results published in `docs/ACCURACY_AND_LIMITS.md`
- ONNX AI-classifier bundled (offscreen, small) alongside stylometry
- CORE API connector (OA full texts)
- OCR for scanned PDFs (Tesseract bundled optional install)
- Report page in-app (HTML preview) matching the PDF design

## v1.2 — Author workflow

- Draft revision tracker (scan I→III, score-over-time chart)
- Citation auto-formatting (APA / MLA / IEEE / Harvard) — carried through into every export
- ~~Fix & Cite worklist (`.docx`)~~ — shipped early in v2.0.0
- Supervisor one-pager report mode

## v1.5 — Coverage & languages

- Cross-lingual matching (translated plagiarism; multilingual embeddings)
- Arabic-first UI localization (RTL) + Arabic tokenizer tuning
- Full per-sentence heatmap view

## v2.0 — Research integrity suite

### Corpus & thesis intelligence

- **Corpus Vault**: persistent local index (opt-in) — every scanned document accumulates; instant
  self-plagiarism checks across your own history; management UI to view/remove indexed documents
- **Thesis mode**: chapter split, per-chapter score rings, cross-chapter duplicate suppression,
  one aggregate report
- **Prior-work positioning**: closest existing works to your abstract (OpenAlex / Crossref + local
  embeddings) — helps you position your contribution honestly

### Claim–citation verification

- **Citation support check**: does the cited source actually support the sentence?
  (sentence vs. abstract comparison via local embeddings)
- **Two-way citation graph**: in-text citations ↔ bibliography — missing references, uncited
  references, duplicate entries
- **Quoted-material audit**: quotes without attribution, block-quote formatting needed, quote
  wording mismatches
- Retraction warnings surfaced on matches, not only in the References tab

### Fix & Cite 2.0

- **Natural rewrite suggestions**: rewrites that read like natural human prose — meaning,
  terminology and citations preserved; verified against the captured source so quotes stay exact
- **One-click compliant rewrite**: quote / cite / paraphrase version inserted into a `.docx` copy
  (your original is never modified)
- **Fix checklist**: tick off resolved flags; remaining issues feed the rescan diff

### Reports & trust

- **Revision diff report**: Draft I vs II — fixed / new / persisting findings + score deltas
- **Supervisor review packet**: one-pager + evidence + revision history compiled into one PDF
- **Offline tamper-evident certificates**: signed payload + QR; in-app verify dialog
  (a hosted verification page stays optional)
- **Redacted shareable report**: findings + sources without your draft text

### AI signals with explanations

- Multi-signal ensemble (stylometry + classifier + burstiness): agreement shown;
  disagreement displayed as uncertainty
- Per-sentence reasoning: which metric fired and why
- Human-edit delta: did your revisions reduce machine-like markers? (feeds the revision tracker)

### Platform & automation

- CLI mode: `attribo scan file.docx --json` for scripting and batch automation
- Shell integration: right-click any file → "Scan with Attribo"
- Portable mode (run from USB, data beside the exe) + backup/restore of history and settings
- Model manager: optional downloads with checksums; import models offline from a friend's machine
- Privacy dashboard (what is stored where, per-item wipe, export-all) + light theme

## v2.x — Institution option (only if desired)

- Department dashboard (batch scans, cohort reports)
- Verification page for certificate IDs (hosted, optional — offline tamper-evidence ships in v2.0)
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
- "Detector evasion" modes or human-likeness guarantees — rewrite assistance exists to improve
  clarity and attribution; AI detection is probabilistic and never presented as a verdict
- Storing, uploading, or analyzing user documents on any server

---
*© 2026 Attribo. All rights reserved.*
