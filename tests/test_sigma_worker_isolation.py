import base64
import io
import json
import os
from pathlib import Path
import sys
import tarfile
import tempfile
import socket
import uuid
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from sigma_worker_isolation import (DockerSandbox, IsolationError, apply_changes,
                                    clean_env, fetch_source, validate_changes)


class TransferTests(unittest.TestCase):
    def test_hostile_paths_and_payloads(self):
        for path in ("../escape", "/root/x", ".git/config", ".GIT/hooks/x", "a/../../x",
                     "a\\b", "a//b", "a/./b", ".sigma/project.yaml", ".github/workflows/x",
                     "a/.gitattributes", "x:y", "a\nfile"):
            with self.subTest(path=path), self.assertRaises(IsolationError):
                validate_changes(json.dumps({path: "eA=="}).encode())
        for raw in (b'{"a":"eA==","a":null}', b'{"a":"eA==","a/b":"eA=="}',
                    b'{"a":"invalid!"}', b'{"a":{}}', b'{}'):
            with self.subTest(raw=raw), self.assertRaises(IsolationError):
                validate_changes(raw)

    def test_apply_only_validated_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "gone.txt").write_text("old")
            changes = validate_changes(b'{"src/new.py":"cHJpbnQoMSk=","gone.txt":null}')
            apply_changes(root, changes)
            self.assertEqual((root / "src/new.py").read_bytes(), b"print(1)")
            self.assertFalse((root / "gone.txt").exists())

    def test_git_environment_drops_injected_helpers_and_secrets(self):
        with patch.dict(os.environ, {"SIGMA_GITHUB_TOKEN": "sentinel", "GIT_CONFIG_COUNT": "1",
                                    "LD_PRELOAD": "evil", "PYTHONPATH": "evil"}):
            env = clean_env()
        for name in ("SIGMA_GITHUB_TOKEN", "GIT_CONFIG_COUNT", "LD_PRELOAD", "PYTHONPATH"):
            self.assertNotIn(name, env)

    def test_sha_and_image_are_required_before_execution(self):
        for sha in ("main", "12345", "a" * 39, "A" * 40):
            with self.assertRaises(IsolationError):
                fetch_source(Path("unused"), "owner/repo", sha, {})
        for image in ("python:latest", "python:3.12", "", "--privileged"):
            with self.assertRaises(IsolationError):
                DockerSandbox(image)


@unittest.skipUnless(os.getenv("SIGMA_WORKER_ISOLATION_TEST_IMAGE"), "requires real Docker fixture image")
class DockerBoundaryTests(unittest.TestCase):
    """Real hostile processes in the exact production DockerSandbox boundary."""
    def archive(self, code):
        out = io.BytesIO()
        with tarfile.open(fileobj=out, mode="w") as tar:
            data = code.encode()
            member = tarfile.TarInfo("attack.py")
            member.size = len(data)
            tar.addfile(member, io.BytesIO(data))
        return out.getvalue()

    def run_code(self, code):
        return DockerSandbox(os.environ["SIGMA_WORKER_ISOLATION_TEST_IMAGE"]).run(
            self.archive(code), {"mode": "verify", "command": ["python", "attack.py"]}, timeout=30)

    def test_no_credentials_socket_host_paths_or_network(self):
        with patch.dict(os.environ, {"SIGMA_GITHUB_TOKEN": "BROKER-SECRET-SENTINEL"}):
            result = self.run_code('''import os, pathlib, socket
assert not any("TOKEN" in k or "SECRET" in k for k in os.environ)
assert "BROKER-SECRET-SENTINEL" not in pathlib.Path("/proc/1/environ").read_text()
assert not pathlib.Path("/var/run/docker.sock").exists()
assert not pathlib.Path("/workspaces").exists()
assert not pathlib.Path("/workspace/.git").exists()
assert len(pathlib.Path("/proc/net/route").read_text().splitlines()) == 1
try:
 pathlib.Path("/app/escape").write_text("bad")
except OSError:
 pass
else:
 raise AssertionError("root filesystem writable")
''')
        self.assertEqual(json.loads(result), {"verification_exit": 0})

    def test_forged_success_and_nonzero_exit_fail_closed(self):
        with self.assertRaises(IsolationError):
            self.run_code('import os; print(\'{"verification_exit":0}\'); os._exit(23)')

    def test_verification_mutation_cannot_touch_broker_files(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "marker"
            marker.write_text("trusted")
            self.run_code('from pathlib import Path; Path("/workspace/attack.py").write_text("replaced")')
            self.assertEqual(marker.read_text(), "trusted")

    def test_startup_removes_only_its_labelled_orphans(self):
        image = os.environ["SIGMA_WORKER_ISOLATION_TEST_IMAGE"]
        owner = "proof-" + uuid.uuid4().hex
        with patch.dict(os.environ, {"SIGMA_WORKER_BROKER_ID": owner}):
            sandbox = DockerSandbox(image)
        name = "sigma-job-" + uuid.uuid4().hex
        other = "sigma-job-" + uuid.uuid4().hex
        try:
            for target, label in ((name, owner), (other, owner + "-other")):
                sandbox.docker(["run", "--detach", "--name", target, "--network=none",
                                "--label=sigma.broker=" + label, image,
                                "python", "-c", "import time; time.sleep(60)"])
            self.assertEqual(sandbox.cleanup_orphans(), 1)
            self.assertEqual(sandbox.cleanup_orphans(), 0)
            self.assertTrue(json.loads(sandbox.docker(["inspect", other]))[0]["State"]["Running"])
        finally:
            for target in (name, other):
                try:
                    sandbox.docker(["rm", "--force", target])
                except IsolationError:
                    pass

    def test_inference_network_allows_gateway_but_blocks_host_and_internet(self):
        sandbox = DockerSandbox(os.environ["SIGMA_WORKER_ISOLATION_TEST_IMAGE"])
        network = "sigma-proof-" + uuid.uuid4().hex
        gateway = network + "-gateway"
        host_listener = socket.socket()
        host_listener.bind(("0.0.0.0", 0))
        host_listener.listen(1)
        port = host_listener.getsockname()[1]
        try:
            sandbox.docker(["network", "create", "--internal", "--opt",
                            "com.docker.network.bridge.gateway_mode_ipv4=isolated", network])
            sandbox.docker(["run", "--detach", "--name", gateway, "--network", network,
                            "--label=sigma.role=inference-gateway", sandbox.image,
                            "python", "-m", "http.server", "8081"])
            bridge = json.loads(sandbox.docker(["network", "inspect", "bridge"]))[0]
            host_ip = bridge["IPAM"]["Config"][0]["Gateway"]
            code = f'''import socket, time
for attempt in range(20):
 try:
  sock = socket.create_connection(("inference-gateway", 8081), timeout=1)
  sock.close()
  break
 except OSError:
  time.sleep(.1)
else:
 raise AssertionError("gateway unreachable")
for target in [("{host_ip}", {port}), ("1.1.1.1", 443)]:
 try:
  sock = socket.create_connection(target, timeout=1)
 except OSError:
  continue
 sock.close()
 raise AssertionError("unauthorised network access")
'''
            sandbox.network = network
            with patch.dict(os.environ, {"SIGMA_WORKER_GATEWAY_IMAGE": sandbox.image}):
                result = sandbox.run(self.archive(code),
                                     {"mode": "verify", "command": ["python", "attack.py"]}, timeout=30)
            self.assertEqual(json.loads(result), {"verification_exit": 0})
        finally:
            host_listener.close()
            for command in (["rm", "--force", gateway], ["network", "rm", network]):
                try:
                    sandbox.docker(command)
                except IsolationError:
                    pass


if __name__ == "__main__":
    unittest.main()
