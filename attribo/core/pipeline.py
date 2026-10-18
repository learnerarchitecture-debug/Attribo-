"""
Scan orchestration: parse -> segment -> query -> retrieve -> match -> score.

v0.10 pipeline:
  - matching runs on one global token stream (paragraph-boundary safe)
  - verbatim (1.00) / near (0.85) / semantic (0.70) / paraphrase (0.60) classes,
    deduplicated per token, strongest class wins
  - TF-IDF rarity-weighted cosine as a second paraphrase signal
  - optional local semantic layer (ONNX MiniLM, see core/semantic.py)
  - internal duplication check (repeats inside the document itself)
  - citation gap finder + reference list parsing for the validator tab
  - every match carries original-text char spans and a source snippet
    (evidence view / highlight export / Word comments)

(c) 2026 Attribo. All rights reserved.
"""
import datetime
import hashlib
import random
from bisect import bisect_left
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from .ai_detect import analyze_ai
from .citation import find_citation_gaps
from .fixcite import suggestion_for
from .matching import (
    STOPWORDS,
    TfidfIndex,
    content_stem_list,
    content_stems,
    find_internal_duplicates,
    find_near_runs,
    find_verbatim_runs,
    paraphrase_check,
    tokenize_spans,
)
from .normalizer import normalize_text
from .parser import parse_document
from .references import split_entries
from .scoring import MatchItem, SourceInfo, compute_scores
from .segmenter import classify_sections, is_quote_paragraph, split_sentences_with_spans
from .strictness import profile as strictness_profile
from ..engines.academic import AcademicChecker
from ..engines.archive import ArchiveChecker
from ..engines.web_engine import WebChecker
from ..licensing.keycheck import verify_key

MAX_PER_DOMAIN = 2
SEMANTIC_MAX_SOURCE_SENTENCES = 2500
SEMANTIC_MAX_PER_SOURCE = 120


@dataclass
class ScanResult:
    file_name: str = ""
    file_path: str = ""
    doc_hash: str = ""
    report_id: str = ""
    timestamp: str = ""
    words: int = 0
    pages: int = 0
    content_tokens: int = 0
    similarity: float = 0.0
    originality: float = 100.0
    paraphrase_risk: float = 0.0
    ai_likelihood: float = 0.0
    integrity: float = 100.0
    ai_details: dict = field(default_factory=dict)
    matches: list = field(default_factory=list)
    sources: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    queries_run: int = 0
    licensed: bool = False
    full_text: str = ""
    content_paras: list = field(default_factory=list)
    citation_gaps: list = field(default_factory=list)
    ref_entries: list = field(default_factory=list)
    semantic_used: bool = False
    strictness: str = "balanced"


def _suggestion(match_type: str) -> str:
    """Structured, attribution-first fix text (see core/fixcite.py)."""
    return suggestion_for(match_type)


def build_queries(
    content_paras: list, max_queries: int, exclude_quotes: bool, min_terms: int = 6
) -> list:
    low = max(6, int(min_terms) + 2)
    candidates = []
    for para in content_paras:
        if exclude_quotes and is_quote_paragraph(para):
            continue
        for _start, _end, sent in split_sentences_with_spans(para):
            words = [t[0] for t in tokenize_spans(sent)]
            content = [w for w in words if w not in STOPWORDS]
            if low <= len(content) <= 34:
                rarity = sum(1 for w in content if len(w) >= 6)
                candidates.append((rarity + 0.01 * len(content), sent))
    candidates.sort(key=lambda x: -x[0])

    queries = []
    seen_prefixes = set()
    for _score, sent in candidates:
        phrase_words = [t[0] for t in tokenize_spans(sent) if t[0] not in STOPWORDS][:14]
        if len(phrase_words) >= max(5, int(min_terms)):
            key = tuple(phrase_words[:8])
            if key in seen_prefixes:
                continue
            seen_prefixes.add(key)
            phrase = " ".join(phrase_words)
            if phrase not in queries:
                queries.append(phrase)
        if len(queries) >= max_queries:
            break
    return queries


def run_scan(path, settings: dict, progress=None, cancel=None) -> ScanResult:
    def report(pct, msg):
        if progress:
            progress(int(pct), msg)

    def check_cancel():
        if cancel and cancel():
            raise RuntimeError("Scan cancelled.")

    prof = strictness_profile(settings)
    result = ScanResult()
    result.strictness = prof["level"]
    f = Path(path)
    result.file_name = f.name
    result.file_path = str(f)
    result.timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result.report_id = (
        "PC-" + datetime.datetime.now().strftime("%Y") + "-" + "%06X" % random.randrange(16 ** 6)
    )

    try:
        data = f.read_bytes()
    except OSError as exc:
        raise RuntimeError(f"Cannot read file: {exc}") from exc
    result.doc_hash = hashlib.sha256(data).hexdigest()

    # -- parse & normalize -------------------------------------------------
    report(4, "Parsing document...")
    doc = parse_document(str(f))
    result.warnings.extend(doc.warnings)
    result.pages = max(len(doc.pages), 1)
    text = normalize_text(doc.full_text)
    result.words = len(text.split())
    result.full_text = text

    # -- segment -----------------------------------------------------------
    report(9, "Segmenting content...")
    content_paras, ref_paras = classify_sections(text)
    if not content_paras:
        content_paras = [p for p in text.split("\n") if p.strip()] or [text]
    result.content_paras = content_paras
    result.ref_entries = split_entries(ref_paras) if ref_paras else []

    exclude_quotes = bool(settings.get("exclude_quotes", False))
    filtered_paras = [
        p for p in content_paras if not (exclude_quotes and is_quote_paragraph(p))
    ]
    if not filtered_paras:
        filtered_paras = content_paras

    # Build global content text + map content offsets -> original text offsets
    pieces = []
    para_map = []  # (content_start, content_end, orig_start, orig_end)
    c_pos = 0
    cursor = 0
    for para in filtered_paras:
        orig = text.find(para, cursor)
        if orig < 0:
            orig = text.find(para)
            cursor = 0
        if orig >= 0:
            o_end = orig + len(para)
            cursor = o_end
        else:
            orig, o_end = -1, -1
        pieces.append(para)
        para_map.append((c_pos, c_pos + len(para), orig, o_end))
        c_pos += len(para) + 2  # "\n\n"
    content_text = "\n\n".join(pieces)

    def to_original(c_start: int, c_end: int) -> tuple:
        for c0, c1, o0, o1 in para_map:
            if o0 < 0:
                continue
            if c0 <= c_start <= c1:
                if c_end <= c1:
                    return o0 + (c_start - c0), o0 + (c_end - c0)
                return o0 + (c_start - c0), o1
        return -1, -1

    tokens = tokenize_spans(content_text)
    result.content_tokens = sum(1 for t in tokens if t[0] not in STOPWORDS)

    def add_match(mtype, tok_count, weight, text_span, src_title, src_url, gs, ge, snippet=""):
        o_s, o_e = to_original(gs, ge)
        result.matches.append(
            MatchItem(
                match_type=mtype,
                tokens=tok_count,
                weight=weight,
                text=text_span,
                source_title=src_title,
                source_url=src_url,
                suggestion=_suggestion(mtype),
                span_start=o_s,
                span_end=o_e,
                source_snippet=snippet,
            )
        )

    def snippet_tokens(src_text, src_tokens, start_tok, end_tok, pad=140):
        if not src_tokens:
            return ""
        start_tok = max(0, min(int(start_tok), len(src_tokens) - 1))
        end_tok = max(start_tok + 1, min(int(end_tok), len(src_tokens)))
        char_s = src_tokens[start_tok][1]
        char_e = src_tokens[end_tok - 1][2]
        return src_text[max(0, char_s - pad) : min(len(src_text), char_e + pad)]

    def snippet_for_sentence(src_text, sent_words):
        sent_stems = content_stems(sent_words)
        if not sent_stems:
            return ""
        best_sent, best_overlap = "", 0
        for _s, _e, cand in split_sentences_with_spans(src_text):
            cand_stems = content_stems([t[0] for t in tokenize_spans(cand)])
            overlap = len(cand_stems & sent_stems)
            if overlap > best_overlap:
                best_overlap, best_sent = overlap, cand
        return best_sent[:360]

    # -- queries -----------------------------------------------------------
    report(14, "Building search queries...")
    queries = build_queries(
        content_paras, prof["max_queries"], exclude_quotes, prof["min_query_terms"]
    )
    if not queries:
        result.warnings.append("No sentences suitable for web queries were found.")

    # -- retrieval ---------------------------------------------------------
    web = WebChecker(settings)
    academic = AcademicChecker(settings)
    sources = []
    used_urls = set()
    domain_counts = {}

    def allow_domain(url: str) -> bool:
        try:
            domain = urlparse(url).netloc.lower()
        except ValueError:
            return True
        if not domain:
            return True
        if domain_counts.get(domain, 0) >= prof["max_per_domain"]:
            return False
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
        return True

    if settings.get("enable_web", True):
        if web.available():
            for i, phrase in enumerate(queries):
                check_cancel()
                report(16 + int(42 * i / max(len(queries), 1)), f"Web search {i + 1}/{len(queries)}...")
                hits = web.search(phrase)
                for hit in hits[: prof["max_fetch"]]:
                    if not hit.url or hit.url in used_urls or not allow_domain(hit.url):
                        continue
                    used_urls.add(hit.url)
                    fetched = web.fetch_text(hit.url)
                    sources.append(
                        {
                            "title": hit.title or hit.url,
                            "url": hit.url,
                            "text": fetched or "",
                            "kind": "web",
                        }
                    )
                result.queries_run += 1
        elif queries:
            result.warnings.append(
                "Web check skipped: no search API keys configured (local mode)."
            )

    if settings.get("enable_academic", True) and queries:
        half = list(queries) if prof["academic_all"] else queries[: max(4, len(queries) // 2)]
        for i, phrase in enumerate(half):
            check_cancel()
            report(58 + int(9 * i / max(len(half), 1)), f"Academic search {i + 1}/{len(half)}...")
            for hit in academic.search(phrase):
                if not hit.url or hit.url in used_urls:
                    continue
                used_urls.add(hit.url)
                sources.append(
                    {"title": hit.title, "url": hit.url, "text": hit.text, "kind": "academic"}
                )

    archive = ArchiveChecker(settings)
    if archive.available():
        report(68, "Reading local archive...")
        for src in archive.sources(exclude_path=result.file_path):
            if src["url"] in used_urls:
                continue
            used_urls.add(src["url"])
            sources.append(src)
    elif settings.get("enable_archive", False):
        result.warnings.append("Local archive enabled but folder is missing or empty.")

    result.sources = [
        SourceInfo(
            title=src["title"], url=src["url"], kind=src["kind"], fetched=bool(src["text"])
        )
        for src in sources
    ]

    # -- matching ----------------------------------------------------------
    report(72, "Matching passages...")
    prepared = []  # (src, words, stems_set, src_text, stem_list, src_tokens)
    for src in sources:
        if not src["text"]:
            continue
        src_text = normalize_text(src["text"])
        src_tokens = tokenize_spans(src_text)
        if len(src_tokens) < 25:
            continue
        words = [t[0] for t in src_tokens]
        prepared.append((src, words, content_stems(words), src_text, content_stem_list(words), src_tokens))

    min_words = int(prof["min_words"])
    verb_union = set()
    near_union = set()
    para_union = set()
    sem_union = set()
    n_sources = max(len(prepared), 1)

    for sidx, entry in enumerate(prepared):
        check_cancel()
        src, src_words = entry[0], entry[1]
        src_text, src_tokens = entry[3], entry[5]
        report(74 + int(11 * sidx / n_sources), f"Scanning source {sidx + 1}/{len(prepared)}...")

        for a0, a1, s0, length in find_verbatim_runs(tokens, src_words, min_words):
            idxs = set(range(a0, a1))
            if idxs <= verb_union:
                continue
            verb_union.update(idxs)
            text_span = content_text[tokens[a0][1]: tokens[a1 - 1][2]]
            add_match(
                "verbatim", length, 1.0, text_span, src["title"], src["url"],
                tokens[a0][1], tokens[a1 - 1][2],
                snippet_tokens(src_text, src_tokens, s0, s0 + length),
            )

        for a0, a1, s0, matched, _mm in find_near_runs(
            tokens, src_words, min_words, budget=prof["near_budget"]
        ):
            idxs = set(range(a0, a1))
            if idxs & verb_union or idxs & near_union:
                continue
            near_union.update(idxs)
            text_span = content_text[tokens[a0][1]: tokens[a1 - 1][2]]
            add_match(
                "near", matched, 0.85, text_span, src["title"], src["url"],
                tokens[a0][1], tokens[a1 - 1][2],
                snippet_tokens(src_text, src_tokens, s0, s0 + (a1 - a0)),
            )

    # -- paraphrase (stem overlap + TF-IDF) --------------------------------
    report(86, "Paraphrase analysis...")
    if prepared:
        tfidf = TfidfIndex([entry[4] for entry in prepared])
        covered = verb_union | near_union
        starts = [t[1] for t in tokens]
        for s, e, sent in split_sentences_with_spans(content_text):
            check_cancel()
            j0 = bisect_left(starts, s)
            idxs = []
            j = j0
            while j < len(tokens) and tokens[j][1] < e:
                idxs.append(j)
                j += 1
            if len(idxs) < 6:
                continue
            overlap = sum(1 for k in idxs if k in covered)
            if overlap / len(idxs) >= 0.4:
                continue
            sent_words = [tokens[k][0] for k in idxs]
            chosen = None
            best_ratio = 0.0
            for si, entry in enumerate(prepared):
                ratio = paraphrase_check(
                    sent_words,
                    entry[2],
                    prof["para_min_content"],
                    prof["para_min_shared"],
                    prof["para_min_ratio"],
                    prof["para_min_rare"],
                )
                if ratio is not None and ratio > best_ratio:
                    best_ratio = ratio
                    chosen = si
            criterion = "stem-overlap"
            if chosen is None:
                tf = tfidf.best_cosine(
                    content_stem_list(sent_words),
                    min_cosine=prof["tfidf_min_cosine"],
                    min_shared=prof["tfidf_min_shared"],
                )
                if tf is not None:
                    chosen = tf[1]
                    criterion = f"tfidf {tf[0]:.2f}"
            if chosen is not None:
                src = prepared[chosen][0]
                snippet = snippet_for_sentence(prepared[chosen][3], sent_words)
                para_union.update(k for k in idxs if k not in covered)
                add_match(
                    "paraphrase", len(idxs), 0.6, sent, src["title"], src["url"],
                    tokens[idxs[0]][1], tokens[idxs[-1]][2], snippet,
                )

    # -- semantic layer (optional) ------------------------------------------
    if settings.get("enable_semantic", False) and prepared:
        report(89, "Semantic matching (AI embeddings)...")
        from .semantic import embed, model_available

        ok, reason = model_available()
        if not ok:
            result.warnings.append(f"Semantic layer skipped: {reason}")
        else:
            try:
                import numpy as np  # noqa: F401

                covered = verb_union | near_union | para_union
                starts = [t[1] for t in tokens]
                doc_items = []
                for s, e, sent in split_sentences_with_spans(content_text):
                    j0 = bisect_left(starts, s)
                    idxs = []
                    j = j0
                    while j < len(tokens) and tokens[j][1] < e:
                        idxs.append(j)
                        j += 1
                    if len(idxs) < 10:
                        continue
                    overlap = sum(1 for k in idxs if k in covered)
                    if overlap / len(idxs) >= 0.4:
                        continue
                    doc_items.append((idxs, sent))

                src_items = []  # (source_index, sentence_text)
                for si, entry in enumerate(prepared):
                    count = 0
                    for _s, _e, cand in split_sentences_with_spans(entry[3]):
                        if len(tokenize_spans(cand)) < 6:
                            continue
                        src_items.append((si, cand[:400]))
                        count += 1
                        if count >= SEMANTIC_MAX_PER_SOURCE or len(src_items) >= SEMANTIC_MAX_SOURCE_SENTENCES:
                            break
                    if len(src_items) >= SEMANTIC_MAX_SOURCE_SENTENCES:
                        break

                if doc_items and src_items:
                    check_cancel()
                    doc_emb = embed([d[1] for d in doc_items])
                    check_cancel()
                    src_emb = embed([s[1] for s in src_items])
                    check_cancel()
                    sims = doc_emb @ src_emb.T
                    threshold = float(prof["semantic_threshold"])
                    for di, (idxs, _sent) in enumerate(doc_items):
                        row = sims[di]
                        sj = int(np.argmax(row))
                        if float(row[sj]) >= threshold:
                            si, src_sent = src_items[sj]
                            src = prepared[si][0]
                            sem_union.update(k for k in idxs if k not in covered)
                            add_match(
                                "semantic", len(idxs), 0.70, content_text[tokens[idxs[0]][1]: tokens[idxs[-1]][2]],
                                src["title"], src["url"],
                                tokens[idxs[0]][1], tokens[idxs[-1]][2],
                                src_sent,
                            )
                result.semantic_used = True
            except Exception as exc:  # noqa: BLE001
                result.warnings.append(f"Semantic layer error: {exc}")

    # -- internal duplication ----------------------------------------------
    report(92, "Internal duplication check...")
    if settings.get("duplicate_check", True):
        any_union = verb_union | near_union | para_union | sem_union
        for a0, a1, p0, length in find_internal_duplicates(
            tokens, min_words=max(min_words, 8), min_gap=30
        ):
            idxs = set(range(a0, a1))
            if idxs and len(idxs & any_union) / len(idxs) >= 0.8:
                continue
            text_span = content_text[tokens[a0][1]: tokens[a1 - 1][2]]
            earlier = content_text[tokens[p0][1]: tokens[p0 + length - 1][2]][:360]
            add_match(
                "duplicate", length, 0.0, text_span, "This document (earlier passage)", "",
                tokens[a0][1], tokens[a1 - 1][2], earlier,
            )

    # -- citation gaps -------------------------------------------------------
    report(93, "Citation gap analysis...")
    if settings.get("citation_check", True):
        try:
            result.citation_gaps = find_citation_gaps(content_paras)
        except Exception:  # noqa: BLE001
            result.citation_gaps = []

    # per-source attribution (raw indicator, may overlap across sources)
    per_source = {}
    for m in result.matches:
        key = (m.source_url, m.source_title)
        per_source[key] = per_source.get(key, 0) + m.tokens
    for info in result.sources:
        toks = per_source.get((info.url, info.title), 0)
        info.matched_tokens = toks
        info.pct = round(100.0 * toks / max(result.content_tokens, 1), 1)
    result.sources.sort(key=lambda s: -s.pct)

    # -- AI-likelihood -----------------------------------------------------
    report(95, "AI-likelihood analysis...")
    ai_details = {"score": None, "note": "disabled", "flagged": []}
    if settings.get("enable_ai", True):
        ai_details = analyze_ai(text)
    result.ai_details = ai_details

    # -- scores (deduplicated token unions) --------------------------------
    weighted_tokens = (
        len(verb_union) * 1.0
        + len(near_union) * 0.85
        + len(sem_union) * 0.70
        + len(para_union) * 0.60
    )
    scores = compute_scores(
        result.content_tokens,
        weighted_tokens,
        len(para_union) + len(sem_union),
        ai_details.get("score"),
    )
    result.similarity = scores["similarity"]
    result.originality = scores["originality"]
    result.paraphrase_risk = scores["paraphrase"]
    result.ai_likelihood = scores["ai"]
    result.integrity = scores["integrity"]

    if not settings.get("enable_web", True):
        result.warnings.append("Web engine disabled - coverage limited to local analysis.")
    if (
        result.queries_run == 0
        and queries
        and web.available()
        and settings.get("enable_web", True)
        and not archive.available()
    ):
        result.warnings.append("No web queries completed - similarity coverage is limited.")

    license_info = verify_key(str(settings.get("license_key", "")))
    result.licensed = bool(license_info and not license_info.get("expired"))

    report(100, "Done")
    return result
