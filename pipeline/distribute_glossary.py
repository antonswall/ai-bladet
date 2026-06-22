#!/usr/bin/env python3
"""
AI-Bladet — Glossary Distribution Module
==========================================
Varje vecka extraheras en AI-term från numret och blir en permanent SEO-sida.
Bygger en växande kunskapsbank över tid.

Input:  content/YYYY-WW.md (via --issue)
Output: public/ordbok/[term-slug].html
         public/ordbok/index.html (uppdateras)
         pipeline/output/distribution/glossary/YYYY-WW.json

API-kostnad: ~$0.0003 per vecka (DeepSeek)
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
DIST_OUTPUT_DIR = PIPELINE_DIR / "output" / "distribution" / "glossary"
PROJECT_DIR = Path.home() / "ai-bladet"
PUBLIC_DIR = PROJECT_DIR / "public"
GLOSSARY_DIR = PUBLIC_DIR / "ordbok"

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
                  max_tokens: int = 600, temperature: float = 0.3) -> Optional[str]:
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


# ─── Term-generering ─────────────────────────────────────────────────────────

def generate_glossary_term(issue: dict) -> Optional[dict]:
    """
    Identifiera en AI-term från veckans innehåll och generera förklaring.
    Returnerar: {term, slug, explanation, example, related, source_story}
    """
    lead = issue.get("lead", {})
    stories = issue.get("stories", [])

    context_parts = []
    for s in [lead] + stories[:6]:
        headline = s.get("headline", "")
        ingress = s.get("ingress", "")
        body = s.get("body", "")
        if headline:
            context_parts.append(f"{headline}\n{ingress}\n{body[:200]}")

    context = "\n---\n".join(context_parts)

    prompt = f"""Identifiera EN AI-term eller tekniskt begrepp som förekommer i veckans AI-nyheter.
Termen ska vara något som en icke-teknisk svensk läsare kan vara nyfiken på.

Returnera JSON:
{{
  "term": "begreppet",
  "slug": "begreppet-i-lowercase-med-bindestreck",
  "explanation": "Förklara termen på enkel svenska — som om du förklarar för någon som precis börjat intressera sig för AI. Max 150 tecken.",
  "example": "Ett konkret exempel från veckans nyheter som illustrerar termen. Max 200 tecken.",
  "related": ["relaterad-term-1", "relaterad-term-2"],
  "source_story": "Rubriken på storyn där termen förekommer"
}}

Regler:
- Välj en term som är relevant för veckans innehåll, inte en slumpmässig AI-term
- Använd enkel, tydlig svenska i förklaringen
- Gör sluggen URL-vänlig (små bokstäver, bindestreck, inga specialtecken)

Här är veckans innehåll:
{context[:3000]}
"""

    system = "Du är en svensk teknikpedagog. Förklara AI-begrepp enkelt och koncist."

    result = deepseek_call(prompt, system=system, max_tokens=600, temperature=0.3)
    if not result:
        return None

    # Parsa JSON
    try:
        # Hantera kodblock
        cleaned = re.sub(r"```(?:json)?\s*", "", result).strip()
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1:
            return None
        return json.loads(cleaned[start:end + 1])
    except json.JSONDecodeError:
        return None


# ─── HTML-generering ─────────────────────────────────────────────────────────

_TERM_TEMPLATE = """<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{term} — AI-Bladets ordbok</title>
    <meta name="description" content="{explanation}">
    <link rel="canonical" href="{SITE_URL}/ordbok/{slug}">
    <link rel="stylesheet" href="/static/style.css">
    <style>
        .glossary-term {{ max-width: 680px; margin: 4rem auto; padding: 0 1rem; }}
        .glossary-term h1 {{ font-family: 'Fraunces', serif; font-size: 2.2rem; margin-bottom: 0.5rem; }}
        .glossary-term .definition {{ font-size: 1.2rem; line-height: 1.6; color: #444; margin: 1.5rem 0; }}
        .glossary-term .example {{ background: #f8f5f0; padding: 1.2rem 1.5rem; border-radius: 6px; margin: 1.5rem 0; }}
        .glossary-term .example-label {{ font-weight: 600; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; color: #888; }}
        .glossary-term .related {{ margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #eee; }}
        .glossary-term .related a {{ color: #c41230; text-decoration: none; margin-right: 1rem; }}
        .glossary-back {{ margin-top: 3rem; }}
        .glossary-back a {{ color: #888; text-decoration: none; font-size: 0.9rem; }}
    </style>
</head>
<body>
    <nav class="site-nav">
        <a href="/" class="masthead">AI-Bladet</a>
        <div class="nav-links">
            <a href="/">Hem</a>
            <a href="/arkiv">Arkiv</a>
            <a href="/ordbok">Ordbok</a>
            <a href="/om">Om</a>
        </div>
    </nav>
    <main>
        <article class="glossary-term">
            <h1>{term}</h1>
            <p class="definition">{explanation}</p>
            {example_html}
            <p class="meta">📰 Från vecka {week}: <em>{source_story}</em></p>
            {related_html}
            <div class="glossary-back"><a href="/ordbok">← Tillbaka till ordboken</a></div>
        </article>
    </main>
</body>
</html>"""


def build_term_page(term_data: dict, week: int) -> str:
    """Generera HTML-sida för en ordboksterm."""
    example_html = ""
    if term_data.get("example"):
        example_html = f'<div class="example"><span class="example-label">Exempel från veckans nyheter</span><p>{term_data["example"]}</p></div>'

    related_html = ""
    if term_data.get("related"):
        links = " ".join(
            f'<a href="/ordbok/{r}">{r.replace("-", " ").title()}</a>'
            for r in term_data["related"]
        )
        related_html = f'<div class="related">Relaterade: {links}</div>'

    return _TERM_TEMPLATE.format(
        term=term_data["term"],
        slug=term_data["slug"],
        explanation=term_data["explanation"],
        example_html=example_html,
        related_html=related_html,
        week=week,
        source_story=term_data.get("source_story", ""),
        SITE_URL=SITE_URL,
    )


_INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI-ordbok — AI-Bladet</title>
    <meta name="description" content="En växande ordbok med AI-begrepp förklarade på enkel svenska.">
    <link rel="canonical" href="{SITE_URL}/ordbok">
    <link rel="stylesheet" href="/static/style.css">
    <style>
        .glossary-index {{ max-width: 680px; margin: 3rem auto; padding: 0 1rem; }}
        .glossary-index h1 {{ font-family: 'Fraunces', serif; font-size: 2.2rem; }}
        .glossary-index .intro {{ font-size: 1.1rem; line-height: 1.6; color: #555; margin: 1rem 0 2rem; }}
        .glossary-list {{ list-style: none; padding: 0; }}
        .glossary-list li {{ padding: 1rem 0; border-bottom: 1px solid #eee; }}
        .glossary-list li:last-child {{ border-bottom: none; }}
        .glossary-list a {{ font-size: 1.2rem; font-weight: 700; color: #111; text-decoration: none; }}
        .glossary-list a:hover {{ color: #c41230; }}
        .glossary-list .meta {{ font-size: 0.85rem; color: #888; margin-top: 0.25rem; }}
    </style>
</head>
<body>
    <nav class="site-nav">
        <a href="/" class="masthead">AI-Bladet</a>
        <div class="nav-links">
            <a href="/">Hem</a>
            <a href="/arkiv">Arkiv</a>
            <a href="/ordbok">Ordbok</a>
            <a href="/om">Om</a>
        </div>
    </nav>
    <main>
        <div class="glossary-index">
            <h1>AI-ordbok</h1>
            <p class="intro">Varje vecka förklarar vi ett AI-begrepp på enkel svenska — med exempel från veckans nyheter. En växande kunskapsbank för dig som vill förstå AI, ett ord i taget.</p>
            <ul class="glossary-list">
                {terms_html}
            </ul>
        </div>
    </main>
</body>
</html>"""


def build_index(all_terms: list) -> str:
    """Bygg ordboksindex med alla termer."""
    terms_html = ""
    for t in all_terms:
        terms_html += f'<li><a href="/ordbok/{t["slug"]}">{t["term"]}</a><div class="meta">Vecka {t["week"]} — {t.get("source_story", "")[:80]}</div></li>\n'

    return _INDEX_TEMPLATE.format(
        terms_html=terms_html,
        SITE_URL=SITE_URL,
    )


# ─── Huvudfunktion ───────────────────────────────────────────────────────────

def distribute_glossary(issue_path: str, dry_run: bool = False) -> bool:
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

    print(f"  📖 Vecka {week}: genererar ordboksterm...", end=" ", flush=True)

    # Skapa output-kataloger
    GLOSSARY_DIR.mkdir(parents=True, exist_ok=True)
    DIST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if dry_run:
        term_data = {
            "term": "Inferens (dry-run)",
            "slug": "inferens",
            "explanation": "Testförklaring för dry-run.",
            "example": "Testexempel från veckans nyheter.",
            "related": ["traning", "modell"],
            "source_story": "Test-story"
        }
        print("(dry-run)")
    else:
        term_data = generate_glossary_term(issue)
        if not term_data:
            print("❌ Misslyckades")
            return False
        print(f"'{term_data['term']}'")

    # Spara JSON
    meta_path = DIST_OUTPUT_DIR / f"{year}-{week}.json"
    meta_data = {**term_data, "week": week, "year": year}
    meta_path.write_text(json.dumps(meta_data, indent=2, ensure_ascii=False), encoding="utf-8")

    # Bygg term-sidan
    term_path = GLOSSARY_DIR / f"{term_data['slug']}.html"
    term_html = build_term_page(term_data, week)
    term_path.write_text(term_html, encoding="utf-8")

    # Samla alla termer för index
    all_terms = []
    for json_file in sorted(DIST_OUTPUT_DIR.glob("*.json")):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            if not data.get("dry_run"):
                all_terms.append(data)
        except Exception:
            pass

    if not all_terms:
        all_terms = [meta_data]

    # Bygg index
    index_path = GLOSSARY_DIR / "index.html"
    index_html = build_index(all_terms)
    index_path.write_text(index_html, encoding="utf-8")

    print(f"    ➡ /ordbok/{term_data['slug']}.html + index")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI-Bladet — Glossary distribution")
    parser.add_argument("--issue", required=True, help="Sökväg till issue-fil")
    parser.add_argument("--dry-run", action="store_true", help="Simulera utan API-anrop")
    args = parser.parse_args()

    success = distribute_glossary(args.issue, dry_run=args.dry_run)
    sys.exit(0 if success else 1)
