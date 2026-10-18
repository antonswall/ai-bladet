import json
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest

RUNNER = Path(__file__).resolve().parents[1] / "pipeline/run_weekly.sh"


class RetryFeedbackTests(unittest.TestCase):
    def test_short_story_feedback_includes_headline_and_required_length(self):
        text = RUNNER.read_text()
        start = text.index('FEEDBACK=$(python3 -c "')
        end = text.index('" 2>/dev/null)', start) + len('" 2>/dev/null)')
        fragment = text[start:end]
        with tempfile.TemporaryDirectory(dir=Path.home() / ".hermes/cache/scratch") as folder:
            report = Path(folder) / "validation.json"
            report.write_text(json.dumps({"validation": {
                "issues": [], "duplication": {"duplicate": False},
                "se_eu_angle": {"found": True},
                "word_counts": {"all_ok": False, "stories": [
                    {"headline": "För kort modellartikel", "words": 140, "min": 150, "ok": False}
                ]}
            }}))
            script = f"WEEK={shlex.quote(str(report))}\n{fragment}\nprintf '%s' \"$FEEDBACK\"\n"
            result = subprocess.run(["/bin/bash", "-c", script], text=True, capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("För kort modellartikel", result.stdout)
            self.assertIn("140", result.stdout)
            self.assertIn("150", result.stdout)
