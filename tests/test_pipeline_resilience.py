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


class IssueDateTests(unittest.TestCase):
    """Regression: varje nummer daterades en vecka för tidigt (vecka 25–32)."""

    @classmethod
    def setUpClass(cls):
        import write
        cls.write = write

    def _date_line(self, week: str, year: int) -> str:
        prompt = self.write.build_prompt([], week, year, "")
        for line in prompt.splitlines():
            if line.startswith("date: "):
                return line.split("date: ", 1)[1].strip()
        raise AssertionError("ingen date-rad i prompten")

    def test_date_is_sunday_of_the_issue_week(self):
        self.assertEqual(self._date_line("2026-35", 2026), "2026-08-30")
        self.assertEqual(self._date_line("2026-34", 2026), "2026-08-23")
        self.assertEqual(self._date_line("2026-25", 2026), "2026-06-21")

    def test_date_does_not_depend_on_run_time(self):
        """En recovery-körning senare i veckan får inte flytta utgåvans datum."""
        first = self._date_line("2026-35", 2026)
        second = self._date_line("2026-35", 2026)
        self.assertEqual(first, second)
        self.assertEqual(first, date.fromisocalendar(2026, 35, 7).isoformat())


class MoltbookVisibilityTests(unittest.TestCase):
    """Regression vecka 35: verifierad post var spamflaggad och osynlig."""

    @classmethod
    def setUpClass(cls):
        cls.moltbook = load_moltbook_module()

    def test_spam_flagged_post_is_not_visible(self):
        with mock.patch.object(
            self.moltbook, "api_get",
            return_value={"post": {"verification_status": "verified", "is_spam": True}},
        ):
            visible, reason = self.moltbook.post_is_visible("abc")
        self.assertFalse(visible)
        self.assertIn("is_spam", reason)

    def test_verified_and_clean_post_is_visible(self):
        with mock.patch.object(
            self.moltbook, "api_get",
            return_value={"post": {"verification_status": "verified", "is_spam": False}},
        ):
            visible, _ = self.moltbook.post_is_visible("abc")
        self.assertTrue(visible)

    def test_pending_post_is_not_visible(self):
        with mock.patch.object(
            self.moltbook, "api_get",
            return_value={"post": {"verification_status": "pending", "is_spam": False}},
        ):
            visible, reason = self.moltbook.post_is_visible("abc")
        self.assertFalse(visible)
        self.assertIn("verification_status", reason)

    def test_already_published_ignores_hidden_post(self):
        search = {"results": [{"id": "abc", "title": "AI-Bladet Vecka 35 — x",
                               "author": {"name": "lutra_ai"}}]}

        def fake_get(path, query=None):
            if path == "/search":
                return search
            return {"post": {"verification_status": "verified", "is_spam": True}}

        with mock.patch.object(self.moltbook, "api_get", side_effect=fake_get):
            self.assertIsNone(self.moltbook.already_published("35"))

    def test_network_error_on_feed_is_not_treated_as_absent(self):
        with mock.patch.object(self.moltbook, "api_get", return_value=None):
            self.assertIsNone(self.moltbook.in_public_feed("abc"))


class MoltbookIsNotAPublishingGateTests(unittest.TestCase):
    """Vecka 35 tappade audio/meme/SeenDB för att Moltbook-felet gav exit 1."""

    def test_moltbook_failure_does_not_abort_distribution(self):
        runner = (PIPELINE / "run_weekly.sh").read_text()
        self.assertIn("MOLTBOOK_STATUS=$?", runner)
        self.assertNotIn(
            '|| { echo "❌ Moltbook-post eller verifiering misslyckades"; exit 1; }',
            runner,
        )

    def test_moltbook_failure_still_fails_the_run(self):
        runner = (PIPELINE / "run_weekly.sh").read_text()
        self.assertIn('if [ "${MOLTBOOK_STATUS:-0}" -ne 0 ]; then', runner)


class PodcastFeedTests(unittest.TestCase):
    """Enclosure-URL:erna pekade på aibladet.se, som inte serverar sajten."""

    def test_site_url_defaults_to_canonical_host(self):
        self.assertEqual(distribute_audio.SITE_URL, "https://ai-bladet.pages.dev")

    def test_published_feed_has_no_dead_host(self):
        feed = (PIPELINE.parent / "public" / "feed" / "podcast.xml").read_text()
        self.assertNotIn("aibladet.se", feed)


if __name__ == "__main__":
    unittest.main()
