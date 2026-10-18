# Scoring Methodology — Attribo

> © 2026 Attribo. All rights reserved.

Everything on the certificate must be explainable. This document defines each number.

## 1. Content scope

- The **references/bibliography section** is detected (common heading patterns) and excluded from scoring.
- Block-quote lines (starting with `"`, `“`, or `>`) are excluded from scoring **only if** the user enables "exclude quotes" in settings (default: included, so quoted copying cannot hide).
- Everything else is *content*.

## 2. Tokenization

- Unicode NFKC normalization; zero-width characters removed; de-hyphenation of line breaks.
- Tokens = words/numbers (Latin + Arabic-script ranges), lowercased.
- Each token keeps its exact character offsets, enabling character-accurate highlighting.

## 3. Verbatim and near-match detection

- Method: **winnowing k-gram fingerprinting** (k = 5) with run extension.
- A *verbatim match* = a contiguous run of identical tokens of length ≥ `min_match_words` (default **8**).
- A *near match* = an aligned run of ≥ `min_match_words` tokens with a small mismatch budget
  (`max(2, min_match_words / 4)`) — catches copied passages with a few swapped, inserted or deleted
  words (light edits, typos) that pure fingerprinting would miss. Weight: **0.85**.
- Matching runs on **one global token stream** of the document body, so matches that span
  paragraph boundaries are found.
- Overlapping runs are merged; the longest/strongest run per region wins.
- Each match carries: class, source, character span, token count, weight.

## 4. Paraphrase risk (beta)

A sentence is flagged when **all** hold:

1. No verbatim/near match covers it (else it is already counted there).
2. Content-word overlap with a source ≥ 50% of the sentence's content words.
3. At least 6 shared content words, of which ≥ 4 are "rare" (stem length ≥ 6, not generic academic vocabulary).
4. Comparison uses **light stemming** (suffix stripping): analysis / analysing / analysed count as one word family, so shuffled-word-family text is caught without loosening the thresholds.

A second, independent signal is the **TF-IDF paraphrase pass**: sentence stems are compared to
each source document as a rarity-weighted (IDF) vector; the sentence is flagged when
cosine ≥ **0.32** with ≥ 5 shared content words. Plain-frequency overlap and TF-IDF catch
different paraphrases, so both run and the best source wins.

If the **semantic layer** is enabled (Settings → "Semantic matching", requires the one-time
model download), sentences are additionally compared by local sentence embeddings
(all-MiniLM-L6-v2): cosine ≥ **0.70** flags synonym-level paraphrase that stems and TF-IDF
cannot see. Semantic matches have weight **0.70**. Nothing leaves the machine — only the
model file is downloaded once.

This is a heuristic, not proof. It is deliberately conservative to limit noise.

## 5. Similarity score

Every content token is counted **once**, at the weight of its strongest match class
(no double counting when the same passage matches several sources):

```
weighted_tokens = |verbatim_tokens| × 1.00
                + |near_only_tokens| × 0.85
                + |semantic_only_tokens| × 0.70
                + |paraphrase_only_tokens| × 0.60

Similarity (%) = 100 × weighted_tokens / content_tokens        (capped at 100)
Originality (%) = 100 − Similarity
Paraphrase Risk (%) = 100 × (semantic_only_tokens + paraphrase_only_tokens) / content_tokens
```

Per-source contribution: matched tokens attributed to that source ÷ content tokens
(raw indicator — the same passage can be shored up by more than one source).

**Internal duplication** is reported separately (violet flags in exports) and is *not* counted
in the external similarity score: copies of your own text are a writing-quality issue, not
plagiarism. It appears in findings, the highlighted copy and the Word review copy.

## 6. AI-Likelihood score (beta)

Purely stylometric, computed locally — no text leaves the machine for this.

Current version: **stylometry-1.5** (stamped on results and certificates).

| Sub-metric | What it measures | Suspicion direction |
|---|---|---|
| Burstiness | stdev/mean of sentence lengths (words) | Low variance → higher suspicion |
| Lexical diversity | type-token ratio | Uniform mid-range diversity → mild signal |
| Formulaic density | hits per 1,000 words from a curated AI-phrase lexicon | Higher → higher suspicion |
| Discourse markers | transition-word hits per 1,000 words | Higher → higher suspicion |
| Opener repetition | ratio of unique sentence-first-words | Low uniqueness → higher suspicion |
| Repetition | repeated 3-gram ratio | Higher → mild signal |

```
AI (%) = clamp( 0.35·burstiness_score + 0.18·formulaic_score + 0.15·transition_score
              + 0.12·opener_score + 0.10·diversity_score + 0.10·repetition_score )
```

**This is a signal, not a verdict.** Human academic writing can score high; formulaic human writing can too.
Reported with the breakdown so reviewers can judge. See ACCURACY_AND_LIMITS.md.

## 7. Composite integrity score

```
Integrity (%) = 100 − (0.50·Similarity + 0.30·AI + 0.20·ParaphraseRisk)
```

Weights are visible, documented, and adjustable in `settings.json` for power users.

## 8. Confidence & presentation rules

- Scores are 0–100 with **one decimal**; UI shows integer but report keeps the decimal.
- Every similarity percentage on the certificate must link (via report) to listed evidence.
- If the web engine was inactive (no keys), the Similarity figure is marked **"local mode — coverage limited"** on the certificate.
- If fewer than 3 search queries completed, the report adds a coverage warning.
- Report IDs can be checked against this PC's scan history (Certificate tab → **Verify report ID**).

## 9. What would falsify a good score

A low similarity score is only meaningful with sufficient coverage. The report therefore always states:

- queries executed (n of max),
- sources retrieved (n),
- sources fetched successfully (n),
- content tokens analyzed (n).

---
*© 2026 Attribo. All rights reserved.*
