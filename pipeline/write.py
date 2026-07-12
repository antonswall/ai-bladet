#!/usr/bin/env python3
"""
AI-Bladet — Skrivning (Pipeline Steg 6)
==========================================
Claude Sonnet 4.6 via OpenRouter skriver veckans utgåva.

Input:  output/images/{YYYY-WW}.json
Output: content/{YYYY-WW}.md (direkt till ~/ai-bladet/content/)
"""

import json
import os
import re
import sys
from datetime import datetime, timezone, date, timedelta
from pathlib import Path
from typing import Optional

import requests
import yaml

# ─── Config ───────────────────────────────────────────────────────────────────

PIPELINE_DIR = Path(__file__).parent
INPUT_DIR = PIPELINE_DIR / "output" / "images"
CONTENT_DIR = Path.home() / "ai-bladet" / "content"

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
SONNET_MODEL = "anthropic/claude-sonnet-4.6"

MAX_STORIES = 10            # max stories att skicka till Claude
MAX_BRIEFS = 8              # max briefs för KORTNYTT-sektionen
MAX_INPUT_CHARS = 4000      # max tecken per story i prompten
MIN_STORY_WORDS = 200       # måltext per story — valideringen underkänner kortare
MAX_OUTPUT_TOKENS = 8000    # 4000 var för snålt: 5 stories à 250 svenska ord
                            # (~2 tokens/ord) + lead + briefs slog i taket och
                            # pressade Sonnet att skriva 150-ordsartiklar


# ─── OpenRouter helper ───────────────────────────────────────────────────────


def _get_openrouter_key() -> Optional[str]:
    key = os.getenv("OPENROUTER_API_KEY", "")
    if key:
        return key
    env_path = Path.home() / ".hermes" / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("OPENROUTER_API_KEY="):
                k = line.split("=", 1)[1].strip()
                if k:
                    return k
    return None


def sonnet_call(prompt: str, system: str = None,
                max_tokens: int = MAX_OUTPUT_TOKENS) -> Optional[str]:
    """Anropa Claude Sonnet 4.6 via OpenRouter."""
    key = _get_openrouter_key()
    if not key:
        raise ValueError("OPENROUTER_API_KEY saknas")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        r = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://aibladet.se",
                "X-Title": "AI-Bladet",
            },
            json={
                "model": SONNET_MODEL,
                "messages": messages,
                "temperature": 0.4,
                "max_tokens": max_tokens,
            },
            timeout=120,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"  ⚠️  OpenRouter/Sonnet error: {e}", file=sys.stderr)
        if hasattr(e, 'response') and e.response is not None:
            print(f"     Response: {e.response.text[:300]}", file=sys.stderr)
        return None


# ─── Prompt building ─────────────────────────────────────────────────────────


SYSTEM_PROMPT = """Du är chefredaktör för AI-Bladet, en svensk nyhetstidning om AI som utkommer varje söndag.

Din röst: ledig men trovärdig — tabloid i energi, sansad i sak. Tänk DN/SvD möter tech-blogg.
Inga uppmaningar till läsaren, ingen "i den här artikeln", inga emojis, inget marknadsföringsspråk.
Svenska, genomgående. Varje huvudstory skrivs på 200-300 ord enligt strukturkravet (regel 10).

Läsaren är en person som BYGGER med AI dagligen. Frågan varje utgåva besvarar:
"Vad påverkar min AI-vardag den här veckan?"

SEGMENTSTRUKTUR — varje utgåva har EXAKT dessa tre segment, i EXAKT denna ordning:

1. VECKANS VERKTYG (lead + 1-3 stories, segment: "verktyg")
   Modeller, releaser, open source-verktyg — det läsaren faktiskt bygger med.
   Exempel: Claude/GPT/Gemini/Grok/DeepSeek/Hermes/Copilot/nya verktyg och releaser.
   Leaden är ALLTID en verktygsstory (regel 18). Segmentet har alltid minst leaden.

2. BRANSCH I KORTHET (2-4 briefs i briefs_bransch, max 1 full story med segment: "bransch")
   Politik, reglering, förvärv, datacenter, kapitalrundor.
   Varje bransch-brief OCH bransch-story avslutas med "Vad betyder det för dig:"
   följt av en konkret konsekvensmening för AI-byggare (regel 19).
   Kan du inte skriva den meningen trovärdigt utan att hitta på — stryk storyn.

3. VÄRT ATT VETA (0-3 briefs i briefs_vart_att_veta)
   Forskning, metod, papers. En rad per item. Bara när något faktiskt förtjänar plats.
   Tomma veckor: utelämna listan helt — ett tomt segment är bättre än utfyllnad.

REDAKTIONELLA REGLER — inga undantag:

0. ANTI-HALLUCINATION — VIKTIGASTE REGELN
   OM DET INTE FINNS I RESEARCH: SKRIV DET INTE. PERIOD.
   Inga påståenden om företag, produkter, siffror eller händelser som inte
   finns i research-briefsen. Hellre ett tråkigt men korrekt nummer än ett
   engagerande men påhittat. Lead, title och summary är extra kritiska —
   de exponeras mest och ska vara 100% verifierbara mot research.

1. DATERINGSKRAV
   Huvudsektioner: endast utveckling från de senaste 7 dagarna.
   Äldre material får endast tas med om det finns en konkret NY händelse denna vecka som motiverar det.
   Varje story måste ha ett publiceringsdatum i research. Kontrollera det.

2. INGA DUBLETTER
   "Veckans största" får INTE vara samma story som en sektion längre ner.
   Antingen: slå ihop till en längre artikel, eller gör toppen till en ren teaser som leder ner.

3. ATTRIBUERA ALLTID PRESTANDASIFFROR
   Alla prestandasiffror från en modellleverantör ("4x snabbare", "6x effektivitet")
   ska attribueras i rubrik eller första mening: "enligt Google", "xAI uppger".
   Aldrig en leverantörs marknadsföringssiffra som blank sanning.

4. KVALITATIVA SKIFTEN > INKREMENTELLA SLÄPP
   Om research innehåller ett kvalitativt skifte (t.ex. AI som går från diagnos → behandling),
   lyft det till egen sektion. Prioritera före inkrementella modellsläpp.
   Kortnytt är för notiser, inte för paradigmskiften.

5. SVENSK/EU-VINKEL
   Hitta minst en svensk eller EU-vinkel per nummer.
   Detta är det som differentierar AI-Bladet från engelska AI-nyhetsbrev.
   Exempel: svensk datacenterdebatt, EU-reglering, svenska AI-bolag i research.

6. TEASERN FÅR INTE LJUGA
   Lead-ingressen måste spegla veckans faktiska nyhet — inte en gammal story
   som om den vore ny. Läs datumen i research och kolla om storyn är aktuell.

7. KÄLLHÄNVISNING
   Varje påstående ska gå att spåra till en källa i research.
   Hitta inte på siffror, datum eller citat som inte finns där.

8. FALLBACK FÖR TUNNA VECKOR
   Om de senaste 7 dagarna är nyhetsfattiga och du har för få stories:
   Skapa en "Bakgrund/Djupdykning"-sektion. Där får äldre material finnas,
   men det måste TYDLIGT märkas som bakgrund/analys — inte presenteras som nyhet.
   Om färre än 4 stories har fyllig research (>500 tecken i brief):
   kör ENDAST 2-3 stories + 3-5 briefs. En kort tidning är bättre än en
   påhittad tidning. Du får ALDRIG fylla ut med fabricerat innehåll.

9. INGRESS PER STORY (framsidan)
   Varje sekundär story ska ha en fristående ingress på 40-60 ord som besvarar:
   vad hände, och varför det spelar roll. Ingressen är en egen, säljande
   sammanfattning (dek) — INTE de första meningarna av brödtexten ordagrant.
   Den ska kunna stå ensam på framsidan och få läsaren att vilja läsa vidare.

10. LÄNGD & STRUKTUR PÅ BRÖDTEXTEN
   Varje stories.body ska vara 150-250 ord, i markdown med stycken (blankrad mellan),
   och följa denna struktur:
   1) Vad hände — fakta och konkreta detaljer (~60 ord).
   2) Varför det spelar roll / kontext — sätt nyheten i sitt sammanhang (~80 ord).
   3) Vad det betyder för Sverige/EU — ENDAST där det finns en genuin koppling i
      research (~40 ord). Tvinga aldrig in en svensk vinkel som inte finns;
      hoppa över del 3 hellre än att hitta på.
   Fyll inte ut med upprepning — varje mening ska bära ny information från research.
   GÅR DET INTE ATT NÅ 150 ORD UTAN ATT HITTA PÅ: skriv en kortare artikel och
   komplettera med en extra brief — bättre kort och korrekt än lång och osann.

11. AI-BLADETS ANALYS (endast toppstoryn)
   Toppstoryn (lead) avslutas med en kort analys på 50-70 ord, märkt "AI-Bladets analys".
   Den ska kontextualisera och tolka veckans största nyhet — vad den betyder i ett
   större sammanhang — inte återupprepa ingressen och inte spå framtiden lösryckt.
   Allt ska gå att grunda i research (regel 6 och 7 gäller fullt ut). Neutral
   redaktionell röst, ingen personlig signatur, ingen brasklapp.

12. BILDER
   Varje story (och lead) som har en Bild-URL i research ska få ett image-fält
   med EXAKT samma URL — kopiera tecken för tecken, hitta aldrig på eller ändra en
   URL. Saknar storyn bild: utelämna image-raden helt (framsidan visar då en
   snygg fallback). Matcha bilden till rätt story — blanda inte ihop dem.
   Kopiera även Byline ordagrant till credit — det är fotografens/källans
   attribution och licens och får aldrig ändras eller hittas på.

13. FYNDIGA RUBRIKER — MEN ALDRIG PÅ BEKOSTNAD AV FAKTA
   Rubriker får vara säljande och tabloida, men varje påstående i en rubrik måste
   gå att belägga i research (regel 7 gäller fullt ut). Attribuera leverantörers
   prestandasiffror även i rubrik (regel 3): "Google: fyra gånger snabbare", inte
   "fyra gånger snabbare" som blank sanning. Överdriv aldrig, lova aldrig framtid.

14. CITAT — ENDAST ÄKTA, ALDRIG PÅHITTADE
   Lägg gärna in ett pull-citat "då och då" via quote-fältet, MEN:
   - Citatet måste finnas ordagrant i storyns Citat-lista i research.
   - Översätt troget till svenska om originalet är engelskt — ändra inte innebörden.
   - speaker ska vara EXAKT den talare research anger (ofta en organisation som
     "OpenAI" eller "Google"). Tillskriv ALDRIG ett citat en namngiven person
     (t.ex. en vd) om inte research uttryckligen namnger den personen.
   - Har storyn inget citat i research: utelämna quote-blocket helt.

15. YAML-FORMATERING FÖR FLERRADIG TEXT
   Använd ALLTID YAML literal block scalar (|) för fält som kan innehålla
   flera stycken: lead.analysis, stories[].body.
   Exempel:
     body: |
       Första stycket följer direkt efter |.

       Andra stycket — blankrad mellan stycken.

       Tredje stycket.
   Indentera varje rad i blocket med SAMMA antal mellanslag (6 steg för
   stories.body, 4 steg för lead.analysis). En blankrad mellan stycken
   ska vara HELT tom (ingen indent på blankraden).
   För ENRADIGA fält (kicker, headline, ingress, title, summary, image,
   credit) använd vanliga double-quoted strings: headline: "Rubrik här".
   För quote-fältet: använd YAML-mapping med text: och speaker: som är
   enradiga double-quoted strings.

16. ALDRIG CODE BLOCKS
   ALDRIG någonsin wrappa YAML:en i ```yaml eller ``` code blocks.
   Hela svaret ska vara REN YAML-frontmatter + markdown-body.
   ```yaml ``` förstör parsern. Utelämna alla markdown-formatterade
   code block wrappers. Din output börjar direkt med "---" och slutar
   med brödtext efter den avslutande "---".

17. DIVERSIFIERING — INTE ETT FÖRETAG PER NUMMER
   Om fler än 2 av de 10 skickade storiesna handlar om samma företag
   (xAI, OpenAI, Google, etc): välj MAX 2 av dem. Fyll resten av
   numret med stories från ANDRA företag/ämnen, även om de har lägre
   poäng. Ett varierat nyhetsbrev är bättre än ett som bara rapporterar
   om ett företag. Lead-artikeln får vara om det dominerande företaget,
   men de sekundära storiesna måste komma från andra ämnen.
   Har du bara 3-4 stories totalt i research: välj max 1 per företag.

18. LEAD ALLTID OM VERKTYG
   Leaden är ALLTID en story ur segmentet Veckans verktyg (kategori Modeller
   eller Verktyg). En branschnyhet (politik/reglering/förvärv) får ALDRIG vara
   lead om den inte har direkt, konkret påverkan på AI-verktyg som läsaren
   använder — och då skrivs den som verktygsstory med den påverkan i fokus.
   Metaforskning och policyanalys är aldrig lead, oavsett score. Finns ingen
   stark verktygsstory: ta veckans mest konkreta modell/release och skriv den
   rakt — en liten men verklig verktygsnyhet slår en stor abstrakt bransch-story.

19. "VAD BETYDER DET FÖR DIG" — OBLIGATORISK KONSEKVENSRAD
   Varje bransch-story (segment: "bransch") avslutar sin body med ett eget
   stycke som börjar exakt "Vad betyder det för dig:" följt av en konkret
   konsekvensmening för någon som bygger med AI. Varje brief i briefs_bransch
   avslutas med samma fras och en konsekvenssats. Raden måste vara grundad i
   research (regel 0 och 7 gäller) — kan du inte skriva den trovärdigt,
   degradera storyn till brief eller stryk den helt."""

def build_prompt(stories: list[dict], week: str, year: int,
                 published_date: str) -> str:
    """Bygg prompten för Sonnet med alla researchade stories."""
    now = datetime.now(timezone.utc)
    week_num = int(week.split("-")[1])
    date_obj = now - timedelta(days=now.weekday() + 1)  # senaste söndag
    date_str = date_obj.strftime("%Y-%m-%d")

    # Bygg context för varje story
    stories_text = ""
    for i, s in enumerate(stories):
        b = s.get("fact_brief", {})
        title = s.get("title", "Untitled")
        score = s.get("score", 0)
        category = s.get("category", "Övrigt")
        summary = b.get("summary", "")[:300]
        facts = b.get("key_facts", [])
        numbers = b.get("numbers", [])
        quotes = b.get("quotes", [])
        swedish = b.get("swedish_angle", "")
        lead = s.get("lead_potential", 0)
        source = s.get("source_label", "")
        image = s.get("image_url", "")
        credit = s.get("image_credit", "")

        actionable = s.get("actionable", s.get("ai_score", {}).get("actionable", False))
        # Markörer byggs utanför f-stringen — non-ASCII i f-string-uttryck
        # kraschar macOS Python 3.11 (se loggbok 2026-07-12)
        lead_mark = "[LEAD CANDIDATE]" if lead >= 4 else ""
        aktion_mark = "[AKTIONABEL — ändrar AI-byggares vardag denna vecka]" if actionable else ""
        stories_text += f"""
## STORY {i+1} — Score: {score} | Kategori: {category}
{lead_mark}{aktion_mark}

Titel: {title}
Källa: {source}
Svensk vinkel: {swedish or 'Nej'}

Sammanfattning: {summary}

Nyckelfakta:
{chr(10).join(f'  • {f}' for f in facts[:5])}

Siffror:
{chr(10).join(f'  • {n.get("value", "")} — {n.get("context", "")}' for n in numbers[:3])}

Citat:
{chr(10).join(f'  "{q.get("text", "")}" — {q.get("speaker", "")}' for q in quotes[:2])}

Bild (kopiera URL:en EXAKT om du väljer denna story): {image if image else 'Ingen bild'}
Byline (kopiera EXAKT till credit-fältet): {credit if credit else 'Ingen'}
"""
        stories_text += "\n---\n"

    prompt = f"""Skriv veckans utgåva av AI-Bladet.

KONTEXT:
- year: {year}
- week: {week_num}
- date: {date_str}

RESEARCHADE ARTIKLAR (scores från DeepSeek V4 Pro):

{stories_text}

INSTRUKTIONER:

1. Välj lead-story: veckans viktigaste VERKTYGSNYHET (kategori Modeller/Verktyg).
   LEAD- och AKTIONABEL-märkta stories är kandidater. Regel 18 gäller — politik,
   förvärv och forskning kan ALDRIG vara lead.

2. Välj 1-3 ytterligare verktygsstories (segment: "verktyg"). Rangordna efter
   hur mycket de påverkar läsarens AI-vardag.

3. Välj max 1 full bransch-story (segment: "bransch") och 2-4 bransch-briefs
   (briefs_bransch). Bransch = politik, reglering, förvärv, datacenter.
   ALLA avslutas med "Vad betyder det för dig:" + konsekvensmening (regel 19).

4. Välj 0-3 forsknings-/metodbriefs (briefs_vart_att_veta). Bara det som
   faktiskt förtjänar plats — utelämna listan hellre än fyll ut.

5. Skriv i svensk ledig tidningston. Faktabaserat - hitta inte på något som inte finns i research.

6. OUTPUT - exakt detta format, inget annat före eller efter.
   OBS: För flerradiga fält (analysis, body) använd YAML literal block scalar (|).
   För enradiga fält använd double-quoted strings ("...").

---
year: {year}
week: {week_num:02d}
date: {date_str}
title: "Redaktionell rubrik för HELA utgåvan (max 70 tecken)"
summary: "En mening som säljer veckan (max 140 tecken)"
lead:
  kicker: "KATEGORI (Modeller eller Verktyg — segmentheadern visar redan 'Veckans verktyg')"
  segment: "verktyg"
  headline: "Veckans största verktygs-/modellnyhets rubrik (inte exakt samma som research-titeln)"
  ingress: "2-3 meningar som säljer storyn"
  analysis: |
    AI-Bladets analys: 50-70 ord som kontextualiserar toppstoryn, grundad i research (regel 11).
    OBS: indentera med 4 mellanslag. Blankrader mellan stycken ska vara HELT tomma.
  image: "Klistra in Bild-URL:en EXAKT från den valda lead-storyn. Utelämna raden helt om storyn saknar bild."
  credit: "Klistra in Byline EXAKT från den valda lead-storyn (t.ex. 'Foto · X / CC BY 2.0'). Utelämna om bild saknas."
stories:
  - segment: "verktyg"
    kicker: "KATEGORI (Modeller eller Verktyg för segment verktyg)"
    headline: "Rubrik - gärna fyndig/säljande, men 100% förankrad i research (regel 7 + 13)"
    ingress: "40-60 ord: vad hände + varför det spelar roll. Egen formulering, INTE de första meningarna av body."
    image: "Klistra in Bild-URL:en EXAKT från den valda storyn. Utelämna raden helt om storyn saknar bild."
    credit: "Klistra in Byline EXAKT från den valda storyn. Utelämna om bild saknas."
    # quote ska vara ett block med text + speaker, ordagrant från research (regel 14):
    #   quote:
    #     text: "Citatet, troget översatt till svenska om originalet är engelskt"
    #     speaker: "Exakt talare ur research, t.ex. OpenAI (aldrig en påhittad person)"
    body: |
      Första stycket - vad hände, fakta och detaljer (~80 ord). Indentera med 6 mellanslag.

      Andra stycket - varför det spelar roll, kontext (~100 ord). Blankrad mellan stycken.

      Tredje stycket - Sverige/EU-vinkel ENDAST om research stöder det (~50 ord).
  - segment: "bransch"
    kicker: "KATEGORI (Politik, Företag, Säkerhet, Sverige)"
    headline: "Max EN bransch-story per nummer — utelämna blocket om ingen förtjänar full story"
    ingress: "40-60 ord"
    body: |
      Vad hände + kontext enligt regel 10.

      Vad betyder det för dig: konkret konsekvensmening för AI-byggare (regel 19). Sista stycket.
briefs_bransch:
  - "Branschnotis 2-4 meningar. Vad betyder det för dig: konkret konsekvens för AI-byggare."
  - "Ännu en branschnotis. Vad betyder det för dig: konsekvensen."
briefs_vart_att_veta:
  - "Forsknings-/metodnotis, en rad. Utelämna hela listan om inget förtjänar plats."
categories: [Kategori1, Kategori2]
sources: {len(stories)}
---

Segmentordningen i stories-listan: ALLA verktygsstories först, sedan max en
bransch-story. Varje stories.body skrivs på 200-300 ord enligt strukturen i
regel 10 (vad hände / varför det spelar roll / Sverige-EU där relevant).
lead.ingress + varje story.ingress hålls korta (2-3 meningar resp. 40-60 ord)."""

    return prompt


# ─── Parse output ─────────────────────────────────────────────────────────────


def parse_sonnet_output(text: str) -> str:
    """Verifiera att Sonnet producerade korrekt frontmatter + markdown."""
    if not text:
        raise ValueError("Sonnet returnerade tomt svar")

    # Strippa code block wrappers (```yaml / ```) som Sonnet ibland lägger till
    text = re.sub(r'^```(?:yaml)?\s*\n', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n```\s*$', '', text)
    text = text.strip()

    # Kolla att frontmatter finns
    if not text.startswith("---"):
        # Försök hitta frontmatter
        fm_start = text.find("---")
        if fm_start >= 0:
            text = text[fm_start:]
        else:
            raise ValueError(f"Ingen YAML-frontmatter funnen i svar:\n{text[:300]}")

    # Kolla att alla obligatoriska fält finns
    required = ["year:", "week:", "date:", "title:", "summary:", "lead:", "stories:"]
    missing = [f for f in required if f not in text]
    if missing:
        print(f"  ⚠️  Varning: saknar fält: {missing}", file=sys.stderr)

    return text


# ─── Huvudfunktion ────────────────────────────────────────────────────────────


def write_issue(input_path: Path, output_path: Path, feedback: str = "") -> dict:
    """Generera veckans utgåva med Claude Sonnet 4.6.
    
    feedback: Om validering tidigare failat - skickas som extra instruktion
              till Sonnet så den kan korrigera specifika fel.
    """
    with open(input_path) as f:
        data = json.load(f)

    stories = data["stories"]
    week = data.get("meta", {}).get("week", "")
    attempt = " (rättning)" if feedback else ""
    print(f"✍️  Skriver AI-Bladet v.{week} med Claude Sonnet 4.6{attempt}\n")

    # Rensa titlar (ta bort body-konkatinering)
    for s in stories:
        t = s.get("title", "")
        # Klipp vid lowercase→UPPERCASE boundary om titeln är för lång
        words = re.split(r"(?<=[a-z])(?=[A-Z])", t, maxsplit=1)
        if len(words) > 1 and len(words[0]) < 100:
            s["_clean_title"] = words[0].strip()
        else:
            s["_clean_title"] = t[:100].strip()

    # Extrahera år från veckosträng
    year = int(week.split("-")[0]) if "-" in week else 2026

    # Bygg prompt
    top_stories = stories[:MAX_STORIES]
    prompt = build_prompt(top_stories, week, year, "")

    # Om feedback finns — lägg till som extra instruktion
    if feedback:
        prompt += f"\n\n⚠️  TIDIGARE VALIDERINGSFEL ATT ÅTGÄRDA:\n{feedback}\n"
        prompt += "Skriv om utgåvan och åtgärda dessa specifika fel. Behåll allt annat som är korrekt."

    print(f"  🤖 Skickar {len(top_stories)} stories till Sonnet...")
    print(f"     (prompt: ~{len(prompt)//1000}k tokens)")

    response = sonnet_call(prompt, SYSTEM_PROMPT)

    if not response:
        print("\n❌ Sonnet svarade inte. Försök igen?")
        return {"success": False, "error": "No response"}

    # Verifiera och rensa
    try:
        output = parse_sonnet_output(response)
    except ValueError as e:
        print(f"\n❌ Parse-fel: {e}")
        print(f"\nRådata från Sonnet (första 500 tecken):\n{response[:500]}")
        return {"success": False, "error": str(e)}

    # Skriv till content/
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output)
        f.write("\n")

    # Räkna ord
    word_count = len(output.split())
    stories_count = output.count("headline:") - 1  # minus lead
    briefs_count = 0
    # Räkna briefs i alla listor (briefs_bransch, briefs_vart_att_veta, legacy briefs)
    for m in re.finditer(r"^briefs(?:_bransch|_vart_att_veta)?:\n((?:\s+- .*\n)+)", output, re.MULTILINE):
        briefs_count += len(re.findall(r"^\s+- ", m.group(1), re.MULTILINE))

    print(f"\n{'─'*40}")
    print(f"📰 UTGÅVA SKRIVEN ✅")
    print(f"  Fil:        {output_path}")
    print(f"  Ord:        ~{word_count}")
    print(f"  Stories:    ~{stories_count}")
    print(f"  Briefs:     ~{briefs_count}")
    print(f"  Modell:     Claude Sonnet 4.6")
    print(f"{'─'*40}")

    return {
        "success": True,
        "path": str(output_path),
        "word_count": word_count,
        "stories": stories_count,
        "briefs": briefs_count,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AI-Bladet skrivning")
    parser.add_argument("input", nargs="?", help="Input JSON (images)")
    parser.add_argument("--output", "-o", help="Output path")
    parser.add_argument("--feedback", "-f", help="Validation feedback to inject (for retry)")
    args = parser.parse_args()

    if args.input:
        input_path = Path(args.input)
    else:
        images = sorted(INPUT_DIR.glob("*.json"))
        if not images:
            print("Inga bild-filer hittades. Kör images.py först.")
            sys.exit(1)
        input_path = images[-1]

    week = input_path.stem  # YYYY-WW
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = CONTENT_DIR / f"{week}.md"

    result = write_issue(input_path, output_path, feedback=getattr(args, 'feedback', '') or '')
    sys.exit(0 if result.get("success") else 1)
