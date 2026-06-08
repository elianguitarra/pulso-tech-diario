#!/usr/bin/env python3
"""Notify WebSub hubs that the public feeds changed."""

from __future__ import annotations

import argparse
import os
import urllib.parse
import urllib.request


SITE_URL = os.environ.get("SITE_URL", "https://elianguitarra.github.io/pulso-tech-diario").rstrip("/")
WEBSUB_HUB_URL = os.environ.get("WEBSUB_HUB_URL", "https://pubsubhubbub.appspot.com/").strip()
FEEDS = [
    f"{SITE_URL}/feed.xml",
    f"{SITE_URL}/atom.xml",
]


def feed_urls_from(args_feeds: list[str]) -> list[str]:
    env_feeds = [
        feed.strip()
        for feed in os.environ.get("WEBSUB_FEEDS", "").split(",")
        if feed.strip()
    ]
    feeds = args_feeds or env_feeds or FEEDS
    unique_feeds = []
    for feed in feeds:
        if feed not in unique_feeds:
            unique_feeds.append(feed)
    return unique_feeds


def notify(feed_urls: list[str], dry_run: bool = False) -> None:
    fields: list[tuple[str, str]] = [("hub.mode", "publish")]
    fields.extend(("hub.url", url) for url in feed_urls)
    body = urllib.parse.urlencode(fields).encode("utf-8")
    if dry_run:
        print(f"WebSub dry-run: {len(feed_urls)} feeds -> {WEBSUB_HUB_URL}")
        for url in feed_urls:
            print(f"- {url}")
        return
    request = urllib.request.Request(
        WEBSUB_HUB_URL,
        data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "PulsoTechDiarioWebSub/1.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        status = response.status
    print(f"WebSub notified {len(feed_urls)} feeds with status {status}.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Notify WebSub hubs after feed updates.")
    parser.add_argument("--dry-run", action="store_true", help="Build the request without calling the hub.")
    parser.add_argument("--feed", action="append", default=[], help="Feed URL to notify. Can be passed more than once.")
    args = parser.parse_args()
    notify(feed_urls_from(args.feed), dry_run=args.dry_run)


if __name__ == "__main__":
    main()
