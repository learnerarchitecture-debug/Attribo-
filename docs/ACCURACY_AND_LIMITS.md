# Accuracy & Limits — Read Before Trusting Any Score

> © 2026 Attribo. All rights reserved.

## The honest statement

**No plagiarism checker detects 100% of plagiarism.** Not this one, not Turnitin, not iThenticate.
A "0% similarity" result does not prove originality. It proves only that *this scan, with its coverage, found nothing*.

## Known limits

| Limit | Consequence | Mitigation in this app |
|---|---|---|
| Paywalled journals can't be indexed legally | Copied text from paywalled papers may pass | Academic OA connectors + optional licensed-API "premium scan" (roadmap); coverage stated on every report |
| Search APIs don't index the entire web | Deep pages may be missed | Multiple providers supported; more queries = more coverage (user-controlled) |
| Paraphrase detection is heuristic | Deep manual paraphrase can pass | Conservative flagging + TF-IDF rarity-weighted pass + optional local semantic embedding layer (catches synonym-level paraphrase); "review manually" guidance on every flag |
| Semantic layer is a small embedding model (MiniLM) | Very technical or domain-heavy paraphrase may still pass; one-time ~90 MB model download | Opt-in; threshold calibrated at 0.70 (real paraphrases tested at 0.81–0.94, unrelated text ≈ 0.03); runs fully offline after download |
| AI detection is probabilistic | False positives/negatives unavoidable | Reported as confidence signal with sub-metrics (stylometry-1.5); never a binary verdict; no text leaves the machine |
| AI detectors are biased against non-native English writers | Risk of wrongful accusation | Bias disclosure; results framed as signals for self-review, never as evidence against a person |
| Scanned PDFs without OCR | No text = no scan | Detection + warning; OCR on roadmap |
| References excluded from scoring | Copied references won't flag | By design — matches academic convention |

## Trust engineering in this app

1. **Evidence-first design** — every percentage is traceable to a listed source with URL and matched text; the Matches tab shows your passage side-by-side with the captured source passage, and highlighted/Word exports carry the same source notes.
2. **Coverage disclosure** — queries run, sources retrieved, tokens analyzed, all printed on reports.
3. **No over-claiming language** — never "100% accurate", never "proves", always "indicates / signals".
4. **Reproducibility** — evidence snapshots are cached locally so a report can be re-examined later.
5. **Document hash** — the SHA-256 on the certificate fixes exactly what was scanned.
6. **Attribution-first remediation** — Fix & Cite suggests citing/quoting/rewriting, not detection evading.

## Benchmarks (roadmap, before any public accuracy claim)

| Evaluation | Dataset | Metric |
|---|---|---|
| Verbatim detection | PAN-PC-11 / PAN 2012 plagiarism corpus | Span-level precision / recall / F1 |
| AI detection | HC3 / RAID | AUC, per-domain breakdown |
| False-positive rate | Self-seeded original theses | Flags per 1,000 words |

Until benchmarks are run and published in this file, treat all engine scores as **beta-quality signals**.

## Use policy

- Permitted: pre-submission self-screening, supervisor review support, draft improvement.
- Forbidden by license: using the tool to facilitate academic misconduct. Fix & Cite is attribution-first by design.
- The certificate states explicitly: "Advisory screening — not a determination of misconduct."

---
*© 2026 Attribo. All rights reserved.*
