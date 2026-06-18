#!/usr/bin/env python3
"""
AI-Bladet — Research & Fact Brief (Pipeline Steg 4)
=====================================================
Hämtar full text för de bäst scoreade stories och skapar
fakta-briefs med DeepSeek V4 Pro.

Input:  output/scored/{YYYY-WW}.json
Output: output/researched/{YYYY-WW}.json
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests
import trafilatura

# ─── Config ───────────────────────────────────────────────────────────────────

PIPELINE_DIR = Path(__file__).parent
INPUT_DIR = PIPELINE_DIR / "output" / "scored"
OUTPUT_DIR = PIPELINE_DIR / "output" / "researched"
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
JINA_BASE = "https://r.jina.ai"

MAX_STORIES = 15  # antal stories att researca
MAX_TEXT_CHARS = 5000  # max tecken per fulltext (sparar tokens)


# ─── DeepSeek helper ─────────────────────────────────────────────────────────


def _get_deepseek_key() -> Optional[str]:
    key = os.getenv("DEEPSEEK_API_KEY", "")
    if key:
        return key
    env_path = Path.home() / ".hermes" / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("DEEPSEEK_API_KEY="):
                return line.split("=", 1)[1]
    return None


def deepseek_call(prompt: str, system: str = None, max_tokens: int = 1000) -> Optional[str]:
    key = _get_deepseek_key()
    if not key:
        raise ValueError("DEEPSEEK_API_KEY saknas")
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    try:
        r = requests.post(
            DEEPSEEK_URL,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": "deepseek-chat", "messages": messages,
                  "temperature": 0.1, "max_tokens": max_tokens},
            timeout=60
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"  ⚠️  DeepSeek API-fel: {e}", file=sys.stderr)
        return None


# ─── Fulltext extraction ─────────────────────────────────────────────────────


def extract_text(url: str) -> str:
    """Hämta full text via Jina Reader, fallback till trafilatura."""
    # Jina Reader
    try:
        r = requests.get(f"{JINA_BASE}/{url}", timeout=20,
                         headers={"User-Agent": "AI-Bladet/1.0"})
        if r.status_code == 200 and len(r.text) > 200:
            # Rensa bort eventuell Jina-header
            text = r.text.strip()
            # Jina returnerar ibland en kort introduktion före innehållet
            # Ta bort före första rubriken om texten är tillräckligt lång
            if len(text) > MAX_TEXT_CHARS:
                text = text[:MAX_TEXT_CHARS]
            return text
    except Exception as e:
        print(f"    ⚠️  Jina Reader error: {e}")

    # Fallback: trafilatura
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded)
            if text:
                return text[:MAX_TEXT_CHARS]
    except Exception as e:
        print(f"    ⚠️  trafilatura error: {e}")

    return ""


def best_url(candidate: dict) -> str:
    """Välj bästa URL för en story (prioritera originell källa)."""
    urls = candidate.get("url", "")

    # Kolla om vi har ursprungs-URL (inte en media-aggregator)
    source_id = candidate.get("source_id", "")
    url = ""

    if isinstance(urls, str):
        url = urls
    elif isinstance(urls, list) and urls:
        url = urls[0]

    # Rensa URL
    if url:
        # Ta bort tracking-parametrar
        url = re.sub(r"\?utm_.*$", "", url)
        url = re.sub(r"\?ref=.*$", "", url)
        url = re.sub(r"#.*$", "", url)

    return url


def fetch_story(candidate: dict) -> dict:
    """Hämta full info för en story."""
    url = best_url(candidate)
    title = candidate.get("title", "Untitled")

    print(f"    📄 Fetching: {title[:60]}...", end=" ", flush=True)

    full_text = extract_text(url) if url else ""

    if full_text:
        print(f"{len(full_text)} chars")
    else:
        print("no text extracted")

    return {
        "full_text": full_text,
        "fetched_url": url if url else "",
        "fetch_success": bool(full_text and len(full_text) > 100),
    }


# ─── Fact Brief (DeepSeek V4 Pro) ────────────────────────────────────────────

BRIEF_SYSTEM = """Du är en AI-nyhetsresearcher. Din uppgift: extrahera en faktabrief från en artikel.

Briefen ska vara:
- Faktabaserad (INVENTERA INGENTING — bara det som står i texten)
- Strukturerad i rubriker
- Innehålla: nyckelfakta, siffror, citat, svensk vinkel, källa, PUBLICERINGSDATUM

Var kortfattad. Hitta på ingenting. Publiceringsdatum är KRITISKT — leta efter datum i texten, URL, eller metadata."""


def create_brief(title: str, full_text: str, ai_score: dict) -> Optional[dict]:
    """Använd DeepSeek V4 Pro för att skapa en fakta-brief från texten."""
    if not full_text or len(full_text) < 100:
        return None

    prompt = f"""Extrahera en strukturerad faktabrief från följande nyhetsartikel.

TITEL: {title}
AI-KATEGORI: {ai_score.get('category', 'Ovrigt')}

ARTIKELTEXT:
{full_text[:4000]}

Svara med JSON-följande struktur:
{{
  "summary": "kort sammanfattning 2-3 meningar",
  "source_date": "YYYY-MM-DD (publiceringsdatum för artikeln — leta i text, URL eller metadata)",
  "key_facts": ["faktapunkt 1", "faktapunkt 2"],
  "numbers": [{{"value": "siffra/statistik", "context": "vad den betyder"}}],
  "quotes": [{{"text": "citat", "speaker": "vem"}}],
  "swedish_angle": "relevant för svenska läsare eller tom sträng",
  "source_quality": "original/high/medium/low"
}}
Om du inte hittar något datum, sätt source_date till "okänt"."""

    response = deepseek_call(prompt, BRIEF_SYSTEM, max_tokens=800)
    if not response:
        return None

    # Parse JSON
    try:
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
    except (json.JSONDecodeError, Exception) as e:
        print(f"    ⚠️  Brief parse error: {e}", file=sys.stderr)

    return {
        "summary": full_text[:200],
        "key_facts": ["Kunde inte extrahera struktur"],
        "source_quality": "unknown"
    }


# ─── Huvudfunktion ────────────────────────────────────────────────────────────


def research(input_path: Path, output_path: Path, max_stories: int = MAX_STORIES) -> dict:
    """Kör research på scoreade kandidater."""
    with open(input_path) as f:
        data = json.load(f)

    candidates = data["candidates"]
    print(f"🔬 Research: {len(candidates)} tillgängliga, bearbetar topp {max_stories}\n")

    selected = candidates[:max_stories]
    researched = []

    for i, c in enumerate(selected):
        score = c.get("final_score", 0)
        title = c.get("title", "Untitled")
        print(f"\n  [{i+1}/{max_stories}] ({score:.0f}p) {title[:70]}")

        # Steg 1: Hämta full text
        fetch_result = fetch_story(c)

        # Steg 2: Skapa faktabrief
        full_text = fetch_result["full_text"]
        ai_score = c.get("_ai_score", {})

        brief = None
        if fetch_result["fetch_success"]:
            print(f"    🧠 Briefing...", end=" ", flush=True)
            brief = create_brief(title, full_text, ai_score)
            if brief:
                print("OK ✅")
            else:
                print("failed ⚠️")

        researched.append({
            "source_id": c.get("source_id", ""),
            "source_label": c.get("source_label", ""),
            "tier": c.get("tier"),
            "score": score,
            "ai_score": ai_score,
            "category": ai_score.get("category", "Övrigt"),
            "lead_potential": ai_score.get("lead_potential", 1),
            "title": title,
            "url": fetch_result["fetched_url"],
            "full_text_excerpt": full_text[:500] if full_text else "",
            "fetch_success": fetch_result["fetch_success"],
            "fact_brief": brief or {"summary": "Kunde inte extrahera text", "key_facts": []},
        })

    # Skriv output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output = {
        "meta": {
            "week": input_path.stem,
            "stories_researched": len(researched),
            "fetch_success": sum(1 for r in researched if r["fetch_success"]),
            "research_time": datetime.now(timezone.utc).isoformat(),
        },
        "stories": researched,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # Sammanfattning
    success = output["meta"]["fetch_success"]
    print(f"\n{'─'*40}")
    print(f"📊 RESEARCH RESULTAT")
    print(f"  Stories researchade: {len(researched)}")
    print(f"  Fulltext hämtad:     {success}/{len(researched)}")
    print(f"  Fact briefs:         {sum(1 for r in researched if r.get('fact_brief'))}")
    print(f"  Output:              {output_path}")
    print(f"{'─'*40}")

    return {"researched": len(researched), "success": success}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AI-Bladet research")
    parser.add_argument("input", nargs="?", help="Input JSON (scored)")
    parser.add_argument("--limit", type=int, default=MAX_STORIES, help="Max stories to research")
    args = parser.parse_args()

    if args.input:
        input_path = Path(args.input)
    else:
        scored = sorted(INPUT_DIR.glob("*.json"))
        if not scored:
            print("Inga scorede filer hittades.")
            sys.exit(1)
        input_path = scored[-1]

    week = input_path.stem
    output_path = OUTPUT_DIR / f"{week}.json"

    result = research(input_path, output_path, args.limit)
    sys.exit(0)
