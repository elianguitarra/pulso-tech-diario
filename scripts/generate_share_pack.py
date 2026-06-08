#!/usr/bin/env python3
"""Generate share-ready copy and a public sharing page."""

from __future__ import annotations

import html
import json
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
LATEST_OUT = PUBLIC / "ultima-entrada.html"
LATEST_JSON_OUT = PUBLIC / "latest.json"
LINKS_OUT = PUBLIC / "links.html"
SOCIAL_JSON_OUT = PUBLIC / "social-payload.json"
SOCIAL_CARD_OUT = PUBLIC / "assets" / "social-card.svg"
SITEMAP = PUBLIC / "sitemap.xml"
BLOG_URL = "https://pulsotechdiario.blogspot.com"
PAGES_URL = "https://elianguitarra.github.io/pulso-tech-diario"
RSS_URL = f"{BLOG_URL}/feeds/posts/default?alt=rss"
SOCIAL_IMAGE = f"{PAGES_URL}/assets/social-card.svg"


def tracked_url(url: str, source: str, medium: str, campaign: str, content: str = "") -> str:
    params = {
        "utm_source": source,
        "utm_medium": medium,
        "utm_campaign": campaign,
    }
    if content:
        params["utm_content"] = content
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}{urllib.parse.urlencode(params)}"


def tracked_if_blogger(url: str, source: str, medium: str, campaign: str, content: str = "") -> str:
    if url.startswith(BLOG_URL):
        return tracked_url(url, source, medium, campaign, content)
    return url


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
        if not title:
            continue
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


def wrap_text(value: str, max_chars: int, max_lines: int) -> list[str]:
    words = clean(value).split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join(current + [word])
        if current and len(candidate) > max_chars:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
        if len(lines) == max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(" ".join(current))
    if len(lines) == max_lines and len(" ".join(words)) > len(" ".join(lines)):
        lines[-1] = lines[-1].rstrip(" .,:;") + "..."
    return lines


def share_headline(title: str) -> str:
    normalized = clean(title)
    if re.fullmatch(r"Pulso Tech Diario:\s*\d{4}-\d{2}-\d{2}", normalized):
        return "IA, chips y ciberseguridad del dia"
    if normalized.startswith("Pulso Tech Diario:"):
        normalized = normalized.replace("Pulso Tech Diario:", "", 1).strip()
    return normalized or "Tecnologia importante, filtrada a diario"


def render_social_card(title: str) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    headline = share_headline(title)
    title_lines = wrap_text(headline, 32, 3)
    text_nodes = "\n".join(
        f'<text x="76" y="{206 + index * 68}" fill="#fff7ed" font-family="Arial, Helvetica, sans-serif" font-size="54" font-weight="900">{html.escape(line)}</text>'
        for index, line in enumerate(title_lines)
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630" role="img" aria-label="Pulso Tech Diario">
  <defs>
    <linearGradient id="bg" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0" stop-color="#101010"/>
      <stop offset="0.52" stop-color="#211816"/>
      <stop offset="1" stop-color="#073b3a"/>
    </linearGradient>
    <radialGradient id="pulse" cx="78%" cy="38%" r="52%">
      <stop offset="0" stop-color="#2dd4bf" stop-opacity="0.95"/>
      <stop offset="0.42" stop-color="#ff7058" stop-opacity="0.62"/>
      <stop offset="1" stop-color="#101010" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#bg)"/>
  <rect width="1200" height="630" fill="url(#pulse)"/>
  <path d="M690 108 C850 62 1038 130 1094 274 C1006 326 930 432 900 560 C790 476 676 408 536 396 C572 260 604 160 690 108 Z" fill="#ff7058" opacity="0.88"/>
  <path d="M752 160 C876 134 1008 190 1032 292 C938 322 872 396 842 492 C758 430 666 384 580 374 C612 268 654 190 752 160 Z" fill="#fff7ed" opacity="0.15"/>
  <circle cx="858" cy="292" r="82" fill="#2dd4bf" opacity="0.86"/>
  <path d="M700 458 C798 396 880 404 978 334 C1038 292 1082 230 1134 144" fill="none" stroke="#fff7ed" stroke-width="20" stroke-linecap="round" opacity="0.82"/>
  <g opacity="0.18" stroke="#fff7ed" stroke-width="1">
    <path d="M76 104 H518 M76 148 H458 M76 432 H392 M76 476 H456"/>
    <path d="M76 104 V476 M156 104 V476 M236 104 V476 M316 104 V476 M396 104 V476"/>
  </g>
  <rect x="54" y="48" width="1092" height="534" fill="none" stroke="#fff7ed" stroke-width="3" opacity="0.22"/>
  <text x="76" y="104" fill="#ff7058" font-family="Arial, Helvetica, sans-serif" font-size="28" font-weight="900" letter-spacing="2">PULSO TECH DIARIO</text>
  {text_nodes}
  <text x="76" y="542" fill="#fff7ed" font-family="Arial, Helvetica, sans-serif" font-size="30" font-weight="800" opacity="0.9">Tecnologia importante en espanol | {today}</text>
  <text x="948" y="548" fill="#101010" font-family="Arial, Helvetica, sans-serif" font-size="64" font-weight="950">PT</text>
</svg>"""


def share_url(service: str, title: str, url: str) -> str:
    text = f"{share_headline(title)} - tecnologia explicada en espanol"
    if service == "x":
        return f"https://twitter.com/intent/tweet?text={urllib.parse.quote(text)}&url={urllib.parse.quote(url)}"
    if service == "whatsapp":
        return f"https://wa.me/?text={urllib.parse.quote(text + ' ' + url)}"
    if service == "linkedin":
        return f"https://www.linkedin.com/sharing/share-offsite/?url={urllib.parse.quote(url)}"
    if service == "reddit":
        return f"https://www.reddit.com/submit?url={urllib.parse.quote(url)}&title={urllib.parse.quote(text)}"
    if service == "hackernews":
        return f"https://news.ycombinator.com/submitlink?u={urllib.parse.quote(url)}&t={urllib.parse.quote(text)}"
    if service == "telegram":
        return f"https://t.me/share/url?url={urllib.parse.quote(url)}&text={urllib.parse.quote(text)}"
    return url


def social_payload(title: str, url: str, guides: list[tuple[str, str]]) -> dict:
    tracked = {
        "x": tracked_url(url, "share_pack", "social", "daily_share", "x"),
        "linkedin": tracked_url(url, "share_pack", "social", "daily_share", "linkedin"),
        "whatsapp": tracked_url(url, "share_pack", "social", "daily_share", "whatsapp"),
        "telegram": tracked_url(url, "share_pack", "social", "daily_share", "telegram"),
        "reddit": tracked_url(url, "share_pack", "community", "daily_share", "reddit"),
        "hackernews": tracked_url(url, "share_pack", "community", "daily_share", "hackernews"),
    }
    posts = {
        "x": f"{share_headline(title)}\n\nIA, ciberseguridad, chips y herramientas digitales explicadas en espanol.\n\n{tracked['x']}",
        "linkedin": (
            "Hoy en Pulso Tech Diario seleccione las senales tecnologicas que pueden afectar producto, "
            f"seguridad y trabajo.\n\nResumen:\n{tracked['linkedin']}"
        ),
        "whatsapp": f"Pulso Tech Diario:\n- IA y productividad\n- Seguridad digital\n- Chips y plataformas\n\nLeer aqui: {tracked['whatsapp']}",
        "telegram": f"Pulso Tech Diario: tecnologia importante explicada en espanol.\n\n{tracked['telegram']}",
        "reddit": f"{share_headline(title)}\n\nResumen diario en espanol con enlaces a fuentes originales: {tracked['reddit']}",
        "hackernews": f"{share_headline(title)} - Pulso Tech Diario",
    }
    return {
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "title": title,
        "headline": share_headline(title),
        "url": url,
        "image": SOCIAL_IMAGE,
        "tracked_urls": tracked,
        "share_urls": {service: share_url(service, title, service_url) for service, service_url in tracked.items()},
        "posts": posts,
        "guides": [
            {
                "title": guide_title,
                "url": guide_url,
                "tracked_url": tracked_if_blogger(guide_url, "share_pack", "social", "guide_share", f"guide_{index}"),
            }
            for index, (guide_title, guide_url) in enumerate(guides[:7], start=1)
        ],
    }


def render_text(title: str, url: str, guides: list[tuple[str, str]]) -> str:
    payload = social_payload(title, url, guides)
    guide_lines = "\n".join(
        f"- {guide_title}: {tracked_if_blogger(guide_url, 'share_pack', 'social', 'guide_share', f'guide_{index}')}"
        for index, (guide_title, guide_url) in enumerate(guides[:4], start=1)
    )
    return f"""X / Twitter
{payload["posts"]["x"]}

LinkedIn
{payload["posts"]["linkedin"]}

WhatsApp / Telegram
{payload["posts"]["whatsapp"]}

Reddit / comunidades
{payload["posts"]["reddit"]}

Guias para compartir
{guide_lines}
"""


def render_html(title: str, url: str, guides: list[tuple[str, str]]) -> str:
    guide_cards = "\n".join(
        f"""<li><a href="{html.escape(tracked_if_blogger(link, "share_pack", "referral", "guide_list", f"guide_{index}"))}">{html.escape(guide_title)}</a></li>"""
        for index, (guide_title, link) in enumerate(guides, start=1)
    )
    payload = social_payload(title, url, guides)
    buttons = "\n".join(
        f"""<a class="button" href="{html.escape(payload["share_urls"][service])}">{label}</a>"""
        for service, label in [
            ("x", "Compartir en X"),
            ("whatsapp", "WhatsApp"),
            ("telegram", "Telegram"),
            ("linkedin", "LinkedIn"),
            ("reddit", "Reddit"),
            ("hackernews", "Hacker News"),
        ]
    )
    channel_cards = "\n".join(
        f"""<article class="channel">
        <h3>{html.escape(label)}</h3>
        <textarea readonly>{html.escape(payload["posts"][service])}</textarea>
        <p><a class="button secondary" href="{html.escape(payload["share_urls"][service])}">Abrir {html.escape(label)}</a></p>
      </article>"""
        for service, label in [
            ("x", "X"),
            ("linkedin", "LinkedIn"),
            ("whatsapp", "WhatsApp"),
            ("telegram", "Telegram"),
            ("reddit", "Reddit"),
        ]
    )
    main_url = tracked_url(url, "share_pack", "referral", "daily_share", "main")
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
  <meta property="og:type" content="website">
  <meta property="og:title" content="Compartir Pulso Tech Diario">
  <meta property="og:description" content="{html.escape(title)}">
  <meta property="og:image" content="{SOCIAL_IMAGE}">
  <meta property="og:image:type" content="image/svg+xml">
  <meta property="og:url" content="{PAGES_URL}/share-pack.html">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Compartir Pulso Tech Diario">
  <meta name="twitter:description" content="{html.escape(title)}">
  <meta name="twitter:image" content="{SOCIAL_IMAGE}">
  <style>
    body {{ margin: 0; font-family: Arial, Helvetica, sans-serif; background: #151515; color: #f7f1e8; }}
    main {{ width: min(100% - 32px, 920px); margin: 0 auto; padding: 44px 0 64px; }}
    a {{ color: #ff7058; }}
    h1 {{ font-size: clamp(38px, 8vw, 72px); line-height: 0.95; margin: 0 0 18px; }}
    .panel {{ border-top: 3px solid #ff7058; padding: 22px 0; margin-top: 28px; }}
    .button {{ display: inline-block; margin: 0 10px 10px 0; padding: 12px 14px; background: #ff7058; color: #201512; font-weight: 900; text-decoration: none; }}
    .button.secondary {{ background: #f7f1e8; color: #151515; }}
    textarea {{ width: 100%; min-height: 260px; background: #0f0f0f; color: #f7f1e8; border: 1px solid #333; padding: 16px; line-height: 1.5; }}
    .channel {{ border-top: 1px solid #333; padding: 18px 0; }}
    .channel textarea {{ min-height: 150px; }}
    .preview {{ width: 100%; max-width: 720px; border: 1px solid #333; background: #0f0f0f; }}
    li {{ margin-bottom: 10px; }}
  </style>
</head>
<body>
  <main>
    <p>Actualizado {now}</p>
    <h1>Compartir Pulso Tech Diario</h1>
    <p>Usa estos enlaces para mover la publicacion del dia y las guias que pueden atraer busquedas recurrentes.</p>
    <p><img class="preview" src="assets/social-card.svg" alt="Tarjeta social de Pulso Tech Diario" width="1200" height="630"></p>
    <div class="panel">
      <h2>Publicacion principal</h2>
      <p><a href="{html.escape(main_url)}">{html.escape(title)}</a></p>
      <p>{buttons}</p>
    </div>
    <div class="panel">
      <h2>Textos por canal</h2>
      <p>Publica solo donde las reglas de la comunidad permitan compartir enlaces propios.</p>
      {channel_cards}
    </div>
    <div class="panel">
      <h2>Guias para compartir</h2>
      <ul>{guide_cards}</ul>
    </div>
    <div class="panel">
      <h2>Payload para automatizar</h2>
      <p><a href="social-payload.json">social-payload.json</a> contiene titulo, URL, UTMs y textos listos para conectarlo despues con herramientas gratuitas.</p>
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
      <h2><a href="{html.escape(tracked_if_blogger(item["link"], "github_pages", "archive", "blogger_bridge", f"post_{index}"))}">{html.escape(item["title"])}</a></h2>
      <p>{html.escape(item.get("description", "")[:220])}</p>
    </article>"""
        for index, item in enumerate(items[:30], start=1)
    )
    blog_home = tracked_url(BLOG_URL + "/", "github_pages", "archive", "blogger_bridge", "home")
    share_pack = tracked_url(f"{PAGES_URL}/share-pack.html", "github_pages", "archive", "blogger_bridge", "share_pack")
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
      <a href="{blog_home}">Abrir Blogger</a>
      <a href="{RSS_URL}">RSS de Blogger</a>
      <a href="{share_pack}">Compartir</a>
    </p>
    {rows}
  </main>
</body>
</html>
"""


def render_latest_redirect(title: str, url: str) -> str:
    target = tracked_url(url, "github_pages", "redirect", "latest_entry", "canonical")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Ultima entrada | Pulso Tech Diario</title>
  <meta name="description" content="Acceso permanente a la entrada mas reciente de Pulso Tech Diario en Blogger.">
  <meta name="robots" content="index,follow">
  <link rel="canonical" href="{html.escape(url)}">
  <meta http-equiv="refresh" content="2; url={html.escape(target)}">
  <meta property="og:type" content="article">
  <meta property="og:title" content="{html.escape(title)}">
  <meta property="og:description" content="Entrada mas reciente de Pulso Tech Diario.">
  <meta property="og:url" content="{PAGES_URL}/ultima-entrada.html">
  <meta property="og:image" content="{SOCIAL_IMAGE}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{html.escape(title)}">
  <meta name="twitter:description" content="Entrada mas reciente de Pulso Tech Diario.">
  <meta name="twitter:image" content="{SOCIAL_IMAGE}">
  <style>
    body {{ margin: 0; font-family: Arial, Helvetica, sans-serif; background: #151515; color: #f7f1e8; }}
    main {{ width: min(100% - 32px, 820px); margin: 0 auto; padding: 56px 0 72px; }}
    h1 {{ font-size: clamp(38px, 8vw, 72px); line-height: 0.95; margin: 0 0 18px; }}
    a {{ color: #ff7058; font-weight: 900; }}
    .panel {{ border-top: 3px solid #ff7058; margin-top: 28px; padding-top: 18px; }}
  </style>
</head>
<body>
  <main>
    <p>Actualizado {now}</p>
    <h1>Ultima entrada de Pulso Tech Diario</h1>
    <p>Te estamos llevando a la publicacion mas reciente en Blogger.</p>
    <div class="panel">
      <p><strong>{html.escape(title)}</strong></p>
      <p><a href="{html.escape(target)}">Abrir ahora</a></p>
    </div>
  </main>
</body>
</html>
"""


def render_links_page(title: str, url: str, guides: list[tuple[str, str]]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    latest = tracked_url(url, "link_bio", "referral", "profile_links", "latest")
    blogger = tracked_url(BLOG_URL + "/", "link_bio", "referral", "profile_links", "blogger")
    archive = tracked_url(f"{PAGES_URL}/blogger-archivo.html", "link_bio", "referral", "profile_links", "archive")
    share = tracked_url(f"{PAGES_URL}/share-pack.html", "link_bio", "referral", "profile_links", "share_pack")
    guide_cards = "\n".join(
        f"""<a class="link secondary" href="{html.escape(tracked_if_blogger(link, "link_bio", "referral", "profile_guides", f"guide_{index}"))}">
      <span>{html.escape(guide_title)}</span>
      <small>Guia recomendada</small>
    </a>"""
        for index, (guide_title, link) in enumerate(guides[:5], start=1)
    )
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pulso Tech Diario | Links</title>
  <meta name="description" content="Enlaces principales de Pulso Tech Diario: ultima entrada, Blogger, guias y kit para compartir.">
  <meta name="robots" content="index,follow">
  <link rel="canonical" href="{PAGES_URL}/links.html">
  <meta property="og:type" content="website">
  <meta property="og:title" content="Pulso Tech Diario">
  <meta property="og:description" content="Resumen diario de tecnologia en espanol.">
  <meta property="og:url" content="{PAGES_URL}/links.html">
  <meta property="og:image" content="{SOCIAL_IMAGE}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Pulso Tech Diario">
  <meta name="twitter:description" content="Resumen diario de tecnologia en espanol.">
  <meta name="twitter:image" content="{SOCIAL_IMAGE}">
  <style>
    body {{ margin: 0; font-family: Arial, Helvetica, sans-serif; background: #151515; color: #f7f1e8; }}
    main {{ width: min(100% - 30px, 680px); margin: 0 auto; padding: 42px 0 64px; }}
    .brand {{ display: flex; align-items: center; gap: 14px; margin-bottom: 24px; }}
    .mark {{ width: 48px; height: 48px; display: grid; place-items: center; background: #ff7058; color: #201512; font-weight: 950; }}
    h1 {{ font-size: clamp(38px, 9vw, 68px); line-height: .95; margin: 0 0 12px; }}
    p {{ color: #d6c8bc; line-height: 1.55; }}
    .updated {{ color: #ff7058; font-size: 12px; font-weight: 900; text-transform: uppercase; letter-spacing: .08em; }}
    .stack {{ display: grid; gap: 12px; margin-top: 26px; }}
    .link {{ display: block; padding: 18px; border: 1px solid #3a3a3a; color: #f7f1e8; text-decoration: none; background: #202020; }}
    .link.primary {{ background: #ff7058; color: #201512; border-color: #ff7058; }}
    .link span {{ display: block; font-size: 20px; font-weight: 950; line-height: 1.1; }}
    .link small {{ display: block; margin-top: 8px; color: inherit; opacity: .72; font-weight: 800; }}
    .secondary:hover {{ border-color: #ff7058; }}
  </style>
</head>
<body>
  <main>
    <div class="brand"><span class="mark">PT</span><strong>Pulso Tech Diario</strong></div>
    <p class="updated">Actualizado {now}</p>
    <h1>Tecnologia en espanol, directo al punto.</h1>
    <p>Usa esta pagina como link de perfil: siempre apunta a la entrada mas reciente, el blog principal y las guias con mas potencial de busqueda.</p>
    <div class="stack">
      <a class="link primary" href="{html.escape(latest)}"><span>{html.escape(title)}</span><small>Ultima entrada en Blogger</small></a>
      <a class="link" href="{html.escape(blogger)}"><span>Abrir Blogger</span><small>Blog principal preparado para AdSense</small></a>
      <a class="link" href="{html.escape(f"{PAGES_URL}/noticias-tecnologia-espanol.html")}"><span>Noticias de tecnologia en espanol</span><small>Pagina de entrada para nuevos lectores</small></a>
      <a class="link" href="{html.escape(archive)}"><span>Archivo de entradas</span><small>Historial enlazado desde GitHub Pages</small></a>
      <a class="link" href="{html.escape(share)}"><span>Kit para compartir</span><small>Textos y botones sociales listos</small></a>
      {guide_cards}
    </div>
  </main>
</body>
</html>
"""


def latest_payload(title: str, url: str, items: list[dict[str, str]]) -> str:
    payload = {
        "title": title,
        "url": url,
        "tracked_url": tracked_url(url, "github_pages", "redirect", "latest_entry", "json"),
        "permalink": f"{PAGES_URL}/ultima-entrada.html",
        "share_pack": f"{PAGES_URL}/share-pack.html",
        "blogger_archive": f"{PAGES_URL}/blogger-archivo.html",
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "source": RSS_URL,
        "recent": items[:8],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def append_to_sitemap() -> None:
    if not SITEMAP.exists():
        return
    text = SITEMAP.read_text(encoding="utf-8")
    today = datetime.now(timezone.utc).date().isoformat()
    entries = []
    for loc in [
        f"{PAGES_URL}/share-pack.html",
        f"{PAGES_URL}/blogger-archivo.html",
        f"{PAGES_URL}/ultima-entrada.html",
        f"{PAGES_URL}/links.html",
        f"{PAGES_URL}/social-payload.json",
    ]:
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
    SOCIAL_CARD_OUT.parent.mkdir(parents=True, exist_ok=True)
    SOCIAL_CARD_OUT.write_text(render_social_card(title), encoding="utf-8")
    TXT_OUT.write_text(render_text(title, url, guides), encoding="utf-8")
    HTML_OUT.write_text(render_html(title, url, guides), encoding="utf-8")
    ARCHIVE_OUT.write_text(render_archive(items), encoding="utf-8")
    LATEST_OUT.write_text(render_latest_redirect(title, url), encoding="utf-8")
    LATEST_JSON_OUT.write_text(latest_payload(title, url, items), encoding="utf-8")
    LINKS_OUT.write_text(render_links_page(title, url, guides), encoding="utf-8")
    SOCIAL_JSON_OUT.write_text(json.dumps(social_payload(title, url, guides), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    append_to_sitemap()
    print(f"share pack written to {TXT_OUT}, {HTML_OUT}, {ARCHIVE_OUT}, {LATEST_OUT}, {LATEST_JSON_OUT}, {LINKS_OUT}, and {SOCIAL_JSON_OUT}")


if __name__ == "__main__":
    main()
