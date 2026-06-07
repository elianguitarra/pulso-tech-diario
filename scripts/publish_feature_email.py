#!/usr/bin/env python3
"""Publish a manually curated feature post through Mail2Blogger."""

from __future__ import annotations

import smtplib
import ssl
import sys
from datetime import datetime, timezone
from email.message import EmailMessage

from publish_email import env, optional_env


SITE_URL = "https://elianguitarra.github.io/pulso-tech-diario"
IMAGE_URL = f"{SITE_URL}/assets/features/rtx-spark-ai-pc.svg"


TITLE = "Nvidia y Microsoft quieren que la IA viva dentro de tu PC"
SUMMARY = (
    "El anuncio de RTX Spark marca una nueva fase: computadoras Windows capaces de ejecutar agentes de IA "
    "localmente, con menos dependencia de la nube y una competencia mas directa contra Apple, Intel y AMD."
)


def post_html() -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"""
<p><em>Publicado por Pulso Tech Diario el {today}.</em></p>
<p><img src="{IMAGE_URL}" alt="Ilustracion original sobre IA local en laptops y PCs"></p>
<p><strong>La noticia:</strong> Nvidia presento RTX Spark, un superchip pensado para llevar cargas de inteligencia artificial directamente a laptops, mini PCs y estaciones Windows. La compania lo posiciona como hardware para la era de los agentes personales de IA: asistentes que no solo responden, sino que pueden trabajar de forma continua dentro del equipo.</p>
<p>El movimiento importa porque cambia el centro de gravedad de la IA. Hasta ahora, gran parte de la experiencia dependia de servidores remotos: escribes una instruccion, viaja a la nube, vuelve una respuesta. Con chips como RTX Spark, una parte mayor del trabajo puede ejecutarse localmente, cerca de tus archivos, apps y flujos cotidianos.</p>
<p><strong>Por que puede cambiar el PC:</strong> Nvidia habla de hasta 1 petaflop de computo de IA y 128 GB de memoria unificada para atender agentes en el dispositivo. Microsoft tambien entro en escena con hardware Surface basado en esta plataforma, lo que sugiere que Windows quiere dejar de ser solo un sistema para abrir apps y convertirse en un entorno donde los agentes actuen entre aplicaciones.</p>
<p>La apuesta tambien presiona a Apple, Intel, AMD y Qualcomm. Apple ya demostro que integrar CPU, GPU, memoria y software puede redefinir una categoria. Nvidia intenta llevar esa misma logica al mundo Windows, pero con su ventaja historica: CUDA, GPUs RTX y herramientas para desarrolladores de IA.</p>
<p><strong>La lectura practica:</strong> Para usuarios comunes, esto no significa que manana todos necesiten una laptop de IA. Significa que el mercado empieza a preparar maquinas donde tareas como resumir archivos grandes, analizar proyectos, generar contenido, asistir en codigo o automatizar acciones puedan ocurrir con mas privacidad y menor latencia.</p>
<p>Para empresas y creadores, la senal es mas clara: la IA local puede reducir costos de nube, facilitar pruebas con modelos privados y abrir una nueva categoria de software. El reto sera precio, bateria, compatibilidad real de apps y si los agentes son suficientemente utiles como para justificar comprar hardware nuevo.</p>
<p><strong>Conclusion:</strong> RTX Spark no es solo otro chip anunciado en una feria. Es una declaracion de direccion: la proxima batalla de la IA no estara solo en centros de datos, sino tambien en la computadora personal. Si funciona, el PC podria volver a sentirse como una plataforma nueva.</p>
<p><strong>Fuentes:</strong> <a href="https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-and-Microsoft-Reinvent-Windows-PCs-for-the-Age-of-Personal-AI/default.aspx">Nvidia</a>, <a href="https://www.axios.com/2026/06/01/microsoft-nvidia-surface-ultra-rtx-spark">Axios</a>, <a href="https://www.tomshardware.com/laptops/nvidia-unveils-rtx-spark-superchip-at-computex-2026-new-platform-promises-to-turn-windows-into-an-agentic-ai-os-with-arm-cpu-blackwell-gpu-and-128gb-unified-memory">Tom's Hardware</a>.</p>
"""


def make_message() -> EmailMessage:
    smtp_username = env("SMTP_USERNAME")
    subject_prefix = optional_env("EMAIL_SUBJECT_PREFIX", "Pulso Tech Diario")
    message = EmailMessage()
    message["Subject"] = f"{subject_prefix}: {TITLE}"
    message["From"] = optional_env("SMTP_FROM", smtp_username)
    message["To"] = env("BLOGGER_MAIL_TO")
    reply_to = optional_env("SMTP_REPLY_TO")
    if reply_to:
        message["Reply-To"] = reply_to
    message.set_content(f"{TITLE}\n\n{SUMMARY}\n\nFuente visual: {IMAGE_URL}")
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
