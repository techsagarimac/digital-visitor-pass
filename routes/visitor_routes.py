"""Public visitor pages: home, registration, and success."""

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from automation.email_bot import send_registration_emails
from utils.validators import cleaned_registration, validate_registration
from utils.visitor_service import register_visitor

visitor_bp = Blueprint("visitor", __name__)


@visitor_bp.route("/")
def index():
    return render_template("index.html")


@visitor_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    errors = validate_registration(request.form, request.files)
    if errors:
        for message in errors:
            flash(message, "danger")
        return render_template("register.html", form_data=request.form), 400

    data = cleaned_registration(request.form)
    photo = request.files.get("photo")

    try:
        visitor = register_visitor(data, photo)
    except ValueError as exc:
        flash(str(exc), "danger")
        return render_template("register.html", form_data=request.form), 400
    except Exception:
        flash("Could not save this visitor. Please try again.", "danger")
        return render_template("register.html", form_data=request.form), 500

    send_registration_emails(visitor)
    return redirect(url_for("visitor.success", pass_id=visitor.pass_id))


@visitor_bp.route("/success/<pass_id>")
def success(pass_id):
    from database.models import Visitor

    visitor = Visitor.query.filter_by(pass_id=pass_id).first()
    if visitor is None:
        flash("That visitor pass was not found.", "danger")
        return redirect(url_for("visitor.index"))
    return render_template("success.html", visitor=visitor)
