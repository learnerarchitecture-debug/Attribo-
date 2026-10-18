# Privacy — Local-First Design

> © 2026 Attribo. All rights reserved.

## Core promise

**Your document never leaves this computer.**
No account. No cloud upload of text, files, or results. Ever.

## What goes over the network, exactly

| Data | Where | Why |
|---|---|---|
| Short search phrases (≈5–12 words, token-normalized) | Your configured search provider(s): Google CSE, Brave, Serper, Tavily, Exa — or your own SearXNG instance | To find candidate sources |
| HTTP GET for source pages | Public websites found by search | To fetch evidence text for local matching |
| One-time semantic model download (~90 MB) — **only if you enable the semantic layer** | huggingface.co (model file only — no text from your documents) | Local sentence-embedding model for paraphrase detection |
| License key (optional, offline by default) | Nowhere (keys verify locally via HMAC) | Licensing |

Nothing else. No telemetry, no analytics, no crash reporting in v0.10. If telemetry is ever
added, it will be opt-in and documented here first with an off switch.

## What is stored locally

| Data | Location | Retention |
|---|---|---|
| Settings + API keys | `%APPDATA%\Attribo\settings.json` | Until you delete them |
| Scan history (scores, flags) | `%APPDATA%\Attribo\attribo.db` | Until you clear history |
| Source evidence snapshots | same SQLite file | Pruned after 30 days by default |
| Semantic model files (only if downloaded) | `%APPDATA%\Attribo\models\minilm\` | Until you delete them |
| Watch-folder findings reports | `%APPDATA%\Attribo\Watched Reports\` | Until you delete them |
| Export PDFs / HTML / Word copies | Wherever you save them | Yours |

## Deleting everything

1. Close the app.
2. Delete the folder `%APPDATA%\Attribo`.
That removes settings, keys, history, and all cached evidence. Exported PDFs remain where you saved them.

## Choosing a provider

- Google and Brave see your search phrases and your IP, under their own privacy policies.
- If you prefer zero third-party exposure, run in **local mode** (no keys): AI-likelihood and
  paraphrase analysis still work; web/academic checks are skipped and the report says so.

## Your friends' data

If you share this app with friends, the same rules apply on their machines: their documents
stay local to them. You (the distributor) receive nothing. Please keep it that way —
do not add any hidden network feature without updating this document.

---
*© 2026 Attribo. All rights reserved.*
