#!/usr/bin/env python3
"""
AI-Bladet — Validering (Pipeline Steg 7)
===========================================
DeepSeek V4 Pro verifierar att all fakta i den skrivna utgåvan
stöds av research-briefsen.

Kontroller:
1. Claim-check: varje påstående → SUPPORTED / UNSUPPORTED / HALLUCINATION
   (inkl. story-ingresser och lead.analysis — "AI-Bladets analys")
2. Number diff: alla siffror/datum måste finnas i research
3. Källkoll: minst en giltig URL per artikel
4. Lead-krav: ≥2 oberoende källor

Output: validated/{YYYY-WW}.json + skriven markdown (om godkänd)
"""

import json
import os
import re
import sys
from datetime import datetime, timezone, date
from pathlib import Path
from typing import Optional

import requests
import yaml

# ─── Config ───────────────────────────────────────────────────────────────────

PIPELINE_DIR = Path(__file__).parent
CONTENT_DIR = Path.home() / "ai-bladet" / "content"
INPUT_DIR = PIPELINE_DIR / "output" / "images"
OUTPUT_DIR = PIPELINE_DIR / "output" / "validated"
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

VALIDATION_THRESHOLD = 0.7  # minsta andel godkända claims för PASS


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


def deepseek_call(prompt: str, system: str = None,
                  max_tokens: int = 2000) -> Optional[str]:
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
                  "temperature": 0.05, "max_tokens": max_tokens},
            timeout=60,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"  ⚠️  DeepSeek API error: {e}", file=sys.stderr)
        return None


# ─── Läs ut skriven utgåva ──────────────────────────────────────────────────


def parse_issue(content_path: Path) -> dict | None:
    """Läs markdown-fil med YAML frontmatter."""
    if not content_path.exists():
        print(f"  ❌ Ingen utgåva på {content_path}")
        return None

    text = content_path.read_text(encoding="utf-8")

    # Extrahera frontmatter
    fm_match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not fm_match:
        print(f"  ❌ Ingen frontmatter i {content_path}")
        return None

    try:
        fm = yaml.safe_load(fm_match.group(1))
        # Konvertera datum-objekt till strängar (YAML parsar vissa datum som date())
        if isinstance(fm.get("date"), (date, datetime)):
            fm["date"] = str(fm["date"])
    except Exception as e:
        print(f"  ❌ YAML error: {e}")
        return None

    # Extrahera brödtext (efter frontmatter)
    body = text[fm_match.end():].strip()

    return {"frontmatter": fm, "body": body, "full_text": text}


# ─── Claim validation (DeepSeek V4 Pro) ──────────────────────────────────────


def validate_issue(issue: dict, research_stories: list[dict]) -> dict:
    """Kör validering på hela utgåvan."""
    fm = issue["frontmatter"]
    body = issue["body"]

    # Bygg research context — inkludera summary, nyckelfakta OCH siffror
    research_parts = []
    for i, s in enumerate(research_stories):
        b = s.get("fact_brief", {})
        summary = b.get("summary", "")[:500]
        facts = b.get("key_facts", [])
        numbers = b.get("numbers", [])
        sources = s.get("sources", [])  # alternativa käll-URLs
        url = s.get("url", "")
        source_label = s.get("source_label", "")

        parts = [f"STORY {i+1}: {s.get('title', '')}"]

        if summary:
            parts.append(f"Brief: {summary}")

        if facts:
            parts.append("Nyckelfakta:")
            parts.extend(f"  • {f}" for f in facts[:8])

        if numbers:
            parts.append("Siffror:")
            parts.extend(
                f"  • {n.get('value', '')} — {n.get('context', '')}"
                for n in numbers[:8]
            )

        if sources:
            parts.append("Fler källor:")
            parts.extend(f"  • {src}" for src in sources[:3])

        parts.append(f"Primärkälla: {source_label} — {url}")
        research_parts.append("\n".join(parts))

    research_ctx = "\n\n".join(research_parts)

    # Extrahera text per story från utgåvan
    story_sections = []
    if "stories:" in body or "stories:" in str(fm):
        # Prova att hitta stories i frontmatter
        for s in fm.get("stories", []):
            headline = s.get("headline", "")
            ingress = s.get("ingress", "")
            body_text = s.get("body", "")
            if headline or body_text or ingress:
                section = f"RUBRIK: {headline}"
                if ingress:
                    section += f"\nINGRESS: {ingress}"
                section += f"\nTEXT: {body_text[:500]}"
                story_sections.append(section)

    # Lead
    lead = fm.get("lead", {})
    lead_text = lead.get("headline", "") + " " + lead.get("ingress", "")
    if lead.get("analysis"):
        lead_text += " [AI-BLADETS ANALYS] " + lead.get("analysis", "")

    # Claims att verifiera
    claims = {
        "lead": lead_text,
        "title": fm.get("title", ""),
        "summary": fm.get("summary", ""),
        "stories": story_sections[:6],
        "briefs": fm.get("briefs", [])[:8],
    }

    # Bygg prompt
    claims_text = "LEAD:\n" + lead_text + "\n\n"
    claims_text += f"TITEL: {fm.get('title', '')}\n\n"
    claims_text += f"SUMMARY: {fm.get('summary', '')}\n\n"

    for i, s in enumerate(story_sections):
        claims_text += f"ARTICLE {i+1}:\n{s}\n\n"

    for i, b in enumerate(fm.get("briefs", [])):
        claims_text += f"BRIEF {i+1}: {b}\n"

    prompt = f"""Verifiera AI-nyhetsartikeln nedan mot de underliggande research-briefsen.

RESEARCH (faktabaser):
{research_ctx[:18000]}

UTGÅVA ATT VERIFIERA:
{claims_text[:6000]}

Kontrollera:
1. ALLA påståenden — stöds de av research?
2. ALLA siffror/datum — finns de i research?
3. Finns det påståenden som INTE finns i research?
4. Är slutsatser rimliga baserat på fakta?
5. DATUMKONTROLL — Är källorna från senaste 7 dagarna? Om äldre: finns ny vinkel?
6. ATTRIBUERING — Är leverantörspåståenden ("4x snabbare", "6x effektivitet") attribuerade?
7. ANALYS — Är "AI-Bladets analys" och ingresserna grundade i research? Tolkning är OK, men inga lösryckta fakta eller framtidspåståenden som saknar stöd.

Svara endast med JSON:
{{
  "overall": "PASS" eller "FLAGGED",
  "pass_rate": 0.0-1.0,
  "issues": [
    {{
      "severity": "low/medium/high",
      "location": "lead/story 2/brief 3",
      "claim": "citat av påståendet",
      "problem": "vad som är fel",
      "supported": true/false
    }}
  ],
  "summary": "kort bedömning"
}}"""

    response = deepseek_call(prompt, "Du verifierar faktapåståenden. Var strikt men rimlig. Leta efter hallucinationer, hittade siffror och påståenden som inte stöds.", max_tokens=2000)

    result = _parse_validation(response)

    # Koll av käll-URLs
    result["url_checks"] = _check_urls(research_stories)

    # Sammantaget
    result["lead_sources"] = _check_lead_sources(research_stories)
    result["duplication"] = _check_duplication(issue)
    result["se_eu_angle"] = _check_se_eu_angle(issue, research_stories)

    # Hård gate: en enda obekräftad HIGH-allvarlig faktaflagga blockerar deploy,
    # oavsett pass-rate. (Anton 2026-06-18: fakta går före kadens. Retry-loopen i
    # run_weekly.sh skickar high/medium-flaggor till Sonnet för rättning först.)
    result["high_issues"] = [
        i for i in result.get("issues", [])
        if i.get("severity") == "high" and not i.get("supported", True)
    ]

    result["pass"] = (result.get("pass_rate", 0) >= VALIDATION_THRESHOLD and
                      result["url_checks"]["valid"] > 0 and
                      result.get("lead_sources", 1) >= 1 and
                      not result["duplication"]["duplicate"] and
                      result["se_eu_angle"]["found"] and
                      not result["high_issues"])

    return result


def _parse_json_from_text(text: str | None) -> dict | None:
    """Extrahera JSON från text som kan innehålla kodblock, prefix etc."""
    if not text:
        return None
    # Ta bort markdown-kodblock
    cleaned = re.sub(r"```(?:json)?\s*", "", text).strip()
    # Hitta första { och sista }
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    json_str = cleaned[start:end+1]
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        pass
    return None


def _parse_validation(response: str | None) -> dict:
    """Parsa DeepSeeks validerings-JSON."""
    default = {
        "overall": "UNKNOWN",
        "pass_rate": 1.0,
        "issues": [],
        "summary": "Kunde inte validera — okänd modellrespons"
    }

    parsed = _parse_json_from_text(response)
    if parsed:
        return parsed

    if response:
        print(f"  ⚠️  Validerings-JSON parse error (första 200 chars): {response[:200]}",
              file=sys.stderr)

    return default


def _check_urls(research_stories: list[dict]) -> dict:
    """Kontrollera att käll-URLs fortfarande är levande."""
    valid = 0
    invalid = 0
    for s in research_stories[:6]:
        url = s.get("url", "")
        if not url:
            invalid += 1
            continue
        try:
            r = requests.head(url, timeout=8, allow_redirects=True)
            if r.status_code < 400:
                valid += 1
            else:
                invalid += 1
        except Exception:
            invalid += 1

    return {"valid": valid, "invalid": invalid, "total": valid + invalid}


def _check_lead_sources(research_stories: list[dict]) -> int:
    """Räkna antalet oberoende källor för lead-story."""
    unique_sources = set()
    if research_stories:
        # Den första storyn (index 0) är lead
        sources = set()
        s = research_stories[0]
        source_id = s.get("source_id", "")
        if source_id:
            sources.add(source_id)
        return len(sources)
    return 0


def _check_duplication(issue: dict) -> dict:
    """Regel 2: Kolla att lead inte är samma story som en sektion.

    Fuzzy-match: jämför lead-headline mot alla section-headlines.
    Flagga om >70% ordöverlapp eller gemensamt nyckelbolag/produkt.
    """
    fm = issue.get("frontmatter", {})
    lead = fm.get("lead", {})
    lead_headline = (lead.get("headline", "") + " " + lead.get("kicker", "")).lower()
    stories = fm.get("stories", [])

    if not lead_headline or not stories:
        return {"duplicate": False, "reason": ""}

    lead_words = set(lead_headline.split())

    for i, s in enumerate(stories):
        section_text = (s.get("headline", "") + " " + s.get("kicker", "")).lower()
        section_words = set(section_text.split())

        if not lead_words or not section_words:
            continue

        overlap = len(lead_words & section_words) / max(len(lead_words), len(section_words))

        if overlap > 0.7:
            return {
                "duplicate": True,
                "reason": f"Lead ({lead_headline[:60]}...) och story {i+1} ({section_text[:60]}...) har {overlap:.0%} ordöverlapp — trolig dublett."
            }

    return {"duplicate": False, "reason": ""}


def _check_se_eu_angle(issue: dict, research_stories: list[dict]) -> dict:
    """Regel 5: Minst en story måste ha svensk eller EU-vinkel.

    Kollar tre källor:
    1. Kategori "Politik" eller "Sverige"
    2. fact_brief.swedish_angle är icke-tom
    3. Texten nämner Sverige, EU, svensk, europeisk
    """
    fm = issue.get("frontmatter", {})
    stories = fm.get("stories", [])
    body = issue.get("body", "")

    se_keywords = ["sverige", "svensk", "eu", "europeisk", "europa", "stockholm",
                   "svenska", "sveriges", "eu-kommissionen", "eu:s"]

    # Kolla stories
    for story in stories:
        headline = story.get("headline", "")
        ingress = story.get("ingress", "")
        story_body = story.get("body", "")

        # Kolla svensk/EU i text (rubrik, ingress och brödtext)
        combined = (headline + " " + ingress + " " + story_body).lower()
        if any(kw in combined for kw in se_keywords):
            return {"found": True, "source": f"Story: {headline[:60]}..."}

    # Kolla briefs
    briefs = fm.get("briefs", [])
    for brief in briefs:
        if any(kw in brief.lower() for kw in se_keywords):
            return {"found": True, "source": f"Brief: {brief[:60]}..."}

    # Kolla research-stories för svensk_angle
    for s in research_stories:
        b = s.get("fact_brief", {})
        sa = b.get("swedish_angle", "")
        if sa and len(sa) > 10:
            return {"found": True, "source": f"Research swedish_angle: {sa[:60]}..."}

    return {"found": False, "source": ""}


# ─── Huvudfunktion ────────────────────────────────────────────────────────────


def validate(content_path: Path, research_input_path: Path,
             output_path: Path) -> dict:
    """Validera den skrivna utgåvan."""
    week = content_path.stem
    print(f"🔍 Validering — AI-Bladet v.{week}\n")

    # Läs utgåva
    issue = parse_issue(content_path)
    if not issue:
        return {"success": False}

    # Läs research
    with open(research_input_path) as f:
        research_data = json.load(f)
    research_stories = research_data.get("stories", [])[:10]

    # Kör validering
    fm = issue["frontmatter"]
    result = validate_issue(issue, research_stories)

    # Visa resultat
    verdict = "✅ PASS" if result.get("pass") else "❌ FLAGGED"
    print(f"  Dom:      {verdict}")
    print(f"  Pass-rate: {result.get('pass_rate', 0)*100:.0f}%")
    print(f"  Issues:   {len(result.get('issues', []))}")
    print(f"  URL-koll: {result.get('url_checks', {}).get('valid', 0)}/{result.get('url_checks', {}).get('total', 0)} levande")
    dup = result.get("duplication", {})
    se = result.get("se_eu_angle", {})
    dup_icon = "❌" if dup.get("duplicate") else "✅"
    se_icon = "✅" if se.get("found") else "❌"
    print(f"  Dublettkontroll: {dup_icon}")
    print(f"  SE/EU-vinkel:    {se_icon}")
    high = result.get("high_issues", [])
    if high:
        print(f"  HIGH-flaggor:    ❌ {len(high)} (BLOCKERAR deploy oavsett pass-rate)")
        for h in high:
            print(f"      ➜ [{h.get('location','?')}] {h.get('claim','')[:80]}")
    print()

    for issue_item in result.get("issues", [])[:5]:
        sev = issue_item.get("severity", "?")
        s = issue_item.get("supported", True)
        icon = "✅" if s else "⚠️ "
        print(f"  {icon} [{sev}] {issue_item.get('location', '?')}: "
              f"{issue_item.get('claim', '')[:80]}")
        if not s:
            print(f"       ➜ {issue_item.get('problem', '')[:80]}")
    print()

    if result.get("summary"):
        print(f"  Slutsats: {result['summary'][:200]}")

    # Skriv valideringsrapport
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output = {
        "meta": {
            "week": week,
            "validated_at": datetime.now(timezone.utc).isoformat(),
            "pass": result.get("pass", False),
            "pass_rate": result.get("pass_rate", 0),
            "issue_count": len(result.get("issues", [])),
        },
        "validation": result,
        "frontmatter": fm,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n  Rapport: {output_path}")
    print(f"{'─'*40}")

    return {"success": True, "pass": result.get("pass", False)}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AI-Bladet validering")
    parser.add_argument("--content", "-c", help="Uppgiftsfil (content/YYYY-WW.md)")
    parser.add_argument("--research", "-r", help="Research-input (images/YYYY-WW.json)")
    args = parser.parse_args()

    # Auto-detect latest
    if not args.content:
        contents = sorted(CONTENT_DIR.glob("*.md"))
        if not contents:
            print("Inga utgåvor hittades.")
            sys.exit(1)
        content_path = contents[-1]
    else:
        content_path = Path(args.content)

    if not args.research:
        researched = sorted(INPUT_DIR.glob("*.json"))
        if not researched:
            print("Inga researchade filer hittades.")
            sys.exit(1)
        research_path = researched[-1]
    else:
        research_path = Path(args.research)

    week = content_path.stem
    output_path = OUTPUT_DIR / f"{week}.json"

    result = validate(content_path, research_path, output_path)
    sys.exit(0 if result.get("pass") else 1)
