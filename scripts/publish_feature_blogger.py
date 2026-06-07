#!/usr/bin/env python3
"""Publish the curated RTX Spark feature directly with Blogger API."""

from __future__ import annotations

import publish_blogger
import publish_feature_email


LABELS = ["inteligencia artificial", "nvidia", "windows", "pc", "pulso tech diario"]


def publish() -> None:
    blog_id = publish_blogger.required_env("BLOGGER_BLOG_ID")
    token = publish_blogger.get_access_token()
    title = publish_feature_email.EMAIL_TITLE
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
