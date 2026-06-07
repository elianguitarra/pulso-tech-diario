#!/usr/bin/env python3
"""Notify IndexNow-compatible search engines after a successful deploy."""

from __future__ import annotations

import argparse
import json
import os
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
SITE_URL = os.environ.get("SITE_URL", "https://elianguitarra.github.io/pulso-tech-diario").rstrip("/")
INDEXNOW_KEY = os.environ.get("INDEXNOW_KEY", "pulso-tech-diario-2026-indexnow-key").strip()
INDEXNOW_ENDPOINT = os.environ.get("INDEXNOW_ENDPOINT", "https://api.indexnow.org/indexnow").strip()


def sitemap_urls(path: Path) -> list[str]:
    root = ET.parse(path).getroot()
    urls: list[str] = []
    for node in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
        if node.text:
            urls.append(node.text.strip())
    return urls


def submit(urls: list[str]) -> int:
    parsed = urllib.parse.urlparse(SITE_URL)
    key_location = f"{SITE_URL}/{INDEXNOW_KEY}.txt"
    payload = {
        "host": parsed.netloc,
        "key": INDEXNOW_KEY,
        "keyLocation": key_location,
        "urlList": urls,
    }
    request = urllib.request.Request(
        INDEXNOW_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.status


def main() -> None:
    parser = argparse.ArgumentParser(description="Submit the generated sitemap URLs to IndexNow.")
    parser.add_argument("--sitemap", default=str(PUBLIC / "sitemap.xml"), help="Path to generated sitemap.xml.")
    parser.add_argument("--dry-run", action="store_true", help="Validate payload without calling IndexNow.")
    args = parser.parse_args()

    urls = sitemap_urls(Path(args.sitemap))
    if not urls:
        raise SystemExit("No URLs found in sitemap.")
    if args.dry_run:
        print(json.dumps({"key": INDEXNOW_KEY, "site": SITE_URL, "urls": urls}, indent=2))
        return
    status = submit(urls)
    print(f"IndexNow submitted {len(urls)} URLs with status {status}.")


if __name__ == "__main__":
    main()
