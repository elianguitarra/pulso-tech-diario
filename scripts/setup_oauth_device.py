#!/usr/bin/env python3
"""Cloud Shell friendly Blogger OAuth setup using Google's device flow.

Create an OAuth client of type "TVs and Limited Input devices", then run this
script in Cloud Shell. It prints a verification URL and code, polls until the
account authorizes Blogger access, chooses a blog, and stores GitHub Secrets.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


DEVICE_CODE_URL = "https://oauth2.googleapis.com/device/code"
TOKEN_URL = "https://oauth2.googleapis.com/token"
BLOGGER_API = "https://www.googleapis.com/blogger/v3"
SCOPE = "https://www.googleapis.com/auth/blogger"


def read_value(prompt: str, required: bool = True) -> str:
    value = input(prompt).strip()
    if required and not value:
        raise SystemExit(f"Missing value for {prompt}")
    return value


def post_form(url: str, fields: dict[str, str]) -> dict:
    request = urllib.request.Request(
        url,
        data=urllib.parse.urlencode(fields).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def request_device_code(client_id: str) -> dict:
    return post_form(DEVICE_CODE_URL, {"client_id": client_id, "scope": SCOPE})


def poll_token(client_id: str, device_code: str, interval: int) -> dict:
    fields = {
        "client_id": client_id,
        "device_code": device_code,
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
    }
    while True:
        time.sleep(interval)
        try:
            return post_form(TOKEN_URL, fields)
        except urllib.error.HTTPError as exc:
            payload = json.loads(exc.read().decode("utf-8"))
            error = payload.get("error", "")
            if error == "authorization_pending":
                print("Esperando autorizacion...")
                continue
            if error == "slow_down":
                interval += 5
                print(f"Google pidio ir mas lento. Nuevo intervalo: {interval}s")
                continue
            raise SystemExit(json.dumps(payload, indent=2))


def request_json(url: str, token: str) -> dict:
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def choose_blog(access_token: str) -> str:
    payload = request_json(f"{BLOGGER_API}/users/self/blogs", access_token)
    blogs = payload.get("items", [])
    if not blogs:
        raise SystemExit("No Blogger blogs found for this Google account.")
    print("\nBlogs available in this account:")
    for index, blog in enumerate(blogs, start=1):
        print(f"{index}. {blog.get('name')} - {blog.get('url')} - id {blog.get('id')}")
    if len(blogs) == 1:
        print("Using the only blog found.")
        return blogs[0]["id"]
    selected = read_value("Choose blog number: ")
    try:
        return blogs[int(selected) - 1]["id"]
    except (ValueError, IndexError):
        raise SystemExit("Invalid blog selection.")


def set_gh_secret(repo: str, name: str, value: str) -> None:
    subprocess.run(["gh", "secret", "set", name, "--repo", repo, "--body", value], check=True)


def run_publish_workflow(repo: str) -> None:
    subprocess.run(["gh", "workflow", "run", "publish-blogger.yml", "--repo", repo, "--ref", "main"], check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Configure Blogger OAuth from Cloud Shell using device flow.")
    parser.add_argument("--repo", default="elianguitarra/pulso-tech-diario", help="GitHub repo for secrets.")
    parser.add_argument("--store-gh-secrets", action="store_true", help="Store values with gh secret set.")
    parser.add_argument("--run-workflow", action="store_true", help="Run publish-blogger.yml after saving secrets.")
    args = parser.parse_args()
    if args.run_workflow and not args.store_gh_secrets:
        raise SystemExit("--run-workflow requires --store-gh-secrets.")

    print('Create an OAuth client in Google Cloud as "TVs and Limited Input devices".')
    print("Paste its client ID here. Do not paste values in chat.")
    client_id = read_value("GOOGLE_CLIENT_ID: ")
    client_secret = read_value("GOOGLE_CLIENT_SECRET, optional; press Enter if none: ", required=False)

    device = request_device_code(client_id)
    print("\nOpen this URL in your browser:")
    print(device.get("verification_url") or device.get("verification_url_complete"))
    print("\nEnter this code:")
    print(device["user_code"])
    print("\nAfter approving Blogger access, return here. Cloud Shell will keep polling.")

    token = poll_token(client_id, device["device_code"], int(device.get("interval", 5)))
    refresh_token = token.get("refresh_token")
    if not refresh_token:
        raise SystemExit("Google did not return a refresh_token. Revoke access or recreate the OAuth client and try again.")
    blog_id = choose_blog(token["access_token"])

    values = {
        "BLOGGER_BLOG_ID": blog_id,
        "GOOGLE_CLIENT_ID": client_id,
        "GOOGLE_REFRESH_TOKEN": refresh_token,
    }
    if client_secret:
        values["GOOGLE_CLIENT_SECRET"] = client_secret

    if args.store_gh_secrets:
        for name, value in values.items():
            set_gh_secret(args.repo, name, value)
        print("\nGitHub Secrets saved.")
        if args.run_workflow:
            run_publish_workflow(args.repo)
            print("Blogger publish workflow started.")
    else:
        print("\nGenerated values:")
        print(f"BLOGGER_BLOG_ID={blog_id}")
        print(f"GOOGLE_CLIENT_ID={client_id}")
        print("GOOGLE_REFRESH_TOKEN=<hidden>")
        if client_secret:
            print("GOOGLE_CLIENT_SECRET=<hidden>")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as exc:
        sys.stderr.write(exc.read().decode("utf-8", errors="replace"))
        raise
