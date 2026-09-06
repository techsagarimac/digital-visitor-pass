"""Shared visitor registration pipeline used by Flask routes and the RPA bot."""

from pathlib import Path
from shutil import copyfileobj

from flask import current_app
from werkzeug.utils import secure_filename

from database import db
from database.models import Visitor, VisitorStatus
from utils.classifier import classify_purpose
from utils.ids import generate_pass_id
from utils.pass_generator import generate_pass_pdf
from utils.qr_generator import generate_qr_code


def is_duplicate_visit(email, visit_date, host_name):
    return (
        Visitor.query.filter_by(email=email, visit_date=visit_date, host_name=host_name)
        .filter(Visitor.status != VisitorStatus.CANCELLED)
        .first()
        is not None
    )


def register_visitor(data, photo_file):
    """
    Create a visitor record, save the photo, generate QR + PDF.

    data: dict from cleaned_registration()
    photo_file: Werkzeug FileStorage or a file-like object with .filename and .save/.read
    """
    if is_duplicate_visit(data["email"], data["visit_date"], data["host_name"]):
        raise ValueError(
            "A visitor with this email is already registered for this host on this date."
        )

    pass_id = generate_pass_id()
    original_name = secure_filename(getattr(photo_file, "filename", "") or "photo.jpg")
    extension = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else "jpg"
    if extension not in current_app.config["ALLOWED_EXTENSIONS"]:
        extension = "jpg"

    photo_filename = f"{pass_id}.{extension}"
    photo_path = Path(current_app.config["UPLOAD_FOLDER"]) / photo_filename
    _save_upload(photo_file, photo_path)

    visitor = Visitor(
        pass_id=pass_id,
        full_name=data["full_name"],
        mobile=data["mobile"],
        email=data["email"],
        organization=data["organization"],
        host_name=data["host_name"],
        purpose=data["purpose"],
        purpose_category=classify_purpose(data["purpose"]),
        visit_date=data["visit_date"],
        expected_entry=data["expected_entry"],
        expected_exit=data["expected_exit"],
        photo_filename=photo_filename,
        status=VisitorStatus.EXPECTED,
    )
    db.session.add(visitor)
    db.session.commit()

    try:
        visitor.qr_filename = generate_qr_code(
            pass_id,
            current_app.config["QR_FOLDER"],
            current_app.config["BASE_URL"],
        )
        pdf_filename = f"{pass_id}.pdf"
        pdf_path = Path(current_app.config["PASS_FOLDER"]) / pdf_filename
        qr_path = Path(current_app.config["QR_FOLDER"]) / visitor.qr_filename
        generate_pass_pdf(
            visitor,
            current_app.config["ORGANIZATION_NAME"],
            photo_path,
            qr_path,
            pdf_path,
        )
        visitor.pass_pdf_filename = pdf_filename
        db.session.commit()
    except Exception:
        db.session.rollback()
        db.session.add(visitor)
        db.session.commit()

    return visitor


def _save_upload(photo_file, photo_path):
    if hasattr(photo_file, "save"):
        photo_file.save(photo_path)
        return
    photo_path.parent.mkdir(parents=True, exist_ok=True)
    with open(photo_path, "wb") as handle:
        copyfileobj(photo_file, handle)
