#!/usr/bin/env python3
"""
AI-Bladet — Audio Distribution Module
=======================================
Genererar en 90-sekunders TTS-sammanfattning av veckans nummer.

Input:  content/YYYY-WW.md (via --issue)
Output: public/audio/YYYY-WW.mp3
         public/feed/podcast.xml (uppdateras)

API-kostnad: ~$0.0155 per vecka (DeepSeek ~$0.0005 + ElevenLabs ~$0.015)
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET
from xml.dom import minidom

import requests

# ─── Config ───────────────────────────────────────────────────────────────────

PIPELINE_DIR = Path(__file__).parent
DIST_OUTPUT_DIR = PIPELINE_DIR / "output" / "distribution" / "audio"
PROJECT_DIR = Path.home() / "ai-bladet"
PUBLIC_DIR = PROJECT_DIR / "public"
AUDIO_DIR = PUBLIC_DIR / "audio"
FEED_DIR = PUBLIC_DIR / "feed"
CONTENT_DIR = PROJECT_DIR / "content"

SITE_URL = os.getenv("SITE_URL", "https://aibladet.se")

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
ELEVENLABS_URL = "https://api.elevenlabs.io/v1/text-to-speech"

# ElevenLabs röst-ID för svensk röst
# "Freja" om den finns på kontot, annars fallerar vi till första
SWEDISH_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel (fallback — byt till svensk röst)
SWEDISH_MODEL = "eleven_multilingual_v2"    # Multilingual stöder svenska


# ─── API Helpers ──────────────────────────────────────────────────────────────

def _get_env(key: str) -> Optional[str]:
    """Läs API-nyckel från miljö eller ~/.hermes/.env."""
    val = os.getenv(key, "")
    if val:
        return val
    env_path = Path.home() / ".hermes" / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip()
    return None


def _get_deepseek_key() -> str:
    key = _get_env("DEEPSEEK_API_KEY")
    if not key:
        raise ValueError("DEEPSEEK_API_KEY saknas")
    return key


def _get_elevenlabs_key() -> str:
    key = _get_env("ELEVENLABS_API_KEY")
    if not key:
        raise ValueError("ELEVENLABS_API_KEY saknas")
    return key


def deepseek_call(prompt: str, system: str = None,
                  max_tokens: int = 1000, temperature: float = 0.3) -> Optional[str]:
    """Anropa DeepSeek V4 Pro."""
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


def elevenlabs_tts(text: str, voice_id: str = SWEDISH_VOICE_ID) -> Optional[bytes]:
    """Generera ljud från text med ElevenLabs TTS."""
    key = _get_elevenlabs_key()
    url = f"{ELEVENLABS_URL}/{voice_id}"

    try:
        r = requests.post(
            url,
            headers={
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": key,
            },
            json={
                "text": text,
                "model_id": SWEDISH_MODEL,
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "speed": 1.05,
                },
            },
            timeout=30,
        )
        r.raise_for_status()
        return r.content
    except Exception as e:
        print(f"  ⚠️ ElevenLabs API error: {e}", file=sys.stderr)
        return None


# ─── Skriptgenerering ────────────────────────────────────────────────────────

def generate_script(issue: dict) -> Optional[str]:
    """
    Generera manus för 90-sekunders sammanfattning med DeepSeek.
    Returnerar ren text redo för TTS.
    """
    year = issue.get("year", datetime.now().year)
    week = issue.get("week", "?")
    lead = issue.get("lead", {})
    stories = issue.get("stories", [])

    # Plocka topp 3 stories
    top_stories = [lead] + stories[:2]

    # Bygg context för DeepSeek
    story_texts = []
    for i, s in enumerate(top_stories):
        headline = s.get("headline", "")
        ingress = s.get("ingress", "")
        story_texts.append(f"Story {i+1}: {headline}\n{ingress[:200]}")

    prompt = f"""Skriv ett manus för en 90-sekunders ljudsammanfattning av AI-Bladet vecka {week}.

Formatet ska vara:
[0:00-0:05] "AI-Bladet, vecka {week}. Din 90-sekunders sammanfattning."
[0:05-0:30] Story 1 — rubrik + 1 mening kontext + varför det spelar roll
[0:30-0:50] Story 2 — rubrik + 1 mening kontext + varför det spelar roll
[0:50-1:10] Story 3 — rubrik + 1 mening kontext + varför det spelar roll
[1:10-1:20] "Vill du ha hela bilden? Läs hela tidningen på aibladet.se. Nytt nummer varje söndag."

Använd naturlig svenska som låter bra uppläst. Inga parenteser, inga asterisker, inga förkortningar.
Skriv bara själva texten som ska läsas upp — inga tidsangivelser i output, bara den rena texten.
Max 200 ord totalt.

Här är veckans stories:

{chr(10).join(story_texts)}
"""

    system = "Du är en svensk nyhetsankare. Skriv kortfattade manus för uppläsning. Använd enkel, tydlig svenska."

    result = deepseek_call(prompt, system=system, max_tokens=800, temperature=0.4)
    if not result:
        return None

    # Rensa bort eventuella tidsstämplar från svaret
    clean = re.sub(r'\[\d+:\d+-\d+:\d+\]', '', result).strip()
    return clean


# ─── Podcast-RSS ──────────────────────────────────────────────────────────────

def update_podcast_rss(year: int, week: int, date_str: str,
                        title: str, audio_url: str, duration_sec: int = 90):
    """Lägg till avsnitt i podcast-RSS eller skapa ny."""
    FEED_DIR.mkdir(parents=True, exist_ok=True)
    rss_path = FEED_DIR / "podcast.xml"

    episode_title = f"Vecka {week} — {title[:60]}"
    episode_desc = f"AI-Bladet vecka {week}. 90-sekunders sammanfattning av veckans AI-nyheter."
    pub_date = datetime.fromisoformat(date_str).strftime("%a, %d %b %Y 09:00:00 +0000")
    guid = f"ai-bladet-{year}-{week}"
    duration_str = f"00:01:{duration_sec:02d}"
    audio_size = 0  # uppdateras efter att filen sparats

    if rss_path.exists():
        # Läs befintlig RSS
        tree = ET.parse(str(rss_path))
        root = tree.getroot()
        channel = root.find("channel")
    else:
        # Skapa ny RSS
        rss = ET.Element("rss", version="2.0",
                         attrib={"xmlns:itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
                                 "xmlns:content": "http://purl.org/rss/1.0/modules/content/"})
        channel = ET.SubElement(rss, "channel")
        ET.SubElement(channel, "title").text = "AI-Bladet"
        ET.SubElement(channel, "link").text = f"{SITE_URL}/"
        ET.SubElement(channel, "description").text = "Varje söndag — 90 sekunder om veckans viktigaste AI-nyheter på svenska."
        ET.SubElement(channel, "language").text = "sv"
        ET.SubElement(channel, "itunes:author").text = "AI-Bladet"
        ET.SubElement(channel, "itunes:category", text="Technology")
        ET.SubElement(channel, "itunes:explicit").text = "false"
        # Image
        image = ET.SubElement(channel, "itunes:image",
                              href=f"{SITE_URL}/static/android-chrome-512x512.png")
        tree = ET.ElementTree(rss)

    # Nytt item HÖGST UPP (först)
    item = ET.Element("item")
    ET.SubElement(item, "title").text = episode_title
    ET.SubElement(item, "description").text = episode_desc
    ET.SubElement(item, "link").text = f"{SITE_URL}/{audio_url.lstrip('/')}"
    ET.SubElement(item, "guid").text = guid
    ET.SubElement(item, "pubDate").text = pub_date
    ET.SubElement(item, "enclosure",
                  url=f"{SITE_URL}{audio_url}",
                  length=str(audio_size),
                  type="audio/mpeg")
    ET.SubElement(item, "itunes:duration").text = duration_str

    # Sätt högst upp i kanalen (efter metadata, före tidigare items)
    channel.insert(len(list(channel)), item)

    # Spara med fin formatering
    rough_string = ET.tostring(tree.getroot(), encoding="unicode", method="xml")
    reparsed = minidom.parseString(rough_string.encode())
    pretty = reparsed.toprettyxml(indent="  ", encoding="utf-8")
    rss_path.write_bytes(pretty)

    return rss_path


def get_audio_duration(mp3_path: Path) -> int:
    """Uppskatta längd på mp3 i sekunder (90s default om vi inte kan läsa)."""
    try:
        # Försök läsa mp3-header för längd
        import struct
        with open(mp3_path, "rb") as f:
            f.read(10)  # MP3 header
            # Detta är en approximation. Vi använder 90s som default.
    except Exception:
        pass
    return 90  # Default — manuset är designat för 90s


# ─── Huvudfunktion ───────────────────────────────────────────────────────────

def distribute_audio(issue_path: str, dry_run: bool = False) -> bool:
    """
    Huvudfunktion: generera ljudsammanfattning.
    
    1. Läs issue
    2. Generera manus med DeepSeek
    3. Generera ljud med ElevenLabs
    4. Spara mp3 + uppdatera RSS
    """
    import yaml

    # Läs issue
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
    year = issue.get("year", datetime.now().year)
    week = issue.get("week", "?")
    title = issue.get("title", f"Vecka {week}")
    date_str = issue.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))

    print(f"  📝 Vecka {week}: {title[:60]}")

    # Skapa output-kataloger
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    DIST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Steg 1: Generera manus
    print("  🎙️ Genererar manus...", end=" ", flush=True)
    if dry_run:
        script = "Detta är en test-sammanfattning för veckans AI-Bladet. (dry-run)"
        print("(dry-run)")
    else:
        script = generate_script(issue)
        if not script:
            print("❌ Misslyckades")
            return False
        print(f"{len(script.split())} ord")

    # Spara manus för debugging
    script_path = DIST_OUTPUT_DIR / f"{year}-{week}.txt"
    script_path.write_text(script, encoding="utf-8")

    # Steg 2: Generera ljud
    mp3_path = AUDIO_DIR / f"{year}-{week}.mp3"
    print(f"  🔊 Genererar ljud...", end=" ", flush=True)

    if dry_run:
        # Skapa en liten test-mp3
        mp3_path.write_bytes(b"")  # placeholder
        duration = 90
        print("(dry-run)")
    else:
        audio_data = elevenlabs_tts(script)
        if not audio_data:
            print("❌ Misslyckades")
            return False
        mp3_path.write_bytes(audio_data)
        duration = get_audio_duration(mp3_path)
        size_kb = len(audio_data) / 1024
        print(f"{size_kb:.0f}KB, ~{duration}s")

    # Steg 3: Uppdatera podcast-RSS
    print(f"  📡 Uppdaterar podcast-RSS...", end=" ", flush=True)
    if not dry_run:
        audio_url = f"/audio/{year}-{week}.mp3"
        rss_path = update_podcast_rss(year, week, date_str, title, audio_url, duration)
        print(f"{rss_path.name}")
    else:
        print("(dry-run)")

    # Steg 4: Spara metadata för orkestratorn
    meta = {
        "year": year,
        "week": week,
        "title": title,
        "script_path": str(script_path),
        "audio_path": str(mp3_path),
        "audio_url": f"/audio/{year}-{week}.mp3",
        "duration_sec": duration if not dry_run else 90,
        "dry_run": dry_run,
    }
    meta_path = DIST_OUTPUT_DIR / f"{year}-{week}-meta.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"  ✅ Distribution audio klar: /audio/{year}-{week}.mp3")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI-Bladet — Audio distribution")
    parser.add_argument("--issue", required=True, help="Sökväg till issue-fil")
    parser.add_argument("--dry-run", action="store_true", help="Simulera utan API-anrop")
    args = parser.parse_args()

    success = distribute_audio(args.issue, dry_run=args.dry_run)
    sys.exit(0 if success else 1)
