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

    for relative in [
        "index.html",
        "style.css",
        "feed.xml",
        "sitemap.xml",
        "robots.txt",
        "data.json",
        "blogger-archivo.html",
        "acerca.html",
        "politica-editorial.html",
        "privacidad.html",
        "contacto.html",
        "temas.html",
        "inteligencia-artificial.html",
        "ciberseguridad.html",
        "chips-hardware.html",
        "ia-en-el-trabajo.html",
        "comprar-laptop-para-ia.html",
        f"{INDEXNOW_KEY}.txt",
    ]:
        require(PUBLIC / relative)

    parser = SiteParser()
    parser.feed((PUBLIC / "index.html").read_text(encoding="utf-8"))
    if parser.h1_count != 1:
        fail(f"expected one h1, found {parser.h1_count}")
    if parser.story_count < 4:
        fail(f"expected at least 4 stories, found {parser.story_count}")
    if parser.image_count != parser.story_count:
        fail(f"expected one image per story, found {parser.image_count} images for {parser.story_count} stories")
    if parser.link_count < parser.story_count:
        fail("expected story links")

    ET.parse(PUBLIC / "feed.xml")
    sitemap_root = ET.parse(PUBLIC / "sitemap.xml").getroot()
    sitemap_text = ET.tostring(sitemap_root, encoding="unicode")
    for page in [
        "acerca.html",
        "politica-editorial.html",
        "privacidad.html",
        "contacto.html",
        "temas.html",
        "inteligencia-artificial.html",
        "ciberseguridad.html",
        "chips-hardware.html",
        "ia-en-el-trabajo.html",
        "comprar-laptop-para-ia.html",
        "blogger-archivo.html",
    ]:
        if page not in sitemap_text:
            fail(f"sitemap missing {page}")

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
