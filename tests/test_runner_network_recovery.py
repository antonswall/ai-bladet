import os
from pathlib import Path
import subprocess
import shlex
import tempfile
import unittest

RUNNER = Path(__file__).resolve().parents[1] / "pipeline" / "run_weekly.sh"
SCRATCH = Path.home() / ".hermes/cache/scratch"


class NetworkPreflightTests(unittest.TestCase):
    def run_preflight(self, failures, message):
        with tempfile.TemporaryDirectory(dir=SCRATCH) as folder:
            root = Path(folder)
            home = root / "home"
            (home / "ai-bladet/pipeline").mkdir(parents=True)
            bins = root / "bin"
            bins.mkdir()
            counter = root / "attempts"
            stubs = {
                "python": "exit 0",
                "node": "exit 0",
                "claude": "exit 0",
                "sleep": "exit 0",
                "git": f'''if [[ "$*" != *"--dry-run"* ]]; then exit 0; fi
n=0; if [ -f "{counter}" ]; then read n < "{counter}"; fi
n=$((n+1)); printf '%s' "$n" > "{counter}"
if [ "$n" -le {failures} ]; then printf '%s\\n' {shlex.quote(message)} >&2; exit 128; fi
exit 0''',
            }
            for name, body in stubs.items():
                path = bins / name
                path.write_text("#!/bin/bash\n" + body + "\n")
                path.chmod(0o755)
            source = RUNNER.read_text().splitlines()
            source = [f'export PATH="{bins}:/usr/bin:/bin"' if line.startswith("export PATH=") else line for line in source]
            runner = root / "runner.sh"
            runner.write_text("\n".join(source) + "\n")
            env = dict(os.environ, HOME=str(home))
            env.pop("SKIP_GIT_PUSH", None)
            result = subprocess.run(["/bin/bash", str(runner), "--preflight-only"], env=env, capture_output=True, text=True, timeout=10)
            count = int(counter.read_text())
            return result, count

    def test_transient_network_failure_is_retried(self):
        result, count = self.run_preflight(1, "fatal: Failed to connect to github.com port 443: Couldn't connect to server")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(count, 2)
        self.assertIn("PREFLIGHT_ONLY", result.stdout)

    def test_persistent_network_failure_is_bounded_and_labelled(self):
        result, count = self.run_preflight(99, "fatal: Could not resolve host: github.com")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(count, 3)
        self.assertIn("nätverksfel", result.stdout)

    def test_auth_failure_is_not_retried(self):
        result, count = self.run_preflight(99, "fatal: Authentication failed")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(count, 1)
        self.assertIn("autentisering", result.stdout)
