#!/usr/bin/env python3
"""Build Pulso Tech Diario as a zero-dependency static site."""

from __future__ import annotations

import email.utils
import html
import json
import math
import os
import re
import shutil
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
FEATURE_ASSET_SOURCE = ROOT / "assets" / "features"
FEATURE_ASSET_DEST = PUBLIC / "assets" / "features"
BRAND_ASSET_SOURCE = ROOT / "assets" / "brand"
BRAND_ASSET_DEST = PUBLIC / "assets" / "brand"

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
BLOG_URL = "https://pulsotechdiario.blogspot.com"
BLOGGER_START_URL = f"{BLOG_URL}/p/empieza-aqui.html"
BLOGGER_RSS_URL = f"{BLOG_URL}/feeds/posts/default?alt=rss"

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
    "ia-en-el-trabajo.html": {
        "title": "IA en el trabajo: donde si ahorra tiempo",
        "description": "Guia practica para saber en que tareas laborales la inteligencia artificial ayuda y donde requiere supervision humana.",
        "body": """
<p>La IA puede ahorrar tiempo, pero no en cualquier tarea. Funciona mejor cuando hay informacion clara, criterios de revision y un resultado que una persona puede comprobar.</p>
<h2>Donde suele ayudar</h2>
<p>Resumir reuniones, ordenar notas, crear primeros borradores, explicar codigo, comparar opciones, transformar formatos y preparar listas de preguntas son usos donde la IA puede reducir friccion.</p>
<h2>Donde hay que tener cuidado</h2>
<p>Decisiones legales, medicas, financieras, datos sensibles, calculos criticos o comunicados delicados requieren revision experta. La IA puede sugerir, pero no debe reemplazar responsabilidad.</p>
<h2>Como medir si sirve</h2>
<p>El beneficio no es que la herramienta suene inteligente. Mide si reduce minutos, errores o pasos repetidos. Si tienes que corregir demasiado, tal vez el flujo no esta listo.</p>
<h2>Prompts utiles</h2>
<p>Da contexto, objetivo, formato esperado y criterios de calidad. En vez de pedir hazlo mejor, pide resume en 5 puntos para un gerente que necesita decidir hoy.</p>
<h2>La regla de oro</h2>
<p>Usa IA como copiloto para avanzar mas rapido, no como piloto automatico para tareas que no puedes revisar. El ahorro real aparece cuando el humano conserva criterio.</p>
<p><a href="./">Volver al resumen diario</a></p>
""",
    },
    "comprar-laptop-para-ia.html": {
        "title": "Que revisar antes de comprar una laptop para IA",
        "description": "Guia para evaluar memoria, GPU, NPU, software, bateria y uso real antes de comprar una laptop para inteligencia artificial.",
        "body": """
<p>Las computadoras nuevas prometen funciones de IA, pero no todas sirven para lo mismo. Antes de comprar una laptop conviene mirar mas que el anuncio de AI PC.</p>
<h2>Memoria RAM</h2>
<p>La memoria importa mucho para trabajar con modelos, navegadores pesados, edicion y multitarea. Para uso moderno, 16 GB suele ser el punto de partida razonable; para trabajo pesado, mas memoria ayuda.</p>
<h2>GPU, NPU y CPU</h2>
<p>La GPU puede acelerar tareas de IA y graficos. La NPU busca eficiencia para funciones integradas. La CPU sigue importando para rendimiento general. No compres solo por una sigla.</p>
<h2>Software compatible</h2>
<p>Un chip potente no sirve de mucho si tus aplicaciones no lo aprovechan. Revisa si las herramientas que usas soportan funciones locales o aceleracion real.</p>
<h2>Bateria y temperatura</h2>
<p>La IA local puede consumir recursos. Mira resenas de autonomia, ruido y temperatura, no solo numeros de rendimiento.</p>
<h2>Compra con una tarea en mente</h2>
<p>Si solo quieres escribir, navegar y usar chatbots en la nube, no necesitas pagar de mas. Si vas a editar video, programar, generar imagenes o probar modelos locales, hardware y memoria pesan mucho mas.</p>
<p><a href="./">Volver al resumen diario</a></p>
""",
    },
    "temas.html": {
        "title": "Temas de tecnologia",
        "description": "Mapa de temas de Pulso Tech Diario para leer sobre inteligencia artificial, ciberseguridad, chips y guias practicas.",
        "body": f"""
<p>Usa este mapa para entrar por tema y encontrar lecturas recurrentes de Pulso Tech Diario.</p>
<h2>Inteligencia artificial</h2>
<p>Noticias, guias y senales sobre IA, productividad, modelos, agentes y uso responsable.</p>
<p><a href="inteligencia-artificial.html">Ver hub de inteligencia artificial</a> · <a href="{BLOG_URL}/search/label/inteligencia%20artificial">Entradas en Blogger</a></p>
<h2>Ciberseguridad</h2>
<p>Riesgos, phishing, privacidad, cuentas y decisiones practicas para usuarios y equipos.</p>
<p><a href="ciberseguridad.html">Ver hub de ciberseguridad</a> · <a href="{BLOG_URL}/search/label/ciberseguridad">Entradas en Blogger</a></p>
<h2>Chips y hardware</h2>
<p>GPU, NPU, laptops, IA local y senales de la carrera por computo.</p>
<p><a href="chips-hardware.html">Ver hub de chips y hardware</a> · <a href="{BLOG_URL}/search/label/chips">Entradas en Blogger</a></p>
""",
    },
    "inteligencia-artificial.html": {
        "title": "Inteligencia artificial: guias y noticias",
        "description": "Hub de Pulso Tech Diario para leer sobre IA, productividad, privacidad, herramientas y noticias diarias.",
        "body": f"""
<p>La inteligencia artificial cambia software, trabajo, privacidad y hardware. Este hub agrupa rutas para leer sin perderse en el ruido.</p>
<h2>Guias recomendadas</h2>
<ul>
  <li><a href="{BLOG_URL}/search/label/inteligencia%20artificial">Entradas de IA en Blogger</a></li>
  <li><a href="{BLOGGER_START_URL}">Empieza aqui en Blogger</a></li>
  <li><a href="ia-en-el-trabajo.html">IA en el trabajo: donde si ahorra tiempo</a></li>
  <li><a href="{BLOG_URL}/search/label/privacidad">Privacidad e IA</a></li>
</ul>
<h2>Que mirar</h2>
<p>Busca senales de impacto real: tareas que se vuelven mas rapidas, productos que cambian comportamiento, riesgos de datos y costos de computo.</p>
<p><a href="{BLOGGER_RSS_URL}">Seguir por RSS</a> · <a href="share-pack.html">Compartir Pulso Tech Diario</a></p>
""",
    },
    "ciberseguridad.html": {
        "title": "Ciberseguridad: phishing, privacidad y cuentas",
        "description": "Hub de Pulso Tech Diario para leer sobre phishing, privacidad, filtraciones y seguridad digital practica.",
        "body": f"""
<p>La ciberseguridad afecta cuentas, datos personales, empresas y servicios cotidianos. Este hub prioriza acciones simples y senales faciles de vigilar.</p>
<h2>Lecturas recomendadas</h2>
<ul>
  <li><a href="{BLOG_URL}/search/label/ciberseguridad">Entradas de ciberseguridad en Blogger</a></li>
  <li><a href="{BLOG_URL}/search/label/phishing">Guias sobre phishing</a></li>
  <li><a href="{BLOG_URL}/search/label/privacidad">Privacidad y datos</a></li>
  <li><a href="{BLOGGER_START_URL}">Empieza aqui en Blogger</a></li>
</ul>
<h2>Que mirar</h2>
<p>Prioriza cambios de contrasenas, verificacion en dos pasos, sesiones activas, enlaces sospechosos y datos que no deberian compartirse con herramientas externas.</p>
<p><a href="{BLOGGER_RSS_URL}">Seguir por RSS</a> · <a href="share-pack.html">Compartir Pulso Tech Diario</a></p>
""",
    },
    "chips-hardware.html": {
        "title": "Chips y hardware para IA",
        "description": "Hub de Pulso Tech Diario sobre GPU, NPU, laptops, IA local, chips y computo para inteligencia artificial.",
        "body": f"""
<p>Los chips determinan que tan rapido crecen la IA, la nube, las laptops y los dispositivos personales. Este hub junta guias y rutas de lectura.</p>
<h2>Lecturas recomendadas</h2>
<ul>
  <li><a href="{BLOG_URL}/search/label/chips">Entradas de chips en Blogger</a></li>
  <li><a href="{BLOG_URL}/search/label/ia%20local">IA local</a></li>
  <li><a href="comprar-laptop-para-ia.html">Que revisar antes de comprar una laptop para IA</a></li>
  <li><a href="{BLOGGER_START_URL}">Empieza aqui en Blogger</a></li>
</ul>
<h2>Que mirar</h2>
<p>No basta con una sigla. Revisa memoria, eficiencia, software compatible, disponibilidad, bateria y si la aplicacion que usas aprovecha realmente el hardware.</p>
<p><a href="{BLOGGER_RSS_URL}">Seguir por RSS</a> · <a href="share-pack.html">Compartir Pulso Tech Diario</a></p>
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


IMAGE_LABELS = {
    "inteligencia artificial": ["IA EN ACCION", "NUEVA SENAL IA", "FUTURO DEL SOFTWARE"],
    "chips": ["PODER DE COMPUTO", "NUEVA OLA CHIP", "HARDWARE CLAVE"],
    "ciberseguridad": ["ALERTA DIGITAL", "DATOS EN RIESGO", "DEFENSA ACTIVA"],
    "startups": ["CAPITAL TEC", "NUEVA APUESTA", "MERCADO EMERGENTE"],
    "consumo": ["PRODUCTOS Y APPS", "CAMBIO DE USO", "TECNOLOGIA DIARIA"],
    "web y plataformas": ["MAPA DIGITAL", "PLATAFORMAS", "WEB EN CAMBIO"],
    "ciencia": ["CIENCIA APLICADA", "NUEVA FRONTERA", "SENAL CIENTIFICA"],
    "tecnologia": ["PULSO TEC", "SENAL CLAVE", "INDUSTRIA TECH"],
}


def image_label_for(category: str, index: int) -> str:
    labels = IMAGE_LABELS.get(category, IMAGE_LABELS["tecnologia"])
    return labels[index % len(labels)]


def svg_for_item(item: Item, index: int) -> str:
    bg, primary, secondary, paper = palette_for(item.category)
    label = image_label_for(item.category, index)
    seed = sum(ord(ch) for ch in item.title) + index * 31

    def micro_grid() -> str:
        lines = []
        for n in range(18):
            x = 60 + ((seed + n * 67) % 1080)
            y = 52 + ((seed * 3 + n * 41) % 500)
            lines.append(
                f'<path d="M{x} {y} h{36 + (n % 4) * 22} v{18 + (n % 3) * 16}" '
                f'fill="none" stroke="{paper}" stroke-width="2" opacity="0.16"/>'
            )
            lines.append(f'<circle cx="{x}" cy="{y}" r="{3 + n % 3}" fill="{secondary}" opacity="0.55"/>')
        return "".join(lines)

    def chip_visual() -> str:
        pins = []
        for n in range(12):
            pins.append(f'<rect x="{365 + n * 38}" y="156" width="14" height="52" rx="5" fill="{primary}" opacity="0.86"/>')
            pins.append(f'<rect x="{365 + n * 38}" y="422" width="14" height="52" rx="5" fill="{primary}" opacity="0.50"/>')
        return f"""
  <g transform="translate(250 95)">
    <rect x="110" y="85" width="500" height="360" rx="42" fill="{paper}" opacity="0.95"/>
    <rect x="166" y="138" width="388" height="254" rx="28" fill="{bg}" opacity="0.92"/>
    {''.join(pins)}
    <path d="M232 276 C276 194 360 180 418 238 C498 220 540 290 502 354 C452 428 304 416 252 344 C226 324 220 300 232 276 Z" fill="{primary}"/>
    <circle cx="310" cy="278" r="18" fill="{secondary}"/>
    <circle cx="430" cy="278" r="18" fill="{secondary}"/>
    <path d="M314 334 C354 362 406 362 446 334" fill="none" stroke="{paper}" stroke-width="14" stroke-linecap="round"/>
  </g>"""

    def orbit_visual() -> str:
        arcs = []
        for n in range(5):
            arcs.append(
                f'<ellipse cx="720" cy="288" rx="{170 + n * 38}" ry="{58 + n * 21}" '
                f'fill="none" stroke="{primary if n % 2 else secondary}" stroke-width="{5 if n < 2 else 3}" '
                f'opacity="{0.72 - n * 0.10}" transform="rotate({-28 + n * 15} 720 288)"/>'
            )
        return f"""
  <g>
    <circle cx="720" cy="288" r="118" fill="{primary}" opacity="0.92"/>
    <circle cx="720" cy="288" r="62" fill="{bg}" opacity="0.35"/>
    {''.join(arcs)}
    <circle cx="905" cy="226" r="22" fill="{secondary}"/>
    <circle cx="532" cy="365" r="15" fill="{paper}" opacity="0.88"/>
    <path d="M170 470 C330 385 430 492 570 410 C710 328 846 448 1040 332" fill="none" stroke="{paper}" stroke-width="12" opacity="0.28"/>
  </g>"""

    def security_visual() -> str:
        locks = []
        for n in range(5):
            x = 250 + n * 132
            y = 150 + (n % 2) * 120
            locks.append(
                f'<rect x="{x}" y="{y + 42}" width="82" height="68" rx="14" fill="{paper}" opacity="0.92"/>'
                f'<path d="M{x + 18} {y + 48} v-22 c0-48 46-48 46 0 v22" fill="none" stroke="{secondary}" stroke-width="12" stroke-linecap="round"/>'
            )
        return f"""
  <g>
    <path d="M660 90 L950 196 V330 C950 462 842 540 660 586 C478 540 370 462 370 330 V196 Z" fill="{primary}" opacity="0.90"/>
    <path d="M660 154 L872 232 V330 C872 420 790 480 660 518 C530 480 448 420 448 330 V232 Z" fill="{bg}" opacity="0.44"/>
    <path d="M590 324 L642 376 L744 260" fill="none" stroke="{secondary}" stroke-width="26" stroke-linecap="round" stroke-linejoin="round"/>
    {''.join(locks)}
  </g>"""

    def city_visual() -> str:
        buildings = []
        for n in range(11):
            x = 420 + n * 58
            h = 150 + ((seed + n * 29) % 210)
            buildings.append(f'<rect x="{x}" y="{482 - h}" width="42" height="{h}" fill="{paper}" opacity="{0.50 + (n % 3) * 0.12}"/>')
            for w in range(3):
                buildings.append(f'<rect x="{x + 9}" y="{492 - h + w * 38}" width="8" height="18" fill="{secondary}" opacity="0.70"/>')
        return f"""
  <g>
    <path d="M0 500 H1200 V630 H0 Z" fill="{primary}" opacity="0.35"/>
    {''.join(buildings)}
    <path d="M90 438 C270 382 360 492 530 410 C690 332 784 420 1038 296" fill="none" stroke="{secondary}" stroke-width="18" opacity="0.70"/>
    <circle cx="1010" cy="282" r="46" fill="{secondary}" opacity="0.92"/>
  </g>"""

    def product_visual() -> str:
        cards = []
        for n in range(4):
            x = 560 + (n % 2) * 230
            y = 110 + (n // 2) * 170
            cards.append(
                f'<rect x="{x}" y="{y}" width="190" height="126" rx="24" fill="{paper}" opacity="{0.92 - n * 0.08}"/>'
                f'<rect x="{x + 24}" y="{y + 26}" width="96" height="12" rx="6" fill="{primary}"/>'
                f'<rect x="{x + 24}" y="{y + 58}" width="132" height="10" rx="5" fill="{bg}" opacity="0.28"/>'
                f'<circle cx="{x + 146}" cy="{y + 86}" r="22" fill="{secondary}"/>'
            )
        return f"""
  <g>
    <rect x="140" y="120" width="330" height="390" rx="42" fill="{paper}" opacity="0.95"/>
    <rect x="175" y="176" width="260" height="270" rx="26" fill="{bg}" opacity="0.88"/>
    <path d="M220 314 h172 M220 362 h116" stroke="{primary}" stroke-width="18" stroke-linecap="round"/>
    <circle cx="305" cy="232" r="42" fill="{secondary}"/>
    {''.join(cards)}
  </g>"""

    def startup_visual() -> str:
        bars = []
        for n in range(7):
            h = 42 + ((seed + n * 43) % 210)
            bars.append(f'<rect x="{170 + n * 70}" y="{505 - h}" width="42" height="{h}" rx="16" fill="{primary if n % 2 else secondary}" opacity="0.82"/>')
        return f"""
  <g>
    <path d="M770 104 C842 132 906 202 926 282 C826 304 740 380 684 492 C620 404 560 330 462 292 C514 198 610 126 770 104 Z" fill="{primary}" opacity="0.95"/>
    <circle cx="742" cy="254" r="54" fill="{paper}" opacity="0.92"/>
    <path d="M654 494 C604 538 542 552 470 560 C478 488 492 426 536 376" fill="{secondary}" opacity="0.72"/>
    <path d="M808 414 C876 454 930 508 978 582" stroke="{secondary}" stroke-width="18" stroke-linecap="round"/>
    {''.join(bars)}
  </g>"""

    templates = {
        "chips": chip_visual,
        "inteligencia artificial": product_visual,
        "ciberseguridad": security_visual,
        "web y plataformas": city_visual,
        "startups": startup_visual,
        "ciencia": orbit_visual,
        "consumo": product_visual,
        "tecnologia": orbit_visual,
    }
    fallback_variants = [chip_visual, orbit_visual, security_visual, city_visual, product_visual, startup_visual]
    visual = templates.get(item.category, fallback_variants[index % len(fallback_variants)])
    if item.category in {"tecnologia", "inteligencia artificial", "consumo"}:
        visual = fallback_variants[(index + seed) % len(fallback_variants)]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630" role="img" aria-label="{html.escape(item.category)}">
  <defs>
    <radialGradient id="halo{index}" cx="70%" cy="28%" r="62%">
      <stop offset="0" stop-color="{secondary}" stop-opacity="0.58"/>
      <stop offset="0.55" stop-color="{primary}" stop-opacity="0.16"/>
      <stop offset="1" stop-color="{bg}" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="1200" height="630" fill="{bg}"/>
  <rect width="1200" height="630" fill="url(#halo{index})"/>
  <path d="M0 504 C210 410 336 548 536 456 C750 358 880 318 1200 360 L1200 630 L0 630 Z" fill="{primary}" opacity="0.23"/>
  {micro_grid()}
  {visual()}
  <rect x="58" y="54" width="1084" height="522" rx="0" fill="none" stroke="{paper}" stroke-width="3" opacity="0.22"/>
  <text x="84" y="504" fill="{paper}" font-family="Arial, Helvetica, sans-serif" font-size="48" font-weight="900">{html.escape(label[:28])}</text>
  <text x="84" y="558" fill="{paper}" font-family="Arial, Helvetica, sans-serif" font-size="26" font-weight="700" opacity="0.86">Pulso Tech Diario | {html.escape(item.category.title())}</text>
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


ENGLISH_MARKERS = {
    "the",
    "and",
    "with",
    "for",
    "from",
    "after",
    "before",
    "launches",
    "gets",
    "says",
    "new",
    "when",
    "how",
    "why",
    "what",
    "is",
    "are",
    "will",
    "can",
    "ai",
}

PHRASE_REPLACEMENTS = [
    ("artificial intelligence", "inteligencia artificial"),
    ("agentic ai", "IA agentica"),
    ("service disruption", "interrupcion del servicio"),
    ("data breach", "filtracion de datos"),
    ("held for ransom", "retenidos para exigir rescate"),
    ("all the news and trailers", "todas las noticias y avances"),
    ("release date", "fecha de lanzamiento"),
    ("isn't coming", "no llegara"),
    ("is still working", "sigue trabajando"),
    ("set free", "liberada"),
    ("superintelligence", "superinteligencia"),
    ("latest news", "ultimas noticias"),
    ("after recent delay", "tras un retraso reciente"),
    ("for the first time", "por primera vez"),
    ("explains how", "explica como"),
    ("worst breaches", "peores filtraciones"),
    ("so far", "hasta ahora"),
    ("restores access", "restablece el acceso"),
    ("after service disruption", "tras una interrupcion del servicio"),
    ("launches in", "se lanza en"),
    ("gets a", "recibe una"),
]

WORD_REPLACEMENTS = {
    "ai": "IA",
    "chief": "jefe",
    "company": "compania",
    "companies": "companias",
    "says": "dice",
    "said": "dijo",
    "new": "nuevo",
    "news": "noticias",
    "trailers": "avances",
    "showcase": "presentacion",
    "launch": "lanzamiento",
    "launches": "se lanza",
    "arrives": "llega",
    "delay": "retraso",
    "hacked": "hackeado",
    "leaked": "filtrado",
    "breaches": "filtraciones",
    "security": "seguridad",
    "access": "acceso",
    "restores": "restablece",
    "working": "trabajando",
    "superintelligence": "superinteligencia",
    "futurist": "futurista",
    "explains": "explica",
    "uses": "usa",
    "real": "real",
    "world": "mundo",
    "problem": "problema",
    "software": "software",
    "coding": "programacion",
    "solved": "resolvio",
    "exposed": "expuso",
    "every": "cada",
    "other": "otro",
    "gets": "recibe",
    "date": "fecha",
    "first": "primera",
    "time": "vez",
    "smart": "inteligente",
    "lamp": "lampara",
    "post": "poste",
    "under": "por debajo de",
    "coming": "llegando",
    "ps5": "PS5",
    "xbox": "Xbox",
    "microsoft": "Microsoft",
    "openai": "OpenAI",
    "notion": "Notion",
    "anthropic": "Anthropic",
}


def looks_english(value: str) -> bool:
    words = re.findall(r"[A-Za-z']+", value.lower())
    if not words:
        return False
    hits = sum(1 for word in words if word.strip("'") in ENGLISH_MARKERS)
    return hits >= 1 or any(word in {"ai", "xbox", "ps5", "gets", "arrives", "launches"} for word in words)


def spanishize_text(value: str) -> str:
    text = clean_text(value)
    if not text or not looks_english(text):
        return text
    text = text.replace("&#8220;", '"').replace("&#8221;", '"').replace("&#39;", "'")
    for source, target in PHRASE_REPLACEMENTS:
        text = re.sub(re.escape(source), target, text, flags=re.IGNORECASE)

    def repl(match: re.Match[str]) -> str:
        raw = match.group(0)
        translated = WORD_REPLACEMENTS.get(raw.lower())
        return translated if translated else raw

    text = re.sub(r"\b[A-Za-z][A-Za-z']*\b", repl, text)
    text = re.sub(r"\bthe\b", "el", text, flags=re.IGNORECASE)
    text = re.sub(r"\band\b", "y", text, flags=re.IGNORECASE)
    text = re.sub(r"\bfrom\b", "de", text, flags=re.IGNORECASE)
    text = re.sub(r"\bto\b", "a", text, flags=re.IGNORECASE)
    text = re.sub(r"\bfor\b", "para", text, flags=re.IGNORECASE)
    text = re.sub(r"\bafter\b", "despues de", text, flags=re.IGNORECASE)
    text = re.sub(r"\bwith\b", "con", text, flags=re.IGNORECASE)
    text = re.sub(r"\bof\b", "de", text, flags=re.IGNORECASE)
    text = re.sub(r"\bin\b", "en", text, flags=re.IGNORECASE)
    text = re.sub(r"\bis\b", "es", text, flags=re.IGNORECASE)
    text = re.sub(r"\bare\b", "son", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip(" -")
    return text[:1].upper() + text[1:]


def display_title(item: Item) -> str:
    raw = clean_text(item.title)
    if not looks_english(raw):
        return raw
    entities = extract_entities(raw)
    subject = ", ".join(entities[:2])
    if item.category == "inteligencia artificial":
        return f"IA: {subject or item.source} marca una nueva senal para la industria"
    if item.category == "ciberseguridad":
        return f"Ciberseguridad: nuevas alertas elevan la presion sobre empresas y usuarios"
    if item.category == "chips":
        return f"Chips: {subject or item.source} apunta a otra pieza clave para la nueva ola tecnologica"
    if item.category == "startups":
        return f"Startups: {subject or item.source} muestra hacia donde se mueve el capital tecnologico"
    if item.category == "consumo":
        return f"Consumo: {subject or item.source} entra en el radar de productos y plataformas"
    if item.category == "web y plataformas":
        return f"Plataformas: {subject or item.source} anticipa cambios en la web y los servicios digitales"
    if item.category == "ciencia":
        return f"Ciencia y tecnologia: {subject or item.source} abre una senal para seguir de cerca"
    return f"Tecnologia: {subject or item.source} deja una senal importante para la semana"


def display_summary(item: Item) -> str:
    raw = clean_text(item.summary)
    if raw and not looks_english(raw):
        return raw
    source = item.source
    angle = reading_angle(item)
    if item.category == "inteligencia artificial":
        return f"{source} reporta un movimiento relevante en inteligencia artificial. La clave esta en entender si cambia productividad, software o la relacion entre usuarios y herramientas digitales. {angle}"
    if item.category == "ciberseguridad":
        return f"{source} apunta a un riesgo que conviene mirar con calma: datos, accesos y confianza digital vuelven al centro de la conversacion. {angle}"
    if item.category == "chips":
        return f"{source} senala otro paso en la carrera por computo, hardware y capacidad para ejecutar nuevas cargas de inteligencia artificial. {angle}"
    if item.category == "consumo":
        return f"{source} destaca una novedad que puede afectar productos, apps o servicios usados a diario. {angle}"
    if item.category == "web y plataformas":
        return f"{source} muestra una senal sobre plataformas, busqueda, creadores o servicios cloud. {angle}"
    if item.category == "startups":
        return f"{source} recoge una pista sobre inversion, adquisiciones o productos emergentes en tecnologia. {angle}"
    return f"{source} reporta una senal tecnologica relevante. {angle}"


def extract_entities(value: str) -> list[str]:
    ignore = {
        "The",
        "This",
        "That",
        "When",
        "How",
        "What",
        "Why",
        "Where",
        "Which",
        "After",
        "Before",
        "For",
        "With",
        "From",
        "Into",
        "Over",
        "Under",
        "All",
        "Every",
        "Other",
        "More",
        "Less",
        "New",
        "Latest",
        "First",
        "Last",
        "Next",
        "Show",
        "Hacked",
        "Leaked",
        "Changed",
        "Managing",
        "Production",
        "Problem",
        "Solved",
        "Explains",
        "Launches",
        "Arrives",
        "Gets",
        "Says",
        "Could",
        "Would",
        "Should",
        "Will",
        "Can",
        "AI",
        "Agentic",
        "Games",
        "Campaign",
        "February",
        "Dungeons",
    }
    entities = []
    for match in re.findall(r"\b(?:[A-Z][A-Za-z0-9]+|[A-Z]{2,}|[A-Za-z]+(?:\d+))\b", value):
        if match not in ignore and match not in entities:
            entities.append(match)
    return entities


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
            <img src="{esc(image_path)}" alt="{esc(display_title(item))}" loading="lazy" width="1200" height="630">
          </a>
          <div class="story-body">
            <div class="story-meta"><span>#{rank}</span><span>{esc(item.category)}</span><span>{esc(item.source)}</span></div>
            <h2><a href="{esc(item.link)}" target="_blank" rel="noopener">{esc(display_title(item))}</a></h2>
            <p>{esc(display_summary(item))}</p>
            <p class="angle">{esc(reading_angle(item))}</p>
          </div>
        </article>"""
        )
        if rank == 4:
            cards.append(ad_unit("in-grid", ADSENSE_IN_ARTICLE_SLOT, "anuncio en el resumen"))
    lead_image = image_paths[lead.link] if lead else "assets/social-card.svg"
    lead_title = display_title(lead) if lead else "Tecnologia diaria"
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
      <a href="temas.html">Temas</a>
      <a href="share-pack.html">Compartir</a>
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

    <section class="blogger-cta" aria-label="Leer el blog principal">
      <div>
        <p class="kicker">Blog principal</p>
        <h2>Lee la version completa en Blogger</h2>
        <p>Blogger es la casa principal de Pulso Tech Diario: ahi estan las entradas, etiquetas, guias y el flujo preparado para AdSense.</p>
      </div>
      <div class="cta-actions">
        <a href="{BLOG_URL}/" target="_blank" rel="noopener">Abrir Blogger</a>
        <a href="{BLOGGER_START_URL}" target="_blank" rel="noopener">Empieza aqui</a>
        <a href="temas.html">Temas</a>
        <a href="{BLOGGER_RSS_URL}" target="_blank" rel="noopener">RSS Blogger</a>
        <a href="share-pack.html">Compartir</a>
      </div>
    </section>

    {ad_unit("leaderboard", ADSENSE_TOP_SLOT, "anuncio principal")}

    <section class="grid" aria-label="Resumen diario">
      {''.join(cards)}
    </section>
  </main>

  <footer>
    <p>Creado para publicarse gratis con GitHub Pages. Las imagenes son SVG originales generadas por el build diario.</p>
    <p>Fuentes: {", ".join(esc(name) for name, _ in SOURCES)}.</p>
    <p><a href="temas.html">Temas</a> · <a href="share-pack.html">Compartir</a> · <a href="acerca.html">Acerca de</a> · <a href="politica-editorial.html">Politica editorial</a> · <a href="privacidad.html">Privacidad</a> · <a href="contacto.html">Contacto</a></p>
  </footer>
</body>
</html>"""


def render_static_page(filename: str, page: dict[str, str]) -> str:
    title = page["title"]
    description = page["description"]
    body = page["body"]
    canonical = f"{SITE_URL}/{filename}"
    social_image = f"{SITE_URL}/assets/brand/pulso-tech-avatar.png"
    page_schema = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": title,
        "description": description,
        "url": canonical,
        "isPartOf": {
            "@type": "WebSite",
            "name": SITE_NAME,
            "url": SITE_URL,
        },
        "publisher": {
            "@type": "Organization",
            "name": SITE_NAME,
            "url": SITE_URL,
            "logo": social_image,
        },
    }
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)} | {SITE_NAME}</title>
  <meta name="description" content="{esc(description)}">
  <meta name="robots" content="index,follow">
  <link rel="canonical" href="{canonical}">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="{SITE_NAME}">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="{social_image}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(title)}">
  <meta name="twitter:description" content="{esc(description)}">
  <meta name="twitter:image" content="{social_image}">
  {adsense_head()}
  <link rel="stylesheet" href="style.css">
  <script type="application/ld+json">{json.dumps(page_schema, ensure_ascii=False)}</script>
</head>
<body>
  <header class="topbar">
    <a class="brand" href="./" aria-label="{SITE_NAME}">
      <span class="brand-mark">PT</span>
      <span>{SITE_NAME}</span>
    </a>
    <nav aria-label="Secciones">
      <a href="./">Inicio</a>
      <a href="temas.html">Temas</a>
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
    <p><a href="temas.html">Temas</a> · <a href="share-pack.html">Compartir</a> · <a href="acerca.html">Acerca de</a> · <a href="politica-editorial.html">Politica editorial</a> · <a href="privacidad.html">Privacidad</a> · <a href="contacto.html">Contacto</a></p>
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
                {"@type": "ListItem", "position": index + 1, "url": item.link, "name": display_title(item)}
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
.blogger-cta {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 20px;
  align-items: center;
  margin: 0 0 30px;
  padding: 24px;
  border: 1px solid var(--line);
  background: #ffffff;
}
.blogger-cta h2 {
  margin: 0 0 8px;
  font-size: 30px;
  line-height: 1.05;
}
.blogger-cta p {
  margin: 0;
  color: #475569;
  line-height: 1.55;
}
.cta-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
  max-width: 360px;
}
.cta-actions a {
  display: inline-block;
  padding: 11px 13px;
  background: var(--ink);
  color: white;
  text-decoration: none;
  font-weight: 900;
  font-size: 13px;
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
  .blogger-cta { grid-template-columns: 1fr; }
  .cta-actions { justify-content: flex-start; max-width: none; }
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
    <title>{esc(display_title(item))}</title>
    <link>{esc(item.link)}</link>
    <guid>{esc(item.link)}</guid>
    <pubDate>{email.utils.format_datetime(item.published)}</pubDate>
    <description>{esc(display_summary(item))}</description>
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
    if FEATURE_ASSET_SOURCE.exists():
        FEATURE_ASSET_DEST.mkdir(parents=True, exist_ok=True)
        for asset in FEATURE_ASSET_SOURCE.iterdir():
            if asset.is_file():
                shutil.copy2(asset, FEATURE_ASSET_DEST / asset.name)
    if BRAND_ASSET_SOURCE.exists():
        BRAND_ASSET_DEST.mkdir(parents=True, exist_ok=True)
        for asset in BRAND_ASSET_SOURCE.iterdir():
            if asset.is_file():
                shutil.copy2(asset, BRAND_ASSET_DEST / asset.name)
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
    public_items = []
    for item in items:
        payload = item.__dict__ | {"published": item.published.isoformat()}
        payload["title"] = display_title(item)
        payload["summary"] = display_summary(item)
        public_items.append(payload)
    (PUBLIC / "data.json").write_text(json.dumps(public_items, indent=2), encoding="utf-8")


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
