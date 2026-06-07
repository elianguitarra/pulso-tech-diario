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
    return " ".join(svg.split())


def post_html(items: list[build.Item]) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    blocks = [
        f"""
<p><strong>Pulso Tech Diario</strong> selecciona automaticamente las noticias tecnologicas mas relevantes del dia y las presenta con visuales editoriales de alto contraste.</p>
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
    if already_published(blog_id, token, title):
        print(f"Post already exists: {title}")
        return
    payload = post_payload(title, post_html(items), ["tecnologia", "inteligencia artificial", "noticias tech", "pulso tech diario"])
    url = f"{BLOGGER_API}/blogs/{blog_id}/posts/"
    result = request_json(url, method="POST", token=token, payload=payload)
    print(f"Published: {result.get('url', result.get('id'))}")


if __name__ == "__main__":
    try:
        publish()
    except urllib.error.HTTPError as exc:
        sys.stderr.write(exc.read().decode("utf-8", errors="replace"))
        raise
