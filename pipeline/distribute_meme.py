#!/usr/bin/env python3
"""
AI-Bladet — Meme Distribution Module
======================================
Genererar ett meme-kort för veckans roligaste/absurdaste AI-nyhet.

Input:  content/YYYY-WW.md (via --issue)
Output: public/memes/YYYY-WW.png
         pipeline/output/distribution/memes/YYYY-WW.json

Bildgenerering: Pollinations.ai (gratis, ingen API-nyckel)
Text overlay: HTML → PNG via headless Chrome

API-kostnad: ~$0.0002 per vecka (DeepSeek — identifiera story + generera text)
"""

import argparse
import json
import os
import re
import sys
import tempfile
import time
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

# ─── Config ───────────────────────────────────────────────────────────────────

PIPELINE_DIR = Path(__file__).parent
DIST_OUTPUT_DIR = PIPELINE_DIR / "output" / "distribution" / "memes"
PROJECT_DIR = Path.home() / "ai-bladet"
PUBLIC_DIR = PROJECT_DIR / "public"
MEMES_DIR = PUBLIC_DIR / "memes"

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
POLLINATIONS_URL = "https://image.pollinations.ai/prompt"


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
                  max_tokens: int = 500, temperature: float = 0.5) -> Optional[str]:
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


# ─── Meme-generering ──────────────────────────────────────────────────────────

def generate_meme_data(issue: dict) -> Optional[dict]:
    """
    Identifiera veckans mest meme-vänliga story och generera text + bildprompt.
    Returnerar: {top_text, bottom_text, image_prompt, source_story, reason}
    """
    lead = issue.get("lead", {})
    stories = issue.get("stories", [])

    context_parts = []
    for s in [lead] + stories[:5]:
        headline = s.get("headline", "")
        ingress = s.get("ingress", "")
        if headline:
            context_parts.append(f"• {headline}: {ingress[:150]}")

    context = "\n".join(context_parts)

    prompt = f"""Identifiera den roligaste eller mest absurda AI-nyheten från veckans AI-Bladet.
Skapa ett meme-kort för sociala medier.

Returnera JSON:
{{
  "top_text": "MEME-TEXT HÖGST UPP (max 5 ord, versaler, humoristisk)",
  "bottom_text": "meme-text längst ner (max 8 ord, humoristisk punchline)",
  "image_prompt": "beskrivning för AI-bildgenerering — EN mening på engelska, konkret scen/objekt/stil. Använd stil: 'meme template style, bold and simple, high contrast'",
  "source_story": "rubriken på storyn",
  "reason": "varför denna story är meme-värdig (1 mening)"
}}

Regler:
- Meme-texten ska vara rolig men inte elak
- Undvik intern AI-jargong — ska funka för vanliga svenskar
- Bildprompten ska vara konkret (t.ex. "a robot eating a calculator, meme template style" inte "AI doing funny thing")
- Svensk meme-text, engelsk bildprompt

Här är veckans stories:
{context}
"""

    system = "Du är en kreativ meme-skapare. Skapa roliga, delbara memes om AI-nyheter."

    result = deepseek_call(prompt, system=system, max_tokens=500, temperature=0.5)
    if not result:
        return None

    try:
        cleaned = re.sub(r"```(?:json)?\s*", "", result).strip()
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1:
            return None
        return json.loads(cleaned[start:end + 1])
    except json.JSONDecodeError:
        return None


# ─── Bildgenerering ───────────────────────────────────────────────────────────

def generate_meme_image(prompt: str) -> Optional[bytes]:
    """
    Generera bild via Pollinations.ai (gratis).
    Returnerar bildbytes eller None.
    """
    encoded = urllib.parse.quote(prompt)
    url = f"{POLLINATIONS_URL}/{encoded}?width=1080&height=1080&nologo=true"

    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return r.content
    except Exception as e:
        print(f"  ⚠️ Pollinations API error: {e}", file=sys.stderr)
        return None


def render_meme_with_text(image_path: Path, top_text: str, bottom_text: str,
                          output_path: Path) -> bool:
    """
    Rendera meme-bild med text overlay via headless Chrome.
    """
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    width: 1080px;
    height: 1080px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    align-items: center;
    background: #000;
    font-family: 'Impact', 'Arial Black', sans-serif;
    color: #fff;
    text-align: center;
    text-shadow: 3px 3px 0 #000, -2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000;
    overflow: hidden;
    position: relative;
}}
img {{
    position: absolute;
    top: 0; left: 0;
    width: 1080px;
    height: 1080px;
    object-fit: cover;
    z-index: 0;
}}
.top-text, .bottom-text {{
    position: relative;
    z-index: 1;
    font-size: 72px;
    letter-spacing: 2px;
    padding: 30px 40px;
    line-height: 1.1;
}}
.top-text {{ margin-top: 40px; }}
.bottom-text {{ margin-bottom: 40px; }}
</style>
</head>
<body>
<img src="file://{image_path}">
<div class="top-text">{top_text.upper()}</div>
<div class="bottom-text">{bottom_text.lower()}</div>
</body>
</html>"""

    with tempfile.NamedTemporaryFile(suffix=".html", mode="w", encoding="utf-8", delete=False) as f:
        html_path = f.name
        f.write(html)

    try:
        cmd = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "--headless",
            f"--screenshot={output_path}",
            f"--window-size=1080,1080",
            "--hide-scrollbars",
            "--disable-gpu",
            f"file://{html_path}",
        ]
        result = os.system(" ".join(f"'{c}'" for c in cmd))
        if result != 0:
            print(f"  ⚠️ Chrome exit code: {result}", file=sys.stderr)
            return False
        return output_path.exists()
    finally:
        try:
            os.unlink(html_path)
        except Exception:
            pass


# ─── Huvudfunktion ───────────────────────────────────────────────────────────

def distribute_meme(issue_path: str, dry_run: bool = False) -> bool:
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

    # Skapa output-kataloger
    MEMES_DIR.mkdir(parents=True, exist_ok=True)
    DIST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"  😂 Vecka {week}: skapar meme...", end=" ", flush=True)

    # Steg 1: Identifiera story + generera text
    if dry_run:
        meme_data = {
            "top_text": "NÄR AI:N FÅR 90 MINUTER",
            "bottom_text": "att stänga ner sig själv",
            "image_prompt": "a robot running away with a briefcase, meme template style, bold and simple, high contrast",
            "source_story": "USA exportkontrollerade Anthropics AI",
            "reason": "Absurt kort deadline"
        }
        print("(dry-run)")
    else:
        meme_data = generate_meme_data(issue)
        if not meme_data:
            print("❌ Misslyckades (identifiering)")
            return False
        print(f"'{meme_data['top_text']}'")

    # Spara metadata
    meta_path = DIST_OUTPUT_DIR / f"{year}-{week}.json"
    meta_data = {**meme_data, "week": week, "year": year}
    meta_path.write_text(json.dumps(meta_data, indent=2, ensure_ascii=False), encoding="utf-8")

    # Steg 2: Generera bild
    meme_img = MEMES_DIR / f"{year}-{week}.png"

    if dry_run:
        # Skapa en liten placeholder-bild
        meme_img.write_bytes(b"")
        print(f"    ➡ Sparad (placeholder): {meme_img.name}")
        return True

    print(f"  🎨 Genererar bild...", end=" ", flush=True)
    image_data = generate_meme_image(meme_data["image_prompt"])
    if not image_data:
        print("❌ Misslyckades (bild)")
        return False

    # Steg 3: Rendera med text overlay
    raw_img = MEMES_DIR / f"{year}-{week}-raw.png"
    raw_img.write_bytes(image_data)
    print(f"rendrerar...", end=" ", flush=True)

    success = render_meme_with_text(
        raw_img,
        meme_data["top_text"],
        meme_data["bottom_text"],
        meme_img,
    )

    # Städa raw-bild
    try:
        os.unlink(raw_img)
    except Exception:
        pass

    if success:
        print(f"✅")
        print(f"    ➡ Sparad: {meme_img.name}")
        return True
    else:
        print("❌ Misslyckades (rendering)")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI-Bladet — Meme distribution")
    parser.add_argument("--issue", required=True, help="Sökväg till issue-fil")
    parser.add_argument("--dry-run", action="store_true", help="Simulera utan API-anrop")
    args = parser.parse_args()

    success = distribute_meme(args.issue, dry_run=args.dry_run)
    sys.exit(0 if success else 1)
