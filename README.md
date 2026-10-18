# Attribo

A local-first plagiarism and AI-likelihood screening tool for research papers, theses, and dissertations.
Built for personal and small-circle use (you + your friends), designed to compete on **transparency, privacy, and report quality** — not on false promises.

> **© 2026 Attribo. All rights reserved.**

---

## What it does

| Output | Description |
|---|---|
| Similarity Report | Compares your document against web sources (via search APIs) and open-access academic repositories (OpenAlex, Crossref) |
| Paraphrase Risk | Heuristic detection of sentences that mirror source content without word-for-word matching — stem overlap, TF-IDF, plus an optional local semantic (embedding) layer (beta) |
| AI-Likelihood | Stylometric heuristic signal (burstiness, lexical diversity, formulaic-phrase density, discourse markers, opener repetition) — reported as a probability, never a verdict (beta) |
| Evidence viewer | Every flag side-by-side: your passage next to the actual source passage |
| Fix & Cite | For every flag: the exact passage, its source, and the legitimate fix — quote it, cite it, or rewrite with attribution |
| Cite Assist | Sentences that make claims without citations + one-click candidate sources (OpenAlex / Crossref) |
| References check | Bibliography validated against Crossref/OpenAlex: existence, DOI correctness, retraction status |
| Highlighted copy | Full document HTML with color-coded flags and numbered source footnotes (print-to-PDF ready) |
| Word review copy | A `.docx` copy of your document with every flag inserted as an inline Word comment |
| Batch & watch folder | Scan a whole folder; or watch a folder and auto-scan new documents with tray notifications |
| Internal duplication | Flags passages you repeat inside your own document (reported separately from similarity) |
| Certificate PDF | Hash-stamped, timestamped, QR-coded certificate with a 0–100 score table |
| Full Report PDF | Source-by-source breakdown with matched passages |

## What it does NOT claim

- **No tool detects 100% of plagiarism.** Turnitin/iThenticate included.
- Paywalled journal content cannot be indexed legally — coverage is *web + open access*.
- AI detection is probabilistic. False positives exist. This tool never labels a human as "AI" — it reports a confidence band.

Read [docs/ACCURACY_AND_LIMITS.md](docs/ACCURACY_AND_LIMITS.md) before trusting any score.

## Privacy — local-first

Your document **never leaves this PC**. Only short search phrases (a few words per query) are sent to search APIs. Source pages are fetched and cached locally for evidence. See [docs/PRIVACY.md](docs/PRIVACY.md).

## Quickstart

Requirements: Windows 10/11, Python 3.10+ (3.12 recommended).

`run.cmd` uses a virtual environment at `C:\apcvenv` when it exists (recommended —
keeps installs out of OneDrive and avoids Windows long-path issues), otherwise it
falls back to plain `python`.

```powershell
cd "Attribo-Attribo"
python -m venv C:\apcvenv
C:\apcvenv\Scripts\python -m pip install -r requirements.txt
run.cmd
```

On this PC that setup is already done — just double-click **run.cmd** or run it
from PowerShell to launch the app.

First launch: click the gear icon → paste your free API keys (see [docs/API_KEYS.md](docs/API_KEYS.md)). Without keys, the app still works in **local mode**: AI-likelihood + paraphrase analysis + formatting checks, no web search.

Optional: in Settings, enable **Semantic matching** and click "Download semantic model (~90 MB)" once — after that, synonym-level paraphrase detection runs fully offline on your CPU.

## Build a Windows installer

See [docs/BUILD_WINDOWS.md](docs/BUILD_WINDOWS.md) — PyInstaller (onedir) + Inno Setup, producing `Attribo_Setup.exe`.

## Project structure

```
Attribo-Attribo/
├─ run.py                    # entry point
├─ requirements.txt
├─ attribo/   # application package
│  ├─ main.py                # app bootstrap
│  ├─ theme.py               # dark theme (QSS)
│  ├─ core/                  # parser, normalizer, segmenter, matching, scoring, AI heuristics, semantic (optional), pipeline
│  ├─ engines/               # web search + academic connectors + cache + local archive
│  ├─ report/                # PDF report + certificate + highlight export + Word review copy
│  ├─ storage/               # settings + SQLite history
│  ├─ ui/                    # main window, drag&drop zone, gauges, worker thread
│  └─ licensing/             # offline friend-license keys
├─ tools/license_generator.py # keygen GUI + CLI (for you, the owner)
├─ tools/genkey.py           # tiny CLI keygen (scriptable)
├─ packaging/                # PyInstaller + Inno Setup scripts
├─ tests/smoke_test.py       # offline sanity test
└─ docs/                     # all documentation
```

## Documentation index

| File | Contents |
|---|---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Modules, pipeline, data flow |
| [docs/FEATURES.md](docs/FEATURES.md) | Feature list with MVP / planned status |
| [docs/SCORING.md](docs/SCORING.md) | How the 0–100 scores are computed |
| [docs/ACCURACY_AND_LIMITS.md](docs/ACCURACY_AND_LIMITS.md) | Honest accuracy statement |
| [docs/API_KEYS.md](docs/API_KEYS.md) | Free keys setup (Google, Brave, CORE) |
| [docs/PRIVACY.md](docs/PRIVACY.md) | Local-first data handling |
| [docs/BUILD_WINDOWS.md](docs/BUILD_WINDOWS.md) | Packaging to `Setup.exe` |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Phases from MVP to department tool |
| [docs/COPYRIGHT.md](docs/COPYRIGHT.md) | Ownership + third-party licenses |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | Version history |

## Disclaimer

This tool is an advisory pre-submission screening instrument. It is not a substitute for institutional systems (Turnitin/iThenticate) and its output must not be treated as proof of misconduct. Scores are signals with uncertainty; always review matched sources manually.

---
*© 2026 Attribo. All rights reserved. See [LICENSE](LICENSE).*
