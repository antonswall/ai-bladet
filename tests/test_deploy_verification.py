import tempfile
import unittest
from pathlib import Path

from pipeline import verify_deploy


class DeployVerificationTests(unittest.TestCase):
    def _issue(self) -> Path:
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False)
        tmp.write(
            "---\n"
            "year: 2026\n"
            "week: 37\n"
            'title: "Rätt upplaga är live"\n'
            "---\n"
        )
        tmp.close()
        self.addCleanup(Path(tmp.name).unlink)
        return Path(tmp.name)

    def test_requires_expected_title_on_permalink_and_homepage(self):
        identity = verify_deploy.load_issue_identity(self._issue())

        def fetch(url):
            if "/v/2026/37/" in url:
                return "<h1>Rätt upplaga är live</h1>"
            return "<h1>Förra veckans upplaga</h1>"

        ok, reason = verify_deploy.verify_live_issue(
            identity, fetch_text=fetch, attempts=1, delay_seconds=0
        )

        self.assertFalse(ok)
        self.assertIn("startsidan", reason)

    def test_retries_until_both_pages_show_expected_issue(self):
        identity = verify_deploy.load_issue_identity(self._issue())
        calls = []

        def fetch(url):
            calls.append(url)
            attempt = (len(calls) - 1) // 2
            if attempt == 0 and "/v/2026/37/" not in url:
                return "<h1>Förra veckan</h1>"
            return "<h1>Rätt upplaga är live</h1>"

        ok, reason = verify_deploy.verify_live_issue(
            identity,
            fetch_text=fetch,
            attempts=2,
            delay_seconds=0,
            sleep_fn=lambda _: None,
        )

        self.assertTrue(ok, reason)
        self.assertEqual(len(calls), 4)

    def test_required_assets_block_final_success(self):
        identity = verify_deploy.load_issue_identity(self._issue())

        def fetch(url):
            if "/memes/2026-37.png" in url:
                raise RuntimeError("HTTP 404")
            return "<h1>Rätt upplaga är live</h1>"

        ok, reason = verify_deploy.verify_live_issue(
            identity,
            fetch_text=fetch,
            attempts=1,
            delay_seconds=0,
            require_assets=True,
        )

        self.assertFalse(ok)
        self.assertIn("meme", reason)

    def test_runner_verifies_before_seen_db_and_before_deployed_message(self):
        runner = (Path(__file__).resolve().parents[1] / "pipeline" / "run_weekly.sh").read_text()
        first_verify = runner.index('verify_deploy.py" --issue')
        seen_commit = runner.index('collect.py" --commit-seen')
        deployed_message = runner.index("DEPLOYAD till ai-bladet.pages.dev")
        self.assertLess(first_verify, seen_commit)
        self.assertLess(first_verify, deployed_message)

    def test_runner_requires_assets_after_final_push(self):
        runner = (Path(__file__).resolve().parents[1] / "pipeline" / "run_weekly.sh").read_text()
        self.assertIn('verify_deploy.py" --issue "$ISSUE_FILE" --require-assets', runner)


if __name__ == "__main__":
    unittest.main()
