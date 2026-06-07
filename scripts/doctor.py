#!/usr/bin/env python3
"""Check whether Pulso Tech Diario is ready to publish to Blogger."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass


REPO = "elianguitarra/pulso-tech-diario"
REQUIRED_SECRETS = {
    "BLOGGER_BLOG_ID",
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "GOOGLE_REFRESH_TOKEN",
}
EMAIL_SECRETS = {
    "BLOGGER_MAIL_TO",
    "SMTP_HOST",
    "SMTP_USERNAME",
    "SMTP_PASSWORD",
    "SMTP_FROM",
}
OPTIONAL_SECRETS = {"ADSENSE_CLIENT"}


@dataclass
class Check:
    name: str
    ok: bool
    detail: str


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True)


def gh_json(args: list[str]) -> dict | list:
    result = run(["gh", *args])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return json.loads(result.stdout or "{}")


def check_python() -> Check:
    version = ".".join(str(part) for part in sys.version_info[:3])
    return Check("Python", sys.version_info >= (3, 12), version)


def check_gh_installed() -> Check:
    path = shutil.which("gh")
    return Check("GitHub CLI", bool(path), path or "gh not found")


def check_gh_auth() -> Check:
    result = run(["gh", "auth", "status"])
    return Check("GitHub auth", result.returncode == 0, "authenticated" if result.returncode == 0 else result.stderr.strip())


def check_repo() -> Check:
    try:
        data = gh_json(["repo", "view", REPO, "--json", "url,visibility"])
        return Check("GitHub repo", True, f"{data.get('url')} ({data.get('visibility')})")
    except RuntimeError as exc:
        return Check("GitHub repo", False, str(exc))


def check_workflows() -> list[Check]:
    result = run(["gh", "workflow", "list", "--repo", REPO])
    if result.returncode != 0:
        return [Check("Workflows", False, result.stderr.strip())]
    output = result.stdout
    return [
        Check("Workflow publicar", "Publicar en Blogger" in output and "active" in output, "publish-blogger.yml"),
        Check("Workflow email", "Publicar por Email" in output and "active" in output, "publish-email.yml"),
        Check("Workflow validar", "Validar generador" in output and "active" in output, "validate.yml"),
    ]


def check_secrets() -> list[Check]:
    result = run(["gh", "secret", "list", "--repo", REPO])
    if result.returncode != 0:
        return [Check("GitHub Secrets", False, result.stderr.strip())]
    present = {line.split()[0] for line in result.stdout.splitlines() if line.strip()}
    checks = [
        Check(f"Secret {name}", name in present, "present" if name in present else "missing")
        for name in sorted(REQUIRED_SECRETS)
    ]
    checks.extend(
        Check(f"Email secret {name}", name in present, "present" if name in present else "missing")
        for name in sorted(EMAIL_SECRETS)
    )
    checks.extend(
        Check(f"Secret {name}", name in present, "present" if name in present else "optional")
        for name in sorted(OPTIONAL_SECRETS)
    )
    return checks


def check_latest_runs() -> list[Check]:
    result = run(["gh", "run", "list", "--repo", REPO, "--limit", "5", "--json", "workflowName,conclusion,status,url"])
    if result.returncode != 0:
        return [Check("Workflow runs", False, result.stderr.strip())]
    runs = json.loads(result.stdout or "[]")
    checks: list[Check] = []
    for workflow in ["Validar generador", "Publicar en Blogger", "Publicar por Email"]:
        run_data = next((item for item in runs if item.get("workflowName") == workflow), None)
        if not run_data:
            checks.append(Check(f"Ultimo run {workflow}", False, "no runs yet"))
            continue
        ok = run_data.get("status") == "completed" and run_data.get("conclusion") == "success"
        detail = f"{run_data.get('status')}/{run_data.get('conclusion')} {run_data.get('url')}"
        checks.append(Check(f"Ultimo run {workflow}", ok, detail))
    return checks


def print_checks(checks: list[Check]) -> None:
    for check in checks:
        mark = "OK" if check.ok else "NO"
        print(f"[{mark}] {check.name}: {check.detail}")


def main() -> None:
    checks = [check_python(), check_gh_installed()]
    if checks[-1].ok:
        checks.append(check_gh_auth())
    if len(checks) >= 3 and checks[-1].ok:
        checks.append(check_repo())
        checks.extend(check_workflows())
        checks.extend(check_secrets())
        checks.extend(check_latest_runs())
    print_checks(checks)

    oauth_ready = all(
        check.ok for check in checks if check.name.startswith("Secret ") and check.name.removeprefix("Secret ") in REQUIRED_SECRETS
    )
    email_ready = all(
        check.ok for check in checks if check.name.startswith("Email secret ") and check.name.removeprefix("Email secret ") in EMAIL_SECRETS
    )
    if not oauth_ready and not email_ready:
        print("\nNext step:")
        print("Option A, no Google Cloud payment: configure Blogger Mail2Blogger + SMTP secrets.")
        print(
            "Option B, OAuth: C:\\Users\\malow\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe "
            "scripts\\setup_oauth.py --store-gh-secrets --run-workflow"
        )
        raise SystemExit(1)

    infrastructure_failure = [
        check
        for check in checks
        if not check.ok
        and not check.name.startswith("Secret ")
        and not check.name.startswith("Email secret ")
        and not check.name.startswith("Ultimo run Publicar")
    ]
    if infrastructure_failure:
        raise SystemExit(1)

    route = "OAuth Blogger API" if oauth_ready else "Mail2Blogger email"
    print(f"\nReady: required automation checks passed via {route}.")


if __name__ == "__main__":
    main()
