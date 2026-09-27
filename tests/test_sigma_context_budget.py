import json
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


class ContextBudgetTests(unittest.TestCase):
    def test_native_ollama_request_is_bounded_to_context_window(self):
        captured = {}
        def fake_urlopen(req, timeout):
            captured["payload"] = json.loads(req.data.decode("utf-8"))
            return _FakeResponse({"message": {"content": "OK"}})

        provider = HTTPModelProvider(
            endpoint="http://ollama:11434/api/chat",
            model="qwen3:4b-instruct",
            protocol="ollama-chat",
            context_tokens=4096,
            max_tokens=512,
            disable_thinking=True,
        )
        huge_user = "X" * 50000
        with patch("sigma_runtime.provider.urlopen", fake_urlopen):
            result = provider.complete(
                CompletionRequest("repair", "SYSTEM", huge_user, {"max_tokens": 384})
            )
        self.assertEqual(result, "OK")
        payload = captured["payload"]
        total_chars = sum(len(m["content"]) for m in payload["messages"])
        # Conservative 3 chars/token, with output + 512 token reserve.
        self.assertLessEqual(total_chars, (4096 - 384 - 512) * 3)
        self.assertEqual(payload["options"]["num_ctx"], 4096)
        self.assertEqual(payload["options"]["num_predict"], 384)


if __name__ == "__main__":
    unittest.main()
