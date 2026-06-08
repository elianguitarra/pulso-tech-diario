#!/usr/bin/env python3
"""Build Pulso Tech Diario as a zero-dependency static site."""

from __future__ import annotations

import email.utils
import html
import json
import math
import os
import re
import shutil
import textwrap
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
ASSET_DIR = PUBLIC / "assets" / "images"
FEATURE_ASSET_SOURCE = ROOT / "assets" / "features"
FEATURE_ASSET_DEST = PUBLIC / "assets" / "features"
BRAND_ASSET_SOURCE = ROOT / "assets" / "brand"
BRAND_ASSET_DEST = PUBLIC / "assets" / "brand"

SITE_NAME = "Pulso Tech Diario"
SITE_DESCRIPTION = (
    "Un resumen diario y automatizado de las noticias tecnologicas mas relevantes, "
    "con imagenes originales generadas por el propio sitio."
)
SITE_URL = os.environ.get("SITE_URL", "https://elianguitarra.github.io/pulso-tech-diario").rstrip("/")
WEBSUB_HUB_URL = "https://pubsubhubbub.appspot.com/"
ADSENSE_CLIENT = os.environ.get("ADSENSE_CLIENT", "").strip()
ADSENSE_TOP_SLOT = os.environ.get("ADSENSE_TOP_SLOT", "").strip()
ADSENSE_IN_ARTICLE_SLOT = os.environ.get("ADSENSE_IN_ARTICLE_SLOT", "").strip()
INDEXNOW_KEY = os.environ.get("INDEXNOW_KEY", "pulso-tech-diario-2026-indexnow-key").strip()
BLOG_URL = "https://pulsotechdiario.blogspot.com"
BLOGGER_START_URL = f"{BLOG_URL}/p/empieza-aqui.html"
BLOGGER_RSS_URL = f"{BLOG_URL}/feeds/posts/default?alt=rss"


def tracked_url(url: str, source: str, medium: str, campaign: str, content: str = "") -> str:
    params = {
        "utm_source": source,
        "utm_medium": medium,
        "utm_campaign": campaign,
    }
    if content:
        params["utm_content"] = content
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}{urllib.parse.urlencode(params)}"


BLOG_HOME_TRACKED = tracked_url(f"{BLOG_URL}/", "github_pages", "referral", "traffic_hub", "home")
BLOGGER_START_TRACKED = tracked_url(BLOGGER_START_URL, "github_pages", "referral", "traffic_hub", "start")
BLOGGER_LABEL_IA_TRACKED = tracked_url(
    f"{BLOG_URL}/search/label/inteligencia%20artificial",
    "github_pages",
    "referral",
    "topic_hub",
    "ia",
)
BLOGGER_LABEL_CYBER_TRACKED = tracked_url(
    f"{BLOG_URL}/search/label/ciberseguridad",
    "github_pages",
    "referral",
    "topic_hub",
    "ciberseguridad",
)
BLOGGER_LABEL_CHIPS_TRACKED = tracked_url(
    f"{BLOG_URL}/search/label/chips",
    "github_pages",
    "referral",
    "topic_hub",
    "chips",
)
BLOGGER_LABEL_PRIVACY_TRACKED = tracked_url(
    f"{BLOG_URL}/search/label/privacidad",
    "github_pages",
    "referral",
    "topic_hub",
    "privacidad",
)
BLOGGER_LABEL_PHISHING_TRACKED = tracked_url(
    f"{BLOG_URL}/search/label/phishing",
    "github_pages",
    "referral",
    "topic_hub",
    "phishing",
)
BLOGGER_LABEL_LOCAL_AI_TRACKED = tracked_url(
    f"{BLOG_URL}/search/label/ia%20local",
    "github_pages",
    "referral",
    "topic_hub",
    "ia_local",
)

TREND_PAGES = [
    {
        "filename": "tendencias-tecnologia-hoy.html",
        "title": "Tendencias de tecnologia hoy",
        "description": "Tendencias de tecnologia hoy en espanol: IA, ciberseguridad, chips, plataformas y herramientas digitales resumidas rapido.",
        "intro": "Resumen en espanol de las senales que se estan moviendo ahora en IA, chips, ciberseguridad, plataformas y herramientas digitales.",
        "blogger_url": BLOG_HOME_TRACKED,
        "categories": None,
    },
    {
        "filename": "inteligencia-artificial-hoy.html",
        "title": "Inteligencia artificial hoy",
        "description": "Noticias y tendencias de inteligencia artificial hoy en espanol: modelos, agentes, productividad, privacidad y herramientas.",
        "intro": "Senales recientes sobre inteligencia artificial, modelos, agentes, productividad, privacidad y herramientas que conviene vigilar hoy.",
        "blogger_url": BLOGGER_LABEL_IA_TRACKED,
        "categories": {"inteligencia artificial"},
    },
    {
        "filename": "ciberseguridad-hoy.html",
        "title": "Ciberseguridad hoy",
        "description": "Noticias y tendencias de ciberseguridad hoy en espanol: phishing, privacidad, filtraciones, malware y proteccion de cuentas.",
        "intro": "Riesgos, filtraciones, phishing y cambios de seguridad digital explicados rapido para actuar con mas criterio.",
        "blogger_url": BLOGGER_LABEL_CYBER_TRACKED,
        "categories": {"ciberseguridad"},
    },
    {
        "filename": "chips-ia-hoy.html",
        "title": "Chips para IA hoy",
        "description": "Noticias y tendencias de chips para IA hoy en espanol: GPU, NPU, semiconductores, hardware y computo.",
        "intro": "Senales sobre chips, GPU, NPU, semiconductores y hardware que empujan la carrera de inteligencia artificial.",
        "blogger_url": BLOGGER_LABEL_CHIPS_TRACKED,
        "categories": {"chips"},
    },
]

STATIC_PAGES = {
    "acerca.html": {
        "title": "Acerca de",
        "description": "Pulso Tech Diario resume tecnologia relevante cada dia con fuentes publicas, enlaces originales e imagenes propias.",
        "body": """
<p><strong>Pulso Tech Diario</strong> es un sitio automatizado que resume noticias tecnologicas relevantes cada dia.</p>
<p>El objetivo es ayudar a lectores ocupados a detectar senales importantes sobre inteligencia artificial, chips, ciberseguridad, startups, consumo digital, ciencia aplicada y plataformas web.</p>
<p>El sistema revisa fuentes publicas por RSS, ordena las notas por frescura, relevancia tematica y fuente, y enlaza siempre al articulo original.</p>
""",
    },
    "politica-editorial.html": {
        "title": "Politica editorial",
        "description": "Criterios editoriales de Pulso Tech Diario para seleccionar, resumir y enlazar noticias tecnologicas.",
        "body": """
<p>Pulso Tech Diario no copia articulos completos. Cada entrada usa resumen editorial propio y enlaces directos a las fuentes originales.</p>
<p>Las notas se seleccionan automaticamente con reglas de relevancia, pero el sitio prioriza contenido informativo, trazable y util para lectores interesados en tecnologia.</p>
<p>Las imagenes que acompanan cada noticia son ilustraciones SVG originales generadas automaticamente para este sitio. No representan capturas ni fotografias de los articulos enlazados.</p>
""",
    },
    "privacidad.html": {
        "title": "Privacidad",
        "description": "Informacion de privacidad, cookies y anuncios para lectores de Pulso Tech Diario.",
        "body": """
<p>Este sitio se publica como una pagina estatica gratuita en GitHub Pages. El hosting puede procesar datos tecnicos habituales como direccion IP, navegador, dispositivo, fecha de acceso y registros de seguridad.</p>
<p>Si el sitio muestra anuncios mediante Google AdSense, Google y sus socios pueden usar cookies o identificadores para servir, medir y personalizar anuncios segun la configuracion del usuario.</p>
<p>Como lector puedes administrar cookies y preferencias de anuncios desde tu navegador y desde las herramientas de privacidad de Google.</p>
""",
    },
    "contacto.html": {
        "title": "Contacto",
        "description": "Contacto editorial y tecnico de Pulso Tech Diario.",
        "body": """
<p>Para consultas editoriales, correcciones o propuestas relacionadas con Pulso Tech Diario, usa el perfil publico asociado al proyecto en GitHub.</p>
<p>Repositorio del sistema: <a href="https://github.com/elianguitarra/pulso-tech-diario" target="_blank" rel="noopener">github.com/elianguitarra/pulso-tech-diario</a>.</p>
""",
    },
    "noticias-tecnologia-espanol.html": {
        "title": "Noticias de tecnologia en espanol, explicadas rapido",
        "description": "Resumen diario de noticias de tecnologia en espanol sobre inteligencia artificial, ciberseguridad, chips, plataformas y productividad.",
        "body": f"""
<p>Pulso Tech Diario resume cada dia senales relevantes de tecnologia para lectores que quieren entender que cambia sin leer decenas de fuentes.</p>
<h2>Que cubre</h2>
<p>El foco esta en inteligencia artificial, ciberseguridad, chips, plataformas, consumo digital, startups y herramientas que afectan trabajo y vida diaria.</p>
<h2>Como leerlo</h2>
<p>Empieza por la entrada diaria, salta a los temas que te interesan y guarda las guias evergreen para dudas recurrentes como IA local, NPU vs GPU, privacidad con chatbots o phishing.</p>
<h2>Rutas recomendadas</h2>
<ul>
  <li><a href="ultima-entrada.html">Ver la ultima entrada</a></li>
  <li><a href="temas.html">Explorar temas</a></li>
  <li><a href="que-es-ia-local.html">Que es la IA local</a></li>
  <li><a href="checklist-phishing.html">Checklist anti phishing</a></li>
  <li><a href="{BLOG_HOME_TRACKED}">Abrir el blog principal en Blogger</a></li>
</ul>
""",
        "faq": [
            ("Pulso Tech Diario publica noticias todos los dias?", "Si. El sistema genera un resumen diario automatizado y mantiene paginas evergreen para busquedas frecuentes."),
            ("Las notas estan en espanol?", "Si. Los titulares, resumenes y guias se publican en espanol aunque las fuentes originales puedan estar en ingles."),
            ("Donde esta el blog principal?", "El blog principal esta en Blogger, preparado para entradas, etiquetas y monetizacion con AdSense cuando Google lo apruebe."),
        ],
    },
    "seguir.html": {
        "title": "Seguir Pulso Tech Diario",
        "description": "Formas gratuitas de seguir Pulso Tech Diario: Blogger, RSS, Atom, JSON Feed, link en bio y ultima entrada.",
        "body": f"""
<p>El sitio publica tecnologia en espanol todos los dias. Guarda esta pagina si quieres volver rapido o seguir el contenido desde un lector de feeds.</p>
<h2>Lectura principal</h2>
<ul>
  <li><a href="{BLOG_HOME_TRACKED}">Abrir el blog principal en Blogger</a></li>
  <li><a href="ultima-entrada.html">Ultima entrada diaria</a></li>
  <li><a href="links.html">Link en bio</a></li>
  <li><a href="tendencias-tecnologia-hoy.html">Tendencias de tecnologia hoy</a></li>
</ul>
<h2>Feeds para lectores y agregadores</h2>
<ul>
  <li><a href="feed.xml">RSS del sitio</a></li>
  <li><a href="atom.xml">Atom del sitio</a></li>
  <li><a href="feed.json">JSON Feed del sitio</a></li>
  <li><a href="{BLOGGER_RSS_URL}">RSS de Blogger</a></li>
</ul>
<h2>Temas directos</h2>
<ul>
  <li><a href="inteligencia-artificial-hoy.html">Inteligencia artificial hoy</a></li>
  <li><a href="ciberseguridad-hoy.html">Ciberseguridad hoy</a></li>
  <li><a href="chips-ia-hoy.html">Chips para IA hoy</a></li>
</ul>
""",
        "faq": [
            ("Cual es la mejor forma de seguir Pulso Tech Diario?", "La forma principal es Blogger. Si usas lectores de feeds, RSS, Atom y JSON Feed permiten recibir las actualizaciones sin entrar manualmente."),
            ("Los feeds se actualizan solos?", "Si. El build diario genera RSS, Atom y JSON Feed junto con las paginas dinamicas del sitio."),
            ("Puedo compartir esta pagina?", "Si. Es una pagina publica pensada como punto de seguimiento para nuevos lectores."),
        ],
    },
    "ia-en-el-trabajo.html": {
        "title": "IA en el trabajo: donde si ahorra tiempo",
        "description": "Guia practica para saber en que tareas laborales la inteligencia artificial ayuda y donde requiere supervision humana.",
        "body": """
<p>La IA puede ahorrar tiempo, pero no en cualquier tarea. Funciona mejor cuando hay informacion clara, criterios de revision y un resultado que una persona puede comprobar.</p>
<h2>Donde suele ayudar</h2>
<p>Resumir reuniones, ordenar notas, crear primeros borradores, explicar codigo, comparar opciones, transformar formatos y preparar listas de preguntas son usos donde la IA puede reducir friccion.</p>
<h2>Donde hay que tener cuidado</h2>
<p>Decisiones legales, medicas, financieras, datos sensibles, calculos criticos o comunicados delicados requieren revision experta. La IA puede sugerir, pero no debe reemplazar responsabilidad.</p>
<h2>Como medir si sirve</h2>
<p>El beneficio no es que la herramienta suene inteligente. Mide si reduce minutos, errores o pasos repetidos. Si tienes que corregir demasiado, tal vez el flujo no esta listo.</p>
<h2>Prompts utiles</h2>
<p>Da contexto, objetivo, formato esperado y criterios de calidad. En vez de pedir hazlo mejor, pide resume en 5 puntos para un gerente que necesita decidir hoy.</p>
<h2>La regla de oro</h2>
<p>Usa IA como copiloto para avanzar mas rapido, no como piloto automatico para tareas que no puedes revisar. El ahorro real aparece cuando el humano conserva criterio.</p>
<p><a href="./">Volver al resumen diario</a></p>
""",
    },
    "comprar-laptop-para-ia.html": {
        "title": "Que revisar antes de comprar una laptop para IA",
        "description": "Guia para evaluar memoria, GPU, NPU, software, bateria y uso real antes de comprar una laptop para inteligencia artificial.",
        "body": """
<p>Las computadoras nuevas prometen funciones de IA, pero no todas sirven para lo mismo. Antes de comprar una laptop conviene mirar mas que el anuncio de AI PC.</p>
<h2>Memoria RAM</h2>
<p>La memoria importa mucho para trabajar con modelos, navegadores pesados, edicion y multitarea. Para uso moderno, 16 GB suele ser el punto de partida razonable; para trabajo pesado, mas memoria ayuda.</p>
<h2>GPU, NPU y CPU</h2>
<p>La GPU puede acelerar tareas de IA y graficos. La NPU busca eficiencia para funciones integradas. La CPU sigue importando para rendimiento general. No compres solo por una sigla.</p>
<h2>Software compatible</h2>
<p>Un chip potente no sirve de mucho si tus aplicaciones no lo aprovechan. Revisa si las herramientas que usas soportan funciones locales o aceleracion real.</p>
<h2>Bateria y temperatura</h2>
<p>La IA local puede consumir recursos. Mira resenas de autonomia, ruido y temperatura, no solo numeros de rendimiento.</p>
<h2>Compra con una tarea en mente</h2>
<p>Si solo quieres escribir, navegar y usar chatbots en la nube, no necesitas pagar de mas. Si vas a editar video, programar, generar imagenes o probar modelos locales, hardware y memoria pesan mucho mas.</p>
<p><a href="./">Volver al resumen diario</a></p>
""",
    },
    "herramientas-ia-gratis.html": {
        "title": "Herramientas de IA gratis: como elegir sin perder tiempo",
        "description": "Guia en espanol para elegir herramientas de IA gratis segun tarea, privacidad, limites y valor real.",
        "body": f"""
<p>Las herramientas de IA gratis sirven para probar flujos, aprender y ahorrar tiempo en tareas concretas. La clave no es acumular cuentas, sino elegir segun lo que necesitas resolver.</p>
<h2>Empieza por la tarea</h2>
<p>Define si necesitas resumir textos, escribir borradores, estudiar, programar, generar ideas, transcribir audio o analizar documentos. Una herramienta gratuita es buena si reduce pasos sin aumentar errores.</p>
<h2>Revisa los limites</h2>
<p>Muchos planes gratis tienen limites de mensajes, archivos, velocidad, modelos disponibles o historial. Antes de depender de una herramienta, prueba que el limite no rompa tu flujo diario.</p>
<h2>Cuida tus datos</h2>
<p>No subas contrasenas, datos de clientes, documentos privados, claves API ni informacion que no publicarias. Para datos sensibles, usa ejemplos ficticios o versiones anonimizadas.</p>
<h2>Como comparar rapido</h2>
<p>Prueba la misma tarea en dos o tres herramientas: un resumen, una tabla y un borrador. Quedate con la que requiere menos correcciones y explica mejor sus resultados.</p>
<h2>Rutas recomendadas</h2>
<ul>
  <li><a href="chatgpt-gemini-claude.html">ChatGPT, Gemini o Claude: como elegir</a></li>
  <li><a href="privacidad-chatbots-ia.html">Privacidad con chatbots de IA</a></li>
  <li><a href="ia-en-el-trabajo.html">IA en el trabajo</a></li>
  <li><a href="{BLOGGER_LABEL_IA_TRACKED}">Noticias de IA en Blogger</a></li>
</ul>
""",
        "faq": [
            ("Cual es la mejor herramienta de IA gratis?", "Depende de la tarea. La mejor es la que resuelve tu caso real con menos correcciones y sin exponer datos sensibles."),
            ("Conviene pagar por una herramienta de IA?", "Conviene si el plan gratis se queda corto y la herramienta ahorra tiempo de forma constante."),
            ("Puedo usar IA gratis para trabajo?", "Si, pero evita datos confidenciales y revisa las politicas de tu empresa o cliente."),
        ],
    },
    "proteger-cuenta-google.html": {
        "title": "Como proteger tu cuenta Google: checklist rapido",
        "description": "Checklist en espanol para proteger una cuenta Google con contrasena segura, verificacion en dos pasos, sesiones y alertas.",
        "body": f"""
<p>Tu cuenta Google suele concentrar correo, archivos, fotos, Android, recuperacion de contrasenas y acceso a otros servicios. Protegerla reduce mucho el riesgo digital diario.</p>
<h2>1. Activa verificacion en dos pasos</h2>
<p>Usa una app autenticadora, passkey o llave de seguridad cuando sea posible. El SMS es mejor que nada, pero no es la opcion mas resistente.</p>
<h2>2. Revisa dispositivos conectados</h2>
<p>En seguridad de la cuenta, cierra sesiones que no reconozcas y elimina equipos antiguos. Si ves actividad rara, cambia contrasena y revisa recuperacion.</p>
<h2>3. Cuida correo y recuperacion</h2>
<p>Verifica que el correo y telefono de recuperacion sean tuyos. Si alguien controla la recuperacion, puede intentar recuperar tu cuenta.</p>
<h2>4. Desconfia de avisos urgentes</h2>
<p>No abras enlaces de correos que amenazan con cerrar tu cuenta. Entra manualmente a Google desde el navegador y revisa alertas oficiales.</p>
<h2>Rutas recomendadas</h2>
<ul>
  <li><a href="checklist-phishing.html">Checklist anti phishing</a></li>
  <li><a href="privacidad-chatbots-ia.html">Privacidad con IA</a></li>
  <li><a href="{BLOGGER_LABEL_CYBER_TRACKED}">Entradas de ciberseguridad en Blogger</a></li>
</ul>
""",
        "faq": [
            ("Que hago si alguien entro a mi cuenta Google?", "Cambia la contrasena, cierra sesiones desconocidas, revisa recuperacion, activa verificacion en dos pasos y revisa actividad reciente."),
            ("Las passkeys son mejores que contrasenas?", "Pueden reducir phishing y robo de contrasenas, pero conviene mantener metodos de recuperacion seguros."),
            ("Debo revisar permisos de apps?", "Si. Elimina apps que no uses o que tengan permisos excesivos sobre correo, archivos o contactos."),
        ],
    },
    "ia-para-estudiantes.html": {
        "title": "IA para estudiantes: usos utiles y errores a evitar",
        "description": "Guia para usar IA al estudiar sin copiar: resumenes, preguntas, explicaciones, privacidad y revision critica.",
        "body": f"""
<p>La IA puede ayudar a estudiar mejor si se usa como apoyo, no como sustituto del aprendizaje. Sirve para explicar, practicar, ordenar ideas y detectar dudas.</p>
<h2>Usos utiles</h2>
<p>Pide explicaciones con ejemplos, preguntas de repaso, mapas de conceptos, resumenes comparativos o una lista de temas que debes dominar antes de un examen.</p>
<h2>Errores a evitar</h2>
<p>No entregues respuestas generadas sin revisar, no copies trabajos completos y no confies en datos sin verificar. La IA puede inventar referencias o equivocarse con seguridad.</p>
<h2>Mejor prompt</h2>
<p>Da nivel, tema, objetivo y formato. Por ejemplo: explicame fotosintesis como si estuviera en secundaria y luego hazme 10 preguntas con respuestas.</p>
<h2>Privacidad</h2>
<p>No subas datos personales, documentos internos de la escuela, nombres de companeros ni informacion sensible. Puedes reemplazar datos reales por ejemplos ficticios.</p>
<h2>Rutas recomendadas</h2>
<ul>
  <li><a href="herramientas-ia-gratis.html">Herramientas de IA gratis</a></li>
  <li><a href="chatgpt-gemini-claude.html">Elegir chatbot de IA</a></li>
  <li><a href="glosario-ia-tecnologia.html">Glosario rapido de IA</a></li>
  <li><a href="{BLOGGER_LABEL_IA_TRACKED}">Noticias de IA en Blogger</a></li>
</ul>
""",
        "faq": [
            ("Usar IA para estudiar es trampa?", "Depende del uso y las reglas de tu escuela. Usarla para explicar o practicar puede ayudar; entregar respuestas copiadas suele ser un problema."),
            ("La IA siempre da respuestas correctas?", "No. Conviene verificar datos, fuentes y ejercicios, especialmente en matematicas, fechas y citas."),
            ("Como uso IA sin dejar de aprender?", "Pide pistas, explicaciones y preguntas de practica antes de pedir una respuesta final."),
        ],
    },
    "que-es-ia-local.html": {
        "title": "Que es la IA local y cuando conviene usarla",
        "description": "Explicacion clara sobre IA local, modelos en el dispositivo, ventajas, limites y casos donde conviene frente a la nube.",
        "body": f"""
<p>La IA local es inteligencia artificial que corre en tu computadora, telefono o dispositivo sin depender todo el tiempo de un servidor externo. Puede servir para escribir, resumir, transcribir, clasificar archivos o ejecutar modelos pequenos con mas control.</p>
<h2>Por que importa</h2>
<p>Si una tarea se ejecuta localmente, puede mejorar privacidad, reducir latencia y funcionar incluso cuando la conexion no es ideal. Tambien puede bajar costos si haces muchas pruebas.</p>
<h2>Limites reales</h2>
<p>Los modelos locales suelen necesitar memoria, bateria y hardware adecuado. No siempre igualan a los modelos grandes en la nube, y requieren revisar resultados con criterio.</p>
<h2>Cuando elegirla</h2>
<p>Conviene para datos sensibles, tareas repetidas, prototipos, notas personales, busqueda interna y flujos donde la velocidad importa mas que tener el modelo mas grande.</p>
<p><a href="comprar-laptop-para-ia.html">Ver que revisar antes de comprar una laptop para IA</a></p>
<p><a href="{BLOGGER_LABEL_LOCAL_AI_TRACKED}">Leer entradas de IA local en Blogger</a></p>
""",
        "faq": [
            ("La IA local necesita internet?", "No siempre. Algunas funciones pueden correr sin conexion, pero descargar modelos, actualizaciones o herramientas suele requerir internet."),
            ("La IA local es mas privada?", "Puede serlo cuando los datos no salen del dispositivo, aunque depende de la app, permisos, sincronizacion y configuracion."),
            ("Necesito una GPU para usar IA local?", "No para todo. Tareas pequenas pueden correr en CPU o NPU, pero modelos mas grandes y generacion multimedia suelen beneficiarse de GPU y mas memoria."),
        ],
    },
    "npu-vs-gpu.html": {
        "title": "NPU vs GPU: diferencias para inteligencia artificial",
        "description": "Comparacion practica entre NPU, GPU y CPU para entender que hardware importa en laptops y PCs con inteligencia artificial.",
        "body": f"""
<p>NPU y GPU no son lo mismo. Ambas pueden acelerar tareas de inteligencia artificial, pero estan pensadas para necesidades distintas.</p>
<h2>Que hace una GPU</h2>
<p>La GPU esta disenada para procesamiento paralelo potente. Es clave en graficos, video, juegos, entrenamiento, generacion de imagenes y modelos pesados.</p>
<h2>Que hace una NPU</h2>
<p>La NPU busca eficiencia. Sirve para funciones integradas como desenfoque de camara, transcripcion, efectos en tiempo real o asistentes locales con menor consumo.</p>
<h2>Que mirar al comprar</h2>
<p>No compres solo por una sigla. Revisa memoria RAM, compatibilidad de software, autonomia, temperatura, puertos y si tus aplicaciones realmente aprovechan esa NPU o GPU.</p>
<p><a href="comprar-laptop-para-ia.html">Guia de compra de laptops para IA</a></p>
<p><a href="{BLOGGER_LABEL_CHIPS_TRACKED}">Leer entradas de chips en Blogger</a></p>
""",
        "faq": [
            ("Es mejor una NPU o una GPU?", "Depende del uso. La GPU suele rendir mejor en tareas pesadas; la NPU suele ser mas eficiente para funciones integradas y continuas."),
            ("Una laptop con NPU sirve para generar imagenes?", "Puede ayudar en algunas funciones, pero la generacion exigente normalmente depende mas de GPU, memoria y soporte de software."),
            ("La CPU deja de importar?", "No. La CPU sigue siendo central para rendimiento general, multitarea, navegacion, programacion y muchas tareas diarias."),
        ],
    },
    "privacidad-chatbots-ia.html": {
        "title": "Privacidad con chatbots de IA: que datos no subir",
        "description": "Lista practica de datos que conviene evitar en chatbots de IA y como usarlos con menor riesgo.",
        "body": f"""
<p>Los chatbots de IA son utiles, pero no todo debe pegarse en una conversacion. La regla simple: si no lo publicarias o no tienes permiso para compartirlo, no lo subas.</p>
<h2>Datos que debes evitar</h2>
<p>No subas contrasenas, codigos de verificacion, documentos legales sensibles, datos medicos, claves API, informacion bancaria, datos de clientes o archivos internos sin autorizacion.</p>
<h2>Como reducir riesgo</h2>
<p>Quita nombres, cambia numeros, resume el contexto y usa ejemplos ficticios. Si trabajas en empresa, revisa politicas internas antes de subir documentos.</p>
<h2>Buen uso</h2>
<p>Puedes pedir estructuras, listas de revision, ideas, borradores y explicaciones sin revelar datos reales. El valor aparece cuando separas la tarea del dato sensible.</p>
<p><a href="{BLOGGER_LABEL_PRIVACY_TRACKED}">Leer mas sobre privacidad en Blogger</a></p>
<p><a href="ia-en-el-trabajo.html">Ver usos de IA en el trabajo</a></p>
""",
        "faq": [
            ("Puedo pegar datos de clientes en un chatbot?", "Solo si tienes permiso, contrato, configuracion adecuada y una politica clara. En caso de duda, no lo hagas."),
            ("Que hago si necesito ayuda con un documento sensible?", "Crea una version anonimizada, elimina identificadores y pregunta por estructura o criterios, no por datos reales."),
            ("Los chatbots siempre entrenan con mis datos?", "Depende del servicio, plan y configuracion. Revisa privacidad, controles de historial y politicas de uso de datos."),
        ],
    },
    "checklist-phishing.html": {
        "title": "Checklist anti phishing antes de hacer clic",
        "description": "Checklist rapido para detectar phishing en correos, mensajes, enlaces, adjuntos y codigos de verificacion.",
        "body": f"""
<p>El phishing funciona porque empuja a actuar rapido. Esta checklist ayuda a frenar unos segundos antes de entregar contrasenas, codigos o datos personales.</p>
<h2>Revision rapida</h2>
<ul>
  <li>Confirma el dominio real del enlace.</li>
  <li>Desconfia de urgencia extrema o amenazas.</li>
  <li>No abras adjuntos inesperados.</li>
  <li>No compartas codigos de verificacion.</li>
  <li>Entra al servicio escribiendo la direccion manualmente.</li>
</ul>
<h2>Senales comunes</h2>
<p>Errores raros, remitentes parecidos, enlaces acortados, formularios externos y solicitudes de pago fuera del canal normal son senales para detenerse.</p>
<p><a href="{BLOGGER_LABEL_PHISHING_TRACKED}">Leer guias de phishing en Blogger</a></p>
<p><a href="{BLOGGER_LABEL_CYBER_TRACKED}">Ver mas sobre ciberseguridad</a></p>
""",
        "faq": [
            ("Que hago si ya hice clic?", "Cambia la contrasena desde el sitio oficial, cierra sesiones activas, activa verificacion en dos pasos y revisa actividad reciente."),
            ("Un mensaje puede ser phishing si viene de alguien conocido?", "Si. Las cuentas comprometidas tambien se usan para enviar enlaces maliciosos a contactos reales."),
            ("Debo abrir un adjunto para comprobarlo?", "No. Si no esperabas el archivo, confirma por otro canal antes de abrirlo."),
        ],
    },
    "glosario-ia-tecnologia.html": {
        "title": "Glosario rapido de IA, chips y ciberseguridad",
        "description": "Definiciones simples de terminos frecuentes sobre inteligencia artificial, hardware, seguridad digital y tecnologia diaria.",
        "body": f"""
<p>Este glosario resume terminos que aparecen una y otra vez en noticias de tecnologia. La idea es leer rapido, entender el contexto y saber que ruta seguir.</p>
<h2>Inteligencia artificial</h2>
<p><strong>IA:</strong> sistemas que realizan tareas asociadas con lenguaje, vision, prediccion, clasificacion o generacion de contenido.</p>
<p><strong>LLM:</strong> modelo de lenguaje grande. Sirve para generar texto, resumir, responder preguntas y ayudar con codigo o documentos.</p>
<p><strong>Agente de IA:</strong> sistema que no solo responde, sino que intenta ejecutar pasos para cumplir una tarea.</p>
<p><strong>IA local:</strong> IA que corre en tu dispositivo. Puede mejorar privacidad y velocidad, pero depende de memoria, chips y software compatible.</p>
<h2>Chips y hardware</h2>
<p><strong>GPU:</strong> procesador grafico util para tareas paralelas, graficos, video y cargas pesadas de IA.</p>
<p><strong>NPU:</strong> unidad pensada para acelerar funciones de IA con menor consumo en dispositivos modernos.</p>
<p><strong>Memoria unificada:</strong> memoria compartida por CPU, GPU y otros componentes. Puede ayudar en equipos que ejecutan modelos o tareas multimedia.</p>
<h2>Ciberseguridad</h2>
<p><strong>Phishing:</strong> intento de engaño para robar contrasenas, codigos, dinero o datos personales.</p>
<p><strong>Filtracion de datos:</strong> exposicion no autorizada de informacion privada, credenciales o registros internos.</p>
<p><strong>2FA:</strong> verificacion en dos pasos. Agrega una segunda prueba de identidad ademas de la contrasena.</p>
<h2>Rutas recomendadas</h2>
<ul>
  <li><a href="que-es-ia-local.html">Que es la IA local</a></li>
  <li><a href="npu-vs-gpu.html">NPU vs GPU</a></li>
  <li><a href="checklist-phishing.html">Checklist anti phishing</a></li>
  <li><a href="noticias-tecnologia-espanol.html">Noticias de tecnologia en espanol</a></li>
  <li><a href="{BLOGGER_LABEL_IA_TRACKED}">Entradas de IA en Blogger</a></li>
</ul>
""",
        "faq": [
            ("Que significa LLM?", "LLM significa modelo de lenguaje grande. Es una tecnologia de IA entrenada para procesar y generar texto."),
            ("Que diferencia hay entre GPU y NPU?", "La GPU suele ser mas potente para cargas paralelas pesadas; la NPU busca eficiencia para funciones de IA integradas y continuas."),
            ("Que es phishing en palabras simples?", "Es un engaño para que entregues datos, contrasenas, codigos o dinero haciendose pasar por una entidad confiable."),
        ],
    },
    "chatgpt-gemini-claude.html": {
        "title": "ChatGPT, Gemini o Claude: como elegir un chatbot de IA",
        "description": "Comparacion practica en espanol para elegir entre ChatGPT, Gemini, Claude u otros chatbots de IA segun tarea, privacidad y flujo de trabajo.",
        "body": f"""
<p>ChatGPT, Gemini y Claude son chatbots de IA utiles, pero no conviene elegir solo por popularidad. La mejor opcion depende de la tarea, los datos que manejas y el ecosistema donde trabajas.</p>
<h2>Resumen rapido</h2>
<p>Si quieres escribir, resumir o explorar ideas, prueba el chatbot que te entregue respuestas claras y faciles de revisar. Si trabajas con documentos largos, mira manejo de contexto. Si dependes de correo, calendario, archivos o navegador, pesa mas la integracion con tus herramientas diarias.</p>
<h2>Como comparar sin perder tiempo</h2>
<ul>
  <li><strong>Calidad:</strong> pide el mismo resumen, tabla o borrador en cada herramienta y compara cual requiere menos correccion.</li>
  <li><strong>Privacidad:</strong> revisa si puedes controlar historial, entrenamiento con datos y permisos de archivos.</li>
  <li><strong>Contexto:</strong> prueba documentos largos, enlaces o instrucciones complejas si eso es parte de tu flujo.</li>
  <li><strong>Multimodal:</strong> mira si necesitas analizar imagenes, archivos, audio o capturas.</li>
  <li><strong>Costo real:</strong> no mires solo el plan; mide cuanto trabajo te ahorra al mes.</li>
</ul>
<h2>Que elegir para cada uso</h2>
<p><strong>Trabajo diario:</strong> prioriza integraciones, rapidez y facilidad para corregir.</p>
<p><strong>Estudio:</strong> busca explicaciones paso a paso, ejemplos y capacidad para generar preguntas de repaso.</p>
<p><strong>Programacion:</strong> prueba con tu propio codigo, pide tests y revisa si entiende el contexto del proyecto.</p>
<p><strong>Documentos sensibles:</strong> usa versiones anonimizadas o una opcion local/empresarial con controles claros.</p>
<h2>La prueba de 15 minutos</h2>
<p>Elige tres tareas reales: resumir un texto, crear un borrador y revisar una decision. Ejecutalas en dos o tres chatbots con el mismo prompt. La herramienta ganadora es la que produce una salida util, verificable y con menos edicion.</p>
<h2>Rutas recomendadas</h2>
<ul>
  <li><a href="privacidad-chatbots-ia.html">Privacidad con chatbots de IA</a></li>
  <li><a href="ia-en-el-trabajo.html">IA en el trabajo</a></li>
  <li><a href="que-es-ia-local.html">Que es la IA local</a></li>
  <li><a href="glosario-ia-tecnologia.html">Glosario de IA y tecnologia</a></li>
  <li><a href="{BLOGGER_LABEL_IA_TRACKED}">Noticias de IA en Blogger</a></li>
</ul>
""",
        "faq": [
            ("Cual chatbot de IA es mejor?", "No hay uno mejor para todo. Conviene probarlos con tus tareas reales y elegir el que ahorre mas tiempo con menos correccion."),
            ("Puedo subir documentos privados a un chatbot?", "Solo si tienes permiso y entiendes la politica de datos de la herramienta. Para dudas sensibles, usa versiones anonimizadas."),
            ("Vale la pena pagar por un chatbot de IA?", "Vale la pena si reduce tiempo, errores o pasos repetidos de forma constante. Si solo lo usas ocasionalmente, primero mide el ahorro real."),
        ],
    },
    "temas.html": {
        "title": "Temas de tecnologia",
        "description": "Mapa de temas de Pulso Tech Diario para leer sobre inteligencia artificial, ciberseguridad, chips y guias practicas.",
        "body": f"""
<p>Usa este mapa para entrar por tema y encontrar lecturas recurrentes de Pulso Tech Diario.</p>
<p><a href="blogger-archivo.html">Ver archivo de entradas reales de Blogger</a></p>
<h2>Inteligencia artificial</h2>
<p>Noticias, guias y senales sobre IA, productividad, modelos, agentes y uso responsable.</p>
<p><a href="inteligencia-artificial.html">Ver hub de inteligencia artificial</a> &middot; <a href="glosario-ia-tecnologia.html">Glosario</a> &middot; <a href="chatgpt-gemini-claude.html">ChatGPT vs Gemini vs Claude</a> &middot; <a href="que-es-ia-local.html">IA local</a> &middot; <a href="privacidad-chatbots-ia.html">Privacidad con chatbots</a> &middot; <a href="{BLOGGER_LABEL_IA_TRACKED}">Entradas en Blogger</a></p>
<h2>Ciberseguridad</h2>
<p>Riesgos, phishing, privacidad, cuentas y decisiones practicas para usuarios y equipos.</p>
<p><a href="ciberseguridad.html">Ver hub de ciberseguridad</a> &middot; <a href="checklist-phishing.html">Checklist anti phishing</a> &middot; <a href="{BLOGGER_LABEL_CYBER_TRACKED}">Entradas en Blogger</a></p>
<h2>Chips y hardware</h2>
<p>GPU, NPU, laptops, IA local y senales de la carrera por computo.</p>
<p><a href="chips-hardware.html">Ver hub de chips y hardware</a> &middot; <a href="npu-vs-gpu.html">NPU vs GPU</a> &middot; <a href="{BLOGGER_LABEL_CHIPS_TRACKED}">Entradas en Blogger</a></p>
""",
    },
    "inteligencia-artificial.html": {
        "title": "Inteligencia artificial: guias y noticias",
        "description": "Hub de Pulso Tech Diario para leer sobre IA, productividad, privacidad, herramientas y noticias diarias.",
        "body": f"""
<p>La inteligencia artificial cambia software, trabajo, privacidad y hardware. Este hub agrupa rutas para leer sin perderse en el ruido.</p>
<h2>Guias recomendadas</h2>
<ul>
  <li><a href="{BLOGGER_LABEL_IA_TRACKED}">Entradas de IA en Blogger</a></li>
  <li><a href="{BLOGGER_START_TRACKED}">Empieza aqui en Blogger</a></li>
  <li><a href="ia-en-el-trabajo.html">IA en el trabajo: donde si ahorra tiempo</a></li>
  <li><a href="glosario-ia-tecnologia.html">Glosario rapido de IA y tecnologia</a></li>
  <li><a href="chatgpt-gemini-claude.html">ChatGPT, Gemini o Claude: como elegir</a></li>
  <li><a href="que-es-ia-local.html">Que es la IA local</a></li>
  <li><a href="privacidad-chatbots-ia.html">Privacidad con chatbots de IA</a></li>
  <li><a href="{BLOGGER_LABEL_PRIVACY_TRACKED}">Privacidad e IA</a></li>
</ul>
<h2>Que mirar</h2>
<p>Busca senales de impacto real: tareas que se vuelven mas rapidas, productos que cambian comportamiento, riesgos de datos y costos de computo.</p>
<p><a href="{BLOGGER_RSS_URL}">Seguir por RSS</a> · <a href="share-pack.html">Compartir Pulso Tech Diario</a></p>
""",
    },
    "ciberseguridad.html": {
        "title": "Ciberseguridad: phishing, privacidad y cuentas",
        "description": "Hub de Pulso Tech Diario para leer sobre phishing, privacidad, filtraciones y seguridad digital practica.",
        "body": f"""
<p>La ciberseguridad afecta cuentas, datos personales, empresas y servicios cotidianos. Este hub prioriza acciones simples y senales faciles de vigilar.</p>
<h2>Lecturas recomendadas</h2>
<ul>
  <li><a href="{BLOGGER_LABEL_CYBER_TRACKED}">Entradas de ciberseguridad en Blogger</a></li>
  <li><a href="glosario-ia-tecnologia.html">Glosario de terminos clave</a></li>
  <li><a href="{BLOGGER_LABEL_PHISHING_TRACKED}">Guias sobre phishing</a></li>
  <li><a href="checklist-phishing.html">Checklist anti phishing</a></li>
  <li><a href="{BLOGGER_LABEL_PRIVACY_TRACKED}">Privacidad y datos</a></li>
  <li><a href="{BLOGGER_START_TRACKED}">Empieza aqui en Blogger</a></li>
</ul>
<h2>Que mirar</h2>
<p>Prioriza cambios de contrasenas, verificacion en dos pasos, sesiones activas, enlaces sospechosos y datos que no deberian compartirse con herramientas externas.</p>
<p><a href="{BLOGGER_RSS_URL}">Seguir por RSS</a> · <a href="share-pack.html">Compartir Pulso Tech Diario</a></p>
""",
    },
    "chips-hardware.html": {
        "title": "Chips y hardware para IA",
        "description": "Hub de Pulso Tech Diario sobre GPU, NPU, laptops, IA local, chips y computo para inteligencia artificial.",
        "body": f"""
<p>Los chips determinan que tan rapido crecen la IA, la nube, las laptops y los dispositivos personales. Este hub junta guias y rutas de lectura.</p>
<h2>Lecturas recomendadas</h2>
<ul>
  <li><a href="{BLOGGER_LABEL_CHIPS_TRACKED}">Entradas de chips en Blogger</a></li>
  <li><a href="glosario-ia-tecnologia.html">Glosario de IA, chips y seguridad</a></li>
  <li><a href="{BLOGGER_LABEL_LOCAL_AI_TRACKED}">IA local</a></li>
  <li><a href="comprar-laptop-para-ia.html">Que revisar antes de comprar una laptop para IA</a></li>
  <li><a href="npu-vs-gpu.html">NPU vs GPU para IA</a></li>
  <li><a href="{BLOGGER_START_TRACKED}">Empieza aqui en Blogger</a></li>
</ul>
<h2>Que mirar</h2>
<p>No basta con una sigla. Revisa memoria, eficiencia, software compatible, disponibilidad, bateria y si la aplicacion que usas aprovecha realmente el hardware.</p>
<p><a href="{BLOGGER_RSS_URL}">Seguir por RSS</a> · <a href="share-pack.html">Compartir Pulso Tech Diario</a></p>
""",
    },
}

SOURCES = [
    ("The Verge", "https://www.theverge.com/rss/index.xml"),
    ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/index"),
    ("TechCrunch", "https://techcrunch.com/feed/"),
    ("MIT Technology Review", "https://www.technologyreview.com/feed/"),
    ("Wired", "https://www.wired.com/feed/rss"),
    ("VentureBeat", "https://venturebeat.com/feed/"),
    ("Hacker News", "https://hnrss.org/frontpage"),
]

KEYWORDS = {
    "inteligencia artificial": [
        "ai",
        "artificial intelligence",
        "openai",
        "anthropic",
        "gemini",
        "llm",
        "model",
        "agents",
        "robot",
    ],
    "chips": ["chip", "semiconductor", "nvidia", "amd", "intel", "gpu", "tsmc", "arm"],
    "ciberseguridad": ["security", "hack", "breach", "malware", "privacy", "encryption", "vulnerability"],
    "startups": ["startup", "funding", "venture", "ipo", "acquisition", "raises"],
    "consumo": ["iphone", "android", "windows", "apple", "google", "samsung", "device", "app"],
    "web y plataformas": ["social", "platform", "creator", "search", "browser", "web", "cloud"],
    "ciencia": ["space", "climate", "quantum", "battery", "energy", "science", "health"],
}

SOURCE_WEIGHT = {
    "MIT Technology Review": 8,
    "Ars Technica": 7,
    "The Verge": 6,
    "Wired": 6,
    "TechCrunch": 5,
    "VentureBeat": 4,
    "Hacker News": 3,
}


@dataclass(frozen=True)
class Item:
    title: str
    link: str
    source: str
    summary: str
    published: datetime
    category: str
    score: int


def clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def fetch(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "PulsoTechDiario/1.0 (+https://github.com/elianguitarra/pulso-tech-diario)",
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
        },
    )
    with urllib.request.urlopen(request, timeout=18) as response:
        return response.read()


def parse_date(value: str) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    try:
        parsed = email.utils.parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return datetime.now(timezone.utc)


def find_child_text(node: ET.Element, names: Iterable[str]) -> str:
    for name in names:
        found = node.find(name)
        if found is not None and found.text:
            return found.text
    for child in node:
        local_name = child.tag.rsplit("}", 1)[-1].lower()
        if local_name in names and child.text:
            return child.text
    return ""


def detect_category(title: str, summary: str) -> tuple[str, int]:
    haystack = f"{title} {summary}".lower()
    best_category = "tecnologia"
    best_score = 0
    for category, keywords in KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in haystack)
        if score > best_score:
            best_category = category
            best_score = score
    return best_category, best_score


def score_item(source: str, title: str, summary: str, published: datetime, category_score: int) -> int:
    age_hours = max(0.0, (datetime.now(timezone.utc) - published).total_seconds() / 3600)
    freshness = max(0, 24 - int(age_hours / 2))
    signal_terms = ["launch", "release", "breakthrough", "lawsuit", "ban", "deal", "report", "new", "first"]
    signal = sum(2 for term in signal_terms if term in f"{title} {summary}".lower())
    return SOURCE_WEIGHT.get(source, 3) + freshness + category_score * 5 + signal


def parse_feed(source: str, payload: bytes) -> list[Item]:
    root = ET.fromstring(payload)
    entries = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
    items: list[Item] = []
    for entry in entries[:20]:
        title = clean_text(find_child_text(entry, ["title"]))
        link = clean_text(find_child_text(entry, ["link"]))
        if not link:
            link_node = entry.find("{http://www.w3.org/2005/Atom}link")
            link = link_node.attrib.get("href", "") if link_node is not None else ""
        summary = clean_text(find_child_text(entry, ["description", "summary", "content"]))
        published_raw = find_child_text(entry, ["pubDate", "published", "updated"])
        published = parse_date(published_raw)
        if not title or not link:
            continue
        category, category_score = detect_category(title, summary)
        score = score_item(source, title, summary, published, category_score)
        items.append(
            Item(
                title=title,
                link=link,
                source=source,
                summary=summary[:260],
                published=published,
                category=category,
                score=score,
            )
        )
    return items


def collect_items() -> list[Item]:
    collected: list[Item] = []
    for source, url in SOURCES:
        try:
            collected.extend(parse_feed(source, fetch(url)))
        except (urllib.error.URLError, ET.ParseError, TimeoutError, OSError) as exc:
            print(f"warning: could not read {source}: {exc}")
    deduped: dict[str, Item] = {}
    for item in collected:
        key = re.sub(r"[^a-z0-9]+", "", item.title.lower())[:90]
        if key not in deduped or item.score > deduped[key].score:
            deduped[key] = item
    return sorted(deduped.values(), key=lambda item: (item.score, item.published), reverse=True)[:12]


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")[:70] or "noticia"


def image_filename(item: Item, ordinal: int) -> str:
    return f"{ordinal:02d}-{slugify(display_title(item))}.svg"


def story_filename(item: Item, ordinal: int) -> str:
    return f"noticias/{ordinal:02d}-{slugify(display_title(item))}.html"


def palette_for(category: str) -> tuple[str, str, str, str]:
    palettes = {
        "inteligencia artificial": ("#0b1220", "#2dd4bf", "#facc15", "#e0f2fe"),
        "chips": ("#171717", "#fb7185", "#38bdf8", "#f5f5f4"),
        "ciberseguridad": ("#111827", "#a3e635", "#f97316", "#ecfccb"),
        "startups": ("#1f2937", "#f59e0b", "#22c55e", "#fff7ed"),
        "consumo": ("#172554", "#f472b6", "#60a5fa", "#eff6ff"),
        "web y plataformas": ("#164e63", "#c084fc", "#fbbf24", "#ecfeff"),
        "ciencia": ("#14532d", "#67e8f9", "#fde047", "#f0fdf4"),
        "tecnologia": ("#1e293b", "#14b8a6", "#f97316", "#f8fafc"),
    }
    return palettes.get(category, palettes["tecnologia"])


IMAGE_LABELS = {
    "inteligencia artificial": ["IA EN ACCION", "NUEVA SENAL IA", "SOFTWARE EN CAMBIO"],
    "chips": ["PODER DE COMPUTO", "NUEVA OLA CHIP", "PIEZA CLAVE"],
    "ciberseguridad": ["ALERTA DIGITAL", "DATOS EN RIESGO", "DEFENSA ACTIVA"],
    "startups": ["CAPITAL TEC", "NUEVA APUESTA", "MERCADO EMERGENTE"],
    "consumo": ["PRODUCTOS DIGITALES", "CAMBIO DE USO", "TECNOLOGIA DIARIA"],
    "web y plataformas": ["MAPA DIGITAL", "PLATAFORMAS", "WEB EN CAMBIO"],
    "ciencia": ["CIENCIA APLICADA", "NUEVA FRONTERA", "SENAL CIENTIFICA"],
    "tecnologia": ["PULSO TEC", "SENAL CLAVE", "INDUSTRIA DIGITAL"],
}


def image_label_for(category: str, index: int) -> str:
    labels = IMAGE_LABELS.get(category, IMAGE_LABELS["tecnologia"])
    return labels[index % len(labels)]


def svg_for_item(item: Item, index: int) -> str:
    bg, primary, secondary, paper = palette_for(item.category)
    label = image_label_for(item.category, index)
    seed = sum(ord(ch) for ch in item.title) + index * 31

    def micro_grid() -> str:
        lines = []
        for n in range(18):
            x = 60 + ((seed + n * 67) % 1080)
            y = 52 + ((seed * 3 + n * 41) % 500)
            lines.append(
                f'<path d="M{x} {y} h{36 + (n % 4) * 22} v{18 + (n % 3) * 16}" '
                f'fill="none" stroke="{paper}" stroke-width="2" opacity="0.16"/>'
            )
            lines.append(f'<circle cx="{x}" cy="{y}" r="{3 + n % 3}" fill="{secondary}" opacity="0.55"/>')
        return "".join(lines)

    def chip_visual() -> str:
        pins = []
        for n in range(12):
            pins.append(f'<rect x="{365 + n * 38}" y="156" width="14" height="52" rx="5" fill="{primary}" opacity="0.86"/>')
            pins.append(f'<rect x="{365 + n * 38}" y="422" width="14" height="52" rx="5" fill="{primary}" opacity="0.50"/>')
        return f"""
  <g transform="translate(250 95)">
    <rect x="110" y="85" width="500" height="360" rx="42" fill="{paper}" opacity="0.95"/>
    <rect x="166" y="138" width="388" height="254" rx="28" fill="{bg}" opacity="0.92"/>
    {''.join(pins)}
    <path d="M232 276 C276 194 360 180 418 238 C498 220 540 290 502 354 C452 428 304 416 252 344 C226 324 220 300 232 276 Z" fill="{primary}"/>
    <circle cx="310" cy="278" r="18" fill="{secondary}"/>
    <circle cx="430" cy="278" r="18" fill="{secondary}"/>
    <path d="M314 334 C354 362 406 362 446 334" fill="none" stroke="{paper}" stroke-width="14" stroke-linecap="round"/>
  </g>"""

    def orbit_visual() -> str:
        arcs = []
        for n in range(5):
            arcs.append(
                f'<ellipse cx="720" cy="288" rx="{170 + n * 38}" ry="{58 + n * 21}" '
                f'fill="none" stroke="{primary if n % 2 else secondary}" stroke-width="{5 if n < 2 else 3}" '
                f'opacity="{0.72 - n * 0.10}" transform="rotate({-28 + n * 15} 720 288)"/>'
            )
        return f"""
  <g>
    <circle cx="720" cy="288" r="118" fill="{primary}" opacity="0.92"/>
    <circle cx="720" cy="288" r="62" fill="{bg}" opacity="0.35"/>
    {''.join(arcs)}
    <circle cx="905" cy="226" r="22" fill="{secondary}"/>
    <circle cx="532" cy="365" r="15" fill="{paper}" opacity="0.88"/>
    <path d="M170 470 C330 385 430 492 570 410 C710 328 846 448 1040 332" fill="none" stroke="{paper}" stroke-width="12" opacity="0.28"/>
  </g>"""

    def security_visual() -> str:
        locks = []
        for n in range(5):
            x = 250 + n * 132
            y = 150 + (n % 2) * 120
            locks.append(
                f'<rect x="{x}" y="{y + 42}" width="82" height="68" rx="14" fill="{paper}" opacity="0.92"/>'
                f'<path d="M{x + 18} {y + 48} v-22 c0-48 46-48 46 0 v22" fill="none" stroke="{secondary}" stroke-width="12" stroke-linecap="round"/>'
            )
        return f"""
  <g>
    <path d="M660 90 L950 196 V330 C950 462 842 540 660 586 C478 540 370 462 370 330 V196 Z" fill="{primary}" opacity="0.90"/>
    <path d="M660 154 L872 232 V330 C872 420 790 480 660 518 C530 480 448 420 448 330 V232 Z" fill="{bg}" opacity="0.44"/>
    <path d="M590 324 L642 376 L744 260" fill="none" stroke="{secondary}" stroke-width="26" stroke-linecap="round" stroke-linejoin="round"/>
    {''.join(locks)}
  </g>"""

    def city_visual() -> str:
        buildings = []
        for n in range(11):
            x = 420 + n * 58
            h = 150 + ((seed + n * 29) % 210)
            buildings.append(f'<rect x="{x}" y="{482 - h}" width="42" height="{h}" fill="{paper}" opacity="{0.50 + (n % 3) * 0.12}"/>')
            for w in range(3):
                buildings.append(f'<rect x="{x + 9}" y="{492 - h + w * 38}" width="8" height="18" fill="{secondary}" opacity="0.70"/>')
        return f"""
  <g>
    <path d="M0 500 H1200 V630 H0 Z" fill="{primary}" opacity="0.35"/>
    {''.join(buildings)}
    <path d="M90 438 C270 382 360 492 530 410 C690 332 784 420 1038 296" fill="none" stroke="{secondary}" stroke-width="18" opacity="0.70"/>
    <circle cx="1010" cy="282" r="46" fill="{secondary}" opacity="0.92"/>
  </g>"""

    def product_visual() -> str:
        cards = []
        for n in range(4):
            x = 560 + (n % 2) * 230
            y = 110 + (n // 2) * 170
            cards.append(
                f'<rect x="{x}" y="{y}" width="190" height="126" rx="24" fill="{paper}" opacity="{0.92 - n * 0.08}"/>'
                f'<rect x="{x + 24}" y="{y + 26}" width="96" height="12" rx="6" fill="{primary}"/>'
                f'<rect x="{x + 24}" y="{y + 58}" width="132" height="10" rx="5" fill="{bg}" opacity="0.28"/>'
                f'<circle cx="{x + 146}" cy="{y + 86}" r="22" fill="{secondary}"/>'
            )
        return f"""
  <g>
    <rect x="140" y="120" width="330" height="390" rx="42" fill="{paper}" opacity="0.95"/>
    <rect x="175" y="176" width="260" height="270" rx="26" fill="{bg}" opacity="0.88"/>
    <path d="M220 314 h172 M220 362 h116" stroke="{primary}" stroke-width="18" stroke-linecap="round"/>
    <circle cx="305" cy="232" r="42" fill="{secondary}"/>
    {''.join(cards)}
  </g>"""

    def startup_visual() -> str:
        bars = []
        for n in range(7):
            h = 42 + ((seed + n * 43) % 210)
            bars.append(f'<rect x="{170 + n * 70}" y="{505 - h}" width="42" height="{h}" rx="16" fill="{primary if n % 2 else secondary}" opacity="0.82"/>')
        return f"""
  <g>
    <path d="M770 104 C842 132 906 202 926 282 C826 304 740 380 684 492 C620 404 560 330 462 292 C514 198 610 126 770 104 Z" fill="{primary}" opacity="0.95"/>
    <circle cx="742" cy="254" r="54" fill="{paper}" opacity="0.92"/>
    <path d="M654 494 C604 538 542 552 470 560 C478 488 492 426 536 376" fill="{secondary}" opacity="0.72"/>
    <path d="M808 414 C876 454 930 508 978 582" stroke="{secondary}" stroke-width="18" stroke-linecap="round"/>
    {''.join(bars)}
  </g>"""

    templates = {
        "chips": chip_visual,
        "inteligencia artificial": product_visual,
        "ciberseguridad": security_visual,
        "web y plataformas": city_visual,
        "startups": startup_visual,
        "ciencia": orbit_visual,
        "consumo": product_visual,
        "tecnologia": orbit_visual,
    }
    fallback_variants = [chip_visual, orbit_visual, security_visual, city_visual, product_visual, startup_visual]
    visual = templates.get(item.category, fallback_variants[index % len(fallback_variants)])
    if item.category in {"tecnologia", "inteligencia artificial", "consumo"}:
        visual = fallback_variants[(index + seed) % len(fallback_variants)]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630" role="img" aria-label="{html.escape(item.category)}">
  <defs>
    <radialGradient id="halo{index}" cx="70%" cy="28%" r="62%">
      <stop offset="0" stop-color="{secondary}" stop-opacity="0.58"/>
      <stop offset="0.55" stop-color="{primary}" stop-opacity="0.16"/>
      <stop offset="1" stop-color="{bg}" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="1200" height="630" fill="{bg}"/>
  <rect width="1200" height="630" fill="url(#halo{index})"/>
  <path d="M0 504 C210 410 336 548 536 456 C750 358 880 318 1200 360 L1200 630 L0 630 Z" fill="{primary}" opacity="0.23"/>
  {micro_grid()}
  {visual()}
  <rect x="58" y="54" width="1084" height="522" rx="0" fill="none" stroke="{paper}" stroke-width="3" opacity="0.22"/>
  <text x="84" y="504" fill="{paper}" font-family="Arial, Helvetica, sans-serif" font-size="48" font-weight="900">{html.escape(label[:28])}</text>
  <text x="84" y="558" fill="{paper}" font-family="Arial, Helvetica, sans-serif" font-size="26" font-weight="700" opacity="0.86">Pulso Tech Diario | {html.escape(item.category.title())}</text>
</svg>"""


def save_images(items: list[Item]) -> dict[str, str]:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    for old_image in ASSET_DIR.glob("*.svg"):
        old_image.unlink()
    image_paths = {}
    for index, item in enumerate(items):
        filename = image_filename(item, index + 1)
        path = ASSET_DIR / filename
        path.write_text(svg_for_item(item, index), encoding="utf-8")
        image_paths[item.link] = f"assets/images/{filename}"
    return image_paths


def reading_angle(item: Item) -> str:
    if item.category == "inteligencia artificial":
        return "Vigila el impacto en productividad, derechos de autor y nuevas interfaces de software."
    if item.category == "chips":
        return "Puede mover precios, disponibilidad de hardware y la velocidad de la siguiente ola de IA."
    if item.category == "ciberseguridad":
        return "Conviene revisar riesgos, datos expuestos y posibles acciones preventivas."
    if item.category == "startups":
        return "Senala donde los inversionistas creen que habra crecimiento durante los proximos meses."
    if item.category == "consumo":
        return "Afecta los productos, apps y servicios que millones de personas usan a diario."
    if item.category == "ciencia":
        return "Puede convertirse en infraestructura, energia o salud aplicada en el mediano plazo."
    return "Es una senal temprana de hacia donde se esta moviendo la industria tecnologica."


def esc(value: str) -> str:
    return html.escape(value, quote=True)


ENGLISH_MARKERS = {
    "the",
    "and",
    "with",
    "for",
    "from",
    "after",
    "before",
    "launches",
    "gets",
    "says",
    "new",
    "when",
    "how",
    "why",
    "what",
    "is",
    "are",
    "will",
    "can",
    "ai",
}

PHRASE_REPLACEMENTS = [
    ("artificial intelligence", "inteligencia artificial"),
    ("agentic ai", "IA agentica"),
    ("service disruption", "interrupcion del servicio"),
    ("data breach", "filtracion de datos"),
    ("held for ransom", "retenidos para exigir rescate"),
    ("all the news and trailers", "todas las noticias y avances"),
    ("release date", "fecha de lanzamiento"),
    ("isn't coming", "no llegara"),
    ("is still working", "sigue trabajando"),
    ("set free", "liberada"),
    ("superintelligence", "superinteligencia"),
    ("latest news", "ultimas noticias"),
    ("after recent delay", "tras un retraso reciente"),
    ("for the first time", "por primera vez"),
    ("explains how", "explica como"),
    ("worst breaches", "peores filtraciones"),
    ("so far", "hasta ahora"),
    ("restores access", "restablece el acceso"),
    ("after service disruption", "tras una interrupcion del servicio"),
    ("launches in", "se lanza en"),
    ("gets a", "recibe una"),
]

WORD_REPLACEMENTS = {
    "ai": "IA",
    "chief": "jefe",
    "company": "compania",
    "companies": "companias",
    "says": "dice",
    "said": "dijo",
    "new": "nuevo",
    "news": "noticias",
    "trailers": "avances",
    "showcase": "presentacion",
    "launch": "lanzamiento",
    "launches": "se lanza",
    "arrives": "llega",
    "delay": "retraso",
    "hacked": "hackeado",
    "leaked": "filtrado",
    "breaches": "filtraciones",
    "security": "seguridad",
    "access": "acceso",
    "restores": "restablece",
    "working": "trabajando",
    "superintelligence": "superinteligencia",
    "futurist": "futurista",
    "explains": "explica",
    "uses": "usa",
    "real": "real",
    "world": "mundo",
    "problem": "problema",
    "software": "software",
    "coding": "programacion",
    "solved": "resolvio",
    "exposed": "expuso",
    "every": "cada",
    "other": "otro",
    "gets": "recibe",
    "date": "fecha",
    "first": "primera",
    "time": "vez",
    "smart": "inteligente",
    "lamp": "lampara",
    "post": "poste",
    "under": "por debajo de",
    "coming": "llegando",
    "ps5": "PS5",
    "xbox": "Xbox",
    "microsoft": "Microsoft",
    "openai": "OpenAI",
    "notion": "Notion",
    "anthropic": "Anthropic",
}


def looks_english(value: str) -> bool:
    words = re.findall(r"[A-Za-z']+", value.lower())
    if not words:
        return False
    hits = sum(1 for word in words if word.strip("'") in ENGLISH_MARKERS)
    return hits >= 1 or any(word in {"ai", "xbox", "ps5", "gets", "arrives", "launches"} for word in words)


def spanishize_text(value: str) -> str:
    text = clean_text(value)
    if not text or not looks_english(text):
        return text
    text = text.replace("&#8220;", '"').replace("&#8221;", '"').replace("&#39;", "'")
    for source, target in PHRASE_REPLACEMENTS:
        text = re.sub(re.escape(source), target, text, flags=re.IGNORECASE)

    def repl(match: re.Match[str]) -> str:
        raw = match.group(0)
        translated = WORD_REPLACEMENTS.get(raw.lower())
        return translated if translated else raw

    text = re.sub(r"\b[A-Za-z][A-Za-z']*\b", repl, text)
    text = re.sub(r"\bthe\b", "el", text, flags=re.IGNORECASE)
    text = re.sub(r"\band\b", "y", text, flags=re.IGNORECASE)
    text = re.sub(r"\bfrom\b", "de", text, flags=re.IGNORECASE)
    text = re.sub(r"\bto\b", "a", text, flags=re.IGNORECASE)
    text = re.sub(r"\bfor\b", "para", text, flags=re.IGNORECASE)
    text = re.sub(r"\bafter\b", "despues de", text, flags=re.IGNORECASE)
    text = re.sub(r"\bwith\b", "con", text, flags=re.IGNORECASE)
    text = re.sub(r"\bof\b", "de", text, flags=re.IGNORECASE)
    text = re.sub(r"\bin\b", "en", text, flags=re.IGNORECASE)
    text = re.sub(r"\bis\b", "es", text, flags=re.IGNORECASE)
    text = re.sub(r"\bare\b", "son", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip(" -")
    return text[:1].upper() + text[1:]


EDITORIAL_TITLES = {
    "inteligencia artificial": [
        "IA: nuevas herramientas vuelven a mover el software",
        "IA: agentes y asistentes toman protagonismo esta semana",
        "IA: otra senal fuerte para productividad y plataformas",
        "IA: el mercado ajusta sus apuestas alrededor de los modelos",
        "IA: nuevas capacidades cambian la conversacion del dia",
        "IA: empresas y usuarios miran con mas atencion los agentes",
        "IA: productividad, datos y software vuelven al centro",
        "IA: la competencia por mejores asistentes se acelera",
        "IA: una nueva pista muestra hacia donde va el software",
        "IA: modelos y plataformas vuelven a marcar la agenda",
        "IA: el uso diario gana peso frente al anuncio llamativo",
        "IA: otra decision de la industria merece seguimiento",
    ],
    "ciberseguridad": [
        "Ciberseguridad: nuevas alertas elevan la presion sobre usuarios",
        "Ciberseguridad: datos, accesos y confianza vuelven al centro",
        "Ciberseguridad: una senal para revisar cuentas y defensas",
    ],
    "chips": [
        "Chips: otra pieza clave empuja la carrera por computo",
        "Chips: hardware y memoria vuelven a marcar la agenda de IA",
        "Chips: la infraestructura vuelve al centro de la tecnologia",
    ],
    "startups": [
        "Startups: el capital tecnologico apunta a nuevos productos",
        "Startups: una apuesta muestra hacia donde se mueve el mercado",
        "Startups: nuevas senales revelan oportunidades emergentes",
    ],
    "consumo": [
        "Consumo digital: productos y servicios vuelven a moverse",
        "Consumo digital: cambios de plataforma llegan al usuario final",
        "Consumo digital: nuevas funciones entran en el radar diario",
    ],
    "web y plataformas": [
        "Plataformas: la web prepara cambios para usuarios y creadores",
        "Plataformas: busqueda, servicios y creadores entran en movimiento",
        "Plataformas: una nueva senal anticipa cambios digitales",
    ],
    "ciencia": [
        "Ciencia y tecnologia: una nueva senal merece seguimiento",
        "Ciencia aplicada: avances que podrian cambiar infraestructura",
        "Ciencia y tecnologia: otra frontera entra en observacion",
    ],
    "tecnologia": [
        "Tecnologia: una senal importante para seguir esta semana",
        "Tecnologia: nuevos movimientos dibujan la agenda digital",
        "Tecnologia: otra pista ayuda a leer hacia donde va la industria",
    ],
}


def editorial_title(item: Item) -> str:
    titles = EDITORIAL_TITLES.get(item.category, EDITORIAL_TITLES["tecnologia"])
    seed = sum(ord(ch) for ch in f"{item.title}|{item.link}|{item.source}")
    return titles[seed % len(titles)]


def display_title(item: Item) -> str:
    raw = clean_text(item.title)
    # Las fuentes principales son angloparlantes; para el sitio publico preferimos
    # titulares editoriales propios en espanol antes que dejar pasar el titular RSS.
    source_is_foreign = item.source in {source for source, _url in SOURCES}
    if not source_is_foreign and not looks_english(raw):
        return raw
    return editorial_title(item)


def display_summary(item: Item) -> str:
    raw = clean_text(item.summary)
    if raw and not looks_english(raw):
        return raw
    source = item.source
    angle = reading_angle(item)
    if item.category == "inteligencia artificial":
        return f"{source} reporta un movimiento relevante en inteligencia artificial. La clave esta en entender si cambia productividad, software o la relacion entre usuarios y herramientas digitales. {angle}"
    if item.category == "ciberseguridad":
        return f"{source} apunta a un riesgo que conviene mirar con calma: datos, accesos y confianza digital vuelven al centro de la conversacion. {angle}"
    if item.category == "chips":
        return f"{source} senala otro paso en la carrera por computo, hardware y capacidad para ejecutar nuevas cargas de inteligencia artificial. {angle}"
    if item.category == "consumo":
        return f"{source} destaca una novedad que puede afectar productos, apps o servicios usados a diario. {angle}"
    if item.category == "web y plataformas":
        return f"{source} muestra una senal sobre plataformas, busqueda, creadores o servicios cloud. {angle}"
    if item.category == "startups":
        return f"{source} recoge una pista sobre inversion, adquisiciones o productos emergentes en tecnologia. {angle}"
    return f"{source} reporta una senal tecnologica relevante. {angle}"


def extract_entities(value: str) -> list[str]:
    ignore = {
        "The",
        "This",
        "That",
        "When",
        "How",
        "What",
        "Why",
        "Where",
        "Which",
        "After",
        "Before",
        "For",
        "With",
        "From",
        "Into",
        "Over",
        "Under",
        "All",
        "Every",
        "Other",
        "More",
        "Less",
        "New",
        "Latest",
        "First",
        "Last",
        "Next",
        "Show",
        "Hacked",
        "Leaked",
        "Changed",
        "Managing",
        "Production",
        "Problem",
        "Solved",
        "Explains",
        "Launches",
        "Arrives",
        "Gets",
        "Says",
        "Could",
        "Would",
        "Should",
        "Will",
        "Can",
        "AI",
        "Agentic",
        "Games",
        "Campaign",
        "Download",
        "Evolved",
        "Futurist",
        "September",
        "Showcase",
        "Trailer",
        "Trailers",
        "War",
        "World",
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "October",
        "November",
        "December",
        "Dungeons",
    }
    entities = []
    for match in re.findall(r"\b(?:[A-Z][A-Za-z0-9]+|[A-Z]{2,}|[A-Za-z]+(?:\d+))\b", value):
        if match not in ignore and match not in entities:
            entities.append(match)
    return entities


def render_index(items: list[Item], image_paths: dict[str, str], story_paths: dict[str, str]) -> str:
    now = datetime.now(timezone.utc)
    lead = items[0] if items else None
    cards = []
    for rank, item in enumerate(items, start=1):
        image_path = image_paths[item.link]
        story_path = story_paths[item.link]
        cards.append(
            f"""
        <article class="story" data-category="{esc(item.category)}">
          <a class="story-image" href="{esc(story_path)}">
            <img src="{esc(image_path)}" alt="{esc(display_title(item))}" loading="lazy" width="1200" height="630">
          </a>
          <div class="story-body">
            <div class="story-meta"><span>#{rank}</span><span>{esc(item.category)}</span><span>{esc(item.source)}</span></div>
            <h2><a href="{esc(story_path)}">{esc(display_title(item))}</a></h2>
            <p>{esc(display_summary(item))}</p>
            <p class="angle">{esc(reading_angle(item))}</p>
            <p><a href="{esc(item.link)}" target="_blank" rel="noopener">Fuente original</a></p>
          </div>
        </article>"""
        )
        if rank == 4:
            cards.append(ad_unit("in-grid", ADSENSE_IN_ARTICLE_SLOT, "anuncio en el resumen"))
    lead_image = image_paths[lead.link] if lead else "assets/social-card.svg"
    lead_title = display_title(lead) if lead else "Tecnologia diaria"
    evergreen_guides = [
        ("Noticias de tecnologia", "noticias-tecnologia-espanol.html", "Resumen diario en espanol para entender senales clave."),
        ("Tendencias tech hoy", "tendencias-tecnologia-hoy.html", "Lo mas relevante del dia en IA, chips y seguridad."),
        ("IA hoy", "inteligencia-artificial-hoy.html", "Modelos, agentes y herramientas que se mueven ahora."),
        ("Ciberseguridad hoy", "ciberseguridad-hoy.html", "Riesgos, phishing y privacidad explicados rapido."),
        ("Chips IA hoy", "chips-ia-hoy.html", "GPU, NPU y hardware para la carrera de IA."),
        ("Glosario tech rapido", "glosario-ia-tecnologia.html", "IA, chips y seguridad explicados sin vueltas."),
        ("Herramientas IA gratis", "herramientas-ia-gratis.html", "Como elegir herramientas gratuitas sin perder tiempo."),
        ("ChatGPT, Gemini o Claude", "chatgpt-gemini-claude.html", "Como elegir un chatbot de IA segun tu tarea."),
        ("IA para estudiantes", "ia-para-estudiantes.html", "Usos utiles para estudiar sin copiar ni exponer datos."),
        ("Proteger cuenta Google", "proteger-cuenta-google.html", "Checklist de seguridad para una cuenta clave."),
        ("Que es la IA local", "que-es-ia-local.html", "Modelos en tu dispositivo, privacidad y limites reales."),
        ("NPU vs GPU para IA", "npu-vs-gpu.html", "Diferencias practicas antes de comprar hardware."),
        ("Privacidad con chatbots", "privacidad-chatbots-ia.html", "Datos que conviene no subir a herramientas de IA."),
        ("Checklist anti phishing", "checklist-phishing.html", "Una revision rapida antes de hacer clic."),
    ]
    guide_cards = "\n".join(
        f"""        <a class="guide-card" href="{esc(url)}">
          <span>{index:02d}</span>
          <strong>{esc(title)}</strong>
          <em>{esc(description)}</em>
        </a>"""
        for index, (title, url, description) in enumerate(evergreen_guides, start=1)
    )
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{SITE_NAME} | Tecnologia relevante cada dia</title>
  <meta name="description" content="{esc(SITE_DESCRIPTION)}">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <link rel="canonical" href="{SITE_URL}/">
  <link rel="alternate" type="application/rss+xml" title="{SITE_NAME}" href="{SITE_URL}/feed.xml">
  <link rel="alternate" type="application/atom+xml" title="{SITE_NAME}" href="{SITE_URL}/atom.xml">
  <link rel="alternate" type="application/feed+json" title="{SITE_NAME}" href="{SITE_URL}/feed.json">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{SITE_NAME}">
  <meta property="og:description" content="{esc(lead_title)}">
  <meta property="og:image" content="{SITE_URL}/{esc(lead_image)}">
  <meta property="og:url" content="{SITE_URL}/">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{SITE_NAME}">
  <meta name="twitter:description" content="{esc(lead_title)}">
  <meta name="twitter:image" content="{SITE_URL}/{esc(lead_image)}">
  {adsense_head()}
  <link rel="stylesheet" href="style.css">
  <script type="application/ld+json">{json.dumps(schema(items, story_paths), ensure_ascii=False)}</script>
</head>
<body>
  <header class="topbar">
    <a class="brand" href="./" aria-label="{SITE_NAME}">
      <span class="brand-mark">PT</span>
      <span>{SITE_NAME}</span>
    </a>
    <nav aria-label="Acciones">
      <a href="noticias-tecnologia-espanol.html">Noticias</a>
      <a href="tendencias-tecnologia-hoy.html">Tendencias</a>
      <a href="links.html">Links</a>
      <a href="seguir.html">Seguir</a>
      <a href="feed.xml">RSS</a>
      <a href="temas.html">Temas</a>
      <a href="share-pack.html">Compartir</a>
      <a href="acerca.html">Acerca</a>
      <a href="privacidad.html">Privacidad</a>
      <a href="https://twitter.com/intent/tweet?text={urllib.parse.quote(SITE_NAME)}&url={urllib.parse.quote(SITE_URL + '/')}" target="_blank" rel="noopener">Compartir</a>
    </nav>
  </header>

  <main>
    <section class="hero">
      <div class="hero-copy">
        <p class="kicker">Actualizado automaticamente: {now.strftime("%Y-%m-%d %H:%M UTC")}</p>
        <h1>Tecnologia importante, filtrada a diario.</h1>
        <p>{SITE_DESCRIPTION}</p>
      </div>
      <div class="hero-panel">
        <span>Nota lider</span>
        <strong>{esc(lead_title)}</strong>
      </div>
    </section>

    <section class="ticker" aria-label="Temas destacados">
      <span>IA</span><span>Chips</span><span>Ciberseguridad</span><span>Startups</span><span>Consumo</span><span>Ciencia</span>
    </section>

    <section class="blogger-cta" aria-label="Leer el blog principal">
      <div>
        <p class="kicker">Blog principal</p>
        <h2>Lee la version completa en Blogger</h2>
        <p>Blogger es la casa principal de Pulso Tech Diario: ahi estan las entradas, etiquetas, guias y el flujo preparado para AdSense.</p>
      </div>
      <div class="cta-actions">
        <a href="{BLOG_HOME_TRACKED}" target="_blank" rel="noopener">Abrir Blogger</a>
        <a href="ultima-entrada.html">Ultima entrada</a>
        <a href="tendencias-tecnologia-hoy.html">Tendencias hoy</a>
        <a href="inteligencia-artificial-hoy.html">IA hoy</a>
        <a href="ciberseguridad-hoy.html">Seguridad hoy</a>
        <a href="chips-ia-hoy.html">Chips IA</a>
        <a href="noticias-tecnologia-espanol.html">Noticias en espanol</a>
        <a href="links.html">Link en bio</a>
        <a href="seguir.html">Seguir</a>
        <a href="{BLOGGER_START_TRACKED}" target="_blank" rel="noopener">Empieza aqui</a>
        <a href="blogger-archivo.html">Archivo</a>
        <a href="temas.html">Temas</a>
        <a href="{BLOGGER_RSS_URL}" target="_blank" rel="noopener">RSS Blogger</a>
        <a href="share-pack.html">Compartir</a>
      </div>
    </section>

    <section class="guide-strip" aria-label="Guias populares">
      <div class="section-heading">
        <p class="kicker">Guias populares</p>
        <h2>Lecturas utiles que siguen trayendo busquedas</h2>
      </div>
      <div class="guide-grid">
{guide_cards}
      </div>
    </section>

    {ad_unit("leaderboard", ADSENSE_TOP_SLOT, "anuncio principal")}

    <section class="grid" aria-label="Resumen diario">
      {''.join(cards)}
    </section>
  </main>

  <footer>
    <p>Creado para publicarse gratis con GitHub Pages. Las imagenes son SVG originales generadas por el build diario.</p>
    <p>Fuentes: {", ".join(esc(name) for name, _ in SOURCES)}.</p>
    <p><a href="temas.html">Temas</a> · <a href="share-pack.html">Compartir</a> · <a href="acerca.html">Acerca de</a> · <a href="politica-editorial.html">Politica editorial</a> · <a href="privacidad.html">Privacidad</a> · <a href="contacto.html">Contacto</a></p>
  </footer>
</body>
</html>"""


def render_static_page(filename: str, page: dict[str, str]) -> str:
    title = page["title"]
    description = page["description"]
    body = page["body"]
    faq = page.get("faq", [])
    canonical = f"{SITE_URL}/{filename}"
    social_image = f"{SITE_URL}/assets/brand/pulso-tech-avatar.png"
    page_schema = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": title,
        "description": description,
        "url": canonical,
        "isPartOf": {
            "@type": "WebSite",
            "name": SITE_NAME,
            "url": SITE_URL,
        },
        "publisher": {
            "@type": "Organization",
            "name": SITE_NAME,
            "url": SITE_URL,
            "logo": social_image,
        },
    }
    schemas: list[dict] = [page_schema]
    if faq:
        schemas.append(
            {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": question,
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": answer,
                        },
                    }
                    for question, answer in faq
                ],
            }
        )
    schema_payload: dict | list[dict] = schemas[0] if len(schemas) == 1 else schemas
    faq_html = ""
    if faq:
        faq_items = "\n".join(
            f"""<details>
        <summary>{esc(question)}</summary>
        <p>{esc(answer)}</p>
      </details>"""
            for question, answer in faq
        )
        faq_html = f"""
    <section class="faq-block" aria-label="Preguntas frecuentes">
      <h2>Preguntas frecuentes</h2>
      {faq_items}
    </section>"""
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)} | {SITE_NAME}</title>
  <meta name="description" content="{esc(description)}">
  <meta name="robots" content="index,follow">
  <link rel="canonical" href="{canonical}">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="{SITE_NAME}">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="{social_image}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(title)}">
  <meta name="twitter:description" content="{esc(description)}">
  <meta name="twitter:image" content="{social_image}">
  {adsense_head()}
  <link rel="stylesheet" href="style.css">
  <script type="application/ld+json">{json.dumps(schema_payload, ensure_ascii=False)}</script>
</head>
<body>
  <header class="topbar">
    <a class="brand" href="./" aria-label="{SITE_NAME}">
      <span class="brand-mark">PT</span>
      <span>{SITE_NAME}</span>
    </a>
    <nav aria-label="Secciones">
      <a href="./">Inicio</a>
      <a href="noticias-tecnologia-espanol.html">Noticias</a>
      <a href="temas.html">Temas</a>
      <a href="feed.xml">RSS</a>
      <a href="contacto.html">Contacto</a>
    </nav>
  </header>
  <main class="page">
    <p class="kicker">Informacion del sitio</p>
    <h1>{esc(title)}</h1>
    <div class="page-body">
      {body}
    </div>
    {faq_html}
  </main>
  <footer>
    <p><a href="temas.html">Temas</a> · <a href="share-pack.html">Compartir</a> · <a href="acerca.html">Acerca de</a> · <a href="politica-editorial.html">Politica editorial</a> · <a href="privacidad.html">Privacidad</a> · <a href="contacto.html">Contacto</a></p>
  </footer>
</body>
</html>"""


def render_story_page(item: Item, ordinal: int, image_path: str, filename: str) -> str:
    title = display_title(item)
    summary = display_summary(item)
    canonical = f"{SITE_URL}/{filename}"
    image_url = f"{SITE_URL}/{image_path}"
    published = item.published.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    schema = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": title,
        "description": summary,
        "image": image_url,
        "datePublished": published,
        "dateModified": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "inLanguage": "es",
        "mainEntityOfPage": canonical,
        "publisher": {
            "@type": "Organization",
            "name": SITE_NAME,
            "url": SITE_URL,
            "logo": f"{SITE_URL}/assets/brand/pulso-tech-avatar.png",
        },
    }
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)} | {SITE_NAME}</title>
  <meta name="description" content="{esc(summary)}">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <link rel="canonical" href="{canonical}">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="{SITE_NAME}">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(summary)}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="{image_url}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(title)}">
  <meta name="twitter:description" content="{esc(summary)}">
  <meta name="twitter:image" content="{image_url}">
  {adsense_head()}
  <link rel="stylesheet" href="../style.css">
  <script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
</head>
<body>
  <header class="topbar">
    <a class="brand" href="../" aria-label="{SITE_NAME}">
      <span class="brand-mark">PT</span>
      <span>{SITE_NAME}</span>
    </a>
    <nav aria-label="Secciones">
      <a href="../">Inicio</a>
      <a href="../tendencias-tecnologia-hoy.html">Tendencias</a>
      <a href="../seguir.html">Seguir</a>
      <a href="../share-pack.html">Compartir</a>
    </nav>
  </header>
  <main class="page story-detail">
    <p class="kicker">#{ordinal} · {esc(item.category)} · {esc(item.source)}</p>
    <h1>{esc(title)}</h1>
    <p class="lede">{esc(summary)}</p>
    <img class="detail-image" src="../{esc(image_path)}" alt="{esc(title)}" width="1200" height="630">
    <div class="page-body">
      <h2>Por que importa</h2>
      <p>{esc(reading_angle(item))}</p>
      <h2>Lectura recomendada</h2>
      <p>Esta nota forma parte del resumen diario de Pulso Tech Diario. Primero te damos el contexto en espanol y despues enlazamos la fuente original para leer mas.</p>
      <p><a href="{BLOG_HOME_TRACKED}" target="_blank" rel="noopener">Abrir Pulso Tech Diario en Blogger</a> · <a href="{esc(item.link)}" target="_blank" rel="noopener">Leer fuente original</a></p>
      <p><a href="../tendencias-tecnologia-hoy.html">Ver mas tendencias de tecnologia</a> · <a href="../seguir.html">Seguir el sitio</a></p>
    </div>
  </main>
  <footer>
    <p><a href="../temas.html">Temas</a> · <a href="../feed.xml">RSS</a> · <a href="../contacto.html">Contacto</a></p>
  </footer>
</body>
</html>"""


def write_story_pages(items: list[Item], image_paths: dict[str, str]) -> dict[str, str]:
    story_dir = PUBLIC / "noticias"
    if story_dir.exists():
        for old_page in story_dir.glob("*.html"):
            old_page.unlink()
    story_dir.mkdir(parents=True, exist_ok=True)
    story_paths: dict[str, str] = {}
    for ordinal, item in enumerate(items, start=1):
        filename = story_filename(item, ordinal)
        (PUBLIC / filename).write_text(
            render_story_page(item, ordinal, image_paths[item.link], filename),
            encoding="utf-8",
        )
        story_paths[item.link] = filename
    return story_paths


def render_trends_page(
    items: list[Item],
    image_paths: dict[str, str],
    story_paths: dict[str, str],
    filename: str = "tendencias-tecnologia-hoy.html",
    title: str = "Tendencias de tecnologia hoy",
    description: str = "Tendencias de tecnologia hoy en espanol: IA, ciberseguridad, chips, plataformas y herramientas digitales resumidas rapido.",
    intro: str = "Resumen en espanol de las senales que se estan moviendo ahora en IA, chips, ciberseguridad, plataformas y herramientas digitales.",
    blogger_label_url: str = BLOG_HOME_TRACKED,
    category_filter: set[str] | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    canonical = f"{SITE_URL}/{filename}"
    filtered_items = [item for item in items if not category_filter or item.category in category_filter]
    if len(filtered_items) < 4 and category_filter:
        filtered_items = filtered_items + [item for item in items if item not in filtered_items]
    lead = filtered_items[0] if filtered_items else None
    lead_image = image_paths[lead.link] if lead else "assets/social-card.svg"
    lead_title = display_title(lead) if lead else title
    rows = []
    for rank, item in enumerate(filtered_items[:10], start=1):
        story_path = story_paths[item.link]
        rows.append(
            f"""
      <article class="trend-item">
        <a class="trend-image" href="{esc(story_path)}">
          <img src="{esc(image_paths[item.link])}" alt="{esc(display_title(item))}" loading="lazy" width="1200" height="630">
        </a>
        <div>
          <p class="story-meta"><span>#{rank}</span><span>{esc(item.category)}</span><span>{esc(item.source)}</span></p>
          <h2><a href="{esc(story_path)}">{esc(display_title(item))}</a></h2>
          <p>{esc(display_summary(item))}</p>
          <p class="angle">{esc(reading_angle(item))}</p>
          <p><a href="{esc(item.link)}" target="_blank" rel="noopener">Fuente original</a></p>
        </div>
      </article>"""
        )
    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": f"Que se resume en {title.lower()}?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "La pagina resume senales recientes seleccionadas automaticamente y enlaza a fuentes originales y rutas de lectura en Blogger.",
                },
            },
            {
                "@type": "Question",
                "name": "Cada cuanto se actualiza esta pagina?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Se actualiza automaticamente con el build diario de Pulso Tech Diario y enlaza a fuentes originales y al blog principal en Blogger.",
                },
            },
        ],
    }
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)} | {SITE_NAME}</title>
  <meta name="description" content="{esc(description)}">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <link rel="canonical" href="{canonical}">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(lead_title)}">
  <meta property="og:image" content="{SITE_URL}/{esc(lead_image)}">
  <meta property="og:url" content="{canonical}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(title)}">
  <meta name="twitter:description" content="{esc(lead_title)}">
  <meta name="twitter:image" content="{SITE_URL}/{esc(lead_image)}">
  {adsense_head()}
  <link rel="stylesheet" href="style.css">
  <script type="application/ld+json">{json.dumps(faq_schema, ensure_ascii=False)}</script>
</head>
<body>
  <header class="topbar">
    <a class="brand" href="./" aria-label="{SITE_NAME}">
      <span class="brand-mark">PT</span>
      <span>{SITE_NAME}</span>
    </a>
    <nav aria-label="Acciones">
      <a href="./">Inicio</a>
      <a href="ultima-entrada.html">Ultima entrada</a>
      <a href="links.html">Links</a>
      <a href="share-pack.html">Compartir</a>
      <a href="temas.html">Temas</a>
    </nav>
  </header>
  <main>
    <section class="hero trends-hero">
      <div class="hero-copy">
        <p class="kicker">Actualizado automaticamente: {now.strftime("%Y-%m-%d %H:%M UTC")}</p>
        <h1>{esc(title)}</h1>
        <p>{esc(intro)}</p>
      </div>
      <div class="hero-panel">
        <span>Senal principal</span>
        <strong>{esc(lead_title)}</strong>
      </div>
    </section>
    <section class="blogger-cta" aria-label="Leer en Blogger">
      <div>
        <p class="kicker">Ruta principal</p>
        <h2>Lee la entrada completa en Blogger</h2>
        <p>La version de Blogger concentra la entrada diaria, etiquetas y monetizacion con AdSense cuando este aprobada.</p>
      </div>
      <div class="cta-actions">
        <a href="ultima-entrada.html">Abrir ultima entrada</a>
        <a href="{blogger_label_url}" target="_blank" rel="noopener">Abrir Blogger</a>
        <a href="share-pack.html">Compartir</a>
      </div>
    </section>
    <section class="trend-list" aria-label="Tendencias de tecnologia">
      {''.join(rows)}
    </section>
  </main>
  <footer>
    <p>Fuentes: {", ".join(esc(name) for name, _ in SOURCES)}.</p>
    <p><a href="noticias-tecnologia-espanol.html">Noticias en espanol</a> · <a href="glosario-ia-tecnologia.html">Glosario</a> · <a href="privacidad.html">Privacidad</a></p>
  </footer>
</body>
</html>"""


def valid_adsense_client() -> bool:
    return bool(re.fullmatch(r"ca-pub-\d{16}", ADSENSE_CLIENT))


def adsense_publisher_id() -> str:
    return ADSENSE_CLIENT.replace("ca-", "", 1)


def adsense_head() -> str:
    if not valid_adsense_client():
        return ""
    client = esc(ADSENSE_CLIENT)
    return (
        f'<meta name="google-adsense-account" content="{client}">\n'
        f'  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={client}" '
        'crossorigin="anonymous"></script>'
    )


def ad_unit(kind: str, slot: str, label: str) -> str:
    if not valid_adsense_client() or not slot:
        return ""
    return f"""
    <aside class="ad ad-{esc(kind)}" aria-label="{esc(label)}">
      <ins class="adsbygoogle"
        style="display:block"
        data-ad-client="{esc(ADSENSE_CLIENT)}"
        data-ad-slot="{esc(slot)}"
        data-ad-format="auto"
        data-full-width-responsive="true"></ins>
      <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
    </aside>"""


def schema(items: list[Item], story_paths: dict[str, str]) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "NewsMediaOrganization",
        "name": SITE_NAME,
        "url": SITE_URL,
        "description": SITE_DESCRIPTION,
        "publishingPrinciples": f"{SITE_URL}/README.md",
        "mainEntityOfPage": {
            "@type": "ItemList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": index + 1,
                    "url": f"{SITE_URL}/{story_paths[item.link]}",
                    "name": display_title(item),
                }
                for index, item in enumerate(items)
            ],
        },
    }


def render_css() -> str:
    return """* { box-sizing: border-box; }
:root {
  color-scheme: light;
  --ink: #172033;
  --muted: #667085;
  --line: #d9e2ec;
  --paper: #fbfcf8;
  --accent: #0f766e;
  --hot: #e11d48;
  --sun: #f59e0b;
}
body {
  margin: 0;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: var(--paper);
  color: var(--ink);
}
a { color: inherit; text-decoration: none; }
a:hover { color: var(--accent); }
.topbar {
  min-height: 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 0 5vw;
  border-bottom: 1px solid var(--line);
  background: rgba(251, 252, 248, 0.92);
  position: sticky;
  top: 0;
  z-index: 10;
  backdrop-filter: blur(14px);
}
.brand { display: inline-flex; align-items: center; gap: 12px; font-weight: 800; }
.brand-mark {
  width: 42px;
  height: 42px;
  border-radius: 8px;
  display: inline-grid;
  place-items: center;
  color: white;
  background: #172033;
  font-weight: 900;
}
nav { display: flex; gap: 18px; color: var(--muted); font-weight: 700; font-size: 14px; }
main { width: min(1180px, 90vw); margin: 0 auto; }
.hero {
  min-height: 58vh;
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(280px, 0.8fr);
  gap: 42px;
  align-items: center;
  padding: 60px 0 42px;
}
.kicker {
  color: var(--accent);
  font-size: 14px;
  font-weight: 800;
  text-transform: uppercase;
}
h1 {
  margin: 0;
  font-size: clamp(42px, 8vw, 92px);
  line-height: 0.95;
  letter-spacing: 0;
  max-width: 850px;
}
.hero-copy > p:last-child {
  max-width: 680px;
  color: var(--muted);
  font-size: 20px;
  line-height: 1.55;
}
.hero-panel {
  min-height: 330px;
  padding: 34px;
  display: flex;
  flex-direction: column;
  justify-content: end;
  gap: 18px;
  border-left: 6px solid var(--hot);
  background:
    linear-gradient(135deg, rgba(15, 118, 110, 0.10), rgba(245, 158, 11, 0.18)),
    #eef6f2;
}
.hero-panel span { color: var(--hot); font-weight: 900; text-transform: uppercase; font-size: 13px; }
.hero-panel strong { font-size: 28px; line-height: 1.15; }
.ticker {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 28px;
  padding: 18px 0;
  border-block: 1px solid var(--line);
}
.ad {
  min-height: 110px;
  margin: 10px 0 28px;
  display: block;
  border-block: 1px solid var(--line);
  padding: 12px 0;
  overflow: hidden;
}
.ad-in-grid {
  grid-column: 1 / -1;
  margin: 0;
}
.ticker span {
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 10px 14px;
  background: white;
  color: #334155;
  font-weight: 800;
}
.blogger-cta {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 20px;
  align-items: center;
  margin: 0 0 30px;
  padding: 24px;
  border: 1px solid var(--line);
  background: #ffffff;
}
.blogger-cta h2 {
  margin: 0 0 8px;
  font-size: 30px;
  line-height: 1.05;
}
.blogger-cta p {
  margin: 0;
  color: #475569;
  line-height: 1.55;
}
.cta-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
  max-width: 360px;
}
.cta-actions a {
  display: inline-block;
  padding: 11px 13px;
  background: var(--ink);
  color: white;
  text-decoration: none;
  font-weight: 900;
  font-size: 13px;
}
.guide-strip {
  margin: 0 0 34px;
  padding: 26px 0 32px;
  border-block: 1px solid var(--line);
}
.section-heading {
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: 20px;
  margin-bottom: 18px;
}
.section-heading h2 {
  margin: 0;
  font-size: clamp(28px, 4vw, 44px);
  line-height: 1;
  max-width: 720px;
}
.guide-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 14px;
}
.guide-card {
  min-height: 178px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 18px;
  border: 1px solid var(--line);
  background: #ffffff;
}
.guide-card span {
  color: var(--hot);
  font-weight: 950;
  font-size: 13px;
}
.guide-card strong {
  color: var(--ink);
  font-size: 21px;
  line-height: 1.08;
}
.guide-card em {
  color: #475569;
  font-style: normal;
  line-height: 1.45;
}
.grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 22px; padding: 12px 0 64px; }
.story {
  background: white;
  border: 1px solid var(--line);
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 100%;
}
.story:first-child { grid-column: span 2; }
.story-image { display: block; aspect-ratio: 1200 / 630; background: #e2e8f0; overflow: hidden; }
.story-image img { width: 100%; height: 100%; object-fit: cover; display: block; transition: transform 0.2s ease; }
.story:hover img { transform: scale(1.025); }
.story-body { padding: 20px; display: flex; flex-direction: column; gap: 12px; }
.story-meta { display: flex; flex-wrap: wrap; gap: 8px; color: var(--muted); font-size: 12px; font-weight: 900; text-transform: uppercase; }
.story h2 { margin: 0; font-size: 22px; line-height: 1.16; letter-spacing: 0; }
.story p { margin: 0; color: #475569; line-height: 1.52; }
.story .angle {
  color: #123f3c;
  font-weight: 750;
  border-top: 1px solid var(--line);
  padding-top: 12px;
}
.trend-list {
  display: grid;
  gap: 18px;
  padding: 10px 0 64px;
}
.trend-item {
  display: grid;
  grid-template-columns: minmax(220px, 34%) 1fr;
  gap: 18px;
  align-items: stretch;
  background: #ffffff;
  border: 1px solid var(--line);
  border-radius: 8px;
  overflow: hidden;
}
.trend-image {
  min-height: 210px;
  background: #e2e8f0;
  overflow: hidden;
}
.trend-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.trend-item > div {
  padding: 20px 20px 20px 0;
  display: grid;
  gap: 12px;
}
.trend-item h2 {
  margin: 0;
  font-size: clamp(22px, 3vw, 34px);
  line-height: 1.05;
}
.trend-item h2 a { color: var(--ink); text-decoration: none; }
.trend-item p { margin: 0; color: #475569; line-height: 1.52; }
footer {
  border-top: 1px solid var(--line);
  padding: 28px 5vw 44px;
  color: var(--muted);
  font-size: 14px;
}
footer a { color: var(--ink); font-weight: 750; }
.page {
  min-height: 62vh;
  padding: 58px 0 72px;
  max-width: 780px;
}
.page h1 {
  font-size: clamp(40px, 7vw, 74px);
  line-height: 1;
  margin-bottom: 28px;
}
.lede {
  color: #475569;
  font-size: 21px;
  line-height: 1.58;
  margin: -12px 0 24px;
}
.detail-image {
  aspect-ratio: 1200 / 630;
  background: #0f172a;
  display: block;
  height: auto;
  margin: 0 0 30px;
  object-fit: cover;
  width: 100%;
}
.page-body {
  display: grid;
  gap: 18px;
  color: #334155;
  font-size: 19px;
  line-height: 1.7;
}
.page-body p { margin: 0; }
.page-body a {
  color: var(--accent);
  font-weight: 800;
  text-decoration: underline;
  text-underline-offset: 3px;
}
.faq-block {
  margin-top: 36px;
  border-top: 1px solid var(--line);
  padding-top: 22px;
}
.faq-block h2 { margin: 0 0 14px; font-size: 28px; }
.faq-block details {
  border-bottom: 1px solid var(--line);
  padding: 14px 0;
}
.faq-block summary {
  cursor: pointer;
  font-weight: 850;
  color: var(--ink);
}
.faq-block p {
  color: #475569;
  line-height: 1.65;
  margin: 10px 0 0;
}
@media (max-width: 920px) {
  .hero { grid-template-columns: 1fr; min-height: auto; }
  .blogger-cta { grid-template-columns: 1fr; }
  .cta-actions { justify-content: flex-start; max-width: none; }
  .guide-grid { grid-template-columns: repeat(2, 1fr); }
  .grid { grid-template-columns: 1fr 1fr; }
  .story:first-child { grid-column: span 2; }
  .trend-item { grid-template-columns: 1fr; }
  .trend-item > div { padding: 18px; }
  .trend-image { min-height: auto; aspect-ratio: 1200 / 630; }
}
@media (max-width: 640px) {
  .topbar { align-items: flex-start; flex-direction: column; padding-block: 14px; }
  main { width: min(100% - 28px, 1180px); }
  .hero { padding-top: 36px; gap: 24px; }
  .hero-panel { min-height: 230px; padding: 24px; }
  .section-heading { display: block; }
  .guide-grid { grid-template-columns: 1fr; }
  .guide-card { min-height: auto; }
  .grid { grid-template-columns: 1fr; }
  .story:first-child { grid-column: span 1; }
  h1 { font-size: 46px; }
}
"""


def render_feed(items: list[Item], story_paths: dict[str, str]) -> str:
    now = email.utils.format_datetime(datetime.now(timezone.utc))
    entries = []
    for item in items:
        story_url = f"{SITE_URL}/{story_paths[item.link]}"
        entries.append(
            f"""  <item>
    <title>{esc(display_title(item))}</title>
    <link>{esc(story_url)}</link>
    <guid>{esc(story_url)}</guid>
    <pubDate>{email.utils.format_datetime(item.published)}</pubDate>
    <description>{esc(display_summary(item))}</description>
  </item>"""
        )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>{SITE_NAME}</title>
  <link>{SITE_URL}/</link>
  <atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
  <atom:link href="{WEBSUB_HUB_URL}" rel="hub"/>
  <description>{esc(SITE_DESCRIPTION)}</description>
  <lastBuildDate>{now}</lastBuildDate>
{''.join(entries)}
</channel>
</rss>
"""


def render_atom_feed(items: list[Item], story_paths: dict[str, str]) -> str:
    updated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    entries = []
    for item in items:
        published = item.published.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        story_url = f"{SITE_URL}/{story_paths[item.link]}"
        entries.append(
            f"""  <entry>
    <title>{esc(display_title(item))}</title>
    <link href="{esc(story_url)}"/>
    <id>{esc(story_url)}</id>
    <updated>{published}</updated>
    <summary>{esc(display_summary(item))}</summary>
    <category term="{esc(item.category)}"/>
  </entry>"""
        )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>{SITE_NAME}</title>
  <subtitle>{esc(SITE_DESCRIPTION)}</subtitle>
  <link href="{SITE_URL}/atom.xml" rel="self" type="application/atom+xml"/>
  <link href="{WEBSUB_HUB_URL}" rel="hub"/>
  <link href="{SITE_URL}/"/>
  <updated>{updated}</updated>
  <id>{SITE_URL}/</id>
{chr(10).join(entries)}
</feed>
"""


def render_json_feed(items: list[Item], story_paths: dict[str, str]) -> str:
    payload = {
        "version": "https://jsonfeed.org/version/1.1",
        "title": SITE_NAME,
        "home_page_url": f"{SITE_URL}/",
        "feed_url": f"{SITE_URL}/feed.json",
        "description": SITE_DESCRIPTION,
        "language": "es",
        "items": [
            {
                "id": f"{SITE_URL}/{story_paths[item.link]}",
                "url": f"{SITE_URL}/{story_paths[item.link]}",
                "external_url": item.link,
                "title": display_title(item),
                "summary": display_summary(item),
                "date_published": item.published.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "tags": [item.category, item.source],
            }
            for item in items
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def render_sitemap(story_paths: dict[str, str] | None = None) -> str:
    today = datetime.now(timezone.utc).date().isoformat()
    story_urls = "\n".join(
        f"""  <url>
    <loc>{SITE_URL}/{filename}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.8</priority>
  </url>"""
        for filename in (story_paths or {}).values()
    )
    utility_urls = "\n".join(
        f"""  <url>
    <loc>{SITE_URL}/{filename}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>{changefreq}</changefreq>
    <priority>{priority}</priority>
  </url>"""
        for filename, changefreq, priority in [
            ("feed.xml", "daily", "0.7"),
            ("atom.xml", "daily", "0.7"),
            ("feed.json", "daily", "0.7"),
            *[(page["filename"], "daily", "0.9") for page in TREND_PAGES],
            ("llms.txt", "weekly", "0.6"),
            ("humans.txt", "monthly", "0.4"),
        ]
    )
    page_urls = "\n".join(
        f"""  <url>
    <loc>{SITE_URL}/{filename}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.6</priority>
  </url>"""
        for filename in STATIC_PAGES
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{SITE_URL}/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
{utility_urls}
{story_urls}
{page_urls}
</urlset>
"""


def render_news_sitemap(items: list[Item], story_paths: dict[str, str]) -> str:
    entries = []
    for item in items:
        published = item.published.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        story_url = f"{SITE_URL}/{story_paths[item.link]}"
        entries.append(
            f"""  <url>
    <loc>{esc(story_url)}</loc>
    <news:news>
      <news:publication>
        <news:name>{SITE_NAME}</news:name>
        <news:language>es</news:language>
      </news:publication>
      <news:publication_date>{published}</news:publication_date>
      <news:title>{esc(display_title(item))}</news:title>
    </news:news>
  </url>"""
        )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">
{''.join(entries)}
</urlset>
"""


def render_llms_txt() -> str:
    trend_lines = "\n".join(
        f"- {page['title']}: {SITE_URL}/{page['filename']}"
        for page in TREND_PAGES
    )
    guide_lines = "\n".join(
        f"- [{page['title']}]({SITE_URL}/{filename}): {page['description']}"
        for filename, page in STATIC_PAGES.items()
        if filename
        in {
            "noticias-tecnologia-espanol.html",
            "glosario-ia-tecnologia.html",
            "herramientas-ia-gratis.html",
            "ia-para-estudiantes.html",
            "proteger-cuenta-google.html",
            "chatgpt-gemini-claude.html",
            "que-es-ia-local.html",
            "npu-vs-gpu.html",
            "privacidad-chatbots-ia.html",
            "checklist-phishing.html",
        }
    )
    return f"""# {SITE_NAME}

> {SITE_DESCRIPTION}

Pulso Tech Diario es un blog en espanol sobre inteligencia artificial, ciberseguridad, chips, plataformas y herramientas digitales. Publica un resumen diario en Blogger y mantiene guias evergreen en GitHub Pages.

## URLs principales

- Blog principal: {BLOG_URL}/
- Ultima entrada: {SITE_URL}/ultima-entrada.html
- Seguir el sitio: {SITE_URL}/seguir.html
- Link en bio: {SITE_URL}/links.html
- Kit para compartir: {SITE_URL}/share-pack.html
- Archivo de Blogger: {SITE_URL}/blogger-archivo.html
- Feed RSS del sitio: {SITE_URL}/feed.xml
- Feed Atom del sitio: {SITE_URL}/atom.xml
- JSON Feed del sitio: {SITE_URL}/feed.json
- Feed RSS de Blogger: {BLOGGER_RSS_URL}
- Payload social diario: {SITE_URL}/social-payload.json
- Datos publicos del resumen: {SITE_URL}/data.json

## Tendencias diarias por tema

{trend_lines}

## Guias utiles

{guide_lines}

## Uso recomendado

Usa el blog principal como destino canonico de lectura y las guias como contexto estable. Las notas enlazan a fuentes originales y no deben tratarse como reproducciones completas de articulos externos.
"""


def render_humans_txt() -> str:
    today = datetime.now(timezone.utc).date().isoformat()
    return f"""/* TEAM */
Site: {SITE_NAME}
Role: Blog automatizado de tecnologia en espanol
Contact: https://github.com/elianguitarra/pulso-tech-diario

/* SITE */
Blog: {BLOG_URL}/
Static hub: {SITE_URL}/
Last update: {today}
Language: Spanish
Topics: inteligencia artificial, ciberseguridad, chips, hardware, productividad, plataformas digitales
Stack: Python, Blogger API, GitHub Actions, GitHub Pages
Feeds: {SITE_URL}/feed.xml, {SITE_URL}/atom.xml, {SITE_URL}/feed.json, {BLOGGER_RSS_URL}
"""


def write_static(items: list[Item]) -> None:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    image_paths = save_images(items)
    story_paths = write_story_pages(items, image_paths)
    if FEATURE_ASSET_SOURCE.exists():
        FEATURE_ASSET_DEST.mkdir(parents=True, exist_ok=True)
        for asset in FEATURE_ASSET_SOURCE.iterdir():
            if asset.is_file():
                shutil.copy2(asset, FEATURE_ASSET_DEST / asset.name)
    if BRAND_ASSET_SOURCE.exists():
        BRAND_ASSET_DEST.mkdir(parents=True, exist_ok=True)
        for asset in BRAND_ASSET_SOURCE.iterdir():
            if asset.is_file():
                shutil.copy2(asset, BRAND_ASSET_DEST / asset.name)
    (PUBLIC / "index.html").write_text(render_index(items, image_paths, story_paths), encoding="utf-8")
    for page in TREND_PAGES:
        (PUBLIC / page["filename"]).write_text(
            render_trends_page(
                items,
                image_paths,
                story_paths,
                filename=page["filename"],
                title=page["title"],
                description=page["description"],
                intro=page["intro"],
                blogger_label_url=page["blogger_url"],
                category_filter=page["categories"],
            ),
            encoding="utf-8",
        )
    for filename, page in STATIC_PAGES.items():
        (PUBLIC / filename).write_text(render_static_page(filename, page), encoding="utf-8")
    (PUBLIC / "style.css").write_text(render_css(), encoding="utf-8")
    (PUBLIC / "feed.xml").write_text(render_feed(items, story_paths), encoding="utf-8")
    (PUBLIC / "atom.xml").write_text(render_atom_feed(items, story_paths), encoding="utf-8")
    (PUBLIC / "feed.json").write_text(render_json_feed(items, story_paths), encoding="utf-8")
    (PUBLIC / "sitemap.xml").write_text(render_sitemap(story_paths), encoding="utf-8")
    (PUBLIC / "news-sitemap.xml").write_text(render_news_sitemap(items, story_paths), encoding="utf-8")
    (PUBLIC / "llms.txt").write_text(render_llms_txt(), encoding="utf-8")
    (PUBLIC / "humans.txt").write_text(render_humans_txt(), encoding="utf-8")
    (PUBLIC / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\nSitemap: {SITE_URL}/news-sitemap.xml\n",
        encoding="utf-8",
    )
    (PUBLIC / f"{INDEXNOW_KEY}.txt").write_text(INDEXNOW_KEY, encoding="utf-8")
    ads_txt = PUBLIC / "ads.txt"
    if valid_adsense_client():
        ads_txt.write_text(
            f"google.com, {adsense_publisher_id()}, DIRECT, f08c47fec0942fa0\n", encoding="utf-8"
        )
    elif ads_txt.exists():
        ads_txt.unlink()
    public_items = []
    for item in items:
        payload = item.__dict__ | {"published": item.published.isoformat()}
        payload["title"] = display_title(item)
        payload["summary"] = display_summary(item)
        payload["url"] = f"{SITE_URL}/{story_paths[item.link]}"
        payload["external_url"] = item.link
        public_items.append(payload)
    (PUBLIC / "data.json").write_text(json.dumps(public_items, indent=2), encoding="utf-8")


def fallback_items() -> list[Item]:
    now = datetime.now(timezone.utc)
    samples = [
        ("La inteligencia artificial redefine el software de trabajo", "inteligencia artificial"),
        ("La carrera por chips mas eficientes acelera nuevos dispositivos", "chips"),
        ("La seguridad digital vuelve al centro de las decisiones tecnologicas", "ciberseguridad"),
        ("Nuevas startups empujan productos mas pequenos y utiles", "startups"),
    ]
    return [
        Item(
            title=title,
            link=SITE_URL,
            source=SITE_NAME,
            summary="Contenido temporal generado cuando las fuentes RSS no estan disponibles.",
            published=now,
            category=category,
            score=1,
        )
        for title, category in samples
    ]


def main() -> None:
    items = collect_items()
    if not items:
        items = fallback_items()
    write_static(items)
    print(f"built {len(items)} stories in {PUBLIC}")


if __name__ == "__main__":
    main()
