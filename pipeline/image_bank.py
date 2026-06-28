#!/usr/bin/env python3
"""
AI-Bladet — Redaktionell bildbank (utökad v2)
==============================================
Kurerade, fria pressfoton (Wikimedia Commons) som väljs AUTOMATISKT.
Byggd ut 2026-06-28 med 54 bilder i rotation.

Val: 1) temanyckelord 2) källa 3) kategori 4) default
Alla URLer GET-verifierade.
"""


def _c(url, credit):
    return {"url": url, "credit": credit}


IMG_0 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/%28infogr%C3%A1fico%29_INTELLIGENCE_FUNNEL_-_Transforma%C3%A7%C3%A3o_de_dados_em_intelig%C3%AAncia.png/1280px-%28infogr%C3%A1fico%29_INTELLIGENCE_FUNNEL_-_Transforma%C3%A7%C3%A3o_de_dados_em_intelig%C3%AAncia.png",
    "Foto · Cappra.cc / CC BY-SA 4.0")
IMG_1 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/9/92/0_GTzatEUd4cICPVub.png/1280px-0_GTzatEUd4cICPVub.png",
    "Foto · Andrew Ng / CC BY-SA 4.0")
IMG_2 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/1_gigawatt_space-based_AI_supercomputer.webp/1280px-1_gigawatt_space-based_AI_supercomputer.webp.png",
    "Foto · Wikideas1 / Public domain")
IMG_3 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/100mw_AI_orbital_super_computer.webp/1280px-100mw_AI_orbital_super_computer.webp.png",
    "Foto · Wikideas1 / Public domain")
IMG_4 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/f/fc/4fold3class.jpg",
    "Foto · Joan.domenech91 / CC BY-SA 3.0")
IMG_5 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/0/02/A_hybrid_deep_learning_approach_for_medical_relation_extraction.pdf/page1-960px-A_hybrid_deep_learning_approach_for_medical_relation_extraction.pdf.jpg",
    "Foto · Veera Raghavendra Chikka, Kamalakar Karlapalem / Public domain")
IMG_6 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/A.I.CODED_-_Copy.webp/1280px-A.I.CODED_-_Copy.webp.png",
    "Foto · NASA / Public domain")
IMG_7 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a0/5_Pionen_Data_Centre.tif/lossy-page1-1280px-5_Pionen_Data_Centre.tif.jpg",
    "Foto · Simon Klose / CC BY 3.0")
IMG_8 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7d/8B1A0797.jpg/1280px-8B1A0797.jpg",
    "Foto · Virtuo Doc / CC BY-SA 4.0")
IMG_9 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/96pTAB_XL.jpg/1280px-96pTAB_XL.jpg",
    "Foto · Jellyfishz / CC BY-SA 4.0")
IMG_10 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/9/9e/Abudhabi_data_center.jpg",
    "Foto · Gulfdatahub / CC BY-SA 4.0")
IMG_11 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/5/51/Aerial-utah-data-center.jpg",
    "Foto · حمزة مستقيم / CC BY-SA 4.0")
IMG_12 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cf/Alm%C3%A1sf%C3%BCzit%C5%91i_Timf%C3%B6ldgy%C3%A1r%2C_%C3%A9p%C3%BClet15%2C_74.jpg/1280px-Alm%C3%A1sf%C3%BCzit%C5%91i_Timf%C3%B6ldgy%C3%A1r%2C_%C3%A9p%C3%BClet15%2C_74.jpg",
    "Foto · Random photos 1989 / CC BY-SA 4.0")
IMG_13 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b4/%22Disk_hacker%22_or_%22disk_doubler%22.jpg/1280px-%22Disk_hacker%22_or_%22disk_doubler%22.jpg",
    "Foto · Oz1sej / CC BY-SA 4.0")
IMG_14 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/6/67/1983-albert-apple-clone-photo.jpg/1280px-1983-albert-apple-clone-photo.jpg",
    "Foto · Michael Nadeau / Public domain")
IMG_15 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/1999-Router_Trame%2B_i960.jpg/1280px-1999-Router_Trame%2B_i960.jpg",
    "Foto · Josep M. Selga / CC BY-SA 4.0")
IMG_16 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9f/2_Intel_NUC.jpg/1280px-2_Intel_NUC.jpg",
    "Foto · Антон Пищулин / CC BY-SA 4.0")
IMG_17 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/8/83/1_Hopfield_Network_%E2%80%93_Initialization_of_the_Initial_State.jpg",
    "Foto · Tomasz59 / CC BY-SA 4.0")
IMG_18 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/b/bf/10.Suction_of_the_concentrate_samples_700ml_%2815589731280%29.jpg",
    "Foto · SuSanA Secretariat / CC BY 2.0")
IMG_19 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/d/da/%22The_Worker%22_and_%22The_Prize%22_Microscropes_-_DPLA_-_71b9c6cb3cf176fb60c70d4d8c160b57.jpg/1280px-%22The_Worker%22_and_%22The_Prize%22_Microscropes_-_DPLA_-_71b9c6cb3cf176fb60c70d4d8c160b57.jpg",
    "Foto · Philip Harris and Co / Public domain")
IMG_20 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/e/ef/6%E0%B0%B5_%E0%B0%AA%E0%B1%87%E0%B0%9C%E0%B1%80_%28%E0%B0%85%E0%B0%82%E0%B0%9F%E0%B1%81%E0%B0%B5%E0%B1%8D%E0%B0%AF%E0%B0%BE%E0%B0%A7%E0%B1%81%E0%B0%B2%E0%B1%81%29.jpg",
    "Foto · Inquisitive creature / CC BY-SA 4.0")
IMG_21 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/c/cc/614887532300d.jpg",
    "Foto · Dávid Hanko / CC BY-SA 4.0")
IMG_22 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/6/60/A_cavity_of_solar_radiation_receiver.jpg",
    "Foto · Solarturbine / CC BY-SA 3.0")
IMG_23 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/1/18/A_Heliostat_and_External_receiver.jpg",
    "Foto · Solarturbine / CC BY-SA 3.0")
IMG_24 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/0/08/A_tubular_collector_receiver.jpg",
    "Foto · Solarturbine / CC BY-SA 3.0")
IMG_25 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d8/AMP_Energy_Bhadla_Solar_Power_Plant_-_53699816551.jpg/1280px-AMP_Energy_Bhadla_Solar_Power_Plant_-_53699816551.jpg",
    "Foto · Sarvajanik Puralekh / CC BY-SA 2.0")
IMG_26 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/0/0e/Aula_Europa_Oficina_PE_BCN.jpg",
    "Foto · OPEP / Public domain")
IMG_27 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/7/78/MS-Exec-Nadella-Satya-2017-08-31-22_%28cropped%29.jpg/1280px-MS-Exec-Nadella-Satya-2017-08-31-22_%28cropped%29.jpg",
    "Foto · Brian Smale and Microsoft / CC BY-SA 4.0")
IMG_28 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/Satya_Nadella%2C_CEO_of_Microsoft%2C_with_former_CEOs_Bill_Gates%2C_and_Steve_Ballmer.jpg/1280px-Satya_Nadella%2C_CEO_of_Microsoft%2C_with_former_CEOs_Bill_Gates%2C_and_Steve_Ballmer.jpg",
    "Foto · Briansmale / CC BY-SA 4.0")
IMG_29 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6c/Satya_Nadella.jpg/1280px-Satya_Nadella.jpg",
    "Foto · OFFICIAL LEWEB PHOTOS / CC BY 2.0")
IMG_30 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/1/16/Jokowi_and_Sundar_Pichai_Googleplex.jpg",
    "Foto · Consulate General of Indonesia in San Francisco / Public domain")
IMG_31 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/7/7b/Mateusz_Morawiecki_spotka%C5%82_si%C4%99_z_CEO_Google_Sundar_Pichai_w_KPRM_%282022.03.29%29_01_%28cropped%29.jpg",
    "Foto · Krystian Maj / CC BY 3.0 pl")
IMG_32 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8f/Mateusz_Morawiecki_spotka%C5%82_si%C4%99_z_CEO_Google_Sundar_Pichai_w_KPRM_%282022.03.29%29_01.jpg/1280px-Mateusz_Morawiecki_spotka%C5%82_si%C4%99_z_CEO_Google_Sundar_Pichai_w_KPRM_%282022.03.29%29_01.jpg",
    "Foto · Krystian Maj / CC BY 3.0 pl")
IMG_33 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/Mateusz_Morawiecki_spotka%C5%82_si%C4%99_z_CEO_Google_Sundar_Pichai_w_KPRM_%282022.03.29%29_02.jpg/1280px-Mateusz_Morawiecki_spotka%C5%82_si%C4%99_z_CEO_Google_Sundar_Pichai_w_KPRM_%282022.03.29%29_02.jpg",
    "Foto · Krystian Maj / CC BY 3.0 pl")
IMG_34 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/5/52/Mateusz_Morawiecki_spotka%C5%82_si%C4%99_z_CEO_Google_Sundar_Pichai_w_KPRM_%282022.03.29%29_03.jpg/1280px-Mateusz_Morawiecki_spotka%C5%82_si%C4%99_z_CEO_Google_Sundar_Pichai_w_KPRM_%282022.03.29%29_03.jpg",
    "Foto · Krystian Maj / CC BY 3.0 pl")
IMG_35 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/Mateusz_Morawiecki_spotka%C5%82_si%C4%99_z_CEO_Google_Sundar_Pichai_w_KPRM_%282022.03.29%29_04.jpg/1280px-Mateusz_Morawiecki_spotka%C5%82_si%C4%99_z_CEO_Google_Sundar_Pichai_w_KPRM_%282022.03.29%29_04.jpg",
    "Foto · Krystian Maj / CC BY 3.0 pl")
IMG_36 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/5/57/Ha-invest.JPG/330px-Ha-invest.JPG",
    "Foto · Jorgbru / CC BY-SA 3.0")
IMG_37 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Barseback_Nuclear_Power_Plant.jpg/1280px-Barseback_Nuclear_Power_Plant.jpg",
    "Foto · Vitold Muratov / CC BY-SA 4.0")
IMG_38 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/8/8b/Bilan_GES_fili%C3%A8res_energ%C3%A9tiques.jpg",
    "Foto · Pigmalyon / CC BY-SA 4.0")
IMG_39 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Google_Headquarters_in_Ireland_Building_Sign.jpg/1280px-Google_Headquarters_in_Ireland_Building_Sign.jpg",
    "Foto · OutreachPete / CC BY 2.0")
IMG_40 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/Google_Headquarters_in_Ireland_Building_Front_Entrance.jpg/1280px-Google_Headquarters_in_Ireland_Building_Front_Entrance.jpg",
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
IMG_45 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/BalticServers_data_center.jpg/1280px-BalticServers_data_center.jpg",
    "Foto · BalticServers.com / CC BY-SA 3.0")
IMG_46 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Data_Center_2_%28UNC%29.jpg/1280px-Data_Center_2_%28UNC%29.jpg",
    "Foto · Ana Las Heras / CC BY-SA 4.0")
IMG_47 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f0/Power_lines_during_Blue_Hour_BW.jpg/1280px-Power_lines_during_Blue_Hour_BW.jpg",
    "Foto · PumpkinSky / CC BY-SA 3.0")
IMG_48 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/2/23/Trading_Floor_at_the_New_York_Stock_Exchange.jpg",
    "Foto · Scott Beale / CC BY-SA 4.0")
IMG_49 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/6/69/Wikimedia_Foundation_Servers-8055_35.jpg/1280px-Wikimedia_Foundation_Servers-8055_35.jpg",
    "Foto · Victor Grigas / CC BY-SA 3.0")
IMG_50 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/2/2c/European_Parliament_Strasbourg_Hemicycle_-_Diliff.jpg",
    "Foto · Diliff / CC BY-SA 3.0")
IMG_51 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/d/d2/Belgique_-_Bruxelles_-_Schuman_-_Berlaymont_-_01.jpg",
    "Foto · EmDee / CC BY-SA 3.0")
IMG_52 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/5/5a/Government_buildings_by_Norrstr%C3%B6m_in_Stockholm_Sweden_01.jpg",
    "Foto · Sinikka Halme / CC BY-SA 4.0")
IMG_53 = _c(
    "https://upload.wikimedia.org/wikipedia/commons/6/64/Intel_8742_153056995.jpg",
    "Foto · Ioan Sameli / CC BY-SA 2.0")

# ── 1. Tematiska nyckelord ──
KEYWORD_BUCKETS = [
    ("ipo", ["b\u00f6rs", "ipo", "s-1", "s1", " sec", "notering", "nasdaq", "nyse", "b\u00f6rsnotering"], [IMG_48]),
    ("energi", ["elpris", "elpriser", "energi", "energy", "kraftledning", "eln\u00e4t", "wind", "solar", "nuclear", "renewable"], [IMG_22, IMG_23, IMG_25, IMG_37, IMG_47]),
    ("compute", ["gpu", "grafikkort", "colossus", "200 000", "superdator", "kluster", "ber\u00e4kningskraft", "serverhall", "datacenter", "data center", "tr\u00e4nad", "tr\u00e4ning", "chip", "chipp", "processor", "h100", "b100", "trainium", "inferens", "hardware", "semiconductor", "wafer", "halvledare"], [IMG_2, IMG_3, IMG_10, IMG_13, IMG_15, IMG_16, IMG_45, IMG_46, IMG_49, IMG_53]),
    ("rymd/musk", ["spacex", "raket", "falcon", "rymd", "satellit", "elon musk", "elon", "xai"], [IMG_43, IMG_44]),
    ("eu", ["eu", "europeisk", "bryssel", "kommissionen", "parlamentet", "eu:s", "gdpr", "ai-f\u00f6rordningen", "eu-kommissionen", "europa", "europeiska unionen"], [IMG_26, IMG_42, IMG_50, IMG_51]),
    ("sverige", ["sverige", "svensk", "stockholm", "svenska", "sveriges", "riksdag", "kista"], [IMG_52]),
    ("reglering", ["domstol", "exportkontroll", "reglering", "lag", "f\u00f6rbud", "b\u00f6ter", "d\u00f6md", "regulator", "tillsyn", "myndighet", "beslut", "supreme", "court"], [IMG_26, IMG_42, IMG_50, IMG_51, IMG_52]),
    ("robot", ["robot", "robotarm", "automatisering", "humanoid", "autonom"], []),
    ("chip", ["halvledare", "semiconductor", "wafer", "euv", "asml", "tsmc", "fabrik", "tillverkning"], [IMG_16, IMG_53]),
    ("forskning", ["forskning", "research", "science", "vetenskap", "studie", "laboratorium", "mikroskop", "dna", "gen", "l\u00e4kemedel", "drug", "klinisk", "medicine"], [IMG_5, IMG_19]),
    ("openai", ["openai", "sam altman", "altman", "chatgpt", "gpt-", "gpt5", "o1", "o3"], [IMG_41, IMG_42]),
    ("ai_ml", ["artificial intelligence", "machine learning", "neural", "deep learning", "llm", "ai", "modell", "tr\u00e4na", "tr\u00e4ningsdata", "parameters", "transformer"], [IMG_0, IMG_2, IMG_3, IMG_5, IMG_17, IMG_30, IMG_31, IMG_32, IMG_33, IMG_34, IMG_35, IMG_42, IMG_44]),
]

# ── 2. Per källa ──
SOURCE_BUCKETS = {
    "openai": [IMG_41, IMG_42],
    "google-ai": [IMG_30, IMG_31, IMG_32, IMG_33, IMG_34, IMG_35, IMG_39, IMG_40],
    "xai": [IMG_43, IMG_44],
    "microsoft-ai": [IMG_27, IMG_28, IMG_29],
}

# ── 3. Kategori-fallback ──
CATEGORY_BUCKETS = {
    "Företag": [IMG_41, IMG_35, IMG_27, IMG_52, IMG_28, IMG_30, IMG_31, IMG_44, IMG_33, IMG_34, IMG_39, IMG_40, IMG_42, IMG_32, IMG_48, IMG_43, IMG_29],
    "Modeller": [IMG_30, IMG_49, IMG_10, IMG_42, IMG_53, IMG_3, IMG_0, IMG_33, IMG_2, IMG_15, IMG_46, IMG_17, IMG_5, IMG_34, IMG_32, IMG_16, IMG_35, IMG_31, IMG_44, IMG_13, IMG_45],
    "Säkerhet": [IMG_52, IMG_51, IMG_26, IMG_42, IMG_50],
    "Forskning": [IMG_5, IMG_19],
    "Politik": [IMG_52, IMG_51, IMG_26, IMG_42, IMG_50],
    "Verktyg": [IMG_3, IMG_49, IMG_53, IMG_15, IMG_46, IMG_2, IMG_13, IMG_10, IMG_45, IMG_16],
    "Energi": [IMG_25, IMG_23, IMG_47, IMG_22, IMG_37],
    "default": [IMG_30, IMG_49, IMG_10, IMG_42, IMG_53, IMG_3, IMG_0, IMG_33, IMG_19, IMG_2, IMG_15, IMG_46, IMG_17, IMG_5, IMG_34, IMG_32, IMG_16, IMG_35, IMG_31, IMG_44, IMG_13, IMG_45],
}


def _haystack(story: dict) -> str:
    b = story.get("fact_brief", {}) or {}
    parts = [str(story.get("title", "")), str(story.get("source_label", "")),
             str(story.get("category", "")), str(b.get("summary", ""))]
    parts += [str(x) for x in (b.get("key_facts") or [])]
    return " ".join(parts).lower()


def pick(story: dict, used: set) -> tuple[str, str]:
    """Välj (url, credit) för en story."""
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
            break

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

    # 5. Allt använt — tillåt repris
    c = CATEGORY_BUCKETS["default"][0]
    used.add(c["url"])
    return c["url"], c["credit"]
