import importlib.util
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

PIPELINE = Path(__file__).resolve().parents[1] / "pipeline"
sys.path.insert(0, str(PIPELINE))


def load(name):
    spec = importlib.util.spec_from_file_location("paid_guard_" + name, PIPELINE / (name + ".py"))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PaidApiOptInTests(unittest.TestCase):
    def test_configured_key_does_not_authorize_openrouter(self):
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}, clear=True):
            for name, getter in [("llm", "_get_openrouter_api_key"), ("write", "_get_openrouter_key")]:
                with self.subTest(module=name):
                    self.assertFalse(getattr(load(name), getter)())

    def test_explicit_opt_in_allows_configured_key(self):
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key", "AI_BLADET_ALLOW_OPENROUTER": "1"}, clear=True):
            for name, getter in [("llm", "_get_openrouter_api_key"), ("write", "_get_openrouter_key")]:
                with self.subTest(module=name):
                    self.assertEqual(getattr(load(name), getter)(), "test-key")
