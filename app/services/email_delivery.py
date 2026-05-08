from __future__ import annotations

from urllib.parse import quote_plus

import httpx

from app.core.config import Settings


def send_password_reset_email(*, settings: Settings, recipient: str, token: str) -> None:
    html = _build_password_reset_html(settings, token)
    text = _build_password_reset_text(settings, token)
    _send_email(
        settings=settings,
        recipient=recipient,
        subject="Reset your ILAP password",
        html=html,
        text=text,
        idempotency_key=f"password-reset:{recipient}:{token}",
    )


def send_verification_email(*, settings: Settings, recipient: str, token: str) -> None:
    html = _build_verification_html(settings, token)
    text = _build_verification_text(settings, token)
    _send_email(
        settings=settings,
        recipient=recipient,
        subject="Verify your ILAP email",
        html=html,
        text=text,
        idempotency_key=f"verify-email:{recipient}:{token}",
    )


def _send_email(
    *,
    settings: Settings,
    recipient: str,
    subject: str,
    html: str,
    text: str,
    idempotency_key: str,
) -> None:
    if not settings.resend_api_key or not settings.auth_email_from:
        _emit_dev_token("email", recipient, token=idempotency_key.split(":")[-1], settings=settings)
        return
    try:
        with httpx.Client(timeout=15) as client:
            response = client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {settings.resend_api_key}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": idempotency_key[:256],
                },
                json={
                    "from": settings.auth_email_from,
                    "to": [recipient],
                    "subject": subject,
                    "html": html,
                    "text": text,
                },
            )
            response.raise_for_status()
    except Exception:
        _emit_dev_token("email", recipient, token=idempotency_key.split(":")[-1], settings=settings)
        if settings.is_production:
            raise


def _build_verification_html(settings: Settings, token: str) -> str:
    link = _build_optional_link(settings.email_verification_url_template, token)
    if link:
        return (
            "<p>Welcome to ILAP.</p>"
            f'<p>Please verify your email by opening <a href="{link}">this verification link</a>.</p>'
            f"<p>If the link does not open in your app, use this token: <code>{token}</code></p>"
        )
    return (
        "<p>Welcome to ILAP.</p>"
        f"<p>Use this email verification token in the app: <code>{token}</code></p>"
    )


def _build_verification_text(settings: Settings, token: str) -> str:
    link = _build_optional_link(settings.email_verification_url_template, token)
    if link:
        return f"Verify your email: {link}\nIf needed, use token: {token}"
    return f"Use this email verification token in the app: {token}"


def _build_password_reset_html(settings: Settings, token: str) -> str:
    link = _build_optional_link(settings.password_reset_url_template, token)
    if link:
        return (
            "<p>We received a request to reset your ILAP password.</p>"
            f'<p>Open <a href="{link}">this password reset link</a> to continue.</p>'
            f"<p>If the link does not open in your app, use this token: <code>{token}</code></p>"
        )
    return (
        "<p>We received a request to reset your ILAP password.</p>"
        f"<p>Use this password reset token in the app: <code>{token}</code></p>"
    )


def _build_password_reset_text(settings: Settings, token: str) -> str:
    link = _build_optional_link(settings.password_reset_url_template, token)
    if link:
        return f"Reset your password: {link}\nIf needed, use token: {token}"
    return f"Use this password reset token in the app: {token}"


def _build_optional_link(template: str | None, token: str) -> str | None:
    if not template:
        return None
    return template.replace("{token}", quote_plus(token))


def _emit_dev_token(kind: str, recipient: str, token: str, settings: Settings) -> None:
    if settings.is_production:
        return
    print(f"[dev-{kind}] recipient={recipient} token={token}")
