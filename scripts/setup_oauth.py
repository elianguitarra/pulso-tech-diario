#!/usr/bin/env python3
"""Local helper to create Blogger OAuth secrets safely.

This script never sends secrets to chat. It guides the user through Google's
installed-app OAuth flow and can store the resulting values in GitHub Secrets.
"""

from __future__ import annotations

import argparse
import http.server
import json
import secrets
import subprocess
import sys
import threading
import urllib.parse
import urllib.request
import webbrowser


AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
BLOGGER_API = "https://www.googleapis.com/blogger/v3"
SCOPE = "https://www.googleapis.com/auth/blogger"


class OAuthHandler(http.server.BaseHTTPRequestHandler):
    server_version = "PulsoTechOAuth/1.0"

    def log_message(self, format: str, *args: object) -> None:
        return

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        self.server.auth_code = params.get("code", [""])[0]  # type: ignore[attr-defined]
        self.server.auth_state = params.get("state", [""])[0]  # type: ignore[attr-defined]
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            b"<h1>Autorizacion recibida</h1><p>Ya puedes volver a la terminal de Codex.</p>"
        )


def read_secret(prompt: str) -> str:
    value = input(prompt).strip()
    if not value:
        raise SystemExit(f"Missing value for {prompt}")
    return value


def exchange_code(client_id: str, client_secret: str, redirect_uri: str, code: str) -> dict:
    form = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        TOKEN_URL,
        data=form,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def set_gh_secret(name: str, value: str) -> None:
    subprocess.run(["gh", "secret", "set", name], input=value, text=True, check=True)


def request_json(url: str, token: str) -> dict:
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def choose_blog(access_token: str) -> str:
    payload = request_json(f"{BLOGGER_API}/users/self/blogs", access_token)
    blogs = payload.get("items", [])
    if not blogs:
        raise SystemExit("No Blogger blogs found for this Google account. Create a blog first at https://www.blogger.com/")
    print("\nBlogs available in this account:")
    for index, blog in enumerate(blogs, start=1):
        print(f"{index}. {blog.get('name')} - {blog.get('url')} - id {blog.get('id')}")
    if len(blogs) == 1:
        print("Using the only blog found.")
        return blogs[0]["id"]
    selected = read_secret("Choose blog number: ")
    try:
        blog = blogs[int(selected) - 1]
    except (ValueError, IndexError):
        raise SystemExit("Invalid blog selection.")
    return blog["id"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Blogger OAuth refresh token.")
    parser.add_argument("--store-gh-secrets", action="store_true", help="Store values with gh secret set.")
    args = parser.parse_args()

    print("Create an OAuth client in Google Cloud as a Desktop app, then paste its values here.")
    client_id = read_secret("GOOGLE_CLIENT_ID: ")
    client_secret = read_secret("GOOGLE_CLIENT_SECRET: ")
    state = secrets.token_urlsafe(24)
    server = http.server.HTTPServer(("127.0.0.1", 0), OAuthHandler)
    server.auth_code = ""  # type: ignore[attr-defined]
    server.auth_state = ""  # type: ignore[attr-defined]
    redirect_uri = f"http://127.0.0.1:{server.server_port}/callback"

    params = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": SCOPE,
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
    )
    auth_link = f"{AUTH_URL}?{params}"
    print("\nOpening this URL. Approve Blogger access in your browser:\n")
    print(auth_link)
    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()
    try:
        webbrowser.open(auth_link)
    except Exception:
        pass
    print("\nWaiting for Google to redirect back to localhost...")
    thread.join(timeout=180)
    server.server_close()
    code = server.auth_code  # type: ignore[attr-defined]
    returned_state = server.auth_state  # type: ignore[attr-defined]
    if not code:
        raise SystemExit("No authorization code received. Re-run the script and complete the browser approval.")
    if returned_state != state:
        raise SystemExit("OAuth state mismatch. Aborting for safety.")
    token = exchange_code(client_id, client_secret, redirect_uri, code)
    refresh_token = token.get("refresh_token")
    if not refresh_token:
        raise SystemExit("Google did not return a refresh_token. Re-run with prompt=consent or create a new OAuth client.")
    blog_id = choose_blog(token["access_token"])

    values = {
        "BLOGGER_BLOG_ID": blog_id,
        "GOOGLE_CLIENT_ID": client_id,
        "GOOGLE_CLIENT_SECRET": client_secret,
        "GOOGLE_REFRESH_TOKEN": refresh_token,
    }

    if args.store_gh_secrets:
        for name, value in values.items():
            set_gh_secret(name, value)
        print("\nGitHub Secrets saved.")
    else:
        print("\nRun these commands from the project folder. Paste each value when prompted:")
        for name in values:
            print(f"gh secret set {name}")
        print("\nValues generated in this local session:")
        print(f"BLOGGER_BLOG_ID={blog_id}")
        print(f"GOOGLE_CLIENT_ID={client_id}")
        print("GOOGLE_CLIENT_SECRET=<hidden>")
        print("GOOGLE_REFRESH_TOKEN=<hidden>")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as exc:
        sys.stderr.write(exc.read().decode("utf-8", errors="replace"))
        raise
