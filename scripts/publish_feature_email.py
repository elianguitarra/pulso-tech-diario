#!/usr/bin/env python3
"""Publish a manually curated feature post through Mail2Blogger."""

from __future__ import annotations

import smtplib
import ssl
import sys
from datetime import datetime, timezone
from email.message import EmailMessage

import build
import publish_blogger
from publish_email import env, optional_env


TITLE = "Nvidia y Microsoft quieren llevar la inteligencia artificial al centro de tu PC"
EMAIL_TITLE = "Nvidia RTX Spark: la inteligencia artificial llega a las PCs"
SUMMARY = (
    "El anuncio de RTX Spark marca una nueva fase: computadoras Windows capaces de ejecutar agentes de IA "
    "localmente, con menos dependencia de la nube y una competencia mas directa contra Apple, Intel y AMD."
)
SOURCE_URL = "https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-and-Microsoft-Reinvent-Windows-PCs-for-the-Age-of-Personal-AI/default.aspx"


def post_html() -> str:
    item = build.Item(
        title=TITLE,
        link=SOURCE_URL,
        source="Nvidia, Axios y Tom's Hardware",
        summary=(
            "Nvidia presento RTX Spark junto a Microsoft para llevar agentes de inteligencia artificial "
            "directamente a laptops, mini PCs y estaciones Windows. La jugada busca mover parte de la IA "
            "desde la nube hacia el equipo personal, con menos latencia, mas privacidad y una nueva pelea "
            "contra Apple, Intel, AMD y Qualcomm."
        ),
        published=datetime.now(timezone.utc),
        category="inteligencia artificial",
        score=100,
    )
    analysis = """
<p><strong>Analisis de Pulso Tech:</strong> esta noticia importa porque la computadora personal vuelve a ser campo de batalla. Durante los ultimos anos, la inteligencia artificial se sintio como algo que vivia principalmente en la nube. Con propuestas como RTX Spark, Nvidia y Microsoft quieren que una parte de esa inteligencia funcione directamente dentro del equipo.</p>
<p>El cambio puede ser relevante para tareas cotidianas: resumir documentos largos, analizar carpetas de trabajo, revisar codigo, generar contenido o ejecutar asistentes que entiendan mejor el contexto local del usuario. La ventaja seria menor latencia, mas privacidad y menos dependencia de servidores externos.</p>
<p>Tambien hay dudas importantes. Falta ver precio, consumo de energia, compatibilidad de aplicaciones y si los agentes seran lo bastante utiles como para justificar comprar hardware nuevo. Pero la direccion es clara: la proxima etapa de la inteligencia artificial no solo se jugara en centros de datos, tambien en la computadora que usamos todos los dias.</p>
<p><strong>Fuentes adicionales:</strong> <a href="https://www.axios.com/2026/06/01/microsoft-nvidia-surface-ultra-rtx-spark">Axios</a> y <a href="https://www.tomshardware.com/laptops/nvidia-unveils-rtx-spark-superchip-at-computex-2026-new-platform-promises-to-turn-windows-into-an-agentic-ai-os-with-arm-cpu-blackwell-gpu-and-128gb-unified-memory">Tom's Hardware</a>.</p>
"""
    return publish_blogger.post_html([item]) + analysis


def make_message() -> EmailMessage:
    smtp_username = env("SMTP_USERNAME")
    subject_prefix = optional_env("EMAIL_SUBJECT_PREFIX", "Pulso Tech Diario")
    message = EmailMessage()
    message["Subject"] = f"{subject_prefix}: {EMAIL_TITLE}"
    message["From"] = optional_env("SMTP_FROM", smtp_username)
    message["To"] = env("BLOGGER_MAIL_TO")
    reply_to = optional_env("SMTP_REPLY_TO")
    if reply_to:
        message["Reply-To"] = reply_to
    message.set_content(
        f"{TITLE}\n\n"
        f"{SUMMARY}\n\n"
        f"Fuente Nvidia: {SOURCE_URL}\n"
        "Fuente Axios: https://www.axios.com/2026/06/01/microsoft-nvidia-surface-ultra-rtx-spark\n"
        "Fuente Tom's Hardware: https://www.tomshardware.com/laptops/nvidia-unveils-rtx-spark-superchip-at-computex-2026-new-platform-promises-to-turn-windows-into-an-agentic-ai-os-with-arm-cpu-blackwell-gpu-and-128gb-unified-memory\n"
    )
    message.add_alternative(post_html(), subtype="html")
    return message


def publish() -> None:
    host = env("SMTP_HOST")
    port = int(optional_env("SMTP_PORT", "587"))
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

    print(f"Feature email sent to {message['To']} with subject {message['Subject']}")


if __name__ == "__main__":
    try:
        publish()
    except smtplib.SMTPAuthenticationError as exc:
        response = exc.smtp_error.decode("utf-8", errors="replace") if isinstance(exc.smtp_error, bytes) else str(exc.smtp_error)
        if "Unauthorized IP address" in response:
            sys.stderr.write("Brevo rejected this GitHub Actions runner with: Unauthorized IP address.\n")
        raise
