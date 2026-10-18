"""
Word review copy: saves a .docx copy of the document with every flag inserted
as an inline Word comment, so findings can be resolved one by one in Word.

python-docx has no comments API, so the comment ranges are written into
document.xml and the word/comments.xml part is injected at the zip level.

(c) 2026 Attribo. All rights reserved.
"""
import copy
import datetime
import re
import zipfile
from difflib import SequenceMatcher
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from ..core.matching import TOKEN_RE

COMMENT_AUTHOR = "Attribo"
COMMENT_INITIALS = "AP"
MAX_COMMENTS = 150
MIN_BLOCK = 5
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"


def _run_text(r_el) -> str:
    return "".join((t.text or "") for t in r_el.findall(qn("w:t")))


def _split_run_element(r_el, offset: int) -> None:
    """Split a w:r so a text boundary exists at `offset` (0 < offset < len)."""
    ts = r_el.findall(qn("w:t"))
    if not ts:
        return
    cum = 0
    for t in ts:
        txt = t.text or ""
        nxt = cum + len(txt)
        if cum < offset <= nxt:
            cut = offset - cum
            if cut <= 0 or cut >= len(txt):
                return
            t.text = txt[:cut]
            t.set(XML_SPACE, "preserve")
            new_r = copy.deepcopy(r_el)
            new_ts = new_r.findall(qn("w:t"))
            for extra in new_ts[1:]:
                new_r.remove(extra)
            first = new_ts[0]
            first.text = txt[cut:]
            first.set(XML_SPACE, "preserve")
            r_el.addnext(new_r)
            return
        cum = nxt


def _add_comment_range(paragraph, char_start: int, char_end: int, cid: int) -> bool:
    p = paragraph._p

    def current_runs():
        return list(p.findall(qn("w:r")))

    def split_at(offset: int) -> None:
        runs = current_runs()
        cum = 0
        for r in runs:
            txt = _run_text(r)
            nxt = cum + len(txt)
            if cum < offset < nxt:
                _split_run_element(r, offset - cum)
                return
            cum = nxt

    split_at(char_start)
    split_at(char_end)

    runs = current_runs()
    cum = 0
    first = last = None
    for r in runs:
        nxt = cum + len(_run_text(r))
        if nxt > char_start and cum < char_end:
            if first is None:
                first = r
            last = r
        cum = nxt
    if first is None or last is None:
        return False

    start_el = OxmlElement("w:commentRangeStart")
    start_el.set(qn("w:id"), str(cid))
    first.addprevious(start_el)

    end_el = OxmlElement("w:commentRangeEnd")
    end_el.set(qn("w:id"), str(cid))
    last.addnext(end_el)

    ref_run = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    style = OxmlElement("w:rStyle")
    style.set(qn("w:val"), "CommentReference")
    rpr.append(style)
    ref_run.append(rpr)
    ref = OxmlElement("w:commentReference")
    ref.set(qn("w:id"), str(cid))
    ref_run.append(ref)
    end_el.addnext(ref_run)
    return True


def _comment_text(match) -> str:
    parts = [f"[{str(match.match_type).upper()}] {int(match.tokens)} tokens"]
    if match.source_title:
        parts.append(f"Source: {match.source_title}")
    if match.source_url:
        parts.append(match.source_url)
    if match.suggestion:
        parts.append(match.suggestion)
    return "\n".join(parts)[:900]


def _existing_comment_max_id(path: Path) -> int:
    try:
        with zipfile.ZipFile(path) as zf:
            if "word/comments.xml" not in zf.namelist():
                return -1
            blob = zf.read("word/comments.xml").decode("utf-8", errors="ignore")
        ids = [int(i) for i in re.findall(r'w:id="(\d+)"', blob)]
        return max(ids) if ids else -1
    except Exception:  # noqa: BLE001
        return -1


def _comments_xml(comments: list, existing_blob: str = "") -> str:
    stamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = []
    for cid, text in comments:
        lines = text.splitlines() or [""]
        paras = "".join(
            f'<w:p><w:r><w:t xml:space="preserve">{xml_escape(line)}</w:t></w:r></w:p>'
            for line in lines
        )
        rows.append(
            f'<w:comment w:id="{cid}" w:author="{COMMENT_AUTHOR}" '
            f'w:initials="{COMMENT_INITIALS}" w:date="{stamp}">{paras}</w:comment>'
        )
    if existing_blob:
        return existing_blob.replace("</w:comments>", "".join(rows) + "</w:comments>")
    ns = (
        'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f"<w:comments {ns}>{''.join(rows)}</w:comments>"
    )


def _inject_comments(path: Path, comments: list) -> None:
    with zipfile.ZipFile(path) as zin:
        names = zin.namelist()
        data = {name: zin.read(name) for name in names}

    existing_blob = ""
    if "word/comments.xml" in data:
        existing_blob = data["word/comments.xml"].decode("utf-8", errors="ignore")

    # [Content_Types].xml override
    ct_name = "[Content_Types].xml"
    if ct_name in data and "wordprocessingml.comments+xml" not in data[ct_name].decode(
        "utf-8", errors="ignore"
    ):
        ct = data[ct_name].decode("utf-8")
        ct = ct.replace(
            "</Types>",
            '<Override PartName="/word/comments.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/>'
            "</Types>",
        )
        data[ct_name] = ct.encode("utf-8")

    # document.xml.rels relationship
    rels_name = "word/_rels/document.xml.rels"
    if rels_name in data:
        rels = data[rels_name].decode("utf-8")
        if "comments.xml" not in rels:
            used_ids = [int(i) for i in re.findall(r'Id="rId(\d+)"', rels)]
            next_id = (max(used_ids) if used_ids else 0) + 1
            rels = rels.replace(
                "</Relationships>",
                f'<Relationship Id="rId{next_id}" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments" '
                'Target="comments.xml"/></Relationships>',
            )
            data[rels_name] = rels.encode("utf-8")

    data["word/comments.xml"] = _comments_xml(comments, existing_blob).encode("utf-8")

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, blob in data.items():
            zout.writestr(name, blob)


def export_docx_with_comments(result, path) -> tuple:
    """Returns (comments_added, skipped). Raises on unusable input."""
    src = Path(result.file_path)
    if src.suffix.lower() != ".docx":
        raise ValueError("Word comment export requires a .docx source document.")

    doc = Document(str(src))
    paragraphs = [p for p in doc.paragraphs if (p.text or "").strip()]
    index = []
    for p in paragraphs:
        text = p.text or ""
        toks = [(m.group(0).lower(), m.start(), m.end()) for m in TOKEN_RE.finditer(text)]
        index.append((text, toks))

    cid_base = _existing_comment_max_id(src) + 1
    comments = []
    skipped = 0

    for match in result.matches:
        if len(comments) >= MAX_COMMENTS:
            break
        query = [m.group(0).lower() for m in TOKEN_RE.finditer(match.text or "")][:60]
        if len(query) < MIN_BLOCK:
            skipped += 1
            continue
        query_set = set(query)

        best = None  # (size, p_index, start_tok)
        for p_i, (_text, toks) in enumerate(index):
            if len(toks) < MIN_BLOCK:
                continue
            words = [t[0] for t in toks]
            shared = sum(1 for w in set(words) if w in query_set)
            if shared < max(4, MIN_BLOCK):
                continue
            matcher = SequenceMatcher(None, words, query, autojunk=False)
            for block in matcher.get_matching_blocks():
                if block.size >= MIN_BLOCK and (best is None or block.size > best[0]):
                    best = (block.size, p_i, block.a)
        if best is None:
            skipped += 1
            continue

        _size, p_i, start_tok = best
        _text, toks = index[p_i]
        char_start = toks[start_tok][1]
        char_end = toks[start_tok + _size - 1][2]
        cid = cid_base + len(comments)
        if _add_comment_range(paragraphs[p_i], char_start, char_end, cid):
            comments.append((cid, _comment_text(match)))
        else:
            skipped += 1

    if not comments:
        raise RuntimeError(
            "No flagged passages could be located in the .docx text "
            "(the document may have changed since the scan)."
        )

    doc.save(str(path))
    _inject_comments(Path(path), comments)
    return len(comments), skipped
