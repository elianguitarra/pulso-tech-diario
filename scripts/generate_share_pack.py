#!/usr/bin/env python3
"""Generate share-ready copy for the latest Pulso Tech Diario post."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "share-pack.txt"
BLOG_URL = "https://pulsotechdiario.blogspot.com"


def daily_url() -> str:
    return f"{BLOG_URL}/"


def main() -> None:
    url = daily_url()
    text = f"""X / Twitter
Pulso Tech Diario de hoy:

1. IA: una senal clave para productividad y software.
2. Ciberseguridad: riesgos que conviene vigilar.
3. Chips y plataformas: hacia donde se mueve la industria.

Resumen completo:
{url}

LinkedIn
Hoy en Pulso Tech Diario seleccione las senales tecnologicas que mas pueden afectar producto, seguridad y trabajo.

La idea no es leerlo todo, sino detectar que cambia.

Resumen:
{url}

WhatsApp / Telegram
Pulso Tech Diario:
- IA y productividad
- Seguridad digital
- Chips y plataformas

Leer aqui: {url}
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(f"share pack written to {OUT}")


if __name__ == "__main__":
    main()
