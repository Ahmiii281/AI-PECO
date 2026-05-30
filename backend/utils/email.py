"""
Email utility for AI-PECO.

Sends password reset emails via SMTP (TLS).
Falls back to structured log output if SMTP is not configured — useful for
development and viva demonstrations where a mail server is unavailable.

Usage:
    from utils.email import send_password_reset_email
    await send_password_reset_email(email, reset_token)
"""

import asyncio
import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from config import settings

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# HTML email template
# ─────────────────────────────────────────────────────────────────────────────

def _build_reset_email_html(reset_url: str, expiry_hours: int = 1) -> str:
    """Return branded HTML for the password reset email."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Reset Your AI-PECO Password</title>
</head>
<body style="margin:0;padding:0;background-color:#0f172a;font-family:Inter,Segoe UI,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0">
    <tr>
      <td align="center" style="padding:40px 20px;">
        <table width="560" cellpadding="0" cellspacing="0" border="0"
               style="background-color:#1e293b;border-radius:12px;overflow:hidden;border:1px solid #334155;">
          <!-- Header -->
          <tr>
            <td style="padding:32px 40px;background:linear-gradient(135deg,#065f46,#064e3b);text-align:center;">
              <h1 style="color:#34d399;margin:0;font-size:24px;font-weight:700;letter-spacing:-0.5px;">
                ⚡ AI-PECO
              </h1>
              <p style="color:#a7f3d0;margin:8px 0 0;font-size:13px;">
                AI-Powered Energy Consumption Optimizer
              </p>
            </td>
          </tr>
          <!-- Body -->
          <tr>
            <td style="padding:40px;">
              <h2 style="color:#f1f5f9;margin:0 0 16px;font-size:20px;font-weight:600;">
                Password Reset Request
              </h2>
              <p style="color:#94a3b8;line-height:1.6;margin:0 0 24px;">
                We received a request to reset the password for your AI-PECO account.
                Click the button below to set a new password. This link is valid for
                <strong style="color:#e2e8f0;">{expiry_hours} hour(s)</strong>.
              </p>
              <table cellpadding="0" cellspacing="0" border="0" width="100%">
                <tr>
                  <td align="center" style="padding:8px 0 32px;">
                    <a href="{reset_url}"
                       style="display:inline-block;background-color:#10b981;color:#000000;
                              text-decoration:none;font-weight:700;font-size:15px;
                              padding:14px 36px;border-radius:8px;letter-spacing:0.3px;">
                      Reset My Password
                    </a>
                  </td>
                </tr>
              </table>
              <p style="color:#64748b;font-size:13px;line-height:1.6;margin:0 0 16px;">
                If the button doesn't work, copy and paste this URL into your browser:
              </p>
              <p style="word-break:break-all;background:#0f172a;color:#34d399;
                        font-family:monospace;font-size:12px;padding:12px;
                        border-radius:6px;border:1px solid #1e293b;margin:0 0 32px;">
                {reset_url}
              </p>
              <hr style="border:none;border-top:1px solid #334155;margin:0 0 24px;" />
              <p style="color:#64748b;font-size:12px;line-height:1.6;margin:0;">
                If you did not request a password reset, please ignore this email.
                Your password will <strong>not</strong> be changed.<br/><br/>
                For security, this link will expire in {expiry_hours} hour(s).
              </p>
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="padding:20px 40px;background-color:#0f172a;text-align:center;">
              <p style="color:#475569;font-size:11px;margin:0;">
                © 2025 AI-PECO &nbsp;|&nbsp; AI-Powered Energy Monitoring
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _build_reset_email_plain(reset_url: str, expiry_hours: int = 1) -> str:
    """Plain-text fallback for email clients that do not render HTML."""
    return (
        f"AI-PECO — Password Reset\n"
        f"{'=' * 40}\n\n"
        f"We received a request to reset your AI-PECO password.\n\n"
        f"Click the link below (valid for {expiry_hours} hour(s)):\n\n"
        f"{reset_url}\n\n"
        f"If you did not request this, please ignore this message.\n"
        f"Your password will not be changed.\n\n"
        f"— The AI-PECO Team"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Core sender
# ─────────────────────────────────────────────────────────────────────────────

def _send_smtp(to_email: str, subject: str, html_body: str, plain_body: str) -> None:
    """
    Send an email synchronously via SMTP/TLS.
    Raises on failure so the caller can decide how to handle it.
    """
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"AI-PECO <{settings.SMTP_FROM}>"
    msg["To"] = to_email

    msg.attach(MIMEText(plain_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    context = ssl.create_default_context()

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
        if settings.SMTP_USE_TLS:
            server.starttls(context=context)
        server.login(settings.SMTP_USER, settings.SMTP_PASS)
        server.sendmail(settings.SMTP_FROM, to_email, msg.as_string())


async def send_password_reset_email(
    to_email: str,
    reset_token: str,
    expiry_hours: int = 1,
) -> bool:
    """
    Send a password reset email.

    Behaviour:
    - If SMTP is configured (SMTP_HOST, SMTP_USER, SMTP_PASS are all set),
      delivers the email via SMTP/TLS in a thread pool so the async event
      loop is not blocked.
    - If SMTP is not configured, logs the reset URL at WARNING level.
      This is safe for development and viva demonstrations.

    Returns True if the email was sent (or logged), False if an error occurred.
    """
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    subject = "Reset your AI-PECO password"
    html_body = _build_reset_email_html(reset_url, expiry_hours)
    plain_body = _build_reset_email_plain(reset_url, expiry_hours)

    if not settings.smtp_configured:
        # Development / demo fallback — never expose token in production logs
        if settings.DEBUG:
            logger.warning(
                "SMTP not configured — password reset URL (DEV ONLY):\n%s", reset_url
            )
        else:
            # In production without SMTP, log that the email could not be sent
            # but do NOT expose the token.
            logger.error(
                "SMTP not configured. Password reset email could not be sent to %s. "
                "Configure SMTP_HOST, SMTP_USER, SMTP_PASS in environment variables.",
                to_email,
            )
        return True  # Return True so the API still returns 200 (prevents email enumeration)

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, _send_smtp, to_email, subject, html_body, plain_body
        )
        logger.info("Password reset email sent to %s", to_email)
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error(
            "SMTP authentication failed. Check SMTP_USER and SMTP_PASS in .env."
        )
    except smtplib.SMTPConnectError:
        logger.error(
            "Cannot connect to SMTP server %s:%d. Check SMTP_HOST and SMTP_PORT.",
            settings.SMTP_HOST,
            settings.SMTP_PORT,
        )
    except Exception as exc:
        logger.error("Failed to send password reset email: %s", exc)

    return False
