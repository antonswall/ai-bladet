import os
import subprocess
from pathlib import Path

import pytest

RUNNER = Path(__file__).resolve().parents[1] / 'pipeline' / 'run_weekly.sh'


def run_preflight(tmp_path, git_failure='', skip_push=False):
    home = tmp_path / 'home'
    (home / 'ai-bladet' / 'pipeline').mkdir(parents=True)
    bins = tmp_path / 'bin'
    bins.mkdir()
    trace = tmp_path / 'git-calls'
    for name in ('python', 'node', 'claude'):
        executable = bins / name
        executable.write_text('#!/bin/bash\nexit 0\n')
        executable.chmod(0o755)
    git = bins / 'git'
    git.write_text(
        f'#!/bin/bash\nprintf "%s\\n" "$*" >> "{trace}"\n'
        f'case "$*" in *"{git_failure or "never-match"}"*) exit 1;; esac\n'
        'exit 0\n'
    )
    git.chmod(0o755)
    runner = tmp_path / 'runner.sh'
    lines = RUNNER.read_text().splitlines()
    runner.write_text('\n'.join('export PATH="$PATH"' if line.startswith('export PATH=') else line
                                for line in lines) + '\n')
    env = dict(os.environ, HOME=str(home), PATH=f'{bins}:/usr/bin:/bin')
    env.pop('SKIP_GIT_PUSH', None)
    if skip_push:
        env['SKIP_GIT_PUSH'] = '1'
    result = subprocess.run(['bash', str(runner), '--preflight-only'], env=env,
                            capture_output=True, text=True, timeout=15)
    return result, trace.read_text() if trace.exists() else ''


@pytest.mark.parametrize('failure,diagnostic', [
    ('GIT_AUTHOR_IDENT', 'Git-identitet'),
    ('push --dry-run', 'Git-push'),
])
def test_git_failure_stops_preflight(tmp_path, failure, diagnostic):
    result, trace = run_preflight(tmp_path, git_failure=failure)
    assert result.returncode == 1, result.stdout + result.stderr
    assert diagnostic in result.stdout
    assert 'Preflight OK' not in result.stdout
    assert '--dry-run' in trace or failure == 'GIT_AUTHOR_IDENT'


def test_preflight_verifies_push_without_changing_remote(tmp_path):
    result, trace = run_preflight(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'GIT_AUTHOR_IDENT' in trace
    assert 'push --dry-run origin HEAD:refs/heads/main' in trace
    assert all('--dry-run' in line for line in trace.splitlines() if ' push ' in f' {line} ')


def test_local_dry_run_does_not_require_git_credentials(tmp_path):
    result, trace = run_preflight(tmp_path, git_failure='push', skip_push=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'push' not in trace


def test_commit_failure_cannot_continue_to_push(tmp_path):
    import re

    block = re.search(r'git add -A\n(.*?)git push origin main', RUNNER.read_text(), re.S).group(1)
    git = tmp_path / 'git'
    git.write_text('#!/bin/bash\ncase "$1" in diff) exit 1;; commit) exit 2;; esac\nexit 0\n')
    git.chmod(0o755)
    env = dict(os.environ, PATH=f'{tmp_path}:/usr/bin:/bin')
    result = subprocess.run(['bash', '-c', block + '\nprintf AFTER_COMMIT'], env=env,
                            capture_output=True, text=True, timeout=15)
    assert result.returncode != 0
    assert 'AFTER_COMMIT' not in result.stdout
