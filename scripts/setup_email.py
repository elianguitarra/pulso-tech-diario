#!/usr/bin/env python3
"""Store Mail2Blogger + SMTP settings as GitHub Secrets."""

from __future__ import annotations

import argparse
import getpass
import subprocess


DEFAULTS = {
    "SMTP_HOST": "smtp.gmail.com",
    "SMTP_PORT": "587",
    "SMTP_SSL": "false",
    "SMTP_STARTTLS": "true",
    "EMAIL_SUBJECT_PREFIX": "Pulso Tech Diario",
}


def prompt(name: str, default: str = "", secret: bool = False, required: bool = True) -> str:
    suffix = f" [{default}]" if default else ""
    raw_prompt = f"{name}{suffix}: "
    value = getpass.getpass(raw_prompt).strip() if secret else input(raw_prompt).strip()
    if not value:
        value = default
    if required and not value:
        raise SystemExit(f"Missing required value: {name}")
    return value


def set_gh_secret(name: str, value: str) -> None:
    subprocess.run(["gh", "secret", "set", name], input=value, text=True, check=True)


def run_publish_workflow() -> None:
    subprocess.run(["gh", "workflow", "run", "publish-email.yml", "--ref", "main"], check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Configure Mail2Blogger email publishing.")
    parser.add_argument("--run-workflow", action="store_true", help="Run the first email publish workflow after saving secrets.")
    args = parser.parse_args()

    print("Configure Blogger Mail2Blogger + SMTP. Do not paste these values in chat.")
    print("For Gmail use SMTP_SSL=false, SMTP_STARTTLS=true, SMTP_PORT=587.")
    print("For Gmail SMTP_PASSWORD must be a Google App Password, not your normal password.")
    print("Official help: https://support.google.com/mail/answer/185833")
    smtp_username = prompt("SMTP_USERNAME")
    values = {
        "BLOGGER_MAIL_TO": prompt("BLOGGER_MAIL_TO"),
        "SMTP_HOST": prompt("SMTP_HOST", DEFAULTS["SMTP_HOST"]),
        "SMTP_PORT": prompt("SMTP_PORT", DEFAULTS["SMTP_PORT"]),
        "SMTP_USERNAME": smtp_username,
        "SMTP_PASSWORD": prompt("SMTP_PASSWORD", secret=True),
        "SMTP_FROM": prompt("SMTP_FROM", smtp_username, required=False),
        "SMTP_SSL": prompt("SMTP_SSL", DEFAULTS["SMTP_SSL"]),
        "SMTP_STARTTLS": prompt("SMTP_STARTTLS", DEFAULTS["SMTP_STARTTLS"]),
        "EMAIL_SUBJECT_PREFIX": prompt("EMAIL_SUBJECT_PREFIX", DEFAULTS["EMAIL_SUBJECT_PREFIX"], required=False),
    }

    reply_to = prompt("SMTP_REPLY_TO", values["SMTP_FROM"], required=False)
    if reply_to:
        values["SMTP_REPLY_TO"] = reply_to

    for name, value in values.items():
        if value:
            set_gh_secret(name, value)
    print("\nMail2Blogger GitHub Secrets saved.")

    if args.run_workflow:
        run_publish_workflow()
        print("First email publish workflow started. Check it with: gh run list --workflow publish-email.yml")


if __name__ == "__main__":
    main()
