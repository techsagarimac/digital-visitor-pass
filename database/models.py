"""Database models for visitors and demo admin accounts."""

from datetime import datetime, date

from werkzeug.security import check_password_hash, generate_password_hash

from database import db


class VisitorStatus:
    EXPECTED = "EXPECTED"
    CHECKED_IN = "CHECKED_IN"
    CHECKED_OUT = "CHECKED_OUT"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"

    ALL = (EXPECTED, CHECKED_IN, CHECKED_OUT, EXPIRED, CANCELLED)


class Visitor(db.Model):
    __tablename__ = "visitors"

    id = db.Column(db.Integer, primary_key=True)
    pass_id = db.Column(db.String(32), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(120), nullable=False)
    mobile = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    organization = db.Column(db.String(120), nullable=False)
    host_name = db.Column(db.String(120), nullable=False)
    purpose = db.Column(db.String(255), nullable=False)
    purpose_category = db.Column(db.String(50), nullable=True)
    visit_date = db.Column(db.Date, nullable=False)
    expected_entry = db.Column(db.Time, nullable=False)
    expected_exit = db.Column(db.Time, nullable=False)
    photo_filename = db.Column(db.String(255), nullable=True)
    qr_filename = db.Column(db.String(255), nullable=True)
    pass_pdf_filename = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), nullable=False, default=VisitorStatus.EXPECTED)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    check_in_time = db.Column(db.DateTime, nullable=True)
    check_out_time = db.Column(db.DateTime, nullable=True)

    def is_expired(self):
        """A pass is expired if the visit date is in the past and the visitor never checked in."""
        if self.status in (VisitorStatus.CHECKED_OUT, VisitorStatus.CANCELLED):
            return False
        if self.status == VisitorStatus.EXPIRED:
            return True
        return self.visit_date < date.today() and self.status == VisitorStatus.EXPECTED

    def status_label(self):
        return (self.status or "").replace("_", " ").title()


class Admin(db.Model):
    """Simple admin account. Passwords are stored as hashes, never as plain text."""

    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
