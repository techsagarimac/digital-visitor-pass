"""Create a professional visitor-pass PDF (badge layout)."""

from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

NAVY = HexColor("#16345c")
BLUE = HexColor("#2d6cdf")
PAPER = HexColor("#f4f7fb")
LINE = HexColor("#d7e0ec")
INK = HexColor("#1c2430")
MUTED = HexColor("#5b6778")

STATUS_COLORS = {
    "EXPECTED": HexColor("#1e4b8e"),
    "CHECKED_IN": HexColor("#0f7b4c"),
    "CHECKED_OUT": HexColor("#5b6778"),
    "EXPIRED": HexColor("#b45309"),
    "CANCELLED": HexColor("#b42318"),
}

PAGE_W = 620
PAGE_H = 380


def generate_pass_pdf(visitor, org_name, photo_path, qr_path, output_path):
    """Draw a corporate-style visitor badge and save it as PDF. Returns filename."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(output_path), pagesize=(PAGE_W, PAGE_H))
    c.setTitle(f"Visitor Pass {visitor.pass_id}")

    c.setFillColor(white)
    c.roundRect(8, 8, PAGE_W - 16, PAGE_H - 16, 12, fill=1, stroke=0)

    c.setFillColor(NAVY)
    c.rect(8, PAGE_H - 64, PAGE_W - 16, 56, fill=1, stroke=0)

    c.setFillColor(BLUE)
    c.rect(8, 8, 14, PAGE_H - 16, fill=1, stroke=0)

    _draw_placeholder_logo(c, 30, PAGE_H - 50)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(58, PAGE_H - 32, org_name.upper())
    c.setFont("Helvetica-Bold", 18)
    c.drawRightString(PAGE_W - 24, PAGE_H - 36, "VISITOR PASS")

    photo = _safe_image(photo_path)
    if photo:
        c.drawImage(photo, 36, 78, width=118, height=148, preserveAspectRatio=True, mask="auto")
    else:
        c.setFillColor(PAPER)
        c.rect(36, 78, 118, 148, fill=1, stroke=0)
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 9)
        c.drawCentredString(95, 148, "PHOTO")

    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(170, 210, visitor.full_name)

    c.setFillColor(MUTED)
    c.setFont("Helvetica", 9)
    c.drawString(170, 194, "PASS ID")
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(170, 178, visitor.pass_id)

    details = [
        ("Organization", visitor.organization),
        ("Person to visit", visitor.host_name),
        ("Purpose", visitor.purpose),
        ("Visit date", visitor.visit_date.strftime("%d %b %Y")),
        ("Entry / Exit", f"{visitor.expected_entry.strftime('%H:%M')} – {visitor.expected_exit.strftime('%H:%M')}"),
    ]
    y = 154
    for label, value in details:
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 8)
        c.drawString(170, y, label.upper())
        c.setFillColor(INK)
        c.setFont("Helvetica", 10)
        c.drawString(170, y - 13, str(value)[:42])
        y -= 30

    qr = _safe_image(qr_path)
    if qr:
        c.drawImage(qr, PAGE_W - 156, 88, width=118, height=118, mask="auto")

    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawCentredString(PAGE_W - 97, 78, "Scan to verify")

    status = visitor.status or "EXPECTED"
    c.setFillColor(STATUS_COLORS.get(status, NAVY))
    c.roundRect(36, 28, 130, 28, 6, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(101, 38, status.replace("_", " "))

    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawString(180, 36, "Present this pass at the security desk. Not transferable.")

    c.showPage()
    c.save()
    return output_path.name


def _safe_image(path):
    if not path:
        return None
    path = Path(path)
    if not path.exists():
        return None
    try:
        return ImageReader(str(path))
    except Exception:
        return None


def _draw_placeholder_logo(c, x, y):
    """Generic institute mark — not a real-world logo."""
    c.setFillColor(white)
    c.roundRect(x, y, 22, 16, 2, fill=1, stroke=0)
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(x + 11, y + 5, "AIT")
