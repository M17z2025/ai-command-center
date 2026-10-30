"""Offline safety and integration tests for approved free-tier inference."""

import json
import os
from unittest.mock import patch
import unittest

from sigma_runtime.free_tier import FreeTierModelProvider, free_tier_from_env
from sigma_runtime.provider import CompletionRequest, ModelProvider, ProviderError, provider_from_env


class StubPrimary(ModelProvider):
    def __init__(self):
        self.calls = 0

    def complete(self, request):
        self.calls += 1
        return "private-primary"


PUBLIC = {"data_classification": "public", "allow_free_tier": True}
ROUTE = {
    "name": "groq",
    "endpoint": "https://api.groq.com/openai/v1/chat/completions",
    "model": "llama-3.3-70b-versatile",
    "key_env": "SIGMA_FREE_LLM_KEY_GROQ",
    "max_requests_per_minute": 1,
    "max_requests_per_day": 2,
}


def settings(*, route=None, fallback=False):
    return {
        "SIGMA_FREE_LLM_ENABLED": "1",
        "SIGMA_FREE_LLM_ROUTES_JSON": json.dumps([route or ROUTE]),
        "SIGMA_FREE_LLM_KEY_GROQ": "test-secret-not-a-live-key",
        "SIGMA_FREE_LLM_ALLOW_PRIMARY_FALLBACK": "1" if fallback else "0",
    }


class FreeTierRoutingTests(unittest.TestCase):
    def test_disabled_uses_original_primary(self):
        primary = StubPrimary()
        with patch.dict(os.environ, {"SIGMA_FREE_LLM_ENABLED": "0"}):
            self.assertIs(free_tier_from_env(primary), primary)

    def test_public_opt_in_routes_but_private_and_critical_stay_primary(self):
        primary = StubPrimary()
        with patch.dict(os.environ, settings()):
            provider = free_tier_from_env(primary)
        self.assertIsInstance(provider, FreeTierModelProvider)
        with patch("sigma_runtime.free_tier.HTTPModelProvider.complete", return_value="free") as call:
            self.assertEqual(provider.complete(CompletionRequest("analysis", "safe", "public data", PUBLIC)), "free")
            self.assertEqual(provider.complete(CompletionRequest("analysis", "s", "private")), "private-primary")
            self.assertEqual(provider.complete(CompletionRequest("analysis", "s", "unclassified", {"allow_free_tier": True})), "private-primary")
            self.assertEqual(provider.complete(CompletionRequest("critic", "s", "high-risk", PUBLIC)), "private-primary")
        self.assertEqual(call.call_count, 1)
        self.assertEqual(primary.calls, 3)

    def test_per_process_rpm_limit_is_fail_closed(self):
        primary = StubPrimary()
        with patch.dict(os.environ, settings()):
            provider = free_tier_from_env(primary)
        with patch("sigma_runtime.free_tier.HTTPModelProvider.complete", return_value="free") as call:
            self.assertEqual(provider.complete(CompletionRequest("analysis", "", "public", PUBLIC)), "free")
            with self.assertRaisesRegex(ProviderError, "quota exhausted"):
                provider.complete(CompletionRequest("analysis", "", "public", PUBLIC))
        self.assertEqual(call.call_count, 1)
        self.assertEqual(primary.calls, 0)

    def test_failure_can_use_primary_only_if_explicit(self):
        primary = StubPrimary()
        with patch.dict(os.environ, settings(fallback=True)):
            provider = free_tier_from_env(primary)
        with patch("sigma_runtime.free_tier.HTTPModelProvider.complete", side_effect=ProviderError("key=secret upstream debug")):
            self.assertEqual(provider.complete(CompletionRequest("analysis", "", "public", PUBLIC)), "private-primary")
        self.assertEqual(primary.calls, 1)

    def test_free_provider_error_is_sanitized(self):
        primary = StubPrimary()
        with patch.dict(os.environ, settings()):
            provider = free_tier_from_env(primary)
        with patch("sigma_runtime.free_tier.HTTPModelProvider.complete", side_effect=ProviderError("SECRET")):
            with self.assertRaises(ProviderError) as ctx:
                provider.complete(CompletionRequest("analysis", "", "public", PUBLIC))
        self.assertNotIn("SECRET", str(ctx.exception))
        self.assertEqual(primary.calls, 0)

    def test_unapproved_host_or_missing_key_is_rejected(self):
        primary = StubPrimary()
        bad = dict(ROUTE, endpoint="https://private.example.com/v1/chat/completions")
        with patch.dict(os.environ, settings(route=bad)):
            with self.assertRaisesRegex(ProviderError, "approved HTTPS"):
                free_tier_from_env(primary)
        env = settings()
        env["SIGMA_FREE_LLM_KEY_GROQ"] = ""
        with patch.dict(os.environ, env):
            with self.assertRaisesRegex(ProviderError, "credential is missing"):
                free_tier_from_env(primary)

    def test_invalid_config_rejected(self):
        primary = StubPrimary()
        with patch.dict(os.environ, {"SIGMA_FREE_LLM_ENABLED": "1", "SIGMA_FREE_LLM_ROUTES_JSON": "not-json"}):
            with self.assertRaisesRegex(ProviderError, "Invalid"):
                free_tier_from_env(primary)

    def test_factory_opt_in_does_not_change_default_runtime(self):
        env = {
            "SIGMA_RUNTIME_PROVIDER": "http",
            "SIGMA_LLM_ENDPOINT": "http://ollama:11434/api/chat",
            "SIGMA_LLM_MODEL": "qwen2.5:7b",
            "SIGMA_LLM_PROTOCOL": "ollama-chat",
            **settings(),
        }
        with patch.dict(os.environ, env):
            self.assertIsInstance(provider_from_env(), FreeTierModelProvider)


if __name__ == "__main__":
    unittest.main()
