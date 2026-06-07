#!/usr/bin/env python3
"""Build Pulso Tech Diario as a zero-dependency static site."""

from __future__ import annotations

import email.utils
import html
import json
import math
import os
import re
import textwrap
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
ASSET_DIR = PUBLIC / "assets" / "images"

SITE_NAME = "Pulso Tech Diario"
SITE_DESCRIPTION = (
    "Un resumen diario y automatizado de las noticias tecnologicas mas relevantes, "
    "con imagenes originales generadas por el propio sitio."
)
SITE_URL = os.environ.get("SITE_URL", "https://elianguitarra.github.io/pulso-tech-diario").rstrip("/")
ADSENSE_CLIENT = os.environ.get("ADSENSE_CLIENT", "").strip()
ADSENSE_TOP_SLOT = os.environ.get("ADSENSE_TOP_SLOT", "").strip()
ADSENSE_IN_ARTICLE_SLOT = os.environ.get("ADSENSE_IN_ARTICLE_SLOT", "").strip()
INDEXNOW_KEY = os.environ.get("INDEXNOW_KEY", "pulso-tech-diario-2026-indexnow-key").strip()

STATIC_PAGES = {
    "acerca.html": {
        "title": "Acerca de",
        "description": "Pulso Tech Diario resume tecnologia relevante cada dia con fuentes publicas, enlaces originales e imagenes propias.",
        "body": """
<p><strong>Pulso Tech Diario</strong> es un sitio automatizado que resume noticias tecnologicas relevantes cada dia.</p>
<p>El objetivo es ayudar a lectores ocupados a detectar senales importantes sobre inteligencia artificial, chips, ciberseguridad, startups, consumo digital, ciencia aplicada y plataformas web.</p>
<p>El sistema revisa fuentes publicas por RSS, ordena las notas por frescura, relevancia tematica y fuente, y enlaza siempre al articulo original.</p>
""",
    },
    "politica-editorial.html": {
        "title": "Politica editorial",
        "description": "Criterios editoriales de Pulso Tech Diario para seleccionar, resumir y enlazar noticias tecnologicas.",
        "body": """
<p>Pulso Tech Diario no copia articulos completos. Cada entrada usa resumen editorial propio y enlaces directos a las fuentes originales.</p>
<p>Las notas se seleccionan automaticamente con reglas de relevancia, pero el sitio prioriza contenido informativo, trazable y util para lectores interesados en tecnologia.</p>
<p>Las imagenes que acompanan cada noticia son ilustraciones SVG originales generadas automaticamente para este sitio. No representan capturas ni fotografias de los articulos enlazados.</p>
""",
    },
    "privacidad.html": {
        "title": "Privacidad",
        "description": "Informacion de privacidad, cookies y anuncios para lectores de Pulso Tech Diario.",
        "body": """
<p>Este sitio se publica como una pagina estatica gratuita en GitHub Pages. El hosting puede procesar datos tecnicos habituales como direccion IP, navegador, dispositivo, fecha de acceso y registros de seguridad.</p>
<p>Si el sitio muestra anuncios mediante Google AdSense, Google y sus socios pueden usar cookies o identificadores para servir, medir y personalizar anuncios segun la configuracion del usuario.</p>
<p>Como lector puedes administrar cookies y preferencias de anuncios desde tu navegador y desde las herramientas de privacidad de Google.</p>
""",
    },
    "contacto.html": {
        "title": "Contacto",
        "description": "Contacto editorial y tecnico de Pulso Tech Diario.",
        "body": """
<p>Para consultas editoriales, correcciones o propuestas relacionadas con Pulso Tech Diario, usa el perfil publico asociado al proyecto en GitHub.</p>
<p>Repositorio del sistema: <a href="https://github.com/elianguitarra/pulso-tech-diario" target="_blank" rel="noopener">github.com/elianguitarra/pulso-tech-diario</a>.</p>
""",
    },
}

SOURCES = [
    ("The Verge", "https://www.theverge.com/rss/index.xml"),
    ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/index"),
    ("TechCrunch", "https://techcrunch.com/feed/"),
    ("MIT Technology Review", "https://www.technologyreview.com/feed/"),
    ("Wired", "https://www.wired.com/feed/rss"),
    ("VentureBeat", "https://venturebeat.com/feed/"),
    ("Hacker News", "https://hnrss.org/frontpage"),
]

KEYWORDS = {
    "inteligencia artificial": [
        "ai",
        "artificial intelligence",
        "openai",
        "anthropic",
        "gemini",
        "llm",
        "model",
        "agents",
        "robot",
    ],
    "chips": ["chip", "semiconductor", "nvidia", "amd", "intel", "gpu", "tsmc", "arm"],
    "ciberseguridad": ["security", "hack", "breach", "malware", "privacy", "encryption", "vulnerability"],
    "startups": ["startup", "funding", "venture", "ipo", "acquisition", "raises"],
    "consumo": ["iphone", "android", "windows", "apple", "google", "samsung", "device", "app"],
    "web y plataformas": ["social", "platform", "creator", "search", "browser", "web", "cloud"],
    "ciencia": ["space", "climate", "quantum", "battery", "energy", "science", "health"],
}

SOURCE_WEIGHT = {
    "MIT Technology Review": 8,
    "Ars Technica": 7,
    "The Verge": 6,
    "Wired": 6,
    "TechCrunch": 5,
    "VentureBeat": 4,
    "Hacker News": 3,
}


@dataclass(frozen=True)
class Item:
    title: str
    link: str
    source: str
    summary: str
    published: datetime
    category: str
    score: int


def clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def fetch(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "PulsoTechDiario/1.0 (+https://github.com/elianguitarra/pulso-tech-diario)",
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
        },
    )
    with urllib.request.urlopen(request, timeout=18) as response:
        return response.read()


def parse_date(value: str) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    try:
        parsed = email.utils.parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return datetime.now(timezone.utc)


def find_child_text(node: ET.Element, names: Iterable[str]) -> str:
    for name in names:
        found = node.find(name)
        if found is not None and found.text:
            return found.text
    for child in node:
        local_name = child.tag.rsplit("}", 1)[-1].lower()
        if local_name in names and child.text:
            return child.text
    return ""


def detect_category(title: str, summary: str) -> tuple[str, int]:
    haystack = f"{title} {summary}".lower()
    best_category = "tecnologia"
    best_score = 0
    for category, keywords in KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in haystack)
        if score > best_score:
            best_category = category
            best_score = score
    return best_category, best_score


def score_item(source: str, title: str, summary: str, published: datetime, category_score: int) -> int:
    age_hours = max(0.0, (datetime.now(timezone.utc) - published).total_seconds() / 3600)
    freshness = max(0, 24 - int(age_hours / 2))
    signal_terms = ["launch", "release", "breakthrough", "lawsuit", "ban", "deal", "report", "new", "first"]
    signal = sum(2 for term in signal_terms if term in f"{title} {summary}".lower())
    return SOURCE_WEIGHT.get(source, 3) + freshness + category_score * 5 + signal


def parse_feed(source: str, payload: bytes) -> list[Item]:
    root = ET.fromstring(payload)
    entries = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
    items: list[Item] = []
    for entry in entries[:20]:
        title = clean_text(find_child_text(entry, ["title"]))
        link = clean_text(find_child_text(entry, ["link"]))
        if not link:
            link_node = entry.find("{http://www.w3.org/2005/Atom}link")
            link = link_node.attrib.get("href", "") if link_node is not None else ""
        summary = clean_text(find_child_text(entry, ["description", "summary", "content"]))
        published_raw = find_child_text(entry, ["pubDate", "published", "updated"])
        published = parse_date(published_raw)
        if not title or not link:
            continue
        category, category_score = detect_category(title, summary)
        score = score_item(source, title, summary, published, category_score)
        items.append(
            Item(
                title=title,
                link=link,
                source=source,
                summary=summary[:260],
                published=published,
                category=category,
                score=score,
            )
        )
    return items


def collect_items() -> list[Item]:
    collected: list[Item] = []
    for source, url in SOURCES:
        try:
            collected.extend(parse_feed(source, fetch(url)))
        except (urllib.error.URLError, ET.ParseError, TimeoutError, OSError) as exc:
            print(f"warning: could not read {source}: {exc}")
    deduped: dict[str, Item] = {}
    for item in collected:
        key = re.sub(r"[^a-z0-9]+", "", item.title.lower())[:90]
        if key not in deduped or item.score > deduped[key].score:
            deduped[key] = item
    return sorted(deduped.values(), key=lambda item: (item.score, item.published), reverse=True)[:12]


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")[:70] or "noticia"


def palette_for(category: str) -> tuple[str, str, str, str]:
    palettes = {
        "inteligencia artificial": ("#0b1220", "#2dd4bf", "#facc15", "#e0f2fe"),
        "chips": ("#171717", "#fb7185", "#38bdf8", "#f5f5f4"),
        "ciberseguridad": ("#111827", "#a3e635", "#f97316", "#ecfccb"),
        "startups": ("#1f2937", "#f59e0b", "#22c55e", "#fff7ed"),
        "consumo": ("#172554", "#f472b6", "#60a5fa", "#eff6ff"),
        "web y plataformas": ("#164e63", "#c084fc", "#fbbf24", "#ecfeff"),
        "ciencia": ("#14532d", "#67e8f9", "#fde047", "#f0fdf4"),
        "tecnologia": ("#1e293b", "#14b8a6", "#f97316", "#f8fafc"),
    }
    return palettes.get(category, palettes["tecnologia"])


def svg_for_item(item: Item, index: int) -> str:
    bg, primary, secondary, paper = palette_for(item.category)
    title_words = [word for word in re.findall(r"[A-Za-z0-9]+", item.title) if len(word) > 3][:3]
    label = " ".join(title_words).upper() or item.category.upper()
    phase = (sum(ord(ch) for ch in item.title) % 12) + 4
    rings = []
    for n in range(7):
        radius = 40 + n * 28 + (phase % 5)
        opacity = 0.10 + (n % 3) * 0.03
        rings.append(
            f'<circle cx="{160 + n * 72}" cy="{120 + (n % 2) * 70}" r="{radius}" '
            f'fill="none" stroke="{primary}" stroke-width="2" opacity="{opacity:.2f}"/>'
        )
    nodes = []
    for n in range(12):
        x = 70 + ((n * 97 + phase * 13) % 760)
        y = 72 + ((n * 61 + phase * 19) % 310)
        size = 5 + (n % 4) * 2
        nodes.append(f'<circle cx="{x}" cy="{y}" r="{size}" fill="{secondary}" opacity="0.78"/>')
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630" role="img" aria-label="{html.escape(item.category)}">
  <rect width="1200" height="630" fill="{bg}"/>
  <path d="M0 455 C180 390 298 522 474 446 C650 370 774 230 1200 274 L1200 630 L0 630 Z" fill="{primary}" opacity="0.20"/>
  <path d="M0 214 C180 120 308 264 514 184 C748 94 846 150 1200 82 L1200 0 L0 0 Z" fill="{secondary}" opacity="0.15"/>
  {''.join(rings)}
  <g opacity="0.55">{''.join(nodes)}</g>
  <g transform="translate(84 96)">
    <rect x="0" y="0" width="424" height="274" rx="22" fill="{paper}" opacity="0.95"/>
    <rect x="34" y="40" width="188" height="15" rx="7" fill="{primary}"/>
    <rect x="34" y="84" width="326" height="12" rx="6" fill="{bg}" opacity="0.22"/>
    <rect x="34" y="116" width="292" height="12" rx="6" fill="{bg}" opacity="0.18"/>
    <rect x="34" y="169" width="86" height="68" rx="14" fill="{primary}" opacity="0.90"/>
    <rect x="140" y="169" width="86" height="68" rx="14" fill="{secondary}" opacity="0.88"/>
    <rect x="246" y="169" width="86" height="68" rx="14" fill="{bg}" opacity="0.14"/>
  </g>
  <g transform="translate(570 132)">
    <circle cx="206" cy="154" r="132" fill="{primary}" opacity="0.92"/>
    <circle cx="206" cy="154" r="82" fill="{bg}" opacity="0.32"/>
    <path d="M206 34 L244 118 L336 128 L266 188 L286 280 L206 232 L126 280 L146 188 L76 128 L168 118 Z" fill="{secondary}" opacity="0.92"/>
    <path d="M30 314 L430 314" stroke="{paper}" stroke-width="6" opacity="0.42"/>
    <path d="M74 356 L388 356" stroke="{paper}" stroke-width="4" opacity="0.26"/>
  </g>
  <text x="84" y="504" fill="{paper}" font-family="Arial, Helvetica, sans-serif" font-size="42" font-weight="800">{html.escape(label[:28])}</text>
  <text x="84" y="558" fill="{paper}" font-family="Arial, Helvetica, sans-serif" font-size="24" opacity="0.82">Imagen original generada automaticamente por Pulso Tech Diario</text>
</svg>"""


def save_images(items: list[Item]) -> dict[str, str]:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    for old_image in ASSET_DIR.glob("*.svg"):
        old_image.unlink()
    image_paths = {}
    for index, item in enumerate(items):
        filename = f"{index + 1:02d}-{slugify(item.title)}.svg"
        path = ASSET_DIR / filename
        path.write_text(svg_for_item(item, index), encoding="utf-8")
        image_paths[item.link] = f"assets/images/{filename}"
    return image_paths


def reading_angle(item: Item) -> str:
    if item.category == "inteligencia artificial":
        return "Vigila el impacto en productividad, derechos de autor y nuevas interfaces de software."
    if item.category == "chips":
        return "Puede mover precios, disponibilidad de hardware y la velocidad de la siguiente ola de IA."
    if item.category == "ciberseguridad":
        return "Conviene revisar riesgos, datos expuestos y posibles acciones preventivas."
    if item.category == "startups":
        return "Senala donde los inversionistas creen que habra crecimiento durante los proximos meses."
    if item.category == "consumo":
        return "Afecta los productos, apps y servicios que millones de personas usan a diario."
    if item.category == "ciencia":
        return "Puede convertirse en infraestructura, energia o salud aplicada en el mediano plazo."
    return "Es una senal temprana de hacia donde se esta moviendo la industria tecnologica."


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def render_index(items: list[Item], image_paths: dict[str, str]) -> str:
    now = datetime.now(timezone.utc)
    lead = items[0] if items else None
    cards = []
    for rank, item in enumerate(items, start=1):
        image_path = image_paths[item.link]
        cards.append(
            f"""
        <article class="story" data-category="{esc(item.category)}">
          <a class="story-image" href="{esc(item.link)}" target="_blank" rel="noopener">
            <img src="{esc(image_path)}" alt="Imagen generada para {esc(item.title)}" loading="lazy" width="1200" height="630">
          </a>
          <div class="story-body">
            <div class="story-meta"><span>#{rank}</span><span>{esc(item.category)}</span><span>{esc(item.source)}</span></div>
            <h2><a href="{esc(item.link)}" target="_blank" rel="noopener">{esc(item.title)}</a></h2>
            <p>{esc(item.summary or reading_angle(item))}</p>
            <p class="angle">{esc(reading_angle(item))}</p>
          </div>
        </article>"""
        )
        if rank == 4:
            cards.append(ad_unit("in-grid", ADSENSE_IN_ARTICLE_SLOT, "anuncio en el resumen"))
    lead_image = image_paths[lead.link] if lead else "assets/social-card.svg"
    lead_title = lead.title if lead else "Tecnologia diaria"
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{SITE_NAME} | Tecnologia relevante cada dia</title>
  <meta name="description" content="{esc(SITE_DESCRIPTION)}">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <link rel="canonical" href="{SITE_URL}/">
  <link rel="alternate" type="application/rss+xml" title="{SITE_NAME}" href="{SITE_URL}/feed.xml">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{SITE_NAME}">
  <meta property="og:description" content="{esc(lead_title)}">
  <meta property="og:image" content="{SITE_URL}/{esc(lead_image)}">
  <meta property="og:url" content="{SITE_URL}/">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{SITE_NAME}">
  <meta name="twitter:description" content="{esc(lead_title)}">
  <meta name="twitter:image" content="{SITE_URL}/{esc(lead_image)}">
  {adsense_head()}
  <link rel="stylesheet" href="style.css">
  <script type="application/ld+json">{json.dumps(schema(items), ensure_ascii=False)}</script>
</head>
<body>
  <header class="topbar">
    <a class="brand" href="./" aria-label="{SITE_NAME}">
      <span class="brand-mark">PT</span>
      <span>{SITE_NAME}</span>
    </a>
    <nav aria-label="Acciones">
      <a href="feed.xml">RSS</a>
      <a href="acerca.html">Acerca</a>
      <a href="privacidad.html">Privacidad</a>
      <a href="https://twitter.com/intent/tweet?text={urllib.parse.quote(SITE_NAME)}&url={urllib.parse.quote(SITE_URL + '/')}" target="_blank" rel="noopener">Compartir</a>
    </nav>
  </header>

  <main>
    <section class="hero">
      <div class="hero-copy">
        <p class="kicker">Actualizado automaticamente: {now.strftime("%Y-%m-%d %H:%M UTC")}</p>
        <h1>Tecnologia importante, filtrada a diario.</h1>
        <p>{SITE_DESCRIPTION}</p>
      </div>
      <div class="hero-panel">
        <span>Nota lider</span>
        <strong>{esc(lead_title)}</strong>
      </div>
    </section>

    <section class="ticker" aria-label="Temas destacados">
      <span>IA</span><span>Chips</span><span>Ciberseguridad</span><span>Startups</span><span>Consumo</span><span>Ciencia</span>
    </section>

    {ad_unit("leaderboard", ADSENSE_TOP_SLOT, "anuncio principal")}

    <section class="grid" aria-label="Resumen diario">
      {''.join(cards)}
    </section>
  </main>

  <footer>
    <p>Creado para publicarse gratis con GitHub Pages. Las imagenes son SVG originales generadas por el build diario.</p>
    <p>Fuentes: {", ".join(esc(name) for name, _ in SOURCES)}.</p>
    <p><a href="acerca.html">Acerca de</a> · <a href="politica-editorial.html">Politica editorial</a> · <a href="privacidad.html">Privacidad</a> · <a href="contacto.html">Contacto</a></p>
  </footer>
</body>
</html>"""


def render_static_page(filename: str, page: dict[str, str]) -> str:
    title = page["title"]
    description = page["description"]
    body = page["body"]
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)} | {SITE_NAME}</title>
  <meta name="description" content="{esc(description)}">
  <meta name="robots" content="index,follow">
  <link rel="canonical" href="{SITE_URL}/{filename}">
  {adsense_head()}
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <header class="topbar">
    <a class="brand" href="./" aria-label="{SITE_NAME}">
      <span class="brand-mark">PT</span>
      <span>{SITE_NAME}</span>
    </a>
    <nav aria-label="Secciones">
      <a href="./">Inicio</a>
      <a href="feed.xml">RSS</a>
      <a href="contacto.html">Contacto</a>
    </nav>
  </header>
  <main class="page">
    <p class="kicker">Informacion del sitio</p>
    <h1>{esc(title)}</h1>
    <div class="page-body">
      {body}
    </div>
  </main>
  <footer>
    <p><a href="acerca.html">Acerca de</a> · <a href="politica-editorial.html">Politica editorial</a> · <a href="privacidad.html">Privacidad</a> · <a href="contacto.html">Contacto</a></p>
  </footer>
</body>
</html>"""


def valid_adsense_client() -> bool:
    return bool(re.fullmatch(r"ca-pub-\d{16}", ADSENSE_CLIENT))


def adsense_publisher_id() -> str:
    return ADSENSE_CLIENT.replace("ca-", "", 1)


def adsense_head() -> str:
    if not valid_adsense_client():
        return ""
    client = esc(ADSENSE_CLIENT)
    return (
        f'<meta name="google-adsense-account" content="{client}">\n'
        f'  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={client}" '
        'crossorigin="anonymous"></script>'
    )


def ad_unit(kind: str, slot: str, label: str) -> str:
    if not valid_adsense_client() or not slot:
        return ""
    return f"""
    <aside class="ad ad-{esc(kind)}" aria-label="{esc(label)}">
      <ins class="adsbygoogle"
        style="display:block"
        data-ad-client="{esc(ADSENSE_CLIENT)}"
        data-ad-slot="{esc(slot)}"
        data-ad-format="auto"
        data-full-width-responsive="true"></ins>
      <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
    </aside>"""


def schema(items: list[Item]) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "NewsMediaOrganization",
        "name": SITE_NAME,
        "url": SITE_URL,
        "description": SITE_DESCRIPTION,
        "publishingPrinciples": f"{SITE_URL}/README.md",
        "mainEntityOfPage": {
            "@type": "ItemList",
            "itemListElement": [
                {"@type": "ListItem", "position": index + 1, "url": item.link, "name": item.title}
                for index, item in enumerate(items)
            ],
        },
    }


def render_css() -> str:
    return """* { box-sizing: border-box; }
:root {
  color-scheme: light;
  --ink: #172033;
  --muted: #667085;
  --line: #d9e2ec;
  --paper: #fbfcf8;
  --accent: #0f766e;
  --hot: #e11d48;
  --sun: #f59e0b;
}
body {
  margin: 0;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: var(--paper);
  color: var(--ink);
}
a { color: inherit; text-decoration: none; }
a:hover { color: var(--accent); }
.topbar {
  min-height: 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 0 5vw;
  border-bottom: 1px solid var(--line);
  background: rgba(251, 252, 248, 0.92);
  position: sticky;
  top: 0;
  z-index: 10;
  backdrop-filter: blur(14px);
}
.brand { display: inline-flex; align-items: center; gap: 12px; font-weight: 800; }
.brand-mark {
  width: 42px;
  height: 42px;
  border-radius: 8px;
  display: inline-grid;
  place-items: center;
  color: white;
  background: #172033;
  font-weight: 900;
}
nav { display: flex; gap: 18px; color: var(--muted); font-weight: 700; font-size: 14px; }
main { width: min(1180px, 90vw); margin: 0 auto; }
.hero {
  min-height: 58vh;
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(280px, 0.8fr);
  gap: 42px;
  align-items: center;
  padding: 60px 0 42px;
}
.kicker {
  color: var(--accent);
  font-size: 14px;
  font-weight: 800;
  text-transform: uppercase;
}
h1 {
  margin: 0;
  font-size: clamp(42px, 8vw, 92px);
  line-height: 0.95;
  letter-spacing: 0;
  max-width: 850px;
}
.hero-copy > p:last-child {
  max-width: 680px;
  color: var(--muted);
  font-size: 20px;
  line-height: 1.55;
}
.hero-panel {
  min-height: 330px;
  padding: 34px;
  display: flex;
  flex-direction: column;
  justify-content: end;
  gap: 18px;
  border-left: 6px solid var(--hot);
  background:
    linear-gradient(135deg, rgba(15, 118, 110, 0.10), rgba(245, 158, 11, 0.18)),
    #eef6f2;
}
.hero-panel span { color: var(--hot); font-weight: 900; text-transform: uppercase; font-size: 13px; }
.hero-panel strong { font-size: 28px; line-height: 1.15; }
.ticker {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 28px;
  padding: 18px 0;
  border-block: 1px solid var(--line);
}
.ad {
  min-height: 110px;
  margin: 10px 0 28px;
  display: block;
  border-block: 1px solid var(--line);
  padding: 12px 0;
  overflow: hidden;
}
.ad-in-grid {
  grid-column: 1 / -1;
  margin: 0;
}
.ticker span {
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 10px 14px;
  background: white;
  color: #334155;
  font-weight: 800;
}
.grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 22px; padding: 12px 0 64px; }
.story {
  background: white;
  border: 1px solid var(--line);
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 100%;
}
.story:first-child { grid-column: span 2; }
.story-image { display: block; aspect-ratio: 1200 / 630; background: #e2e8f0; overflow: hidden; }
.story-image img { width: 100%; height: 100%; object-fit: cover; display: block; transition: transform 0.2s ease; }
.story:hover img { transform: scale(1.025); }
.story-body { padding: 20px; display: flex; flex-direction: column; gap: 12px; }
.story-meta { display: flex; flex-wrap: wrap; gap: 8px; color: var(--muted); font-size: 12px; font-weight: 900; text-transform: uppercase; }
.story h2 { margin: 0; font-size: 22px; line-height: 1.16; letter-spacing: 0; }
.story p { margin: 0; color: #475569; line-height: 1.52; }
.story .angle {
  color: #123f3c;
  font-weight: 750;
  border-top: 1px solid var(--line);
  padding-top: 12px;
}
footer {
  border-top: 1px solid var(--line);
  padding: 28px 5vw 44px;
  color: var(--muted);
  font-size: 14px;
}
footer a { color: var(--ink); font-weight: 750; }
.page {
  min-height: 62vh;
  padding: 58px 0 72px;
  max-width: 780px;
}
.page h1 {
  font-size: clamp(40px, 7vw, 74px);
  line-height: 1;
  margin-bottom: 28px;
}
.page-body {
  display: grid;
  gap: 18px;
  color: #334155;
  font-size: 19px;
  line-height: 1.7;
}
.page-body p { margin: 0; }
.page-body a {
  color: var(--accent);
  font-weight: 800;
  text-decoration: underline;
  text-underline-offset: 3px;
}
@media (max-width: 920px) {
  .hero { grid-template-columns: 1fr; min-height: auto; }
  .grid { grid-template-columns: 1fr 1fr; }
  .story:first-child { grid-column: span 2; }
}
@media (max-width: 640px) {
  .topbar { align-items: flex-start; flex-direction: column; padding-block: 14px; }
  main { width: min(100% - 28px, 1180px); }
  .hero { padding-top: 36px; gap: 24px; }
  .hero-panel { min-height: 230px; padding: 24px; }
  .grid { grid-template-columns: 1fr; }
  .story:first-child { grid-column: span 1; }
  h1 { font-size: 46px; }
}
"""


def render_feed(items: list[Item]) -> str:
    now = email.utils.format_datetime(datetime.now(timezone.utc))
    entries = []
    for item in items:
        entries.append(
            f"""  <item>
    <title>{esc(item.title)}</title>
    <link>{esc(item.link)}</link>
    <guid>{esc(item.link)}</guid>
    <pubDate>{email.utils.format_datetime(item.published)}</pubDate>
    <description>{esc(item.summary or reading_angle(item))}</description>
  </item>"""
        )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>{SITE_NAME}</title>
  <link>{SITE_URL}/</link>
  <description>{esc(SITE_DESCRIPTION)}</description>
  <lastBuildDate>{now}</lastBuildDate>
{''.join(entries)}
</channel>
</rss>
"""


def render_sitemap() -> str:
    today = datetime.now(timezone.utc).date().isoformat()
    page_urls = "\n".join(
        f"""  <url>
    <loc>{SITE_URL}/{filename}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.6</priority>
  </url>"""
        for filename in STATIC_PAGES
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{SITE_URL}/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
{page_urls}
</urlset>
"""


def write_static(items: list[Item]) -> None:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    image_paths = save_images(items)
    (PUBLIC / "index.html").write_text(render_index(items, image_paths), encoding="utf-8")
    for filename, page in STATIC_PAGES.items():
        (PUBLIC / filename).write_text(render_static_page(filename, page), encoding="utf-8")
    (PUBLIC / "style.css").write_text(render_css(), encoding="utf-8")
    (PUBLIC / "feed.xml").write_text(render_feed(items), encoding="utf-8")
    (PUBLIC / "sitemap.xml").write_text(render_sitemap(), encoding="utf-8")
    (PUBLIC / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8"
    )
    (PUBLIC / f"{INDEXNOW_KEY}.txt").write_text(INDEXNOW_KEY, encoding="utf-8")
    ads_txt = PUBLIC / "ads.txt"
    if valid_adsense_client():
        ads_txt.write_text(
            f"google.com, {adsense_publisher_id()}, DIRECT, f08c47fec0942fa0\n", encoding="utf-8"
        )
    elif ads_txt.exists():
        ads_txt.unlink()
    (PUBLIC / "data.json").write_text(
        json.dumps([item.__dict__ | {"published": item.published.isoformat()} for item in items], indent=2),
        encoding="utf-8",
    )


def fallback_items() -> list[Item]:
    now = datetime.now(timezone.utc)
    samples = [
        ("La inteligencia artificial redefine el software de trabajo", "inteligencia artificial"),
        ("La carrera por chips mas eficientes acelera nuevos dispositivos", "chips"),
        ("La seguridad digital vuelve al centro de las decisiones tecnologicas", "ciberseguridad"),
        ("Nuevas startups empujan productos mas pequenos y utiles", "startups"),
    ]
    return [
        Item(
            title=title,
            link=SITE_URL,
            source=SITE_NAME,
            summary="Contenido temporal generado cuando las fuentes RSS no estan disponibles.",
            published=now,
            category=category,
            score=1,
        )
        for title, category in samples
    ]


def main() -> None:
    items = collect_items()
    if not items:
        items = fallback_items()
    write_static(items)
    print(f"built {len(items)} stories in {PUBLIC}")


if __name__ == "__main__":
    main()
