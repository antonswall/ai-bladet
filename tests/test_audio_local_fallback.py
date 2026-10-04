import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'pipeline'))
import distribute_audio as audio


def test_missing_elevenlabs_key_uses_local_tts():
    with patch.object(audio, '_get_env', return_value=None), \
         patch.object(audio, 'local_tts', return_value=b'ID3-local-audio', create=True) as local, \
         patch.object(audio.requests, 'post') as remote:
        assert audio.elevenlabs_tts('Svenska nyheter') == b'ID3-local-audio'
        local.assert_called_once_with('Svenska nyheter')
        remote.assert_not_called()


def test_audio_script_uses_canonical_site():
    with patch.object(audio, 'llm_call', return_value='Manus') as model:
        assert audio.generate_script({'week': 40, 'lead': {}}) == 'Manus'
        prompt = model.call_args.args[0]
        assert audio.SITE_URL in prompt
        assert 'aibladet.se' not in prompt


def test_local_tts_fails_closed_off_macos():
    with patch.object(audio.sys, 'platform', 'linux'), \
         patch.object(audio.subprocess, 'run') as command:
        assert audio.local_tts('Svenska nyheter') is None
        command.assert_not_called()
