#!/usr/bin/env python3
"""
AI-Bladet — Scoring & Filtrering (Pipeline Steg 3)
====================================================
DeepSeek V4 Pro bedömer och rangordnar dedupade kandidater.

Två steg:
1. Pre-filter (mekanisk) — sålla bort uppenbart irrelevant
2. AI-scoring (DeepSeek V4 Pro) — bedöm nyhetsvärde, lead-potential, kategori

Input:  output/deduped/{YYYY-WW}.json
Output: output/scored/{YYYY-WW}.json
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests

# ─── Config ───────────────────────────────────────────────────────────────────

PIPELINE_DIR = Path(__file__).parent
INPUT_DIR = PIPELINE_DIR / "output" / "deduped"
OUTPUT_DIR = PIPELINE_DIR / "output" / "scored"
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
BATCH_SIZE = 25  # kandidater per API-anrop

# ─── Kända labb-organisationer på HF ─────────────────────────────────────────

KNOWN_HF_ORGS = [
    "meta", "openai", "google", "microsoft", "anthropic", "nvidia", "intel",
    "deepseek", "mistralai", "qwen", "Qwen", "QwenLM",
    "stabilityai", "black-forest-labs", "cohere",
    "01-ai", "THUDM", "zhipuai", "moonshotai", "ByteDance", "MiniMax",
    "allenai", "internlm", "OpenBMB",
    "huggingface", "facebook", "facebookresearch",
    "apple", "ibm", "samsung",
    "upstage", "kakaobrain", "naver",
]

# ─── DeepSeek API ──────────────────────────────────────────────────────────


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


def deepseek_call(prompt: str, system: str = None, max_tokens: int = 2000) -> Optional[str]:
    """Gör API-anrop till DeepSeek V4 Pro."""
    key = _get_deepseek_key()
    if not key:
        raise ValueError("DEEPSEEK_API_KEY saknas — kan inte scorea")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        r = requests.post(
            DEEPSEEK_URL,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": max_tokens,
            },
            timeout=60
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"  ⚠️  DeepSeek API-fel: {e}", file=sys.stderr)
        return None


# ─── Pre-filter ───────────────────────────────────────────────────────────────


def pre_filter(candidates: list[dict]) -> list[dict]:
    """Ta bort uppenbart irrelevanta kandidater mekaniskt."""
    kept = []
    removed = 0
    reasons = []

    for c in candidates:
        sid = c.get("source_id", "")
        title = c.get("title", "")
        summary = c.get("summary", "")
        text = f"{title} {summary}".lower()

        # HF Models: behåll bara från kända orgs
        if sid == "hf-models":
            org_match = any(org.lower() in text for org in KNOWN_HF_ORGS)
            # Kolla downloads i summary
            dl_match = re.search(r"Downloads:\s*([\d,]+)", summary)
            downloads = 0
            if dl_match:
                downloads = int(dl_match.group(1).replace(",", ""))

            if not org_match and downloads < 1000:
                removed += 1
                reasons.append(f"HF Models (okänd org, {downloads} dl): {title[:60]}")
                continue

        # arXiv papers utan upvotes
        if sid in ("arxiv-cs-ai", "arxiv-cs-cl", "arxiv-cs-lg", "arxiv-cs-cv", "arxiv-stat-ml"):
            # Behåll om den även finns i HF Daily Papers (har upvotes) eller nämner kända saker
            known_keywords = ["gpt", "llm", "transformer", "diffusion", "rlhf", "rag",
                              "agent", "alignment", "safety", "benchmark",
                              "openai", "anthropic", "google", "deepmind", "meta",
                              "fine-tuning", "pretraining", "attention"]
            if not any(kw in text for kw in known_keywords):
                removed += 1
                reasons.append(f"arXiv (ingen relevant keyword): {title[:60]}")
                continue

        # Duplicerade Google News-titlar
        if sid in ("google-news-ai", "google-news-sv"):
            title_lower = title.lower()
            # Kolla om titeln är för vag (bara företagsnamn)
            if len(title) < 30 and not any(kw in title_lower for kw in ["ai", "model", "release", "launch"]):
                removed += 1
                reasons.append(f"Google News (för vag): {title[:60]}")
                continue

        kept.append(c)

    if removed > 0:
        print(f"  🗑️  Pre-filter: {removed} borttagna")
        for r in reasons[:5]:
            print(f"    → {r}")

    return kept


# ─── AI-scoring (DeepSeek V4 Pro) ─────────────────────────────────────────────

SCORE_SYSTEM_PROMPT = """Du är en AI-nyhetsredaktör. Din uppgift: bedöm och poängsätt AI-nyheter inför ett svenskt veckobrev.

Varje artikel får en score baserat på:
- Nyhetsvärde (1-10): Hur viktig är nyheten för AI-branschen?
- Lead-potential (1-5): Skulle detta kunna vara veckans lead story?
- Svensk relevans (0-3): Relevant för svenska läsare? (Svenska bolag, EU-policy, svenska forskare)
- Kategori: Modeller, Politik, Verktyg, Forskning, Företag, Säkerhet, Övrigt

Din bedömning påverkar direkt vilka nyheter som publiceras. Var noggrann och motivera kort."""


def build_scoring_prompt(batch: list[dict], start_idx: int) -> str:
    """Bygg en prompt för en batch kandidater."""
    items = []
    for i, c in enumerate(batch):
        idx = start_idx + i
        items.append(
            f"[{idx}] Källa: {c.get('source_label', '?')}\n"
            f"    Titel: {c.get('title', '')}\n"
            f"    Sammanfattning: {c.get('summary', 'Ingen')[:200]}\n"
        )

    prompt = f"""Poängsätt följande AI-nyheter (lista med {len(batch)} st):

{"".join(items)}
Svara endast med JSON-format, ingen annan text:

{{
  "scores": [
    {{
      "id": 0,
      "news_value": 1-10,
      "lead_potential": 1-5,
      "swedish_relevance": 0-3,
      "category": "Modeller|Politik|Verktyg|Forskning|Företag|Säkerhet|Övrigt",
      "reason": "kort motivering (max 15 ord)"
    }}
  ]
}}

Varje objekt i listan 'scores' har 'id' som matchar artikelns index inom denna batch ({start_idx}-{start_idx + len(batch) - 1}).
Var strikt — ge inte höga poäng i onödan. En 7:a i nyhetsvärde är en riktigt stor nyhet."""

    return prompt


def parse_scores(response: str, batch: list[dict], start_idx: int) -> list[dict]:
    """Parsa DeepSeeks JSON-svar till score på varje kandidat."""
    try:
        # Hitta JSON i svaret
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if not json_match:
            print(f"  ⚠️  Ingen JSON i svar: {response[:200]}", file=sys.stderr)
            return _default_scores(batch, start_idx)

        data = json.loads(json_match.group(0))
        scores = data.get("scores", [])
        by_id = {s["id"]: s for s in scores}

        results = []
        for i, c in enumerate(batch):
            idx = start_idx + i
            s = by_id.get(idx, by_id.get(i, {}))
            results.append({
                "score": _clamp(s.get("news_value", 5), 1, 10),
                "lead_potential": _clamp(s.get("lead_potential", 3), 1, 5),
                "swedish_relevance": _clamp(s.get("swedish_relevance", 0), 0, 3),
                "category": s.get("category", "Övrigt"),
                "reason": s.get("reason", ""),
            })
        return results

    except (json.JSONDecodeError, AttributeError) as e:
        print(f"  ⚠️  JSON-parsefel: {e}", file=sys.stderr)
        return _default_scores(batch, start_idx)


def _clamp(val, lo, hi):
    try:
        return max(lo, min(hi, int(val)))
    except (TypeError, ValueError):
        return lo


def _default_scores(batch: list[dict], start_idx: int) -> list[dict]:
    """Default scores om API-anropet misslyckas."""
    return [
        {"score": 5, "lead_potential": 3, "swedish_relevance": 0, "category": "Övrigt", "reason": "API-fallback"}
        for _ in batch
    ]


# ─── Slutgiltig scoring (viktad) ──────────────────────────────────────────────


def final_score(c: dict) -> float:
    """Beräkna slutgiltig viktad score."""
    ai = c.get("_ai_score", {})
    tier = c.get("tier", 4)
    weight = c.get("source_weight", 10)

    news = ai.get("score", 5)
    lead = ai.get("lead_potential", 3)
    swedish = ai.get("swedish_relevance", 0)

    # Viktning:
    # news_value (0-10) ×3
    # lead_potential (0-5) ×2
    # swedish (0-3) ×4
    # tier-bonus: Tier 1 +2, Tier 2 +1, Tier 3 +0, Tier 4 -1
    tier_bonus = {1: 2, 2: 1, 3: 0}.get(tier, -1)

    raw = (news * 3) + (lead * 2) + (swedish * 4) + tier_bonus
    return round(raw, 1)


# ─── Huvudfunktion ────────────────────────────────────────────────────────────


def score(input_path: Path, output_path: Path) -> dict:
    """Kör scoring på dedupade kandidater."""
    with open(input_path) as f:
        data = json.load(f)

    candidates = data["candidates"]
    before = len(candidates)

    print(f"📊 Scoring: {before} kandidater\n")

    # Steg 1: Pre-filter
    candidates = pre_filter(candidates)

    # Steg 2: Ladda source weights från config
    try:
        import yaml
        with open(PIPELINE_DIR / "config" / "sources.yaml") as f:
            cfg = yaml.safe_load(f)
        feed_map = {f["id"]: f.get("weight", 10) for f in cfg.get("feeds", [])}
    except Exception:
        feed_map = {}

    for c in candidates:
        c["source_weight"] = feed_map.get(c.get("source_id", ""), 10)

    # Begränsa till topp 100 för AI-scoring (kvalitet framför kvantitet)
    # Sortera preliminärt efter tier + weight
    candidates.sort(key=lambda c: (c.get("tier", 99), -c["source_weight"]))

    scoring_batch = candidates[:100]  # max 100 till AI
    print(f"  🎯 Skickar {len(scoring_batch)} till DeepSeek V4 Pro för scoring\n")

    # Batcha och scorea
    all_scores = []
    for batch_start in range(0, len(scoring_batch), BATCH_SIZE):
        batch = scoring_batch[batch_start:batch_start + BATCH_SIZE]
        idx_start = batch_start

        print(f"  🤖 Batch {batch_start//BATCH_SIZE + 1}: "
              f"artikel {idx_start}-{idx_start + len(batch) - 1}...", end=" ", flush=True)

        prompt = build_scoring_prompt(batch, idx_start)
        response = deepseek_call(prompt, SCORE_SYSTEM_PROMPT)

        if response:
            scores = parse_scores(response, batch, idx_start)
            all_scores.extend(scores)
            print(f"{len(scores)} scored ✅")
        else:
            all_scores.extend(_default_scores(batch, idx_start))
            print("failed ⚠️")

    # Applicera AI-scores
    for i, c in enumerate(scoring_batch):
        if i < len(all_scores):
            c["_ai_score"] = all_scores[i]

    # Default scores för resten (inte i AI-batch)
    for c in candidates[len(scoring_batch):]:
        c["_ai_score"] = {"score": 3, "lead_potential": 1, "swedish_relevance": 0, "category": "Övrigt", "reason": "Ej i topp 100"}

    # Beräkna final score
    for c in candidates:
        c["final_score"] = final_score(c)

    # Sortera efter final score (fallande)
    candidates.sort(key=lambda c: -c["final_score"])

    # Skriv output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output = {
        "meta": {
            **data.get("meta", {}),
            "before_scoring": before,
            "after_prefilter": before - (before - len(candidates)),
            "after_scoring": len(candidates),
            "ai_batch_size": len(scoring_batch),
            "scored_at": datetime.now(timezone.utc).isoformat(),
        },
        "candidates": candidates,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # Sammanfattning
    print(f"\n{'─'*40}")
    print(f"📊 SCORING RESULTAT")
    print(f"  Före pre-filter:   {before}")
    print(f"  Efter pre-filter:  {len(candidates)}")
    print(f"  AI-scoreade:       {len(scoring_batch)}")
    print(f"  Topp 10:")
    for c in candidates[:10]:
        ai = c.get("_ai_score", {})
        print(f"  {'⭐' if ai.get('lead_potential', 0) >= 4 else '  '}"
              f" {c['final_score']:5.1f} | [{ai.get('category','?')}] "
              f"{c['title'][:70]}")
    print(f"  Output:            {output_path}")
    print(f"{'─'*40}")

    return {"before": before, "after": len(candidates)}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AI-Bladet scoring")
    parser.add_argument("input", nargs="?", help="Input JSON (dedupade)")
    args = parser.parse_args()

    if args.input:
        input_path = Path(args.input)
    else:
        deduped = sorted(INPUT_DIR.glob("*.json"))
        if not deduped:
            print("Inga dedupade filer hittades.")
            sys.exit(1)
        input_path = deduped[-1]

    week = input_path.stem
    output_path = OUTPUT_DIR / f"{week}.json"

    result = score(input_path, output_path)
    sys.exit(0)
