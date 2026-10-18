# Architecture — Attribo

> © 2026 Attribo. All rights reserved.

## Overview

Attribo is a **local-first Windows desktop application** (Python 3.10+, PySide6/Qt6).
All document processing happens on the user's machine. The network is used only for:

1. Sending short search phrases (a handful of words each) to search APIs.
2. Fetching public source pages / open-access academic metadata for evidence.
3. Optional license verification (offline keys work without network).

## Pipeline

```
 ┌────────────┐   ┌──────────────┐   ┌─────────────┐   ┌───────────────────┐
 │  Drop file │ → │ Parse &      │ → │ Segment:    │ → │ Query builder:    │
 │ (UI)       │   │ normalize    │   │ paragraphs, │   │ most distinctive │
 └────────────┘   │ (docx/pdf/…) │   │ sentences,  │   │ sentences         │
                  └──────────────┘   │ sections    │   └────────┬──────────┘
                                     └─────────────┘            │
                        ┌───────────────────────────────────────┴────────────┐
                        │                 ENGINES (network)                  │
                        │  Web engine (Google CSE / Brave)  ──┐              │
                        │  Academic engine (OpenAlex, Crossref)├─→  cache    │
                        └──────────────────────────────────────┼────────────┘
                                                               ▼
                  ┌────────────────────┐   ┌───────────────────────────────┐
                  │ MATCHING           │   │ AI-LIKELIHOOD (stylometry)     │
                  │ - verbatim runs    │   │ - burstiness, diversity,      │
                  │   (winnowing k-gram│   │   formulaic phrase density    │
                  │ - paraphrase       │   └───────────────┬───────────────┘
                  │   heuristic        │                   │
                  └─────────┬──────────┘                   │
                            ▼                              ▼
                  ┌────────────────────────────────────────────────────┐
                  │ SCORING: Similarity / Originality / Paraphrase /   │
                  │ AI-Likelihood / Integrity (0–100, weighted)        │
                  └────────────────────────┬───────────────────────────┘
                                           ▼
             ┌─────────────────┬──────────────────────┬──────────────────────┐
             │ Summary UI      │ Fix & Cite           │ PDF Report +         │
             │ (rings, sources)│ (per-flag guidance)  │ Certificate (QR,hash)│
             └─────────────────┴──────────────────────┴──────────────────────┘
```

## Modules

| Module | Responsibility |
|---|---|
| `attribo/main.py` | Bootstrap: QApplication, theme, DB init, main window |
| `…/theme.py` | Dark theme QSS + palette constants |
| `…/core/parser.py` | Extract text from docx, pdf, txt, md, rtf, odt (OCR: roadmap) |
| `…/core/normalizer.py` | Unicode NFKC, zero-width removal, de-hyphenation, whitespace |
| `…/core/segmenter.py` | Paragraph/sentence splitting, references-section detection, quote-line detection |
| `…/core/matching.py` | Tokenizer with offsets, winnowing k-gram verbatim runs, near-match alignment, stemmed paraphrase, TF-IDF index, internal-duplication detector |
| `…/core/semantic.py` | Optional local ONNX MiniLM embedding layer (one-time model download, offline after) |
| `…/core/citation.py` | Citation gap finder + candidate-source suggestions |
| `…/core/references.py` | Bibliography parsing + Crossref/OpenAlex validation (DOI, retraction) |
| `…/core/batch.py` | Folder batch scanning → per-file findings + master index |
| `…/core/ai_detect.py` | Stylometric AI-likelihood heuristic (stylometry-1.5) with sub-metrics |
| `…/core/scoring.py` | Weighted token scoring, per-source attribution, composite integrity |
| `…/core/pipeline.py` | Orchestrates the scan; progress callbacks; cancellation |
| `…/engines/web_engine.py` | Google CSE / Brave providers, page fetch + text extraction |
| `…/engines/academic.py` | OpenAlex + Crossref search (no key required) |
| `…/engines/archive.py` | Local folder archive (self-plagiarism / department prior work) |
| `…/engines/cache.py` | SQLite evidence cache (URL → title, text, fetched_at) |
| `…/report/pdf_builder.py` | Report PDF (platypus) + Certificate PDF (canvas, QR, hash) |
| `…/report/findings.py` | Styled findings HTML export |
| `…/report/highlight.py` | Highlighted-copy HTML export (color-coded + footnotes) |
| `…/report/word_export.py` | Word review copy: inline comments via OOXML `comments.xml` |
| `…/storage/settings.py` | JSON settings under `%APPDATA%\Attribo` |
| `…/storage/db.py` | SQLite scan history (scans, sources, matches) |
| `…/ui/main_window.py` | Main window: drop zone, options, progress, 7 result tabs, batch + watch controls |
| `…/ui/drop_zone.py` | Drag & drop card widget |
| `…/ui/gauges.py` | Custom-painted score rings |
| `…/ui/worker.py` | QThread workers running pipeline/batch off the UI thread |
| `…/ui/func_worker.py` | Generic background worker (model download, network validation) |
| `…/ui/settings_dialog.py` | API keys, limits, license key, semantic model controls |
| `…/licensing/keycheck.py` | Offline HMAC license keys (`AI-<name>-<expiry>-<sig>`) |

## Data flow & storage

- `%APPDATA%\Attribo\settings.json` — configuration
- `%APPDATA%\Attribo\attribo.db` — history + evidence cache (single SQLite file)
- Exported PDFs are written wherever the user chooses.

## Concurrency model

- UI thread: Qt only.
- One `ScanWorker` (QThread) per scan; emits `progress(int, str)`, `finished_ok(ScanResult)`, `failed(str)`.
- Cancellation: cooperative flag checked between queries.
- Network calls are synchronous inside the worker with timeouts (12 s) and size caps (≈400 KB/page).

## Scoring flow (summary — details in SCORING.md)

1. Content sections are tokenized (references section excluded).
2. Verbatim runs ≥ `min_match_words` (default 8) are recorded with exact character spans.
3. Paraphrase candidates = sentences with high content-word overlap against a source but no verbatim run.
4. `Similarity = Σ(tokens × weight) / content tokens`; weights: verbatim 1.0, paraphrase 0.6.
5. `Integrity = 100 − (0.50·Similarity + 0.30·AI + 0.20·Paraphrase)`.
6. Every number is traceable to listed evidence (source title + URL + matched passage).

## Failure handling

| Failure | Behavior |
|---|---|
| No API keys | Local mode: AI heuristics + paraphrase-only analysis; banner prompts keys |
| API rate limit / HTTP error | Warning recorded; scan continues with remaining sources |
| Page fetch fails | Source listed as "not fetched"; excluded from matching, noted in report |
| Scanned PDF (no text layer) | Warning issued ("OCR not in this build"); roadmap item |
| Corrupt document | Friendly error dialog; nothing partially written to history |

---
*© 2026 Attribo. All rights reserved.*
