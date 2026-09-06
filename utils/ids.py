"""Unique visitor Pass ID helper. Example: VIS-2026-00001."""

from datetime import date

from database.models import Visitor


def generate_pass_id():
    year_num = date.today().year
    prefix = f"VIS-{year_num}-"
    last = (
        Visitor.query.filter(Visitor.pass_id.like(f"{prefix}%"))
        .order_by(Visitor.id.desc())
        .first()
    )
    next_number = 1
    if last:
        try:
            next_number = int(last.pass_id.rsplit("-", 1)[-1]) + 1
        except ValueError:
            next_number = 1
    return f"{prefix}{next_number:05d}"
