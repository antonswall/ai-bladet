import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


PIPELINE = Path(__file__).resolve().parents[1] / "pipeline"
sys.path.insert(0, str(PIPELINE))

import collect
import llm


def load_moltbook_module():
    spec = importlib.util.spec_from_file_location(
        "post_to_moltbook", PIPELINE / "post-to-moltbook.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class CollectionHealthTests(unittest.TestCase):
    def test_one_failed_source_is_degraded_success(self):
        self.assertTrue(collect.collection_is_healthy(32, 33, 331))

    def test_systemic_source_failure_is_fatal(self):
        self.assertFalse(collect.collection_is_healthy(10, 33, 331))

    def test_too_few_candidates_is_fatal(self):
        self.assertFalse(collect.collection_is_healthy(33, 33, 5))


class LlmFailureTests(unittest.TestCase):
    @mock.patch("llm.subprocess.run")
    def test_nonzero_codex_exit_never_becomes_model_output(self, run):
        run.return_value = subprocess.CompletedProcess(
            args=["codex"], returncode=1, stdout="fatal: auth failed", stderr="auth failed"
        )
        self.assertIsNone(llm.llm_call("test", timeout=1, attempts=1))


class MoltbookChallengeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_moltbook_module()

    def test_obfuscated_multiplication_from_week_30(self):
        challenge = (
            "A] LoOoObBsStTeErR^ ClLaAwW/ ExXeErRtTsS] ThHiIrRtTyY- "
            "FoOuUrR NoOoOtToOnNsS, AnNdD[ IiTt MuUlLtTiIpPlLiIeEsS\\ "
            "ByY> TwWoO, WhHaAtT IsS ThHeE PrRoOdDuUcCtT?"
        )
        self.assertEqual(self.module.solve_challenge(challenge), 68)

    def test_addition_and_subtraction(self):
        self.assertEqual(self.module.solve_challenge("twenty four speeds up by six"), 30)
        self.assertEqual(self.module.solve_challenge("forty slows by eleven"), 29)


class RunnerControlFlowTests(unittest.TestCase):
    def test_validation_failure_is_captured_despite_errexit(self):
        runner = (PIPELINE / "run_weekly.sh").read_text()
        self.assertIn("if python validate.py; then", runner)

    def test_failed_run_can_reuse_current_candidates(self):
        runner = (PIPELINE / "run_weekly.sh").read_text()
        self.assertIn("Återupptar från sparade kandidater", runner)


if __name__ == "__main__":
    unittest.main()
