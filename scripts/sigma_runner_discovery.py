#!/usr/bin/env python3
"""Read-only discovery for Sigma managed repositories.

This phase intentionally gathers evidence only. It never mutates GitHub.
"""

from __future__ import annotations

import argparse
import base64
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, build_opener

import yaml

API_ROOT = "https://api.github.com"


class GitHubAPIError(RuntimeError):
    """GitHub API request failed."""

    def __init__(self, status: int | None, message: str):
        super().__init__(message)
        self.status = status


class GitHubReadClient:
    """Minimal GitHub REST client with a hard read-only method boundary."""

    def __init__(
        self,
        token: str | None = None,
        api_root: str = API_ROOT,
        opener: Any | None = None,
    ) -> None:
        self.token = token
        self.api_root = api_root.rstrip("/")
        self.opener = opener or build_opener()

    def _request_json(self, method: str, endpoint: str) -> Any:
        if method.upper() != "GET":
            raise PermissionError(
                f"Sigma runner discovery is read-only; refused HTTP {method.upper()}"
            )

        url = f"{self.api_root}{endpoint}"
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "sigma-command-center-readonly-discovery",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        request = Request(url, headers=headers, method="GET")
        try:
            with self.opener.open(request, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            try:
                detail = exc.read().decode("utf-8", errors="replace")
            except Exception:
                detail = ""
            raise GitHubAPIError(
                exc.code, f"GitHub GET {endpoint} failed with HTTP {exc.code}: {detail[:300]}"
            ) from exc
        except URLError as exc:
            raise GitHubAPIError(None, f"GitHub GET {endpoint} failed: {exc.reason}") from exc

    def repository(self, repository: str) -> dict[str, Any]:
        return self._request_json("GET", f"/repos/{repository}")

    def file_exists(self, repository: str, path: str, ref: str) -> bool:
        encoded_path = quote(path, safe="/")
        query = urlencode({"ref": ref})
        try:
            payload = self._request_json(
                "GET", f"/repos/{repository}/contents/{encoded_path}?{query}"
            )
            return bool(payload)
        except GitHubAPIError as exc:
            if exc.status == 404:
                return False
            raise

    def file_text(self, repository: str, path: str, ref: str) -> str | None:
        encoded_path = quote(path, safe="/")
        query = urlencode({"ref": ref})
        try:
            payload = self._request_json(
                "GET", f"/repos/{repository}/contents/{encoded_path}?{query}"
            )
        except GitHubAPIError as exc:
            if exc.status == 404:
                return None
            raise

        if payload.get("encoding") != "base64" or "content" not in payload:
            raise GitHubAPIError(None, f"Unsupported GitHub contents payload for {path}")
        return base64.b64decode(payload["content"]).decode("utf-8")

    def open_count(self, repository: str, kind: str) -> int:
        if kind not in {"issue", "pr"}:
            raise ValueError(f"Unsupported GitHub search kind: {kind}")
        query = urlencode(
            {"q": f"repo:{repository} is:{kind} is:open", "per_page": 1}
        )
        payload = self._request_json("GET", f"/search/issues?{query}")
        return int(payload.get("total_count", 0))

    def latest_commit(self, repository: str) -> dict[str, Any] | None:
        payload = self._request_json("GET", f"/repos/{repository}/commits?per_page=1")
        if not payload:
            return None
        item = payload[0]
        commit = item.get("commit", {})
        return {
            "sha": item.get("sha"),
            "message": commit.get("message"),
            "date": commit.get("committer", {}).get("date"),
        }


@dataclass
class RepositoryDiscovery:
    repository: str
    lifecycle: str | None
    category: str | None
    accessible: bool = False
    default_branch: str | None = None
    manifest_present: bool | None = None
    status_present: bool | None = None
    open_issues: int | None = None
    open_prs: int | None = None
    latest_commit_sha: str | None = None
    latest_commit_message: str | None = None
    latest_commit_date: str | None = None
    discovery_state: str = "UNKNOWN"
    blockers: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def load_registry(path: Path) -> list[dict[str, Any]]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    projects = payload.get("projects", [])
    if not isinstance(projects, list):
        raise ValueError("projects/registry.yaml must contain a projects list")

    for index, project in enumerate(projects):
        repository = project.get("repository")
        if not repository or "/" not in repository:
            raise ValueError(f"projects[{index}] has invalid repository: {repository!r}")
    return projects


def discover_repository(
    client: GitHubReadClient, project: dict[str, Any]
) -> RepositoryDiscovery:
    repository = project["repository"]
    result = RepositoryDiscovery(
        repository=repository,
        lifecycle=project.get("lifecycle"),
        category=project.get("category"),
    )

    try:
        metadata = client.repository(repository)
    except GitHubAPIError as exc:
        result.discovery_state = "INACCESSIBLE"
        result.blockers.append(
            f"Repository metadata inaccessible"
            + (f" (HTTP {exc.status})" if exc.status else "")
        )
        result.errors.append(str(exc))
        return result

    result.accessible = True
    result.default_branch = metadata.get("default_branch") or "main"

    for attr, path in (
        ("manifest_present", ".sigma/project.yaml"),
        ("status_present", "PROJECT_STATUS.md"),
    ):
        try:
            setattr(
                result,
                attr,
                client.file_exists(repository, path, result.default_branch),
            )
        except GitHubAPIError as exc:
            result.errors.append(str(exc))

    try:
        result.open_issues = client.open_count(repository, "issue")
    except (GitHubAPIError, ValueError) as exc:
        result.errors.append(str(exc))

    try:
        result.open_prs = client.open_count(repository, "pr")
    except (GitHubAPIError, ValueError) as exc:
        result.errors.append(str(exc))

    try:
        latest = client.latest_commit(repository)
        if latest:
            result.latest_commit_sha = latest.get("sha")
            result.latest_commit_message = latest.get("message")
            result.latest_commit_date = latest.get("date")
    except GitHubAPIError as exc:
        result.errors.append(str(exc))

    if result.manifest_present is False or result.status_present is False:
        result.discovery_state = "CONTRACT_GAP"
        if result.manifest_present is False:
            result.blockers.append("Missing .sigma/project.yaml")
        if result.status_present is False:
            result.blockers.append("Missing PROJECT_STATUS.md")
    elif result.errors:
        result.discovery_state = "PARTIAL"
    else:
        result.discovery_state = "DISCOVERED"

    return result


def build_report(
    registry_path: Path,
    discoveries: list[RepositoryDiscovery],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "read-only-discovery",
        "registry": str(registry_path),
        "summary": {
            "repositories": len(discoveries),
            "accessible": sum(1 for item in discoveries if item.accessible),
            "inaccessible": sum(1 for item in discoveries if not item.accessible),
            "contract_gaps": sum(
                1 for item in discoveries if item.discovery_state == "CONTRACT_GAP"
            ),
            "partial": sum(
                1 for item in discoveries if item.discovery_state == "PARTIAL"
            ),
        },
        "repositories": [asdict(item) for item in discoveries],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Sigma Runner Read-Only Discovery",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "> Discovery evidence only. This report is not a product readiness, deployment, security or Sigma User Tester certification.",
        "",
        "| Repository | State | Manifest | Status | Open issues | Open PRs | Latest commit |",
        "| --- | --- | --- | --- | ---: | ---: | --- |",
    ]

    for item in report["repositories"]:
        sha = item["latest_commit_sha"]
        latest = sha[:10] if sha else "—"
        lines.append(
            "| {repository} | {state} | {manifest} | {status} | {issues} | {prs} | {latest} |".format(
                repository=item["repository"],
                state=item["discovery_state"],
                manifest=_bool_mark(item["manifest_present"]),
                status=_bool_mark(item["status_present"]),
                issues=_number_mark(item["open_issues"]),
                prs=_number_mark(item["open_prs"]),
                latest=latest,
            )
        )

    blocked = [
        item for item in report["repositories"] if item["blockers"] or item["errors"]
    ]
    if blocked:
        lines.extend(["", "## Blockers / partial evidence", ""])
        for item in blocked:
            details = item["blockers"] + item["errors"]
            lines.append(f"- **{item['repository']}**: {'; '.join(details)}")

    return "\n".join(lines) + "\n"


def _bool_mark(value: bool | None) -> str:
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return "unknown"


def _number_mark(value: int | None) -> str:
    return str(value) if value is not None else "—"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gather read-only GitHub evidence for Sigma-managed repositories."
    )
    parser.add_argument("--registry", default="projects/registry.yaml")
    parser.add_argument(
        "--repository",
        action="append",
        dest="repositories",
        help="Limit discovery to an exact owner/repo from the registry. Repeatable.",
    )
    parser.add_argument(
        "--json-output", default="artifacts/sigma-runner-discovery.json"
    )
    parser.add_argument(
        "--markdown-output", default="artifacts/sigma-runner-discovery.md"
    )
    parser.add_argument("--api-root", default=API_ROOT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    registry_path = Path(args.registry)
    projects = load_registry(registry_path)

    if args.repositories:
        selected = set(args.repositories)
        known = {project["repository"] for project in projects}
        unknown = sorted(selected - known)
        if unknown:
            raise SystemExit(
                "Requested repository is not in registry: " + ", ".join(unknown)
            )
        projects = [
            project for project in projects if project["repository"] in selected
        ]

    token = os.getenv("SIGMA_GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN")
    client = GitHubReadClient(token=token, api_root=args.api_root)
    discoveries = [discover_repository(client, project) for project in projects]
    report = build_report(registry_path, discoveries)

    json_path = Path(args.json_output)
    markdown_path = Path(args.markdown_output)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)

    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")

    print(
        "Sigma read-only discovery complete: "
        f"{report['summary']['accessible']}/{report['summary']['repositories']} accessible"
    )
    print(f"JSON: {json_path}")
    print(f"Markdown: {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
