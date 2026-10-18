"""
Text normalization: NFKC, zero-width removal, de-hyphenation, whitespace.

(c) 2026 Attribo. All rights reserved.
"""
import re
import unicodedata

_ZERO_WIDTH = "".join(
    chr(c) for c in (0x200B, 0x200C, 0x200D, 0x200E, 0x200F, 0x202A, 0x202B, 0x202C, 0x202D, 0x202E, 0x2060, 0xFEFF)
)


def normalize_text(text: str) -> str:
    t = unicodedata.normalize("NFKC", text or "")
    t = t.translate({ord(ch): None for ch in _ZERO_WIDTH})
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", t)  # de-hyphenate line breaks
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()
