"""
Paragraph/sentence segmentation & section detection.

(c) 2026 Attribo. All rights reserved.
"""
import re

REFERENCE_HEADING = re.compile(
    r"^\s*(references?|bibliography|works\s+cited|literature\s+cited|"
    r"\u0627\u0644\u0645\u0631\u0627\u062c\u0639|\u0642\u0627\u0626\u0645\u0629\s+\u0627\u0644\u0645\u0631\u0627\u062c\u0639)\s*:?\s*$",
    re.IGNORECASE,
)

QUOTE_CHARS = ('"', ">", "\u201c", "\u2018")


def split_paragraphs(text: str) -> list:
    return [p.strip() for p in re.split(r"\n\s*\n", text or "") if p.strip()]


def is_reference_heading(paragraph: str) -> bool:
    return bool(REFERENCE_HEADING.match(paragraph or ""))


def is_quote_paragraph(paragraph: str) -> bool:
    stripped = (paragraph or "").lstrip()
    return bool(stripped) and stripped[0] in QUOTE_CHARS


def classify_sections(text: str):
    """Returns (content_paragraphs, reference_paragraphs)."""
    paragraphs = split_paragraphs(text)
    for index, paragraph in enumerate(paragraphs):
        if is_reference_heading(paragraph):
            return paragraphs[:index], paragraphs[index + 1:]
    return paragraphs, []


def split_sentences_with_spans(paragraph: str) -> list:
    """Returns [(start, end, sentence_text)] with character offsets."""
    spans = []
    if not paragraph:
        return spans
    pattern = r"[^.!?\u061f]+[.!?\u061f]+[\"'\u201d\u2019)\]]*|[^.!?\u061f]+$"
    for match in re.finditer(pattern, paragraph):
        start, end = match.start(), match.end()
        while start < end and paragraph[start].isspace():
            start += 1
        while end > start and paragraph[end - 1].isspace():
            end -= 1
        if end > start:
            spans.append((start, end, paragraph[start:end]))
    return spans
