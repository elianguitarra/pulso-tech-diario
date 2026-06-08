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

    for relative in [
        "index.html",
        "style.css",
        "feed.xml",
        "llms.txt",
        "humans.txt",
        "sitemap.xml",
        "news-sitemap.xml",
        "robots.txt",
        "data.json",
        "latest.json",
        "links.html",
        "social-payload.json",
        "assets/social-card.svg",
        "assets/social-card.png",
        "blogger-archivo.html",
        "ultima-entrada.html",
        "acerca.html",
        "politica-editorial.html",
        "privacidad.html",
        "contacto.html",
        "noticias-tecnologia-espanol.html",
        "glosario-ia-tecnologia.html",
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
    for guide_page in [
        "que-es-ia-local.html",
        "npu-vs-gpu.html",
        "privacidad-chatbots-ia.html",
        "checklist-phishing.html",
        "noticias-tecnologia-espanol.html",
        "glosario-ia-tecnologia.html",
    ]:
        if guide_page not in index_text:
            fail(f"index missing evergreen guide link {guide_page}")

    ET.parse(PUBLIC / "feed.xml")
    news_root = ET.parse(PUBLIC / "news-sitemap.xml").getroot()
    news_text = ET.tostring(news_root, encoding="unicode")
    if "sitemap-news" not in news_text:
        fail("news sitemap missing news namespace")
    news_titles = news_root.findall(".//{http://www.google.com/schemas/sitemap-news/0.9}title")
    if len(news_titles) < parser.story_count:
        fail("news sitemap missing story titles")
    robots_text = (PUBLIC / "robots.txt").read_text(encoding="utf-8")
    if "news-sitemap.xml" not in robots_text:
        fail("robots.txt missing news sitemap")
    sitemap_root = ET.parse(PUBLIC / "sitemap.xml").getroot()
    sitemap_text = ET.tostring(sitemap_root, encoding="unicode")
    for page in [
        "acerca.html",
        "politica-editorial.html",
        "privacidad.html",
        "contacto.html",
        "noticias-tecnologia-espanol.html",
        "glosario-ia-tecnologia.html",
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
        "links.html",
        "social-payload.json",
        "llms.txt",
        "humans.txt",
    ]:
        if page not in sitemap_text:
            fail(f"sitemap missing {page}")

    llms_text = (PUBLIC / "llms.txt").read_text(encoding="utf-8")
    if "Payload social diario" not in llms_text or "chatgpt-gemini-claude.html" not in llms_text:
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

    image_dir = PUBLIC / "assets" / "images"
    images = list(image_dir.glob("*.svg"))
    if len(images) != parser.story_count:
        fail(f"expected {parser.story_count} generated svg images, found {len(images)}")

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
