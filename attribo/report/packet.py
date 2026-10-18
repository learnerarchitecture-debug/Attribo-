"""
Supervisor review packet (PDF).

One document for a supervisor: cover + method & limits, score summary,
findings table, evidence extracts, revision history and the tamper-evident
signature for this report.

(c) 2026 Ayush Gupta (Attribo). All rights reserved.
"""
import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .. import APP_NAME, AUTHOR, COPYRIGHT
from ..core import fixcite
from ..core.signing import sign_result
from ..theme import MATCH_LABELS

INK = colors.HexColor("#111827")
MUTED = colors.HexColor("#6B7280")
ACCENT = colors.HexColor("#4F6BFF")
BORDER = colors.HexColor("#D1D5DB")
LIGHT = colors.HexColor("#F3F4F6")
DARKBAND = colors.HexColor("#0F1420")

MAX_TABLE = 25
MAX_EVIDENCE = 6


def esc(value) -> str:
    return str(value or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _fit(value, limit: int = 110) -> str:
    value = str(value or "")
    return value if len(value) <= limit else value[: limit - 1] + "\u2026"


def _styles():
    sheet = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "PacketTitle", parent=sheet["Title"], textColor=INK, fontSize=22,
            spaceAfter=2 * mm,
        ),
        "sub": ParagraphStyle(
            "PacketSub", parent=sheet["Normal"], textColor=MUTED, fontSize=10,
            spaceAfter=4 * mm,
        ),
        "h2": ParagraphStyle(
            "PacketH2", parent=sheet["Heading2"], textColor=INK, fontSize=13,
            spaceBefore=5 * mm, spaceAfter=2 * mm,
        ),
        "body": ParagraphStyle(
            "PacketBody", parent=sheet["Normal"], fontSize=9.5, leading=13,
            textColor=INK, spaceAfter=2 * mm,
        ),
        "small": ParagraphStyle(
            "PacketSmall", parent=sheet["Normal"], fontSize=8, leading=10.5,
            textColor=MUTED,
        ),
        "mono": ParagraphStyle(
            "PacketMono", parent=sheet["Normal"], fontName="Courier", fontSize=8.5,
            leading=11, textColor=INK,
        ),
    }


def _band_table(data, widths=None, header=True):
    table = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [
        ("TEXTCOLOR", (0, 0), (-1, -1), INK),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("LEADING", (0, 0), (-1, -1), 11),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    if header:
        style += [
            ("BACKGROUND", (0, 0), (-1, 0), DARKBAND),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ]
    table.setStyle(TableStyle(style))
    return table


def build_packet_pdf(result, history_rows, path) -> str:
    """
    Writes the supervisor review packet. `history_rows` are db.recent_scans()
    rows: (ts, doc_name, report_id, similarity, integrity, n_matches).
    Returns the signature string embedded in the packet.
    """
    styles = _styles()
    signature = sign_result(result)
    matches = [m for m in result.matches if (getattr(m, "text", "") or "").strip()]

    story = [
        Paragraph(f"{esc(APP_NAME)} - Supervisor review packet", styles["title"]),
        Paragraph(
            f"Document: <b>{esc(result.file_name)}</b> &nbsp;&middot;&nbsp; "
            f"Report ID: {esc(result.report_id)} &nbsp;&middot;&nbsp; {esc(result.timestamp)}"
            f"<br/>Prepared by the candidate with {esc(APP_NAME)} "
            f"(offline analysis; no document upload) - author: {esc(AUTHOR)}.",
            styles["sub"],
        ),
    ]

    # -- scores ------------------------------------------------------------
    story.append(Paragraph("Score summary", styles["h2"]))
    score_rows = [
        ["Similarity", "Paraphrase risk", "AI-likelihood", "Integrity", "Originality"],
        [
            f"{result.similarity:.1f}%",
            f"{result.paraphrase_risk:.1f}%",
            f"{result.ai_likelihood:.1f}%",
            f"{result.integrity:.1f}%",
            f"{result.originality:.1f}%",
        ],
    ]
    story.append(_band_table(score_rows, header=True))
    story.append(Spacer(1, 2 * mm))
    story.append(
        Paragraph(
            f"Words analysed: {int(result.words):,} &nbsp;&middot;&nbsp; "
            f"flagged passages: {len(matches)} &nbsp;&middot;&nbsp; "
            f"sources compared: {len(result.sources)} &nbsp;&middot;&nbsp; "
            f"search queries: {int(getattr(result, 'queries_run', 0))} &nbsp;&middot;&nbsp; "
            f"scan strictness: {esc(getattr(result, 'strictness', 'balanced'))}",
            styles["small"],
        )
    )

    # -- method & limits ---------------------------------------------------
    story.append(Paragraph("Method & limits", styles["h2"]))
    story.append(
        Paragraph(
            "Passages were compared against web sources (search APIs), academic "
            "indexes (OpenAlex / Crossref) and any locally configured collections "
            "(archive folder, corpus vault). Similarity, paraphrase risk and "
            "AI-likelihood are <b>advisory signals</b>, not verdicts: they can "
            "over-flag common phrasing and under-flag skilled paraphrase. Quoted and "
            "cited material is the expectation; the fixes below follow the "
            "quote / cite / paraphrase rule. Full limits: docs/ACCURACY_AND_LIMITS.md.",
            styles["body"],
        )
    )

    # -- findings table ----------------------------------------------------
    story.append(Paragraph(f"Findings ({min(len(matches), MAX_TABLE)} of {len(matches)})", styles["h2"]))
    if matches:
        rows = [["#", "Type", "Tokens", "Source", "Suggested fix"]]
        for index, match in enumerate(matches[:MAX_TABLE], start=1):
            mtype = getattr(match, "match_type", "")
            rows.append(
                [
                    str(index),
                    MATCH_LABELS.get(mtype, mtype),
                    str(int(getattr(match, "tokens", 0))),
                    Paragraph(esc(_fit(getattr(match, "source_title", "") or "internal", 70)), styles["small"]),
                    Paragraph(esc(_fit(getattr(match, "suggestion", "") or fixcite.suggestion_for(mtype), 90)), styles["small"]),
                ]
            )
        story.append(
            _band_table(rows, widths=[8 * mm, 24 * mm, 13 * mm, 52 * mm, 68 * mm])
        )
    else:
        story.append(Paragraph("No flags were recorded for this scan.", styles["body"]))

    # -- evidence ----------------------------------------------------------
    if matches:
        story.append(PageBreak())
        story.append(Paragraph("Evidence extract", styles["h2"]))
        story.append(
            Paragraph(
                "The strongest flagged passages with their source excerpts and the "
                "compliant replacement used in the fixed copy.",
                styles["small"],
            )
        )
        story.append(Spacer(1, 2 * mm))
        for index, match in enumerate(matches[:MAX_EVIDENCE], start=1):
            mtype = getattr(match, "match_type", "")
            story.append(
                Paragraph(
                    f"{index}. [{esc(MATCH_LABELS.get(mtype, mtype))}] "
                    f"{int(getattr(match, 'tokens', 0))} tokens - "
                    f"{esc(_fit(getattr(match, 'source_title', '') or 'internal comparison', 90))}",
                    styles["body"],
                )
            )
            story.append(
                Paragraph(
                    "&ldquo;" + esc(fixcite.clean_text(getattr(match, "text", ""))[:380]) + "&rdquo;",
                    styles["mono"],
                )
            )
            snippet = fixcite.clean_text(getattr(match, "source_snippet", ""))
            if snippet:
                story.append(
                    Paragraph(
                        f"Source excerpt: <i>{esc(snippet[:260])}</i>",
                        styles["small"],
                    )
                )
            replacement = fixcite.replacement_for(match)
            if replacement:
                story.append(
                    Paragraph(f"Compliant version: {esc(replacement[:300])}", styles["small"])
                )
            story.append(Spacer(1, 3 * mm))

    # -- revision history --------------------------------------------------
    story.append(Paragraph("Revision history (local scan log)", styles["h2"]))
    if history_rows:
        rows = [["When", "Document", "Similarity", "Integrity", "Flags"]]
        for row in history_rows[:15]:
            ts, doc_name, _report_id, similarity, integrity, n_matches = row
            rows.append(
                [
                    esc(_fit(ts, 19)),
                    Paragraph(esc(_fit(Path(str(doc_name)).name, 48)), styles["small"]),
                    f"{float(similarity or 0):.1f}%",
                    f"{float(integrity or 0):.1f}%",
                    str(int(n_matches or 0)),
                ]
            )
        story.append(_band_table(rows, widths=[34 * mm, 76 * mm, 24 * mm, 24 * mm, 15 * mm]))
    else:
        story.append(Paragraph("No earlier scans stored on this machine.", styles["body"]))

    # -- certificate -------------------------------------------------------
    story.append(Paragraph("Certificate & signature", styles["h2"]))
    story.append(
        Paragraph(
            f"Report ID: <b>{esc(result.report_id)}</b><br/>"
            f"Tamper-evident signature: <b>{esc(signature)}</b><br/>"
            "Verification: Attribo &rarr; Certificate tab &rarr; Verify report ID. "
            "The signature is recomputed from the locally stored scan row; if the "
            "packet or report was edited outside the app, verification fails.",
            styles["body"],
        )
    )
    story.append(
        Paragraph(
            f"Generated {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} &middot; "
            f"{esc(COPYRIGHT)}",
            styles["small"],
        )
    )

    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=f"{APP_NAME} supervisor packet - {result.file_name}",
        author=AUTHOR,
    )
    doc.build(story)
    return signature
