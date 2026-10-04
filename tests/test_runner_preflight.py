import os
import subprocess
from pathlib import Path

RUNNER = Path(__file__).resolve().parents[1] / 'pipeline' / 'run_weekly.sh'


def test_preflight_only_does_not_run_collection(tmp_path):
    home = tmp_path / 'home'
    pipeline = home / 'ai-bladet' / 'pipeline'
    pipeline.mkdir(parents=True)
    bins = tmp_path / 'bin'
    bins.mkdir()
    marker = tmp_path / 'collected'
    python = bins / 'python'
    python.write_text(f'#!/bin/bash\nif [ "$1" = "collect.py" ]; then touch "{marker}"; exit 1; fi\nexit 0\n')
    python.chmod(0o755)
    for name in ['node', 'git', 'claude']:
        script = bins / name
        script.write_text('#!/bin/bash\nexit 0\n')
        script.chmod(0o755)
    env = dict(os.environ, HOME=str(home), PATH=str(bins) + ':' + os.environ['PATH'],
               SKIP_GIT_PUSH='1', ELEVENLABS_API_KEY='test-not-a-secret')
    result = subprocess.run(['bash', str(RUNNER), '--preflight-only'], env=env,
                            capture_output=True, text=True, timeout=15)
    assert not marker.exists(), result.stdout
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'PREFLIGHT_ONLY' in result.stdout
