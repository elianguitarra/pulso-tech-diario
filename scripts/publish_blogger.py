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
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import build


TOKEN_URL = "https://oauth2.googleapis.com/token"
BLOGGER_API = "https://www.googleapis.com/blogger/v3"
BLOGGER_SCOPE = "https://www.googleapis.com/auth/blogger"
BLOG_URL = "https://pulsotechdiario.blogspot.com"
RSS_URL = f"{BLOG_URL}/feeds/posts/default?alt=rss"
PAGES_URL = "https://elianguitarra.github.io/pulso-tech-diario"
PAGES_WORK_AI_URL = f"{PAGES_URL}/ia-en-el-trabajo.html"
PAGES_LAPTOP_AI_URL = f"{PAGES_URL}/comprar-laptop-para-ia.html"
PAGES_EXTRA_GUIDES = [
    ("Que es Pulso Tech Diario", f"{PAGES_URL}/pulso-tech-diario.html"),
    ("IA para resumir PDF", f"{PAGES_URL}/mejor-ia-para-resumir-pdf.html"),
    ("Alternativas a ChatGPT", f"{PAGES_URL}/alternativas-chatgpt-gratis.html"),
    ("Prompts ChatGPT", f"{PAGES_URL}/prompts-chatgpt-espanol.html"),
    ("Prompts de IA", f"{PAGES_URL}/prompts-ia-productividad.html"),
    ("IA para presentaciones", f"{PAGES_URL}/ia-para-hacer-presentaciones.html"),
    ("Extensiones Chrome IA", f"{PAGES_URL}/extensiones-chrome-productividad-ia.html"),
    ("Imagenes con IA", f"{PAGES_URL}/crear-imagenes-ia-gratis.html"),
    ("Prompts para estudiar", f"{PAGES_URL}/prompts-para-estudiar-con-ia.html"),
    ("Correo hackeado", f"{PAGES_URL}/que-hacer-si-hackearon-mi-correo.html"),
    ("Enlace seguro", f"{PAGES_URL}/como-saber-si-un-enlace-es-seguro.html"),
    ("Correo falso", f"{PAGES_URL}/como-detectar-correo-falso.html"),
    ("WhatsApp hackeado", f"{PAGES_URL}/recuperar-whatsapp-hackeado.html"),
    ("Passkeys", f"{PAGES_URL}/que-son-passkeys.html"),
    ("Borrar datos Google", f"{PAGES_URL}/como-borrar-datos-personales-google.html"),
    ("Contrasena filtrada", f"{PAGES_URL}/contrasena-filtrada-que-hacer.html"),
    ("Estafa WhatsApp", f"{PAGES_URL}/estafa-whatsapp-que-hacer.html"),
    ("Antivirus gratis", f"{PAGES_URL}/mejor-antivirus-gratis-windows.html"),
    ("VPN gratis segura", f"{PAGES_URL}/vpn-gratis-es-segura.html"),
    ("Laptop con NPU", f"{PAGES_URL}/laptop-con-npu-vale-la-pena.html"),
    ("Automatizar Blogger", f"{PAGES_URL}/automatizar-blogger-gratis.html"),
]


def label_url(label: str) -> str:
    return f"{BLOG_URL}/search/label/{urllib.parse.quote(label)}"


def guide_posts_from(existing_posts: dict[str, dict]) -> list[tuple[str, str]]:
    guides = []
    for post in EVERGREEN_POSTS:
        existing = existing_posts.get(post["title"], {})
        url = existing.get("url", "")
        if url:
            guides.append((post["title"], url))
    return guides[:24]


def guide_links_html(guide_posts: list[tuple[str, str]]) -> str:
    guide_links = [*guide_posts, *PAGES_EXTRA_GUIDES]
    if not guide_links:
        return ""
    links = "".join(
        f'<li style="margin:0 0 8px;"><a href="{html.escape(url)}" target="_blank" rel="noopener" style="color:#ff7058;font-weight:800;text-decoration:none;">{html.escape(title)}</a></li>'
        for title, url in guide_links[:32]
    )
    return f"""
  <div style="margin:18px 0 0;padding:16px;background:#181818;border:1px solid #2f2f2f;">
    <p style="margin:0 0 10px;color:#f7f1e8;font-weight:900;">Guias para seguir leyendo</p>
    <ul style="margin:0;padding-left:18px;color:#c8b8aa;line-height:1.55;">{links}</ul>
  </div>
"""


def internal_link_block(guide_posts: list[tuple[str, str]] | None = None) -> str:
    links = [
        ("Inteligencia artificial", label_url("inteligencia artificial")),
        ("Ciberseguridad", label_url("ciberseguridad")),
        ("Chips", label_url("chips")),
        ("Guias", label_url("guia")),
        ("RSS", RSS_URL),
    ]
    items = "".join(
        f'<a href="{html.escape(url)}" target="_blank" rel="noopener" style="display:inline-block;margin:0 8px 10px 0;padding:9px 12px;border:1px solid #ff7058;color:#ff7058;text-decoration:none;font-weight:800;font-size:12px;text-transform:uppercase;letter-spacing:.05em;">{html.escape(label)}</a>'
        for label, url in links
    )
    share_text = "Pulso Tech Diario: tecnologia importante explicada en espanol"
    share_links = [
        ("Compartir en X", f"https://twitter.com/intent/tweet?text={urllib.parse.quote(share_text)}&url={urllib.parse.quote(BLOG_URL + '/')}"),
        ("WhatsApp", f"https://wa.me/?text={urllib.parse.quote(share_text + ' ' + BLOG_URL + '/')}"),
        ("LinkedIn", f"https://www.linkedin.com/sharing/share-offsite/?url={urllib.parse.quote(BLOG_URL + '/')}"),
    ]
    share_items = "".join(
        f'<a href="{html.escape(url)}" target="_blank" rel="noopener" style="display:inline-block;margin:0 8px 10px 0;padding:9px 12px;background:#ff7058;color:#201512;text-decoration:none;font-weight:900;font-size:12px;text-transform:uppercase;letter-spacing:.05em;">{html.escape(label)}</a>'
        for label, url in share_links
    )
    return f"""
<div style="margin:34px 0 0;padding:22px;border-top:3px solid #ff7058;background:#101010;color:#f7f1e8;">
  <p style="margin:0 0 12px;color:#f7f1e8;font-size:18px;font-weight:900;">Sigue leyendo Pulso Tech Diario</p>
  <p style="margin:0 0 16px;color:#c8b8aa;line-height:1.65;">Explora mas notas por tema, guarda el RSS o comparte el resumen para que mas lectores encuentren tecnologia explicada en espanol.</p>
  <div>{items}</div>
  {guide_links_html(guide_posts or [])}
  <div style="margin-top:8px;">{share_items}</div>
  <p style="margin:8px 0 0;color:#c8b8aa;font-size:13px;line-height:1.6;">Pagina principal: <a href="{BLOG_URL}/" target="_blank" rel="noopener" style="color:#ff7058;font-weight:800;">{BLOG_URL}</a></p>
</div>
"""


def public_image_url(item: build.Item, index: int) -> str:
    filename = build.image_filename(item, index).replace(".svg", ".png")
    return f"{PAGES_URL}/assets/images/{filename}"


def story_image(item: build.Item, index: int, title: str) -> str:
    url = public_image_url(item, index)
    return (
        f'<img src="{html.escape(url)}" alt="{html.escape(title)}" width="1200" height="630" '
        'style="display:block;width:100%;height:auto;border:0;margin:0;padding:0;" loading="lazy">'
    )


def start_here_content(guide_posts: list[tuple[str, str]] | None = None) -> str:
    if guide_posts:
        guide_items = "".join(
            f'<li><a href="{html.escape(url)}">{html.escape(title)}</a></li>' for title, url in guide_posts
        )
    else:
        guide_items = f"""
  <li><a href="{label_url("inteligencia artificial")}">Inteligencia artificial</a></li>
  <li><a href="{label_url("ciberseguridad")}">Ciberseguridad</a></li>
  <li><a href="{label_url("chips")}">Chips y hardware</a></li>
  <li><a href="{label_url("guia")}">Guias practicas</a></li>
"""
    return f"""
<p><strong>Pulso Tech Diario</strong> publica un resumen diario de tecnologia en espanol, pensado para leer rapido y seguir las senales importantes sin ruido.</p>
<h2>Lee primero estas guias</h2>
<ul>
{guide_items}
</ul>
<h2>Explora por tema</h2>
<ul>
  <li><a href="{label_url("inteligencia artificial")}">Inteligencia artificial</a></li>
  <li><a href="{label_url("ciberseguridad")}">Ciberseguridad</a></li>
  <li><a href="{label_url("chips")}">Chips y hardware</a></li>
  <li><a href="{label_url("guia")}">Todas las guias</a></li>
</ul>
<h2>Guias extra</h2>
<ul>
  <li><a href="{PAGES_WORK_AI_URL}">IA en el trabajo: tareas donde si ahorra tiempo</a></li>
  <li><a href="{PAGES_LAPTOP_AI_URL}">Que revisar antes de comprar una laptop para IA</a></li>
</ul>
<h2>Guias rapidas para resolver problemas comunes</h2>
<h3>WhatsApp hackeado</h3>
<p>Si alguien tomo tu cuenta, intenta registrar de nuevo tu numero, no compartas codigos, avisa a tus contactos por otro canal y revisa dispositivos vinculados al recuperar acceso.</p>
<h3>Passkeys</h3>
<p>Las passkeys reducen el riesgo de phishing porque evitan escribir una contrasena en paginas falsas. Conviene activarlas primero en correo, cuentas principales y gestores de contrasenas.</p>
<h3>VPN gratis</h3>
<p>Una VPN gratuita no siempre mejora tu privacidad. Revisa quien opera el servicio, politica de registros, permisos, publicidad y limites antes de instalarla.</p>
<h3>Imagenes con IA gratis</h3>
<p>Para crear imagenes utiles con IA, define sujeto, estilo, encuadre, iluminacion y uso final. Revisa derechos, privacidad y detalles visuales antes de publicar.</p>
<h3>Prompts para estudiar con IA</h3>
<p>Usa la IA como tutor: pide explicaciones, preguntas, pistas y correcciones. Evita pedir respuestas finales para copiar en tareas o examenes.</p>
<h3>Correo falso</h3>
<p>Revisa remitente real, dominio, enlaces, adjuntos y urgencias exageradas antes de hacer clic. Si dudas, entra manualmente al sitio oficial.</p>
<h2>Mas rutas utiles</h2>
<ul>
{''.join(f'<li><a href="{html.escape(url)}">{html.escape(title)}</a></li>' for title, url in PAGES_EXTRA_GUIDES)}
</ul>
<h2>Mapa rapido</h2>
<ul>
  <li><a href="{BLOG_URL}/">Pagina principal</a></li>
  <li><a href="{label_url("inteligencia artificial")}">Inteligencia artificial</a></li>
  <li><a href="{label_url("ciberseguridad")}">Ciberseguridad</a></li>
  <li><a href="{label_url("chips")}">Chips y hardware</a></li>
  <li><a href="{label_url("guia")}">Guias practicas</a></li>
</ul>
<h2>Recibe nuevas publicaciones</h2>
<p>Guarda el <a href="{RSS_URL}">RSS del blog</a> o visita la pagina principal cada dia: <a href="{BLOG_URL}/">{BLOG_URL}</a>.</p>
"""


BASE_PAGES = {
    "Empieza aqui": start_here_content(),
    "Acerca de": """
<p><strong>Pulso Tech Diario</strong> es un blog automatizado que resume noticias tecnologicas relevantes cada dia.</p>
<p>El objetivo es ayudar a lectores ocupados a detectar senales importantes sobre inteligencia artificial, chips, ciberseguridad, startups, consumo digital, ciencia aplicada y plataformas web.</p>
<p>El sistema revisa fuentes publicas por RSS, ordena las notas por frescura, relevancia tematica y fuente, y enlaza siempre al articulo original.</p>
""",
    "Politica editorial": """
<p>Pulso Tech Diario no copia articulos completos. Cada entrada usa fragmentos breves, resumen editorial propio y enlaces directos a las fuentes originales.</p>
<p>Las notas se seleccionan automaticamente con reglas de relevancia, pero el blog prioriza contenido informativo, trazable y util para lectores interesados en tecnologia.</p>
<p>Las imagenes que acompanan cada noticia son visuales editoriales propios del blog. No representan capturas ni fotografias de los articulos enlazados.</p>
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
    {
        "title": "Que es la IA local y por que puede cambiar tu computadora",
        "labels": ["inteligencia artificial", "ia local", "pc", "guia"],
        "content": """
<p>La IA local significa ejecutar modelos o agentes directamente en tu computadora, telefono o dispositivo, en lugar de mandar todo a servidores remotos. Es una tendencia importante porque mezcla productividad, privacidad, hardware y software.</p>
<h2>Por que importa</h2>
<p>Cuando una tarea ocurre localmente, puede responder mas rapido, trabajar con archivos privados y depender menos de la conexion a internet. Esto puede cambiar editores de texto, hojas de calculo, asistentes de codigo, buscadores personales y herramientas creativas.</p>
<h2>Que necesitas mirar</h2>
<p>No basta con que una marca diga "AI PC". Conviene revisar memoria disponible, NPU o GPU, compatibilidad de aplicaciones, bateria, temperatura y si las funciones realmente ahorran tiempo.</p>
<h2>Riesgos</h2>
<p>La IA local tambien puede crear falsas expectativas. Algunos agentes prometen autonomia, pero aun fallan en tareas largas. La clave es preguntar: que hace mejor que una app normal y que datos necesita para hacerlo.</p>
<h2>Resumen rapido</h2>
<p>La IA local no reemplaza a la nube, pero puede volver a darle protagonismo a la computadora personal. Si madura, el PC podria pasar de ser una herramienta pasiva a un espacio de trabajo con asistencia permanente.</p>
""",
    },
    {
        "title": "Como proteger tus cuentas despues de una filtracion de datos",
        "labels": ["ciberseguridad", "privacidad", "guia", "cuentas"],
        "content": """
<p>Las filtraciones de datos son frecuentes y no siempre puedes evitarlas. Lo que si puedes hacer es reducir el dano cuando una contrasena, correo o dato personal aparece en una base filtrada.</p>
<h2>1. Cambia contrasenas repetidas</h2>
<p>Si usaste la misma contrasena en varios servicios, cambia primero correo, banco, redes sociales y cuentas donde haya informacion personal o pagos.</p>
<h2>2. Activa verificacion en dos pasos</h2>
<p>Usa una app autenticadora o llave fisica cuando sea posible. Los codigos por SMS son mejores que nada, pero no son la opcion mas fuerte.</p>
<h2>3. Usa un gestor de contrasenas</h2>
<p>Un gestor permite crear claves unicas y largas sin memorizarlas. La defensa mas simple contra ataques por reutilizacion es que cada sitio tenga una clave distinta.</p>
<h2>4. Revisa sesiones activas</h2>
<p>Cierra sesiones desconocidas y elimina dispositivos que no reconozcas. Muchos servicios permiten ver actividad reciente desde seguridad o privacidad.</p>
<h2>5. Desconfia de correos urgentes</h2>
<p>Despues de una filtracion suelen crecer los ataques de phishing. No abras enlaces de supuestos avisos de seguridad; entra manualmente al sitio oficial.</p>
""",
    },
    {
        "title": "Chips de IA: que significan GPU, NPU y memoria unificada",
        "labels": ["chips", "gpu", "npu", "ia", "guia"],
        "content": """
<p>Los chips de IA aparecen en noticias sobre Nvidia, AMD, Intel, Apple, Qualcomm y centros de datos. Entender algunos terminos ayuda a leer mejor que esta cambiando.</p>
<h2>GPU</h2>
<p>La GPU procesa muchas operaciones en paralelo. Por eso se volvio fundamental para entrenar y ejecutar modelos de inteligencia artificial.</p>
<h2>NPU</h2>
<p>La NPU es una unidad especializada para tareas de IA en dispositivos personales. Suele buscar eficiencia: consumir menos energia para funciones como transcripcion, vision o asistentes.</p>
<h2>Memoria unificada</h2>
<p>Permite que distintas partes del sistema compartan memoria con menos friccion. Para IA puede ser importante porque los modelos necesitan mover grandes cantidades de datos.</p>
<h2>Que mirar en una noticia</h2>
<p>No te quedes solo con el numero mas grande. Revisa consumo energetico, memoria, software compatible, precio y disponibilidad. Un chip potente sin ecosistema puede tardar en importar.</p>
""",
    },
    {
        "title": "Como elegir herramientas de IA sin caer en humo",
        "labels": ["inteligencia artificial", "productividad", "herramientas", "guia"],
        "content": """
<p>Cada semana aparece una herramienta de IA que promete ahorrar horas. Algunas son utiles; otras solo agregan una caja de chat encima de un producto viejo. Esta guia ayuda a separar valor real de marketing.</p>
<h2>Empieza por la tarea</h2>
<p>No preguntes primero que modelo usa. Pregunta que tarea repetitiva o costosa resuelve: resumir reuniones, analizar documentos, generar borradores, revisar codigo o responder soporte.</p>
<h2>Mide antes y despues</h2>
<p>Una buena herramienta debe reducir tiempo, errores o friccion. Si despues de una semana sigues copiando y pegando igual que antes, probablemente no cambio el flujo real.</p>
<h2>Cuida tus datos</h2>
<p>Revisa si la herramienta usa tus datos para entrenamiento, donde procesa la informacion y si permite borrar historiales. Esto importa especialmente en trabajo, clientes y documentos internos.</p>
<h2>Prefiere integraciones reales</h2>
<p>Las mejores herramientas viven cerca del flujo: correo, documentos, hojas, codigo, CRM o navegador. Si todo depende de abrir otra pestana, el beneficio baja rapido.</p>
""",
    },
    {
        "title": "Privacidad con IA: que datos no debes subir a un chatbot",
        "labels": ["inteligencia artificial", "privacidad", "seguridad", "guia"],
        "content": """
<p>Los chatbots de IA son utiles para resumir, redactar y analizar informacion, pero no todo dato debe entrar en una conversacion con una herramienta externa. Esta guia explica como usar IA sin regalar informacion sensible.</p>
<h2>Datos personales directos</h2>
<p>Evita subir identificaciones, direcciones, telefonos, datos fiscales, documentos medicos, cuentas bancarias o cualquier informacion que pueda identificar a una persona.</p>
<h2>Informacion de trabajo</h2>
<p>No pegues contratos, estrategias internas, listas de clientes, codigo privado, credenciales, tickets con datos sensibles o documentos que pertenezcan a una empresa sin permiso claro.</p>
<h2>Como reducir riesgo</h2>
<p>Quita nombres, correos, montos, claves y referencias internas antes de pedir ayuda. Si necesitas analizar un documento, crea una version anonimizada con la estructura pero sin datos reales.</p>
<h2>Que revisar en una herramienta</h2>
<p>Busca controles de privacidad, opcion para no entrenar con tus datos, historial borrable, permisos por equipo y politicas claras. Si la herramienta no explica que hace con la informacion, conviene usarla solo con datos publicos.</p>
<h2>Regla practica</h2>
<p>Si no publicarias ese texto en internet ni lo mandarias a un desconocido, no lo pegues completo en un chatbot. La IA puede ayudar mucho, pero la privacidad empieza antes de escribir el prompt.</p>
""",
    },
    {
        "title": "Como detectar phishing: senales simples antes de hacer clic",
        "labels": ["ciberseguridad", "phishing", "privacidad", "guia"],
        "content": """
<p>El phishing intenta que entregues contrasenas, codigos o datos personales fingiendo ser una empresa, banco, paqueteria o servicio conocido. La buena noticia es que muchas senales se pueden detectar antes de hacer clic.</p>
<h2>Urgencia exagerada</h2>
<p>Mensajes como "tu cuenta sera cerrada hoy" o "pago rechazado, actua ahora" buscan que respondas sin pensar. La urgencia es una de las herramientas favoritas del atacante.</p>
<h2>Enlaces raros</h2>
<p>Antes de abrir un enlace, revisa el dominio. Letras cambiadas, guiones extra, subdominios largos o direcciones que no coinciden con la marca son senales de alerta.</p>
<h2>Archivos inesperados</h2>
<p>No abras adjuntos que no esperabas, especialmente si piden habilitar macros, iniciar sesion o instalar algo. Si parece venir de alguien conocido, confirma por otro canal.</p>
<h2>Codigos de verificacion</h2>
<p>Ningun soporte legitimo necesita que le dictes un codigo de verificacion de dos pasos. Si alguien lo pide, probablemente intenta entrar a tu cuenta.</p>
<h2>Mejor respuesta</h2>
<p>No respondas desde el mensaje sospechoso. Entra manualmente al sitio oficial desde el navegador o la app, revisa notificaciones y cambia contrasenas solo desde canales conocidos.</p>
""",
    },
    {
        "title": "IA en el trabajo: tareas donde si ahorra tiempo y donde no",
        "labels": ["inteligencia artificial", "trabajo", "productividad", "guia"],
        "content": """
<p>La IA puede ahorrar tiempo, pero no en cualquier tarea. Funciona mejor cuando hay informacion clara, criterios de revision y un resultado que una persona puede comprobar.</p>
<h2>Donde suele ayudar</h2>
<p>Resumir reuniones, ordenar notas, crear primeros borradores, explicar codigo, comparar opciones, transformar formatos y preparar listas de preguntas son usos donde la IA puede reducir friccion.</p>
<h2>Donde hay que tener cuidado</h2>
<p>Decisiones legales, medicas, financieras, datos sensibles, calculos criticos o comunicados delicados requieren revision experta. La IA puede sugerir, pero no debe reemplazar responsabilidad.</p>
<h2>Como medir si sirve</h2>
<p>El beneficio no es que la herramienta "suene inteligente". Mide si reduce minutos, errores o pasos repetidos. Si tienes que corregir demasiado, tal vez el flujo no esta listo.</p>
<h2>Prompts utiles</h2>
<p>Da contexto, objetivo, formato esperado y criterios de calidad. En vez de pedir "hazlo mejor", pide "resume en 5 puntos para un gerente que necesita decidir hoy".</p>
<h2>La regla de oro</h2>
<p>Usa IA como copiloto para avanzar mas rapido, no como piloto automatico para tareas que no puedes revisar. El ahorro real aparece cuando el humano conserva criterio.</p>
""",
    },
    {
        "title": "Que revisar antes de comprar una laptop para IA",
        "labels": ["chips", "ia local", "laptop", "hardware", "guia"],
        "content": """
<p>Las computadoras nuevas prometen funciones de IA, pero no todas sirven para lo mismo. Antes de comprar una laptop conviene mirar mas que el anuncio de "AI PC".</p>
<h2>Memoria RAM</h2>
<p>La memoria importa mucho para trabajar con modelos, navegadores pesados, edicion y multitarea. Para uso moderno, 16 GB suele ser el punto de partida razonable; para trabajo pesado, mas memoria ayuda.</p>
<h2>GPU, NPU y CPU</h2>
<p>La GPU puede acelerar tareas de IA y graficos. La NPU busca eficiencia para funciones integradas. La CPU sigue importando para rendimiento general. No compres solo por una sigla.</p>
<h2>Software compatible</h2>
<p>Un chip potente no sirve de mucho si tus aplicaciones no lo aprovechan. Revisa si las herramientas que usas soportan funciones locales o aceleracion real.</p>
<h2>Bateria y temperatura</h2>
<p>La IA local puede consumir recursos. Mira reseñas de autonomia, ruido y temperatura, no solo numeros de rendimiento.</p>
<h2>Compra con una tarea en mente</h2>
<p>Si solo quieres escribir, navegar y usar chatbots en la nube, no necesitas pagar de mas. Si vas a editar video, programar, generar imagenes o probar modelos locales, hardware y memoria pesan mucho mas.</p>
""",
    },
    {
        "title": "WhatsApp hackeado: como recuperar tu cuenta",
        "labels": ["ciberseguridad", "whatsapp", "phishing", "guia"],
        "content": """
<p>Si alguien tomo tu WhatsApp o tus contactos reciben mensajes raros desde tu numero, actua rapido. El objetivo es recuperar acceso, cortar el fraude y evitar que usen tu identidad para pedir dinero o codigos.</p>
<h2>Intenta verificar tu numero</h2>
<p>Abre WhatsApp, registra tu numero y pide el codigo oficial. Nunca compartas ese codigo con nadie. Si el atacante activo verificacion en dos pasos, puede que debas esperar el plazo que indique la app.</p>
<h2>Avisa por otro canal</h2>
<p>Contacta a familiares, amigos y trabajo por llamada, SMS u otra red para decir que no respondan mensajes sospechosos ni envien dinero.</p>
<h2>Revisa dispositivos vinculados</h2>
<p>Cuando recuperes acceso, revisa dispositivos vinculados y cierra cualquiera que no reconozcas. Activa verificacion en dos pasos con un PIN que no uses en otros servicios.</p>
<h2>Protege correo y SIM</h2>
<p>Cambia contrasenas importantes, activa verificacion en dos pasos y llama a tu operador si sospechas duplicado de SIM.</p>
""",
    },
    {
        "title": "Que son las passkeys y por que protegen mejor",
        "labels": ["ciberseguridad", "passkeys", "privacidad", "guia"],
        "content": """
<p>Las passkeys, o claves de acceso, permiten iniciar sesion sin escribir una contrasena tradicional. Usan tu dispositivo y una verificacion local como huella, rostro, PIN o llave de seguridad.</p>
<h2>Por que son utiles</h2>
<p>Una passkey reduce phishing porque no tienes una contrasena que copiar en una pagina falsa. El inicio de sesion queda ligado al sitio correcto y a una clave criptografica.</p>
<h2>Que cambia frente a contrasenas</h2>
<p>No necesitas recordar una clave larga ni reutilizarla. El riesgo se mueve hacia proteger tus dispositivos, copias de seguridad y metodo de recuperacion.</p>
<h2>Donde activarlas primero</h2>
<p>Empieza por correo, cuentas de Google, Apple, Microsoft, gestores de contrasenas, bancos o servicios donde perder acceso seria grave.</p>
<h2>Que revisar</h2>
<p>Antes de activar passkeys, confirma como recuperar la cuenta si pierdes el telefono o computadora. Mantener datos de recuperacion actualizados sigue siendo clave.</p>
""",
    },
    {
        "title": "VPN gratis: es segura o conviene evitarla",
        "labels": ["privacidad", "ciberseguridad", "vpn", "guia"],
        "content": """
<p>Una VPN gratis puede servir para casos puntuales, pero no siempre mejora tu privacidad. Si el servicio no cobra, conviene preguntar como paga servidores, ancho de banda y soporte.</p>
<h2>Que hace una VPN</h2>
<p>Una VPN cifra la conexion entre tu dispositivo y el proveedor de VPN. Puede ocultar tu IP frente al sitio final, pero el proveedor puede ver metadatos y parte de tu actividad segun el caso.</p>
<h2>Riesgos de una VPN gratis</h2>
<p>Algunas tienen limites agresivos, publicidad, registros poco claros, velocidades bajas o modelos de negocio basados en datos. Evita servicios que no expliquen quien los opera.</p>
<h2>Cuando puede servir</h2>
<p>Puede ser util en una red publica si confias en el proveedor y solo necesitas una capa adicional. No reemplaza contrasenas seguras ni verificacion en dos pasos.</p>
<h2>Que revisar antes de instalar</h2>
<p>Politica de registros, empresa responsable, auditorias, apps oficiales, reputacion, permisos, limites y facilidad para borrar cuenta.</p>
""",
    },
    {
        "title": "Crear imagenes con IA gratis: como empezar",
        "labels": ["inteligencia artificial", "imagenes", "herramientas", "guia"],
        "content": """
<p>Crear imagenes con IA gratis es facil para probar ideas, pero la calidad depende del prompt, la herramienta y el uso que le daras a la imagen. No todo resultado sirve para publicar sin revisar.</p>
<h2>Empieza con una idea concreta</h2>
<p>Describe sujeto, estilo, encuadre, iluminacion, colores, formato y uso final. No pidas solo una imagen bonita; pide una imagen que comunique algo.</p>
<h2>Prompt base</h2>
<p>Crea una imagen editorial para una nota de tecnologia sobre este tema. Debe verse moderna, clara, sin texto dentro de la imagen, con foco en una idea principal y composicion llamativa para portada.</p>
<h2>Que revisar antes de usarla</h2>
<p>Mira manos, textos deformes, logos, marcas, rostros, objetos raros y detalles incoherentes. Si la imagen parece generica, ajusta el prompt con mas contexto.</p>
<h2>Privacidad y derechos</h2>
<p>No subas fotos privadas, documentos, rostros de personas sin permiso ni material que no puedas usar. Revisa las condiciones de cada herramienta antes de publicar comercialmente.</p>
""",
    },
    {
        "title": "Prompts para estudiar con IA sin copiar",
        "labels": ["inteligencia artificial", "estudiantes", "prompts", "guia"],
        "content": """
<p>La IA puede ayudarte a estudiar mejor si la usas como tutor, no como maquina para copiar respuestas. La clave es pedir explicaciones, preguntas y correcciones.</p>
<h2>Prompt para entender un tema</h2>
<p>Explicame este tema desde cero como si fuera principiante. Usa ejemplos simples, analogias y al final dame tres errores comunes que debo evitar.</p>
<h2>Prompt para practicar</h2>
<p>Hazme 10 preguntas sobre este tema, una por una. Espera mi respuesta, corrige con explicacion breve y sube la dificultad si respondo bien.</p>
<h2>Prompt para resumir apuntes</h2>
<p>Resume mis apuntes en ideas principales, definiciones, formulas o conceptos clave. Marca dudas y crea una lista de repaso para antes del examen.</p>
<h2>Prompt para no copiar</h2>
<p>No me des la respuesta final. Guiame con pistas, preguntas y pasos para que yo pueda resolver el ejercicio.</p>
""",
    },
    {
        "title": "Como detectar un correo falso antes de hacer clic",
        "labels": ["ciberseguridad", "phishing", "correo", "guia"],
        "content": """
<p>Un correo falso intenta que actues rapido: abrir un enlace, descargar un archivo, pagar, confirmar datos o compartir un codigo. Revisar unos detalles antes de hacer clic puede evitar muchos problemas.</p>
<h2>Mira el remitente real</h2>
<p>No te quedes con el nombre visible. Abre los detalles y revisa el dominio del correo. Un mensaje puede decir que viene de tu banco aunque el remitente use un dominio extrano.</p>
<h2>Desconfia de urgencias</h2>
<p>Frases como tu cuenta sera cerrada, pago rechazado, paquete retenido o premio disponible buscan presionarte. Entra manualmente al sitio oficial en vez de tocar el enlace del mensaje.</p>
<h2>Revisa enlaces y adjuntos</h2>
<p>Pasa el cursor sobre el enlace para ver el destino. No abras archivos inesperados, especialmente si piden habilitar macros, iniciar sesion o instalar algo.</p>
<h2>Que hacer si dudaste</h2>
<p>No respondas al correo. Contacta a la empresa desde su sitio oficial, busca avisos en la app real y reporta el mensaje como phishing si corresponde.</p>
""",
    },
]


PAGE_ONLY_GUIDES = {
    "IA en el trabajo: tareas donde si ahorra tiempo y donde no",
    "Que revisar antes de comprar una laptop para IA",
    "WhatsApp hackeado: como recuperar tu cuenta",
    "Que son las passkeys y por que protegen mejor",
    "VPN gratis: es segura o conviene evitarla",
    "Crear imagenes con IA gratis: como empezar",
    "Prompts para estudiar con IA sin copiar",
    "Como detectar un correo falso antes de hacer clic",
}

BLOGGER_GUIDE_PAGE_TITLES = {
    "WhatsApp hackeado: como recuperar tu cuenta",
    "Que son las passkeys y por que protegen mejor",
    "VPN gratis: es segura o conviene evitarla",
    "Crear imagenes con IA gratis: como empezar",
    "Prompts para estudiar con IA sin copiar",
    "Como detectar un correo falso antes de hacer clic",
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


def _legacy_card_post_html(items: list[build.Item]) -> str:
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
        title = build.display_title(item)
        summary = build.display_summary(item)
        blocks.append(
            f"""
<section style="border:1px solid #d9e2ec;border-radius:18px;padding:18px;margin:0 0 26px;background:#ffffff;box-shadow:0 10px 30px rgba(15,23,42,.08);">
  <div style="width:100%;max-width:980px;overflow:hidden;border-radius:14px;background:#0f172a;">{svg}</div>
  <p style="margin:18px 0 8px;color:#0f766e;font-weight:900;text-transform:uppercase;font-size:13px;letter-spacing:.06em;">#{index} · {html.escape(item.category)} · {html.escape(item.source)}</p>
  <h2 style="margin:0 0 12px;font-size:30px;line-height:1.13;color:#172033;"><a href="{html.escape(item.link)}" target="_blank" rel="noopener" style="color:#172033;text-decoration:none;">{html.escape(title)}</a></h2>
  <p style="margin:0 0 12px;color:#334155;font-size:16px;line-height:1.65;">{html.escape(summary)}</p>
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


def post_html(items: list[build.Item], guide_posts: list[tuple[str, str]] | None = None) -> str:
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
        title = build.display_title(item)
        summary = build.display_summary(item)
        image = story_image(item, index, title)
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
        <td width="42%" valign="middle" style="width:42%;background:#0f172a;padding:0;line-height:0;">{image}</td>
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
        <td width="240" valign="middle" style="width:240px;padding:0 0 34px 0;line-height:0;background:#0f172a;border:1px solid #2f2f2f;">{image}</td>
      </tr>
    </table>
"""
            )
    adsense_client = os.environ.get("ADSENSE_CLIENT", "").strip()
    if adsense_client:
        blocks.append(
            '<p style="color:#c8b8aa;"><small>Monetizacion: este blog esta preparado para AdSense desde la configuracion de Blogger y ads.txt personalizado.</small></p>'
        )
    blocks.append(internal_link_block(guide_posts))
    blocks.append("  </div>\n</div>")
    return "\n".join(blocks)


def page_payload(title: str, content: str) -> dict:
    return {
        "kind": "blogger#page",
        "title": title,
        "content": content.strip(),
    }


def post_payload(title: str, content: str, labels: list[str], published: str | None = None) -> dict:
    payload = {
        "kind": "blogger#post",
        "title": title,
        "labels": labels,
        "content": content.strip(),
    }
    if published:
        payload["published"] = published
    return payload


def ensure_base_pages(blog_id: str, token: str, pages: dict[str, str] | None = None) -> None:
    pages = pages or BASE_PAGES
    query = urllib.parse.urlencode({"fetchBodies": "false", "maxResults": "50"})
    url = f"{BLOGGER_API}/blogs/{blog_id}/pages?{query}"
    existing_pages = {page.get("title"): page for page in paginated_items(url, token=token)}
    for title, content in pages.items():
        payload = page_payload(title, content)
        existing = existing_pages.get(title)
        try:
            if existing and existing.get("id"):
                update_url = f"{BLOGGER_API}/blogs/{blog_id}/pages/{existing['id']}"
                result = request_json(update_url, method="PUT", token=token, payload=payload)
                print(f"Updated page: {title} {result.get('url', '')}".rstrip())
            else:
                insert_url = f"{BLOGGER_API}/blogs/{blog_id}/pages"
                result = request_json(insert_url, method="POST", token=token, payload=payload)
                print(f"Created page: {title} {result.get('url', '')}".rstrip())
            throttle_write()
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            print(f"Warning: skipped page after HTTP {exc.code}: {title}")
            print(body[:600])
            if exc.code not in {403, 429, 500, 502, 503, 504}:
                raise


def blogger_guide_pages(guide_posts: list[tuple[str, str]] | None = None) -> dict[str, str]:
    pages: dict[str, str] = {}
    link_block = internal_link_block(guide_posts or [])
    for post in EVERGREEN_POSTS:
        if post["title"] in BLOGGER_GUIDE_PAGE_TITLES:
            pages[post["title"]] = f"{post['content'].strip()}\n{link_block}"
    return pages


def list_posts(blog_id: str, token: str) -> list[dict]:
    query = urllib.parse.urlencode({"fetchBodies": "false", "maxResults": "500"})
    url = f"{BLOGGER_API}/blogs/{blog_id}/posts?{query}"
    return paginated_items(url, token=token)


def posts_by_title(posts: list[dict]) -> dict[str, dict]:
    grouped: dict[str, list[dict]] = {}
    for post in posts:
        title = post.get("title", "")
        if title:
            grouped.setdefault(title, []).append(post)
    return {title: sorted(matches, key=lambda post: post.get("updated", ""), reverse=True)[0] for title, matches in grouped.items()}


def find_post_by_title(blog_id: str, token: str, title: str) -> dict | None:
    return posts_by_title(list_posts(blog_id, token)).get(title)


def already_published(blog_id: str, token: str, title: str) -> bool:
    return find_post_by_title(blog_id, token, title) is not None


def legacy_daily_title(today: str) -> str:
    return f"Pulso Tech Diario: {today}"


def find_daily_post_for_date(existing_posts: dict[str, dict], today: str) -> dict | None:
    for candidate_title, post in existing_posts.items():
        if candidate_title.startswith("Noticias de tecnologia:") and candidate_title.endswith(f"| {today}"):
            return post
    return None


def daily_post_title(items: list[build.Item], today: str) -> str:
    preferred = ["inteligencia artificial", "chips", "ciberseguridad", "web y plataformas", "startups"]
    labels = {
        "inteligencia artificial": "IA",
        "chips": "chips",
        "ciberseguridad": "ciberseguridad",
        "web y plataformas": "plataformas",
        "startups": "startups",
        "consumo": "apps",
        "ciencia": "ciencia",
    }
    categories = []
    item_categories = {item.category for item in items}
    for category in preferred:
        if category in item_categories:
            categories.append(labels[category])
    for item in items:
        label = labels.get(item.category, item.category)
        if label not in categories:
            categories.append(label)
        if len(categories) == 3:
            break
    topic_text = ", ".join(categories[:3]) if categories else "IA, chips y ciberseguridad"
    return f"Noticias de tecnologia: {topic_text} | {today}"


TOPIC_DIGESTS = [
    {
        "title": "Inteligencia artificial hoy",
        "categories": {"inteligencia artificial"},
        "labels": ["inteligencia artificial", "ia", "noticias tech", "pulso tech diario"],
        "intro": "Resumen en espanol de las senales de IA que pueden afectar software, productividad, trabajo y plataformas digitales.",
    },
    {
        "title": "Ciberseguridad hoy",
        "categories": {"ciberseguridad"},
        "labels": ["ciberseguridad", "privacidad", "noticias tech", "pulso tech diario"],
        "intro": "Alertas y movimientos de seguridad digital explicados rapido para entender riesgos, datos y acciones preventivas.",
    },
    {
        "title": "Chips y hardware para IA hoy",
        "categories": {"chips"},
        "labels": ["chips", "hardware", "ia local", "noticias tech", "pulso tech diario"],
        "intro": "Senales sobre GPU, NPU, semiconductores y computo que pueden mover la siguiente ola de inteligencia artificial.",
    },
]


def topic_post_title(topic: dict, today: str) -> str:
    return f"{topic['title']}: resumen de tecnologia | {today}"


def topic_digest_posts(
    items: list[build.Item],
    today: str,
    daily_url: str,
    guide_posts: list[tuple[str, str]] | None = None,
) -> list[dict]:
    indexed_items = list(enumerate(items, start=1))
    posts = []
    for topic in TOPIC_DIGESTS:
        selected = [(index, item) for index, item in indexed_items if item.category in topic["categories"]]
        if not selected:
            continue
        rows = []
        for rank, (original_index, item) in enumerate(selected[:4], start=1):
            title = build.display_title(item)
            rows.append(
                f"""
<section style="margin:0 0 28px;padding:0 0 24px;border-bottom:1px solid #2b2b2b;">
  <p style="margin:0 0 10px;color:#ff7058;font-size:12px;font-weight:900;text-transform:uppercase;letter-spacing:.08em;">#{rank} &middot; {html.escape(item.source)}</p>
  <img src="{html.escape(public_image_url(item, original_index))}" alt="{html.escape(title)}" width="1200" height="630" style="display:block;width:100%;height:auto;margin:0 0 16px;background:#0f172a;border:0;" loading="lazy">
  <h2 style="margin:0 0 10px;font-size:30px;line-height:1.08;font-style:italic;color:#ff7058;"><a href="{html.escape(item.link)}" target="_blank" rel="noopener" style="color:#ff7058;text-decoration:none;">{html.escape(title)}</a></h2>
  <p style="margin:0 0 12px;color:#f1e7dd;font-size:15px;line-height:1.7;">{html.escape(build.display_summary(item))}</p>
  <p style="margin:0;color:#c8b8aa;font-size:13px;line-height:1.6;"><strong style="color:#f7f1e8;">Por que importa:</strong> {html.escape(build.reading_angle(item))}</p>
</section>
"""
            )
        content = f"""
<div style="background:#151515;color:#f7f1e8;padding:30px 28px 36px;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:900px;margin:0 auto;">
    <p style="margin:0 0 10px;color:#ff7058;font-size:12px;font-weight:900;text-transform:uppercase;letter-spacing:.08em;">Pulso Tech Diario &middot; {today}</p>
    <h1 style="margin:0 0 14px;font-size:42px;line-height:1.02;font-style:italic;color:#ffffff;">{html.escape(topic["title"])}</h1>
    <p style="margin:0 0 26px;color:#c8b8aa;font-size:17px;line-height:1.65;">{html.escape(topic["intro"])}</p>
    {''.join(rows)}
    <div style="margin:28px 0 0;padding:18px;background:#201512;border:1px solid #ff7058;">
      <p style="margin:0 0 10px;color:#ffffff;font-weight:900;">Resumen completo del dia</p>
      <p style="margin:0;color:#f1e7dd;line-height:1.6;">Esta entrada tematica complementa el resumen diario general. Para ver todas las senales de tecnologia de hoy, abre: <a href="{html.escape(daily_url)}" style="color:#ff7058;font-weight:900;">noticias de tecnologia del dia</a>.</p>
    </div>
    {internal_link_block(guide_posts)}
  </div>
</div>
"""
        posts.append(
            {
                "title": topic_post_title(topic, today),
                "labels": topic["labels"],
                "content": content,
            }
        )
    return posts


def cleanup_managed_duplicates(blog_id: str, token: str, managed_titles: set[str]) -> None:
    grouped: dict[str, list[dict]] = {}
    for post in list_posts(blog_id, token):
        title = post.get("title", "")
        if title in managed_titles:
            grouped.setdefault(title, []).append(post)
    for title, posts in grouped.items():
        ordered = sorted(posts, key=lambda post: post.get("updated", ""), reverse=True)
        for duplicate in ordered[1:]:
            post_id = duplicate.get("id")
            if not post_id:
                continue
            delete_url = f"{BLOGGER_API}/blogs/{blog_id}/posts/{post_id}"
            request_json(delete_url, method="DELETE", token=token)
            print(f"Deleted duplicate managed post: {title}")
            throttle_write()


def cleanup_legacy_daily_posts(blog_id: str, token: str, current_title: str) -> None:
    legacy_daily = re.compile(r"^Pulso Tech Diario:\s*\d{4}-\d{2}-\d{2}$")
    for post in list_posts(blog_id, token):
        title = (post.get("title") or "").strip()
        post_id = post.get("id")
        if not post_id:
            continue
        if title == current_title:
            continue
        should_delete = legacy_daily.match(title) is not None or title == ""
        if not should_delete:
            continue
        delete_url = f"{BLOGGER_API}/blogs/{blog_id}/posts/{post_id}"
        request_json(delete_url, method="DELETE", token=token)
        print(f"Deleted legacy daily post: {title or '(sin titulo)'}")
        throttle_write()


def ensure_evergreen_posts(blog_id: str, token: str, existing_posts: dict[str, dict]) -> None:
    guide_posts = guide_posts_from(existing_posts)
    update_existing = os.environ.get("BLOGGER_UPDATE_EXISTING_EVERGREEN", "").strip().lower() in {"1", "true", "yes"}
    for post in EVERGREEN_POSTS:
        title = post["title"]
        if title in PAGE_ONLY_GUIDES:
            print(f"Page-only guide skipped as post: {title}")
            continue
        content = f"{post['content'].strip()}\n{internal_link_block(guide_posts)}"
        payload = post_payload(title, content, post["labels"])
        existing = existing_posts.get(title)
        try:
            if existing and existing.get("id"):
                if update_existing:
                    update_url = f"{BLOGGER_API}/blogs/{blog_id}/posts/{existing['id']}"
                    request_json(update_url, method="PUT", token=token, payload=payload)
                    print(f"Updated evergreen post: {title}")
                    throttle_write()
                else:
                    print(f"Evergreen post already exists: {title}")
            else:
                insert_url = f"{BLOGGER_API}/blogs/{blog_id}/posts/"
                request_json(insert_url, method="POST", token=token, payload=payload)
                print(f"Created evergreen post: {title}")
                throttle_write()
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            print(f"Warning: skipped evergreen post after HTTP {exc.code}: {title}")
            print(body[:600])
            if exc.code not in {403, 429, 500, 502, 503, 504}:
                raise


def daily_growth_block(daily_url: str, items: list[build.Item]) -> str:
    topics = []
    for item in items:
        if item.category not in topics:
            topics.append(item.category)
        if len(topics) == 4:
            break
    topic_text = ", ".join(topics) if topics else "inteligencia artificial, chips y ciberseguridad"
    return f"""
<div style="margin:28px 0;padding:18px;background:#151515;color:#f7f1e8;border:1px solid #ff7058;">
  <p style="margin:0 0 8px;color:#ff7058;font-weight:900;text-transform:uppercase;letter-spacing:.08em;font-size:12px;">Hoy en Pulso Tech Diario</p>
  <p style="margin:0 0 12px;line-height:1.65;">El resumen actualizado de hoy sigue senales sobre {html.escape(topic_text)}. Esta guia se mantiene enlazada al flujo diario para que los lectores encuentren noticias recientes desde paginas ya indexadas.</p>
  <p style="margin:0;"><a href="{html.escape(daily_url)}" style="color:#ff7058;font-weight:900;">Leer noticias de tecnologia de hoy</a></p>
</div>
"""


def growth_refresh_titles(items: list[build.Item]) -> list[str]:
    priority = [
        "Como leer tecnologia sin ruido: metodo Pulso Tech",
        "Senales que miramos cada dia en chips, seguridad y startups",
        "Glosario rapido de inteligencia artificial para lectores ocupados",
        "Como elegir herramientas de IA sin caer en humo",
        "Como detectar phishing: senales simples antes de hacer clic",
        "Como proteger tus cuentas despues de una filtracion de datos",
        "Chips de IA: que significan GPU, NPU y memoria unificada",
        "Que es la IA local y por que puede cambiar tu computadora",
        "Privacidad con IA: que datos no debes subir a un chatbot",
    ]
    available = [post["title"] for post in EVERGREEN_POSTS if post["title"] not in PAGE_ONLY_GUIDES]
    ordered = [title for title in priority if title in available]
    ordered.extend(title for title in available if title not in ordered)
    return ordered[:10]


def refresh_existing_growth_posts(
    blog_id: str,
    token: str,
    existing_posts: dict[str, dict],
    items: list[build.Item],
    daily_url: str,
    guide_posts: list[tuple[str, str]] | None = None,
) -> None:
    posts_by_static_title = {post["title"]: post for post in EVERGREEN_POSTS}
    block = daily_growth_block(daily_url, items)
    for title in growth_refresh_titles(items):
        post = posts_by_static_title.get(title)
        existing = existing_posts.get(title)
        if not post or not existing or not existing.get("id"):
            continue
        content = f"{post['content'].strip()}\n{block}\n{internal_link_block(guide_posts)}"
        payload = post_payload(title, content, post["labels"])
        try:
            update_url = f"{BLOGGER_API}/blogs/{blog_id}/posts/{existing['id']}"
            result = request_json(update_url, method="PUT", token=token, payload=payload)
            print(f"Refreshed growth post: {result.get('url', result.get('id'))}")
            throttle_write()
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            print(f"Warning: skipped growth refresh after HTTP {exc.code}: {title}")
            print(body[:600])
            if exc.code not in {403, 429, 500, 502, 503, 504}:
                raise


def publish() -> None:
    blog_id = required_env("BLOGGER_BLOG_ID")
    token = get_access_token()
    ensure_base_pages(blog_id, token)
    items = build.collect_items() or build.fallback_items()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    title = daily_post_title(items, today)
    old_title = legacy_daily_title(today)
    managed_titles = {post["title"] for post in EVERGREEN_POSTS if post["title"] not in PAGE_ONLY_GUIDES}
    managed_titles.add(title)
    managed_titles.add(old_title)
    cleanup_legacy_daily_posts(blog_id, token, title)
    cleanup_managed_duplicates(blog_id, token, managed_titles)
    existing_posts = posts_by_title(list_posts(blog_id, token))
    ensure_evergreen_posts(blog_id, token, existing_posts)
    existing_posts = posts_by_title(list_posts(blog_id, token))
    guide_posts = guide_posts_from(existing_posts)
    ensure_base_pages(
        blog_id,
        token,
        {"Empieza aqui": start_here_content(guide_posts)},
    )
    create_extra_pages = os.environ.get("BLOGGER_CREATE_EXTRA_GUIDE_PAGES", "").strip().lower() in {"1", "true", "yes"}
    if create_extra_pages:
        ensure_base_pages(blog_id, token, blogger_guide_pages(guide_posts))
    existing = existing_posts.get(title) or existing_posts.get(old_title) or find_daily_post_for_date(existing_posts, today)
    daily_published = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    payload = post_payload(
        title,
        post_html(items, guide_posts),
        ["tecnologia", "inteligencia artificial", "noticias tech", "pulso tech diario"],
        published=daily_published,
    )
    if existing and existing.get("id"):
        update_url = f"{BLOGGER_API}/blogs/{blog_id}/posts/{existing['id']}"
        result = request_json(update_url, method="PUT", token=token, payload=payload)
        daily_url = result.get("url", result.get("id", BLOG_URL + "/"))
        print(f"Updated daily post: {daily_url}")
    else:
        url = f"{BLOGGER_API}/blogs/{blog_id}/posts/"
        result = request_json(url, method="POST", token=token, payload=payload)
        daily_url = result.get("url", result.get("id", BLOG_URL + "/"))
        print(f"Published: {daily_url}")
    throttle_write()
    existing_posts = posts_by_title(list_posts(blog_id, token))
    refresh_existing_growth_posts(blog_id, token, existing_posts, items, daily_url, guide_posts)


if __name__ == "__main__":
    try:
        publish()
    except urllib.error.HTTPError as exc:
        sys.stderr.write(exc.read().decode("utf-8", errors="replace"))
        raise
