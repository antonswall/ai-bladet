"""
pipeline/llm.py — Gemensam LLM-wrapper via Claude Code CLI (claude -p).

Använder Antons redan inloggade OAuth-session (Claude Pro/Max) — ingen extra
API-kostnad. Kräver att `claude` CLI är inloggad (claude /login).

Fallback: OpenRouter GPT-5.6 Luna om Claude CLI inte svarar (OAuth expired etc).

Användning:
    from llm import llm_call
    result = llm_call("Scora dessa nyheter...", system="Du är en AI-redaktör.")
"""

import os
import sys
import subprocess
import time
from typing import Optional

import requests

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_FALLBACK_MODEL = "openai/gpt-5.6-luna"
DEFAULT_TIMEOUT = 90

# Claude-modell för `claude -p`. Opus är AVSIKTLIGT spärrat: pipelinen får aldrig välja Opus utan
# Antons uttryckliga godkännande (se ALLOWED_CLAUDE_MODELS). Utan --model ärver `claude -p` användarens
# standardmodell, vilket 2026-09-20 var Opus och brände Claude-kvoten (~40 Opus-sessioner på en körning).
DEFAULT_CLAUDE_MODEL = "haiku"
ALLOWED_CLAUDE_MODELS = {"haiku", "sonnet"}


def _get_openrouter_api_key() -> str:
    key = os.getenv("OPENROUTER_API_KEY", "")
    if not key:
        env_path = os.path.expanduser("~/.hermes/.env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("OPENROUTER_API_KEY=") and not line.startswith("#"):
                        key = line.split("=", 1)[1].strip()
                        break
    return key


def _llm_call_claude_cli(
    prompt: str,
    system: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
    model: Optional[str] = None,
) -> Optional[str]:
    """Anropa Claude i headless-läge utan verktyg eller sparad session.

    Varje anrop är en ren textcompletion. Det är avsiktligt inte en Codex-agent:
    `codex exec --ephemeral` registreras fortfarande som en task i Codex desktop
    med nyare CLI-versioner och får därför inte användas av batchpipelinen.
    """
    model = (model or DEFAULT_CLAUDE_MODEL).strip().lower()
    if model not in ALLOWED_CLAUDE_MODELS:
        print(
            f"  ⛔ Claude-modell '{model}' är inte tillåten i pipelinen (tillåtna: "
            f"{', '.join(sorted(ALLOWED_CLAUDE_MODELS))}). Opus kräver Antons godkännande.",
            file=sys.stderr,
        )
        return None
    # Ersätt Claude Codes stora agentsystemprompt med pipeline-stegets egen. Det
    # minskar input-tokens per anrop och hindrar projektinstruktioner/plugins från
    # att läcka in i en ren textcompletion.
    system_prompt = system or "Svara endast på användarens uppgift, kort och exakt."

    try:
        result = subprocess.run(
            [
                "claude",
                "-p",
                "--model",
                model,
                "--no-session-persistence",
                "--safe-mode",
                "--disable-slash-commands",
                "--system-prompt",
                system_prompt,
                "--tools",
                "",
                "--permission-prompts",
                "none",
            ],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        detail = (result.stderr or result.stdout or "").strip()[:300]
        print(f"  ⚠️  Claude CLI-fel (exit {result.returncode}): {detail}", file=sys.stderr)
        return None
    except subprocess.TimeoutExpired:
        print(f"  ⚠️  Claude CLI timeout efter {timeout}s", file=sys.stderr)
        return None
    except FileNotFoundError:
        print("  ⚠️  claude CLI hittades inte i PATH", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  ⚠️  Claude CLI oväntat fel: {e}", file=sys.stderr)
        return None


def _llm_call_openrouter(
    prompt: str,
    system: Optional[str] = None,
    max_tokens: int = 4000,
    temperature: float = 0.1,
    timeout: int = DEFAULT_TIMEOUT,
    attempts: int = 2,
) -> Optional[str]:
    """Fallback: GPT-5.6 Luna via OpenRouter."""
    api_key = _get_openrouter_api_key()
    if not api_key:
        print("  ❌  OPENROUTER_API_KEY saknas (fallback otillgänglig)", file=sys.stderr)
        return None

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://ai-bladet.pages.dev",
        "X-Title": "AI-Bladet",
    }
    payload = {
        "model": OPENROUTER_FALLBACK_MODEL,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": messages,
    }

    for attempt in range(1, max(1, attempts) + 1):
        try:
            resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    return choices[0]["message"]["content"].strip()
                print(f"  ⚠️  Tomt svar från OpenRouter Luna: {data}", file=sys.stderr)
                return None
            else:
                detail = resp.text[:300]
                print(
                    f"  ⚠️  OpenRouter Luna HTTP {resp.status_code} (försök {attempt}/{attempts}): {detail}",
                    file=sys.stderr,
                )
        except requests.Timeout:
            print(f"  ⚠️  OpenRouter Luna timeout (försök {attempt}/{attempts})", file=sys.stderr)
        except Exception as e:
            print(f"  ⚠️  OpenRouter Luna-fel: {e}", file=sys.stderr)
            return None

        if attempt < attempts:
            time.sleep(attempt * 2)

    return None


def llm_call(
    prompt: str,
    system: Optional[str] = None,
    max_tokens: int = 4000,
    temperature: float = 0.1,
    model: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
    attempts: int = 2,
) -> Optional[str]:
    """Anropa LLM: Claude Code CLI (primär) → OpenRouter GPT-5.6 Luna (fallback).

    Returnerar svarssträngen, eller None vid fel.
    """
    result = _llm_call_claude_cli(prompt, system, timeout, model=model)
    if result:
        return result

    print("  ⚠️  Claude CLI misslyckades — provar OpenRouter Luna...", file=sys.stderr)
    result = _llm_call_openrouter(prompt, system, max_tokens, temperature, timeout, attempts)
    if result:
        return result

    return None


if __name__ == "__main__":
    # Snabbtest
    result = llm_call("Svara exakt OK", attempts=1)
    print("result:", result)
    raise SystemExit(0 if result else 1)
