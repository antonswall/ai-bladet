#!/usr/bin/env python3
"""
AI-Bladet — Insamlingsmodul (Pipeline Steg 1)
===============================================
Hämtar från alla källor, normaliserar till enhetligt format,
deduplicerar på URL och skriver kandidatlista.

Kör: source .venv/bin/activate && python collect.py
"""

import json
import hashlib
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import feedparser
import requests
import yaml
from bs4 import BeautifulSoup

# ─── Config ───────────────────────────────────────────────────────────────────

CONFIG_PATH = Path(__file__).parent / "config" / "sources.yaml"
OUTPUT_DIR = Path(__file__).parent / "output" / "candidates"
REQUEST_TIMEOUT = 20  # sekunder per feed
USER_AGENT = "AI-Bladet/1.0 (+https://aibladet.se; news-collector)"

# ─── Imports (utanför funktioner) ────────────────────────────────────────

from seen_db import SeenDB

# ─── Helpers ──────────────────────────────────────────────────────────────────


def now_iso():
    return datetime.now(timezone.utc).isoformat()

def url_hash(url: str) -> str:
    return hashlib.sha256(url.strip().lower().encode()).hexdigest()[:16]

def safe_get(url: str, **kwargs) -> requests.Response | None:
    """Hämta URL med timeout och user-agent. Returnerar None vid fel."""
    headers = kwargs.pop("headers", {})
    headers.setdefault("User-Agent", USER_AGENT)
    try:
        r = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT, **kwargs)
        r.raise_for_status()
        return r
    except requests.RequestException as e:
        print(f"  ⚠️  HTTP-fel ({url[:60]}): {e}", file=sys.stderr)
        return None

# ─── Collectors ───────────────────────────────────────────────────────────────

def collect_rss(feed_cfg: dict) -> list[dict]:
    """Hämta och normalisera RSS/Atom-feed."""
    feed = feedparser.parse(feed_cfg["url"])
    candidates = []

    if feed.bozo:
        print(f"  ⚠️  RSS parse-varning ({feed_cfg['id']}): {feed.bozo_exception}", file=sys.stderr)

    for entry in feed.entries[:30]:  # max 30 per feed
        url = entry.get("link", "")
        if not url:
            continue

        title = entry.get("title", "").strip()
        summary = entry.get("summary", entry.get("description", ""))
        # Rensa HTML från summary
        if summary:
            summary = BeautifulSoup(summary, "lxml").get_text().strip()[:500]

        published = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).isoformat()
        elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
            published = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc).isoformat()

        candidates.append({
            "source_id": feed_cfg["id"],
            "source_label": feed_cfg["label"],
            "tier": feed_cfg["tier"],
            "type": "rss",
            "title": title[:300],
            "url": url[:500],
            "summary": summary[:500],
            "published": published,
            "content_hash": url_hash(url),
        })

    return candidates


def collect_json_api(feed_cfg: dict) -> list[dict]:
    """Hämta och normalisera JSON API (HF Models, HF Daily Papers)."""
    r = safe_get(feed_cfg["url"], params=feed_cfg.get("params"))
    if not r:
        return []

    try:
        data = r.json()
    except json.JSONDecodeError:
        print(f"  ⚠️  JSON parse-fel ({feed_cfg['id']})", file=sys.stderr)
        return []

    candidates = []
    items = data if isinstance(data, list) else data.get("data", data.get("results", []))
    if not isinstance(items, list):
        items = [items]
    items = items[:feed_cfg.get("params", {}).get("limit", 50)]

    for item in items:
        # HF Models API format
        if feed_cfg["id"] == "hf-models":
            model_id = item.get("id", "")
            url = f"https://huggingface.co/{model_id}" if model_id else ""
            title = f"Ny modell: {model_id}"
            downloads = item.get("downloads", 0) or 0
            likes = item.get("likes", 0) or 0
            created = item.get("createdAt", "")
            summary = f"Downloads: {downloads:,} · Likes: {likes:,}"
            if item.get("pipeline_tag"):
                summary += f" · Pipeline: {item['pipeline_tag']}"
            if item.get("tags"):
                summary += f" · Tags: {', '.join(item['tags'][:5])}"

        # HF Daily Papers format
        elif feed_cfg["id"] == "hf-daily-papers":
            paper = item.get("paper", item)
            title = paper.get("title", "")
            paper_id = paper.get("id", "")
            url = f"https://arxiv.org/abs/{paper_id}" if paper_id else ""
            upvotes = item.get("upvotes", 0)
            created = item.get("publishedAt", "")
            summary = f"Upvotes: {upvotes}"
            if item.get("ai_keywords"):
                summary += f" · Keywords: {', '.join(item['ai_keywords'][:5])}"

        else:
            continue

        if url:
            candidates.append({
                "source_id": feed_cfg["id"],
                "source_label": feed_cfg["label"],
                "tier": feed_cfg["tier"],
                "type": "json_api",
                "title": title[:300],
                "url": url[:500],
                "summary": summary[:500],
                "published": created if created else None,
                "content_hash": url_hash(url),
            })

    return candidates


def collect_xai(feed_cfg: dict) -> list[dict]:
    """Skrapa x.ai/news — extrahera nyheter från HTML.

    xAI-sidan har två format:
    1. "Jun 17, 2026TITELJun 17, 2026TITELBody..."
    2. "TITELBody...Jun 11, 2026"

    Strategi: ta bort alla datum, splittra titel från body
    vid lowercase→UPPERCASE-gräns.
    """
    r = safe_get(feed_cfg["url"])
    if not r:
        return []

    soup = BeautifulSoup(r.text, "lxml")
    candidates = []
    seen_urls = set()
    import re

    DATE_RE = re.compile(
        r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}"
    )
    TITLE_BODY_SPLIT = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")

    news_links = soup.select('a[href^="/news/"]')

    for link in news_links:
        href = link.get("href", "")
        if not href or href == "/news" or href == "/news/" or href in seen_urls:
            continue
        seen_urls.add(href)

        if not href.startswith("http"):
            href = f"https://x.ai{href}"

        raw_text = link.get_text(strip=True)

        # Extrahera alla datum
        dates = DATE_RE.findall(raw_text)  # list of month names (groups)
        full_dates = DATE_RE.findall(raw_text)  # same, we'll use finditer
        date_str = ""
        date_matches = list(DATE_RE.finditer(raw_text))
        if date_matches:
            date_str = date_matches[0].group(0)

        # Ta bort alla datum från texten
        clean = DATE_RE.sub("", raw_text).strip()

        # Ta bort "Read More"-text
        clean = re.sub(r"Read More\.?$", "", clean).strip()

        # Splittra vid första lowercase→UPPERCASE-gräns (titel → body)
        parts = TITLE_BODY_SPLIT.split(clean, maxsplit=1)
        if len(parts) == 2:
            title = parts[0].strip()
            summary = parts[1].strip()[:500]
        else:
            # Ingen tydlig split — använd allt som titel
            title = clean[:120].strip()
            summary = ""

        # Om titeln är tom eller för kort efter splitten
        if not title or len(title) < 5:
            # Försök med bara första meningen
            dot = clean.find(".")
            title = clean[:dot].strip() if dot > 0 else clean[:120].strip()

        candidates.append({
            "source_id": feed_cfg["id"],
            "source_label": feed_cfg["label"],
            "tier": feed_cfg["tier"],
            "type": "scrape",
            "title": title[:300],
            "url": href[:500],
            "summary": summary[:500],
            "published": date_str if date_str else None,
            "content_hash": url_hash(href),
        })

    if not candidates:
        print(f"  ⚠️  xAI: inga kandidater extraherade", file=sys.stderr)

    return candidates


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print(f"╔══════════════════════════════════════╗")
    print(f"║   AI-Bladet · Insamling Pipeline     ║")
    print(f"║   {now_iso()[:19].replace('T', ' ')}                    ║")
    print(f"╚══════════════════════════════════════╝")
    print()

    # Ladda config
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)

    feeds = config["feeds"]
    print(f"📡 {len(feeds)} källor konfigurerade")

    # Steg 0: Ladda seen-databas
    seen = SeenDB()
    seen.init()
    seen_hashes = seen.get_all_hashes()
    print(f"🧠 Seen-db: {len(seen_hashes)} tidigare sedda artiklar\n")

    # Samla in
    all_candidates = []
    stats = {"ok": 0, "fail": 0, "tier_counts": {}}

    for feed_cfg in feeds:
        fid = feed_cfg["id"]
        ftype = feed_cfg["type"]
        tier = feed_cfg["tier"]
        print(f"  [{feed_cfg['label']}] ", end="", flush=True)

        start = time.monotonic()
        try:
            if ftype == "rss":
                candidates = collect_rss(feed_cfg)
            elif ftype == "json_api":
                candidates = collect_json_api(feed_cfg)
            elif ftype == "scrape_xai":
                candidates = collect_xai(feed_cfg)
            else:
                print(f"⚠️  Okänd typ: {ftype}")
                stats["fail"] += 1
                continue

            elapsed = time.monotonic() - start
            all_candidates.extend(candidates)
            stats["ok"] += 1
            stats["tier_counts"][f"tier{tier}"] = stats["tier_counts"].get(f"tier{tier}", 0) + len(candidates)
            print(f"{len(candidates)} st ({elapsed:.1f}s)")

        except Exception as e:
            print(f"❌ {e}")
            stats["fail"] += 1

    # Dedup på URL
    before_dedup = len(all_candidates)
    seen_this_run = {}
    deduped = []
    for c in all_candidates:
        chash = c["content_hash"]
        if chash not in seen_this_run:
            seen_this_run[chash] = c
            deduped.append(c)
    all_candidates = deduped

    # Steg 0: Filtrera bort redan sedda (från tidigare veckor)
    before_seen_filter = len(all_candidates)
    new_candidates = []
    skipped_seen = 0
    for c in all_candidates:
        if c["content_hash"] in seen_hashes:
            skipped_seen += 1
        else:
            new_candidates.append(c)
    all_candidates = new_candidates

    # Markera nya som sedda
    if all_candidates:
        seen.mark_seen_batch(all_candidates)

    # Sortera: tier (1-4) → weight descending → published
    feed_map = {f["id"]: f["weight"] for f in feeds}
    all_candidates.sort(
        key=lambda c: (
            c["tier"],
            -feed_map.get(c["source_id"], 0),
            c.get("published") or "",
        ),
    )

    # Skriv output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc)
    week_num = today.isocalendar()[1]
    year = today.isocalendar()[0]
    output_path = OUTPUT_DIR / f"{year}-{week_num:02d}.json"

    output = {
        "meta": {
            "year": year,
            "week": week_num,
            "generated": now_iso(),
            "candidate_count": len(all_candidates),
            "sources_ok": stats["ok"],
            "sources_fail": stats["fail"],
        },
        "candidates": all_candidates,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # Sammanfattning
    print(f"\n{'─'*40}")
    print(f"📊 RESULTAT")
    print(f"  Kandidater totalt:  {before_dedup}")
    print(f"  Efter URL-dedup:    {before_seen_filter}  ({before_dedup - before_seen_filter} borttagna)")
    print(f"  Efter seen-filter:  {len(all_candidates)}  ({skipped_seen} redan sedda borttagna)")
    print(f"  Källor OK:          {stats['ok']}/{len(feeds)}")
    print(f"  Källor fail:        {stats['fail']}/{len(feeds)}")
    print(f"  Per tier:           ", end="")
    for t in sorted(stats["tier_counts"]):
        print(f"{t}: {stats['tier_counts'][t]}  ", end="")
    print(f"\n  Output:             {output_path}")
    print(f"{'─'*40}")

    seen.close()
    return 0 if stats["fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
