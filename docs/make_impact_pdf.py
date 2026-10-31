# Orchestral Input Pipeline
# Author: KEYUR SHAILESHKUMAR PATEL
# ORCID: https://orcid.org/0009-0008-5261-043X
# Affiliations: (1) MSc Artificial Intelligence student, Department of Computer Science,
#   Brunel University London, UK; (2) Independent researcher.
# Conducted independently; not an official Brunel University London project.
# Copyright (c) 2026 KEYUR SHAILESHKUMAR PATEL
# Licence: MIT (see LICENSE)
"""Build the plain-language PDFs: docs/impact.pdf (from IMPACT.md) and docs/app_guide.pdf (from APP_GUIDE.md).

Run: python docs/make_impact_pdf.py
"""
import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

HERE = Path(__file__).resolve().parent
INK = colors.HexColor("#1f2933")
ACCENT = colors.HexColor("#2f5d8a")

base = getSampleStyleSheet()
S = {
    "h1": ParagraphStyle("h1", parent=base["Title"], fontSize=20, leading=25, textColor=INK, alignment=TA_LEFT,
                         spaceAfter=10),
    "h2": ParagraphStyle("h2", parent=base["Heading2"], fontSize=13.5, leading=18, textColor=ACCENT,
                         spaceBefore=12, spaceAfter=5),
    "h3": ParagraphStyle("h3", parent=base["Heading3"], fontSize=12, leading=16, textColor=INK,
                         spaceBefore=10, spaceAfter=4),
    "p": ParagraphStyle("p", parent=base["BodyText"], fontSize=10.5, leading=15, textColor=INK, spaceAfter=5),
    "cell": ParagraphStyle("cell", parent=base["BodyText"], fontSize=9, leading=12, textColor=INK),
    "meta": ParagraphStyle("meta", parent=base["BodyText"], fontSize=9.5, leading=13,
                           textColor=colors.HexColor("#52606d")),
}


def inline(text: str) -> str:
    t = html.escape(text)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"\*(.+?)\*", r"<i>\1</i>", t)
    t = re.sub(r"`(.+?)`", r"<font face='Courier'>\1</font>", t)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"<link href='\2' color='#2f5d8a'><u>\1</u></link>", t)
    return t


FRAME_W, FRAME_H = A4[0] - 36 * mm, A4[1] - 40 * mm


def picture(path: Path):
    from PIL import Image as PILImage
    w, h = PILImage.open(path).size
    scale = min(FRAME_W / w, (FRAME_H - 12 * mm) / h)
    return Image(str(path), width=w * scale, height=h * scale)


def build(src: Path, out: Path, title: str = "Impact and credit, in plain words") -> None:
    lines = src.read_text(encoding="utf-8").splitlines()
    story, bullets, numbered, table = [], [], [], []

    def flush():
        nonlocal bullets, numbered, table
        if bullets:
            story.append(ListFlowable([ListItem(Paragraph(inline(b), S["p"]), leftIndent=12) for b in bullets],
                                      bulletType="bullet", start="•", leftIndent=12))
            bullets = []
        if numbered:
            story.append(ListFlowable([ListItem(Paragraph(inline(b), S["p"])) for b in numbered],
                                      bulletType="1", leftIndent=14))
            numbered = []
        if table:
            data = [[Paragraph(inline(c), S["cell"]) for c in row] for row in table]
            n = max(len(r) for r in table)
            widths = [45 * mm, 70 * mm, 55 * mm] if n == 3 else [FRAME_W / n] * n
            t = Table(data, colWidths=widths, repeatRows=1)
            t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd2d9")),
                                   ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eef5")),
                                   ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                   ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
            story.append(t)
            story.append(Spacer(1, 6))
            table = []

    in_code = False
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("```"):
            flush()
            in_code = not in_code
            continue
        if in_code:
            story.append(Paragraph(f"<font face='Courier'>{html.escape(s)}</font>", S["p"]))
            continue
        img = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", s)
        if img:
            flush()
            story.append(Spacer(1, 4))
            story.append(picture(src.parent / img.group(2)))
            story.append(Paragraph(f"<i>{html.escape(img.group(1))}</i>", S["meta"]))
            continue
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if not all(set(c) <= {"-", " "} for c in cells):
                table.append(cells)
            continue
        if s.startswith("- "):
            bullets.append(s[2:])
            continue
        m = re.match(r"\d+\.\s+(.*)", s)
        if m:
            numbered.append(m.group(1))
            continue
        flush()
        if not s:
            continue
        if s.startswith("# "):
            story.append(Paragraph(inline(s[2:]), S["h1"]))
        elif s.startswith("### "):
            story.append(Paragraph(inline(s[4:]), S["h3"]))
        elif s.startswith("## "):
            story.append(Paragraph(inline(s[3:]), S["h2"]))
        elif i < 6:
            story.append(Paragraph(inline(s), S["meta"]))
        else:
            story.append(Paragraph(inline(s), S["p"]))
    flush()

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#7b8794"))
        canvas.drawString(18 * mm, 10 * mm, "KEYUR SHAILESHKUMAR PATEL · ORCID 0009-0008-5261-043X · CC BY 4.0")
        canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Page {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm,
                            bottomMargin=18 * mm, title=title,
                            author="KEYUR SHAILESHKUMAR PATEL")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


if __name__ == "__main__":
    build(HERE / "IMPACT.md", HERE / "impact.pdf")
    print(f"wrote {HERE / 'impact.pdf'}")
    build(HERE / "APP_GUIDE.md", HERE / "app_guide.pdf", title="KeyurTattva Orchestra Studio: app guide")
    print(f"wrote {HERE / 'app_guide.pdf'}")
