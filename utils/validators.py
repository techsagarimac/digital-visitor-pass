"""Input validation for visitor registration."""

import re
from datetime import date, datetime, time

from flask import current_app

EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
MOBILE_PATTERN = re.compile(r"^\+?[0-9]{10,15}$")
NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z .'-]{1,118}$")


def _clean(value):
    return (value or "").strip()


def allowed_image(filename):
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in current_app.config["ALLOWED_EXTENSIONS"]


def parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def parse_time(value):
    try:
        return datetime.strptime(value, "%H:%M").time()
    except (TypeError, ValueError):
        try:
            return datetime.strptime(value, "%H:%M:%S").time()
        except (TypeError, ValueError):
            return None


def validate_registration(form, files):
    """Return a list of error messages. Empty list means the form is valid."""
    errors = []

    full_name = _clean(form.get("full_name"))
    mobile = re.sub(r"[\s-]", "", _clean(form.get("mobile")))
    email = _clean(form.get("email")).lower()
    organization = _clean(form.get("organization"))
    host_name = _clean(form.get("host_name"))
    purpose = _clean(form.get("purpose"))
    visit_date = parse_date(form.get("visit_date"))
    expected_entry = parse_time(form.get("expected_entry"))
    expected_exit = parse_time(form.get("expected_exit"))
    photo = files.get("photo")

    if not full_name:
        errors.append("Full name is required.")
    elif not NAME_PATTERN.match(full_name):
        errors.append("Enter a valid full name (letters only).")

    if not mobile:
        errors.append("Mobile number is required.")
    elif not MOBILE_PATTERN.match(mobile):
        errors.append("Enter a valid mobile number (10 to 15 digits).")

    if not email:
        errors.append("Email is required.")
    elif not EMAIL_PATTERN.match(email):
        errors.append("Enter a valid email address.")

    if not organization:
        errors.append("Visitor organization is required.")
    elif len(organization) > 120:
        errors.append("Organization name is too long.")

    if not host_name:
        errors.append("Person to visit is required.")
    elif not NAME_PATTERN.match(host_name):
        errors.append("Enter a valid host name (letters only).")

    if not purpose:
        errors.append("Purpose of visit is required.")
    elif len(purpose) > 255:
        errors.append("Purpose must be 255 characters or fewer.")

    if visit_date is None:
        errors.append("Visit date is required and must be a valid date.")
    elif visit_date < date.today():
        errors.append("Visit date cannot be in the past.")

    if expected_entry is None:
        errors.append("Expected entry time is required.")
    if expected_exit is None:
        errors.append("Expected exit time is required.")
    if expected_entry and expected_exit and expected_exit <= expected_entry:
        errors.append("Expected exit time must be after entry time.")

    if photo is None or not photo.filename:
        errors.append("Visitor photo is required.")
    elif not allowed_image(photo.filename):
        errors.append("Photo must be a JPG or PNG image.")

    return errors


def cleaned_registration(form):
    """Return sanitized field values after validation has already passed."""
    return {
        "full_name": _clean(form.get("full_name")),
        "mobile": re.sub(r"[\s-]", "", _clean(form.get("mobile"))),
        "email": _clean(form.get("email")).lower(),
        "organization": _clean(form.get("organization")),
        "host_name": _clean(form.get("host_name")),
        "purpose": _clean(form.get("purpose")),
        "visit_date": parse_date(form.get("visit_date")),
        "expected_entry": parse_time(form.get("expected_entry")),
        "expected_exit": parse_time(form.get("expected_exit")),
    }
