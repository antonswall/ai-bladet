"""
pipeline/llm.py — Gemensam LLM-wrapper via OpenRouter (Claude Haiku).

Använder OPENROUTER_API_KEY (laddas från ~/.hermes/.env eller projektets .env).
Standardmodell: anthropic/claude-haiku-4-5 — billig och snabb för scoring/dedup/research.

Kostnad: direktfakturerat OpenRouter. Overhead: ~1-2s per anrop.

Användning:
    from llm import llm_call
    result = llm_call("Scora dessa nyheter...", system="Du är en AI-redaktör.")
"""

import os
import sys
import time
from typing import Optional

import requests

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
CLAUDE_MODEL = "anthropic/claude-haiku-4-5"
DEFAULT_TIMEOUT = 60


def _get_api_key() -> str:
    key = os.getenv("OPENROUTER_API_KEY", "")
    if not key:
        # Försök läsa från ~/.hermes/.env
        env_path = os.path.expanduser("~/.hermes/.env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("OPENROUTER_API_KEY=") and not line.startswith("#"):
                        key = line.split("=", 1)[1].strip()
                        break
    return key


def llm_call(
    prompt: str,
    system: Optional[str] = None,
    max_tokens: int = 4000,
    temperature: float = 0.1,
    model: str = CLAUDE_MODEL,
    timeout: int = DEFAULT_TIMEOUT,
    attempts: int = 2,
) -> Optional[str]:
    """Anropa Claude Haiku via OpenRouter.

    Returnerar svarssträngen, eller None vid fel.
    """
    api_key = _get_api_key()
    if not api_key:
        print("  ❌  OPENROUTER_API_KEY saknas", file=sys.stderr)
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
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": messages,
    }

    for attempt in range(1, max(1, attempts) + 1):
        try:
            resp = requests.post(
                OPENROUTER_URL,
                headers=headers,
                json=payload,
                timeout=timeout,
            )
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    return choices[0]["message"]["content"].strip()
                print(f"  ⚠️  Tomt svar från OpenRouter: {data}", file=sys.stderr)
                return None
            else:
                detail = resp.text[:300]
                print(
                    f"  ⚠️  OpenRouter HTTP {resp.status_code} (försök {attempt}/{attempts}): {detail}",
                    file=sys.stderr,
                )
        except requests.Timeout:
            print(
                f"  ⚠️  OpenRouter timeout efter {timeout}s (försök {attempt}/{attempts})",
                file=sys.stderr,
            )
        except Exception as e:
            print(f"  ⚠️  OpenRouter-fel: {e}", file=sys.stderr)
            return None

        if attempt < attempts:
            time.sleep(attempt * 2)

    return None


if __name__ == "__main__":
    # Snabbtest
    result = llm_call("Svara exakt OK", attempts=1)
    print("result:", result)
    raise SystemExit(0 if result else 1)
