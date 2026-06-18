# AI-Bladet — Content-pipeline: Analys & rekommendation

*Brainstorm av Claude Opus 4.8 — för Anton. Allt nedan är designat för $0/mån på Mac Mini (SearXNG + n8n + Cloudflare Pages).*

---

## 1. Bedömning av Antons 4-stegsprocess

Grundstrukturen är **rätt** och i rätt ordning. Insamling → filtrering → bild → renskrivning är den logiska kedjan, och dina instinkter ("inte för mycket text", "RÄTT bild, inte smetigt", lead-nyhet på förstasidan) är precis rätt redaktionella prioriteringar. Det är en *tidning* du bygger, inte en länkdump — den känslan ska genomsyra pipelinen.

Tre saker jag skulle justera:

**A) Lägg till ett steg 0 — Dedup & minne.**
Det enskilt största kvalitetsproblemet i en veckopipeline är inte att hitta nyheter — det är att inte återpublicera samma sak två veckor i rad, och att kunna säga "förra veckan rapporterade vi X, nu har det hänt Y". Du behöver ett persistent minne (en enkel `seen.json` / SQLite) med URL-hashar + titlar + embeddings för redan publicerade stories. Detta löser också din "färre än 10"-regel elegant: en återanvänd nyhet blir en *uppföljning* ("Förra veckans GPT-5-rykte — så här blev det"), inte en upprepning.

**B) Slå ihop "filtrering" och "validering" konceptuellt, men kör validering EFTER skrivning.**
Filtrering = "ska detta med?" (före skrivning). Validering = "stämmer det jag skrev?" (efter skrivning). De är olika steg vid olika tidpunkter. Antons lista har inte med validering alls i 4-stegsprocessen (den dyker bara upp i frågorna) — den måste in som ett explicit steg.

**C) Separera "research/sammanfattning per nyhet" från "renskrivning av tidningen".**
Det är två olika skrivuppgifter. Steg 1 bör producera en *strukturerad fakta-brief per nyhet* (vad, vem, när, källa, citat) redan vid insamling. Steg 4 förvandlar briefs → redaktionell text. Om du blandar ihop dem får du hallucinationer, för modellen "skriver snyggt" innan den har fakta på plats.

### Reviderad process (7 steg)

```
0. MINNE        Ladda seen-databas (URL-hashar + embeddings av tidigare stories)
1. INSAMLING    Hämta råa kandidater från alla källor → normaliserad kandidatlista
2. DEDUP        Filtrera bort redan publicerat + klustra dubbletter av samma story
3. FILTRERING   Poängsätt → välj topp 10–12 + 1 lead → fyll-på-regel om <10
4. RESEARCH     Per vald nyhet: hämta full källtext, extrahera fakta-brief + citat
5. BILD         Per artikel: välj/generera rätt bild enligt bildstrategin
6. SKRIVNING    Brief → redaktionell artikel + frontmatter (med inline-källor)
7. VALIDERING   Fact-check mot brief, länk-koll, dödar/flaggar osäkra påståenden
   → build.js → git push
```

n8n orkestrerar 0–7; AI-modellen anropas i 3 (poängsättning), 4 (extraktion), 6 (skrivning) och 7 (validering).

---

## 2. Konkreta källförslag

Filosofin: **RSS är ryggraden** (gratis, strukturerat, ingen scraping, inga rate limits). SearXNG är ditt *upptäckts- och kompletteringslager* för det RSS missar. Scraping bara för full källtext på utvalda artiklar.

### Lager 1 — RSS-flöden (primär ryggrad, ~80% av råmaterialet)

Företags-/labbkällor (förstahandskällor, högst trovärdighet):
| Källa | URL | Varför |
|---|---|---|
| OpenAI Blog | `https://openai.com/blog/rss.xml` | Förstahands produktnyheter |
| Google DeepMind | `https://deepmind.google/blog/rss.xml` | Forskning + modeller |
| Anthropic News | `https://www.anthropic.com/news` (RSS via SearXNG/scrape om ej native) | Claude-nyheter |
| Meta AI | `https://ai.meta.com/blog/rss/` | Llama m.m. |
| Hugging Face Blog | `https://huggingface.co/blog/feed.xml` | Open source-pulsen |
| Mistral | via SearXNG | EU-vinkel |

Nyhets-/branschmedia (kontext, urval, andrahandskällor):
| Källa | URL |
|---|---|
| TechCrunch AI | `https://techcrunch.com/category/artificial-intelligence/feed/` |
| The Verge AI | `https://www.theverge.com/rss/ai-artificial-intelligence/index.xml` |
| Ars Technica AI | `https://arstechnica.com/ai/feed/` |
| VentureBeat AI | `https://venturebeat.com/category/ai/feed/` |
| MIT Technology Review | `https://www.technologyreview.com/feed/` |
| The Decoder | `https://the-decoder.com/feed/` (ren AI-sajt, bra signal) |

Aggregatorer/community (för att fånga det som trendar):
| Källa | Metod |
|---|---|
| Hacker News (AI-filtrerat) | Algolia API: `https://hn.algolia.com/api/v1/search?query=AI&tags=story&numericFilters=points>100` — **gratis, inget nyckel, ger poäng & kommentarsantal = inbyggd prioriteringssignal** |
| r/LocalLLaMA, r/artificial | Reddit JSON: `https://www.reddit.com/r/LocalLLaMA/top.json?t=week` (gratis, sätt User-Agent) |
| arXiv cs.AI/cs.CL | `http://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=submittedDate` (gratis, för forskningstunga veckor) |
| GitHub Trending | scrape `github.com/trending` filtrerat på AI-repos (för verktygsnyheter) |

Svenska/nordiska källor (lokal relevans — en svensk AI-tidning bör ha minst 1–2 lokala vinklar/vecka):
- Ny Teknik, Breakit, DI Digital, Computer Sweden — RSS finns. SearXNG-sökning `AI Sverige` med `time_range=week` fångar resten. AI Sweden (organisationen) har nyhetsflöde.

### Lager 2 — SearXNG (komplettering & lucktäckning)

SearXNG kör du redan. Använd dess **JSON-API** (`?format=json`) i n8n. Tre roller:
1. **Lucktäckare** — om RSS gett <15 kandidater, kör tematiska sökningar: `"AI" after:<förra söndagen>`, `LLM release`, `AI regulation EU`, `OpenAI OR Anthropic OR Google AI`, med `time_range=week`.
2. **Svensk vinkel** — `artificiell intelligens Sverige`, `AI nyheter`.
3. **Verifieringssök** i valideringssteget (se §5).

> Tips: aktivera `news`-kategorin och Google News-motorn i SearXNG:s `settings.yml`. Google News via SearXNG är i praktiken en gratis nyhets-API utan nyckel — guld för det här projektet.

### Lager 3 — Full källtext (bara för de utvalda ~10)

När filtreringen valt nyheterna, hämta full artikeltext för fakta-extraktion. **Scrapa inte själv om du slipper** — kör artikeln genom en "reader":
- **Jina Reader**: `https://r.jina.ai/<URL>` → returnerar ren markdown. Gratis tier, inget nyckel för låg volym. Perfekt för 10 artiklar/vecka.
- Fallback: lokal scraping med readability/trafilatura (Python) i n8n via Execute Command-nod.
- Firecrawl-skillen du redan har installerad är overkill för 10 sidor/vecka men funkar som reserv för JS-tunga sidor.

**Sammanfattning av källstrategi:** ~15 RSS-flöden ger nästan alltid >30 råkandidater/vecka. SearXNG täcker luckor och svensk vinkel. HN/Reddit-poäng ger gratis popularitetssignal. Du kommer aldrig ha problem att hitta 10 — problemet blir att *välja bort*, vilket är precis vad en tidning ska göra.

---

## 3. Filtrerings- & prioriteringssystem

Ja, bygg ett **poängsystem** — men håll det enkelt och deterministiskt där det går, och låt AI bara göra det AI är bra på (bedöma relevans/läsvärde). Hybrid är bäst: regelbaserad förfiltrering + AI-bedömning på toppkandidaterna.

### Steg A — Billig regelbaserad pre-score (ingen AI, körs på alla kandidater)

```
score = 0
score += källvikt            # se tabell nedan (0–30)
score += färskhet            # publicerad senaste 7 dgr: +20, 7–14: +10, äldre: 0
score += popularitet         # HN-poäng/25 (cap 20), Reddit-upvotes/100 (cap 15)
score += antal_oberoende_källor_i_kluster * 8   # samma story i flera flöden = viktigt
score += kategori-bonus      # se nedan
score -= brus-straff         # "5 best AI tools", "sponsored", listicles, ren PR
```

**Källvikt (trovärdighet):**
| Nivå | Källor | Vikt |
|---|---|---|
| Förstahands | OpenAI/Anthropic/DeepMind/Meta/arXiv | 30 |
| Etablerad media | Ars Technica, MIT TR, The Verge, TechCrunch | 22 |
| Branschsajt | The Decoder, VentureBeat, HF blog | 16 |
| Community/aggregator | HN, Reddit | 10 (men popularitetspoäng kompenserar) |
| Okänd/blogg | övrigt | 5 |

**Kategori-vikter** (en tidning vill ha *spridning*, inte 10 modell-releases):
- Modell-/produktlansering: +10
- Forskningsgenombrott: +8
- Policy/reglering/juridik: +8
- Företag/affärer (förvärv, finansiering): +6
- Verktyg/open source: +6
- Etik/samhälle/debatt: +6
- Svensk/nordisk vinkel: **+12** (medveten boost — det är er nisch)

### Steg B — AI-bedömning på topp ~20

Skicka de ~20 högst rankade (titel + ingress + källa, INTE full text — spar tokens) till modellen med en strikt JSON-prompt:

```
För varje nyhet, betygsätt 1–10 på:
- nyhetsvärde (hur stort/oväntat?)
- läsvärde för en allmänbildad svensk AI-intresserad läsare
- "förstaside-potential" (skulle detta få någon att öppna tidningen?)
Returnera JSON: [{id, nyhetsvärde, läsvärde, lead_potential, kategori, en_menings_motivering}]
```

Slutpoäng = `0.5 * pre_score (normaliserad) + 0.5 * AI-score`. Detta gör systemet robust: regler fångar det mätbara, AI fångar redaktionell känsla.

### Steg C — Redaktionellt urval (regler ovanpå poäng)

- **Topp 10–12** efter slutpoäng går vidare.
- **Lead-nyhet** = högsta `lead_potential` (inte nödvändigtvis högsta totalpoäng — en stor men torr regleringsnyhet är inte en bra förstasida).
- **Diversifieringsregel:** max 3 nyheter per kategori i en utgåva. Hellre 1 bra forskningsnyhet än 5 modell-releases. Detta skyddar mot "för mycket av samma" → läsaren tappar inte fokus.
- **Längdbudget mot textmängd:** sätt en hård budget, t.ex. lead = 250–350 ord, 3–4 mellanstora = 150 ord, resten = 60–80 ords notiser. Antons "inte för mycket text" blir då en *strukturell* regel, inte en känsla. Tidningen får rytm: en huvudartikel, några i mellanformat, en notis-spalt.

### Fyll-på-regel (när <10 färska)

Prioritetsordning:
1. Sänk färskhetströskeln till 14 dagar.
2. Plocka en "fördjupning" — en evergreen/förklarande vinkel på något pågående (t.ex. "Vad är egentligen en reasoning-modell?").
3. **Uppföljning** ur seen-databasen: ta en story från förra veckan som fått utveckling. Markera tydligt som uppföljning. Detta är bättre redaktionellt än att skrapa botten på källistan.

---

## 4. Bildstrategi

Din instinkt "RÄTT bild, inte smetigt" är nyckeln. Det största misstaget vore att slänga in generiska AI-stockbilder (blå robothjärnor, glödande neuralnätverk) — det skriker "AI-slop" och dödar trovärdigheten direkt. Prioritetsordning per artikel:

**Nivå 1 — Officiell källbild (bäst, default).**
De flesta förstahandskällor har en OG-bild (`og:image` i metadatan). När du ändå hämtar full text, plocka `<meta property="og:image">`. För en OpenAI-release är *deras egen* hero-bild den rätta bilden. Detta löser ~60% av bilderna gratis och korrekt. Spara lokalt, kör genom `sharp` (Node) → beskär till thumbnail-format, komprimera till WebP.

> Notera upphovsrätt: OG-bilder är tänkta för delning, men för en publicerad tidning bör du (a) hålla dem små/thumbnail, (b) alltid länka till källan, (c) på sikt föredra nivå 2–3 för säkerhets skull. För v1 är källbild + tydlig attribution rimligt.

**Nivå 2 — Kuraterad stock via Unsplash/Pexels API (gratis nyckel).**
För nyheter utan bra källbild. **Men inte sökord som "AI"** → då får du sloppet. Bygg en mappning kategori → bra konkreta sökord:
- Reglering → "european parliament building", "courtroom", "gavel"
- Chip/hårdvara → "data center servers", "circuit board macro"
- Företag/affär → "stockholm office", "handshake business"
- Open source → "developer keyboard code"

Unsplash API: 50 req/h gratis, mer än nog. Pexels som backup. Cacha så samma bild inte återanvänds två veckor i rad (lägg i seen-db).

**Nivå 3 — AI-genererad (selektivt, för lead-nyheten).**
För förstasidan kan en distinkt, konsekvent illustration lyfta tidningen och ge varumärke. Gratisvägar: lokal Stable Diffusion / ComfyUI på Mac Mini (om GPU räcker), eller gratis-tier hos Pollinations.ai (`https://image.pollinations.ai/prompt/<text>` — nyckel-fritt). **Lås en stilguide** (t.ex. "redaktionell flat-illustration, dämpad färgpalett, ingen text") så hela tidningen ser sammanhållen ut. Risk: AI-bilder blir lätt smetiga — kör bara där du kan kvalitetsgranska, dvs. leadbilden.

**Rekommendation för v1:** Ja, ha bilder — en bildlös tidning ser oavslutad ut. Men håll det disciplinerat:
- Lead: nivå 1 (källbild) eller nivå 3 (egen illustration, om du orkar kvalitetsgranska).
- Mellanartiklar: nivå 1 → fallback nivå 2.
- Notiser: **ingen bild** (en ren textspalt ger kontrast och "tidningskänsla", och minskar smet-risken).
- Hård regel: aldrig en bild du inte skulle visa en redaktör. Hellre en ren typografisk artikel än en dålig bild. Ha en kategori-baserad SVG/gradient-platshållare som sista utväg — snyggare än en irrelevant stockbild.

---

## 5. Valideringssteg (anti-hallucination)

Den viktigaste principen: **modellen får aldrig hitta på fakta — den får bara omformulera fakta som redan finns i briefen.** Designa bort hallucinationer i stället för att fånga dem i efterhand.

### Förebyggande (i skrivsteget, §6)
1. **Grounding:** Skrivprompten får ENDAST fakta-briefen (extraherad i steg 4 från full källtext) + källcitat. Instruktion: "Använd inga siffror, namn, datum eller citat som inte står i briefen. Om du saknar info, skriv runt det — gissa aldrig."
2. **Extraktion separerad från generering:** steg 4 (fakta) använder låg temperatur och drar ut exakta citat/siffror; steg 6 (text) skriver runt dem. Det gör det möjligt att diffa.

### Kontrollerande (steg 7, efter skrivning)
3. **Claim-check:** Skicka {genererad artikel + brief} till modellen: "Lista varje konkret påstående (siffra, datum, namn, citat) i artikeln. Markera för var och en: STÖDS / STÖDS_EJ av briefen." Allt STÖDS_EJ → ta bort eller flagga för manuell koll.
4. **Sifferdiff (deterministisk, ingen AI):** regex ut alla tal/procent/datum ur artikeln, kontrollera att varje finns i briefen. Snabbt och fångar de farligaste felen (uppfunna benchmarks/siffror).
5. **Länkvalidering:** varje artikel MÅSTE ha minst en käll-URL i frontmatter. Kör HTTP HEAD → 200? Annars flagga. Döda artiklar utan giltig källa.
6. **Cross-source för leaden:** för förstasidesnyheten, kräv ≥2 oberoende källor (du har redan klustringen från §3). Enkällade rykten får inte vara lead.

### Output-design som bygger förtroende
7. **Synliga källor:** varje artikel renderar "Källa: [Namn](url)" — det är både redaktionell hederlighet och din viktigaste hallucinationsförsäkring (läsaren kan klicka).
8. **Hedging-språk för osäkert:** om en story är ett rykte/läcka → skrivregeln tvingar "enligt uppgifter", "rapporteras", inte påståenden i indikativ.
9. **Logga allt:** spara brief + artikel + claim-check-resultat per utgåva. Om något fel slinker igenom kan du spåra var.

> Modellval kopplat till detta: DeepSeek V4 Flash är fin för *extraktion och första utkast* (billigt, högvolym). Men låt **Claude Sonnet göra det redaktionella finliret + claim-checken** — där är omdöme och instruktionsföljsamhet värt mer än kostnaden, och det är bara ~10 artiklar/vecka. Hybrid = bäst pris/kvalitet.

---

## 6. Rekommenderad implementation — vad bygger vi först?

**Princip: bygg tunnaste möjliga end-to-end först, manuell granskning i loopen, automatisera bakåt.** Du vill ha en publicerbar utgåva i vecka 1, inte en perfekt insamlare som aldrig når print.

### Fas 0 — Manuell pilot (denna helg, ~halvdag)
Innan en rad automation: gör **en utgåva för hand med Claude** för att låsa formatet.
- Definiera frontmatter-schemat skarpt nu (det är kontraktet allt annat bygger mot):
  ```yaml
  ---
  title: ""
  slug: ""
  category: ""        # model-release | research | policy | business | tools | sweden
  lead: false         # true för förstasidesnyhet
  summary: ""         # 1 mening, för förstasidan/listvy
  body_length: notis | medium | lead
  image: ""           # lokal sökväg, valfri
  image_credit: ""
  sources:            # MINST en, alltid
    - name: ""
      url: ""
  published: 2026-06-21
  ---
  ```
- Kör 1 utgåva, putsa tills den känns som en tidning. **Detta dokument blir kravspecen.**

### Fas 1 — Insamling + filtrering (MVP, vecka 1)
n8n-workflow:
1. RSS Read-noder för de ~15 flödena → slå ihop.
2. HN Algolia + Reddit JSON-noder → slå ihop.
3. Code-nod: normalisera till `{title, url, source, published, popularity}`, deduplicera på URL-hash + titel-likhet.
4. Code-nod: regelbaserad pre-score (§3 steg A).
5. AI-nod (1 anrop): topp-20 → JSON-betyg (§3 steg B).
6. Output: en `kandidater.json` med topp 12 + lead markerad.

**Stopp här och granska manuellt första veckorna.** Detta ensamt sparar dig timmar och du ser snabbt om poängsystemet väljer rätt.

### Fas 2 — Research + skrivning (vecka 2)
7. För varje vald: Jina Reader → full text + og:image.
8. AI-extraktion → fakta-brief (DeepSeek Flash).
9. AI-skrivning → artikel + frontmatter (Claude Sonnet), längdbudget per `body_length`.
10. Skriv markdown-filer till content-mappen.

### Fas 3 — Validering + bild (vecka 3)
11. Claim-check + sifferdiff + länkkoll (§5). Flaggade artiklar → en `review.md` du tittar på.
12. Bildpipeline: og:image → sharp/WebP; fallback Unsplash per kategori-sökord; notiser bildlöst.

### Fas 4 — Publicering & automation (vecka 4)
13. `node build.js` → git commit → push → Cloudflare Pages (du har detta).
14. n8n **Cron** söndag morgon kör hela kedjan → producerar utkast → notis till dig (mail/Slack) → **du godkänner manuellt** innan push.
15. Lägg in seen-databasen (§ steg 0) så uppföljningar och dedup funkar över veckor.

### Vad jag INTE skulle bygga (i v1)
- Egen scraper-flotta — RSS + Jina räcker. Scraping är underhållsbörda.
- AI-bildgenerering för alla artiklar — bara lead, om ens det.
- Fullt automatiserad publicering utan människa — håll "human in the loop"-godkännandet kvar tills du litar på valideringen. Det är en *publicerad tidning med ditt namn på*; den manuella grinden kostar 10 min/vecka och är värd det länge.

### Bygg-ordning, kort
> **Frontmatter-schema → n8n insamling+filtrering (granska manuellt) → research+skrivning → validering+bild → cron+godkännandegrind → seen-db för dedup/uppföljning.**

Är SearXNG rätt verktyg? **Ja — men som komplement, inte motor.** RSS är motorn (stabilt, gratis, strukturerat). SearXNG är din lucktäckare, svensk-vinkel-sökare och verifieringsverktyg. n8n är limmet. Den kombinationen kör hela pipelinen på $0/mån, och enda återkommande kostnaden blir några ören i API-tokens till Sonnet för ~10 artiklar/vecka — i praktiken försumbart.

---

### En sista redaktionell tanke
Det som gör AI-Bladet till en *tidning* och inte en feed är **urval och röst**. Lägg krutet där: diversifieringsregeln (max 3/kategori), längdbudgeten (notiser ger rytm), och en konsekvent skrivröst i Sonnet-prompten (sätt en kort "stilguide": saklig, nyfiken, lätt ironisk där det passar, svensk, förklarar jargong). Tekniken ovan är bara röret — själen sitter i de redaktionella reglerna.
