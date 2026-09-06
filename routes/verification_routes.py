"""Public verification and digital pass pages."""

from pathlib import Path

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)

from database.models import Visitor
from utils.gate import check_in_visitor, check_out_visitor, verification_state
from utils.pass_generator import generate_pass_pdf

verification_bp = Blueprint("verification", __name__)


@verification_bp.route("/verify", methods=["GET", "POST"])
def verify_form():
    if request.method == "POST":
        pass_id = (request.form.get("pass_id") or "").strip().upper()
        if not pass_id:
            flash("Enter a Pass ID.", "danger")
            return render_template("verify.html")
        return redirect(url_for("verification.verify_pass", pass_id=pass_id))
    return render_template("verify.html")


@verification_bp.route("/verify/<pass_id>")
def verify_pass(pass_id):
    pass_id = (pass_id or "").strip().upper()
    visitor = Visitor.query.filter_by(pass_id=pass_id).first()
    state = verification_state(visitor)
    admin_logged_in = bool(session.get("admin_id"))
    return render_template(
        "verification_result.html",
        visitor=visitor if state != "invalid" else None,
        state=state,
        pass_id=pass_id,
        admin_logged_in=admin_logged_in,
    )


@verification_bp.route("/pass/<pass_id>")
def view_pass(pass_id):
    visitor = Visitor.query.filter_by(pass_id=pass_id).first()
    if visitor is None:
        flash("That visitor pass was not found.", "danger")
        return redirect(url_for("visitor.index"))
    return render_template("visitor_pass.html", visitor=visitor)


@verification_bp.route("/pass/<pass_id>/download")
def download_pass(pass_id):
    visitor = Visitor.query.filter_by(pass_id=pass_id).first()
    if visitor is None:
        flash("That visitor pass was not found.", "danger")
        return redirect(url_for("visitor.index"))

    folder = Path(current_app.config["PASS_FOLDER"])
    filename = visitor.pass_pdf_filename
    pdf_path = folder / filename if filename else None
    if not filename or not pdf_path.exists():
        filename = f"{visitor.pass_id}.pdf"
        photo_path = Path(current_app.config["UPLOAD_FOLDER"]) / (visitor.photo_filename or "")
        qr_path = Path(current_app.config["QR_FOLDER"]) / (visitor.qr_filename or "")
        generate_pass_pdf(
            visitor,
            current_app.config["ORGANIZATION_NAME"],
            photo_path,
            qr_path,
            folder / filename,
        )
        visitor.pass_pdf_filename = filename
        from database import db

        db.session.commit()

    return send_from_directory(
        folder,
        filename,
        as_attachment=True,
        download_name=f"{visitor.pass_id}.pdf",
    )


@verification_bp.route("/verify/<pass_id>/check-in", methods=["POST"])
def public_check_in(pass_id):
    if not session.get("admin_id"):
        flash("Admin login is required to check visitors in.", "warning")
        return redirect(url_for("admin.login"))
    visitor = Visitor.query.filter_by(pass_id=pass_id).first()
    if visitor is None:
        flash("Invalid Pass ID.", "danger")
        return redirect(url_for("verification.verify_form"))
    ok, message = check_in_visitor(visitor)
    flash(message, "success" if ok else "danger")
    return redirect(url_for("verification.verify_pass", pass_id=pass_id))


@verification_bp.route("/verify/<pass_id>/check-out", methods=["POST"])
def public_check_out(pass_id):
    if not session.get("admin_id"):
        flash("Admin login is required to check visitors out.", "warning")
        return redirect(url_for("admin.login"))
    visitor = Visitor.query.filter_by(pass_id=pass_id).first()
    if visitor is None:
        flash("Invalid Pass ID.", "danger")
        return redirect(url_for("verification.verify_form"))
    ok, message = check_out_visitor(visitor)
    flash(message, "success" if ok else "danger")
    return redirect(url_for("verification.verify_pass", pass_id=pass_id))
