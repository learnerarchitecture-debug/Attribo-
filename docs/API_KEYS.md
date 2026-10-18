# API Keys Setup — Attribo

> © 2026 Attribo. All rights reserved.

The app works without keys (local mode), but web checking needs at least one search provider.
Academic checking (OpenAlex, Crossref) is **always free and needs no key, no account**.

Add keys via the gear icon → Settings → **Test search APIs** verifies each key live.
Keys are stored locally in `%APPDATA%\Attribo\settings.json`.

## No-card options at a glance

| Provider | Free tier | Credit card? | Get it at |
|---|---|---|---|
| **Brave Search API** | ~2,000 queries/month (1 q/s) | **No** | https://api-dashboard.search.brave.com |
| **Serper.dev** | 2,500 one-time credits | **No** | https://serper.dev |
| **Tavily** | 1,000 credits/month | **No** | https://app.tavily.com |
| **Exa** | free credits on signup | **No** | https://dashboard.exa.ai |
| **SearXNG (self-hosted)** | unlimited | **No** (no account at all) | see below |
| Google Custom Search JSON API | 100 queries/day | Google account; billing may be requested for some new projects | https://console.cloud.google.com |

> Avoid Bing Web Search API — Microsoft **retired it in August 2025**. Any tutorial mentioning it is outdated.

**Recommended combo (all no-card):** Brave (big monthly budget) + Serper or Tavily (top-up) + Exa (semantic-ish results).
Google CSE is a nice extra if you already have a Google Cloud account.

## Cross-verification: how the app uses several providers

Two independent layers:

1. **Provider cross-check** — with "Cross-check: query all configured providers" enabled
   (default), every search phrase is sent to *all* configured providers; results are merged
   and de-duplicated by URL. If one provider silently fails or throttles, the others cover it.
2. **Evidence verification** — every hit is fetched as an actual page and matched against the
   *page text itself* (not the search snippet). A flag only counts when the real source
   confirms it, so a provider can never "fake" a match. Snippets are just leads.

One scan with 12 queries and 3 providers ≈ 36 provider calls. Mind your free tiers:
Brave 2,000/month is plenty, Serper's 2,500 credits is one-time — keep it as backup.

## Provider setup steps

### Brave Search API (recommended first key)
1. Go to https://api-dashboard.search.brave.com and create an account (email only).
2. Subscribe to the **Free** plan and create an API key.
3. Paste into Settings: *Brave API key*.

### Serper.dev (no card, 2,500 free credits)
1. Go to https://serper.dev and sign up (email/Google).
2. Your API key is shown on the dashboard immediately.
3. Paste into Settings: *Serper API key*.

### Tavily (no card, 1,000 credits/month)
1. Go to https://app.tavily.com and sign up.
2. Copy the API key from the dashboard.
3. Paste into Settings: *Tavily API key*.

### Exa (no card, free credits)
1. Go to https://dashboard.exa.ai and sign up.
2. Create an API key.
3. Paste into Settings: *Exa API key*.

### SearXNG (unlimited, zero accounts, fully private)
Runs on your own PC; no provider sees your queries at all. Requires Docker (or Python).
```powershell
docker run -d --name searxng -p 8888:8888 -v searxng:/etc/searxng searxng/searxng
```
Then set *SearXNG URL* in Settings to `http://localhost:8888`.
Note: most **public** searx instances disable the JSON API — self-hosting is the reliable way.

### Google Custom Search JSON API (100 queries/day)
1. https://console.cloud.google.com/ → create a project (free).
2. Enable "Custom Search API" (APIs & Services → Library).
3. Credentials → Create credentials → **API key**. Copy it.
4. Create a search engine at https://programmablesearchengine.google.com/
   - Set it to search **the entire web**, copy the **Search engine ID** (`cx`).
5. Paste both into Settings: *Google API key* and *Google search engine ID*.

Billing note: beyond 100/day Google charges ~$5 per 1,000 queries. For personal use the free
tier is usually enough if you keep `max_queries` at 8–12. Some new Google Cloud accounts are
asked to link a billing account (card) even for the free tier — if you don't want that, just
use the no-card providers above.

## CORE API (future connector — roadmap)

Free for non-commercial use: https://core.ac.uk/services/api — not yet wired in (v0.10).

## Rate limiting built into the app

| Setting | Default | Meaning |
|---|---|---|
| Search queries per scan | 12 | How many distinctive sentences are sent to providers |
| Fetch cap | 4 per query | Max source pages fetched and matched per query |
| Domain cap | 2 per domain | Diversity guard per scan |
| Timeout / request | 12 s | Per search/fetch timeout |
| Page size cap | ~400 KB | Larger pages are truncated |

Keep the query count low until you know your daily API budget.

## Privacy reminder

Only the short search phrase (a few words) leaves your machine, plus normal HTTP metadata to
the provider(s) you configured. **Your document is never uploaded.** With self-hosted SearXNG,
nothing leaves your PC at all.

---
*© 2026 Attribo. All rights reserved.*
