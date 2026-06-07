#!/usr/bin/env python3
"""Publish the curated RTX Spark feature directly with Blogger API."""

from __future__ import annotations

import os

import publish_blogger
import publish_feature_email


LABELS = ["inteligencia artificial", "nvidia", "windows", "pc", "pulso tech diario"]
OLD_TITLES = [
    "Nvidia RTX Spark: IA local en PCs",
    "Nvidia y Microsoft quieren que la IA viva dentro de tu PC",
]


def truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "si", "sí"}


def delete_post(blog_id: str, token: str, post_id: str) -> None:
    url = f"{publish_blogger.BLOGGER_API}/blogs/{blog_id}/posts/{post_id}"
    publish_blogger.request_json(url, method="DELETE", token=token)


def publish() -> None:
    blog_id = publish_blogger.required_env("BLOGGER_BLOG_ID")
    token = publish_blogger.get_access_token()
    title = publish_feature_email.EMAIL_TITLE
    if truthy(os.environ.get("RECREATE_FEATURE", "")):
        for old_title in [title, *OLD_TITLES]:
            existing_old = publish_blogger.find_post_by_title(blog_id, token, old_title)
            if existing_old and existing_old.get("id"):
                delete_post(blog_id, token, existing_old["id"])
                print(f"Deleted feature: {old_title}")
                publish_blogger.throttle_write()

    existing = publish_blogger.find_post_by_title(blog_id, token, title)
    payload = publish_blogger.post_payload(title, publish_feature_email.post_html(), LABELS)
    if existing and existing.get("id"):
        url = f"{publish_blogger.BLOGGER_API}/blogs/{blog_id}/posts/{existing['id']}"
        result = publish_blogger.request_json(url, method="PUT", token=token, payload=payload)
        print(f"Updated feature: {result.get('url', result.get('id'))}")
        return
    url = f"{publish_blogger.BLOGGER_API}/blogs/{blog_id}/posts/"
    result = publish_blogger.request_json(url, method="POST", token=token, payload=payload)
    print(f"Published feature: {result.get('url', result.get('id'))}")


if __name__ == "__main__":
    publish()
