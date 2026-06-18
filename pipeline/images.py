#!/usr/bin/env python3
"""
AI-Bladet — Bild (Pipeline Steg 5)
======================================
Extraherar OG-bilder från käll-URLs för scoreade stories.

Strategi (per plan):
1. OG-image från källans HTML (<meta property="og:image">)
2. Fallback: hitta bilder i extracted text
3. Briefs får INGA bilder (medvetet kontrast)

Output: output/images/{YYYY-WW}.json
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ─── Config ───────────────────────────────────────────────────────────────────

PIPELINE_DIR = Path(__file__).parent
INPUT_DIR = PIPELINE_DIR / "output" / "researched"
OUTPUT_DIR = PIPELINE_DIR / "output" / "images"
REQUEST_TIMEOUT = 15
USER_AGENT = "AI-Bladet/1.0 (+https://aibladet.se; image-finder)"

# ─── OG-image extraction ─────────────────────────────────────────────────────


def extract_og_image(url: str) -> str | None:
    """Hämta OG-image från en URL:s HTML."""
    if not url:
        return None

    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT},
                         timeout=REQUEST_TIMEOUT, allow_redirects=True)
        if r.status_code != 200:
            return None

        soup = BeautifulSoup(r.text, "lxml")

        # OG image (prioritet 1)
        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            img_url = og["content"].strip()
            if img_url.startswith("/"):
                from urllib.parse import urlparse
                parsed = urlparse(url)
                img_url = f"{parsed.scheme}://{parsed.netloc}{img_url}"
            return img_url

        # Twitter image (prioritet 2)
        twitter = soup.find("meta", attrs={"name": "twitter:image"})
        if twitter and twitter.get("content"):
            return twitter["content"].strip()

        # Första stora bilden i content (prioritet 3)
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src") or ""
            if src and (src.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")) or
                        "image" in src.lower()):
                if len(src) > 20:  # undvik små icons
                    if src.startswith("/"):
                        from urllib.parse import urlparse
                        parsed = urlparse(url)
                        src = f"{parsed.scheme}://{parsed.netloc}{src}"
                    return src

    except Exception as e:
        print(f"    ⚠️  OG-bild error ({url[:50]}): {e}", file=sys.stderr)

    return None


def find_image_in_text(text: str) -> str | None:
    """Hitta bild-URL i markdown-text (full_text_excerpt)."""
    if not text:
        return None

    # Markdown bild: ![alt](url)
    md_match = re.search(r"!\[.*?\]\((https?://[^\s)]+\.(?:jpg|jpeg|png|webp|gif))\)", text)
    if md_match:
        return md_match.group(1)

    # Direkta bild-URLs
    url_match = re.search(r"(https?://[^\s]+\.(?:jpg|jpeg|png|webp|gif))", text)
    if url_match:
        return url_match.group(1)

    return None


def verify_image(url: str) -> bool:
    """Kolla om en bild-URL faktiskt returnerar en bild."""
    if not url:
        return False
    try:
        r = requests.head(url, headers={"User-Agent": USER_AGENT},
                          timeout=8, allow_redirects=True)
        content_type = r.headers.get("Content-Type", "")
        return r.status_code == 200 and "image" in content_type
    except Exception:
        return False


# ─── Huvudfunktion ────────────────────────────────────────────────────────────


def find_images(input_path: Path, output_path: Path) -> dict:
    """Hitta bilder för alla researchade stories."""
    with open(input_path) as f:
        data = json.load(f)

    stories = data["stories"]
    print(f"🖼️  Bildsökning: {len(stories)} stories\n")

    for i, story in enumerate(stories):
        title = story.get("title", "Untitled")[:70]
        url = story.get("url", "")
        fetch_success = story.get("fetch_success", False)

        print(f"  [{i+1}/{len(stories)}] {title}...", end=" ", flush=True)

        img_url = None

        # Steg 1: OG-image från käll-URL
        if url:
            img_url = extract_og_image(url)

        # Steg 2: Fallback — bild i extracted text
        if not img_url and fetch_success:
            img_url = find_image_in_text(story.get("full_text_excerpt", ""))

        # Steg 3: Verify
        if img_url:
            valid = verify_image(img_url)
            if valid:
                print(f"✅")
            else:
                print(f"⚠️  OG hittad men ej verifierbar")
                img_url = None  # acceptera ändå? ja, låt den stå
        else:
            print("—")

        story["image_url"] = img_url or ""

    # Statistik
    with_images = sum(1 for s in stories if s.get("image_url"))
    without = len(stories) - with_images

    # Skriv output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output = {
        "meta": {
            **data.get("meta", {}),
            "stories_with_images": with_images,
            "stories_without": without,
            "image_time": datetime.now(timezone.utc).isoformat(),
        },
        "stories": stories,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n{'─'*40}")
    print(f"📊 BILD RESULTAT")
    print(f"  Med bild:           {with_images}/{len(stories)}")
    print(f"  Utan bild:          {without}/{len(stories)}")
    print(f"  Output:             {output_path}")
    print(f"{'─'*40}")

    return {"with": with_images, "without": without}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AI-Bladet bildsökning")
    parser.add_argument("input", nargs="?", help="Input JSON (researched)")
    args = parser.parse_args()

    if args.input:
        input_path = Path(args.input)
    else:
        researched = sorted(INPUT_DIR.glob("*.json"))
        if not researched:
            print("Inga researchade filer hittades.")
            sys.exit(1)
        input_path = researched[-1]

    week = input_path.stem
    output_path = OUTPUT_DIR / f"{week}.json"

    result = find_images(input_path, output_path)
    sys.exit(0)
