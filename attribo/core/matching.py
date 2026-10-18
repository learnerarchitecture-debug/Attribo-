"""
Tokenization & matching:
  - winnowing k-gram verbatim runs
  - near-match runs (edit-distance tolerant, up to a mismatch budget)
  - paraphrase heuristic with light stemming

(c) 2026 Attribo. All rights reserved.
"""
import math
import re
from collections import Counter, defaultdict

TOKEN_RE = re.compile(r"[A-Za-z0-9\u0600-\u06FF']+")

STOPWORDS = set(
    """
a an the and or but if then else when while for nor so yet at by on in of to from with
without within into onto over under above below between during before after again further
once here there all any both each few more most other some such no not only own same than
too very can could will would should may might must shall do does did doing done have has
had having is are was were be been being it its this that these those i you he she they
we them him her his hers their theirs our ours your yours am as about up down out off
""".split()
)

# Generic academic vocabulary — excluded when judging "rare" shared words.
COMMON_WORDS = STOPWORDS | set(
    """
study research paper result results data method methods analysis figure figures table
tables section chapter thesis dissertation approach system systems based used using show
shows shown given provide provides provided presented propose proposes proposed conclude
concludes conclusion conclusions important significant however therefore thus also among
between theory model models
""".split()
)

_SUFFIXES = (
    "ations", "ation", "izing", "ising", "ingly", "edly", "ments", "ement",
    "nesses", "ness", "ously", "ively", "ings", "ing", "ies", "ied", "ally",
    "ous", "ive", "izes", "ised", "ize", "ise", "ment", "s",
)


def stem(word: str) -> str:
    """Light suffix-stripping stemmer (no external dependencies)."""
    w = word.lower()
    for suffix in _SUFFIXES:
        if w.endswith(suffix) and len(w) - len(suffix) >= 4:
            return w[: len(w) - len(suffix)]
    return w


def tokenize_spans(text: str) -> list:
    """Returns [(word_lower, start_char, end_char)]."""
    return [(m.group(0).lower(), m.start(), m.end()) for m in TOKEN_RE.finditer(text or "")]


def content_set(words: list) -> set:
    """Raw content words (no stopwords, len > 2)."""
    return {w for w in words if w not in STOPWORDS and len(w) > 2}


def content_stems(words: list) -> set:
    """Stemmed content words (no stopwords, len > 2)."""
    return {stem(w) for w in words if w not in STOPWORDS and len(w) > 2}


def content_stem_list(words: list) -> list:
    """Stemmed content words as a list (keeps term frequencies)."""
    return [stem(w) for w in words if w not in STOPWORDS and len(w) > 2]


_COMMON_STEMS = {stem(w) for w in COMMON_WORDS}


def find_verbatim_runs(p_tokens: list, s_words: list, min_words: int, k: int = 5) -> list:
    """
    p_tokens: [(word, start, end)] from the document.
    s_words:  [word] from a fetched source.
    Returns runs as (p0_index, p1_index_exclusive, s0_index, length), length >= min_words.
    """
    if len(p_tokens) < min_words or len(s_words) < k:
        return []
    grams = defaultdict(list)
    for i in range(len(s_words) - k + 1):
        grams[tuple(s_words[i : i + k])].append(i)
    pw = [t[0] for t in p_tokens]
    runs = []
    i = 0
    n = len(pw)
    while i <= n - k:
        positions = grams.get(tuple(pw[i : i + k]))
        if not positions:
            i += 1
            continue
        best_len = 0
        best_sp = -1
        for sp in positions[:8]:
            length = k
            while (
                i + length < n
                and sp + length < len(s_words)
                and pw[i + length] == s_words[sp + length]
            ):
                length += 1
            if length > best_len:
                best_len, best_sp = length, sp
        if best_len >= min_words:
            runs.append((i, i + best_len, best_sp, best_len))
            i += best_len
        else:
            i += 1
    # merge runs that are contiguous in both document and source
    merged = []
    for run in runs:
        if merged:
            a0, a1, s0, length = merged[-1]
            if run[0] - a1 <= 1 and run[2] == s0 + length:
                merged[-1] = (a0, run[1], s0, length + run[3])
                continue
        merged.append(run)
    return merged


def find_near_runs(p_tokens: list, s_words: list, min_words: int, k: int = 5) -> list:
    """
    Edit-tolerant matching: seeds on exact k-grams, extends forward and backward
    allowing a small mismatch budget (typos, inserted/deleted words).
    Returns runs as (p0, p1, s0, matched_tokens, mismatches) with matched >= min_words
    and mismatches >= 1 (purely verbatim regions are handled by find_verbatim_runs).
    """
    if len(p_tokens) < min_words or len(s_words) < k:
        return []
    budget = max(2, min_words // 4)
    grams = defaultdict(list)
    for i in range(len(s_words) - k + 1):
        grams[tuple(s_words[i : i + k])].append(i)
    pw = [t[0] for t in p_tokens]
    n = len(pw)
    src_len = len(s_words)
    runs = []
    i = 0
    while i <= n - k:
        positions = grams.get(tuple(pw[i : i + k]))
        if not positions:
            i += 1
            continue
        best = None
        for sp in positions[:4]:
            x0, y0 = i, sp
            mism = 0
            while x0 > 0 and y0 > 0 and mism < budget:
                if pw[x0 - 1] == s_words[y0 - 1]:
                    x0 -= 1
                    y0 -= 1
                else:
                    mism += 1
                    x0 -= 1
                    y0 -= 1
            x1, y1 = i + k, sp + k
            mm = mism
            while x1 < n and y1 < src_len and mm <= budget:
                if pw[x1] == s_words[y1]:
                    x1 += 1
                    y1 += 1
                else:
                    mm += 1
                    if mm > budget:
                        mm -= 1
                        break
                    x1 += 1
                    y1 += 1
            length = x1 - x0
            matched = length - mm
            if matched >= min_words and mm >= 1 and (best is None or matched > best[3]):
                best = (x0, x1, y0, matched, mm)
        if best:
            runs.append(best)
            i = best[1]
        else:
            i += 1
    return runs


def paraphrase_check(sent_words: list, source_stems: set):
    """
    Conservative paraphrase heuristic over *stemmed* content words.
    Returns overlap ratio (float) or None if the sentence does not qualify.
    """
    content = content_stems(sent_words)
    if len(content) < 8:
        return None
    shared = content & source_stems
    if len(shared) < 6:
        return None
    ratio = len(shared) / len(content)
    if ratio < 0.5:
        return None
    rare_shared = sum(1 for w in shared if len(w) >= 6 and w not in _COMMON_STEMS)
    if rare_shared < 4:
        return None
    return ratio


def find_internal_duplicates(
    tokens: list, min_words: int = 8, min_gap: int = 25, k: int = 5, max_runs: int = 40
) -> list:
    """
    Detect passages repeated *within the same document* (copy-paste accidents).
    Returns runs as (a0, a1, first_position, length) where [a0, a1) repeats the
    text already seen at first_position.
    """
    pw = [t[0] for t in tokens]
    n = len(pw)
    runs = []
    if n < min_words + min_gap:
        return runs
    seen = {}
    i = 0
    while i <= n - k and len(runs) < max_runs:
        key = tuple(pw[i : i + k])
        p = seen.get(key)
        if (
            p is not None
            and i - p >= min_gap
            and (not runs or i >= runs[-1][1])
        ):
            length = k
            while (
                i + length < n
                and p + length < i
                and pw[i + length] == pw[p + length]
            ):
                length += 1
            if length >= min_words:
                runs.append((i, i + length, p, length))
                i += length - (k - 1)
                continue
        if key not in seen:
            seen[key] = i
        i += 1
    return runs


class TfidfIndex:
    """
    Lightweight TF-IDF index over stemmed source documents. Used as a second,
    rarity-weighted paraphrase signal (complements the plain stem-overlap check).
    """

    def __init__(self, stem_lists: list):
        self.df = Counter()
        for stems in stem_lists:
            self.df.update(set(stems))
        self.n_docs = max(len(stem_lists), 1)
        self.default_idf = math.log(self.n_docs + 1.0) + 1.0
        self.doc_vectors = []
        for stems in stem_lists:
            counts = Counter(stems)
            length = len(stems) or 1
            vec = {}
            for term, count in counts.items():
                vec[term] = (1.0 + math.log(count)) * self.idf(term) / length
            norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
            self.doc_vectors.append((vec, norm))

    def idf(self, term: str) -> float:
        return math.log((self.n_docs + 1.0) / (self.df.get(term, 0) + 1.0)) + 1.0

    def best_cosine(self, query_stems: list, min_cosine: float = 0.32, min_shared: int = 5):
        """
        Returns (best_cosine, doc_index, shared_terms) if the best posing source
        clears the thresholds, else None.
        """
        if not query_stems or not self.doc_vectors:
            return None
        counts = Counter(query_stems)
        length = len(query_stems) or 1
        query = {}
        for term, count in counts.items():
            query[term] = (1.0 + math.log(count)) * self.idf(term) / length
        qnorm = math.sqrt(sum(v * v for v in query.values())) or 1.0
        best = None
        for index, (vec, norm) in enumerate(self.doc_vectors):
            dot = 0.0
            shared = 0
            for term, qv in query.items():
                dv = vec.get(term)
                if dv:
                    dot += qv * dv
                    shared += 1
            cosine = dot / (qnorm * norm)
            if cosine >= min_cosine and shared >= min_shared:
                if best is None or cosine > best[0]:
                    best = (cosine, index, shared)
        return best
