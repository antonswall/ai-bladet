#!/usr/bin/env python3
"""Verifiera att rätt AI-Bladet-upplaga faktiskt är live på Cloudflare."""

from __future__ import annotations

import argparse
import html
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable

import yaml

SITE_URL = os.getenv("AI_BLADET_SITE_URL", "https://ai-bladet.pages.dev").rstrip("/")


def load_issue_identity(issue_path: str | Path) -> dict:
    path = Path(issue_path)
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"Ofullständig YAML-frontmatter i {path}")
    data = yaml.safe_load(parts[1]) or {}
    missing = [key for key in ("year", "week", "title") if not data.get(key)]
    if missing:
        raise ValueError(f"Issue saknar obligatoriska fält: {', '.join(missing)}")
    return {
        "year": int(data["year"]),
        "week": int(data["week"]),
        "title": str(data["title"]).strip(),
    }


def _visible_text(document: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", html.unescape(document))
    return " ".join(without_tags.split())


def fetch_text(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (AI-Bladet deploy verifier)",
            "Cache-Control": "no-cache",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status} för {url}")
        return response.read().decode("utf-8", errors="replace")


def verify_live_issue(
    identity: dict,
    *,
    fetch_text: Callable[[str], str] = fetch_text,
    attempts: int = 18,
    delay_seconds: float = 10,
    sleep_fn: Callable[[float], None] = time.sleep,
    require_assets: bool = False,
) -> tuple[bool, str]:
    title = identity["title"]
    year = identity["year"]
    week = identity["week"]
    last_reason = "ingen kontroll kördes"

    for attempt in range(1, attempts + 1):
        cache_buster = urllib.parse.urlencode({"verify": f"{year}-{week}-{attempt}"})
        resources = {
            "permalänken": (f"{SITE_URL}/v/{year}/{week:02d}/?{cache_buster}", title),
            "startsidan": (f"{SITE_URL}/?{cache_buster}", title),
        }
        if require_assets:
            resources.update(
                {
                    "RSS": (f"{SITE_URL}/feed.xml?{cache_buster}", title),
                    "podcast-RSS": (f"{SITE_URL}/feed/podcast.xml?{cache_buster}", title),
                    "ljud": (f"{SITE_URL}/audio/{year}-{week:02d}.mp3?{cache_buster}", None),
                    "meme": (f"{SITE_URL}/memes/{year}-{week:02d}.png?{cache_buster}", None),
                }
            )
        failures = []
        for label, (url, expected_text) in resources.items():
            try:
                document = fetch_text(url)
                if expected_text and expected_text not in _visible_text(document):
                    failures.append(f"{label} visar inte titeln '{expected_text}'")
            except Exception as exc:
                failures.append(f"{label}: {type(exc).__name__}: {exc}")

        if not failures:
            return True, f"rätt upplaga live efter försök {attempt}/{attempts}"

        last_reason = "; ".join(failures)
        print(f"  ⚠️ Live-verifiering {attempt}/{attempts}: {last_reason}", flush=True)
        if attempt < attempts:
            sleep_fn(delay_seconds)

    return False, last_reason


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--issue", required=True, help="content/YYYY-WW.md")
    parser.add_argument(
        "--attempts",
        type=int,
        default=int(os.getenv("AI_BLADET_DEPLOY_ATTEMPTS", "18")),
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=float(os.getenv("AI_BLADET_DEPLOY_DELAY", "10")),
    )
    parser.add_argument(
        "--require-assets",
        action="store_true",
        help="Kräv även RSS, podcast-RSS, ljud och meme för aktuell vecka",
    )
    args = parser.parse_args()

    try:
        identity = load_issue_identity(args.issue)
        ok, reason = verify_live_issue(
            identity,
            attempts=args.attempts,
            delay_seconds=args.delay,
            require_assets=args.require_assets,
        )
    except Exception as exc:
        print(f"❌ Live-verifiering kunde inte starta: {exc}")
        return 1

    if not ok:
        print(f"❌ Rätt upplaga är inte verifierad live: {reason}")
        return 1

    print(
        f"✅ Live-verifierad: vecka {identity['week']}/{identity['year']} — "
        f"{identity['title']} ({reason})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
