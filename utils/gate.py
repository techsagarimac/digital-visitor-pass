"""Check-in and check-out rules for visitor passes."""

from datetime import date, datetime

from database import db
from database.models import Visitor, VisitorStatus


def refresh_expiry(visitor):
    """Mark EXPECTED passes as EXPIRED when the visit date has passed."""
    if visitor and visitor.is_expired() and visitor.status == VisitorStatus.EXPECTED:
        visitor.status = VisitorStatus.EXPIRED
        db.session.commit()
    return visitor


def check_in_visitor(visitor):
    """Return (ok, message)."""
    refresh_expiry(visitor)
    if visitor.status == VisitorStatus.CANCELLED:
        return False, "This pass has been cancelled."
    if visitor.status == VisitorStatus.EXPIRED:
        return False, "This pass has expired."
    if visitor.status == VisitorStatus.CHECKED_IN:
        return False, "This visitor is already checked in."
    if visitor.status == VisitorStatus.CHECKED_OUT:
        return False, "This visitor has already checked out."
    if visitor.visit_date != date.today():
        return False, "Check-in is only allowed on the visit date."
    if visitor.status != VisitorStatus.EXPECTED:
        return False, "This pass cannot be used for check-in."

    visitor.status = VisitorStatus.CHECKED_IN
    visitor.check_in_time = datetime.utcnow()
    db.session.commit()
    return True, f"{visitor.full_name} is checked in."


def check_out_visitor(visitor):
    """Return (ok, message)."""
    if visitor.status == VisitorStatus.CANCELLED:
        return False, "This pass has been cancelled."
    if visitor.status != VisitorStatus.CHECKED_IN:
        return False, "Visitor must be checked in before check-out."

    visitor.status = VisitorStatus.CHECKED_OUT
    visitor.check_out_time = datetime.utcnow()
    db.session.commit()
    return True, f"{visitor.full_name} is checked out."


def verification_state(visitor):
    """Public verification outcome: valid, expired, or invalid."""
    if visitor is None:
        return "invalid"
    refresh_expiry(visitor)
    if visitor.status == VisitorStatus.CANCELLED:
        return "invalid"
    if visitor.status == VisitorStatus.EXPIRED:
        return "expired"
    return "valid"
