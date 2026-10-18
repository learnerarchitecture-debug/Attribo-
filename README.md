<div align="center">

# 🛡️ Attribo

**Local-first plagiarism & AI-likelihood screening for theses — with a workflow that helps you fix what it finds.**

[![Version](https://img.shields.io/badge/version-2.0.0-5B8CFF?style=for-the-badge)](docs/CHANGELOG.md)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-0078D6?style=for-the-badge)](packaging/BUILD_WINDOWS.md)
[![Privacy](https://img.shields.io/badge/privacy-offline--first-34D399?style=for-the-badge)](docs/PRIVACY.md)
[![Python](https://img.shields.io/badge/python-3.12-FFD43B?style=for-the-badge&logo=python&logoColor=black)](requirements.txt)
[![License](https://img.shields.io/badge/license-proprietary-F87171?style=for-the-badge)](LICENSE)

`📄 your document never leaves your PC` · `🧾 explainable signals` · `🛠 fixes, not just scores`

</div>

---

## 💡 Why Attribo

A checker that gives you **"31% similar"** and nothing else helps nobody. Attribo shows you the exact passage, the actual source text beside it, *why* a signal fired — and then hands you the compliant fix.

|  | ☁️ Typical cloud checkers | 🛡️ **Attribo** |
|---|---|---|
| Your document | uploaded to a server | **never leaves your PC** |
| Result | one opaque percentage | **per-passage evidence + source excerpts** |
| AI score | black-box number | **per-metric breakdown + explanations** |
| Help to fix it | none | **quote / cite / rewrite worklist + compliant `.docx` copy** |
| Your history | their database | **yours: corpus vault, diffs, signed certificates** |
| Offline use | ✖ | **✅ full local mode; web checks optional** |
| Price | $100+/year | **free for you and your friends (offline keys)** |

---

## ✨ Feature tour

### 🔍 Checking engines

| | |
|---|---|
| 🌐 **Web check** | Google Custom Search, Brave, Serper.dev, Tavily, Exa — all card-free tiers; **cross-check mode** queries every provider and merges results |
| 🏛️ **Academic check** | OpenAlex + Crossref (open access, no key) |
| ✅ **Evidence verification** | every hit is fetched and matched against the *real page text* — provider-independent proof |
| 🗂️ **Local archive** | compare against a folder of your previous documents (self-plagiarism) |
| 🔐 **Corpus Vault** | opt-in persistent index of **your** scanned documents — every scan also self-checks against your own history |
| 🎚️ **Strictness profiles** | Balanced / **Strict (default)** / Maximum — one dial scales match length, queries, fetch limits, semantic and paraphrase sensitivity |
| 🧠 **Query builder** | picks your most distinctive sentences; quoted search with automatic fallback |
| ⚡ **Evidence cache** | fetched pages cached in SQLite — repeat scans are faster and reproducible |

### 🧠 Matching & analysis

| | |
|---|---|
| 🔴 **Verbatim detection** | winnowing k-gram runs (6–8 words minimum, by strictness) |
| 🟠 **Near-match detection** | edit-tolerant alignment — a few swapped words still count |
| 🔵 **Semantic paraphrase** | optional local ONNX MiniLM embeddings (~90 MB one-time download, then fully offline) |
| 🟡 **Paraphrase heuristics** | stem-overlap + TF-IDF rarity-weighted cosine (two independent signals) |
| 🧩 **Global token-stream matching** | catches matches across paragraph boundaries |
| 🎯 **Character-accurate spans** | colour-coded highlighting down to the character |
| 👀 **Evidence viewer** | your passage side-by-side with the real source passage |
| ♻️ **Internal duplication** | repeats inside your own document, reported separately |
| 🚫 **References excluded** | bibliography automatically kept out of scoring |

### 🤖 AI-likelihood (beta) — explained, never a verdict

| | |
|---|---|
| 📊 **Six sub-signals** | burstiness · lexical diversity (TTR) · formulaic-phrase density · discourse markers · sentence-opener repetition · trigram repetition |
| 🤝 **Agreement line** | "N of 6 sub-signals raised" — disagreement is shown as uncertainty |
| 🗣️ **Explain AI signals** | per-metric dialog: what raised the score and why, with the flagged passages |
| 🏷️ **Versioned** | stylometry engine version stamped in every report (`stylometry-1.5`) |

### 📚 Citation & integrity suite

| | |
|---|---|
| 🕳️ **Citation gap finder** | claim sentences with no citation nearby (Cite Assist tab) |
| 🔎 **Candidate sources** | one-click OpenAlex / Crossref search per gap + ready-to-copy reference line |
| 🔁 **Citation cross-check** (offline) | cited-but-missing · uncited entries · duplicate references |
| 💬 **Quoted-material audit** (offline) | quotes without nearby attribution · block-quote formatting needs |
| 🧪 **Citation support check** | citing sentence vs. the cited work's abstract (embeddings or term overlap) |
| ✅ **Reference validator** | bibliography → Crossref/OpenAlex: existence, DOI correctness, **retraction status** |
| ⚠️ **Retraction warnings** | surfaced in the Summary tab, not buried in a table |

### 🛠️ Fix & Cite — remediation, not just detection

| | |
|---|---|
| 💡 **Per-flag suggestion** | quote correctly · add the citation · rewrite with attribution |
| ✍️ **Natural attribution frames** | deterministic templates that read like human writing ("According to …, …") |
| ✅ **Verified quotes** | "word-for-word" marker only when the passage is confirmed against the captured source excerpt |
| 📋 **Worklist export (.docx)** | numbered flags with read-and-replace rows: ORIGINAL → REPLACEMENT with citation placeholder |
| 🖱️ **Copy fix** | fix + replacement + frames to the clipboard in one click |
| ☑️ **Fix checklist** | "Done" column with a live “fixed N of M” counter — ticked flags skip the worklist export |
| 🪄 **One-click compliant rewrite** | exports a **copy** of your `.docx` with every flag replaced by its quoted/cited version — your original is never modified |

### 📊 Reports & trust

| | |
|---|---|
| 📄 **Full PDF report** | source-by-source breakdown with matched passages |
| 🖍️ **Highlighted copy (HTML)** | full document with colour-coded flags + numbered source footnotes (print-to-PDF ready) |
| 💬 **Word review copy** | a `.docx` copy with every flag inserted as an inline Word comment |
| 🏅 **Certificate PDF** | report ID · SHA-256 · timestamp · score table · QR code · **HMAC tamper-evident signature** |
| 🔏 **Signature verifier** | "Verify report ID" recomputes the signature against the stored scan row |
| 🔀 **Revision diff report** | Draft I vs II: fixed / persisting / new findings + score deltas |
| 👔 **Supervisor review packet** | one PDF: summary, method & limits, evidence, revision history, signature |
| 🕶️ **Redacted shareable report** | findings + sources **without a word of your draft** — safe to share early |

### ⚙️ Automation & platform

| | |
|---|---|
| 📦 **Batch mode** | scan a whole folder → per-file findings + master `index.html` |
| 🎓 **Thesis mode** | per-chapter score table + cross-chapter overlap detection in one summary |
| 👁️ **Watch folder** | auto-scans new documents with system-tray notifications |
| 🧭 **Prior-work positioning** | closest published works to your abstract (OpenAlex / Crossref) |
| ⌨️ **CLI** | `python -m attribo.cli scan file.docx --json` — scripting & batch automation |
| 🖱️ **Explorer integration** | right-click `.docx` / `.pdf` / `.txt` → **"Scan with Attribo"** |
| 🔌 **Portable mode** | marker file beside the exe → all data in `AttriboData\` (USB-stick friendly) |
| 💾 **Backup & restore** | one-click zip of settings + history; per-item wipe of history / vault / cache |
| 🎨 **Dark + light theme** | Settings → Appearance |
| 🔄 **Updater** | GitHub update detection with in-app banner (activates with published releases) |
| 🔑 **Offline license keys** | `AI-<slug>-<date>-<sig>` — issued from `tools/license_generator.py`, verified offline |

---

## 🚀 Quickstart

> [!NOTE]
> **Install:** run `Attribo_Setup.exe` → Start Menu + desktop shortcuts + right-click integration.
> Unsigned build: SmartScreen will warn once → *More info* → *Run anyway*.

**From source** (Windows, Python 3.10+; 3.12 recommended):

```powershell
cd <this folder>
python -m venv C:\apcvenv
C:\apcvenv\Scripts\python -m pip install -r requirements.txt
run.cmd            # or: C:\apcvenv\Scripts\python run.py
```

**First launch**

1. ⚙️ Gear icon → paste your free API keys (see [docs/API_KEYS.md](docs/API_KEYS.md)) — or skip and run in **local mode** (paraphrase + AI signals + archive/vault, no web search).
2. 🧠 Optional: Settings → AI & Semantic → *Download semantic model (~90 MB)* once — synonym-level paraphrase detection runs offline afterwards.
3. 📄 Drag your document onto the window and hit **Start Scan**.

---

## 🎓 A typical thesis workflow

```text
1. Scan draft        → Summary (scores) → Matches (your text vs. source text)
2. Work the list     → Fix & Cite → tick "Done" as you fix each flag
3. Re-scan           → History → diff report: fixed / persisting / new + deltas
4. Share             → Supervisor packet (PDF) or redacted report (no draft text)
5. Keep the receipt  → Certificate tab → signed certificate PDF
6. Stay honest       → Corpus Vault keeps self-plagiarism visible across chapters/drafts
```

---

## 🚫 What Attribo does **not** claim

```diff
- ❌ No tool detects 100% of plagiarism — Turnitin/iThenticate included.
- ❌ Paywalled journal content cannot be indexed legally — coverage = web + open access.
- ❌ AI detection is probabilistic; false positives exist — Attribo reports a signal, never a verdict.
- ❌ No detector-evasion, "humanizer" guarantees or hidden AI assistance — ever, by design.
```

> [!IMPORTANT]
> Read [docs/ACCURACY_AND_LIMITS.md](docs/ACCURACY_AND_LIMITS.md) before trusting any score.

---

## 🔒 Privacy — local-first, permanently

Your document **never leaves this PC**. Only short search phrases (a few words per query) go to search APIs you configured; source pages are fetched and cached locally as evidence. The vault, history, certificates and signatures are local files you can wipe any time (Settings → Privacy). See [docs/PRIVACY.md](docs/PRIVACY.md).

---

## 🗂️ Documentation index

| 🔖 File | Contents |
|---|---|
| [docs/FEATURES.md](docs/FEATURES.md) | Complete feature list with status |
| [docs/ROADMAP.md](docs/ROADMAP.md) | v2.0 shipped · **v3.0 automation suite** · idea bank |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Modules, pipeline, data flow |
| [docs/SCORING.md](docs/SCORING.md) | How the 0–100 scores are computed |
| [docs/ACCURACY_AND_LIMITS.md](docs/ACCURACY_AND_LIMITS.md) | Honest accuracy statement |
| [docs/API_KEYS.md](docs/API_KEYS.md) | Free API keys setup (no card needed) |
| [docs/PRIVACY.md](docs/PRIVACY.md) | Local-first data handling |
| [docs/BUILD_WINDOWS.md](docs/BUILD_WINDOWS.md) | Packaging to `Attribo_Setup.exe` |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | Version history |
| [docs/COPYRIGHT.md](docs/COPYRIGHT.md) | Ownership + third-party licenses |

<details>
<summary><b>📁 Project structure</b> (click to expand)</summary>

```text
Attribo/
├─ run.py                     # entry point
├─ run.cmd                    # dev launcher (uses C:\apcvenv when present)
├─ requirements.txt
├─ version.json               # update manifest read by the in-app updater
├─ attribo/                   # application package
│  ├─ main.py                 # bootstrap (--scan shell integration, themes)
│  ├─ cli.py                  # headless scans: python -m attribo.cli scan file.docx --json
│  ├─ theme.py                # dark + light themes (QSS)
│  ├─ core/                   # parsing, matching, scoring, AI heuristics, semantic (optional),
│  │                          #   strictness, vault, citation graph, diff check, thesis mode,
│  │                          #   signing, Fix & Cite text, updater, pipeline
│  ├─ engines/                # web search + academic connectors + cache + local archive
│  ├─ report/                 # PDF report/certificate, highlight + Word exports, worklist,
│  │                          #   fixed-copy, supervisor packet, redacted & diff reports
│  ├─ storage/                # settings (portable-aware) + SQLite history/vault
│  ├─ ui/                     # main window, drop zone, gauges, workers, settings dialog
│  └─ licensing/              # offline friend-license keys
├─ tools/                     # license generator GUI + CLI keygen
├─ packaging/                 # PyInstaller + Inno Setup scripts, app icon
├─ tests/smoke_test.py        # offline sanity suite (30 checks)
└─ docs/                      # all documentation
```

</details>

---

<div align="center">

**© 2026 Ayush Gupta (Attribo). All rights reserved.** · See [LICENSE](LICENSE)

*Advisory pre-submission screening — not a substitute for institutional systems, and never proof of misconduct.*

</div>
