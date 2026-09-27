import json
import os
from unittest.mock import patch
import unittest

from sigma_runtime.provider import CompletionRequest, HTTPModelProvider


class _FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class NativeOllamaProviderTests(unittest.TestCase):
    def test_native_ollama_payload_disables_thinking_and_bounds_generation(self):
        captured = {}

        def fake_urlopen(req, timeout):
            captured["timeout"] = timeout
            captured["payload"] = json.loads(req.data.decode("utf-8"))
            return _FakeResponse({"message": {"content": "OK"}})

        provider = HTTPModelProvider(
            endpoint="http://ollama:11434/api/chat",
            model="qwen3:4b-instruct",
            protocol="ollama-chat",
            timeout=300,
            max_tokens=512,
            context_tokens=4096,
            disable_thinking=True,
        )
        with patch("sigma_runtime.provider.urlopen", fake_urlopen):
            result = provider.complete(
                CompletionRequest("analysis", "system", "user")
            )

        self.assertEqual(result, "OK")
        self.assertEqual(captured["timeout"], 300)
        self.assertFalse(captured["payload"]["think"])
        self.assertFalse(captured["payload"]["stream"])
        self.assertEqual(captured["payload"]["options"]["num_predict"], 512)
        self.assertEqual(captured["payload"]["options"]["num_ctx"], 4096)

    def test_invalid_protocol_is_rejected(self):
        with self.assertRaises(Exception):
            HTTPModelProvider(
                endpoint="http://localhost",
                model="x",
                protocol="not-valid",
            )


if __name__ == "__main__":
    unittest.main()
