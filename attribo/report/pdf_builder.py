"""
PDF report + certificate builders.

(c) 2026 Attribo. All rights reserved.
"""
import io

import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .. import APP_NAME, COPYRIGHT

INK = colors.HexColor("#111827")
MUTED = colors.HexColor("#6B7280")
ACCENT = colors.HexColor("#4F6BFF")
BORDER = colors.HexColor("#D1D5DB")
LIGHT = colors.HexColor("#F3F4F6")
DARKBAND = colors.HexColor("#0F1420")


def esc(value) -> str:
    return str(value or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _fit(value, limit: int = 110) -> str:
    value = str(value or "")
    return value if len(value) <= limit else value[: limit - 1] + "\u2026"


def build_report(result, path) -> None:
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        title=f"Attribo Report {result.report_id}",
        author="Attribo",
    )
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], textColor=INK, fontSize=19, spaceAfter=2)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], textColor=INK, fontSize=12, spaceBefore=10, spaceAfter=4)
    body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=9.5, textColor=INK, leading=13)
    small = ParagraphStyle("small", parent=body, textColor=MUTED, fontSize=8)

    story = [
        Paragraph(f"{esc(APP_NAME)} - Screening Report", h1),
        Paragraph(f"Report ID: {esc(result.report_id)} | Generated: {esc(result.timestamp)}", small),
        Spacer(1, 6),
        Paragraph("Document", h2),
        Paragraph(
            f"<b>{esc(_fit(result.file_name, 90))}</b><br/>"
            f"SHA-256: {esc(result.doc_hash)}<br/>"
            f"Words: {result.words} | Pages: {result.pages} | "
            f"Content tokens analysed: {result.content_tokens}",
            body,
        ),
        Paragraph("Scores (0-100)", h2),
    ]

    score_rows = [
        ["Metric", "Value"],
        ["Similarity", f"{result.similarity}%"],
        ["Originality", f"{result.originality}%"],
        ["Paraphrase risk (beta)", f"{result.paraphrase_risk}%"],
        ["AI-likelihood (beta signal)", f"{result.ai_likelihood}%"],
        ["Composite integrity", f"{result.integrity}%"],
    ]
    table = Table(score_rows, colWidths=[70 * mm, 40 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF1FF")),
                ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(table)

    story.append(Paragraph("Coverage", h2))
    story.append(
        Paragraph(
            f"Web queries executed: {result.queries_run} | "
            f"Sources retrieved: {len(result.sources)} | "
            f"Licensed copy: {'Yes' if result.licensed else 'No (unregistered)'}",
            body,
        )
    )
    for warning in result.warnings:
        story.append(Paragraph(f"[note] {esc(warning)}", small))
    if not result.licensed:
        story.append(
            Paragraph("Unregistered copy - certificate will be marked accordingly.", small)
        )

    story.append(Paragraph("Sources", h2))
    if result.sources:
        rows = [["#", "Source", "Type", "%"]]
        for index, source in enumerate(result.sources[:40], 1):
            rows.append(
                [
                    str(index),
                    Paragraph(
                        f"<b>{esc(_fit(source.title, 95))}</b><br/>"
                        f"<font size=7 color='#6B7280'>{esc(_fit(source.url, 120))}</font>",
                        small,
                    ),
                    esc(source.kind),
                    f"{source.pct:.1f}%",
                ]
            )
        table2 = Table(rows, colWidths=[8 * mm, 108 * mm, 22 * mm, 20 * mm])
        table2.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
                    ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
                    ("FONTSIZE", (0, 1), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(table2)
    else:
        story.append(Paragraph("No matching sources were found within this scan's coverage.", body))

    story.append(Paragraph("Flagged passages", h2))
    if result.matches:
        for index, match in enumerate(result.matches[:80], 1):
            story.append(
                Paragraph(
                    f"<b>{index}. [{esc(match.match_type)}] "
                    f"{esc(_fit(match.source_title, 80))}</b><br/>"
                    f"\u201c{esc(_fit(match.text, 300))}\u201d<br/>"
                    f"<font size=7 color='#6B7280'>{esc(_fit(match.source_url, 120))}</font><br/>"
                    f"<i>{esc(match.suggestion)}</i>",
                    body,
                )
            )
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph("No flagged passages.", body))

    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            "Advisory screening only - not a determination of misconduct. Coverage and method "
            "limits apply (see methodology documentation). " + esc(COPYRIGHT),
            small,
        )
    )
    doc.build(story)


def build_certificate(result, path, licensed: bool = False) -> None:
    width, height = A4
    canvas = pdfcanvas.Canvas(str(path), pagesize=A4)
    canvas.setTitle(f"Attribo Certificate {result.report_id}")

    canvas.setFillColor(colors.white)
    canvas.rect(0, 0, width, height, stroke=0, fill=1)

    # header band
    band_h = 44 * mm
    canvas.setFillColor(DARKBAND)
    canvas.rect(0, height - band_h, width, band_h, stroke=0, fill=1)
    canvas.setFillColor(ACCENT)
    canvas.rect(0, height - band_h - 1.5 * mm, width, 1.5 * mm, stroke=0, fill=1)

    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 23)
    canvas.drawString(20 * mm, height - 23 * mm, "Attribo")
    canvas.setFillColor(colors.HexColor("#9AA7C7"))
    canvas.setFont("Helvetica", 11.5)
    canvas.drawString(20 * mm, height - 30 * mm, "Attribo - Screening Certificate")

    canvas.setFont("Courier-Bold", 10)
    canvas.setFillColor(colors.white)
    canvas.drawRightString(width - 20 * mm, height - 22 * mm, result.report_id)
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.HexColor("#9AA7C7"))
    canvas.drawRightString(width - 20 * mm, height - 28 * mm, f"Generated: {result.timestamp}")

    # document
    y = height - band_h - 14 * mm
    canvas.setFillColor(INK)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(20 * mm, y, "Document")
    y -= 6 * mm
    canvas.setFont("Helvetica", 11)
    canvas.drawString(20 * mm, y, _fit(result.file_name, 70))
    y -= 4.5 * mm
    canvas.setFont("Courier", 7.2)
    canvas.setFillColor(MUTED)
    canvas.drawString(20 * mm, y, f"SHA-256: {result.doc_hash}")
    y -= 12 * mm

    # scores
    canvas.setFillColor(INK)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(20 * mm, y, "Scores (0-100)")
    y -= 7 * mm

    rows = [
        ("Similarity", result.similarity),
        ("Originality", result.originality),
        ("Paraphrase risk (beta)", result.paraphrase_risk),
        ("AI-likelihood (beta signal)", result.ai_likelihood),
        ("Composite integrity", result.integrity),
    ]
    for label, value in rows:
        canvas.setFillColor(LIGHT)
        canvas.rect(20 * mm, y - 2.2 * mm, 132 * mm, 7.6 * mm, stroke=0, fill=1)
        canvas.setFillColor(INK)
        canvas.setFont("Helvetica", 10)
        canvas.drawString(23 * mm, y, label)
        canvas.setFont("Helvetica-Bold", 10)
        if label.startswith("Composite"):
            canvas.setFillColor(ACCENT)
        else:
            canvas.setFillColor(INK)
        canvas.drawRightString(148 * mm, y, f"{value:.1f}%")
        y -= 9 * mm

    # coverage + license
    y -= 2 * mm
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 8.5)
    canvas.drawString(
        20 * mm,
        y,
        f"Web queries executed: {result.queries_run} | "
        f"Sources retrieved: {len(result.sources)} | "
        f"Flagged passages: {len(result.matches)}",
    )
    y -= 5 * mm
    status = "Registered copy" if licensed else "Unregistered copy (trial)"
    canvas.drawString(20 * mm, y, f"License status: {status}")

    # QR
    qr = qrcode.QRCode(border=1, box_size=4)
    qr.add_data(
        f"ATTRIBO|{result.report_id}|SHA={result.doc_hash[:16]}"
        f"|SIM={result.similarity}|INT={result.integrity}"
    )
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    canvas.drawImage(ImageReader(buffer), width - 58 * mm, 24 * mm, 34 * mm, 34 * mm)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawRightString(width - 20 * mm, 20 * mm, "Scan to verify report ID")

    # disclaimer
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(20 * mm, 34 * mm, "Advisory screening only - not a determination of misconduct.")
    canvas.drawString(20 * mm, 30 * mm, "Coverage and method limits apply; see methodology documentation.")
    canvas.drawString(20 * mm, 26 * mm, COPYRIGHT)

    # watermark
    if not licensed:
        canvas.saveState()
        canvas.setFillAlpha(0.10)
        canvas.setFillColor(INK)
        canvas.setFont("Helvetica-Bold", 40)
        canvas.translate(width / 2, height / 2)
        canvas.rotate(30)
        canvas.drawCentredString(0, 0, "UNREGISTERED COPY")
        canvas.restoreState()

    # footer band
    canvas.setFillColor(DARKBAND)
    canvas.rect(0, 0, width, 13 * mm, stroke=0, fill=1)
    canvas.setFillColor(colors.HexColor("#9AA7C7"))
    canvas.setFont("Helvetica", 8.5)
    canvas.drawString(20 * mm, 5 * mm, "Attribo - local-first screening")
    canvas.drawRightString(width - 20 * mm, 5 * mm, "Attribo")

    canvas.showPage()
    canvas.save()
