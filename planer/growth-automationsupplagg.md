# AI-Bladet Growth — Automationsupplägg (Fable 5)

> Svar på `/tmp/ai-bladet-growth-task.md`, 2026-07-12.
> Baserat på faktisk inspektion av `~/ai-bladet/` (build.js, templates/, pipeline/, public/, RUNBOOK.md, planer/seo-plan.md).

---

## 0. Tre saker jag hittade som ändrar planen

Innan frågorna — jag verifierade nuläget mot koden och den levande sajten, och tre fynd flyttar om prioriteringarna:

1. **`aibladet.se` svarar inte** (curl → tomt, ingen HTTP-respons), men `build.js:11` defaultar `SITE_URL` till `https://aibladet.se` och den deployade `public/sitemap.xml` + RSS + JSON-LD pekar dit. Sajten lever på `ai-bladet.pages.dev`. **Allt SEO-arbete i F0-1 är bortkastat tills domänen är kopplad** — Google får idag en sitemap på pages.dev vars URL:er pekar mot en död domän. Detta är steg noll, före Lighthouse.

2. **E-postlistan existerar inte.** Planen säger "E-postlistan är tillgången. Alla kanaler driver dit" — men det finns ingen signup-form, ingen ESP, noll prenumeranter-infrastruktur i templates/ eller public/. F0-6 ligger som näst sista punkt; den borde vara **F0-0**. Varje vecka utan signup är trafik som försvinner spårlöst. Dessutom låser ESP-valet F0-8 (referral) — se fråga 6.

3. **Delar av planen är redan byggd.** `pipeline/distribute_linkedin.py` (= F0-3) finns och körs redan via `distribute.py` i `run_weekly.sh`. `distribute_glossary.py` (= F0-2) finns också, men gör 1 term/vecka ur numret — planen säger 5/vecka, vilket kräver en separat generator. Planen bör uppdateras så den inte beställer om sådant som finns.

---

## 1. Automationsgrad per uppgift (F0-1 → F0-8)

| Uppgift | Grad | Motivering |
|---|---|---|
| **F0-1** SEO/arkiv | **Auto** | Engångsfix i kod (build.js + templates), sedan permanent gate i `run_weekly.sh`. Ingen veckoinsats. |
| **F0-2** Ordlista | **Semi → auto** | Generering helt auto (DeepSeek, ~$0.002/term). Publicering: Anton godkänner batch (10 min/vecka) tills valideringen bevisat sig — sedan auto med samma DeepSeek-validering som steg 7. |
| **F0-3** LinkedIn-utkast | **Auto** (finns redan) | `distribute_linkedin.py` genererar utkastet. Själva posten är F0-4:s problem. |
| **F0-4** LinkedIn-närvaro | **Manuell** | Företagssida skapas manuellt (engång). Postning: LinkedIns API för företagssidor kräver app-godkännande (Community Management API) — kan bli semi i Fas 1, men **LinkedIn Newsletter har inget API alls**: spegling = Anton klistrar in, ~10 min/vecka, för alltid. Räkna in det i 3–5h-budgeten. |
| **F0-5** Analytics | **Semi-setup, auto-drift** | Kontoskapande + DNS = Anton (engång, 30 min). Veckorapporten därefter 100 % auto (fråga 4). |
| **F0-6** Signup + välkomstmejl | **Semi-setup, auto-drift** | ESP-konto, domänverifiering (SPF/DKIM i DNS) = Anton. Välkomstsekvens = automation i ESP:n, skriven av mig, godkänd av Anton en gång. |
| **F0-7** OG-bilder | **Auto** | Genereras i `build.js` per nummer med `satori` + `sharp` (ren Node, inga externa tjänster). Engångsbygge. |
| **F0-8** Referral | **Beror på F0-6** | Med beehiiv: inbyggt, auto. Med Buttondown/listmonk: vi bygger själva (unik kod per prenumerant + räknare) — auto i drift men ~en dags bygge. Välj ESP med detta i åtanke. |

**Summering:** efter Fas 0 är Antons återkommande manuella arbete: LinkedIn-post + Newsletter-spegling (~20 min/v), ordliste-godkännande (~10 min/v under inkörning), läsa veckorapporten. Allt annat rullar i söndagskörningen.

---

## 2. F0-1: Smartaste ordningen + fällor

Planens ordning (Lighthouse först) är fel — jag hittade gapen redan genom att läsa koden. Kör istället:

### Ordning

1. **Domän först.** Koppla `aibladet.se` till Cloudflare Pages (custom domain) + bulk redirect `ai-bladet.pages.dev/*` → `aibladet.se/$1` (301). Verifiera bägge i Google Search Console (`google9ef664c542093724.html` ligger redan i public/ — kolla vilken property den hör till). *Utan detta är resten meningslöst.*
2. **Fixa URL-konsekvens i kod:**
   - `templates/base.js:16` — canonical är **relativ** (`href="/v/2026/28/"`). Gör absolut via `SITE_URL`.
   - `og:url` **saknas helt** i base.js — lägg till.
   - `templates/issue.js:45` — hårdkodad `https://aibladet.se`, ska läsa samma `SITE_URL` som build.js.
3. **Städa sitemap** (`build.js:137–192`):
   - **Testfiler ligger i produktions-sitemapen**: `/ordbok/test` och `/audio/test.mp3` skickas till Google idag. Filtrera bort, och radera `public/ordbok/test.html`.
   - `lastmod=TODAY_ISO` sätts på arkiv, om-sida, ordbok, audio — **varje sida påstår sig ändrad varje dag**. Google lär sig ignorera lastmod som ljuger. Använd fil-mtime eller issue-datum.
   - `<priority>` ignoreras av Google (dokumenterat) — låt stå men lägg noll tid på den.
4. **RSS-komplettering** (`build.js:117–135`): `<enclosure>` (numrets OG-bild, med length + type), och överväg `<content:encoded>` med full text — RSS-läsare och Feedly-synlighet är gratis distribution.
5. **Internlänkning**: prev/next-edge cases + "Tidigare nummer" finns redan i issue.js — verifiera kanterna (första numret, senaste numret) med ett litet testskript istället för ögon.
6. **Lighthouse sist, som gate**: `tools/seo_audit.sh` — servar `public/` lokalt (`npx serve`), kör `npx lighthouse --only-categories=seo,performance,accessibility` mot front + senaste nummer + arkiv, failar under tröskel. Koppla in i `run_weekly.sh` efter `node build.js`, före push.

### Fällor planen missat

- **Startsidan kanoniserar bort sig själv.** `public/index.html` har `canonical → /v/2026/28/`. Det betyder att startsidan säger till Google "indexera inte mig, indexera veckans permalänk". För varumärkessökningen "AI-Bladet" vill du att **startsidan** rankar. Antingen egen canonical för `/` (och acceptera duplicate-risken, den är låg med olika title/beskrivning), eller gör startsidan till ett skal med utdrag + länk istället för hela numret.
- **Lighthouse SEO ≥95 är fel mål.** Lighthouse mäter bara att meta-taggar *finns* — inte att sajten rankar. 95+ nås på en eftermiddag. Den riktiga mätaren är GSC: indexerade sidor, visningar, klick. Sätt målet där.
- **Ordbok/audio/memes lever i `public/`** — byggoutput, inte källa. `build.js:21–23` räddar dem via en /tmp-roundtrip före wipe. Det är skört och gör att sitemap-lastmod inte kan sättas rätt. Fix: flytta till `content/ordbok/*.md` som källa och låt build.js rendera dem som allt annat (se fråga 3).

---

## 3. Arkitektur: samma repo, separerade lager

**Samma repo.** Tillväxtkoden konsumerar `content/*.md`, templates och `SITE_URL` — ett separat repo betyder duplicerad byggloggik, två deploy-kedjor och versionsdrift. Repot är litet; problemet är inte storlek utan sammanblandning. Lös det med kataloger och separata körningar:

```
~/ai-bladet/
├── pipeline/            # ENDAST tidningen: collect→…→validate + run_weekly.sh
│   └── distribute_*.py  # flytta → growth/distribute/ (se nedan)
├── growth/
│   ├── distribute/      # linkedin, x, audio, meme (flyttas från pipeline/)
│   ├── glossary/        # F0-2: generator + validering, 5 termer/v
│   ├── report/          # F0-5: veckorapport (report_weekly.py)
│   ├── referral/        # F0-8: kod-generering + landningslogik
│   └── tools/           # seo_audit.sh, link_check.py
├── content/
│   ├── *.md             # utgåvor (som idag)
│   └── ordbok/*.md      # ordlistetermer SOM KÄLLA (inte public/)
├── build.js             # renderar ALLT ur content/ → public/
└── templates/           # + ordbok.js-mall
```

**Principer:**
- `content/` är enda sanningskällan; `public/` får aldrig innehålla något som inte kan regenereras. Det tar bort /tmp-roundtripen i build.js.
- **Två cron-jobb i Hermes**, inte ett: "AI-Bladet söndag" (tidningen, som idag) och "AI-Bladet growth" (ordlista + rapport, t.ex. måndag 07:00). Då kan tillväxtkoden aldrig fälla tidningsutgivningen — samma resonemang som runbookens valideringsgate.
- Tillväxtkörningen får egen loggfil och egen Telegram-leverans, samma mönster som `runner-*.log`.

---

## 4. Veckorapporten: helt automatiserbar utom LinkedIn

**Verktygsval:** Plausible framför CF Web Analytics — Plausible har ett rent Stats API (`/api/v1/stats`) med UTM-nedbrytning; CF Web Analytics API:t är begränsat. Antingen $9/mån eller Plausible CE self-hostat på Mac Minin (den är always-on och kör redan Hermes).

**`growth/report/report_weekly.py`** — körs i growth-cronen, levererar markdown till Telegram (samma kanal som pipelinen) och committar `growth/report/kpi/YYYY-WW.json` för historik/trendlinjer:

| Data | Källa | Auto? |
|---|---|---|
| Trafik, källor, UTM, toppsidor | Plausible Stats API | ✅ |
| Sökvisningar, klick, position, indexering | Google Search Console API (service account) | ✅ |
| Prenumeranter, opens, clicks, unsubs | ESP:ns API (beehiiv/Buttondown/listmonk — alla har API) | ✅ |
| Signup-konvertering | Plausible custom event `signup` / ESP | ✅ |
| Referral-topplista (Fas 2) | ESP eller egen tabell | ✅ |
| LinkedIn: följare, post-räckvidd | **Inget API för personliga profiler.** Företagssida kräver API-godkännande. | ❌ Anton klistrar in 3 siffror/vecka, eller hoppa mätningen tills företagssidans API är godkänt |
| Podd-outreach, DM-utfall (Fas 1–2) | Antons anteckningar | ❌ enkel `growth/report/manual.yaml` som rapporten läser in |

Rapportformat: en skärm i Telegram — prenumeranter (Δ), trafik (Δ), topp-3 källor, GSC-klick (Δ), bästa sida, 1 rad "åtgärd föreslås". Inte en dashboard ingen tittar på.

**UTM-disciplin:** lägg UTM-generering i distribute-stegen (linkedin/x-utkasten får färdiga `?utm_source=linkedin&utm_medium=social&utm_campaign=v28`-länkar automatiskt) så att attribution aldrig beror på Antons minne.

---

## 5. Största riskerna

1. **Fas 1 kan inte automatiseras — och det är hela tillväxtmotorn.** 0→100 bygger på Antons LinkedIn-loop och DM:er. Kod kan generera utkast, men räckvidd på LinkedIn kommer från personens kommentarer, svar och närvaro. Risken är att vi (AI:erna) bygger automation i veckor medan det enda som faktiskt flyttar nålen — att Anton postar och pratar med folk — inte händer. **Automationens jobb är att skydda Antons 3–5h till exakt det, inte att fylla dem.**
2. **SEO på fel domän.** Redan täckt ovan, men det är risk #1 i tid: varje vecka på pages.dev utan 301-strategi är länkkraft och indexering som måste flyttas senare.
3. **Automatisera inte Antons LinkedIn-konto.** Auto-postning/auto-DM via inofficiella vägar bryter LinkedIns ToS och kontot är Fas 1-motorn. Utkast auto, publicering människa. Företagssidan via officiellt API är okej när/om det godkänns.
4. **Programmatisk SEO-tunnhet.** 60 genererade definitionssidor konkurrerar med Wikipedia och IDG. Googles policy mot "scaled content abuse" träffar exakt detta mönster om sidorna är generiska. Motmedel: varje term får svensk affärsvinkel + länk till nummer där termen förekom + exempel — och hellre 2 bra/vecka än 5 tunna. Valideringssteget (steg 7-mönstret) ska gälla ordboken också.
5. **Deliverability när listan växer.** Self-host (listmonk på Mac Minin) ger kontroll men hamnar i spam utan dedikerad SMTP (Postmark/SES) och korrekt SPF/DKIM/DMARC. En hosted ESP köper bort hela risken för ~0 kr under 1000 prenumeranter.
6. **Mac Minin är single point of failure** för både tidning och tillväxt. Runbooken hanterar tidningen; se till att growth-cronen ärver samma fellägen + att **ESP-listan exporteras veckovis till repot** (krypterad) — listan är tillgången, den ska inte bara bo hos en tredjepart.

---

## 6. Vad saknas i planen

1. **F0-0: ESP-val + signup — före allt annat.** Rekommendation: **beehiiv** (gratis <2 500 prenumeranter, inbyggt referral-program som löser F0-8 gratis, API för rapporten). Alternativ om oberoende väger tyngre: Buttondown eller listmonk self-hostat — men då bygger vi referral själva och äger deliverability-risken. Signup-formulär i `templates/base.js` (footer på varje sida + efter lead-storyn), custom event i Plausible.
2. **GDPR saknas helt.** Svensk publik, e-postinsamling: kräver integritetspolicy-sida (`/om/integritet/`), samtyckestext vid signup, double opt-in. Även marknadsföringslagen för utskick. En kväll att fixa, dyrt att strunta i. Ingen sådan sida finns i templates/ idag.
3. **Google News / Publisher Center.** Sajten har redan NewsArticle-JSON-LD och nyhetsformat. Ansökan till Google Nyheter är gratis och kan vara den enskilt största trafikkanalen för en svensk nyhetspublikation. Kräver egen domän (skäl #4 att fixa domänen först). Planen nämner det inte förrän möjligen "PR-offensiv" i Fas 3 — det hör hemma i Fas 0/1.
4. **Baslinje och definition av "störst".** Målet "Sveriges största AI-publikation" saknar mätdefinition och nolläge. Skriv in i veckorapporten från vecka 1: prenumeranter (idag: 0), unika/vecka, GSC-klick. Annars går det inte att veta om planen fungerar förrän det är för sent att ändra den.
5. **Välkomstsekvensens innehåll** (F0-6 säger "välkomstmejl", singular). En 3-mejlssekvens (bekräftelse → bästa arkivnumren → "svara och berätta vad du jobbar med") är standard eftersom svar dessutom tränar deliverability. Genereras en gång, godkänns av Anton, körs av ESP:n.
6. **Planen är delvis redan genomförd** — F0-3 körs i produktion, F0-2 finns till 40 %. Uppdatera plandokumentet mot koden innan nästa fas beställs, annars byggs saker dubbelt (jag noterade samma mönster i `planer/seo-plan.md`, som överlappar F0-1).

---

## Föreslagen exekveringsordning (Fas 0, reviderad)

| # | Vad | Vem | Tid |
|---|---|---|---|
| 1 | Koppla aibladet.se + 301 från pages.dev + GSC-verifiering | Anton (DNS/CF-UI) | 30 min |
| 2 | F0-6: beehiiv-konto + DNS-poster | Anton | 30 min |
| 3 | F0-6: signup i templates + välkomstsekvens | AI, Anton godkänner texter | — |
| 4 | F0-1: kodfixar enligt §2 + `tools/seo_audit.sh` som gate | AI | — |
| 5 | F0-7: OG-bilder (satori+sharp i build.js) | AI | — |
| 6 | F0-5: Plausible + `growth/report/report_weekly.py` + growth-cron | AI, Anton skapar konto | 15 min |
| 7 | GDPR-sida + double opt-in | AI, Anton godkänner | — |
| 8 | F0-2: ordbok → `content/ordbok/`, generator + validering, 2–3 termer/v | AI, Anton skummar batch | 10 min/v |
| 9 | F0-4: företagssida + Newsletter-spegling | Anton | 20 min/v löpande |
| 10 | Google News-ansökan (kräver #1) | Anton skickar, AI förbereder | 20 min |

Antons totala engångsinsats: ~2 h. Löpande: ~30–40 min/vecka utöver LinkedIn-loopen — inom budget.
