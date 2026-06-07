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

BASE_PAGES = {
    "Acerca de": """
<p><strong>Pulso Tech Diario</strong> es un blog automatizado que resume noticias tecnologicas relevantes cada dia.</p>
<p>El objetivo es ayudar a lectores ocupados a detectar senales importantes sobre inteligencia artificial, chips, ciberseguridad, startups, consumo digital, ciencia aplicada y plataformas web.</p>
<p>El sistema revisa fuentes publicas por RSS, ordena las notas por frescura, relevancia tematica y fuente, y enlaza siempre al articulo original.</p>
""",
    "Politica editorial": """
<p>Pulso Tech Diario no copia articulos completos. Cada entrada usa fragmentos breves, resumen editorial propio y enlaces directos a las fuentes originales.</p>
<p>Las notas se seleccionan automaticamente con reglas de relevancia, pero el blog prioriza contenido informativo, trazable y util para lectores interesados en tecnologia.</p>
<p>Las imagenes que acompanan cada noticia son ilustraciones SVG originales generadas automaticamente para este blog. No representan capturas ni fotografias de los articulos enlazados.</p>
""",
    "Privacidad": """
<p>Este blog se publica en Blogger, una plataforma de Google. Blogger puede procesar datos tecnicos habituales como cookies, direccion IP, navegador, dispositivo y datos de uso.</p>
<p>Si el blog muestra anuncios mediante Google AdSense, Google y sus socios pueden usar cookies o identificadores para servir, medir y personalizar anuncios segun la configuracion del usuario.</p>
<p>Como lector puedes administrar cookies y preferencias de anuncios desde tu navegador y desde las herramientas de privacidad de Google.</p>
""",
    "Contacto": """
<p>Para consultas editoriales, correcciones o propuestas relacionadas con Pulso Tech Diario, usa el perfil publico asociado al proyecto en GitHub.</p>
<p>Repositorio del sistema: <a href="https://github.com/elianguitarra/pulso-tech-diario" target="_blank" rel="noopener">github.com/elianguitarra/pulso-tech-diario</a>.</p>
""",
}


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


def paginated_items(url: str, token: str, key: str = "items") -> list[dict]:
    items: list[dict] = []
    next_token = ""
    while True:
        page_url = url
        if next_token:
            sep = "&" if "?" in page_url else "?"
            page_url = f"{page_url}{sep}{urllib.parse.urlencode({'pageToken': next_token})}"
        payload = request_json(page_url, token=token)
        items.extend(payload.get(key, []))
        next_token = payload.get("nextPageToken", "")
        if not next_token:
            return items


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
  <p style="margin:16px 0 6px;color:#667085;font-weight:700;text-transform:uppercase;">#{index} - {html.escape(item.category)} - {html.escape(item.source)}</p>
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


def page_payload(title: str, content: str) -> dict:
    return {
        "kind": "blogger#page",
        "title": title,
        "content": content.strip(),
    }


def ensure_base_pages(blog_id: str, token: str) -> None:
    query = urllib.parse.urlencode({"fetchBodies": "false", "maxResults": "50"})
    url = f"{BLOGGER_API}/blogs/{blog_id}/pages?{query}"
    existing_pages = {page.get("title"): page for page in paginated_items(url, token=token)}
    for title, content in BASE_PAGES.items():
        payload = page_payload(title, content)
        existing = existing_pages.get(title)
        if existing and existing.get("id"):
            update_url = f"{BLOGGER_API}/blogs/{blog_id}/pages/{existing['id']}"
            request_json(update_url, method="PUT", token=token, payload=payload)
            print(f"Updated page: {title}")
        else:
            insert_url = f"{BLOGGER_API}/blogs/{blog_id}/pages"
            request_json(insert_url, method="POST", token=token, payload=payload)
            print(f"Created page: {title}")


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
    ensure_base_pages(blog_id, token)
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
