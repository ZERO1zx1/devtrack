"""Email delivery via stdlib SMTP.

When ``SMTP_HOST`` is empty (devs without credentials), messages are written
to the server log instead of the wire so the reset flow stays testable. Set
the variables in ``.env`` to send real mail.
"""

import logging
import smtplib
from email.mime.text import MIMEText

from flask import current_app

logger = logging.getLogger("devtrack.mail")


def _settings():
    cfg = current_app.config
    return {
        "host": cfg.get("SMTP_HOST", "").strip(),
        "port": int(cfg.get("SMTP_PORT", 587)),
        "username": cfg.get("SMTP_USERNAME", ""),
        "password": cfg.get("SMTP_PASSWORD", ""),
        "from_addr": cfg.get("SMTP_MAIL_FROM", "") or cfg.get("SMTP_USERNAME", ""),
        "use_tls": bool(cfg.get("SMTP_USE_TLS", True)),
        "use_ssl": bool(cfg.get("SMTP_USE_SSL", False)),
    }


def send_email(to_email, subject, body):
    """Send a plain-text email. Returns ``True`` on success.

    A missing SMTP host (no credentials configured) never fails loudly —
    the message is logged so developers still see what would be sent.
    """
    s = _settings()
    if not s["host"] or not s["from_addr"]:
        logger.warning(
            "SMTP not configured — would send:\nTo: %s\nSubject: %s\n\n%s",
            to_email, subject, body,
        )
        return False

    message = MIMEText(body, "plain", "utf-8")
    message["Subject"] = subject
    message["From"] = s["from_addr"]
    message["To"] = to_email

    try:
        if s["use_ssl"]:
            server = smtplib.SMTP_SSL(s["host"], s["port"], timeout=15)
        else:
            server = smtplib.SMTP(s["host"], s["port"], timeout=15)
        try:
            server.ehlo()
            if s["use_tls"] and not s["use_ssl"]:
                server.starttls()
                server.ehlo()
            if s["username"] and s["password"]:
                server.login(s["username"], s["password"])
            server.sendmail(s["from_addr"], [to_email], message.as_string())
        finally:
            server.quit()
        logger.info("Sent email to %s (subject: %s)", to_email, subject)
        return True
    except Exception:
        logger.exception("Failed to send email to %s", to_email)
        return False


def send_password_reset_email(to_email, username, reset_url):
    """Email a one-time password-reset link."""
    subject = "DevTrack — reset your password"
    body = (
        f"Hi {username},\n\n"
        "Someone asked to reset the password for your DevTrack account.\n\n"
        f"Open this link to choose a new password (valid for 1 hour):\n{reset_url}\n\n"
        "If you didn't request this, you can safely ignore this email.\n\n"
        "— DevTrack"
    )
    return send_email(to_email, subject, body)