import importlib.util
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import feedparser


PIPELINE = Path(__file__).resolve().parents[1] / "pipeline"
sys.path.insert(0, str(PIPELINE))

import collect
import distribute_audio
import distribute_linkedin
import llm
import validate as pipeline_validate


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

    def test_disabled_source_is_excluded(self):
        self.assertFalse(collect.source_enabled({"enabled": False}))
        self.assertTrue(collect.source_enabled({}))

    def test_encoding_override_with_entries_is_not_a_problem(self):
        feed = SimpleNamespace(
            bozo=1,
            bozo_exception=feedparser.CharacterEncodingOverride("utf-8"),
            entries=[{"title": "ok"}],
        )
        self.assertIsNone(collect.rss_parse_problem(feed))

    def test_malformed_empty_feed_is_a_problem(self):
        feed = SimpleNamespace(
            bozo=1,
            bozo_exception=ValueError("invalid token"),
            entries=[],
        )
        self.assertIn("invalid token", collect.rss_parse_problem(feed))


class LlmFailureTests(unittest.TestCase):
    @mock.patch("llm._get_api_key", return_value="test-key")
    @mock.patch("llm.requests.post")
    def test_openrouter_http_error_never_becomes_model_output(self, post, _key):
        post.return_value.status_code = 401
        post.return_value.text = "unauthorized"
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

    def test_seen_db_is_committed_immediately_after_site_push(self):
        """En distributionskanal får inte göra publicerade artiklar nya igen."""
        runner = (PIPELINE / "run_weekly.sh").read_text()
        seen_commit = runner.index('collect.py" --commit-seen')
        distribution = runner.index('python "$PIPELINE_DIR/distribute.py"')
        self.assertLess(seen_commit, distribution)


class UrlValidationTests(unittest.TestCase):
    def test_supported_observations_are_not_factual_issues(self):
        result = {
            "factual_validation_ok": True,
            "pass_rate": 0.50,
            "issues": [{"severity": "low", "supported": True, "problem": "korrekt detalj"}],
        }
        normalized = pipeline_validate._normalize_factual_validation(result)
        self.assertEqual(normalized["issues"], [])
        self.assertEqual(normalized["pass_rate"], 1.0)

    def test_mixed_observations_recalculate_pass_rate_from_real_issues(self):
        result = {
            "factual_validation_ok": True,
            "pass_rate": 0.20,
            "issues": [
                {"severity": "low", "supported": True, "problem": "korrekt detalj"},
                {"severity": "medium", "supported": False, "problem": "saknar stöd"},
            ],
        }
        normalized = pipeline_validate._normalize_factual_validation(result)
        self.assertEqual(len(normalized["issues"]), 1)
        self.assertEqual(normalized["pass_rate"], 0.85)

    def test_private_and_unsupported_urls_are_rejected(self):
        self.assertFalse(pipeline_validate._acceptable_source_url("http://127.0.0.1/admin"))
        self.assertFalse(pipeline_validate._acceptable_source_url("http://169.254.169.254/latest/meta-data"))
        self.assertFalse(pipeline_validate._acceptable_source_url("http://2130706433/admin"))
        self.assertFalse(pipeline_validate._acceptable_source_url("http://0x7f000001/admin"))
        self.assertFalse(pipeline_validate._acceptable_source_url("http://127.1/admin"))
        self.assertFalse(pipeline_validate._acceptable_source_url("http://0177.0.0.1/admin"))
        self.assertFalse(pipeline_validate._acceptable_source_url("file:///etc/passwd"))

    def test_hostname_resolving_to_private_network_is_rejected(self):
        private = [(2, 1, 6, "", ("10.0.0.5", 443))]
        with mock.patch.object(pipeline_validate.socket, "getaddrinfo", return_value=private):
            self.assertFalse(pipeline_validate._acceptable_source_url("https://internal.example/article"))

    def test_absent_or_malformed_model_validation_fails_closed(self):
        for response in (None, "not json"):
            result = pipeline_validate._normalize_factual_validation(
                pipeline_validate._parse_validation(response)
            )
            self.assertFalse(result["factual_validation_ok"])
            self.assertEqual(result["pass_rate"], 0.0)

    def test_jina_soft_error_is_not_accepted(self):
        body = "Title: Access Denied\nURL Source: https://example.com\nMarkdown Content:\nCAPTCHA required"
        self.assertFalse(pipeline_validate._jina_content_is_valid(body, "https://example.com"))

    def test_jina_mismatched_source_is_not_accepted(self):
        body = "Title: Real article\nURL Source: https://evil.example/phish\nMarkdown Content:\n" + ("real words " * 30)
        self.assertFalse(pipeline_validate._jina_content_is_valid(body, "https://example.com/article"))

    def test_bot_blocked_primary_source_can_be_verified_via_jina(self):
        jina = SimpleNamespace(
            status_code=200,
            text="Title: Valid source\nURL Source: https://openai.com/example\nMarkdown Content:\n" + ("substantive article words " * 20),
        )
        with mock.patch.object(pipeline_validate.requests, "head") as direct_head, \
             mock.patch.object(pipeline_validate.requests, "get", return_value=jina):
            result = pipeline_validate._check_urls([{"url": "https://openai.com/example"}])
        self.assertEqual(result, {"valid": 1, "invalid": 0, "total": 1})
        direct_head.assert_not_called()

    def test_any_unverified_source_fails_strict_url_gate(self):
        self.assertFalse(pipeline_validate._urls_healthy({"valid": 5, "invalid": 1, "total": 6}))
        self.assertTrue(pipeline_validate._urls_healthy({"valid": 6, "invalid": 0, "total": 6}))


class CrossIssueDuplicationTests(unittest.TestCase):
    def _issue(self, headline, image):
        return {
            "frontmatter": {
                "lead": {"headline": headline, "kicker": "Modeller", "image": image},
                "stories": [{"headline": "En annan story", "kicker": "Verktyg"}],
            }
        }

    def test_same_lead_image_as_previous_issue_is_blocked(self):
        current = self._issue(
            "Grok 4.6 landar på Amazon Bedrock",
            "https://x.ai/images/news/og-grok-4-6-on-bedrock.webp",
        )
        previous = self._issue(
            "Grok 4.6 flyttar in i Amazon Bedrock",
            "https://x.ai/images/news/og-grok-4-6-on-bedrock.webp",
        )
        result = pipeline_validate._check_duplication(current, previous_issue=previous)
        self.assertTrue(result["duplicate"])
        self.assertIn("föregående utgåva", result["reason"])

    def test_distinct_lead_from_previous_issue_is_allowed(self):
        current = self._issue(
            "OpenAI bryter modellavtalet med Cursor",
            "https://openai.com/cursor.png",
        )
        previous = self._issue(
            "Grok 4.6 flyttar in i Amazon Bedrock",
            "https://x.ai/images/news/og-grok-4-6-on-bedrock.webp",
        )
        result = pipeline_validate._check_duplication(current, previous_issue=previous)
        self.assertFalse(result["duplicate"])

    def test_near_identical_lead_headline_is_blocked_even_if_image_changed(self):
        current = self._issue(
            "Grok 4.6 landar på Amazon Bedrock",
            "https://cdn.example/new-image.webp",
        )
        previous = self._issue(
            "Grok 4.6 flyttar in i Amazon Bedrock",
            "https://x.ai/images/old-image.webp",
        )
        result = pipeline_validate._check_duplication(current, previous_issue=previous)
        self.assertTrue(result["duplicate"])

    def test_loader_finds_previous_number_for_cross_issue_gate(self):
        current_path = PIPELINE.parent / "content" / "2026-35.md"
        previous = pipeline_validate._load_previous_issue(current_path)
        self.assertEqual(previous["frontmatter"]["week"], "34")
        self.assertIn("Grok 4.6", previous["frontmatter"]["lead"]["headline"])


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
    """Moltbook är avkopplad och får inte påverka publiceringen."""

    def test_moltbook_is_explicitly_disabled(self):
        runner = (PIPELINE / "run_weekly.sh").read_text()
        self.assertIn("MOLTBOOK_STATUS=0", runner)
        self.assertNotIn('python "$PIPELINE_DIR/post-to-moltbook.py"', runner)

    def test_moltbook_failure_still_fails_the_run(self):
        runner = (PIPELINE / "run_weekly.sh").read_text()
        self.assertIn('if [ "${MOLTBOOK_STATUS:-0}" -ne 0 ]; then', runner)


class InterpreterTests(unittest.TestCase):
    """`python3` = homebrew 3.14 utan requests/yaml; `python` = venv-tolken."""

    def test_distribution_uses_the_preflight_validated_interpreter(self):
        runner = (PIPELINE / "run_weekly.sh").read_text()
        self.assertIn('python "$PIPELINE_DIR/distribute.py"', runner)
        self.assertNotIn('python3 "$PIPELINE_DIR/distribute.py"', runner)

    def test_moltbook_is_not_called_by_runner(self):
        runner = (PIPELINE / "run_weekly.sh").read_text()
        self.assertNotIn('post-to-moltbook.py"', runner)

    def test_distribution_modules_inherit_the_parent_interpreter(self):
        """distribute.py startar modulerna med sys.executable — därför spelar
        anropstolken i runnern roll hela vägen ner."""
        distributor = (PIPELINE / "distribute.py").read_text()
        self.assertIn("sys.executable", distributor)


class PodcastFeedTests(unittest.TestCase):
    """Enclosure-URL:erna pekade på aibladet.se, som inte serverar sajten."""

    def test_site_url_defaults_to_canonical_host(self):
        self.assertEqual(distribute_audio.SITE_URL, "https://ai-bladet.pages.dev")

    def test_published_feed_has_no_dead_host(self):
        feed = (PIPELINE.parent / "public" / "feed" / "podcast.xml").read_text()
        self.assertNotIn("aibladet.se", feed)


class LinkedInDraftTests(unittest.TestCase):
    def test_draft_uses_canonical_issue_url(self):
        self.assertEqual(
            distribute_linkedin.issue_url(2026, 37),
            "https://ai-bladet.pages.dev/v/2026/37/",
        )


if __name__ == "__main__":
    unittest.main()
