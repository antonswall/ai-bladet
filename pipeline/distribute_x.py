#!/usr/bin/env python3
"""
AI-Bladet — X/Twitter Distribution Module
===========================================
Genererar två X-poster per vecka:
1. Thread: topp 3 stories som tråd (4 tweets)
2. "Veckans AI-lögn": konträr tweet som avslöjar en överdrift

Input:  content/YYYY-WW.md (via --issue)
Output: pipeline/output/distribution/x/YYYY-WW-thread.md
         pipeline/output/distribution/x/YYYY-WW-lie.md

API-kostnad: ~$0.0006 per vecka (DeepSeek)
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

# ─── Config ───────────────────────────────────────────────────────────────────

PIPELINE_DIR = Path(__file__).parent
DIST_OUTPUT_DIR = PIPELINE_DIR / "output" / "distribution" / "x"

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"


# ─── API Helpers ──────────────────────────────────────────────────────────────

def _get_deepseek_key() -> str:
    key = os.getenv("DEEPSEEK_API_KEY", "")
    if key:
        return key
    env_path = Path.home() / ".hermes" / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("DEEPSEEK_API_KEY="):
                return line.split("=", 1)[1].strip()
    raise ValueError("DEEPSEEK_API_KEY saknas")


def deepseek_call(prompt: str, system: str = None,
                  max_tokens: int = 1000, temperature: float = 0.4) -> Optional[str]:
    key = _get_deepseek_key()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        r = requests.post(
            DEEPSEEK_URL,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=30,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"  ⚠️ DeepSeek API error: {e}", file=sys.stderr)
        return None


# ─── Thread-generering ────────────────────────────────────────────────────────

def generate_thread(issue: dict, week: int, year: int) -> Optional[str]:
    """
    Generera en X-thread med veckans 3 viktigaste stories.
    """
    lead = issue.get("lead", {})
    stories = issue.get("stories", [])
    title = issue.get("title", f"Vecka {week}")

    # Välj lead + topp 2 stories
    selected = [lead] + stories[:2]
    story_summaries = []
    for i, s in enumerate(selected):
        headline = s.get("headline", "")
        ingress = s.get("ingress", "")[:200]
        story_summaries.append(f"{i+1}. {headline}\n   {ingress}")

    prompt = f"""Skriv en X-thread med 4 tweets som sammanfattar AI-Bladet vecka {week}.

Tweet 1: Hook — "Här är veckans viktigaste AI-nyheter från AI-Bladet."
Tweet 2: Story 1 — rubrik + kort förklaring varför det spelar roll
Tweet 3: Story 2 — rubrik + kort förklaring varför det spelar roll
Tweet 4: Story 3 + länk: "Läs hela veckans AI-Bladet på aibladet.se [länk]"

Varje tweet MAX 280 tecken. Använd naturlig svenska. 
Inga hashtags. Var konkret.
Engagera — avsluta tweet 4 med en fråga.

Här är veckans stories:
{chr(10).join(story_summaries)}

Returnera som:
--- TWEET 1 ---
[text]
--- TWEET 2 ---
[text]
--- TWEET 3 ---
[text]
--- TWEET 4 ---
[text]
"""

    system = "Du är AI-Bladets redaktör på X. Skriv korta, engagerande tweets på svenska."

    result = deepseek_call(prompt, system=system, max_tokens=800, temperature=0.5)
    if not result:
        return None

    return result


# ─── AI-lögn-generering ──────────────────────────────────────────────────────

def generate_lie_tweet(issue: dict) -> Optional[str]:
    """
    Generera en konträr tweet som avslöjar en överdrift/myt.
    """
    title = issue.get("title", "")
    lead = issue.get("lead", {})
    stories = issue.get("stories", [])

    context = []
    context.append(f"Lead: {lead.get('headline', '')} — {lead.get('ingress', '')[:150]}")
    for s in stories[:5]:
        context.append(f"Story: {s.get('headline', '')} — {s.get('ingress', '')[:150]}")

    prompt = f"""Läs veckans AI-nyheter och identifiera EN överdrift eller myt som förekommer.

Skriv en tweet som krossar myten:
"Alla säger att [X]. Här är varför de har fel: [fakta/siffra]."

Format: MAX 280 tecken. Naturlig svenska. Länk till AI-Bladet för källa.
Välj den story med mest hype-gap — där skillnaden mellan vad folk säger och vad som faktiskt är sant är störst.

Här är veckans stories:
{chr(10).join(context)}

Returnera endast tweet-texten, inget annat.
"""

    system = "Du är en kritisk AI-analytiker. Din uppgift är att avslöja hype och överdrifter med fakta."

    result = deepseek_call(prompt, system=system, max_tokens=300, temperature=0.3)
    if not result:
        return None

    # Rensa output — ta bara själva tweeten
    clean = result.strip().strip('"').strip("'")
    return clean[:280]  # Max 280 tecken


# ─── Huvudfunktion ───────────────────────────────────────────────────────────

def distribute_x(issue_path: str, dry_run: bool = False) -> bool:
    """
    Generera X-innehåll för veckans issue.
    """
    import yaml

    path = Path(issue_path)
    if not path.exists():
        print(f"❌ Saknar issue: {issue_path}")
        return False

    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3:
        print("❌ Ingen frontmatter")
        return False

    issue = yaml.safe_load(parts[1])
    week = issue.get("week", "?")
    year = issue.get("year", datetime.now().year)
    title = issue.get("title", f"Vecka {week}")

    print(f"  📝 Vecka {week}: {title[:50]}...")

    # Skapa output-kataloger
    DIST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Steg 1: Thread
    print(f"  🧵 Genererar X-thread...", end=" ", flush=True)
    if dry_run:
        thread = "--- TWEET 1 ---\n(dry-run)\n--- TWEET 2 ---\n(dry-run)\n--- TWEET 3 ---\n(dry-run)\n--- TWEET 4 ---\n(dry-run)"
        print("(dry-run)")
    else:
        thread = generate_thread(issue, week, year)
        if not thread:
            print("❌")
        else:
            tweet_count = thread.count("--- TWEET")
            print(f"{tweet_count} tweets")

    # Spara thread
    thread_path = DIST_OUTPUT_DIR / f"{year}-{week}-thread.md"
    if thread:
        thread_content = f"""# AI-Bladet X-thread — Vecka {week}/{year}

Publicera måndag 09:00.

```
{thread.strip()}
```

---
Länk: https://aibladet.se/{year}/{week}
"""
        thread_path.write_text(thread_content, encoding="utf-8")
        print(f"    ➡ Sparad: {thread_path.name}")

    # Steg 2: AI-lögn
    print(f"  🔍 Genererar AI-lögn...", end=" ", flush=True)
    if dry_run:
        lie_tweet = "Alla säger att AI kommer ta ditt jobb. Här är varför det är fel. (dry-run)"
        print("(dry-run)")
    else:
        lie_tweet = generate_lie_tweet(issue)
        if not lie_tweet:
            print("❌")
        else:
            print(f"{len(lie_tweet)} tecken")

    # Spara AI-lögn
    lie_path = DIST_OUTPUT_DIR / f"{year}-{week}-lie.md"
    if lie_tweet:
        lie_content = f"""# AI-Bladet Veckans lögn — Vecka {week}/{year}

Publicera måndag 09:00 (EFTER thread).

```
{lie_tweet.strip()}
```

---
Länk: https://aibladet.se/{year}/{week}
"""
        lie_path.write_text(lie_content, encoding="utf-8")
        print(f"    ➡ Sparad: {lie_path.name}")

    # Summering
    thread_ok = thread is not None
    lie_ok = lie_tweet is not None
    print(f"  ✅ Thread: {'✅' if thread_ok else '❌'} · Lie: {'✅' if lie_ok else '❌'}")

    return thread_ok and lie_ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI-Bladet — X distribution")
    parser.add_argument("--issue", required=True, help="Sökväg till issue-fil")
    parser.add_argument("--dry-run", action="store_true", help="Simulera utan API-anrop")
    args = parser.parse_args()

    success = distribute_x(args.issue, dry_run=args.dry_run)
    sys.exit(0 if success else 1)
