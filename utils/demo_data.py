"""Create about 10 clearly fake sample visitors for demonstrations."""

from datetime import date, datetime, time, timedelta
from pathlib import Path

from flask import current_app
from PIL import Image, ImageDraw

from database import db
from database.models import Visitor, VisitorStatus
from utils.classifier import classify_purpose
from utils.ids import generate_pass_id
from utils.pass_generator import generate_pass_pdf
from utils.qr_generator import generate_qr_code


DEMO_VISITORS = [
    {
        "full_name": "Priya Nair",
        "mobile": "9000000001",
        "email": "priya.nair.demo@example.com",
        "organization": "Nimbus Software",
        "host_name": "Anita Sharma",
        "purpose": "Interview for software developer position",
        "status": VisitorStatus.EXPECTED,
        "day_offset": 0,
        "entry": time(10, 0),
        "exit": time(12, 0),
    },
    {
        "full_name": "Arjun Mehta",
        "mobile": "9000000002",
        "email": "arjun.mehta.demo@example.com",
        "organization": "Harbor Analytics",
        "host_name": "Rahul Verma",
        "purpose": "Meeting with project manager",
        "status": VisitorStatus.CHECKED_IN,
        "day_offset": 0,
        "entry": time(9, 30),
        "exit": time(11, 30),
    },
    {
        "full_name": "Sneha Iyer",
        "mobile": "9000000003",
        "email": "sneha.iyer.demo@example.com",
        "organization": "ParcelPoint Logistics",
        "host_name": "Front Desk",
        "purpose": "Delivering a package",
        "status": VisitorStatus.CHECKED_OUT,
        "day_offset": 0,
        "entry": time(8, 45),
        "exit": time(9, 15),
    },
    {
        "full_name": "Rohan Kapoor",
        "mobile": "9000000004",
        "email": "rohan.kapoor.demo@example.com",
        "organization": "City College of Engineering",
        "host_name": "Dr Meera Joshi",
        "purpose": "College project discussion",
        "status": VisitorStatus.EXPECTED,
        "day_offset": 0,
        "entry": time(14, 0),
        "exit": time(16, 0),
    },
    {
        "full_name": "Kabir Khan",
        "mobile": "9000000005",
        "email": "kabir.khan.demo@example.com",
        "organization": "CoolAir Services",
        "host_name": "Facilities Office",
        "purpose": "Maintenance work on lab air conditioning",
        "status": VisitorStatus.CHECKED_IN,
        "day_offset": 0,
        "entry": time(11, 0),
        "exit": time(15, 0),
    },
    {
        "full_name": "Ananya Reddy",
        "mobile": "9000000006",
        "email": "ananya.reddy.demo@example.com",
        "organization": "BrightPath Recruiters",
        "host_name": "Anita Sharma",
        "purpose": "Campus placement interview",
        "status": VisitorStatus.EXPECTED,
        "day_offset": 1,
        "entry": time(10, 30),
        "exit": time(12, 30),
    },
    {
        "full_name": "Vikram Desai",
        "mobile": "9000000007",
        "email": "vikram.desai.demo@example.com",
        "organization": "Oakridge Consulting",
        "host_name": "Rahul Verma",
        "purpose": "Client business meeting",
        "status": VisitorStatus.CHECKED_OUT,
        "day_offset": -1,
        "entry": time(13, 0),
        "exit": time(14, 30),
    },
    {
        "full_name": "Tara Sen",
        "mobile": "9000000008",
        "email": "tara.sen.demo@example.com",
        "organization": "Northline Couriers",
        "host_name": "Front Desk",
        "purpose": "Courier parcel drop off",
        "status": VisitorStatus.EXPIRED,
        "day_offset": -2,
        "entry": time(9, 0),
        "exit": time(10, 0),
    },
    {
        "full_name": "Nikhil Rao",
        "mobile": "9000000009",
        "email": "nikhil.rao.demo@example.com",
        "organization": "Self",
        "host_name": "Dr Meera Joshi",
        "purpose": "Research seminar discussion",
        "status": VisitorStatus.CANCELLED,
        "day_offset": 0,
        "entry": time(15, 0),
        "exit": time(16, 30),
    },
    {
        "full_name": "Leela Krishnan",
        "mobile": "9000000010",
        "email": "leela.krishnan.demo@example.com",
        "organization": "Pixel Forge Studio",
        "host_name": "Anita Sharma",
        "purpose": "Meeting to review internship project",
        "status": VisitorStatus.EXPECTED,
        "day_offset": 0,
        "entry": time(16, 0),
        "exit": time(17, 30),
    },
]


def create_demo_data():
    """Insert sample visitors if they are not already present. Returns count created."""
    created = 0
    today = date.today()
    upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
    qr_folder = Path(current_app.config["QR_FOLDER"])
    pass_folder = Path(current_app.config["PASS_FOLDER"])

    for item in DEMO_VISITORS:
        if Visitor.query.filter_by(email=item["email"]).first():
            continue
        pass_id = generate_pass_id()
        photo_filename = f"{pass_id}.jpg"
        _make_placeholder_photo(upload_folder / photo_filename, item["full_name"])
        qr_filename = generate_qr_code(pass_id, qr_folder, current_app.config["BASE_URL"])
        visit_date = today + timedelta(days=item["day_offset"])
        visitor = Visitor(
            pass_id=pass_id,
            full_name=item["full_name"],
            mobile=item["mobile"],
            email=item["email"],
            organization=item["organization"],
            host_name=item["host_name"],
            purpose=item["purpose"],
            purpose_category=classify_purpose(item["purpose"]),
            visit_date=visit_date,
            expected_entry=item["entry"],
            expected_exit=item["exit"],
            photo_filename=photo_filename,
            qr_filename=qr_filename,
            status=item["status"],
        )
        if item["status"] == VisitorStatus.CHECKED_IN:
            visitor.check_in_time = datetime.combine(visit_date, item["entry"])
        if item["status"] == VisitorStatus.CHECKED_OUT:
            visitor.check_in_time = datetime.combine(visit_date, item["entry"])
            visitor.check_out_time = datetime.combine(visit_date, item["exit"])
        db.session.add(visitor)
        db.session.flush()
        pdf_filename = f"{pass_id}.pdf"
        generate_pass_pdf(
            visitor,
            current_app.config["ORGANIZATION_NAME"],
            upload_folder / photo_filename,
            qr_folder / qr_filename,
            pass_folder / pdf_filename,
        )
        visitor.pass_pdf_filename = pdf_filename
        created += 1

    db.session.commit()
    return created


def _make_placeholder_photo(path, name):
    image = Image.new("RGB", (240, 300), (22, 52, 92))
    draw = ImageDraw.Draw(image)
    draw.ellipse((50, 40, 190, 180), fill=(244, 247, 251))
    initials = "".join(part[0] for part in name.split()[:2]).upper()
    draw.text((100, 220), initials, fill=(255, 255, 255))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="JPEG", quality=85)
