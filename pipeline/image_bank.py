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

# ── Utökad bank (2026-06-21) ──────────────────────────────────────────────────
SERVER_RACK = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/6/69/Wikimedia_Foundation_Servers-8055_35.jpg/1280px-Wikimedia_Foundation_Servers-8055_35.jpg",
    "Foto · Victor Grigas / CC BY-SA 3.0")
EU_PARLIAMENT = _c(
    "https://upload.wikimedia.org/wikipedia/commons/2/2c/European_Parliament_Strasbourg_Hemicycle_-_Diliff.jpg",
    "Foto · Diliff / CC BY-SA 3.0")
EU_COMMISSION = _c(
    "https://upload.wikimedia.org/wikipedia/commons/d/d2/Belgique_-_Bruxelles_-_Schuman_-_Berlaymont_-_01.jpg",
    "Foto · EmDee / CC BY-SA 3.0")
RIKSDAG = _c(
    "https://upload.wikimedia.org/wikipedia/commons/5/5a/Government_buildings_by_Norrstr%C3%B6m_in_Stockholm_Sweden_01.jpg",
    "Foto · Sinikka Halme / CC BY-SA 4.0")
MICROCHIP = _c(
    "https://upload.wikimedia.org/wikipedia/commons/6/64/Intel_8742_153056995.jpg",
    "Foto · Ioan Sameli / CC BY-SA 2.0")


# ── 1. Tematiska nyckelord (slår källan när de matchar story-texten) ──────────
#    Ordning spelar roll — första matchande bucket vinner.
KEYWORD_BUCKETS = [
    ("ipo", ["börs", "ipo", "s-1", "s1", " sec", "notering", "nasdaq", "nyse", "börsnotering"],
     [NYSE]),
    ("energi", ["elpris", "elpriser", "energi", "energy", "kraftledning", "elnät"],
     [POWERLINES]),
    ("compute", ["gpu", "grafikkort", "colossus", "200 000", "superdator", "kluster",
                 "beräkningskraft", "serverhall", "datacenter", "data center", "tränad", "träning",
                 "chip", "chipp", "processor", "h100", "b100", "trainium", "inferens"],
     [DATACENTER, DATACENTER2, SERVER_RACK, MICROCHIP]),
    ("rymd", ["spacex", "raket", "falcon", "rymd", "satellit", "förvärv", "köper", "köpte", "joins"],
     [MUSK, FALCON9]),
    ("eu", ["eu", "europeisk", "bryssel", "kommissionen", "parlamentet", "eu:s", "gdpr",
            "ai-förordningen", "eu-kommissionen", "europa", "europeiska unionen"],
     [EU_PARLIAMENT, EU_COMMISSION, OPENAI_EC]),
    ("sverige", ["sverige", "svensk", "stockholm", "svenska", "sveriges", "riksdag", "kista"],
     [RIKSDAG, OPENAI_EC]),
    ("reglering", ["domstol", "exportkontroll", "reglering", "lag", "förbud", "böter", "dömd",
                   "regulator", "tillsyn", "myndighet", "beslut", "supreme"],
     [NYSE, EU_PARLIAMENT]),
    ("robot", ["robot", "robotarm", "automatisering", "humanoid", "autonom"],
     [DATACENTER2, MICROCHIP]),
    ("chip", ["halvledare", "chip", "chipp", "processor", "h100", "b100", "semiconductor",
              "wafer", "kisel", "euv", "asml", "tsmc", "tillverkning", "fabrik", "factory"],
     [MICROCHIP, SERVER_RACK, DATACENTER]),
]

# ── 2. Per källa (source_id) — porträtt/varumärke ────────────────────────────
SOURCE_BUCKETS = {
    "openai": [ALTMAN, OPENAI_EC],
    "google-ai": [GOOGLE_SIGN, GOOGLE_ENTRANCE],
    "xai": [MUSK, FALCON9],
}

# ── 3. Kategori-fallback ─────────────────────────────────────────────────────
CATEGORY_BUCKETS = {
    "Företag": [NYSE, DATACENTER2, GOOGLE_ENTRANCE],
    "Modeller": [DATACENTER, SERVER_RACK, DATACENTER2, MICROCHIP],
    "Säkerhet": [DATACENTER2, POWERLINES, EU_PARLIAMENT],
    "Forskning": [DATACENTER2, DATACENTER, MICROCHIP],
    "Politik": [EU_PARLIAMENT, RIKSDAG, EU_COMMISSION],
    "Verktyg": [SERVER_RACK, DATACENTER, MICROCHIP],
    "default": [DATACENTER, DATACENTER2, SERVER_RACK, MICROCHIP],
}


def _haystack(story: dict) -> str:
    b = story.get("fact_brief", {}) or {}
    parts = [str(story.get("title", "")), str(story.get("source_label", "")),
             str(story.get("category", "")), str(b.get("summary", ""))]
    parts += [str(x) for x in (b.get("key_facts") or [])]
    return " ".join(parts).lower()


def pick(story: dict, used: set) -> tuple[str, str]:
    """Välj (url, credit) för en story. `used` muteras för att undvika dubbletter.

    Tre steg: 1) temanyckelord → 2) källa → 3) kategori → 4) default.
    Om alla kandidater i ett steg är använda, fall tillbaka till nästa steg.
    Om ALLT är använt (inklusive default), tillåt repris som sista utväg."""
    hay = _haystack(story)

    def _try_candidates(cands: list) -> tuple[str, str] | None:
        for c in cands:
            if c["url"] not in used:
                used.add(c["url"])
                return c["url"], c["credit"]
        return None

    # 1. Tema (keyword)
    for _name, kws, cands in KEYWORD_BUCKETS:
        if any(k in hay for k in kws):
            result = _try_candidates(cands)
            if result:
                return result
            break  # bucket matchade men alla bilder använda → fall igenom

    # 2. Källa
    result = _try_candidates(SOURCE_BUCKETS.get(story.get("source_id", ""), []))
    if result:
        return result

    # 3. Kategori
    result = _try_candidates(CATEGORY_BUCKETS.get(story.get("category", ""), []))
    if result:
        return result

    # 4. Default
    result = _try_candidates(CATEGORY_BUCKETS["default"])
    if result:
        return result

    # 5. Allt använt — tillåt repris (välj första default-bilden)
    c = CATEGORY_BUCKETS["default"][0]
    used.add(c["url"])
    return c["url"], c["credit"]
