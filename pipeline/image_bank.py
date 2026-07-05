#!/usr/bin/env python3
"""
AI-Bladet — Redaktionell bildbank (rensad v3)
==============================================
Kurerade, fria pressfoton (Wikimedia Commons). Rensad 2026-07-05:
endast bilder med VERKLIG motivrelevans (personer, HQ, datacenter,
chip, EU/Sverige). Generiska kategori-/default-listor är borttagna —
banken används numera bara som näst sista fallback i images.py, och
enbart vid specifik träff (tema eller källa). Ingen träff → None →
grafisk placeholder (fallback_image.py).

API: pick_specific(story, used) -> (url, credit) | None
"""


def _c(url, credit):
    return {"url": url, "credit": credit}


# ── Datacenter & compute ──
IMG_7 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a0/5_Pionen_Data_Centre.tif/lossy-page1-1280px-5_Pionen_Data_Centre.tif.jpg",
    "Foto · Simon Klose / CC BY 3.0")
IMG_10 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/9/9e/Abudhabi_data_center.jpg",
    "Foto · Gulfdatahub / CC BY-SA 4.0")
IMG_11 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/5/51/Aerial-utah-data-center.jpg",
    "Foto · حمزة مستقيم / CC BY-SA 4.0")
IMG_45 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/BalticServers_data_center.jpg/1280px-BalticServers_data_center.jpg",
    "Foto · BalticServers.com / CC BY-SA 3.0")
IMG_46 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Data_Center_2_%28UNC%29.jpg/1280px-Data_Center_2_%28UNC%29.jpg",
    "Foto · Ana Las Heras / CC BY-SA 4.0")
IMG_49 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/6/69/Wikimedia_Foundation_Servers-8055_35.jpg/1280px-Wikimedia_Foundation_Servers-8055_35.jpg",
    "Foto · Victor Grigas / CC BY-SA 3.0")
IMG_53 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/6/64/Intel_8742_153056995.jpg",
    "Foto · Ioan Sameli / CC BY-SA 2.0")

# ── Energi ──
IMG_25 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d8/AMP_Energy_Bhadla_Solar_Power_Plant_-_53699816551.jpg/1280px-AMP_Energy_Bhadla_Solar_Power_Plant_-_53699816551.jpg",
    "Foto · Sarvajanik Puralekh / CC BY-SA 2.0")
IMG_37 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Barseback_Nuclear_Power_Plant.jpg/1280px-Barseback_Nuclear_Power_Plant.jpg",
    "Foto · Vitold Muratov / CC BY-SA 4.0")
IMG_47 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f0/Power_lines_during_Blue_Hour_BW.jpg/1280px-Power_lines_during_Blue_Hour_BW.jpg",
    "Foto · PumpkinSky / CC BY-SA 3.0")

# ── Personer & bolag ──
IMG_27 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/7/78/MS-Exec-Nadella-Satya-2017-08-31-22_%28cropped%29.jpg/1280px-MS-Exec-Nadella-Satya-2017-08-31-22_%28cropped%29.jpg",
    "Foto · Brian Smale and Microsoft / CC BY-SA 4.0")
IMG_29 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6c/Satya_Nadella.jpg/1280px-Satya_Nadella.jpg",
    "Foto · OFFICIAL LEWEB PHOTOS / CC BY 2.0")
IMG_39 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Google_Headquarters_in_Ireland_Building_Sign.jpg/1280px-Google_Headquarters_in_Ireland_Building_Sign.jpg",
    "Foto · OutreachPete / CC BY 2.0")
IMG_41 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/3/32/Sam_Altman_November_2022.jpg/1280px-Sam_Altman_November_2022.jpg",
    "Foto · Village Global / CC BY 2.0")
IMG_42 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Visit_of_OpenAI_representatives_to_the_European_Commission_-_P061880-380830.jpg/1280px-Visit_of_OpenAI_representatives_to_the_European_Commission_-_P061880-380830.jpg",
    "Foto · Europeiska kommissionen / CC BY 4.0")
IMG_43 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/9/99/Elon_Musk_Colorado_2022_%28cropped2%29.jpg",
    "Foto · Trevor Cokley / U.S. Air Force / Public domain")
IMG_44 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/7/72/2016_Falcon_9_at_Vandenberg_Air_Force_Base.jpg/1280px-2016_Falcon_9_at_Vandenberg_Air_Force_Base.jpg",
    "Foto · SpaceX / CC0")

# ── Börs, EU & Sverige ──
IMG_48 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/2/23/Trading_Floor_at_the_New_York_Stock_Exchange.jpg",
    "Foto · Scott Beale / CC BY-SA 4.0")
IMG_50 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/2/2c/European_Parliament_Strasbourg_Hemicycle_-_Diliff.jpg",
    "Foto · Diliff / CC BY-SA 3.0")
IMG_51 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/d/d2/Belgique_-_Bruxelles_-_Schuman_-_Berlaymont_-_01.jpg",
    "Foto · EmDee / CC BY-SA 3.0")
IMG_52 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/5/5a/Government_buildings_by_Norrstr%C3%B6m_in_Stockholm_Sweden_01.jpg",
    "Foto · Sinikka Halme / CC BY-SA 4.0")

# ── 1. Tematiska nyckelord (specifika ämnen, inte "AI" i allmänhet) ──
KEYWORD_BUCKETS = [
    ("ipo", ["börs", "ipo", "s-1", "s1", " sec", "notering", "nasdaq", "nyse", "börsnotering"], [IMG_48]),
    ("energi", ["elpris", "elpriser", "kärnkraft", "kraftledning", "elnät", "solar", "nuclear", "renewable", "gigawatt"], [IMG_37, IMG_47, IMG_25]),
    ("compute", ["gpu", "grafikkort", "colossus", "superdator", "kluster", "serverhall", "datacenter", "data center", "h100", "b100", "trainium"], [IMG_46, IMG_45, IMG_10, IMG_11, IMG_7, IMG_49]),
    ("chip", ["halvledare", "semiconductor", "wafer", "euv", "asml", "tsmc", "chipfabrik"], [IMG_53]),
    ("rymd/musk", ["spacex", "raket", "falcon", "starship", "elon musk"], [IMG_44, IMG_43]),
    ("eu", ["bryssel", "kommissionen", "parlamentet", "gdpr", "ai-förordningen", "eu-kommissionen", "europeiska unionen"], [IMG_51, IMG_50]),
    ("sverige", ["sverige", "svensk", "stockholm", "svenska", "sveriges", "riksdag", "regeringen"], [IMG_52]),
    ("openai", ["openai", "sam altman", "altman", "chatgpt"], [IMG_41, IMG_42]),
    ("microsoft", ["microsoft", "nadella", "copilot", "azure"], [IMG_27, IMG_29]),
    ("google", ["google", "deepmind", "gemini", "pichai"], [IMG_39]),
]

# ── 2. Per källa ──
SOURCE_BUCKETS = {
    "openai": [IMG_41, IMG_42],
    "google-ai": [IMG_39],
    "xai": [IMG_43, IMG_44],
    "microsoft-ai": [IMG_27, IMG_29],
}


def _haystack(story: dict) -> str:
    b = story.get("fact_brief", {}) or {}
    parts = [str(story.get("title", "")), str(story.get("source_label", "")),
             str(b.get("summary", ""))]
    parts += [str(x) for x in (b.get("key_facts") or [])]
    return " ".join(parts).lower()


def pick_specific(story: dict, used: set) -> tuple[str, str] | None:
    """Välj (url, credit) vid SPECIFIK träff (tema/källa), annars None."""
    hay = _haystack(story)

    def _try_candidates(cands: list) -> tuple[str, str] | None:
        for c in cands:
            if c["url"] not in used:
                used.add(c["url"])
                return c["url"], c["credit"]
        return None

    for _name, kws, cands in KEYWORD_BUCKETS:
        if any(k in hay for k in kws):
            result = _try_candidates(cands)
            if result:
                return result

    return _try_candidates(SOURCE_BUCKETS.get(story.get("source_id", ""), []))
