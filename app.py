"""
Smart Digital Visitor Pass Generator
Apex Institute of Technology — Visitor Management System
"""

import sys
from pathlib import Path

from flask import Flask, flash, redirect, render_template, url_for
from werkzeug.security import generate_password_hash

from config import Config
from database import db


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(config_class)
    app.config["TRAP_HTTP_EXCEPTIONS"] = False

    for folder_key in ("UPLOAD_FOLDER", "QR_FOLDER", "PASS_FOLDER"):
        Path(app.config[folder_key]).mkdir(parents=True, exist_ok=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    db.init_app(app)

    from routes.admin_routes import admin_bp
    from routes.verification_routes import verification_bp
    from routes.visitor_routes import visitor_bp

    app.register_blueprint(visitor_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(verification_bp)

    with app.app_context():
        from database import models  # noqa: F401

        db.create_all()
        _ensure_demo_admin()

    @app.context_processor
    def inject_globals():
        return {"org_name": app.config["ORGANIZATION_NAME"]}

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("404.html"), 404

    @app.errorhandler(413)
    def too_large(_error):
        flash("The photo is too large. Please upload an image under 2 MB.", "danger")
        return redirect(url_for("visitor.register"))

    @app.errorhandler(500)
    def server_error(_error):
        return render_template("500.html"), 500

    return app


def _ensure_demo_admin():
    """Create the demo admin account if it does not exist.

    Demo credentials (change before any real deployment):
      username: admin
      password: admin123
    """
    from database.models import Admin

    username = Config.ADMIN_USERNAME
    if Admin.query.filter_by(username=username).first():
        return
    admin = Admin(
        username=username,
        password_hash=generate_password_hash(Config.ADMIN_PASSWORD),
    )
    db.session.add(admin)
    db.session.commit()


app = create_app()


if __name__ == "__main__":
    if "--demo-data" in sys.argv:
        with app.app_context():
            from utils.demo_data import create_demo_data

            count = create_demo_data()
            print(f"Demo visitors created: {count}")
    else:
        app.run(host="127.0.0.1", port=5000, debug=Config.DEBUG)
