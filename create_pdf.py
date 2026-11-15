
from pathlib import Path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import re
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Preformatted
)

BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "DESIGN_DOCUMENT.md"
OUTPUT_FILE = BASE_DIR / "DESIGN_DOCUMENT.pdf"


if not INPUT_FILE.exists():
    raise FileNotFoundError(
        "DESIGN_DOCUMENT.md was not found in the project folder."
    )


# Read the Markdown document
document_text = INPUT_FILE.read_text(encoding="utf-8")

FONT_PATH = Path("C:/Windows/Fonts/arial.ttf")
BOLD_FONT_PATH = Path("C:/Windows/Fonts/arialbd.ttf")

pdfmetrics.registerFont(TTFont("ArialUnicode", str(FONT_PATH)))
pdfmetrics.registerFont(TTFont("ArialUnicode-Bold", str(BOLD_FONT_PATH)))
# Set up PDF styles
FONT_PATH = Path("C:/Windows/Fonts/Nirmala.ttf")

pdfmetrics.registerFont(
    TTFont("Nirmala", str(FONT_PATH))
)

styles = getSampleStyleSheet()

styles["Normal"].fontName = "Nirmala"
styles["Title"].fontName = "Nirmala"
styles["Heading1"].fontName = "Nirmala"
styles["Heading2"].fontName = "Nirmala"

styles.add(ParagraphStyle(
    name="DocTitleCustom",
    parent=styles["Title"],
    fontName="Nirmala",
    fontSize=20,
    leading=25,
    alignment=TA_CENTER,
    textColor=colors.HexColor("#17365D"),
    spaceAfter=20
))

styles.add(ParagraphStyle(
    name="Heading1Custom",
    parent=styles["Heading1"],
    fontName="Nirmala",
    fontSize=15,
    leading=19,
    textColor=colors.HexColor("#17365D"),
    spaceBefore=14,
    spaceAfter=8
))

styles.add(ParagraphStyle(
    name="Heading2Custom",
    parent=styles["Heading2"],
    fontName="Nirmala",
    fontSize=12,
    leading=15,
    textColor=colors.HexColor("#24527A"),
    spaceBefore=10,
    spaceAfter=6
))

styles.add(ParagraphStyle(
    name="Heading3Custom",
    parent=styles["Heading3"],
    fontName="Nirmala",
    fontSize=10,
    leading=13,
    spaceBefore=8,
    spaceAfter=5
))

styles.add(ParagraphStyle(
    name="BodyCustom",
    parent=styles["BodyText"],
    fontName="Nirmala",
    fontSize=9,
    leading=13,
    spaceAfter=7
))

styles.add(ParagraphStyle(
    name="BulletCustom",
    parent=styles["BodyText"],
    fontName="Nirmala",
    fontSize=9,
    leading=13,
    leftIndent=14,
    firstLineIndent=-9,
    spaceAfter=4
))

styles.add(ParagraphStyle(
    name="CodeCustom",
    fontName="Nirmala",
    fontSize=7,
    leading=9,
    backColor=colors.HexColor("#F2F2F2"),
    borderPadding=6
))

styles.add(ParagraphStyle(
    name="TableHeaderCustom",
    parent=styles["BodyText"],
    fontName="Nirmala",
    fontSize=8,
    leading=10,
    textColor=colors.white
))

styles.add(ParagraphStyle(
    name="TableCellCustom",
    parent=styles["BodyText"],
    fontName="Nirmala",
    fontSize=7.5,
    leading=10
))


def format_inline(text):
    """Convert basic Markdown inline formatting into ReportLab markup."""

    text = escape(text)

    text = re.sub(
        r"\*\*(.+?)\*\*",
        r"<b>\1</b>",
        text
    )

    text = re.sub(
        r"(?<!\*)\*([^*]+)\*(?!\*)",
        r"<i>\1</i>",
        text
    )

    text = re.sub(
        r"`([^`]+)`",
        r'<font name="Courier">\1</font>',
        text
    )

    return text


def is_table_separator(line):
    """Identify Markdown table separator rows."""

    cells = [cell.strip() for cell in line.strip("|").split("|")]

    return bool(cells) and all(
        re.fullmatch(r":?-{3,}:?", cell)
        for cell in cells
    )


def make_table(rows):
    """Create a formatted PDF table."""

    if not rows:
        return None

    column_count = max(len(row) for row in rows)

    cleaned_rows = []

    for row_index, row in enumerate(rows):
        while len(row) < column_count:
            row.append("")

        if row_index == 0:
            cleaned_rows.append([
                Paragraph(format_inline(cell), styles["TableHeaderCustom"])
                for cell in row
            ])
        else:
            cleaned_rows.append([
                Paragraph(format_inline(cell), styles["TableCellCustom"])
                for cell in row
            ])

    available_width = A4[0] - 36 * mm
    column_width = available_width / column_count

    table = Table(
        cleaned_rows,
        colWidths=[column_width] * column_count,
        repeatRows=1,
        hAlign="LEFT"
    )

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17365D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B7C9D6")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
            colors.white,
            colors.HexColor("#F2F6FA")
        ])
    ]))

    return table


def add_page_number(canvas, doc):
    """Add page numbers to the PDF."""

    canvas.saveState()

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)

    canvas.drawCentredString(
        A4[0] / 2,
        10 * mm,
        f"Page {doc.page}"
    )

    canvas.restoreState()


# Build PDF content
story = []
lines = document_text.splitlines()

first_heading = True
inside_code = False
code_lines = []
table_rows = []

def flush_table():
    global table_rows

    if table_rows:
        table = make_table(table_rows)

        if table:
            story.append(Spacer(1, 5))
            story.append(table)
            story.append(Spacer(1, 10))

        table_rows = []


def flush_code():
    global code_lines

    if code_lines:
        code_text = "\n".join(code_lines)

        story.append(Preformatted(
            code_text,
            styles["CodeCustom"],
            maxLineLength=90
        ))

        story.append(Spacer(1, 8))
        code_lines = []


for raw_line in lines:

    line = raw_line.strip()

    # Code block handling
    if line.startswith("```"):

        flush_table()

        if not inside_code:
            inside_code = True
            code_lines = []
        else:
            inside_code = False
            flush_code()

        continue

    if inside_code:
        code_lines.append(raw_line)
        continue

    # Markdown table handling
    if line.startswith("|"):

        if is_table_separator(line):
            continue

        cells = [
            cell.strip()
            for cell in line.strip("|").split("|")
        ]

        table_rows.append(cells)
        continue

    else:
        flush_table()

    # Empty lines
    if not line:
        story.append(Spacer(1, 4))
        continue

    # Main title
    if line.startswith("# "):

        heading = format_inline(line[2:])

        if first_heading:
            story.append(
                Paragraph(heading, styles["DocTitleCustom"])
            )
            first_heading = False
        else:
            story.append(
                Paragraph(heading, styles["Heading1Custom"])
            )

    # Second-level heading
    elif line.startswith("## "):

        story.append(
            Paragraph(
                format_inline(line[3:]),
                styles["Heading2Custom"]
            )
        )

    # Third-level heading
    elif line.startswith("### "):

        story.append(
            Paragraph(
                format_inline(line[4:]),
                styles["Heading3Custom"]
            )
        )

    # Bullet list
    elif line.startswith("- ") or line.startswith("* "):

        story.append(
            Paragraph(
                "&#8226; " + format_inline(line[2:]),
                styles["BulletCustom"]
            )
        )

    # Numbered list
    elif re.match(r"^\d+\.\s+", line):

        item = re.sub(r"^\d+\.\s+", "", line)

        story.append(
            Paragraph(
                format_inline(line.split(".", 1)[0] + ". ")
                + format_inline(item),
                styles["BulletCustom"]
            )
        )

    # Normal paragraph
    else:

        story.append(
            Paragraph(
                format_inline(line),
                styles["BodyCustom"]
            )
        )


# Finish remaining content
flush_table()
flush_code()


# Create the PDF
pdf = SimpleDocTemplate(
    str(OUTPUT_FILE),
    pagesize=A4,
    rightMargin=18 * mm,
    leftMargin=18 * mm,
    topMargin=18 * mm,
    bottomMargin=18 * mm,
    title="PS-025 AML Transaction Monitoring Design Document",
    author="Team T116"
)

pdf.build(
    story,
    onFirstPage=add_page_number,
    onLaterPages=add_page_number
)


if OUTPUT_FILE.exists() and OUTPUT_FILE.stat().st_size > 0:
    print("\nPDF created successfully!")
    print("File:", OUTPUT_FILE.name)
    print("Size:", round(OUTPUT_FILE.stat().st_size / 1024, 2), "KB")
else:
    raise RuntimeError("PDF creation failed.")
