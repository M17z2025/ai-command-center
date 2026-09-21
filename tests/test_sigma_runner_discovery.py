import json
from pathlib import Path
import tempfile
import unittest

from scripts.sigma_runner_discovery import (
    GitHubAPIError,
    GitHubReadClient,
    build_report,
    discover_repository,
    load_registry,
    render_markdown,
)


class NeverOpen:
    def open(self, request, timeout=20):
        raise AssertionError("network must not be reached")


class FakeClient:
    def __init__(self, *, accessible=True, manifest=True, status=True):
        self.accessible = accessible
        self.manifest = manifest
        self.status = status

    def repository(self, repository):
        if not self.accessible:
            raise GitHubAPIError(403, "forbidden")
        return {"default_branch": "main"}

    def file_exists(self, repository, path, ref):
        if path == ".sigma/project.yaml":
            return self.manifest
        if path == "PROJECT_STATUS.md":
            return self.status
        raise AssertionError(path)

    def open_count(self, repository, kind):
        return 4 if kind == "issue" else 2

    def latest_commit(self, repository):
        return {
            "sha": "abcdef1234567890",
            "message": "test commit",
            "date": "2026-09-21T12:00:00Z",
        }


class RunnerDiscoveryTests(unittest.TestCase):
    def test_read_client_refuses_non_get_before_network(self):
        client = GitHubReadClient(opener=NeverOpen())
        with self.assertRaises(PermissionError):
            client._request_json("POST", "/repos/example/repo/issues")

    def test_load_registry_reads_projects(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "registry.yaml"
            path.write_text(
                "projects:\n"
                "  - name: Example\n"
                "    repository: owner/repo\n"
                "    lifecycle: active\n"
                "    category: product\n",
                encoding="utf-8",
            )
            projects = load_registry(path)
            self.assertEqual(projects[0]["repository"], "owner/repo")

    def test_load_registry_rejects_invalid_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "registry.yaml"
            path.write_text(
                "projects:\n  - name: Broken\n    repository: invalid\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                load_registry(path)

    def test_discovery_records_contract_gap_without_guessing(self):
        project = {
            "repository": "owner/repo",
            "lifecycle": "active",
            "category": "product",
        }
        result = discover_repository(
            FakeClient(manifest=False, status=True),
            project,
        )
        self.assertTrue(result.accessible)
        self.assertEqual(result.discovery_state, "CONTRACT_GAP")
        self.assertFalse(result.manifest_present)
        self.assertIn("Missing .sigma/project.yaml", result.blockers)
        self.assertEqual(result.open_issues, 4)
        self.assertEqual(result.open_prs, 2)

    def test_discovery_marks_inaccessible_repository(self):
        project = {
            "repository": "owner/private",
            "lifecycle": "active",
            "category": "product",
        }
        result = discover_repository(FakeClient(accessible=False), project)
        self.assertFalse(result.accessible)
        self.assertEqual(result.discovery_state, "INACCESSIBLE")
        self.assertIsNone(result.manifest_present)
        self.assertTrue(result.blockers)

    def test_report_is_explicitly_discovery_only(self):
        project = {
            "repository": "owner/repo",
            "lifecycle": "active",
            "category": "product",
        }
        discovery = discover_repository(FakeClient(), project)
        report = build_report(Path("projects/registry.yaml"), [discovery])
        markdown = render_markdown(report)
        self.assertEqual(report["mode"], "read-only-discovery")
        self.assertIn("not a product readiness", markdown)
        self.assertIn("owner/repo", markdown)


if __name__ == "__main__":
    unittest.main()
