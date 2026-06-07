# Pulso Tech Diario

Blog automatizado que publica un resumen diario de noticias tecnologicas relevantes en Blogger/Blogspot. No usa hosting de pago ni dominio propio.

## Como funciona

- `scripts/build.py` lee fuentes RSS publicas de tecnologia y tambien puede generar una preview estatica.
- `scripts/publish_blogger.py` crea un post diario en Blogger con la API oficial.
- Puntua las notas por frescura, fuente y tema.
- Crea una imagen SVG original incrustada para cada nota, construida automaticamente a partir de su tema.
- Crea o actualiza paginas base del blog: `Acerca de`, `Politica editorial`, `Privacidad` y `Contacto`.
- Crea o actualiza posts evergreen originales para sembrar el blog con contenido util y monetizable.
- GitHub Actions lo ejecuta todos los dias a las 12:10 UTC y publica en tu blog de Blogger.

## Publicacion gratuita en Blogger

Blogger es gratis y puede usarse con subdominio `blogspot.com`. Es una buena opcion para AdSense porque pertenece a Google y tiene panel de monetizacion propio.

Tambien existe una version publica de respaldo en GitHub Pages:

`https://elianguitarra.github.io/pulso-tech-diario/`

Esa version es gratis y se reconstruye a diario. La ruta Blogger/Mail2Blogger sigue siendo la recomendada para monetizacion con AdSense.

Para publicar automaticamente hacen falta estos secretos en el repositorio que ejecuta la automatizacion:

- `BLOGGER_BLOG_ID`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REFRESH_TOKEN`

La cuenta Google debe autorizar el alcance `https://www.googleapis.com/auth/blogger`. Sin esa autorizacion, ningun sistema externo puede crear posts en tu blog.

### Alternativa sin Google Cloud: Mail2Blogger

Si Google Cloud te pide pago, usa Mail2Blogger. Blogger permite publicar enviando un correo a una direccion secreta del blog.

En Blogger:

1. Ve a `Settings`.
2. Busca `Email`.
3. En `Post using email` / `Mail2Blogger`, crea una direccion secreta.
4. Elige publicar inmediatamente o guardar como borrador, segun prefieras.

Luego guarda estos secretos en GitHub:

- `BLOGGER_MAIL_TO`: la direccion secreta de Mail2Blogger.
- `SMTP_HOST`: servidor SMTP, por ejemplo `smtp.gmail.com`.
- `SMTP_PORT`: normalmente `587`.
- `SMTP_USERNAME`: usuario del correo remitente.
- `SMTP_PASSWORD`: password SMTP o app password.
- `SMTP_FROM`: correo remitente. Opcional si es igual a `SMTP_USERNAME`.

Comandos:

```powershell
gh secret set BLOGGER_MAIL_TO
gh secret set SMTP_HOST
gh secret set SMTP_PORT
gh secret set SMTP_USERNAME
gh secret set SMTP_PASSWORD
gh secret set SMTP_FROM
```

O usa el asistente local:

```powershell
cd "C:\Users\malow\Documents\New project\pulso-tech-diario"
C:\Users\malow\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe scripts\setup_email.py --run-workflow
```

Despues ejecuta el workflow `Publicar por Email` desde GitHub Actions o con:

```powershell
gh workflow run publish-email.yml --ref main
```

### Conexion OAuth segura

Guia detallada con Cloud Shell: [docs/OAUTH_CLOUD_SHELL.md](docs/OAUTH_CLOUD_SHELL.md).

1. Crea un blog gratis en [Blogger](https://www.blogger.com/).
2. En [Google Cloud Console](https://console.cloud.google.com/), crea un proyecto.
3. Activa la **Blogger API v3**.
4. Configura la pantalla de consentimiento OAuth.
5. Crea credenciales OAuth tipo **Desktop app**.
6. Ejecuta el asistente local:

```powershell
cd "C:\Users\malow\Documents\New project\pulso-tech-diario"
C:\Users\malow\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe scripts\setup_oauth.py --store-gh-secrets
```

El asistente abre Google en tu navegador, captura la autorizacion en `localhost`, lista tus blogs y guarda los valores con `gh secret set`. No pegues secretos en el chat.

Para guardar secretos y lanzar la primera publicacion inmediatamente:

```powershell
C:\Users\malow\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe scripts\setup_oauth.py --store-gh-secrets --run-workflow
```

Si prefieres revisar antes de guardar:

```powershell
C:\Users\malow\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe scripts\setup_oauth.py
```

Para revisar el estado de configuracion en cualquier momento:

```powershell
C:\Users\malow\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe scripts\doctor.py
```

El doctor revisa GitHub CLI, autenticacion, workflows, secrets requeridos y ultimas corridas.

El doctor tambien revisa que la version publica de GitHub Pages responda con contenido real.

## Crecimiento y visibilidad

El sitio incluye:

- Paginas de confianza para lectores y revision de AdSense.
- Posts evergreen propios sobre metodologia, glosario de IA y senales de industria.
- Etiquetas tematicas para que Blogger agrupe los posts por tecnologia, IA y noticias tech.
- Titulares enlazados a fuentes originales para evitar copiar contenido completo.
- Imagenes propias por nota para mejorar vistas previas y diferenciacion visual.
- Preparacion para AdSense desde Blogger, incluyendo soporte para `ads.txt` personalizado.

## AdSense

El blog esta preparado para monetizacion, pero Google debe aprobar la web y tu cuenta. No conviene publicar IDs falsos.

En Blogger, activa la monetizacion desde el panel y configura `ads.txt` personalizado con el valor que te de AdSense. Si usas secretos, puedes conservar:

- `ADSENSE_CLIENT`: tu ID con formato `ca-pub-0000000000000000`.

En Blogger normalmente se hace desde **Configuracion > Monetizacion > Habilitar ads.txt personalizado**. El valor de AdSense suele tener esta forma:

```text
google.com, pub-0000000000000000, DIRECT, f08c47fec0942fa0
```

Reemplaza `pub-0000000000000000` por tu ID real de AdSense. Google puede tardar dias en revisar el blog y el `ads.txt`.

Siguientes pasos recomendados despues de publicarlo:

- Enviar `sitemap.xml` a Google Search Console cuando quieras acelerar indexacion.
- Compartir la URL diaria en X, LinkedIn, Reddit o comunidades tech.
- Agregar la URL al perfil de GitHub y a cualquier bio publica.

## Preview local

```powershell
C:\Users\malow\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe scripts\build.py
```

Luego abre `public/index.html`.

## Verificacion publica

La version publica debe responder en:

```text
https://elianguitarra.github.io/pulso-tech-diario/
```

Puedes verificarla con:

```powershell
C:\Users\malow\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe scripts\doctor.py
```

## Publicacion manual de prueba

```powershell
$env:BLOGGER_BLOG_ID="tu_blog_id_real"
$env:GOOGLE_CLIENT_ID="tu_client_id_real"
$env:GOOGLE_CLIENT_SECRET="tu_client_secret_real"
$env:GOOGLE_REFRESH_TOKEN="tu_refresh_token_real"
C:\Users\malow\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe scripts\publish_blogger.py
```

## Automatizacion diaria

El workflow `.github/workflows/publish-blogger.yml` corre todos los dias a las 12:10 UTC y publica un nuevo post si no existe uno para esa fecha. Tambien puedes ejecutarlo manualmente desde la pestana **Actions** del repositorio.

Aunque la publicacion final sera Blogger, GitHub Actions sigue siendo util como motor gratuito de automatizacion. No aloja el sitio: solo despierta el script diario y manda el post a Blogspot.

Si usas la ruta sin Google Cloud, el workflow `.github/workflows/publish-email.yml` envia el post diario por Mail2Blogger todos los dias a las 12:20 UTC.

El workflow `.github/workflows/pages.yml` publica una version estatica gratis en GitHub Pages todos los dias a las 12:30 UTC.

Despues de correr el asistente con `--run-workflow`, puedes ver el primer despliegue con:

```powershell
gh run list --workflow publish-blogger.yml
```

El publicador usa endpoints oficiales de Blogger API v3:

- Posts: `POST /blogs/{blogId}/posts`
- Pages: `POST /blogs/{blogId}/pages`
- Pages update: `PUT /blogs/{blogId}/pages/{pageId}`
