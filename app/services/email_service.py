import logging
import smtplib
import ssl
from email.message import EmailMessage

from ..core.config import get_settings

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str) -> bool:
    """Send a plain-text email through SMTP. Never raises: failures are only logged."""
    settings = get_settings()
    if not settings.SMTP_HOST or not settings.SMTP_FROM:
        logger.error("SMTP is not configured (SMTP_HOST / SMTP_FROM); email to %s was not sent", to)
        return False
    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        if settings.SMTP_SSL:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15,
                                      context=ssl.create_default_context())
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
        with server:
            if not settings.SMTP_SSL and settings.SMTP_STARTTLS:
                server.starttls(context=ssl.create_default_context())
            if settings.SMTP_USER:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD or "")
            server.send_message(msg)
        return True
    except Exception:
        logger.exception("Failed to send email to %s", to)
        return False


def send_password_reset_email(to: str, token: str) -> None:
    settings = get_settings()
    link = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?token={token}"
    if not settings.SMTP_HOST and not settings.is_production:
        logger.warning("Password reset link for %s: %s", to, link)  # local testing without SMTP
        return
    send_email(
        to,
        "Reset your password",
        f"We received a request to reset your password.\n\n{link}\n\n"
        "The link is valid for 1 hour. If you did not request this, ignore this email.",
    )