import importlib.util
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock


PIPELINE = Path(__file__).resolve().parents[1] / "pipeline"
sys.path.insert(0, str(PIPELINE))

import collect
import distribute_audio
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

    def test_snaps_times_multiplication(self):
        challenge = "A ClAw ExErTs ThIrTy FoUr NoOtOnS and snaps TwO times"
        self.assertEqual(self.module.solve_challenge(challenge), 68)

    def test_week_34_split_tens_multiplied_by(self):
        challenge = "Thirty five multiplied by two"
        self.assertEqual(self.module.solve_challenge(challenge), 70)

    def test_unknown_operator_fails_closed(self):
        with self.assertRaises(ValueError):
            self.module.solve_challenge("twenty four lobsters near six buoys")

    def test_week_31_recovery_challenge(self):
        challenge = (
            "A] Lo^OoB-StEr | ClAw Ex/ErTs TwEnTy ThReE NoOtOnS, "
            "AnD AnOtHeR ClAw Ex\\ErTs SeVeN NoOtOnS ~ WhAt'S ThE ToTaL FoRcE?"
        )
        self.assertEqual(self.module.solve_challenge(challenge), 30)

    def test_decimal_number(self):
        challenge = "A lobster moves at two point five meters and speeds up by three"
        self.assertEqual(self.module.solve_challenge(challenge), 5.5)

    def test_addition_and_subtraction(self):
        self.assertEqual(self.module.solve_challenge("twenty four speeds up by six"), 30)
        self.assertEqual(self.module.solve_challenge("forty slows by eleven"), 29)


class AudioDistributionTests(unittest.TestCase):
    def test_yaml_date_object_is_normalized_for_rss(self):
        self.assertEqual(
            distribute_audio.normalize_date(date(2026, 7, 26)),
            "2026-07-26",
        )

    def test_audio_duration_is_valid_itunes_format(self):
        self.assertEqual(distribute_audio.format_duration(90), "00:01:30")


class RunnerControlFlowTests(unittest.TestCase):
    def test_validation_failure_is_captured_despite_errexit(self):
        runner = (PIPELINE / "run_weekly.sh").read_text()
        self.assertIn("if python validate.py; then", runner)

    def test_failed_run_can_reuse_current_candidates(self):
        runner = (PIPELINE / "run_weekly.sh").read_text()
        self.assertIn("Återupptar från sparade kandidater", runner)

    def test_distribution_requires_all_modules(self):
        distributor = (PIPELINE / "distribute.py").read_text()
        self.assertIn("successes == total", distributor)

    def test_distribution_preserves_stderr_on_failure(self):
        distributor = (PIPELINE / "distribute.py").read_text()
        self.assertIn("result.stdout", distributor)
        self.assertIn("result.stderr", distributor)


if __name__ == "__main__":
    unittest.main()
