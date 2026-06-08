#!/usr/bin/env python3
"""Generate share-ready copy and a public sharing page."""

from __future__ import annotations

import email.utils
import html
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
TXT_OUT = PUBLIC / "share-pack.txt"
HTML_OUT = PUBLIC / "share-pack.html"
ARCHIVE_OUT = PUBLIC / "blogger-archivo.html"
SITEMAP = PUBLIC / "sitemap.xml"
BLOG_URL = "https://pulsotechdiario.blogspot.com"
PAGES_URL = "https://elianguitarra.github.io/pulso-tech-diario"
RSS_URL = f"{BLOG_URL}/feeds/posts/default?alt=rss"


def fetch_text(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "PulsoTechDiarioSharePack/1.0"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", errors="replace")


def clean(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def feed_items() -> list[dict[str, str]]:
    try:
        root = ET.fromstring(fetch_text(RSS_URL))
    except (urllib.error.URLError, TimeoutError, ET.ParseError, OSError):
        return []
    items = []
    for item in root.findall(".//item"):
        title = clean(item.findtext("title", "Pulso Tech Diario"))
        link = clean(item.findtext("link", BLOG_URL + "/"))
        description = clean(item.findtext("description", ""))
        published = clean(item.findtext("pubDate", ""))
        items.append({"title": title, "link": link, "description": description, "published": published})
    return items


def latest_link(items: list[dict[str, str]]) -> tuple[str, str]:
    for item in items:
        if item["title"].startswith("Pulso Tech Diario:"):
            return item["title"], item["link"]
    if items:
        return items[0]["title"], items[0]["link"]
    return "Pulso Tech Diario", BLOG_URL + "/"


def guide_links(items: list[dict[str, str]]) -> list[tuple[str, str]]:
    guides = []
    for item in items:
        title = item["title"]
        if title.startswith("Pulso Tech Diario:"):
            continue
        if len(guides) < 5:
            guides.append((title, item["link"]))
    static_guides = [
        ("IA en el trabajo: donde si ahorra tiempo", f"{PAGES_URL}/ia-en-el-trabajo.html"),
        ("Que revisar antes de comprar una laptop para IA", f"{PAGES_URL}/comprar-laptop-para-ia.html"),
    ]
    for title, url in static_guides:
        if url not in {link for _, link in guides}:
            guides.append((title, url))
    return guides[:7]


def share_url(service: str, title: str, url: str) -> str:
    text = f"{title} - tecnologia explicada en espanol"
    if service == "x":
        return f"https://twitter.com/intent/tweet?text={urllib.parse.quote(text)}&url={urllib.parse.quote(url)}"
    if service == "whatsapp":
        return f"https://wa.me/?text={urllib.parse.quote(text + ' ' + url)}"
    if service == "linkedin":
        return f"https://www.linkedin.com/sharing/share-offsite/?url={urllib.parse.quote(url)}"
    return url


def render_text(title: str, url: str, guides: list[tuple[str, str]]) -> str:
    guide_lines = "\n".join(f"- {guide_title}: {guide_url}" for guide_title, guide_url in guides[:4])
    return f"""X / Twitter
{title}

IA, ciberseguridad, chips y herramientas digitales explicadas en espanol.

Leer:
{url}

LinkedIn
Hoy en Pulso Tech Diario:

Seleccion de tecnologia con contexto rapido para entender que cambia en IA, seguridad, hardware y productividad.

Resumen:
{url}

WhatsApp / Telegram
Pulso Tech Diario:
- IA y productividad
- Seguridad digital
- Chips y plataformas

Leer aqui: {url}

Guias para compartir
{guide_lines}
"""


def render_html(title: str, url: str, guides: list[tuple[str, str]]) -> str:
    guide_cards = "\n".join(
        f"""<li><a href="{html.escape(link)}">{html.escape(guide_title)}</a></li>"""
        for guide_title, link in guides
    )
    buttons = "\n".join(
        f"""<a class="button" href="{html.escape(share_url(service, title, url))}">{label}</a>"""
        for service, label in [("x", "Compartir en X"), ("whatsapp", "WhatsApp"), ("linkedin", "LinkedIn")]
    )
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Compartir Pulso Tech Diario</title>
  <meta name="description" content="Textos y botones para compartir Pulso Tech Diario en redes y mensajeria.">
  <meta name="robots" content="index,follow">
  <link rel="canonical" href="{PAGES_URL}/share-pack.html">
  <style>
    body {{ margin: 0; font-family: Arial, Helvetica, sans-serif; background: #151515; color: #f7f1e8; }}
    main {{ width: min(100% - 32px, 920px); margin: 0 auto; padding: 44px 0 64px; }}
    a {{ color: #ff7058; }}
    h1 {{ font-size: clamp(38px, 8vw, 72px); line-height: 0.95; margin: 0 0 18px; }}
    .panel {{ border-top: 3px solid #ff7058; padding: 22px 0; margin-top: 28px; }}
    .button {{ display: inline-block; margin: 0 10px 10px 0; padding: 12px 14px; background: #ff7058; color: #201512; font-weight: 900; text-decoration: none; }}
    textarea {{ width: 100%; min-height: 260px; background: #0f0f0f; color: #f7f1e8; border: 1px solid #333; padding: 16px; line-height: 1.5; }}
    li {{ margin-bottom: 10px; }}
  </style>
</head>
<body>
  <main>
    <p>Actualizado {now}</p>
    <h1>Compartir Pulso Tech Diario</h1>
    <p>Usa estos enlaces para mover la publicacion del dia y las guias que pueden atraer busquedas recurrentes.</p>
    <div class="panel">
      <h2>Publicacion principal</h2>
      <p><a href="{html.escape(url)}">{html.escape(title)}</a></p>
      <p>{buttons}</p>
    </div>
    <div class="panel">
      <h2>Guias para compartir</h2>
      <ul>{guide_cards}</ul>
    </div>
    <div class="panel">
      <h2>Texto listo</h2>
      <textarea readonly>{html.escape(render_text(title, url, guides))}</textarea>
    </div>
  </main>
</body>
</html>
"""


def render_archive(items: list[dict[str, str]]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    if not items:
        items = [{"title": "Pulso Tech Diario", "link": BLOG_URL + "/", "description": "Resumen diario de tecnologia en espanol.", "published": ""}]
    rows = "\n".join(
        f"""<article>
      <p class="date">{html.escape(item.get("published", ""))}</p>
      <h2><a href="{html.escape(item["link"])}">{html.escape(item["title"])}</a></h2>
      <p>{html.escape(item.get("description", "")[:220])}</p>
    </article>"""
        for item in items[:30]
    )
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Archivo de Blogger | Pulso Tech Diario</title>
  <meta name="description" content="Archivo enlazado de entradas reales de Pulso Tech Diario en Blogger.">
  <meta name="robots" content="index,follow">
  <link rel="canonical" href="{PAGES_URL}/blogger-archivo.html">
  <style>
    body {{ margin: 0; font-family: Arial, Helvetica, sans-serif; background: #fbfcf8; color: #172033; }}
    main {{ width: min(100% - 32px, 980px); margin: 0 auto; padding: 44px 0 64px; }}
    h1 {{ font-size: clamp(38px, 8vw, 72px); line-height: 0.95; margin: 0 0 18px; }}
    article {{ border-top: 1px solid #d9e2ec; padding: 20px 0; }}
    article h2 {{ margin: 0 0 8px; font-size: 24px; line-height: 1.1; }}
    a {{ color: #0f766e; font-weight: 850; }}
    .date {{ color: #667085; font-size: 13px; margin: 0 0 8px; }}
    .actions a {{ display: inline-block; margin: 0 10px 10px 0; padding: 10px 12px; background: #172033; color: white; text-decoration: none; }}
  </style>
</head>
<body>
  <main>
    <p>Actualizado {now}</p>
    <h1>Archivo de Blogger</h1>
    <p>Entradas reales del blog principal enlazadas desde GitHub Pages para facilitar descubrimiento, lectura y rastreo.</p>
    <p class="actions">
      <a href="{BLOG_URL}/">Abrir Blogger</a>
      <a href="{RSS_URL}">RSS de Blogger</a>
      <a href="{PAGES_URL}/share-pack.html">Compartir</a>
    </p>
    {rows}
  </main>
</body>
</html>
"""


def append_to_sitemap() -> None:
    if not SITEMAP.exists():
        return
    text = SITEMAP.read_text(encoding="utf-8")
    today = datetime.now(timezone.utc).date().isoformat()
    entries = []
    for loc in [f"{PAGES_URL}/share-pack.html", f"{PAGES_URL}/blogger-archivo.html"]:
        if loc in text:
            continue
        entries.append(f"""  <url>
    <loc>{loc}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.7</priority>
  </url>
""")
    if not entries:
        return
    text = text.replace("</urlset>", f"{''.join(entries)}</urlset>")
    SITEMAP.write_text(text, encoding="utf-8")


def main() -> None:
    items = feed_items()
    title, url = latest_link(items)
    guides = guide_links(items)
    PUBLIC.mkdir(parents=True, exist_ok=True)
    TXT_OUT.write_text(render_text(title, url, guides), encoding="utf-8")
    HTML_OUT.write_text(render_html(title, url, guides), encoding="utf-8")
    ARCHIVE_OUT.write_text(render_archive(items), encoding="utf-8")
    append_to_sitemap()
    print(f"share pack written to {TXT_OUT}, {HTML_OUT}, and {ARCHIVE_OUT}")


if __name__ == "__main__":
    main()
