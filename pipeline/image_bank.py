#!/usr/bin/env python3
"""
AI-Bladet — Redaktionell bildbank
=================================
Kurerade, fria pressfoton (Wikimedia Commons) som väljs AUTOMATISKT per story
i images.py. Syftet: slående, läsarvänliga bilder (ansikten, serverhallar,
kraftledningar, raketer) i stället för källornas tråkiga marknadsförings-banners.

Varje post har en verifierad hotlink-bar URL + korrekt fotobyline med licens.
Val sker i tre steg (se pick()): 1) tematiska nyckelord, 2) källa, 3) kategori.
Banken är medvetet liten — pipelinens källor är en fast uppsättning (OpenAI,
Google, xAI, Qwen). Lägg till fler poster när nya återkommande aktörer dyker upp.

Alla URL:er HEAD-verifierade 2026-06-18 (200 image/jpeg).
"""


def _c(url, credit):
    return {"url": url, "credit": credit}


# ── Återanvändbara foton ──────────────────────────────────────────────────────
GOOGLE_SIGN = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Google_Headquarters_in_Ireland_Building_Sign.jpg/1280px-Google_Headquarters_in_Ireland_Building_Sign.jpg",
    "Foto · OutreachPete / CC BY 2.0")
GOOGLE_ENTRANCE = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/Google_Headquarters_in_Ireland_Building_Front_Entrance.jpg/1280px-Google_Headquarters_in_Ireland_Building_Front_Entrance.jpg",
    "Foto · OutreachPete / CC BY 2.0")
ALTMAN = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/3/32/Sam_Altman_November_2022.jpg/1280px-Sam_Altman_November_2022.jpg",
    "Foto · Village Global / CC BY 2.0")
OPENAI_EC = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Visit_of_OpenAI_representatives_to_the_European_Commission_-_P061880-380830.jpg/1280px-Visit_of_OpenAI_representatives_to_the_European_Commission_-_P061880-380830.jpg",
    "Foto · Europeiska kommissionen / CC BY 4.0")
MUSK = _c(
    "https://upload.wikimedia.org/wikipedia/commons/9/99/Elon_Musk_Colorado_2022_%28cropped2%29.jpg",
    "Foto · Trevor Cokley / U.S. Air Force / Public domain")
FALCON9 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/7/72/2016_Falcon_9_at_Vandenberg_Air_Force_Base.jpg/1280px-2016_Falcon_9_at_Vandenberg_Air_Force_Base.jpg",
    "Foto · SpaceX / CC0")
DATACENTER = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/BalticServers_data_center.jpg/1280px-BalticServers_data_center.jpg",
    "Foto · BalticServers.com / CC BY-SA 3.0")
DATACENTER2 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Data_Center_2_%28UNC%29.jpg/1280px-Data_Center_2_%28UNC%29.jpg",
    "Foto · Ana Las Heras / CC BY-SA 4.0")
POWERLINES = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f0/Power_lines_during_Blue_Hour_BW.jpg/1280px-Power_lines_during_Blue_Hour_BW.jpg",
    "Foto · PumpkinSky / CC BY-SA 3.0")
NYSE = _c(
    "https://upload.wikimedia.org/wikipedia/commons/2/23/Trading_Floor_at_the_New_York_Stock_Exchange.jpg",
    "Foto · Scott Beale / CC BY-SA 4.0")


# ── 1. Tematiska nyckelord (slår källan när de matchar story-texten) ──────────
#    Ordning spelar roll — första matchande bucket vinner.
KEYWORD_BUCKETS = [
    ("ipo", ["börs", "ipo", "s-1", "s1", " sec", "notering", "nasdaq", "nyse", "börsnotering"],
     [NYSE]),
    ("energi", ["elpris", "elpriser", "energi", "energy", "kraftledning", "elnät"],
     [POWERLINES]),
    ("compute", ["gpu", "grafikkort", "colossus", "200 000", "superdator", "kluster",
                 "beräkningskraft", "serverhall", "datacenter", "data center", "tränad", "träning"],
     [DATACENTER, DATACENTER2]),
    ("rymd", ["spacex", "raket", "falcon", "rymd", "satellit", "förvärv", "köper", "köpte", "joins"],
     [MUSK, FALCON9]),
]

# ── 2. Per källa (source_id) — porträtt/varumärke ────────────────────────────
SOURCE_BUCKETS = {
    "openai": [ALTMAN, OPENAI_EC],
    "google-ai": [GOOGLE_SIGN, GOOGLE_ENTRANCE],
    "xai": [MUSK, FALCON9],
    # qwen saknar eget foto → faller igenom till kategori/default
}

# ── 3. Kategori-fallback ─────────────────────────────────────────────────────
CATEGORY_BUCKETS = {
    "Företag": [NYSE, DATACENTER2],
    "Modeller": [DATACENTER, DATACENTER2],
    "Säkerhet": [DATACENTER2, POWERLINES],
    "Forskning": [DATACENTER2, DATACENTER],
    "Verktyg": [DATACENTER, DATACENTER2],
    "default": [DATACENTER, DATACENTER2],
}


def _haystack(story: dict) -> str:
    b = story.get("fact_brief", {}) or {}
    parts = [str(story.get("title", "")), str(story.get("source_label", "")),
             str(story.get("category", "")), str(b.get("summary", ""))]
    parts += [str(x) for x in (b.get("key_facts") or [])]
    return " ".join(parts).lower()


def pick(story: dict, used: set) -> tuple[str, str]:
    """Välj (url, credit) för en story. `used` muteras för att undvika dubbletter."""
    hay = _haystack(story)

    candidates = []
    for _name, kws, cands in KEYWORD_BUCKETS:           # 1. tema
        if any(k in hay for k in kws):
            candidates = cands
            break
    if not candidates:                                  # 2. källa
        candidates = SOURCE_BUCKETS.get(story.get("source_id", ""), [])
    if not candidates:                                  # 3. kategori
        candidates = CATEGORY_BUCKETS.get(story.get("category", ""), [])
    if not candidates:                                  # 4. default
        candidates = CATEGORY_BUCKETS["default"]

    for c in candidates:                                # första oanvända
        if c["url"] not in used:
            used.add(c["url"])
            return c["url"], c["credit"]
    c = candidates[0]                                   # allt använt → tillåt repris
    used.add(c["url"])
    return c["url"], c["credit"]
