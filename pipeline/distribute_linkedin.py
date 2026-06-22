#!/usr/bin/env python3
"""
AI-Bladet — LinkedIn Distribution Module
==========================================
Tar veckans mest vardagsrelevanta AI-story och skriver om den för en
icke-teknisk publik på LinkedIn.

Input:  content/YYYY-WW.md (via --issue)
Output: pipeline/output/distribution/linkedin/YYYY-WW.md (utkast för manuell post)

API-kostnad: ~$0.0004 per vecka (DeepSeek)
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
DIST_OUTPUT_DIR = PIPELINE_DIR / "output" / "distribution" / "linkedin"
PROJECT_DIR = Path.home() / "ai-bladet"
CONTENT_DIR = PROJECT_DIR / "content"
SITE_URL = os.getenv("SITE_URL", "https://aibladet.se")

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

# ─── API Helper ───────────────────────────────────────────────────────────────

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
                  max_tokens: int = 800, temperature: float = 0.4) -> Optional[str]:
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


# ─── Välj story att humanisera ────────────────────────────────────────────────

def pick_human_story(issue: dict) -> Optional[dict]:
    """
    Välj den story från veckans issue som har högst vardagsrelevans.
    Ledaren har företräde om den är vardagsrelevant, annars sektionerna.
    Returnerar story-dict med extra fält: {headline, ingress, body, ...}
    """
    lead = issue.get("lead", {})
    stories = issue.get("stories", [])

    candidates = []

    # Lägg till lead
    if lead and lead.get("headline"):
        candidates.append({
            "source": "lead",
            "headline": lead.get("headline", ""),
            "ingress": lead.get("ingress", ""),
            "body": lead.get("analysis", ""),
            "image": lead.get("image", ""),
            "credit": lead.get("credit", ""),
        })

    # Lägg till sektioner
    for i, s in enumerate(stories):
        candidates.append({
            "source": f"story_{i}",
            "headline": s.get("headline", ""),
            "ingress": s.get("ingress", ""),
            "body": s.get("body", ""),
            "image": s.get("image", ""),
            "credit": s.get("credit", ""),
        })

    # Skicka till DeepSeek för att bedöma vardagsrelevans
    context_lines = []
    for c in candidates:
        context_lines.append(
            f"[{c['source']}] {c['headline']}\n"
            f"  Ingress: {c['ingress'][:150]}\n"
            f"  Body: {c['body'][:200]}\n"
        )

    context = "\n".join(context_lines)

    prompt = f"""Läs veckans AI-nyheter och välj EN story som har högst vardagsrelevans för en icke-teknisk svensk LinkedIn-användare.

"Vardagsrelevans" betyder: påverkar denna story vanliga människors jobb, vardag, privatekonomi eller framtid inom 1-3 år?

Returnera JSON:
{{
  "source": "lead eller story_0/story_1/etc",
  "headline": "storyns rubrik",
  "reason": "En mening om varför just denna story är mest vardagsrelevant"
}}

Här är veckans stories:
{context}
"""

    system = "Du bedömer AI-nyheters relevans för vanliga människor. Välj den story som påverkar flest människors vardag."

    result = deepseek_call(prompt, system=system, max_tokens=300, temperature=0.2)
    if not result:
        return candidates[0] if candidates else None

    # Parsa JSON
    try:
        cleaned = re.sub(r"```(?:json)?\s*", "", result).strip()
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            selection = json.loads(cleaned[start:end + 1])
            source = selection.get("source", "lead")
            for c in candidates:
                if c["source"] == source:
                    c["selection_reason"] = selection.get("reason", "")
                    return c
    except (json.JSONDecodeError, Exception):
        pass

    # Fallback: första kandidaten
    return candidates[0] if candidates else None


# ─── LinkedIn-post-generering ─────────────────────────────────────────────────

def generate_linkedin_post(issue: dict, story: dict, week: int) -> Optional[str]:
    """
    Generera en LinkedIn-post från en story. Skriven för icke-tekniska läsare.
    Max 1500 tecken.
    """
    headline = story.get("headline", "")
    ingress = story.get("ingress", "")
    body = story.get("body", "")[:500]
    reason = story.get("selection_reason", "")

    prompt = f"""Skriv en LinkedIn-post på svenska baserad på denna AI-nyhet.

Målgrupp: Svenskar som är nyfikna på AI men INTE tekniska. De jobbar kanske som lärare,
sjuksköterska, säljare, ekonom — de hör om AI hela tiden men vet inte vad de ska tro.

Krav:
- Hook i första raden som fångar uppmärksamhet. Ex: "Har du undrat varför [X]? Här är varför."
- Förklara storyn helt utan jargong
- Berätta VARFÖR den spelar roll för en vanlig person
- Avsluta med en reflektion eller fråga som engagerar
- Max 1500 tecken
- Länk till AI-Bladet i slutet för "läs mer"
- Inga hashtags
- Personlig, inte formell ton — som en kollega som förklarar över en kaffe

Story:
Rubrik: {headline}
Ingress: {ingress}
Detaljer: {body}
Varför den valdes: {reason}

Skriv bara själva LinkedIn-posten, inget annat.
"""

    system = ("Du är AI-Bladets redaktör på LinkedIn. Din röst är nyfiken, personlig och "
              "pedagogisk. Du förklarar AI för vanliga människor utan att förenkla för mycket.")

    result = deepseek_call(prompt, system=system, max_tokens=800, temperature=0.5)
    if not result:
        return None

    # Trim till max 1500 tecken
    result = result.strip()
    if len(result) > 1500:
        result = result[:1497] + "..."

    return result


# ─── Huvudfunktion ───────────────────────────────────────────────────────────

def distribute_linkedin(issue_path: str, dry_run: bool = False) -> bool:
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

    # Skapa output-kataloger
    DIST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"  💼 Vecka {week}: {title[:50]}...")

    # Steg 1: Välj story
    print(f"  🔍 Väljer mest vardagsrelevant story...", end=" ", flush=True)
    if dry_run:
        story = {
            "source": "lead",
            "headline": "USA exportkontrollerade Anthropics AI-modeller (dry-run)",
            "ingress": "Test (dry-run)",
            "body": "Test body",
            "selection_reason": "Test reason",
        }
        print("(dry-run)")
    else:
        story = pick_human_story(issue)
        if not story:
            print("❌ Ingen story vald")
            return False
        print(f"'{story['headline'][:60]}...'")

    # Steg 2: Generera LinkedIn-post
    print(f"  ✍️ Skriver LinkedIn-post...", end=" ", flush=True)
    if dry_run:
        post = (
            "Har du också fått känslan av att AI-pratet bara växer men ingen "
            "riktigt förklarar vad det betyder för dig?\n\n"
            "Den här veckan hände något som faktiskt påverkar din vardag mer än "
            "du tror. [Story-förklaring här...]\n\n"
            "Vad betyder detta för Sverige? Kanske mer än vi tror.\n\n"
            "Läs hela veckans AI-Bladet på aibladet.se (dry-run)"
        )
        print("(dry-run)")
    else:
        post = generate_linkedin_post(issue, story, week)
        if not post:
            print("❌ Misslyckades")
            return False
        print(f"{len(post)} tecken")

    # Spara output
    output_path = DIST_OUTPUT_DIR / f"{year}-{week}.md"
    output_content = f"""# AI-Bladet LinkedIn-post — Vecka {week}/{year}

**Story:** {story['headline']}
**Varför den valdes:** {story.get('selection_reason', '')}
**Publicera:** måndag 09:00
**Tecken:** {len(post)}

---

{post}

---

Länk: {SITE_URL}/{year}/{week}
"""
    output_path.write_text(output_content, encoding="utf-8")

    print(f"    ➡ Sparad: {output_path.name} ({len(post)} tecken)")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI-Bladet — LinkedIn distribution")
    parser.add_argument("--issue", required=True, help="Sökväg till issue-fil")
    parser.add_argument("--dry-run", action="store_true", help="Simulera utan API-anrop")
    args = parser.parse_args()

    success = distribute_linkedin(args.issue, dry_run=args.dry_run)
    sys.exit(0 if success else 1)
