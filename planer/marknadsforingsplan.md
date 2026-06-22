# AI-Bladet — Autonom Marknadsföringsplan

> Organisk distribution. Bygger publik utan annonskostnader.
> Endast API-kostnader för innehållsproduktion.
> Publicerad 2026-06-22.

---

## Strategisk princip

AI-Bladet producerar redan 10–12 redaktionella stories varje vecka via pipeline.
**Varje story är en marknadsföringstillgång som används en gång.**

Denna plan bygger på **content atomization**: spräng varje story i 5–7 format,
ett per plattform, helt automatiskt. Samma research, olika uttryck.

Allt som är mekaniskt (omformatering, rendering, schemaläggning) → automatiseras.
Allt som kräver omdöme (communitysvar, debatt, personlig ton) → Anton/Lutra manuellt.

---

## Översikt: Distributionspipeline

```
Söndag 07:00 — Issue publiceras (befintlig pipeline)
         │
         ▼
Söndag 08:00 — Distributionspipeline kickar igång
         │
         ├── 1. TTS-audio (90s sammanfattning) → mp3 → sajt + RSS
         ├── 2. Veckans AI-ord → SEO-sida + Instagram-kort
         ├── 3. Humaniserad story → LinkedIn
         ├── 4. Veckans AI-lögn → X/Twitter
         ├── 5. Meme-kort → Instagram + Reddit
         └── 6. X-thread (topp 3 stories) → X/Twitter
```

---

## Byggblock 1: 90-sekunders ljudsammanfattning

### Format
En svensk 90-sekunders sammanfattning av veckans 3 hetaste nyheter, läst av
ElevenLabs TTS (röst: "Freja" eller "Matilda"). Inkluderas som ljudspelare på
varje issue-sida + separat RSS för framtida podcast-distribution.

### Manusstruktur
```
[0:00-0:10]  JINGEL + "AI-Bladet, vecka [WW]. Din 90-sekunders sammanfattning."
[0:10-0:30]  Story 1 — rubrik + 1 mening kontext + varför det spelar roll
[0:30-0:50]  Story 2 — rubrik + 1 mening kontext + varför det spelar roll
[0:50-1:10]  Story 3 — rubrik + 1 mening kontext + varför det spelar roll
[1:10-1:25]  Veckans AI-ord: [term] — [kort förklaring]
[1:25-1:30]  "Läs hela tidningen på ai-bladet.se. Nytt nummer varje söndag."
```

### Teknisk implementation
```
Pipeline-steg: pipeline/distribute_audio.py

Input:  content/YYYY-WW.md (befintlig issue-fil)
Steg:
  1. Extrahera lead + topp 2 stories + veckans ord från frontmatter
  2. DeepSeek V4 Pro: generera manus enligt struktur ovan (~500 tokens, ~$0.0005)
  3. ElevenLabs TTS: generera ljud från manus
     - API: POST /v1/text-to-speech/{voice_id}
     - Röst: "Freja" (svensk, kvinnlig) eller "Matilda"
     - Kostnad: ~$0.015 per 90s (1000 tecken)
  4. Spara mp3 → public/audio/YYYY-WW.mp3
  5. Uppdatera issue-sidan med <audio>-spelare
  6. Uppdatera podcast-RSS (/feed/podcast.xml)

Kostnad per vecka: ~$0.0155
Output: public/audio/YYYY-WW.mp3
```

### RSS för podcast
```
Fil: public/feed/podcast.xml
Format: Apple Podcasts-kompatibel RSS 2.0
Innehåller: alla historiska avsnitt
Syfte: submit till Spotify for Podcasters, Apple Podcasts, Google Podcasts
```

---

## Byggblock 2: Veckans AI-ordbok

### Format
Varje vecka extraheras en AI-term från veckans innehåll. En SEO-optimerad
förklaringssida skapas (permanent URL). Ett Instagram-vänligt story-kort
genereras för delning.

### Struktur per term
```yaml
Term: "inferens"
Förklaring: "När en AI-modell använder sin träning för att analysera ny data
            och komma fram till ett svar. Tänk: träning = plugga till prov,
            inferens = skriva provet."
Exempel från veckans nyheter: "Nvidias nya chip snabbar upp inferens med 40%,
                              vilket betyder att AI-appar svarar snabbare."
Relaterade termer: ["träning", "modell", "GPU"]
```

### Teknisk implementation
```
Pipeline-steg: pipeline/distribute_glossary.py

Input:  content/YYYY-WW.md
Steg:
  1. DeepSeek V4 Pro: identifiera 1 AI-term från veckans stories,
     generera förklaring + exempel (~300 tokens, ~$0.0003)
  2. Generera SEO-sida: public/ordbok/[term-slug].html
     - Canonical URL, meta description
     - Länkar till relaterade termer och arkiv
  3. Generera Instagram-kort: 1080x1920 PNG med term + förklaring
     - HTML → PNG via headless Chrome (gratis)
     - Spara: public/ordbok/img/[term-slug].png
  4. Uppdatera ordbok-index: public/ordbok/index.html

Kostnad per vecka: ~$0.0003
Output: public/ordbok/[term-slug].html + .png
SEO-värde: högt. 52 termer/år = permanent sökbar kunskapsbank.
```

---

## Byggblock 3: Humaniserad story (LinkedIn)

### Format
En story från veckans issue skrivs om för en icke-teknisk publik. Svarar på
"vad betyder detta för mig?" och postas på LinkedIn.

### Teknisk implementation
```
Pipeline-steg: pipeline/distribute_linkedin.py

Input:  content/YYYY-WW.md
Steg:
  1. Välj story med högst "vardagsrelevans"-score
     (DeepSeek bedömer: påverkar detta vanliga människor?)
  2. DeepSeek: skriv om till LinkedIn-format:
     - Hook: "Har du undrat varför [X] plötsligt finns överallt?"
     - Ingress: förklara storyn för en icke-teknisk person
     - Varför det spelar roll: 2-3 meningar
     - Länk till AI-Bladet för "hela bilden"
     - Max 1500 tecken (LinkedIn optimalt)
     (~400 tokens, ~$0.0004)
  3. Spara som utkast: pipeline/output/linkedin/YYYY-WW.md
  4. Anton granskar → postar manuellt (eller auto-posta via n8n senare)

Kostnad per vecka: ~$0.0004
Output: pipeline/output/linkedin/YYYY-WW.md
Manuellt steg: LinkedIn-posten (kan auto-postas senare via n8n)
```

---

## Byggblock 4: Veckans AI-lögn (X/Twitter)

### Format
Ett konträr statement som avslöjar en överdrift eller myt från veckans AI-nyheter.
Postas på X/Twitter. Designat för att vara delbart och provocera diskussion.

### Teknisk implementation
```
Pipeline-steg: pipeline/distribute_x_thread.py (del 1 av 2)

Input:  content/YYYY-WW.md
Steg:
  1. DeepSeek: identifiera en överdrift/hype från veckans stories
  2. DeepSeek: skriv en tweet som krossar myten:
     - Format: "Alla säger att [X]. Här är varför de har fel: [fakta/siffra]."
     - Max 280 tecken
     - Länk till AI-Bladets story för källa
  3. Spara: pipeline/output/x/YYYY-WW-lie.md

Kostnad per vecka: ~$0.0003
Output: pipeline/output/x/YYYY-WW-lie.md
```

### Publiceringsstrategi för X
```
Dag:         Måndag 09:00 (dagen efter publicering)
Timing:      Morgon = högst engagemang för tech-innehåll
Hashtags:    #AI #SvenskAI #TechNews (max 2-3)
```

---

## Byggblock 5: Meme-kort (Instagram + Reddit)

### Format
En AI-genererad bild + text som fångar veckans roligaste/absurdaste AI-nyhet.
För Instagram och Reddit (r/artificial, r/sweden, r/unket).

### Teknisk implementation
```
Pipeline-steg: pipeline/distribute_meme.py

Input:  content/YYYY-WW.md
Steg:
  1. DeepSeek: identifiera veckans mest meme-vänliga story
     (bedömningskriterier: absurditet, igenkänning, humorpotential)
  2. DeepSeek: generera meme-text (top text + bottom text) + bildbeskrivning
     (~200 tokens, ~$0.0002)
  3. Pollinations.ai: generera bild från prompt (gratis, ingen API-nyckel)
     - URL: https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1080
  4. HTML → PNG med text overlay via headless Chrome (gratis)
  5. Spara: public/memes/YYYY-WW.png

Kostnad per vecka: ~$0.0002
Output: public/memes/YYYY-WW.png
```

---

## Byggblock 6: X-thread (topp 3 stories)

### Format
En tråd på X med veckans 3 viktigaste stories, en per tweet. Avslutas med
en "läs hela tidningen"-länk.

### Teknisk implementation
```
Pipeline-steg: pipeline/distribute_x_thread.py (del 2 av 2)

Input:  content/YYYY-WW.md
Steg:
  1. Extrahera lead + topp 2 stories
  2. DeepSeek: skriv om varje till tweet-format
     - 1 tweet per story
     - Max 280 tecken per tweet
     - Behåll redaktionell röst men korta ner
     (~300 tokens, ~$0.0003)
  3. Tweet 4: "Läs hela AI-Bladet vecka [WW]: [länk]"
  4. Spara: pipeline/output/x/YYYY-WW-thread.md

Kostnad per vecka: ~$0.0003
Output: pipeline/output/x/YYYY-WW-thread.md
```

---

## Teknisk arkitektur: distribute.py (orkestrator)

Samordnar alla distribueringssteg efter lyckad publicering:

```python
# pipeline/distribute.py — körs efter run_weekly.sh
#
# Anrop: python distribute.py --issue content/YYYY-WW.md [--dry-run]

def main():
    issue = load_issue(args.issue)

    # Alla steg körs parallellt (oberoende av varandra)
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(build_audio_summary, issue):   "audio",
            executor.submit(build_glossary_term, issue):   "glossary",
            executor.submit(build_linkedin_post, issue):   "linkedin",
            executor.submit(build_x_lie, issue):           "x_lie",
            executor.submit(build_meme, issue):            "meme",
            executor.submit(build_x_thread, issue):        "x_thread",
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                future.result()
                log(f"✓ {name}")
            except Exception as e:
                log(f"✗ {name}: {e}")

    # Bygg om sajten med nya assets (audio, memes, ordbok)
    subprocess.run(["node", "build.js"], check=True)

    # Git push → Cloudflare Pages deploy
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", f"distribute: week {issue.week}"])
    subprocess.run(["git", "push"])
```

### Integration med run_weekly.sh

```bash
# I run_weekly.sh, efter lyckad validate + git push:
echo "🚀 Starting distribution pipeline..."
python pipeline/distribute.py --issue "content/$(date +%Y)-$(date +%V).md"

# Distribution är best-effort — en failad meme stoppar inte allt annat
```

---

## Kostnadssammanställning

| Byggblock | Modell | Kostnad/vecka | Kostnad/år |
|-----------|--------|---------------|------------|
| 1. Audio-sammanfattning | DeepSeek + ElevenLabs | $0.0155 | $0.81 |
| 2. AI-ordbok | DeepSeek | $0.0003 | $0.02 |
| 3. LinkedIn-post | DeepSeek | $0.0004 | $0.02 |
| 4. AI-lögn (X) | DeepSeek | $0.0003 | $0.02 |
| 5. Meme-kort | DeepSeek + Pollinations | $0.0002 | $0.01 |
| 6. X-thread | DeepSeek | $0.0003 | $0.02 |
| **Totalt** | | **~$0.017** | **~$0.90** |

Plus befintlig pipeline: ~$0.10/vecka. **Total drift: ~$0.12/vecka, ~$6.24/år.**

---

## Implementationsordning

### Sprint 1: Audio + X (vecka 1–2)
- `distribute_audio.py` — TTS-sammanfattning + podcast-RSS
- `distribute_x_thread.py` — X-thread + AI-lögn
- `distribute.py` — orkestrator
- Modifiera `run_weekly.sh` att anropa distribute efter publicering

### Sprint 2: Ordbok + Meme (vecka 3–4)
- `distribute_glossary.py` — AI-ordbok + SEO-sidor
- `distribute_meme.py` — Meme-generering
- Ordboks-index + navigation på sajten

### Sprint 3: LinkedIn + Förfining (vecka 5–6)
- `distribute_linkedin.py` — Humaniserad story
- Finjustera TTS-röst, meme-mallar, timing

---

## Vad medvetet INTE är med

- **Annonser/Adwords.** Kostar pengar, bygger inte publik organiskt.
- **Auto-DM/bottar.** Förstör förtroende, ger blocks.
- **Nyhetsbrev (än).** Kräver prenumeranthantering (Mailchimp/Beehiive).
  Vänta tills vi har 100+ RSS-prenumeranter, bygg sedan.
- **Discord-community.** Kräver aktiv moderering. För tidigt.
- **SEO-verktyg (Ahrefs/Semrush).** Kostar $100+/mån. Använd gratis
  Google Search Console tills vidare.
- **TikTok/YouTube Shorts.** Kräver videoproduktion. Utforska efter Fas 3.

---

## Mätning (gratis verktyg)

| Metrik | Verktyg | Frekvens |
|--------|---------|----------|
| Sidvisningar | Cloudflare Analytics | Veckovis |
| RSS-prenumeranter | Serverloggar | Veckovis |
| X-impressions | X Analytics (gratis) | Veckovis |
| Google-indexerade sidor | Google Search Console | Månadsvis |
| Sökord i topp 100 | Google Search Console | Månadsvis |

---

## Nästa steg

1. Bygg `pipeline/distribute.py` — orkestrator
2. Bygg `pipeline/distribute_audio.py` — första byggblocket
3. Skaffa ElevenLabs API-nyckel (~$5/mån för 10h ljud, räcker till ~400 avsnitt)
4. Modifiera `run_weekly.sh` — anropa distribution efter publicering
5. Kör första distribuerade numret

**Börja med Sprint 1.** Audio + X ger störst räckvidd för minst effort.
Resten bygger vi iterativt.
