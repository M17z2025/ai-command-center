"""Offline wire-contract proof for OpenJarvis's OpenAI-compatible chat endpoint.

This checks Sigma's ACTUAL HTTPModelProvider using a local synthetic server.
It does not install OpenJarvis, commission a model or prove an Android release.
"""
from __future__ import annotations

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

from sigma_runtime.provider import CompletionRequest, HTTPModelProvider, ProviderError


class _OpenJarvisContractFixture(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):  # noqa: ANN002
        """Never log prompts or authentication material."""
        pass

    def _send(self, status, value):
        raw = json.dumps(value).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", "0"))
        if n < 1 or n > 8192:
            self._send(413, {"detail": "invalid length"})
            return
        body = self.rfile.read(n)
        try:
            request = json.loads(body)
        except (ValueError, UnicodeDecodeError):
            self._send(400, {"detail": "invalid json"})
            return
        self.server.observed.append({
            "path": self.path,
            "authorization": self.headers.get("Authorization"),
            "payload": request,
        })
        if self.path != "/v1/chat/completions":
            self._send(404, {"detail": "unknown route"})
        elif self.headers.get("Authorization") != "Bearer synthetic-test-token":
            self._send(401, {"detail": "invalid key"})
        elif self.server.test_mode == "busy":
            self._send(503, {"detail": "model unavailable"})
        elif self.server.test_mode == "malformed":
            self._send(200, {"choices": [{"message": {"unexpected": "field"}}]})
        else:
            self._send(200, {"model": "test-model", "choices": [
                {"message": {"role": "assistant", "content": "Synthetic answer."}}
            ]})


class OpenJarvisSigmaContractTests(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), _OpenJarvisContractFixture)
        self.server.daemon_threads = True
        self.server.observed = []
        self.server.test_mode = "ok"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.endpoint = "http://127.0.0.1:%s/v1/chat/completions" % self.server.server_port

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

    def _provider(self, *, token="synthetic-test-token", path=None):
        return HTTPModelProvider(
            endpoint=path or self.endpoint, model="test-model",
            api_key=token, protocol="chat-completions", timeout=2,
        )

    def _completion(self, provider):
        return provider.complete(CompletionRequest(
            kind="analysis",
            system="Give a brief response without tools.",
            user="Check the read-only contract.",
        ))

    def test_real_http_wire_contract_with_bearer_token(self):
        self.assertEqual(self._completion(self._provider()), "Synthetic answer.")
        observed = self.server.observed
        self.assertEqual(len(observed), 1)
        self.assertEqual(observed[0]["path"], "/v1/chat/completions")
        self.assertEqual(observed[0]["authorization"], "Bearer synthetic-test-token")
        payload = observed[0]["payload"]
        self.assertEqual(payload["model"], "test-model")
        self.assertEqual([m["role"] for m in payload["messages"]], ["system", "user"])
        self.assertEqual(payload["messages"][1]["content"], "Check the read-only contract.")
        self.assertNotIn("tools", payload)
        self.assertNotIn("stream", payload)

    def test_missing_or_invalid_auth_is_rejected(self):
        for token in (None, "wrong-test-token"):
            with self.subTest(token=token):
                with self.assertRaisesRegex(ProviderError, "HTTP 401"):
                    self._completion(self._provider(token=token))

    def test_missing_route_fails_closed(self):
        other = self.endpoint.replace("/v1/chat/completions", "/wrong")
        with self.assertRaisesRegex(ProviderError, "HTTP 404"):
            self._completion(self._provider(path=other))

    def test_upstream_unavailable_fails_closed(self):
        self.server.test_mode = "busy"
        with self.assertRaisesRegex(ProviderError, "HTTP 503"):
            self._completion(self._provider())

    def test_unrecognised_response_is_not_a_success(self):
        self.server.test_mode = "malformed"
        with self.assertRaisesRegex(ProviderError, "Unrecognized model response shape"):
            self._completion(self._provider())

    def test_timeout_is_not_a_completed_action(self):
        with patch("sigma_runtime.provider.urlopen", side_effect=TimeoutError("synthetic")):
            with self.assertRaisesRegex(ProviderError, "Model endpoint failed"):
                self._completion(self._provider())


if __name__ == "__main__":
    unittest.main()
