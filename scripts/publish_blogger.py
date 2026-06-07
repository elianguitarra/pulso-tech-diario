#!/usr/bin/env python3
"""Publish the daily tech digest to Blogger.

Required environment variables:
- BLOGGER_BLOG_ID
- GOOGLE_CLIENT_ID
- GOOGLE_CLIENT_SECRET
- GOOGLE_REFRESH_TOKEN
"""

from __future__ import annotations

import html
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import build


TOKEN_URL = "https://oauth2.googleapis.com/token"
BLOGGER_API = "https://www.googleapis.com/blogger/v3"
BLOGGER_SCOPE = "https://www.googleapis.com/auth/blogger"


def required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def request_json(url: str, method: str = "GET", token: str | None = None, payload: dict | None = None) -> dict:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def get_access_token() -> str:
    form = urllib.parse.urlencode(
        {
            "client_id": required_env("GOOGLE_CLIENT_ID"),
            "client_secret": required_env("GOOGLE_CLIENT_SECRET"),
            "refresh_token": required_env("GOOGLE_REFRESH_TOKEN"),
            "grant_type": "refresh_token",
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        TOKEN_URL,
        data=form,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload["access_token"]


def compact_svg(svg: str) -> str:
    return " ".join(svg.split())


def post_html(items: list[build.Item]) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    blocks = [
        f"""
<p><strong>Pulso Tech Diario</strong> selecciona automaticamente las noticias tecnologicas mas relevantes del dia. Cada bloque incluye una imagen original generada por el propio sistema.</p>
<p><em>Actualizado: {today} UTC.</em></p>
"""
    ]
    for index, item in enumerate(items, start=1):
        svg = compact_svg(build.svg_for_item(item, index))
        blocks.append(
            f"""
<section style="border-top:1px solid #d9e2ec;padding:24px 0;margin:0;">
  <div style="width:100%;max-width:900px;overflow:hidden;border-radius:8px;">{svg}</div>
  <p style="margin:16px 0 6px;color:#667085;font-weight:700;text-transform:uppercase;">#{index} · {html.escape(item.category)} · {html.escape(item.source)}</p>
  <h2 style="margin:0 0 10px;font-size:28px;line-height:1.15;"><a href="{html.escape(item.link)}" target="_blank" rel="noopener">{html.escape(item.title)}</a></h2>
  <p>{html.escape(item.summary or build.reading_angle(item))}</p>
  <p><strong>Por que importa:</strong> {html.escape(build.reading_angle(item))}</p>
</section>
"""
        )
    adsense_client = os.environ.get("ADSENSE_CLIENT", "").strip()
    if adsense_client:
        blocks.append(
            "<p><small>Monetizacion: este blog esta preparado para AdSense desde la configuracion de Blogger y ads.txt personalizado.</small></p>"
        )
    return "\n".join(blocks)


def already_published(blog_id: str, token: str, title: str) -> bool:
    query = urllib.parse.urlencode({"q": title, "maxResults": "5"})
    url = f"{BLOGGER_API}/blogs/{blog_id}/posts?{query}"
    try:
        payload = request_json(url, token=token)
    except Exception:
        return False
    return any(post.get("title") == title for post in payload.get("items", []))


def publish() -> None:
    blog_id = required_env("BLOGGER_BLOG_ID")
    token = get_access_token()
    items = build.collect_items() or build.fallback_items()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    title = f"Pulso Tech Diario: {today}"
    if already_published(blog_id, token, title):
        print(f"Post already exists: {title}")
        return
    payload = {
        "kind": "blogger#post",
        "blog": {"id": blog_id},
        "title": title,
        "labels": ["tecnologia", "inteligencia artificial", "noticias tech", "pulso tech diario"],
        "content": post_html(items),
    }
    url = f"{BLOGGER_API}/blogs/{blog_id}/posts/"
    result = request_json(url, method="POST", token=token, payload=payload)
    print(f"Published: {result.get('url', result.get('id'))}")


if __name__ == "__main__":
    try:
        publish()
    except urllib.error.HTTPError as exc:
        sys.stderr.write(exc.read().decode("utf-8", errors="replace"))
        raise
