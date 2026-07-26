#!/usr/bin/env python3
"""
AI-Bladet — Semantisk Dedup (Pipeline Steg 2)
===============================================
Klustrar ihop samma nyhet från olika källor och behåller
den bästa versionen per kluster.

Två-stegs process:
1. Regex-baserad entitetsextraktion (billig, snabb)
2. GPT-5.6 Sol via Codex CLI för osäkra gränsfall (precisionshöjning)

Input:  output/candidates/{YYYY-WW}.json (från collect.py)
Output: output/deduped/{YYYY-WW}.json
"""

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests
import yaml

from llm import llm_call

# ─── Config ───────────────────────────────────────────────────────────────────

PIPELINE_DIR = Path(__file__).parent
CONFIG_PATH = PIPELINE_DIR / "config" / "sources.yaml"
INPUT_DIR = PIPELINE_DIR / "output" / "candidates"
OUTPUT_DIR = PIPELINE_DIR / "output" / "deduped"
REQUEST_TIMEOUT = 20

# Ladda source weights från config
feed_map = {}
try:
    with open(CONFIG_PATH) as f:
        cfg = yaml.safe_load(f)
    feed_map = {f["id"]: f.get("weight", 10) for f in cfg.get("feeds", [])}
except Exception:
    pass

# ─── Entitetsregexar ─────────────────────────────────────────────────────────

# Modellnamn (prioritera specifika → generella)
MODEL_NAMES = re.compile(
    r"(?:GPT-|Claude|Grok|Llama|Gemini|Qwen|DeepSeek|Mistral|DALL-E|Stable Diffusion|"
    r"FLUX|Yi|Falcon|Phi-4|Phi-3|Gemma|Mamba|Mixtral|Nemotron|"
    r"Codex|Copilot|Cursor|Windsurf)"
    r"\s*(?:[\d.]+\s*)*(?:Preview|Vision|Turbo|Mini|Max|Ultra|Pro|Fast)?",
    re.IGNORECASE
)

# Företagsnamn
COMPANY_NAMES = re.compile(
    r"(OpenAI|Anthropic|Google|DeepMind|Meta[ -]?AI|Microsoft|NVIDIA|"
    r"Apple|Amazon|AWS|Salesforce|IBM|Intel|AMD|"
    r"Samsung|ByteDance|Tencent|Alibaba|Huawei|Baidu|"
    r"Mistral[ -]?AI|xAI|Stability[ -]?AI|Cohere|Hugging[ -]?Face|"
    r"Scale[ -]?AI|Databricks|Perplexity|Notion[ -]?AI|"
    r"Ailingo|Sana|ElevenLabs|Runway|Midjourney)",
    re.IGNORECASE
)

# Produkter/verktyg
PRODUCT_NAMES = re.compile(
    r"(GitHub Copilot|Claude Code|Grok Build|ChatGPT|Gemini|"
    r"ComfyUI|vLLM|LangChain|LlamaIndex|Hugging Face|"
    r"Replit Agent|Devon|Devin|"
    r"Spotify AI|Notion AI|Adobe Firefly|"
    r"Windows|macOS|iOS|Android)",
    re.IGNORECASE
)

# Ämnen/kategorier
TOPIC_KEYWORDS = re.compile(
    r"(reglering|säkerhet|alignment|safety|policy|etik|"
    r"finansiering|investering|kapital|miljoner|miljarder|"
    r"samarbete|partnerskap|acquisition|förvärv|"
    r"benchmark|prestanda|resultat|rekord|genombrott|"
    r"öppen[ -]?källkod|open[ -]?source|"
    r"EU[ -]?kommissionen|AI[ -]?Act|förordning|"
    r"verktyg|tool|lansering|release|uppdatering|"
    r"forskning|paper|studie|rapport|"
    r"rättegång|stämning|copyright|upphovsrätt)",
    re.IGNORECASE
)

# Pengar (summor, investeringar)
MONEY_PATTERN = re.compile(
    r"\d[\d\s]*(?:miljoner|miljarder|Mkr|mdkr|[MBT]?[$€£¥])\s*(?:kronor|dollar|euro)?",
    re.IGNORECASE
)

# Kinesiska labb
CHINESE_LABS = re.compile(
    r"(Qwen|DeepSeek|01[.-]?AI|Moonshot|Kimi|GLM|Zhipu|"
    r"ByteDance|Tencent|Huawei|Baidu|Alibaba|"
    r"InternLM|Yi[ -]?Lightning|MiniMax|Hunyuan)",
    re.IGNORECASE
)


def extract_entities(title: str, summary: str = "") -> dict:
    """Extrahera entiteter från titel + ev. sammanfattning."""
    text = f"{title} {summary}"

    models = list(set(m.strip() for m in MODEL_NAMES.findall(text) if len(m.strip()) > 2))
    companies = list(set(c.strip() for c in COMPANY_NAMES.findall(text) if len(c.strip()) > 2))
    products = list(set(p.strip() for p in PRODUCT_NAMES.findall(text) if len(p.strip()) > 2))
    topics = list(set(t.strip().lower() for t in TOPIC_KEYWORDS.findall(text) if len(t.strip()) > 2))
    money = list(set(m.strip() for m in MONEY_PATTERN.findall(text)))
    chinese = list(set(c.strip() for c in CHINESE_LABS.findall(text) if len(c.strip()) > 2))

    # Rensa duplikater
    models = [m for m in models if m]
    companies = [c for c in companies if c]
    products = [p for p in products if p]
    topics = [t for t in topics if t]
    money = [m for m in money if m]
    chinese = [c for c in chinese if c]

    return {
        "models": models,
        "companies": companies,
        "products": products,
        "topics": topics,
        "money": money,
        "chinese_labs": chinese,
        # Skapa en enkel signatur
        "signature_parts": sorted(set(
            [m.lower() for m in models] +
            [c.lower() for c in companies] +
            [p.lower() for p in products] +
            [t.lower() for t in topics]
        ))
    }


def entities_match(e1: dict, e2: dict, threshold: int = 2) -> bool:
    """Kolla om två entitetsuppsättningar indikerar samma story."""
    if not e1 or not e2:
        return False

    parts1 = set(e1.get("signature_parts", []))
    parts2 = set(e2.get("signature_parts", []))

    if not parts1 or not parts2:
        return False

    overlap = parts1 & parts2

    # Minst 2 gemensamma entiteter för match
    if len(overlap) >= threshold:
        return True

    # Specialfall: samma modellnamn räcker
    models1 = set(m.lower() for m in e1.get("models", []))
    models2 = set(m.lower() for m in e2.get("models", []))
    if models1 & models2 and (models1 & parts2 or models2 & parts1):
        return True

    # Specialfall: samma företag + ämne räcker även om bara 1 match
    companies1 = set(c.lower() for c in e1.get("companies", []))
    companies2 = set(c.lower() for c in e2.get("companies", []))
    topics1 = set(e1.get("topics", []))
    topics2 = set(e2.get("topics", []))

    if (companies1 & companies2) and (topics1 & topics2):
        return True

    return False


# ─── GPT-5.6 Sol via Codex CLI för osäkra fall ─────────────────────────────


def llm_verify_cluster(candidates: list[dict]) -> list[dict]:
    """Använd GPT-5.6 Sol för att verifiera ett kluster.
    Returnerar kandidaterna med cluster_id satt."""
    if len(candidates) < 2:
        for c in candidates:
            c["cluster_id"] = candidates[0].get("content_hash", "0")
            c["cluster_size"] = 1
        return candidates

    items_text = "\n".join(
        f"{i+1}. [{c['source_label']}] {c['title']}"
        for i, c in enumerate(candidates)
    )

    prompt = f"""Du klustrar AI-nyheter. Samma story från olika källor ska ha samma kluster-ID.

Artiklar:
{items_text}

Fråga: Vilka av dessa handlar om SAMMA nyhet/händelse?
Svara endast med ett JSON-objekt:
{{"clusters": [{{"article_ids": [1, 3, 5], "story": "kort rubrik"}}]}}

Där article_ids är index (1-baserat) för artiklar som hör ihop."""

    try:
        content = llm_call(
            prompt,
            system="Du klustrar AI-nyheter. Svara endast med JSON.",
            max_tokens=500,
            temperature=0,
        )
        if not content:
            raise ValueError("Tomt svar från Codex CLI")

        # Extract JSON — städa bort kodblock
        cleaned = re.sub(r"```(?:json)?\s*", "", content).strip()
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError(f"Ingen JSON i svar: {content[:200]}")

        clusters = json.loads(cleaned[start:end+1]).get("clusters", [])

        # Applicera kluster-ID
        for ci, cluster in enumerate(clusters):
            cluster_id = f"ai-{ci:04d}"
            story = cluster.get("story", f"story-{ci}")
            for aid in cluster.get("article_ids", []):
                idx = aid - 1  # 0-indexed
                if 0 <= idx < len(candidates):
                    candidates[idx]["cluster_id"] = cluster_id
                    candidates[idx]["cluster_story"] = story

        # Markera oklustrade som singlar
        for c in candidates:
            if "cluster_id" not in c:
                c["cluster_id"] = f"ai-99{candidates.index(c):04d}"
                c["cluster_story"] = c.get("title", "okänd")[:100]
            c["cluster_size"] = sum(
                1 for oc in candidates if oc.get("cluster_id") == c.get("cluster_id")
            )

    except Exception as e:
        print(f"  ⚠️  GPT-5.6 verify misslyckades: {e}", file=sys.stderr)
        # Fallback: allt i ett kluster
        cluster_id = candidates[0].get("content_hash", "0")
        for c in candidates:
            c["cluster_id"] = cluster_id
            c["cluster_size"] = 1

    return candidates


# ─── Huvudfunktion ────────────────────────────────────────────────────────────

def dedup(input_path: Path, output_path: Path, use_ai: bool = True) -> dict:
    """Kör semantisk dedup på kandidater."""
    with open(input_path) as f:
        data = json.load(f)

    candidates = data["candidates"]
    before = len(candidates)

    print(f"🔍 Semantisk dedup: {before} kandidater\n")

    # Steg 1: Extrahera entiteter
    for c in candidates:
        c["_entities"] = extract_entities(c.get("title", ""), c.get("summary", ""))

    # Steg 2: Klustra baserat på entiteter
    clusters = []
    assigned = set()

    for i, c1 in enumerate(candidates):
        if i in assigned:
            continue
        cluster = [i]
        assigned.add(i)

        for j, c2 in enumerate(candidates):
            if j in assigned:
                continue
            if entities_match(c1["_entities"], c2["_entities"]):
                cluster.append(j)
                assigned.add(j)

        clusters.append(cluster)

    print(f"  🏷️  Steg 1 (regex): {len(candidates)} → {len(clusters)} kluster")
    avg_size = sum(len(cl) for cl in clusters) / len(clusters) if clusters else 0
    print(f"  ⌀ Genomsnittlig klusterstorlek: {avg_size:.1f}")

    # Steg 3: GPT-5.6 Sol för stora/komplexa kluster
    if use_ai:
        large_clusters = [cl for cl in clusters if len(cl) > 3]
        if large_clusters:
            print(f"  🧠  GPT-5.6 Sol granskar {len(large_clusters)} stora kluster...")
            for cl in large_clusters:
                cluster_candidates = [candidates[i] for i in cl]
                llm_verify_cluster(cluster_candidates)
                for i, c_idx in enumerate(cl):
                    candidates[c_idx] = cluster_candidates[i]

    # Steg 4: Välj bästa kandidaten per kluster
    selected = []
    removed = 0

    for cl in clusters:
        if len(cl) == 1:
            c = candidates[cl[0]]
            c["cluster_id"] = c.get("content_hash", str(cl[0]))
            c["cluster_size"] = 1
            selected.append(c)
            continue

        # Rangordna inom klustret efter tier (primary), weight (secondary)
        ranked = sorted(
            [candidates[i] for i in cl],
            key=lambda c: (
                c.get("tier", 99),
                -feed_map.get(c.get("source_id", ""), 10),
                -len(c.get("summary", ""))
            )
        )

        # Behåll ettan, markera resten som dupes
        best = ranked[0]
        best["cluster_id"] = cl[0]
        best["cluster_size"] = len(cl)
        selected.append(best)
        removed += len(ranked) - 1

    # Sortera: tier → weight
    selected.sort(key=lambda c: (
        c.get("tier", 99),
        -feed_map.get(c.get("source_id", ""), 10),
    ))

    # Städa bort temporära fält
    for c in selected:
        c.pop("_entities", None)

    # Skriv output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output = {
        "meta": {
            **data.get("meta", {}),
            "before_dedup": before,
            "after_dedup": len(selected),
            "clusters": len(clusters),
            "dupes_removed": removed,
            "dedup_time": datetime.now(timezone.utc).isoformat(),
        },
        "candidates": selected,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n{'─'*40}")
    print(f"📊 DEDUP RESULTAT")
    print(f"  Kandidater före:   {before}")
    print(f"  Kluster:           {len(clusters)}")
    print(f"  Dupes borttagna:   {removed}")
    print(f"  Kvarvarande:       {len(selected)}")
    print(f"  Output:            {output_path}")
    print(f"{'─'*40}")

    return {"before": before, "after": len(selected), "clusters": len(clusters)}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AI-Bladet semantisk dedup")
    parser.add_argument("input", nargs="?", help="Input JSON (candidates)")
    parser.add_argument("--no-ai", action="store_true", help="Skippa DeepSeek V4")
    args = parser.parse_args()

    # Auto-detect senaste candidates
    if args.input:
        input_path = Path(args.input)
    else:
        candidates = sorted(INPUT_DIR.glob("*.json"))
        if not candidates:
            print("Inga kandidatfiler hittades. Kör collect.py först.")
            sys.exit(1)
        input_path = candidates[-1]

    week = input_path.stem  # YYYY-WW
    output_path = OUTPUT_DIR / f"{week}.json"

    result = dedup(input_path, output_path, use_ai=not args.no_ai)
    sys.exit(0)
