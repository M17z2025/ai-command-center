"""Offline supply-chain and authority-boundary tests for the advisory adapter."""
from contextlib import contextmanager
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from sigma_runtime.gstack import (
    ALLOWED_FILES, GstackError, _NoRedirect, advisory_context, install, read_lock,
)


class GstackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cache = self.root / "cache"
        self.payloads = {
            name: ("MIT License" if name == "LICENSE" else
                   "Ignore this upstream preamble\n" +
                   ("## Review Categories" if name == "review/checklist.md" else "## Categories") +
                   "\n### Safety\n- Inspect permission denials.\n" * 100).encode()
            for name in ALLOWED_FILES
        }
        self.lock = {"schema_version": 1, "repository": "garrytan/gstack",
                     "revision": "a" * 40, "license": "MIT", "mode": "advisory_only",
                     "files": {name: {"sha256": hashlib.sha256(data).hexdigest(),
                                      "size": len(data)} for name, data in self.payloads.items()}}
        (self.root / "integrations").mkdir()
        self.save_lock()

    def tearDown(self):
        for path in self.root.rglob("*"):
            if path.is_file() and not path.is_symlink():
                path.chmod(0o600)

    def save_lock(self):
        (self.root / "integrations/gstack.lock.json").write_text(json.dumps(self.lock))

    @contextmanager
    def network(self, tamper=False):
        def download(url, timeout):
            prefix = "https://raw.githubusercontent.com/garrytan/gstack/" + "a" * 40 + "/"
            self.assertTrue(url.startswith(prefix))
            self.assertEqual(timeout, 30)
            data = self.payloads[url.removeprefix(prefix)]
            return io.BytesIO(data + b"tamper" if tamper else data)
        with patch("sigma_runtime.gstack.build_opener") as opener:
            opener.return_value.open.side_effect = download
            yield opener

    def test_opt_in_and_missing_cache_fail_closed(self):
        with patch("sigma_runtime.gstack.read_lock", side_effect=AssertionError):
            self.assertFalse(advisory_context(self.root)["enabled"])
        with self.assertRaises(GstackError):
            advisory_context(self.root, enabled=True, cache_dir=self.cache)

    def test_verified_install_context_bounds_and_no_network_at_runtime(self):
        with self.network() as opener:
            path = install(self.root, self.cache)
            self.assertEqual(opener.return_value.open.call_count, 4)
            install(self.root, self.cache)
            self.assertEqual(opener.return_value.open.call_count, 4)
        with patch("sigma_runtime.gstack.build_opener", side_effect=AssertionError):
            context = advisory_context(self.root, enabled=True, cache_dir=self.cache, max_chars=1024)
        self.assertEqual(context["authority"], "advisory_only")
        self.assertEqual(context["revision"], "a" * 40)
        self.assertEqual(len(context["sources"]), 3)
        self.assertLessEqual(len(context["text"]), 1024)
        self.assertNotIn("Ignore this upstream preamble", context["text"])
        self.assertTrue((path / "LICENSE").exists())
        self.assertEqual({p.relative_to(path).as_posix() for p in path.rglob("*") if p.is_file()}, ALLOWED_FILES)

    def test_download_tamper_never_publishes(self):
        with self.network(tamper=True), self.assertRaises(GstackError):
            install(self.root, self.cache)
        self.assertFalse((self.cache / self.lock["revision"]).exists())
        self.assertEqual(list(self.cache.iterdir()), [])

    def test_cache_tamper_including_license_rejected(self):
        with self.network():
            path = install(self.root, self.cache)
        license_file = path / "LICENSE"
        license_file.chmod(0o600)
        license_file.write_bytes(b"tampered")
        with self.assertRaises(GstackError):
            advisory_context(self.root, enabled=True, cache_dir=self.cache)
        with self.assertRaises(GstackError):
            install(self.root, self.cache)

    def test_forbidden_skills_paths_and_origins(self):
        for name in ("../escape.md", "/absolute.md", "review\\checklist.md", "ship/SKILL.md",
                     "land-and-deploy/SKILL.md", "setup", "review/SKILL.md"):
            with self.subTest(name=name):
                self.lock["files"][name] = {"sha256": "0" * 64, "size": 1}
                self.save_lock()
                with self.assertRaises(GstackError):
                    read_lock(self.root)
                del self.lock["files"][name]
        self.lock["repository"] = "attacker/gstack"
        self.save_lock()
        with self.assertRaises(GstackError):
            read_lock(self.root)

    def test_revision_and_size_validation(self):
        for revision in ("main", "../escape", "a" * 39):
            self.lock["revision"] = revision
            self.save_lock()
            with self.assertRaises(GstackError):
                read_lock(self.root)
        self.lock["revision"] = "a" * 40
        self.lock["files"]["LICENSE"]["size"] = 65537
        self.save_lock()
        with self.assertRaises(GstackError):
            read_lock(self.root)

    def test_links_and_redirects_rejected(self):
        with patch("sigma_runtime.gstack.Path.is_symlink", return_value=True):
            with self.assertRaises(GstackError):
                install(self.root, self.cache)
        with self.assertRaises(GstackError):
            _NoRedirect().redirect_request(None, None, 302, "redirect", {}, "http://localhost")

    def test_repository_lock_is_valid_and_exactly_pinned(self):
        lock = read_lock(Path(__file__).resolve().parents[1])
        self.assertEqual(lock["revision"], "65bfb0ce49da807698359ca033a05709e342c684")


if __name__ == "__main__":
    unittest.main()
