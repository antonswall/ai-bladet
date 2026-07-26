"""
pipeline/llm.py — Gemensam LLM-wrapper via Codex CLI (GPT-5.6 Sol).

Använder Anton's Codex CLI (OpenAI Plus OAuth) istället för direkt API.
Codex CLI anropas som subprocess — samma auth som Hermes använder internt.

Kostnad: 0 (ingår i OpenAI Plus). Overhead: ~3-5s per anrop (agent-init).

Användning:
    from llm import llm_call
    result = llm_call("Scora dessa nyheter...", system="Du är en AI-redaktör.")
"""

import subprocess
import tempfile
import os
import sys
from pathlib import Path
from typing import Optional

CODEX_MODEL = "gpt-5.6-sol"
CODEX_TIMEOUT = 120  # sekunder — codex exec har agent-overhead


def llm_call(
    prompt: str,
    system: Optional[str] = None,
    max_tokens: int = 2000,
    temperature: float = 0.1,
    model: str = CODEX_MODEL,
    timeout: int = CODEX_TIMEOUT,
) -> Optional[str]:
    """Anropa GPT-5.6 Sol via Codex CLI (subprocess).

    Kombinerar system prompt + user prompt och skickar som stdin till `codex exec`.
    Returnerar sista meddelandet från agenten, eller None vid fel.
    """
    # Bygg full prompt
    full_prompt = prompt
    if system:
        full_prompt = f"{system}\n\n---\n\n{prompt}"

    # Tempfil för output-last-message
    output_fd, output_path = tempfile.mkstemp(suffix=".txt", prefix="codex_out_")
    os.close(output_fd)

    try:
        # codex exec läser prompt från stdin, skriver sista meddelandet till -o
        result = subprocess.run(
            [
                "codex", "exec",
                "-m", model,
                "--ephemeral",
                "--dangerously-bypass-approvals-and-sandbox",
                "--skip-git-repo-check",
                "-o", output_path,
                "-",  # läs prompt från stdin
            ],
            input=full_prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        # Läs output från tempfil
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            with open(output_path) as f:
                return f.read().strip()

        # Fallback: kolla stdout (JSONL mode)
        if result.stdout.strip():
            return result.stdout.strip().split("\n")[-1]

        # Fel
        if result.stderr:
            print(f"  ⚠️  Codex CLI stderr: {result.stderr[:200]}", file=sys.stderr)
        return None

    except subprocess.TimeoutExpired:
        print(f"  ⚠️  Codex CLI timeout efter {timeout}s", file=sys.stderr)
        return None
    except FileNotFoundError:
        print("  ❌  Codex CLI ('codex') inte installerat eller inte i PATH", file=sys.stderr)
        raise
    except Exception as e:
        print(f"  ⚠️  Codex CLI-fel: {e}", file=sys.stderr)
        return None
    finally:
        # Städa tempfil
        try:
            os.unlink(output_path)
        except OSError:
            pass
