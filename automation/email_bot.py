"""Email automation wrapper used by the RPA module and registration flow."""

from flask import current_app

from utils.email_sender import email_is_configured, send_email


def send_registration_emails(visitor):
    """
    Send visitor confirmation and a host/reception copy.

    Returns a dict describing what was sent or skipped.
    """
    result = {"configured": email_is_configured(), "visitor": False, "host": False}
    if not result["configured"]:
        return result

    org = current_app.config["ORGANIZATION_NAME"]
    base_url = current_app.config["BASE_URL"].rstrip("/")
    verify_url = f"{base_url}/verify/{visitor.pass_id}"

    visitor_body = (
        f"Hello {visitor.full_name},\n\n"
        f"Your visitor pass for {org} is ready.\n\n"
        f"Pass ID: {visitor.pass_id}\n"
        f"Visit date: {visitor.visit_date.strftime('%d %b %Y')}\n"
        f"Expected entry: {visitor.expected_entry.strftime('%H:%M')}\n"
        f"Person to visit: {visitor.host_name}\n\n"
        f"Show your digital pass at the security desk. "
        f"Security can verify it here:\n{verify_url}\n\n"
        f"This is an automated message.\n"
    )
    result["visitor"] = send_email(
        visitor.email,
        "Visitor Pass Confirmation",
        visitor_body,
    )

    reception = current_app.config.get("MAIL_FROM")
    host_body = (
        f"A visitor has been registered to meet {visitor.host_name}.\n\n"
        f"Visitor: {visitor.full_name}\n"
        f"Organization: {visitor.organization}\n"
        f"Purpose: {visitor.purpose}\n"
        f"Pass ID: {visitor.pass_id}\n"
        f"Visit date: {visitor.visit_date.strftime('%d %b %Y')}\n"
        f"Expected entry: {visitor.expected_entry.strftime('%H:%M')}\n"
        f"Verify: {verify_url}\n"
    )
    result["host"] = send_email(
        reception,
        f"Visitor arriving: {visitor.full_name}",
        host_body,
    )
    return result
