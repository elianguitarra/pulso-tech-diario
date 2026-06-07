#!/usr/bin/env python3
"""Publish the daily digest through Blogger Mail2Blogger or any post-by-email target."""

from __future__ import annotations

import os
import smtplib
import ssl
import sys
from datetime import datetime, timezone
from email.message import EmailMessage

import build
import publish_blogger


def env(name: str, default: str = "") -> str:
    value = os.environ.get(name, default).strip()
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def optional_env(name: str, default: str = "") -> str:
    return os.environ.get(name, "").strip() or default


def build_email_html(items: list[build.Item]) -> str:
    intro = """
<p><strong>Pulso Tech Diario</strong> selecciona automaticamente noticias tecnologicas relevantes y las acompana con imagenes SVG originales generadas por el sistema.</p>
"""
    evergreen_links = """
<p><strong>Lecturas base:</strong> Como leer tecnologia sin ruido, glosario de IA y senales de chips, seguridad y startups se publican desde el flujo principal cuando se usa Blogger API. En la ruta por email, este post diario mantiene el blog activo sin Google Cloud.</p>
"""
    return intro + publish_blogger.post_html(items) + evergreen_links


def make_message() -> EmailMessage:
    items = build.collect_items() or build.fallback_items()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    subject_prefix = optional_env("EMAIL_SUBJECT_PREFIX", "Pulso Tech Diario")
    smtp_username = env("SMTP_USERNAME")
    message = EmailMessage()
    message["Subject"] = f"{subject_prefix}: {today}"
    message["From"] = optional_env("SMTP_FROM", smtp_username)
    message["To"] = env("BLOGGER_MAIL_TO")
    reply_to = optional_env("SMTP_REPLY_TO")
    if reply_to:
        message["Reply-To"] = reply_to
    message.set_content(
        "Pulso Tech Diario requiere un lector compatible con HTML para ver las imagenes y el formato completo."
    )
    message.add_alternative(build_email_html(items), subtype="html")
    return message


def smtp_port() -> int:
    return int(optional_env("SMTP_PORT", "587"))


def publish() -> None:
    host = env("SMTP_HOST")
    port = smtp_port()
    username = env("SMTP_USERNAME")
    password = env("SMTP_PASSWORD")
    use_ssl = optional_env("SMTP_SSL", "false").lower() in {"1", "true", "yes"}
    use_starttls = optional_env("SMTP_STARTTLS", "true").lower() in {"1", "true", "yes"}
    message = make_message()

    if use_ssl:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, context=context, timeout=30) as smtp:
            smtp.login(username, password)
            smtp.send_message(message)
    else:
        with smtplib.SMTP(host, port, timeout=30) as smtp:
            smtp.ehlo()
            if use_starttls:
                smtp.starttls(context=ssl.create_default_context())
                smtp.ehlo()
            smtp.login(username, password)
            smtp.send_message(message)

    print(f"Email publish sent to {message['To']} with subject {message['Subject']}")


if __name__ == "__main__":
    try:
        publish()
    except smtplib.SMTPAuthenticationError as exc:
        sys.stderr.write(
            "SMTP authentication failed. Check SMTP_USERNAME and SMTP_PASSWORD for your provider. "
            "For Gmail, SMTP_PASSWORD must be a Google App Password, not your normal Gmail password. "
            "If Google App Passwords are unavailable for your account, use a free SMTP relay such as Brevo "
            "with SMTP_HOST=smtp-relay.brevo.com, SMTP_PORT=587, SMTP_SSL=false, SMTP_STARTTLS=true.\n"
        )
        raise
