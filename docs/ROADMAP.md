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

## v2.0 — Research integrity suite — SHIPPED (2026-10-18)

Everything below ships in the same **2.0.0** build, as pragmatic implementations with honest
simplifications noted inline. Detector evasion remains a non-goal (see bottom of file).

### Corpus & thesis intelligence

- ✅ **Corpus Vault** — opt-in local index of documents you have scanned (stored in `attribo.db`);
  every scan is then also compared against your own history (extra sources of kind `vault`).
  Vault tab: enable, list, remove selected, wipe. Nothing is ever uploaded.
- ✅ **Thesis mode** — tick it before a batch scan: per-chapter score table + aggregate means +
  cross-chapter verbatim overlap detection (≥ 8 words) written to `thesis_summary.html`.
  *Simplification:* chapters are files (one per chapter); a single `.docx` is not split by
  headings yet.
- ✅ **Prior-work positioning** — the abstract is extracted locally and its most distinctive
  sentences are searched on OpenAlex / Crossref; closest works (title / year / citations) are
  listed in the Prior work tab.

### Claim–citation verification

- ✅ **Citation support check** — citing sentence vs. the cited work's abstract (local embeddings
  when the semantic model is installed, term-overlap otherwise). Verdicts: supported / weak /
  no-cite / unavailable. Abstracts are fetched from OpenAlex by DOI (network; only the DOI
  leaves the machine).
- ✅ **Two-way citation graph** — offline parse of in-text citations ↔ bibliography: cited but
  missing, uncited entries, duplicate entries. Heuristic author/year matching — verify manually.
- ✅ **Quoted-material audit** — finds quotations ≥ 6 words, attribution proximity (±220 chars),
  and block-quote formatting needs (40+ words). Fix & Cite marks quotes *verified
  word-for-word* only when the flagged passage matches the captured source excerpt exactly.
- ✅ **Retraction warnings on matches** — after reference validation, retracted entries surface
  in the Summary tab as well as the References tab. *Simplification:* warnings attach to your
  bibliography, not to a specific match row.

### Fix & Cite 2.0

- ✅ **Natural rewrite suggestions** — deterministic attribution frames (quote / cite /
  paraphrase) that preserve meaning and terminology, with citation placeholders for you to fill.
- ✅ **One-click compliant rewrite** — writes a *copy* of the scanned `.docx` with every flag
  replaced by its compliant version; your original is never modified. *Limitation:* paragraph
  text only (not text boxes / tables / headers); the replaced span keeps its first run's
  formatting.
- ✅ **Fix checklist** — "Done" column in Fix & Cite with a live "fixed N of M" counter; ticked
  flags are skipped in the worklist export. *Note:* ticks are a workflow aid — they do not
  change scan scoring.

### Reports & trust

- ✅ **Revision diff report** — Draft I vs Draft II (same session): fixed / persisting / new
  findings + score deltas (similarity, paraphrase, AI, integrity), as HTML from the History tab.
- ✅ **Supervisor review packet** — one PDF: score summary, method & limits, findings table,
  evidence extracts, revision history, signature.
- ✅ **Offline tamper-evident certificates** — HMAC-SHA256 signature (`SIG-…`) over
  report ID | document hash | scores | timestamp, embedded in the certificate PDF and QR
  payload; "Verify report ID" recomputes it against the stored scan row and fails loudly on
  mismatch. *Scope:* tamper-evidence against edits of the stored data — an app-local secret,
  not third-party cryptographic attestation (hosted page stays optional, v2.x).
- ✅ **Redacted shareable report** — HTML findings + sources without a single word of your draft.

### AI signals with explanations

- ✅ **Multi-signal view with agreement** — stylometry sub-signals (burstiness, formulaic
  phrases, discourse markers, opener repetition, TTR, trigram repetition) each scored and
  explained; "N of 6 sub-signals raised" shown in the Summary and the explain dialog.
- ✅ **Per-metric reasoning** — "Explain AI signals" lists the worst four signals with the
  values that raised them, plus the flagged formulaic passages.
- ✅ **Human-edit delta** — the revision diff reports the AI-likelihood change between drafts.
  *Simplification:* the separate bundled ONNX classifier stays a v1.0 item; this build's
  ensemble is the stylometry sub-signal set (+ optional semantic layer for paraphrase).

### Platform & automation

- ✅ **CLI mode** — `python -m attribo.cli scan <file> [--json] [--out DIR] [--strictness LEVEL]
  [--license KEY] [--no-web]`.
- ✅ **Shell integration** — the installer writes per-user Explorer entries for `.docx` / `.pdf` /
  `.txt`: right-click → "Scan with Attribo" (`Attribo.exe --scan "%1"`); removed on uninstall.
- ✅ **Portable mode** — an empty `Attribo-portable.marker` beside `Attribo.exe` (or
  `ATTRIBO_PORTABLE=1`) keeps settings, history, models and vault in `AttriboData\` next to the
  app. Privacy tab: one-click zip backup / restore of settings + history.
- ✅ **Model manager** (partial) — status, download and delete of the optional semantic model.
  Checksum pinning and offline import from another machine remain on the v2.x list.
- ✅ **Privacy dashboard** — new Privacy tab: data folder + mode, an honest "what leaves this
  machine" list, one-click wipe of history / vault / evidence cache, backup & restore.
- ✅ **Light theme** — Settings → Scanning → Appearance (dark / light), applied instantly.

## v2.x — Institution option (only if desired)

- Department dashboard (batch scans, cohort reports)
- Verification page for certificate IDs (hosted, optional — offline tamper-evidence ships in v2.0)
- Moodle add-in (the Word / LibreOffice sidebar moved to v3.0)
- Self-hosted mode for universities (data sovereignty pitch)

## v3.0 — Automation & the integrity copilot (planned)

Turn Attribo from a scanner you open into an **automation loop that runs by itself** — and add
the intelligence cloud checkers can't offer, because they only ever see one upload and never
your history. Ideas below are planned, in rough priority order; the promises (local-first,
honest signals, no evasion) carry over unchanged.

### 🔁 Document CI — scans that run themselves

- **Auto-rescan on save** — every save of a watched draft re-scans it quietly; Attribo only
  interrupts when something got *worse* (similarity up / new flags) via a tray notification.
  *Cloud tools can't do this: their model is upload → wait → download.*
- **Regression gate for scripting / CI** — `attribo scan --fail-over 15 --json`: exit codes so
  a scheduler, git hook or build pipeline can fail on a regression. *No checker offers
  CI-grade document gating.*
- **Scheduled thesis watch** — weekly unattended scans with a digest: what changed, what
  regressed, what is new.
- **Multi-draft lifecycle tracking** — every scan is a snapshot; each flag gets a lifecycle
  (new → persisting → fixed → regressed) drawn as a timeline. *The history is yours and stays
  local — the opposite of an opaque cloud database.*

### 🕰️ Authorship timeline (evidence vault)

- Snapshots are hashed + signed locally (v2.0 signatures already exist), then optionally
  **anchored with OpenTimestamps** — a free, trustless proof-of-existence on the Bitcoin
  blockchain (only a hash leaves the machine).
- **Authorship evidence pack** export: snapshot chain + timestamps + signatures proving when
  each part of your work existed. *New in this space — provenance for your own writing.*
- Anchors verify with public OTS tools, even without Attribo installed.

### 📦 One-click submission pack

- A single ZIP for submission day: integrity statement + certificate PDF + redacted report +
  supervisor packet + compliant-rewrite copy + coverage report.
- **Integrity statement generator** — ready appendix text ("This thesis was screened with
  Attribo v… on …, report ID …; the certificate is attached"). *Checkers give you a
  percentage; none generate the disclosure paperwork for you.*

### 🎓 Viva / defence preparation

- For each flag: **the question a committee member might ask**, the source context, and
  bullet-point answers built from your own surrounding text.
- "Weakest links" drill — the five findings most likely to be challenged, each with a fix or a
  justification. *Nothing in the checker market prepares you to defend the work.*

### 🗺️ Claim–coverage map 2.0

- Whole-document **support graph** — which paragraphs are backed by which cited works
  (extends v2.0's citation support check from cited sentences to every claim).
- Coverage heatmap: supported / weak / unsupported / uncited — printable for supervisor
  meetings.
- **Reference gap analysis** — the citation network around your bibliography (OpenAlex) flags
  seminal works you cite around but never cite directly.

### 🧾 Coverage transparency report

- Per scan: what was actually compared (providers, queries, fetched sources), what could not
  be checked (paywalled / offline / not found), and a coverage estimate.
- An inspectable alternative to "98% similar" black boxes — you can audit every number.

### ✍️ Assisted-writing log (disclosure, never evasion)

- Optional ledger of passages revised with Fix & Cite (quote / cite / paraphrase) and when.
- Exportable if an institution asks how this tool was used — **voluntary disclosure**.
- Detector-evasion stays an explicit non-goal forever (see bottom of this file).

### 🔌 Integrations

- **Word / LibreOffice sidebar** — scan the open document from a pane (local HTTP on
  127.0.0.1; still fully offline), push fixes back as comments.
- Supervisor digests by email / network folder (optional, self-hosted).
- CLI grows subcommands: `attribo vault`, `attribo diff`, `attribo packet`, `attribo verify`.

### 🧠 Honest-AI upgrades

- Bundled small classifier next to stylometry — ensemble with agreement display (same UX
  philosophy as v2.0's sub-signals); runs offline on CPU.
- Per-sentence "why" panels for every signal, not only the top four.
- Cross-lingual plagiarism (multilingual embeddings) — carried over from v1.5.

### 🛡️ Platform polish

- Code-signed installer (removes the SmartScreen warning) once a certificate is affordable.
- Privacy/consent recap before first network use; per-feature kill-switches already exist.
- Mac / Linux builds (PySide6 is cross-platform; packaging differs).

## Idea bank (uncommitted)

- ~~Integrity statement generator~~ — promoted to v3.0 (submission pack)
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
