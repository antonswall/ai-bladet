#!/usr/bin/env python3
"""
AI-Bladet — Bild (Pipeline Steg 5)
======================================
Väljer en bild per story som faktiskt illustrerar innehållet.

Strategi (prioritetsordning):
1. OG-bild från källan (<meta property="og:image">) — direkt, annars via
   r.jina.ai-proxy (samma trick som research.py, klarar Cloudflare).
2. AI-genererad lead-bild — Pollinations.ai (gratis, ingen nyckel) för
   veckans lead-kandidat. Sparas lokalt i static/img/generated/.
3. Openverse-sökning — CC-licensierade foton på konkreta nyckelord från
   titeln (ersätter Unsplash/Pexels som kräver API-nycklar).
4. Bildbanken (image_bank.py) — ENDAST specifika träffar (tema/källa),
   aldrig generiska kategori-bilder.
5. Grafisk placeholder (fallback_image.py) — AI-Bladet-grafik per kategori.

Output: output/images/{YYYY-WW}.json
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlparse

import requests
from bs4 import BeautifulSoup

import fallback_image
import image_bank

# ─── Config ───────────────────────────────────────────────────────────────────

PIPELINE_DIR = Path(__file__).parent
INPUT_DIR = PIPELINE_DIR / "output" / "researched"
OUTPUT_DIR = PIPELINE_DIR / "output" / "images"
GENERATED_DIR = PIPELINE_DIR.parent / "static" / "img" / "generated"
SITE_URL = "https://aibladet.se"
REQUEST_TIMEOUT = 15
JINA_BASE = "https://r.jina.ai"
OPENVERSE_API = "https://api.openverse.org/v1/images/"
POLLINATIONS_BASE = "https://image.pollinations.ai/prompt"
USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# ─── Nivå 1: OG-bild från källan ─────────────────────────────────────────────


def _absolutize(img_url: str, page_url: str) -> str:
    if img_url.startswith("//"):
        return "https:" + img_url
    if img_url.startswith("/"):
        p = urlparse(page_url)
        return f"{p.scheme}://{p.netloc}{img_url}"
    return img_url


def _og_from_html(html: str, page_url: str) -> str | None:
    soup = BeautifulSoup(html, "lxml")

    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        return _absolutize(og["content"].strip(), page_url)

    twitter = soup.find("meta", attrs={"name": "twitter:image"})
    if twitter and twitter.get("content"):
        return _absolutize(twitter["content"].strip(), page_url)

    return None


def extract_og_image(url: str) -> str | None:
    """Hämta OG-bild från en URL — direkt först, sen via jina-proxy."""
    if not url:
        return None

    # Direkt
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT},
                         timeout=REQUEST_TIMEOUT, allow_redirects=True)
        if r.status_code == 200:
            img = _og_from_html(r.text, url)
            if img:
                return img
    except Exception:
        pass

    # Via r.jina.ai (klarar Cloudflare-skyddade sidor, t.ex. x.ai)
    try:
        r = requests.get(f"{JINA_BASE}/{url}", timeout=25,
                         headers={"User-Agent": "AI-Bladet/1.0",
                                  "X-Return-Format": "html"})
        if r.status_code == 200:
            return _og_from_html(r.text, url)
    except Exception as e:
        print(f"\n    ⚠️  OG via jina misslyckades ({url[:50]}): {e}", file=sys.stderr)

    return None


def find_image_in_text(text: str) -> str | None:
    """Hitta bild-URL i markdown-text (full_text_excerpt)."""
    if not text:
        return None
    md_match = re.search(r"!\[.*?\]\((https?://[^\s)]+\.(?:jpg|jpeg|png|webp|gif))\)", text)
    if md_match:
        return md_match.group(1)
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
        if r.status_code == 200 and "image" in content_type:
            return True
        # Vissa CDN:er svarar fel på HEAD — testa GET på första bytes
        r = requests.get(url, headers={"User-Agent": USER_AGENT, "Range": "bytes=0-1023"},
                         timeout=8, allow_redirects=True, stream=True)
        content_type = r.headers.get("Content-Type", "")
        return r.status_code in (200, 206) and "image" in content_type
    except Exception:
        return False


# ─── Nivå 2: AI-genererad lead-bild (Pollinations) ───────────────────────────


def generate_lead_image(story: dict, week: str) -> tuple[str, str] | None:
    """Generera en unik lead-bild via Pollinations.ai och spara lokalt."""
    title = story.get("title", "")[:120]
    brief = story.get("fact_brief", {}) or {}
    summary = str(brief.get("summary", ""))[:150]
    prompt = (f"Editorial newspaper illustration, modern flat style, no text: "
              f"{title}. {summary}")
    url = (f"{POLLINATIONS_BASE}/{quote(prompt)}"
           f"?width=1216&height=684&nologo=true&seed=27")
    try:
        r = requests.get(url, timeout=90, headers={"User-Agent": "AI-Bladet/1.0"})
        if r.status_code != 200 or "image" not in r.headers.get("Content-Type", ""):
            return None
        GENERATED_DIR.mkdir(parents=True, exist_ok=True)
        path = GENERATED_DIR / f"{week}-lead.jpg"
        path.write_bytes(r.content)
        return (f"{SITE_URL}/img/generated/{week}-lead.jpg",
                "Illustration · AI-Bladet / Pollinations.ai")
    except Exception as e:
        print(f"\n    ⚠️  Pollinations-fel: {e}", file=sys.stderr)
        return None


# ─── Nivå 3: Openverse keyword-sökning ───────────────────────────────────────

_STOPWORDS = {
    # engelska
    "the", "and", "for", "with", "from", "into", "that", "this", "its", "our",
    "new", "first", "announcing", "announces", "announced", "today", "raises",
    "round", "series", "bringing", "next", "generation", "world", "worlds",
    "mission", "supporting", "partnership", "joins", "age", "beta",
    # svenska
    "och", "för", "med", "från", "till", "som", "det", "den", "har", "nya",
    "veckans", "efter", "inför",
}


def _keywords(story: dict, max_words: int = 4) -> str:
    """Konkreta sökord ur titeln (INTE kategorier som 'AI' eller 'Företag')."""
    title = story.get("title", "")
    words = re.findall(r"[A-Za-zÅÄÖåäö0-9][\w.-]*", title)
    picked = []
    for w in words:
        lw = w.lower()
        if len(lw) < 3 or lw in _STOPWORDS:
            continue
        if lw not in (p.lower() for p in picked):
            picked.append(w)
        if len(picked) >= max_words:
            break
    return " ".join(picked)


def _format_license(lic: str, version: str) -> str:
    """Openverse-licens ('by-sa', '4.0') → 'CC BY-SA 4.0'."""
    lic = lic.lower()
    if lic in ("cc0", "pdm"):
        return "Public domain" if lic == "pdm" else "CC0"
    name = f"CC {lic.upper()}" if lic else "CC"
    return f"{name} {version}".strip()


def search_openverse(story: dict, used: set) -> tuple[str, str] | None:
    """Sök CC-licensierad bild på nyckelord från titeln. Ingen API-nyckel.

    Openverse AND:ar söktermer, så smalna av progressivt: 4 → 3 → 2 ord.
    """
    tried = set()
    for max_words in (4, 3, 2):
        query = _keywords(story, max_words)
        if not query or query in tried:
            continue
        tried.add(query)
        try:
            r = requests.get(OPENVERSE_API, timeout=15,
                             params={"q": query, "license_type": "commercial",
                                     "page_size": 8},
                             headers={"User-Agent": "AI-Bladet/1.0"})
            if r.status_code != 200:
                continue
            qwords = {w.lower() for w in query.split()}
            for item in r.json().get("results", []):
                img = item.get("url") or ""
                if not img or img in used:
                    continue
                # Relevansfilter: minst ett sökord i bildens titel/taggar,
                # annars returnerar Openverse lätt lösa associationer.
                item_text = " ".join(
                    [str(item.get("title") or "")]
                    + [str(t.get("name", "")) for t in (item.get("tags") or [])]
                ).lower()
                if not any(w in item_text for w in qwords):
                    continue
                if verify_image(img):
                    creator = (item.get("creator") or "Okänd").strip()
                    lic = _format_license(item.get("license") or "",
                                          item.get("license_version") or "")
                    return img, f"Foto · {creator} / {lic}"
        except Exception as e:
            print(f"\n    ⚠️  Openverse-fel ({query}): {e}", file=sys.stderr)
    return None


# ─── Huvudfunktion ────────────────────────────────────────────────────────────


def _lead_candidate_index(stories: list) -> int:
    """Index för trolig lead: högsta lead_potential, tie-break på score."""
    def _num(v):
        return v if isinstance(v, (int, float)) else 0

    return max(range(len(stories)),
               key=lambda i: (_num(stories[i].get("lead_potential")),
                              _num(stories[i].get("score"))))


def find_images(input_path: Path, output_path: Path) -> dict:
    """Hitta bilder för alla researchade stories."""
    with open(input_path) as f:
        data = json.load(f)

    stories = data["stories"]
    week = input_path.stem
    print(f"🖼️  Bildval: {len(stories)} stories (OG → AI-lead → Openverse → bank → grafik)\n")

    used: set[str] = set()  # undvik samma bild två gånger i samma nummer
    lead_idx = _lead_candidate_index(stories) if stories else -1
    levels = {"og": 0, "ai": 0, "openverse": 0, "bank": 0, "grafik": 0}

    for i, story in enumerate(stories):
        title = story.get("title", "Untitled")[:70]
        print(f"  [{i+1}/{len(stories)}] {title}...", end=" ", flush=True)

        img_url, credit, level = None, None, None

        # 1. OG-bild från källan
        og = extract_og_image(story.get("url", ""))
        if not og:
            og = find_image_in_text(story.get("full_text_excerpt", ""))
        if og and og not in used and verify_image(og):
            src = story.get("source_label", "källan")
            img_url, credit, level = og, f"Foto · {src} (pressbild)", "og"

        # 2. AI-genererad bild för lead-kandidaten
        if not img_url and i == lead_idx:
            result = generate_lead_image(story, week)
            if result:
                img_url, credit, level = *result, "ai"

        # 3. Openverse (konkreta nyckelord från titeln)
        if not img_url:
            result = search_openverse(story, used)
            if result:
                img_url, credit, level = *result, "openverse"

        # 4. Bildbank — endast specifik träff (tema/källa)
        if not img_url:
            result = image_bank.pick_specific(story, used)
            if result:
                img_url, credit, level = *result, "bank"

        # 5. Grafisk AI-Bladet-placeholder
        if not img_url:
            img_url, credit = fallback_image.get(story.get("category", ""))
            level = "grafik"

        used.add(img_url)
        levels[level] += 1
        story["image_url"] = img_url
        story["image_credit"] = credit
        print(f"✅ [{level}] {credit}")

    with_images = sum(1 for s in stories if s.get("image_url"))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output = {
        "meta": {
            **data.get("meta", {}),
            "stories_with_images": with_images,
            "stories_without": len(stories) - with_images,
            "image_levels": levels,
            "image_time": datetime.now(timezone.utc).isoformat(),
        },
        "stories": stories,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n{'─'*40}")
    print(f"📊 BILD RESULTAT")
    print(f"  OG från källa:      {levels['og']}/{len(stories)}")
    print(f"  AI-genererad:       {levels['ai']}/{len(stories)}")
    print(f"  Openverse:          {levels['openverse']}/{len(stories)}")
    print(f"  Bildbank:           {levels['bank']}/{len(stories)}")
    print(f"  Grafik-fallback:    {levels['grafik']}/{len(stories)}")
    print(f"  Output:             {output_path}")
    print(f"{'─'*40}")

    return {"with": with_images, "without": len(stories) - with_images, "levels": levels}


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
