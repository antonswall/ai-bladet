#!/usr/bin/env python3
"""
AI-Bladet — Bildbankskurator
=============================
Söker Wikimedia Commons efter CC-licensierade foton för AI-relaterade ämnen,
HEAD-verifierar URL:er, och lägger till nya poster i image_bank.py.

Användning:
  python curate_images.py              # sök alla kategorier, visa förslag
  python curate_images.py --auto       # automatiskt lägg till i banken
  python curate_images.py --dry-run    # visa förslag utan att ändra

Arkitektur:
  1. Sök Wikimedia Commons API per ämneskategori
  2. Välj bilder med rätt licens (CC-BY, CC-BY-SA, CC0, Public Domain)
  3. HEAD-verifiera URL:er (200 image/jpeg)
  4. Generera image_bank.py-kompatibla poster
  5. Skriv till image_bank.py (i --auto-läge)
"""

import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import quote
from typing import Optional

import requests

PIPELINE_DIR = Path(__file__).parent
BANK_PATH = PIPELINE_DIR / "image_bank.py"

# ─── Search config ────────────────────────────────────────────────────────────

SEARCHES = [
    # (bucket_name, search_query, max_results)
    ("ai_chips", "semiconductor chip factory wafer production", 3),
    ("eu_politics", "European Parliament Brussels EU Commission building exterior", 3),
    ("ai_robots", "robot artificial intelligence laboratory", 3),
    ("tech_campus", "Google headquarters Apple campus Microsoft office building exterior", 3),
    ("research_lab", "AI research laboratory scientist computer", 3),
    ("data_centers_extra", "data center server rack interior", 4),
    ("sweden_tech", "Stockholm Sweden technology office building", 3),
    ("cloud_infra", "cloud computing network server infrastructure", 3),
]


def search_commons(query: str, limit: int = 5) -> list[dict]:
    """Sök Wikimedia Commons efter bilder."""
    url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srnamespace": "6",      # File namespace
        "srlimit": limit * 5,    # Hämta fler — vi filtrerar sen
        "format": "json",
    }
    try:
        r = requests.get(url, params=params, timeout=15,
                        headers={"User-Agent": "AI-Bladet-image-curator/1.0"})
        r.raise_for_status()
        results = r.json().get("query", {}).get("search", [])
    except Exception as e:
        print(f"   ⚠️  Search error: {e}")
        return []

    # Hämta bildinformation för att få URL + licens
    titles = [res["title"] for res in results[:limit * 5]]
    if not titles:
        return []

    info_params = {
        "action": "query",
        "titles": "|".join(titles),
        "prop": "imageinfo",
        "iiprop": "url|size|mime|extmetadata",
        "format": "json",
    }
    try:
        r2 = requests.post(url, data=info_params, timeout=15,
                          headers={"User-Agent": "AI-Bladet-image-curator/1.0"})
        r2.raise_for_status()
        pages = r2.json().get("query", {}).get("pages", {})
    except Exception:
        return []

    images = []
    for page_id, page in pages.items():
        if page_id == "-1":
            continue
        info = (page.get("imageinfo") or [{}])[0]
        url_img = info.get("url", "")
        mime = info.get("mime", "")
        meta = info.get("extmetadata", {})

        # Filtrera: endast JPEG, minst 800px bred
        if mime != "image/jpeg":
            continue
        if info.get("width", 0) < 800:
            continue

        # Licensinfo
        license_obj = meta.get("LicenseUrl", {})
        license_url = license_obj.get("value", "")
        artist = meta.get("Artist", {}).get("value", "")
        credit_text = meta.get("Credit", {}).get("value", "")

        # Bestäm credit-sträng
        if artist:
            credit = f"Foto · {artist} / Wikimedia Commons"
        elif credit_text:
            credit = f"Foto · {credit_text}"
        else:
            credit = "Foto · Wikimedia Commons"

        # Tillåtna licenser
        allowed = ["creativecommons.org/licenses/by", "creativecommons.org/publicdomain",
                   "creativecommons.org/licenses/by-sa", "creativecommons.org/publicdomain/zero"]
        if any(a in license_url.lower() for a in allowed):
            images.append({"url": url_img, "credit": credit})

        if len(images) >= limit:
            break

    return images


def verify_url(url: str, timeout: int = 8) -> bool:
    """HEAD-kolla att URL:en lever och returnerar image/jpeg."""
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=True,
                         headers={"User-Agent": "AI-Bladet-image-curator/1.0"})
        if r.status_code == 200:
            ct = r.headers.get("content-type", "")
            return "image/jpeg" in ct or "image/jpg" in ct
    except Exception:
        pass
    return False


def format_entry(url: str, credit: str, var_name: str) -> str:
    """Generera en BANK_ENTRY-rad för image_bank.py."""
    return f'{var_name} = _c(\n    "{url}",\n    "{credit}")'


def find_insert_point(content: str) -> int:
    """Hitta var nya variabler ska infogas — efter sista _c()-anropet."""
    matches = list(re.finditer(r'^\w+\s*=\s*_c\(', content, re.MULTILINE))
    if not matches:
        return -1
    last = matches[-1]
    # Hitta slutet av detta _c()-block (slutparentes + newline)
    end = content.find("\n", last.end())
    # Hitta matchande slutparentes
    depth = 1
    i = last.end()
    while i < len(content) and depth > 0:
        if content[i] == "(":
            depth += 1
        elif content[i] == ")":
            depth -= 1
        i += 1
    return i


def curate(auto: bool = False, dry_run: bool = True) -> dict:
    """Huvudfunktion: sök, verifiera, lägg till."""
    results = {}
    total_found = 0
    total_verified = 0
    new_entries = []

    for bucket, query, limit in SEARCHES:
        print(f"\n🔍 Söker: {bucket} ('{query[:60]}...')")
        images = search_commons(query, limit)
        print(f"   Hittade {len(images)} kandidater")

        verified = []
        for img in images:
            if verify_url(img["url"]):
                verified.append(img)
                total_verified += 1
            else:
                print(f"   ❌ Död URL: {img['url'][:80]}...")
            time.sleep(0.3)  # Var snäll mot Commons

        print(f"   ✅ {len(verified)}/{len(images)} verifierade")
        results[bucket] = verified
        total_found += len(images)
        new_entries.extend(verified)

    print(f"\n{'='*50}")
    print(f"📊 Totalt: {total_verified} verifierade av {total_found} kandidater")

    if dry_run or not auto:
        print("\n📋 Förslag (lägg till manuellt i image_bank.py):\n")
        for i, img in enumerate(new_entries):
            var = f"NEW_{i+1:02d}"
            print(format_entry(img["url"], img["credit"], var))
            print()
        return results

    # Auto-läge: modifiera image_bank.py
    if auto and new_entries:
        content = BANK_PATH.read_text()
        insert_at = find_insert_point(content)
        if insert_at < 0:
            print("❌ Kunde inte hitta infogningspunkt i image_bank.py")
            return results

        # Bygg nya variabler
        new_vars = []
        for i, img in enumerate(new_entries):
            var = f"CURATED_{i+1:02d}"
            new_vars.append(var)
            content = (content[:insert_at] +
                      f"\n{var} = _c(\n    \"{img['url']}\",\n    \"{img['credit']}\")\n" +
                      content[insert_at:])
            # Flytta infogningspunkt (efter den nyss infogade)
            insert_at = content.find(f"{var} = _c(") + len(f"{var} = _c(\n    \"{img['url']}\",\n    \"{img['credit']}\")\n")

        BANK_PATH.write_text(content)
        print(f"\n✅ Lagt till {len(new_entries)} nya poster i image_bank.py")
        print(f"   Variabler: {', '.join(new_vars)}")
        print(f"   ⚠️  Du måste manuellt lägga till dessa i KEYWORD_BUCKETS / CATEGORY_BUCKETS")

    return results


if __name__ == "__main__":
    auto = "--auto" in sys.argv
    dry_run = "--dry-run" in sys.argv or (not auto)
    curate(auto=auto, dry_run=dry_run)
