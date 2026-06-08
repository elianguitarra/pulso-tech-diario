#!/usr/bin/env python3
"""Validate the generated preview site without external test dependencies."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
INDEXNOW_KEY = os.environ.get("INDEXNOW_KEY", "pulso-tech-diario-2026-indexnow-key").strip()


class SiteParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.h1_count = 0
        self.story_count = 0
        self.image_count = 0
        self.link_count = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        if tag == "h1":
            self.h1_count += 1
        if tag == "article" and "story" in (attr.get("class") or ""):
            self.story_count += 1
        if tag == "img":
            self.image_count += 1
        if tag == "a" and attr.get("href"):
            self.link_count += 1


def fail(message: str) -> None:
    raise SystemExit(f"validation failed: {message}")


def require(path: Path) -> None:
    if not path.exists():
        fail(f"missing {path.relative_to(ROOT)}")


def validate() -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build.py")], check=True, cwd=ROOT)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "generate_share_pack.py")], check=True, cwd=ROOT)
    subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; sys.path.insert(0, 'scripts'); import build as b, publish_blogger as p; items=b.fallback_items(); title=p.daily_post_title(items, '2026-01-02'); assert title.startswith('Noticias de tecnologia:') and 'Pulso Tech Diario:' not in title, title",
        ],
        check=True,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; sys.path.insert(0, 'scripts'); import build as b, publish_blogger as p; items=b.fallback_items(); html=p.post_html(items, []); blocked=['Read more','Recent posts','Post a comment','Share this','Subscribe','Search','Generated image','AI-generated','Pulso Tech Diario: 2026']; assert all(text not in html for text in blocked), html[:500]; assert 'Notas recientes' in html and 'Compartir' in html and 'Leer fuente' in html, html[:500]",
        ],
        check=True,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; sys.path.insert(0, 'scripts'); import build as b, publish_blogger as p; items=b.fallback_items(); block=p.daily_growth_block('https://pulsotechdiario.blogspot.com/example.html', items); titles=p.growth_refresh_titles(items); assert 'Hoy en Pulso Tech Diario' in block and 'Leer noticias de tecnologia de hoy' in block, block; assert len(titles) >= 9 and 'Como leer tecnologia sin ruido: metodo Pulso Tech' in titles and 'Privacidad con IA: que datos no debes subir a un chatbot' in titles, titles",
        ],
        check=True,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; sys.path.insert(0, 'scripts'); import publish_blogger as p; existing={post['title']:{'url':'https://example.com/'+str(i)} for i,post in enumerate(p.EVERGREEN_POSTS)}; guides=p.guide_posts_from(existing); assert len(guides) >= 9, guides",
        ],
        check=True,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; sys.path.insert(0, 'scripts'); import publish_blogger as p; content=p.start_here_content([('Guia prueba','https://example.com/guia')]); assert 'Mapa rapido' in content and 'Prompts de IA' in content and 'RSS del blog' in content and 'Pagina principal' in content, content",
        ],
        check=True,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    for relative in [
        "index.html",
        "style.css",
        "feed.xml",
        "feed-ia.xml",
        "feed-ciberseguridad.xml",
        "feed-chips.xml",
        "atom.xml",
        "feed.json",
        "opml.xml",
        "llms.txt",
        "humans.txt",
        "tendencias-tecnologia-hoy.html",
        "inteligencia-artificial-hoy.html",
        "ciberseguridad-hoy.html",
        "chips-ia-hoy.html",
        "sitemap.xml",
        "sitemap-index.xml",
        "news-sitemap.xml",
        "image-sitemap.xml",
        "robots.txt",
        "data.json",
        "latest.json",
        "links.html",
        "buscar.html",
        "social-payload.json",
        "assets/social-card.svg",
        "assets/social-card.png",
        "blogger-archivo.html",
        "ultima-entrada.html",
        "pulso-tech-diario.html",
        "acerca.html",
        "politica-editorial.html",
        "privacidad.html",
        "contacto.html",
        "noticias-tecnologia-espanol.html",
        "pulso-tech-diario.html",
        "buscar.html",
        "seguir.html",
        "feeds.html",
        "guias.html",
        "glosario-ia-tecnologia.html",
        "herramientas-ia-gratis.html",
        "mejor-ia-para-resumir-pdf.html",
        "alternativas-chatgpt-gratis.html",
        "prompts-chatgpt-espanol.html",
        "ia-para-hacer-presentaciones.html",
        "extensiones-chrome-productividad-ia.html",
        "crear-imagenes-ia-gratis.html",
        "prompts-para-estudiar-con-ia.html",
        "ia-para-estudiantes.html",
        "proteger-cuenta-google.html",
        "prompts-ia-productividad.html",
        "que-hacer-si-hackearon-mi-correo.html",
        "como-saber-si-un-enlace-es-seguro.html",
        "como-detectar-correo-falso.html",
        "recuperar-whatsapp-hackeado.html",
        "que-son-passkeys.html",
        "como-borrar-datos-personales-google.html",
        "vpn-gratis-es-segura.html",
        "contrasena-filtrada-que-hacer.html",
        "estafa-whatsapp-que-hacer.html",
        "mejor-antivirus-gratis-windows.html",
        "laptop-con-npu-vale-la-pena.html",
        "automatizar-blogger-gratis.html",
        "chatgpt-gemini-claude.html",
        "temas.html",
        "inteligencia-artificial.html",
        "ciberseguridad.html",
        "chips-hardware.html",
        "ia-en-el-trabajo.html",
        "comprar-laptop-para-ia.html",
        "que-es-ia-local.html",
        "npu-vs-gpu.html",
        "privacidad-chatbots-ia.html",
        "checklist-phishing.html",
        f"{INDEXNOW_KEY}.txt",
    ]:
        require(PUBLIC / relative)

    parser = SiteParser()
    parser.feed((PUBLIC / "index.html").read_text(encoding="utf-8"))
    index_text = (PUBLIC / "index.html").read_text(encoding="utf-8")
    if parser.h1_count != 1:
        fail(f"expected one h1, found {parser.h1_count}")
    if parser.story_count < 4:
        fail(f"expected at least 4 stories, found {parser.story_count}")
    if parser.image_count != parser.story_count:
        fail(f"expected one image per story, found {parser.image_count} images for {parser.story_count} stories")
    if parser.link_count < parser.story_count:
        fail("expected story links")
    if "noticias/01-" not in index_text or "Fuente original" not in index_text:
        fail("index missing internal story links")
    for guide_page in [
        "que-es-ia-local.html",
        "npu-vs-gpu.html",
        "privacidad-chatbots-ia.html",
        "checklist-phishing.html",
        "noticias-tecnologia-espanol.html",
        "pulso-tech-diario.html",
        "seguir.html",
        "tendencias-tecnologia-hoy.html",
        "inteligencia-artificial-hoy.html",
        "ciberseguridad-hoy.html",
        "chips-ia-hoy.html",
        "glosario-ia-tecnologia.html",
        "guias.html",
        "herramientas-ia-gratis.html",
        "mejor-ia-para-resumir-pdf.html",
        "alternativas-chatgpt-gratis.html",
        "prompts-chatgpt-espanol.html",
        "ia-para-hacer-presentaciones.html",
        "extensiones-chrome-productividad-ia.html",
        "crear-imagenes-ia-gratis.html",
        "prompts-para-estudiar-con-ia.html",
        "ia-para-estudiantes.html",
        "proteger-cuenta-google.html",
        "prompts-ia-productividad.html",
        "que-hacer-si-hackearon-mi-correo.html",
        "como-saber-si-un-enlace-es-seguro.html",
        "como-detectar-correo-falso.html",
        "recuperar-whatsapp-hackeado.html",
        "que-son-passkeys.html",
        "como-borrar-datos-personales-google.html",
        "vpn-gratis-es-segura.html",
        "contrasena-filtrada-que-hacer.html",
        "estafa-whatsapp-que-hacer.html",
        "mejor-antivirus-gratis-windows.html",
        "laptop-con-npu-vale-la-pena.html",
        "automatizar-blogger-gratis.html",
    ]:
        if guide_page not in index_text:
            fail(f"index missing evergreen guide link {guide_page}")

    ET.parse(PUBLIC / "feed.xml")
    feed_text = (PUBLIC / "feed.xml").read_text(encoding="utf-8")
    if "rel=\"hub\"" not in feed_text or "pubsubhubbub.appspot.com" not in feed_text:
        fail("feed.xml missing WebSub hub discovery")
    if "<link>https://elianguitarra.github.io/pulso-tech-diario/noticias/" not in feed_text:
        fail("feed.xml missing internal story URLs")
    atom_root = ET.parse(PUBLIC / "atom.xml").getroot()
    atom_text = ET.tostring(atom_root, encoding="unicode")
    if "Atom" not in atom_text and not atom_root.tag.endswith("feed"):
        fail("atom.xml is not an Atom feed")
    if "rel=\"hub\"" not in atom_text or "pubsubhubbub.appspot.com" not in atom_text:
        fail("atom.xml missing WebSub hub discovery")
    if "https://elianguitarra.github.io/pulso-tech-diario/noticias/" not in atom_text:
        fail("atom.xml missing internal story URLs")
    json_feed = json.loads((PUBLIC / "feed.json").read_text(encoding="utf-8"))
    if json_feed.get("version") != "https://jsonfeed.org/version/1.1" or len(json_feed.get("items", [])) < parser.story_count:
        fail("feed.json missing JSON Feed payload")
    if not all(item.get("url", "").startswith("https://elianguitarra.github.io/pulso-tech-diario/noticias/") for item in json_feed.get("items", [])):
        fail("feed.json items should point to internal story URLs")
    if "atom.xml" not in index_text or "feed.json" not in index_text or "feed-ia.xml" not in index_text or "feed-ciberseguridad.xml" not in index_text or "feed-chips.xml" not in index_text or "feeds.html" not in index_text:
        fail("index missing alternate feed links")
    for topic_feed, phrase in {
        "feed-ia.xml": "Pulso Tech Diario IA",
        "feed-ciberseguridad.xml": "Pulso Tech Diario Ciberseguridad",
        "feed-chips.xml": "Pulso Tech Diario Chips",
    }.items():
        topic_root = ET.parse(PUBLIC / topic_feed).getroot()
        topic_text = ET.tostring(topic_root, encoding="unicode")
        if phrase not in topic_text or "rel=\"hub\"" not in topic_text or "https://elianguitarra.github.io/pulso-tech-diario/noticias/" not in topic_text:
            fail(f"{topic_feed} missing topic RSS content or WebSub hub")
    ET.parse(PUBLIC / "opml.xml")
    opml_text = (PUBLIC / "opml.xml").read_text(encoding="utf-8")
    if "RSS de Blogger" not in opml_text or "feed.xml" not in opml_text or "feed-ia.xml" not in opml_text or "feed-ciberseguridad.xml" not in opml_text or "feed-chips.xml" not in opml_text or "atom.xml" not in opml_text:
        fail("opml.xml missing feed bundle")
    news_root = ET.parse(PUBLIC / "news-sitemap.xml").getroot()
    news_text = ET.tostring(news_root, encoding="unicode")
    if "sitemap-news" not in news_text:
        fail("news sitemap missing news namespace")
    news_titles = news_root.findall(".//{http://www.google.com/schemas/sitemap-news/0.9}title")
    if len(news_titles) < parser.story_count:
        fail("news sitemap missing story titles")
    if "https://elianguitarra.github.io/pulso-tech-diario/noticias/" not in news_text:
        fail("news sitemap missing internal story URLs")
    robots_text = (PUBLIC / "robots.txt").read_text(encoding="utf-8")
    if "sitemap-index.xml" not in robots_text or "news-sitemap.xml" not in robots_text or "image-sitemap.xml" not in robots_text:
        fail("robots.txt missing sitemap index, news or image sitemap")
    sitemap_index_root = ET.parse(PUBLIC / "sitemap-index.xml").getroot()
    sitemap_index_text = ET.tostring(sitemap_index_root, encoding="unicode")
    if not sitemap_index_root.tag.endswith("sitemapindex"):
        fail("sitemap-index.xml is not a sitemap index")
    for required_sitemap in ["sitemap.xml", "news-sitemap.xml", "image-sitemap.xml"]:
        if required_sitemap not in sitemap_index_text:
            fail(f"sitemap-index.xml missing {required_sitemap}")
    image_root = ET.parse(PUBLIC / "image-sitemap.xml").getroot()
    image_text = ET.tostring(image_root, encoding="unicode")
    image_nodes = image_root.findall(".//{http://www.google.com/schemas/sitemap-image/1.1}image")
    if len(image_nodes) < parser.story_count:
        fail("image-sitemap.xml missing image namespace or image entries")
    if "/assets/images/" not in image_text or "https://elianguitarra.github.io/pulso-tech-diario/noticias/" not in image_text:
        fail("image-sitemap.xml missing story image URLs")
    sitemap_root = ET.parse(PUBLIC / "sitemap.xml").getroot()
    sitemap_text = ET.tostring(sitemap_root, encoding="unicode")
    for page in [
        "acerca.html",
        "pulso-tech-diario.html",
        "politica-editorial.html",
        "privacidad.html",
        "contacto.html",
        "noticias-tecnologia-espanol.html",
        "seguir.html",
        "feeds.html",
        "feed-ia.xml",
        "feed-ciberseguridad.xml",
        "feed-chips.xml",
        "glosario-ia-tecnologia.html",
        "guias.html",
        "herramientas-ia-gratis.html",
        "mejor-ia-para-resumir-pdf.html",
        "alternativas-chatgpt-gratis.html",
        "prompts-chatgpt-espanol.html",
        "ia-para-hacer-presentaciones.html",
        "extensiones-chrome-productividad-ia.html",
        "crear-imagenes-ia-gratis.html",
        "prompts-para-estudiar-con-ia.html",
        "ia-para-estudiantes.html",
        "proteger-cuenta-google.html",
        "prompts-ia-productividad.html",
        "que-hacer-si-hackearon-mi-correo.html",
        "como-saber-si-un-enlace-es-seguro.html",
        "como-detectar-correo-falso.html",
        "recuperar-whatsapp-hackeado.html",
        "que-son-passkeys.html",
        "como-borrar-datos-personales-google.html",
        "vpn-gratis-es-segura.html",
        "contrasena-filtrada-que-hacer.html",
        "estafa-whatsapp-que-hacer.html",
        "mejor-antivirus-gratis-windows.html",
        "laptop-con-npu-vale-la-pena.html",
        "automatizar-blogger-gratis.html",
        "chatgpt-gemini-claude.html",
        "temas.html",
        "inteligencia-artificial.html",
        "ciberseguridad.html",
        "chips-hardware.html",
        "ia-en-el-trabajo.html",
        "comprar-laptop-para-ia.html",
        "que-es-ia-local.html",
        "npu-vs-gpu.html",
        "privacidad-chatbots-ia.html",
        "checklist-phishing.html",
        "blogger-archivo.html",
        "ultima-entrada.html",
        "buscar.html",
        "links.html",
        "social-payload.json",
        "opml.xml",
        "atom.xml",
        "feed.json",
        "tendencias-tecnologia-hoy.html",
        "inteligencia-artificial-hoy.html",
        "ciberseguridad-hoy.html",
        "chips-ia-hoy.html",
        "llms.txt",
        "humans.txt",
    ]:
        if page not in sitemap_text:
            fail(f"sitemap missing {page}")

    llms_text = (PUBLIC / "llms.txt").read_text(encoding="utf-8")
    if "Seguir el sitio" not in llms_text or "sitemap-index.xml" not in llms_text or "image-sitemap.xml" not in llms_text or "buscar.html" not in llms_text or "pulso-tech-diario.html" not in llms_text or "feeds.html" not in llms_text or "feed-ia.xml" not in llms_text or "feed-ciberseguridad.xml" not in llms_text or "feed-chips.xml" not in llms_text or "opml.xml" not in llms_text or "guias.html" not in llms_text or "herramientas-ia-gratis.html" not in llms_text or "mejor-ia-para-resumir-pdf.html" not in llms_text or "alternativas-chatgpt-gratis.html" not in llms_text or "prompts-chatgpt-espanol.html" not in llms_text or "ia-para-hacer-presentaciones.html" not in llms_text or "extensiones-chrome-productividad-ia.html" not in llms_text or "crear-imagenes-ia-gratis.html" not in llms_text or "prompts-para-estudiar-con-ia.html" not in llms_text or "como-saber-si-un-enlace-es-seguro.html" not in llms_text or "como-detectar-correo-falso.html" not in llms_text or "recuperar-whatsapp-hackeado.html" not in llms_text or "que-son-passkeys.html" not in llms_text or "como-borrar-datos-personales-google.html" not in llms_text or "vpn-gratis-es-segura.html" not in llms_text or "contrasena-filtrada-que-hacer.html" not in llms_text or "estafa-whatsapp-que-hacer.html" not in llms_text or "mejor-antivirus-gratis-windows.html" not in llms_text or "chatgpt-gemini-claude.html" not in llms_text:
        fail("llms.txt missing discovery links")
    if "https://pulsotechdiario.blogspot.com/" not in llms_text:
        fail("llms.txt missing Blogger URL")

    humans_text = (PUBLIC / "humans.txt").read_text(encoding="utf-8")
    if "Language: Spanish" not in humans_text or "GitHub Actions" not in humans_text:
        fail("humans.txt missing site metadata")

    links_text = (PUBLIC / "links.html").read_text(encoding="utf-8")
    if "utm_campaign=profile_links" not in links_text:
        fail("links.html missing profile link tracking")
    if "Ultima entrada en Blogger" not in links_text:
        fail("links.html missing latest entry link")
    search_text = (PUBLIC / "buscar.html").read_text(encoding="utf-8")
    if (
        "SearchResultsPage" not in search_text
        or "SearchAction" not in search_text
        or "SEARCH_INDEX" not in search_text
        or "mejor-ia-para-resumir-pdf.html" not in search_text
        or "alternativas-chatgpt-gratis.html" not in search_text
        or "ia-para-hacer-presentaciones.html" not in search_text
        or "crear-imagenes-ia-gratis.html" not in search_text
        or "recuperar-whatsapp-hackeado.html" not in search_text
        or "mejor-antivirus-gratis-windows.html" not in search_text
    ):
        fail("buscar.html missing internal search index or schema")
    if "\"@type\": \"WebSite\"" not in index_text or "SearchAction" not in index_text or "buscar.html?q={search_term_string}" not in index_text:
        fail("index missing SearchAction schema")

    follow_text = (PUBLIC / "seguir.html").read_text(encoding="utf-8")
    for required in ["RSS del sitio", "Atom del sitio", "JSON Feed del sitio", "RSS de Blogger", "RSS de inteligencia artificial", "RSS de ciberseguridad", "RSS de chips", "OPML", "Directorio de feeds", "Inteligencia artificial hoy"]:
        if required not in follow_text:
            fail(f"seguir.html missing {required}")
    feeds_text = (PUBLIC / "feeds.html").read_text(encoding="utf-8")
    if "Feeds RSS y OPML" not in feeds_text or "opml.xml" not in feeds_text or "RSS del blog en Blogger" not in feeds_text or "feed-ia.xml" not in feeds_text or "feed-ciberseguridad.xml" not in feeds_text or "feed-chips.xml" not in feeds_text:
        fail("feeds.html missing feed directory content")
    guides_text = (PUBLIC / "guias.html").read_text(encoding="utf-8")
    if (
        "Guias de tecnologia en espanol" not in guides_text
        or "CollectionPage" not in guides_text
        or "BreadcrumbList" not in guides_text
        or "FAQPage" not in guides_text
        or "sameAs" not in guides_text
        or "ItemList" not in guides_text
    ):
        fail("guias.html missing guide hub schema")
    brand_text = (PUBLIC / "pulso-tech-diario.html").read_text(encoding="utf-8")
    if (
        "Pulso Tech Diario: noticias de tecnologia en espanol" not in brand_text
        or "AboutPage" not in brand_text
        or "FAQPage" not in brand_text
        or "Blog principal de Pulso Tech Diario en Blogger" not in brand_text
        or "sameAs" not in brand_text
    ):
        fail("pulso-tech-diario.html missing brand discovery schema")
    for long_tail_page, phrase in {
        "herramientas-ia-gratis.html": "Herramientas de IA gratis",
        "mejor-ia-para-resumir-pdf.html": "Mejor IA para resumir PDF",
        "alternativas-chatgpt-gratis.html": "Alternativas gratis a ChatGPT",
        "prompts-chatgpt-espanol.html": "Prompts para ChatGPT en espanol",
        "ia-para-hacer-presentaciones.html": "IA para hacer presentaciones",
        "extensiones-chrome-productividad-ia.html": "Extensiones de Chrome con IA",
        "crear-imagenes-ia-gratis.html": "Crear imagenes con IA gratis",
        "prompts-para-estudiar-con-ia.html": "Prompts para estudiar con IA",
        "ia-para-estudiantes.html": "IA para estudiantes",
        "proteger-cuenta-google.html": "Como proteger tu cuenta Google",
        "prompts-ia-productividad.html": "Prompts de IA para productividad",
        "que-hacer-si-hackearon-mi-correo.html": "Que hacer si hackearon mi correo",
        "como-saber-si-un-enlace-es-seguro.html": "Como saber si un enlace es seguro",
        "como-detectar-correo-falso.html": "Como detectar un correo falso",
        "recuperar-whatsapp-hackeado.html": "WhatsApp hackeado",
        "que-son-passkeys.html": "Que son las passkeys",
        "como-borrar-datos-personales-google.html": "Como borrar datos personales de Google",
        "vpn-gratis-es-segura.html": "VPN gratis",
        "contrasena-filtrada-que-hacer.html": "Contrasena filtrada",
        "estafa-whatsapp-que-hacer.html": "Estafa por WhatsApp",
        "mejor-antivirus-gratis-windows.html": "Mejor antivirus gratis para Windows",
        "laptop-con-npu-vale-la-pena.html": "Laptop con NPU",
        "automatizar-blogger-gratis.html": "Como automatizar un blog en Blogger gratis",
    }.items():
        page_text = (PUBLIC / long_tail_page).read_text(encoding="utf-8")
        if phrase not in page_text or "FAQPage" not in page_text or "Blogger" not in page_text:
            fail(f"{long_tail_page} missing long-tail SEO content")

    trend_pages = {
        "tendencias-tecnologia-hoy.html": "Tendencias de tecnologia hoy",
        "inteligencia-artificial-hoy.html": "Inteligencia artificial hoy",
        "ciberseguridad-hoy.html": "Ciberseguridad hoy",
        "chips-ia-hoy.html": "Chips para IA hoy",
    }
    for trend_page, heading in trend_pages.items():
        trends_text = (PUBLIC / trend_page).read_text(encoding="utf-8")
        if heading not in trends_text:
            fail(f"{trend_page} missing primary heading")
        if trends_text.count('class="trend-item"') < 4:
            fail(f"{trend_page} missing daily trend items")
        if "FAQPage" not in trends_text or "ultima-entrada.html" not in trends_text:
            fail(f"{trend_page} missing FAQ schema or Blogger route")

    latest_text = (PUBLIC / "ultima-entrada.html").read_text(encoding="utf-8")
    if "utm_campaign=latest_entry" not in latest_text:
        fail("ultima-entrada.html missing latest_entry tracking")
    if "http-equiv=\"refresh\"" not in latest_text:
        fail("ultima-entrada.html missing refresh redirect")
    if "og:image" not in latest_text or "twitter:card" not in latest_text:
        fail("ultima-entrada.html missing social preview metadata")
    if "assets/social-card.png" not in latest_text:
        fail("ultima-entrada.html missing PNG daily social card")
    share_text = (PUBLIC / "share-pack.html").read_text(encoding="utf-8")
    if "assets/social-card.png" not in share_text or "og:image" not in share_text:
        fail("share-pack.html missing social card preview metadata")
    if "og:image:type\" content=\"image/png" not in share_text:
        fail("share-pack.html missing PNG social image type")
    latest_data = json.loads((PUBLIC / "latest.json").read_text(encoding="utf-8"))
    if not latest_data.get("url", "").startswith("https://pulsotechdiario.blogspot.com/"):
        fail("latest.json missing Blogger URL")
    if "utm_campaign=latest_entry" not in latest_data.get("tracked_url", ""):
        fail("latest.json missing tracked latest URL")

    social_data = json.loads((PUBLIC / "social-payload.json").read_text(encoding="utf-8"))
    required_channels = {"x", "linkedin", "whatsapp", "telegram", "reddit", "hackernews"}
    if set(social_data.get("tracked_urls", {})) != required_channels:
        fail("social-payload.json missing required tracked channels")
    if "tecnologia" not in json.dumps(social_data.get("posts", {}), ensure_ascii=False).lower():
        fail("social-payload.json missing Spanish social copy")
    if len(social_data.get("headline", "")) < 12:
        fail("social-payload.json missing useful social headline")
    if not social_data.get("image", "").endswith("/assets/social-card.png"):
        fail("social-payload.json missing PNG daily social image")
    for channel in required_channels:
        tracked = social_data["tracked_urls"].get(channel, "")
        if "utm_campaign=daily_share" not in tracked:
            fail(f"social-payload.json missing daily_share tracking for {channel}")

    social_card_text = (PUBLIC / "assets" / "social-card.svg").read_text(encoding="utf-8")
    if "PULSO TECH DIARIO" not in social_card_text or "<svg" not in social_card_text:
        fail("social-card.svg missing brand content")
    if "IA, chips y ciberseguridad" not in social_card_text and "Tecnologia importante" not in social_card_text:
        fail("social-card.svg missing useful headline")
    social_card_png = (PUBLIC / "assets" / "social-card.png").read_bytes()
    if not social_card_png.startswith(b"\x89PNG\r\n\x1a\n") or len(social_card_png) < 1000:
        fail("social-card.png is not a valid generated PNG")

    data = json.loads((PUBLIC / "data.json").read_text(encoding="utf-8"))
    if len(data) != parser.story_count:
        fail(f"data.json count {len(data)} does not match story count {parser.story_count}")
    story_dir = PUBLIC / "noticias"
    story_pages = list(story_dir.glob("*.html"))
    if len(story_pages) != parser.story_count:
        fail(f"expected {parser.story_count} story pages, found {len(story_pages)}")
    sample_story = story_pages[0].read_text(encoding="utf-8")
    if "NewsArticle" not in sample_story or "Leer fuente original" not in sample_story or "sameAs" not in sample_story:
        fail("story page missing article schema or source link")

    image_dir = PUBLIC / "assets" / "images"
    images = list(image_dir.glob("*.svg"))
    if len(images) != parser.story_count:
        fail(f"expected {parser.story_count} generated svg images, found {len(images)}")
    english_slug_markers = {
        "when",
        "what",
        "how",
        "gets",
        "launches",
        "arrives",
        "changed",
        "managing",
        "production",
        "trailer",
        "trailers",
    }
    for image in images:
        slug_words = set(image.stem.lower().split("-"))
        if slug_words & english_slug_markers:
            fail(f"generated image filename still looks English: {image.name}")

    key_text = (PUBLIC / f"{INDEXNOW_KEY}.txt").read_text(encoding="utf-8").strip()
    if key_text != INDEXNOW_KEY:
        fail("IndexNow key file content does not match expected key")

    print(
        "validation ok:",
        {
            "stories": parser.story_count,
            "images": len(images),
            "links": parser.link_count,
        },
    )


if __name__ == "__main__":
    validate()
