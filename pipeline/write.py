#!/usr/bin/env python3
"""
AI-Bladet — Skrivning (Pipeline Steg 6)
==========================================
Claude Sonnet 4.6 via OpenRouter skriver veckans utgåva.

Input:  output/images/{YYYY-WW}.json
Output: content/{YYYY-WW}.md (direkt till ~/ai-bladet/content/)
"""

import json
import os
import re
import sys
from datetime import datetime, timezone, date, timedelta
from pathlib import Path
from typing import Optional

import requests

# ─── Config ───────────────────────────────────────────────────────────────────

PIPELINE_DIR = Path(__file__).parent
INPUT_DIR = PIPELINE_DIR / "output" / "images"
CONTENT_DIR = Path.home() / "ai-bladet" / "content"

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
SONNET_MODEL = "anthropic/claude-sonnet-4.6"

MAX_STORIES = 10            # max stories att skicka till Claude
MAX_BRIEFS = 8              # max briefs för KORTNYTT-sektionen
MAX_INPUT_CHARS = 4000      # max tecken per story i prompten


# ─── OpenRouter helper ───────────────────────────────────────────────────────


def _get_openrouter_key() -> Optional[str]:
    key = os.getenv("OPENROUTER_API_KEY", "")
    if key:
        return key
    env_path = Path.home() / ".hermes" / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("OPENROUTER_API_KEY="):
                k = line.split("=", 1)[1].strip()
                if k:
                    return k
    return None


def sonnet_call(prompt: str, system: str = None,
                max_tokens: int = 4000) -> Optional[str]:
    """Anropa Claude Sonnet 4.6 via OpenRouter."""
    key = _get_openrouter_key()
    if not key:
        raise ValueError("OPENROUTER_API_KEY saknas")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        r = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://aibladet.se",
                "X-Title": "AI-Bladet",
            },
            json={
                "model": SONNET_MODEL,
                "messages": messages,
                "temperature": 0.4,
                "max_tokens": max_tokens,
            },
            timeout=120,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"  ⚠️  OpenRouter/Sonnet error: {e}", file=sys.stderr)
        if hasattr(e, 'response') and e.response is not None:
            print(f"     Response: {e.response.text[:300]}", file=sys.stderr)
        return None


# ─── Prompt building ─────────────────────────────────────────────────────────


SYSTEM_PROMPT = """Du är chefredaktör för AI-Bladet, en svensk nyhetstidning om AI som utkommer varje söndag.

Din röst: ledig men trovärdig — tabloid i energi, sansad i sak. Tänk DN/SvD möter tech-blogg.
Inga uppmaningar till läsaren, ingen "i den här artikeln", inga emojis, inget marknadsföringsspråk.
Svenska, genomgående. 500-700 ord totalt.

REDAKTIONELLA REGLER — inga undantag:

1. DATERINGSKRAV
   Huvudsektioner: endast utveckling från de senaste 7 dagarna.
   Äldre material får endast tas med om det finns en konkret NY händelse denna vecka som motiverar det.
   Varje story måste ha ett publiceringsdatum i research. Kontrollera det.

2. INGA DUBLETTER
   "Veckans största" får INTE vara samma story som en sektion längre ner.
   Antingen: slå ihop till en längre artikel, eller gör toppen till en ren teaser som leder ner.

3. ATTRIBUERA ALLTID PRESTANDASIFFROR
   Alla prestandasiffror från en modellleverantör ("4x snabbare", "6x effektivitet")
   ska attribueras i rubrik eller första mening: "enligt Google", "xAI uppger".
   Aldrig en leverantörs marknadsföringssiffra som blank sanning.

4. KVALITATIVA SKIFTEN > INKREMENTELLA SLÄPP
   Om research innehåller ett kvalitativt skifte (t.ex. AI som går från diagnos → behandling),
   lyft det till egen sektion. Prioritera före inkrementella modellsläpp.
   Kortnytt är för notiser, inte för paradigmskiften.

5. SVENSK/EU-VINKEL
   Hitta minst en svensk eller EU-vinkel per nummer.
   Detta är det som differentierar AI-Bladet från engelska AI-nyhetsbrev.
   Exempel: svensk datacenterdebatt, EU-reglering, svenska AI-bolag i research.

6. TEASERN FÅR INTE LJUGA
   Lead-ingressen måste spegla veckans faktiska nyhet — inte en gammal story
   som om den vore ny. Läs datumen i research och kolla om storyn är aktuell.

7. KÄLLHÄNVISNING
   Varje påstående ska gå att spåra till en källa i research.
   Hitta inte på siffror, datum eller citat som inte finns där.

8. FALLBACK FÖR TUNNA VECKOR
   Om de senaste 7 dagarna är nyhetsfattiga och du har för få stories:
   Skapa en "Bakgrund/Djupdykning"-sektion. Där får äldre material finnas,
   men det måste TYDLIGT märkas som bakgrund/analys — inte presenteras som nyhet.
   Exempel: "SpaceX/xAI-affären (feb 2026): Så här ser det ut nu."
   Detta löser tunna veckor utan att ljuga om datering.

9. INGRESS PER STORY (framsidan)
   Varje sekundär story ska ha en fristående ingress på 40-60 ord som besvarar:
   vad hände, och varför det spelar roll. Ingressen är en egen, säljande
   sammanfattning (dek) — INTE de första meningarna av brödtexten ordagrant.
   Den ska kunna stå ensam på framsidan och få läsaren att vilja läsa vidare."""


def build_prompt(stories: list[dict], week: str, year: int,
                 published_date: str) -> str:
    """Bygg prompten för Sonnet med alla researchade stories."""
    now = datetime.now(timezone.utc)
    week_num = int(week.split("-")[1])
    date_obj = now - timedelta(days=now.weekday() + 1)  # senaste söndag
    date_str = date_obj.strftime("%Y-%m-%d")

    # Bygg context för varje story
    stories_text = ""
    for i, s in enumerate(stories):
        b = s.get("fact_brief", {})
        title = s.get("title", "Untitled")
        score = s.get("score", 0)
        category = s.get("category", "Övrigt")
        summary = b.get("summary", "")[:300]
        facts = b.get("key_facts", [])
        numbers = b.get("numbers", [])
        quotes = b.get("quotes", [])
        swedish = b.get("swedish_angle", "")
        lead = s.get("lead_potential", 0)
        source = s.get("source_label", "")
        image = s.get("image_url", "")

        stories_text += f"""
## STORY {i+1} — Score: {score} | Kategori: {category}
{'⭐ LEAD CANDIDATE' if lead >= 4 else ''}

Titel: {title}
Källa: {source}
Svensk vinkel: {swedish or 'Nej'}

Sammanfattning: {summary}

Nyckelfakta:
{chr(10).join(f'  • {f}' for f in facts[:5])}

Siffror:
{chr(10).join(f'  • {n.get("value", "")} — {n.get("context", "")}' for n in numbers[:3])}

Citat:
{chr(10).join(f'  "{q.get("text", "")}" — {q.get("speaker", "")}' for q in quotes[:2])}

Bild: {image[:80] if image else 'Ingen bild'}
"""
        stories_text += "\n---\n"

    prompt = f"""Skriv veckans utgåva av AI-Bladet.

KONTEXT:
- year: {year}
- week: {week_num}
- date: {date_str}

RESEARCHADE ARTIKLAR (scores från DeepSeek V4 Pro):

{stories_text}

INSTRUKTIONER:

1. Välj lead-story (veckans viktigaste). ⭐-märkta stories har hög lead-potential.

2. Välj 3-6 sekundära stories. Rangordna efter betydelse.

3. Välj 0-8 kortnytt-briefs från återstående stories (en mening var).
   Kortnytt är för notiser som inte förtjänar en full artikel men är värda att nämna.

4. Skriv i svensk ledig tidningston. Faktabaserat — hitta inte på något som inte finns i research.

5. OUTPUT — exakt detta format, inget annat före eller efter:

---
year: {year}
week: {week_num:02d}
date: {date_str}
title: "Redaktionell rubrik för HELA utgåvan (max 70 tecken)"
summary: "En mening som säljer veckan (max 140 tecken)"
lead:
  kicker: "VECKANS STÖRSTA"
  headline: "#1-nyhetens rubrik (inte exakt samma som research-titeln)"
  ingress: "2-3 meningar som säljer storyn"
stories:
  - kicker: "KATEGORI (Modeller, Politik, Verktyg, Forskning, Företag, Säkerhet, Sverige)"
    headline: "Rubrik"
    ingress: "40-60 ord: vad hände + varför det spelar roll. Egen formulering, INTE de första meningarna av body."
    body: "1-3 stycken markdown-brödtext"
briefs:
  - "Kort enradare"
  - "Ännu en kort enradare"
categories: [Kategori1, Kategori2]
sources: {len(stories)}
---

Skriv 500-700 ord totalt (lead.ingress + alla stories.body + briefs)."""

    return prompt


# ─── Parse output ─────────────────────────────────────────────────────────────


def parse_sonnet_output(text: str) -> str:
    """Verifiera att Sonnet producerade korrekt frontmatter + markdown."""
    if not text:
        raise ValueError("Sonnet returnerade tomt svar")

    # Kolla att frontmatter finns
    if not text.startswith("---"):
        # Försök hitta frontmatter
        fm_start = text.find("---")
        if fm_start >= 0:
            text = text[fm_start:]
        else:
            raise ValueError(f"Ingen YAML-frontmatter funnen i svar:\n{text[:300]}")

    # Kolla att alla obligatoriska fält finns
    required = ["year:", "week:", "date:", "title:", "summary:", "lead:", "stories:"]
    missing = [f for f in required if f not in text]
    if missing:
        print(f"  ⚠️  Varning: saknar fält: {missing}", file=sys.stderr)

    return text


# ─── Huvudfunktion ────────────────────────────────────────────────────────────


def write_issue(input_path: Path, output_path: Path, feedback: str = "") -> dict:
    """Generera veckans utgåva med Claude Sonnet 4.6.
    
    feedback: Om validering tidigare failat — skickas som extra instruktion
              till Sonnet så den kan korrigera specifika fel.
    """
    with open(input_path) as f:
        data = json.load(f)

    stories = data["stories"]
    week = data.get("meta", {}).get("week", "")
    attempt = " (rättning)" if feedback else ""
    print(f"✍️  Skriver AI-Bladet v.{week} med Claude Sonnet 4.6{attempt}\n")

    # Rensa titlar (ta bort body-konkatinering)
    for s in stories:
        t = s.get("title", "")
        # Klipp vid lowercase→UPPERCASE boundary om titeln är för lång
        words = re.split(r"(?<=[a-z])(?=[A-Z])", t, maxsplit=1)
        if len(words) > 1 and len(words[0]) < 100:
            s["_clean_title"] = words[0].strip()
        else:
            s["_clean_title"] = t[:100].strip()

    # Extrahera år från veckosträng
    year = int(week.split("-")[0]) if "-" in week else 2026

    # Bygg prompt
    top_stories = stories[:MAX_STORIES]
    prompt = build_prompt(top_stories, week, year, "")

    # Om feedback finns — lägg till som extra instruktion
    if feedback:
        prompt += f"\n\n⚠️  TIDIGARE VALIDERINGSFEL ATT ÅTGÄRDA:\n{feedback}\n"
        prompt += "Skriv om utgåvan och åtgärda dessa specifika fel. Behåll allt annat som är korrekt."

    print(f"  🤖 Skickar {len(top_stories)} stories till Sonnet...")
    print(f"     (prompt: ~{len(prompt)//1000}k tokens)")

    response = sonnet_call(prompt, SYSTEM_PROMPT)

    if not response:
        print("\n❌ Sonnet svarade inte. Försök igen?")
        return {"success": False, "error": "No response"}

    # Verifiera och rensa
    try:
        output = parse_sonnet_output(response)
    except ValueError as e:
        print(f"\n❌ Parse-fel: {e}")
        print(f"\nRådata från Sonnet (första 500 tecken):\n{response[:500]}")
        return {"success": False, "error": str(e)}

    # Skriv till content/
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output)
        f.write("\n")

    # Räkna ord
    word_count = len(output.split())
    stories_count = output.count("- kicker:")
    briefs_count = 0
    briefs_match = re.search(r"briefs:\n((?:  - .*\n)+)", output)
    if briefs_match:
        briefs_count = len(re.findall(r"^- ", briefs_match.group(1), re.MULTILINE))

    print(f"\n{'─'*40}")
    print(f"📰 UTGÅVA SKRIVEN ✅")
    print(f"  Fil:        {output_path}")
    print(f"  Ord:        ~{word_count}")
    print(f"  Stories:    ~{stories_count}")
    print(f"  Briefs:     ~{briefs_count}")
    print(f"  Modell:     Claude Sonnet 4.6")
    print(f"{'─'*40}")

    return {
        "success": True,
        "path": str(output_path),
        "word_count": word_count,
        "stories": stories_count,
        "briefs": briefs_count,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AI-Bladet skrivning")
    parser.add_argument("input", nargs="?", help="Input JSON (images)")
    parser.add_argument("--output", "-o", help="Output path")
    parser.add_argument("--feedback", "-f", help="Validation feedback to inject (for retry)")
    args = parser.parse_args()

    if args.input:
        input_path = Path(args.input)
    else:
        images = sorted(INPUT_DIR.glob("*.json"))
        if not images:
            print("Inga bild-filer hittades. Kör images.py först.")
            sys.exit(1)
        input_path = images[-1]

    week = input_path.stem  # YYYY-WW
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = CONTENT_DIR / f"{week}.md"

    result = write_issue(input_path, output_path, feedback=getattr(args, 'feedback', '') or '')
    sys.exit(0 if result.get("success") else 1)
