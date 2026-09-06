"""Application configuration. Sensitive values come from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Ensure folders used by the app always exist
for folder in ("instance", "static/uploads", "static/qr", "static/passes"):
    (BASE_DIR / folder).mkdir(parents=True, exist_ok=True)


class Config:
    """Default configuration for local demonstration."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + str(BASE_DIR / "instance" / "visitor.db"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Uploads: photos only, 2 MB limit
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024
    UPLOAD_FOLDER = str(BASE_DIR / "static" / "uploads")
    QR_FOLDER = str(BASE_DIR / "static" / "qr")
    PASS_FOLDER = str(BASE_DIR / "static" / "passes")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

    ORGANIZATION_NAME = os.environ.get(
        "ORGANIZATION_NAME", "Apex Institute of Technology"
    )
    BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:5000").rstrip("/")

    # Demo admin — change these before any real deployment
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

    # Optional SMTP. Email is skipped when host or username is missing.
    SMTP_HOST = os.environ.get("SMTP_HOST", "").strip()
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "").strip()
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "").strip()
    SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes")
    MAIL_FROM = os.environ.get("MAIL_FROM", "").strip()

    # Optional OpenAI key for purpose classification (keyword fallback if absent)
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()

    DEBUG = os.environ.get("FLASK_DEBUG", "1") == "1"
