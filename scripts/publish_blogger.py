#!/usr/bin/env python3
"""Publish the daily tech digest to Blogger.

Required environment variables:
- BLOGGER_BLOG_ID
- GOOGLE_CLIENT_ID
- GOOGLE_REFRESH_TOKEN

Optional environment variables:
- GOOGLE_CLIENT_SECRET
"""

from __future__ import annotations

import html
import json
import os
import sys
import time
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

EVERGREEN_POSTS = [
    {
        "title": "Como leer tecnologia sin ruido: metodo Pulso Tech",
        "labels": ["tecnologia", "guia", "pulso tech diario"],
        "content": """
<p>La tecnologia produce demasiadas noticias para leerlas todas. Pulso Tech Diario usa una regla sencilla: priorizar senales que puedan cambiar productos, trabajo, seguridad, inversion o comportamiento de usuarios.</p>
<h2>1. Frescura con contexto</h2>
<p>Una noticia reciente importa mas cuando encaja en una tendencia mayor: nuevas capacidades de inteligencia artificial, cambios en chips, regulacion, ciberseguridad o plataformas que concentran usuarios.</p>
<h2>2. Fuente y trazabilidad</h2>
<p>Cada resumen enlaza a la fuente original o a la publicacion que reporta la noticia. El objetivo no es sustituir al articulo completo, sino ayudarte a decidir que merece tu atencion.</p>
<h2>3. Impacto practico</h2>
<p>Una nota se vuelve relevante cuando responde una pregunta: que cambia para usuarios, empresas, desarrolladores, creadores o inversores.</p>
<h2>4. Menos volumen, mas senal</h2>
<p>El blog no intenta cubrirlo todo. Prefiere una seleccion corta con imagenes originales, etiquetas claras y una explicacion rapida de por que importa.</p>
""",
    },
    {
        "title": "Glosario rapido de inteligencia artificial para lectores ocupados",
        "labels": ["inteligencia artificial", "guia", "tecnologia"],
        "content": """
<p>La inteligencia artificial avanza rapido, pero muchas noticias usan los mismos terminos. Este glosario explica los conceptos que aparecen con mas frecuencia en Pulso Tech Diario.</p>
<h2>Modelo fundacional</h2>
<p>Sistema entrenado con grandes cantidades de datos que puede adaptarse a tareas como texto, codigo, imagenes, audio o analisis.</p>
<h2>Agente</h2>
<p>Software que no solo responde, sino que puede planear pasos, usar herramientas y completar tareas con cierto grado de autonomia.</p>
<h2>Inferencia</h2>
<p>Momento en el que un modelo ya entrenado genera una respuesta. Es importante porque consume computo, energia y dinero.</p>
<h2>Ventana de contexto</h2>
<p>Cantidad de informacion que un modelo puede considerar al responder. Ventanas mas grandes permiten analizar documentos, historiales o proyectos completos.</p>
<h2>Modelo abierto</h2>
<p>Modelo que permite algun nivel de descarga, inspeccion o uso local. No todos los modelos abiertos tienen las mismas licencias ni el mismo nivel de transparencia.</p>
""",
    },
    {
        "title": "Senales que miramos cada dia en chips, seguridad y startups",
        "labels": ["chips", "ciberseguridad", "startups", "guia"],
        "content": """
<p>Las noticias tecnologicas suelen parecer aisladas. Pulso Tech Diario las agrupa en senales porque una sola nota rara vez explica todo el movimiento de la industria.</p>
<h2>Chips</h2>
<p>Seguimos avances en GPU, semiconductores, fabricacion y eficiencia energetica porque determinan que tan rapido pueden crecer la IA, los dispositivos y la nube.</p>
<h2>Ciberseguridad</h2>
<p>Brechas, vulnerabilidades y ataques importan cuando exponen datos, cambian practicas de defensa o afectan infraestructura usada por muchas personas.</p>
<h2>Startups</h2>
<p>Financiamientos, adquisiciones y lanzamientos muestran donde se esta formando competencia nueva. No todo anuncio importa, pero algunos revelan mercados que estan naciendo.</p>
<h2>Consumo y plataformas</h2>
<p>Aplicaciones, sistemas operativos, redes sociales y buscadores afectan habitos diarios. Por eso una decision de producto puede tener impacto cultural y economico.</p>
""",
    },
]


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
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = response.read().decode("utf-8")
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as exc:
            if exc.code not in {429, 500, 502, 503, 504} or attempt == 4:
                raise
            wait = 8 * (attempt + 1)
            print(f"Google API returned {exc.code}; waiting {wait}s before retry {attempt + 2}/5")
            time.sleep(wait)
    raise RuntimeError("unreachable retry state")


def throttle_write() -> None:
    time.sleep(3)


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
    fields = {
        "client_id": required_env("GOOGLE_CLIENT_ID"),
        "refresh_token": required_env("GOOGLE_REFRESH_TOKEN"),
        "grant_type": "refresh_token",
    }
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "").strip()
    if client_secret:
        fields["client_secret"] = client_secret
    form = urllib.parse.urlencode(fields).encode("utf-8")
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
    svg = " ".join(svg.split())
    return svg.replace("<svg ", '<svg style="display:block;width:100%;height:auto;" ', 1)


def post_html(items: list[build.Item]) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    blocks = [
        f"""
<div style="margin:0 0 28px;padding:28px;border-radius:18px;background:#07111f;color:#ecfeff;border:1px solid #164e63;">
  <p style="margin:0 0 10px;color:#67e8f9;font-weight:800;text-transform:uppercase;letter-spacing:.08em;">Pulso Tech Diario</p>
  <h1 style="margin:0;font-size:36px;line-height:1.05;color:#ffffff;">Tecnologia importante, filtrada con criterio.</h1>
  <p style="margin:14px 0 0;color:#cbd5e1;font-size:17px;line-height:1.6;">Noticias relevantes, contexto rapido y visuales editoriales para leer mejor hacia donde se mueve la industria.</p>
  <p style="margin:14px 0 0;color:#facc15;font-weight:700;">Actualizado: {today} UTC</p>
</div>
"""
    ]
    for index, item in enumerate(items, start=1):
        svg = compact_svg(build.svg_for_item(item, index))
        blocks.append(
            f"""
<section style="border:1px solid #d9e2ec;border-radius:18px;padding:18px;margin:0 0 26px;background:#ffffff;box-shadow:0 10px 30px rgba(15,23,42,.08);">
  <div style="width:100%;max-width:980px;overflow:hidden;border-radius:14px;background:#0f172a;">{svg}</div>
  <p style="margin:18px 0 8px;color:#0f766e;font-weight:900;text-transform:uppercase;font-size:13px;letter-spacing:.06em;">#{index} · {html.escape(item.category)} · {html.escape(item.source)}</p>
  <h2 style="margin:0 0 12px;font-size:30px;line-height:1.13;color:#172033;"><a href="{html.escape(item.link)}" target="_blank" rel="noopener" style="color:#172033;text-decoration:none;">{html.escape(item.title)}</a></h2>
  <p style="margin:0 0 12px;color:#334155;font-size:16px;line-height:1.65;">{html.escape(item.summary or build.reading_angle(item))}</p>
  <p style="margin:0;padding:14px 16px;border-left:5px solid #f59e0b;background:#fff7ed;color:#123f3c;font-weight:700;line-height:1.55;"><strong>Por que importa:</strong> {html.escape(build.reading_angle(item))}</p>
</section>
"""
        )
    adsense_client = os.environ.get("ADSENSE_CLIENT", "").strip()
    if adsense_client:
        blocks.append(
            "<p><small>Monetizacion: este blog esta preparado para AdSense desde la configuracion de Blogger y ads.txt personalizado.</small></p>"
        )
    return "\n".join(blocks)


def post_html(items: list[build.Item]) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    blocks = [
        f"""
<div style="background:#151515;color:#f7f1e8;padding:30px 28px 36px;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:980px;margin:0 auto;">
    <div style="display:flex;align-items:center;justify-content:space-between;gap:18px;margin:0 0 28px;">
      <div style="font-weight:900;font-style:italic;letter-spacing:.04em;text-transform:uppercase;color:#ffffff;">Pulso Tech Diario</div>
      <div style="color:#ff7058;font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.08em;">Actualizado {today} UTC</div>
    </div>
"""
    ]
    for index, item in enumerate(items, start=1):
        svg = compact_svg(build.svg_for_item(item, index))
        title = build.display_title(item)
        summary = build.display_summary(item)
        if index == 1:
            blocks.append(
                f"""
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="width:100%;border-collapse:collapse;margin:0 0 42px;background:#ff7058;color:#201512;">
      <tr>
        <td width="58%" valign="middle" style="width:58%;padding:48px 42px 36px;">
        <p style="margin:0 0 18px;font-size:13px;font-weight:900;text-transform:uppercase;letter-spacing:.08em;color:#5b1d16;">#{index} &middot; {html.escape(item.category)} &middot; {html.escape(item.source)}</p>
        <h2 style="margin:0 0 14px;font-size:40px;line-height:1.02;font-style:italic;font-weight:900;color:#201512;"><a href="{html.escape(item.link)}" target="_blank" rel="noopener" style="color:#201512;text-decoration:none;">{html.escape(title)}</a></h2>
        <p style="margin:0 0 22px;font-size:16px;line-height:1.65;color:#3c201b;">{html.escape(summary)}</p>
        <div style="display:flex;justify-content:space-between;gap:16px;color:#5b1d16;font-size:11px;font-weight:900;text-transform:uppercase;letter-spacing:.08em;">
          <span>Compartir</span>
          <a href="{html.escape(item.link)}" target="_blank" rel="noopener" style="color:#5b1d16;text-decoration:none;">Leer fuente</a>
        </div>
        </td>
        <td width="42%" valign="middle" style="width:42%;background:#0f172a;padding:0;line-height:0;">{svg}</td>
      </tr>
    </table>
    <p style="margin:0 0 24px;color:#f7f1e8;font-size:13px;font-weight:900;">Notas recientes</p>
"""
            )
        else:
            blocks.append(
                f"""
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="width:100%;border-collapse:collapse;margin:0 0 42px;border-bottom:1px solid #2b2b2b;">
      <tr>
        <td valign="middle" style="padding:0 28px 34px 0;">
        <p style="margin:0 0 10px;color:#ff7058;font-size:12px;font-weight:900;text-transform:uppercase;letter-spacing:.08em;">#{index} &middot; {html.escape(item.category)} &middot; {html.escape(item.source)}</p>
        <h2 style="margin:0 0 12px;font-size:32px;line-height:1.05;font-style:italic;font-weight:900;color:#ff7058;"><a href="{html.escape(item.link)}" target="_blank" rel="noopener" style="color:#ff7058;text-decoration:none;">{html.escape(title)}</a></h2>
        <p style="margin:0 0 16px;color:#f1e7dd;font-size:15px;line-height:1.75;">{html.escape(summary)}</p>
        <p style="margin:0;color:#c8b8aa;font-size:13px;line-height:1.6;"><strong style="color:#f7f1e8;">Por que importa:</strong> {html.escape(build.reading_angle(item))}</p>
        </td>
        <td width="240" valign="middle" style="width:240px;padding:0 0 34px 0;line-height:0;background:#0f172a;border:1px solid #2f2f2f;">{svg}</td>
      </tr>
    </table>
"""
            )
    adsense_client = os.environ.get("ADSENSE_CLIENT", "").strip()
    if adsense_client:
        blocks.append(
            '<p style="color:#c8b8aa;"><small>Monetizacion: este blog esta preparado para AdSense desde la configuracion de Blogger y ads.txt personalizado.</small></p>'
        )
    blocks.append("  </div>\n</div>")
    return "\n".join(blocks)


def page_payload(title: str, content: str) -> dict:
    return {
        "kind": "blogger#page",
        "title": title,
        "content": content.strip(),
    }


def post_payload(title: str, content: str, labels: list[str]) -> dict:
    return {
        "kind": "blogger#post",
        "title": title,
        "labels": labels,
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
            print(f"Page already exists: {title}")
        else:
            insert_url = f"{BLOGGER_API}/blogs/{blog_id}/pages"
            request_json(insert_url, method="POST", token=token, payload=payload)
            print(f"Created page: {title}")
            throttle_write()


def find_post_by_title(blog_id: str, token: str, title: str) -> dict | None:
    query = urllib.parse.urlencode({"q": title, "maxResults": "5"})
    url = f"{BLOGGER_API}/blogs/{blog_id}/posts?{query}"
    try:
        payload = request_json(url, token=token)
    except Exception:
        return None
    return next((post for post in payload.get("items", []) if post.get("title") == title), None)


def already_published(blog_id: str, token: str, title: str) -> bool:
    return find_post_by_title(blog_id, token, title) is not None


def ensure_evergreen_posts(blog_id: str, token: str) -> None:
    for post in EVERGREEN_POSTS:
        title = post["title"]
        payload = post_payload(title, post["content"], post["labels"])
        existing = find_post_by_title(blog_id, token, title)
        if existing and existing.get("id"):
            print(f"Evergreen post already exists: {title}")
        else:
            insert_url = f"{BLOGGER_API}/blogs/{blog_id}/posts/"
            request_json(insert_url, method="POST", token=token, payload=payload)
            print(f"Created evergreen post: {title}")
            throttle_write()


def publish() -> None:
    blog_id = required_env("BLOGGER_BLOG_ID")
    token = get_access_token()
    ensure_base_pages(blog_id, token)
    ensure_evergreen_posts(blog_id, token)
    items = build.collect_items() or build.fallback_items()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    title = f"Pulso Tech Diario: {today}"
    existing = find_post_by_title(blog_id, token, title)
    payload = post_payload(title, post_html(items), ["tecnologia", "inteligencia artificial", "noticias tech", "pulso tech diario"])
    if existing and existing.get("id"):
        update_url = f"{BLOGGER_API}/blogs/{blog_id}/posts/{existing['id']}"
        result = request_json(update_url, method="PUT", token=token, payload=payload)
        print(f"Updated daily post: {result.get('url', result.get('id'))}")
        return
    url = f"{BLOGGER_API}/blogs/{blog_id}/posts/"
    result = request_json(url, method="POST", token=token, payload=payload)
    print(f"Published: {result.get('url', result.get('id'))}")


if __name__ == "__main__":
    try:
        publish()
    except urllib.error.HTTPError as exc:
        sys.stderr.write(exc.read().decode("utf-8", errors="replace"))
        raise
