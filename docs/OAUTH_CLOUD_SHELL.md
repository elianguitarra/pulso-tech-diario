# Crear OAuth Desktop App para Pulso Tech Diario

Esta guia prepara Google Cloud para que `scripts/setup_oauth.py` pueda publicar en Blogger.

No pegues `GOOGLE_CLIENT_SECRET` ni `GOOGLE_REFRESH_TOKEN` en chats, issues o commits. El asistente local los guarda como GitHub Secrets.

## 1. Preparar Google Cloud desde Cloud Shell

Abre Google Cloud Console y entra a Cloud Shell:

https://console.cloud.google.com/

Ejecuta:

```bash
PROJECT_ID="pulso-tech-diario-$RANDOM"

gcloud projects create "$PROJECT_ID" --name="Pulso Tech Diario"
gcloud config set project "$PROJECT_ID"
gcloud services enable blogger.googleapis.com

echo "Proyecto listo: $PROJECT_ID"
```

Guarda el `PROJECT_ID`.

Si ya tienes un proyecto, puedes usarlo asi:

```bash
PROJECT_ID="tu-project-id"
gcloud config set project "$PROJECT_ID"
gcloud services enable blogger.googleapis.com
```

## 2. Configurar Google Auth Platform

Entra a:

https://console.cloud.google.com/auth/overview

Selecciona el proyecto `PROJECT_ID` y configura:

- App name: `Pulso Tech Diario`
- User support email: tu correo
- Audience/User type: `External`
- Contact email: tu correo

Nota importante: si la app queda en modo `Testing`, Google puede hacer que el refresh token expire despues de 7 dias. Para automatizacion diaria real, pasa la app a `Production` cuando la consola lo permita.

## 3. Crear OAuth Client tipo Desktop app

Entra a:

https://console.cloud.google.com/auth/clients

Pasos:

1. Click `Create client`.
2. Application type: `Desktop app`.
3. Name: `Pulso Tech Diario Local OAuth`.
4. Click `Create`.
5. Copia y guarda:
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`

Guarda el `GOOGLE_CLIENT_SECRET` en un lugar seguro. Google puede mostrarlo completo solo al crearlo.

## 4. Autorizar Blogger localmente y publicar

Este paso debe correr en Windows/local, no en Cloud Shell, porque el asistente escucha en `localhost` para recibir el callback OAuth.

```powershell
cd "C:\Users\malow\Documents\New project\pulso-tech-diario"
C:\Users\malow\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe scripts\setup_oauth.py --store-gh-secrets --run-workflow
```

El asistente:

1. Pide `GOOGLE_CLIENT_ID`.
2. Pide `GOOGLE_CLIENT_SECRET`.
3. Abre Google en el navegador.
4. Captura la autorizacion en `localhost`.
5. Lista tus blogs de Blogger.
6. Guarda `BLOGGER_BLOG_ID`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` y `GOOGLE_REFRESH_TOKEN` en GitHub Secrets.
7. Lanza el primer workflow `publish-blogger.yml`.

## 5. Revisar el primer despliegue

```powershell
gh run list --workflow publish-blogger.yml
gh run watch
```

Si el workflow termina bien, Blogger tendra:

- Paginas base: Acerca de, Politica editorial, Privacidad, Contacto.
- Posts evergreen originales.
- Post diario con noticias tecnologicas e imagenes SVG originales.

