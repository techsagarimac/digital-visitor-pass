"""
RPA-style visitor processing bot.

This module is separate from Flask routes. It runs the same pipeline a clerk
would repeat by hand:

    Register → Validate → Create record → Pass ID → QR → PDF → Notify → Status

Playwright is used only for an optional browser demo that fills the public form.
The core bot does not need a browser.
"""

from pathlib import Path

from utils.visitor_service import register_visitor
from utils.validators import cleaned_registration, validate_registration
from automation.email_bot import send_registration_emails


class FileUpload:
    """Tiny stand-in for Flask's FileStorage so the bot can reuse validation."""

    def __init__(self, path):
        self.path = Path(path)
        self.filename = self.path.name

    def save(self, destination):
        Path(destination).write_bytes(self.path.read_bytes())


class VisitorBot:
    """Automates repetitive visitor-pass processing."""

    def process(self, form_data, photo_path):
        """
        form_data: dict matching the registration form field names.
        photo_path: path to a JPG/PNG photo.

        Returns the saved Visitor or raises ValueError on validation errors.
        """
        upload = FileUpload(photo_path)
        files = _FormFiles(upload)
        errors = validate_registration(form_data, files)
        if errors:
            raise ValueError("; ".join(errors))

        data = cleaned_registration(form_data)
        visitor = register_visitor(data, upload)
        send_registration_emails(visitor)
        return visitor


class _FormFiles:
    """Minimal object with .get('photo') for validate_registration()."""

    def __init__(self, upload):
        self.upload = upload

    def get(self, key, default=None):
        if key == "photo":
            return self.upload
        return default


def run_browser_registration(base_url, form_data, photo_path, headless=True):
    """
    Optional Playwright demo: open the site and submit the registration form.

    Requires: pip install playwright && playwright install chromium
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright is not installed. Run: pip install playwright && playwright install chromium"
        ) from exc

    url = base_url.rstrip("/") + "/register"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        page = browser.new_page()
        page.goto(url)
        page.fill("#full_name", form_data["full_name"])
        page.fill("#mobile", form_data["mobile"])
        page.fill("#email", form_data["email"])
        page.fill("#organization", form_data["organization"])
        page.fill("#host_name", form_data["host_name"])
        page.fill("#purpose", form_data["purpose"])
        page.fill("#visit_date", form_data["visit_date"])
        page.fill("#expected_entry", form_data["expected_entry"])
        page.fill("#expected_exit", form_data["expected_exit"])
        page.set_input_files("#photo", str(photo_path))
        page.click("button[type=submit]")
        page.wait_for_url("**/success/**", timeout=15000)
        final_url = page.url
        browser.close()
        return final_url


if __name__ == "__main__":
    print("VisitorBot is a library.")
    print("Use it from Flask, from create_demo_data(), or call process() in a script.")
    print("Optional browser demo: run_browser_registration(base_url, form_data, photo_path)")
