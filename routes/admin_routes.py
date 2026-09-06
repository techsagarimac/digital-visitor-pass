"""Admin login, dashboard, visitor list, reports, and gate actions."""

import csv
import io
from datetime import date, datetime
from functools import wraps
from io import BytesIO

from flask import (
    Blueprint,
    Response,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy import func, or_

from database.models import Admin, Visitor, VisitorStatus
from utils.gate import check_in_visitor, check_out_visitor

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
PER_PAGE = 10


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            flash("Please log in with an admin account.", "warning")
            return redirect(url_for("admin.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin_id"):
        return redirect(url_for("admin.dashboard"))
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        admin = Admin.query.filter_by(username=username).first()
        if admin is None or not admin.check_password(password):
            flash("Invalid username or password.", "danger")
            return render_template("admin_login.html"), 401
        session.clear()
        session["admin_id"] = admin.id
        session["admin_username"] = admin.username
        flash("Signed in as admin.", "success")
        next_url = request.args.get("next")
        if next_url and next_url.startswith("/"):
            return redirect(next_url)
        return redirect(url_for("admin.dashboard"))
    return render_template("admin_login.html")


@admin_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("visitor.index"))


@admin_bp.route("/")
@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    today = date.today()
    stats = {
        "total": Visitor.query.count(),
        "today": Visitor.query.filter(Visitor.visit_date == today).count(),
        "inside": Visitor.query.filter(Visitor.status == VisitorStatus.CHECKED_IN).count(),
        "expected": Visitor.query.filter(Visitor.status == VisitorStatus.EXPECTED).count(),
        "checked_out": Visitor.query.filter(Visitor.status == VisitorStatus.CHECKED_OUT).count(),
    }
    query = _filtered_query()
    page = request.args.get("page", 1, type=int)
    pagination = query.order_by(Visitor.created_at.desc()).paginate(
        page=page, per_page=PER_PAGE, error_out=False
    )
    hosts = [
        row[0]
        for row in Visitor.query.with_entities(Visitor.host_name).distinct().order_by(Visitor.host_name)
    ]
    return render_template(
        "dashboard.html",
        stats=stats,
        visitors=pagination.items,
        pagination=pagination,
        hosts=hosts,
        filters={
            "q": request.args.get("q", ""),
            "status": request.args.get("status", ""),
            "visit_date": request.args.get("visit_date", ""),
            "host": request.args.get("host", ""),
        },
        statuses=VisitorStatus.ALL,
    )


@admin_bp.route("/visitors/<pass_id>")
@admin_required
def visitor_details(pass_id):
    visitor = Visitor.query.filter_by(pass_id=pass_id).first()
    if visitor is None:
        flash("Visitor not found.", "danger")
        return redirect(url_for("admin.dashboard"))
    return render_template("visitor_details.html", visitor=visitor)


@admin_bp.route("/visitors/<pass_id>/check-in", methods=["POST"])
@admin_required
def check_in(pass_id):
    visitor = Visitor.query.filter_by(pass_id=pass_id).first()
    if visitor is None:
        flash("Visitor not found.", "danger")
        return redirect(url_for("admin.dashboard"))
    ok, message = check_in_visitor(visitor)
    flash(message, "success" if ok else "danger")
    return redirect(request.referrer or url_for("admin.dashboard"))


@admin_bp.route("/visitors/<pass_id>/check-out", methods=["POST"])
@admin_required
def check_out(pass_id):
    visitor = Visitor.query.filter_by(pass_id=pass_id).first()
    if visitor is None:
        flash("Visitor not found.", "danger")
        return redirect(url_for("admin.dashboard"))
    ok, message = check_out_visitor(visitor)
    flash(message, "success" if ok else "danger")
    return redirect(request.referrer or url_for("admin.dashboard"))


@admin_bp.route("/reports")
@admin_required
def reports():
    today = date.today()
    summary = {
        "daily_count": Visitor.query.filter(Visitor.visit_date == today).count(),
        "checked_in": Visitor.query.filter(Visitor.status == VisitorStatus.CHECKED_IN).count(),
        "checked_out": Visitor.query.filter(Visitor.status == VisitorStatus.CHECKED_OUT).count(),
        "expected": Visitor.query.filter(Visitor.status == VisitorStatus.EXPECTED).count(),
        "total": Visitor.query.count(),
    }
    by_status = (
        Visitor.query.with_entities(Visitor.status, func.count(Visitor.id))
        .group_by(Visitor.status)
        .all()
    )
    recent = (
        Visitor.query.filter(Visitor.visit_date == today)
        .order_by(Visitor.created_at.desc())
        .limit(20)
        .all()
    )
    return render_template("reports.html", summary=summary, by_status=by_status, recent=recent, today=today)


@admin_bp.route("/reports/export.csv")
@admin_required
def export_csv():
    visitors = _filtered_query().order_by(Visitor.created_at.desc()).all()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "Pass ID",
            "Full Name",
            "Organization",
            "Host",
            "Purpose",
            "Category",
            "Visit Date",
            "Entry",
            "Exit",
            "Status",
            "Check In",
            "Check Out",
        ]
    )
    for visitor in visitors:
        writer.writerow(
            [
                visitor.pass_id,
                visitor.full_name,
                visitor.organization,
                visitor.host_name,
                visitor.purpose,
                visitor.purpose_category or "",
                visitor.visit_date.isoformat(),
                visitor.expected_entry.strftime("%H:%M"),
                visitor.expected_exit.strftime("%H:%M"),
                visitor.status,
                visitor.check_in_time.isoformat(sep=" ", timespec="minutes") if visitor.check_in_time else "",
                visitor.check_out_time.isoformat(sep=" ", timespec="minutes") if visitor.check_out_time else "",
            ]
        )
    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=visitor-report.csv"},
    )


@admin_bp.route("/reports/export.pdf")
@admin_required
def export_pdf():
    today = date.today()
    visitors = Visitor.query.filter(Visitor.visit_date == today).order_by(Visitor.full_name).all()
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    pdf.setTitle("Daily Visitor Report")
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(40, height - 50, "Daily Visitor Report")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(40, height - 68, today.strftime("%d %B %Y"))
    y = height - 100
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(40, y, "Pass ID")
    pdf.drawString(140, y, "Name")
    pdf.drawString(280, y, "Host")
    pdf.drawString(400, y, "Status")
    y -= 16
    pdf.setFont("Helvetica", 9)
    for visitor in visitors:
        if y < 50:
            pdf.showPage()
            y = height - 50
            pdf.setFont("Helvetica", 9)
        pdf.drawString(40, y, visitor.pass_id)
        pdf.drawString(140, y, visitor.full_name[:22])
        pdf.drawString(280, y, visitor.host_name[:18])
        pdf.drawString(400, y, visitor.status)
        y -= 14
    if not visitors:
        pdf.drawString(40, y, "No visitors scheduled for today.")
    pdf.save()
    buffer.seek(0)
    return Response(
        buffer.getvalue(),
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment; filename=visitor-report.pdf"},
    )


def _filtered_query():
    query = Visitor.query
    search = (request.args.get("q") or "").strip()
    status = (request.args.get("status") or "").strip()
    visit_date = (request.args.get("visit_date") or "").strip()
    host = (request.args.get("host") or "").strip()
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                Visitor.pass_id.ilike(like),
                Visitor.full_name.ilike(like),
                Visitor.organization.ilike(like),
                Visitor.host_name.ilike(like),
            )
        )
    if status:
        query = query.filter(Visitor.status == status)
    if visit_date:
        try:
            parsed = datetime.strptime(visit_date, "%Y-%m-%d").date()
            query = query.filter(Visitor.visit_date == parsed)
        except ValueError:
            pass
    if host:
        query = query.filter(Visitor.host_name == host)
    return query
