"""Real HTTP input tests against the production inference gateway Handler."""
from http.client import HTTPConnection
from http.server import HTTPServer
import io
import json
import os
from pathlib import Path
import socket
import sys
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import sigma_worker_inference_gateway as gateway


class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.server = HTTPServer(("127.0.0.1", 0), gateway.Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def request(self, path, payload, headers=None):
        connection = HTTPConnection(*self.server.server_address, timeout=2)
        try:
            connection.request("POST", path, json.dumps(payload), headers or {})
            response = connection.getresponse()
            response.read()
            return response.status
        finally:
            connection.close()

    def test_forbidden_paths_models_framing_and_non_objects(self):
        with patch.dict(os.environ, {"SIGMA_GATEWAY_MODEL": "approved"}), patch.object(gateway, "build_opener") as opener:
            self.assertEqual(self.request("/api/pull", {"model": "approved"}), 403)
            self.assertEqual(self.request("/api/chat", {"model": "other"}), 502)
            self.assertEqual(self.request("/api/chat", []), 502)
            self.assertEqual(self.request("/api/chat", {"model": "approved"}, {"Transfer-Encoding": "chunked"}), 502)
            opener.assert_not_called()

    def test_untrusted_model_resource_options_are_replaced(self):
        observed = []
        class Upstream:
            def open(self, request, timeout):
                observed.append((request.full_url, json.loads(request.data), timeout))
                return io.BytesIO(b'{"done":true}')
        with patch.dict(os.environ, {"SIGMA_GATEWAY_MODEL": "approved"}), patch.object(gateway, "build_opener", return_value=Upstream()):
            self.assertEqual(self.request("/api/chat", {"model": "approved", "stream": True,
                             "options": {"num_ctx": 999999999, "num_predict": -1}, "keep_alive": -1}), 200)
        url, payload, timeout = observed[0]
        self.assertEqual(url, "http://ollama:11434/api/chat")
        self.assertEqual(payload["options"], {"num_ctx": 8192, "num_predict": 4096})
        self.assertEqual(payload["keep_alive"], "5m")
        self.assertIs(payload["stream"], False)
        self.assertEqual(timeout, 300)

    def test_incomplete_body_times_out_and_releases_single_request_server(self):
        with patch.object(gateway, "BODY_TIMEOUT", .1):
            with socket.create_connection(self.server.server_address, timeout=2) as connection:
                connection.sendall(b"POST /api/chat HTTP/1.1\r\nHost: local\r\nContent-Length: 100\r\n\r\n{")
                self.assertIn(b"502", connection.recv(4096))
        self.assertEqual(self.request("/api/pull", {}), 403)

    def test_incomplete_headers_cannot_hold_the_single_request_server(self):
        with patch.object(gateway, "BODY_TIMEOUT", .1):
            with socket.create_connection(self.server.server_address, timeout=2) as connection:
                connection.sendall(b"POST /api/chat HTTP/1.1\r\nHost: local")
                self.assertEqual(connection.recv(4096), b"")
        self.assertEqual(self.request("/api/pull", {}), 403)


if __name__ == "__main__":
    unittest.main()
