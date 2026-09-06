"""QR codes contain only the public verification URL, never personal data."""

from pathlib import Path

import qrcode


def generate_qr_code(pass_id, qr_folder, base_url):
    """Save a PNG QR code that opens /verify/<pass_id>. Returns the filename."""
    verify_url = f"{base_url.rstrip('/')}/verify/{pass_id}"
    filename = f"{pass_id}.png"
    output_path = Path(qr_folder) / filename

    qr = qrcode.QRCode(version=2, box_size=8, border=2)
    qr.add_data(verify_url)
    qr.make(fit=True)
    image = qr.make_image(fill_color="#16345c", back_color="white")
    image.save(output_path)
    return filename
