# AI-Bladet — Loggbok

> **Delad logg för båda agenterna (Claude Code + lutra).** Läs de översta posterna
> innan du börjar; lägg en ny post högst upp när du är klar och tagga `[vem]`.
|> Spelregler: se `AGENTS.md`.

## 2026-06-22 — [lutra] SEO implementerad 🔍 — alla 6 punkter klara

- **JSON-LD (#2):** `issue.js` — image, author (Anton Swall), publisher (AI-Bladet + logo), isAccessibleForFree, url, dateModified, keywords. Kvalificerar för Google News carousel.
- **Sitemap (#6):** `build.js` — lastmod, changefreq, priority per URL. Inkluderar ordbok/audio/memes/feed om de finns. 4 URLs för nuvarande issue-sida.
- **Alt-text (#4):** `issue.js` + `archive.js` — tidigare-nummer-kort använder issue-titel som alt. 0 tomma alt-attribut i hela bygget.
- **Rubriker (#3):** `issue.js` — Kortnytt-sektionen använder `<h2>` istället för `<div>`.
- **Meta descriptions (#1):** `issue.js` + `base.js` — rikare sidbeskrivning: "summary + AI-Bladet vecka X år". OG-bild + twitter:card=summary_large_image.
- **Internlänkar (#5):** `issue.js` — "Relaterade artiklar"-widget baserad på kategori-överlapp mellan nummer. Syns först när ≥2 nummer finns.
- **Dist-tillgångar bevaras:** `build.js` — backuppar ordbok/audio/memes/feed till /tmp före wipe och återställer efter.
- **Testad ✅** — build.js kör, sitemap=4 URLs, 0 tomma alt, JSON-LD på index + permalink
- **Nästa:** Google indexerar om — resultat syns om 1–2 veckor

## 2026-06-22 — [lutra] SEO-plan skapad 🔍

- **planer/seo-plan.md:** Detaljerad analys av 6 SEO-punkter + åtgärdsplan i 3 faser
- **Status:** 3 punkter är redan delvis klara (meta, titlar, sitemap), 3 behöver jobb (JSON-LD, alt-text, interna länkar)
- **Största vinst:** JSON-LD enrichment → kvalificerar för Google News carousel
- **3 faser:** Fas 1 (JSON-LD + sitemap + alt-text, ~30 min) → Fas 2 (rubriker + meta, ~20 min) → Fas 3 (korsreferenser, ~30 min)
- **Nästa:** Anton bestämmer om jag ska koda fas 1

## 2026-06-22 — [lutra] Sprint 3 byggd: LinkedIn 💼 + Alla 5 distribueringsmoduler klara

- **pipeline/distribute_linkedin.py:** DeepSeek väljer mest vardagsrelevant story → genererar LinkedIn-post (max 1500 tecken, icke-teknisk ton) → sparar som utkast
- **distribute.py:** 5/5 moduler i default-setet (audio, x, glossary, meme, linkedin)
- **Dry-run testad ✅** med alla 5 parallellt: 5/5 lyckades
- **Total distribution per vecka:** ~$0.017 (alla 5 moduler)
- **Nästa:** API-nycklar + live-test på söndagens pipeline

## 2026-06-22 — [lutra] Sprint 2 byggd: Ordbok + Meme 🎨

- **pipeline/distribute_glossary.py:** DeepSeek identifierar AI-term → genererar SEO-sida i `public/ordbok/[slug].html` + uppdaterar index med alla termer
- **pipeline/distribute_meme.py:** DeepSeek identifierar memevärdig story → Pollinations.ai genererar bild (gratis) → Chrome renderar text overlay → `public/memes/YYYY-WW.png`
- **distribute.py:** Default-moduler uppdaterade till alla 4 (audio, x, glossary, meme)
- **Dry-run testad ✅** på vecka 25: 4/4 moduler parallellt, alla output-filer skapade
- **Kostnad Sprint 2:** ~$0.0005/vecka extra (DeepSeek x2, Pollinations gratis)
- **Nästa:** Sprint 3 (LinkedIn) eller verkligt API-test med ElevenLabs

## 2026-06-22 — [lutra] Sprint 1 byggd: Audio + X distribution 📡

- **pipeline/distribute.py:** Orkestrator — kör alla distribueringsmoduler parallellt, exit 0 om ≥50% lyckas
- **pipeline/distribute_audio.py:** TTS-sammanfattning (DeepSeek-manus → ElevenLabs → mp3 → podcast-RSS)
- **pipeline/distribute_x.py:** X-thread (4 tweets) + Veckans AI-lögn (konträr tweet → sparas som .md)
- **run_weekly.sh:** Distribution anropas efter lyckad git push + Moltbook, med re-build + re-push för audio-assets
- **Dry-run testad ✅** på vecka 25: 2/2 moduler, alla output-filer skapade
- **Kostnad:** ~$0.016/vecka extra (DeepSeek ~$0.001 + ElevenLabs ~$0.015)
- **Saknas för live:** ElevenLabs-röst-ID måste verifieras (använder "Rachel" som fallback — byt till svensk röst)
- **Nästa:** Anton testar med riktigt ElevenLabs-anrop + verifierar podcast-RSS

## 2026-06-22 — [lutra] Marknadsföringsplan skapad 📋

- **planer/marknadsforingsplan.md:** Detaljerad plan för autonom organisk marknadsföring
- **6 byggblock:** Audio-sammanfattning (TTS), AI-ordbok (SEO), LinkedIn-post, X-lögn, Meme-kort, X-thread
- **Content atomization:** Varje story → 5–7 format, helt automatiskt
- **Kostnad:** ~$0.017/vecka extra (~$0.90/år)
- **Implementation:** 3 sprintar över 6 veckor. Sprint 1: Audio + X
- **Claude Code:** Läs och granska planen. Börja inte bygga förrän Anton säger kör.
- **Nästa:** Anton beslutar om vi börjar med Sprint 1 (audio) eller annat block först

## 2026-06-21 — [lutra] Moltbook-autopost + Vecka 25 postad 🦞

- **Manuell post:** Vecka 25 postad till Moltbook/general — verifierad och live
- **Automatik:** `pipeline/post-to-moltbook.py` — anropas från `run_weekly.sh` efter lyckad git push
- **Inbyggd verification:** math challenge parsas (summa/subtraktion/multiplikation) och svar skickas
- **Misslyckande bryter inte:** `|| echo` så pipelinen fortsätter även om Moltbook krånglar
- **Nästa söndag 07:00:** postas automatiskt efter deploy 🦞

## 2026-06-21 — [lutra] write.py YAML-fix

- **write.py regel 15:** SYSTEM_PROMPT + output-mall instruerar nu Sonnet att använda YAML block scalars (`|`) för flerradiga fält (lead.analysis, stories[].body). Enradiga fält förblir double-quoted. Detta löser root cause till att både PyYAML och js-yaml kraschade.
- **Bildbankskurator:** `pipeline/curate_images.py` — söker Wikimedia Commons API, filtrerar CC-licens, HEAD-verifierar. Just nu 0 nya bilder (API:n funkar men returnerar få JPEG-resultat per query — scriptet finns på plats för framtida körning). +SERVER_RACK manuellt tillagd.
- **Bildbanken:** 14 poster nu (11 foton + 3 interna). Nya keyword-buckets för eu/sverige/reglering/robot/chip.
- **Arkiv UX:** Rikare arkivkort med bild + ingress + kategorier. "Tidigare nummer"-sektion på framsidans botten (visas när det finns ≥2 utgåvor).
- **Nästa:** curatorn behöver bredare söktermer eller manuell körning. Banken behöver ~10 fler bilder för att vara bekväm vid 5 stories/vecka.

## 2026-06-21 — [lutra] Vecka 25 ute ✅ + bilddedup-fix i image_bank.py

- **Första autonoma körningen** lyckades — trots flera buggar som fixades i farten
- **Buggar fixade:** symlänk-block i cron (wrapper-skript), frontmatter-stängning saknades (Sonnet), YAML multi-paragraph i body-fält (konverterade till block scalars), validate.py patched till regex-baserad parsning
- **Bilddubbletter:** BalticServers användes för 2 stories, Scott Beale/NYSE för lead+ASML. Bytt i content/2026-25.md. Root cause: `pick()` återanvände `candidates[0]` istället för att falla tillbaka till nästa nivå. Fixat i image_bank.py — faller nu keyword → source → category → default innan repris tillåts.
- **Kvar till nästa vecka:** write.py måste instruera Sonnet att använda `|` block scalars för body-text. Annars kraschar YAML-parsningen igen.
- Cloudflare deployar om automatiskt vid push → live

## 2026-06-21 — [lutra] Fix: ersatt symlänk med wrapper-skript i .hermes/scripts/

- `~/.hermes/scripts/ai-bladet-weekly.sh` var en symlänk → `pipeline/run_weekly.sh`
- Hermes cron schedulern resolverar symlänkar och blockar om target är utanför scripts-katalogen
- Ersatt symlänken med ett bash-wrapper-skript som `exec`ar pipeline-scriptet
- Uppdaterat AGENTS.md (symlänk → wrapper-skript)
- Nästa: nästa söndag 07:00 borde pipelinen gå utan fel. Testa med torrkörning om du vill validera nu

## 2026-06-18 — [Claude Code] Hård gate: HIGH-faktaflagga blockerar deploy

Torrkörning #2 (lutra) gick hela vägen ✅ MEN valideringen PASSADE (75%) trots en
[high]-flagga (lead tillskrev Jassy en 50-mdr-siffra som research inte stöder).
Grinden i `validate.py` saknade severity-koll → allvarliga faktafel kunde gå live.

**Fix (Antons beslut: fakta > kadens):** `result["pass"]` kräver nu även
`not high_issues`, där high_issues = flaggor med severity=="high" och supported=False.
Retry-loopen i run_weekly.sh skickar redan high/medium till Sonnet → 3 försök att
rätta; kvarstår en high → ingen deploy, utkast sparas, notis till Telegram.
Lade även en tydlig "HIGH-flaggor ❌ BLOCKERAR"-rad i valideringsutskriften.
Gate-logiken enhetstestad (blockerar obekräftad high, släpper medium + bekräftad high).

## 2026-06-18 — [Claude Code] Preflight härdad efter lutras torrkörning

Lutras torrkörning avslöjade två miljöbuggar (tack!):
- Scriptet använde Hermes-python (saknade `feedparser`) i stället för pipelinens
  egna `.venv`. lutra fixade PATH:en (la `pipeline/.venv/bin` först i run_weekly.sh).
- **Preflighten missade `feedparser`/`trafilatura`/`yaml`** → "passerade" falskt, och
  collect.py kraschade i stället. Utökade dep-kollen till hela setet pipelinen
  importerar: `requests, bs4, lxml, feedparser, trafilatura, yaml`. Verifierat → PASS
  med .venv-pythonen. Nu fångas saknade deps i preflight (loud) i stället för mitt i körningen.

Committar lutras PATH-fix + min preflight-fix tillsammans. seen.db verifierat återställd
(identisk med backup) → söndag opåverkad. Inga content/public-ändringar kvar.

## 2026-06-19 — [lutra] Torrkörning #2 — full pipeline PASS ✅

- **Preflight:** ✅ (PATH-fix från igår fungerar)
- **Pipeline:** collect ✅ → dedup ✅ → score ✅ → research ✅ → images ✅ (15/15) → write ✅ (~1501 ord, Sonnet) → validate ✅ (PASS, 75%, 1 försök) → build ✅ (Vecka 25)
- **Deploy:** ❌ SKIP_GIT_PUSH — torrkörning, städad: seen.db återställd, git restore, runnerloggar bort
- **Fynd:** en high-flagga i valideringen — lead-artikelns 50 miljarder-siffra attribueras som Jassy-citat trots att research säger internt estimat. Inget blockerande.
- **Nästa:** söndag 21/6 07:00 — första autonoma skarpa körningen 🚀

## 2026-06-18 — [lutra] Torrkörning — pipeline OK men avbruten (research 14/15)

- **Syfte:** testa hela pipelinen inför söndagens premiärkörning
- **Preflight:** ✅ (efter PATH-fix: la till pipeline-venv före Hermes-venv i run_weekly.sh)
- **Pipeline:** collect ✅ → dedup ✅ → score ✅ → research ⚠️ (14/15 briefingar klara, interrupt)
- **Validering:** ❌ nåddes aldrig (avbrott under research)
- **Build:** ❌ nåddes aldrig
- **Git/Deploy:** ❌ SKIP_GIT_PUSH satt, ingen push — städat: seen.db återställd, content/ + public/ git-restore, runnerlog borttagen
- **Fynd:** PATH-buggen är nu fixad i repot. Inget annat blockerar — söndagskörningen bör funka
- **Nästa:** första autonoma körningen söndag 21/6 07:00

## 2026-06-18 — [lutra] Synkroniserad — cron fixad, AGENTS.md inläst

- Pausade gamla Discord-cron "LUTRA AI NEWS — Veckorapport" (556028abe1ba)
- Symlänkade `~/.hermes/scripts/ai-bladet-weekly.sh` → `pipeline/run_weekly.sh`
- Läste AGENTS.md och loggbok-toppen — följer samarbetsrutinen framöver
- Minne uppdaterat: innan AI-Bladet-arbete → läs loggbok; efter → skriv [lutra]-post
- Nästa: första autonoma söndagskörningen 2026-06-21 07:00 🚀

## 2026-06-18 — [Claude Code] Samarbetskontrakt: AGENTS.md + delad loggbok

Gjorde det enkelt för Claude Code och lutra att turas om på projektet och se varandras
jobb. Ny `AGENTS.md` = spelregler (läs loggbok-toppen innan, skriv taggad post efter,
revirgränser). Loggboken är nu officiellt delad och poster taggas `[Claude Code]`/`[lutra]`.
Nästa: Anton ber lutra läsa AGENTS.md + loggboken och följa konventionen.

## 2026-06-18 — Driftsäkring inför första autonoma körningen (Claude Code, Opus 4.8)

Granskning inför premiärkörningen söndag 2026-06-21. Reda ut Antons farhågor:

- **"Scriptet saknas" — falskt.** `~/.hermes/scripts/ai-bladet-weekly.sh` FINNS och är
  byte-identiskt med `pipeline/run_weekly.sh`. Cronen failar inte av den orsaken.
- **"Loggboken föråldrad (Fas 0)" — fel fil.** Det står i den gamla planeringsfilen
  `claude-analyser/runda4-content-pipeline.md`, inte i loggbok.md (som är aktuell).
- **Riktiga risker åtgärdade i `run_weekly.sh`:**
  - Härdad PATH (homebrew + system + hermes-venv) — cron-miljön kan vara minimal.
  - Preflight som failar TIDIGT och tydligt (till Telegram) om python/node/git,
    python-deps (requests/bs4/lxml) eller OPENROUTER_API_KEY saknas. Testad → PASS.
  - `mkdir -p output` så loggfilen alltid kan skrivas.
- **`RUNBOOK.md` skapad** — driftmanual: manuell körning (SKIP_GIT_PUSH=1), samt
  åtgärder vid validerings-fail, Sonnet nere, git-push-fail, preflight-stopp.
- **Kvar för Anton (hans revir, ~/.hermes):**
  1. Symlänka Hermes-kopian → repo så de inte driftar:
     `ln -sf ~/ai-bladet/pipeline/run_weekly.sh ~/.hermes/scripts/ai-bladet-weekly.sh`
  2. Besluta om Discord-jobbet "LUTRA AI NEWS — Veckorapport" (0 9 * * 0) ska vara
     kvar parallellt, ersättas, eller bli en länk-postare till AI-Bladet.

## 2026-06-18 — Sessionssummering + autonomi-klargörande (Claude Code, Opus 4.8)

Sammanfattar dagens session (framsida-omarbetningen, iteration 1–3 nedan) plus två
saker som inte hade egen post:

**Bildstorlek — 20% större (efter iteration 3).** Anton ville ha bilderna något
större. `.figure-frame max-height`: lead 380→456px, story 280→336px. (Ersätter
pixelangivelserna i iteration 2-posten.) Byggd + deployad.

**Autonomi — schemaläggs av lutra (Hermes-agenten), INTE av sajten/repot.**
- Det finns INGEN system-cron, launchd-agent eller GitHub Action för AI-Bladet.
  Schemaläggningen sköts av Antons Hermes-agent "lutra" via dess egna cron-system
  (`~/.hermes/cron/jobs.json`).
- Jobb: **"AI-Bladet söndag"** (id ae23c12f7f29), `0 7 * * 0` (söndagar 07:00),
  enabled, deliver=telegram. Kör scriptet `~/.hermes/scripts/ai-bladet-weekly.sh`.
  Skapat 2026-06-18, första körning 2026-06-21 07:00 (last_run: ingen än).
- `ai-bladet-weekly.sh` = i praktiken samma som `pipeline/run_weekly.sh`:
  collect→dedup→score→research→images→write → validate (3 försök m. feedback-retry)
  → `node build.js` → `git add/commit/push origin main` → Cloudflare deployar.
  (SKIP_GIT_PUSH=1 ger torrkörning utan push.)
- VIKTIGT: Anton schemalägger/ändrar cron-jobb SJÄLV via lutra. Claude Code ska
  INTE röra `~/.hermes/`. Dagens session gjorde bara läs-koll där, inga ändringar.
- Alla dagens kodändringar ligger committade i repot → söndagskörningen plockar upp
  nya bildbanken, designen, rubrik-/citat-reglerna automatiskt.

## 2026-06-18 — Iteration 3: AUTOMATISK redaktionell bildbank (KLAR, live)

Anton: OG-bilderna (källornas marknadsföringsbanners) är tråkiga — bild + rubrik är
det första läsaren ser. KRAV: likvärdiga slående bilder ska hämtas AUTOMATISKT varje
söndag, inte handplockas.

**Lösning — `pipeline/image_bank.py`:** kurerad bank av fria pressfoton (Wikimedia
Commons, alla HEAD-verifierade 200 image/jpeg) med korrekt fotobyline + licens.
`pick(story, used)` väljer i tre steg: 1) tematiska nyckelord (ipo→NYSE, energi→
kraftledningar, compute/gpu→serverhall, rymd/förvärv→Musk/Falcon 9), 2) källa
(openai→Sam Altman, google-ai→Google HQ, xai→Musk), 3) kategori-fallback. `used`-set
ger automatisk avdramatisering av dubbletter (t.ex. två olika serverhallar, Musk +
Falcon 9). Pipelinens källor är en fast uppsättning → banken täcker dem; nya aktörer
faller till kategori-default tills banken utökas.

- `images.py`: OG-skrapningen ersatt — bildbanken är nu primär källa, sätter
  image_url + image_credit. (OG-helpers kvar men oanvända.)
- `write.py`: skickar Byline i prompten, emit:ar credit ordagrant (regel #12).
- `issue.js`: figcaption renderar credit rakt av ("Foto · X / CC BY").
- content/2026-25.md: backfillat med bankens 6 foton + bylines (Google HQ, Google
  HQ-entré, NYSE-golvet, Elon Musk, BalticServers serverhall, kraftledningar).

Verifierat: körde banken mot riktiga research-JSON:en → korrekt automatiskt val.
Byggd, screenshot-granskad, deployad → live.

## 2026-06-18 — Iteration 2: pressbild-känsla, fyndiga rubriker, äkta citat (KLAR, live)

Antons feedback efter att tabloid-looken gått live. Tre saker:
1. **Mindre bilder + pressbild-känsla:** `.figure-frame` med `max-height` (lead 380px,
   story 280px) → bilderna blir editorial-band istället för stora hero. Ny
   `figure-credit`-byline under varje bild ("PRESSBILD · {credit}"). `credit`-fält
   backfillat i content + emit:as av write.py (= källans namn).
2. **Fyndigare rubriker:** skrev om lead + 5 story-rubriker till säljande men
   100% research-förankrade (t.ex. "OpenAI tar första steget mot börsen: "Vi räknar
   med att det läcker""). write.py regel #13 kodifierar detta (attribuera siffror
   även i rubrik).
3. **Äkta citat "då och då":** nytt `quote`-block (text + speaker) som pull-quote på
   framsidan. KRITISKT: bara citat som finns ordagrant i research, troget översatta,
   attribuerade till EXAKT talaren (org-nivå: "OpenAI"/"Google" — research har inga
   namngivna personer, så inga påhittade vd-citat). 3 citat denna vecka: Gemini,
   OpenAI-S1, kinesisk påverkanskampanj. write.py regel #14.

Filer: content/2026-25.md, templates/issue.js (figure-helper + quote-render),
static/style.css (figure-frame/credit/story-quote), pipeline/write.py (regel 13+14,
output-mall). Byggd, verifierad i headless Chrome, deployad till main → live.

## 2026-06-18 — UI-omarbetning av framsidan: tabloid-look (KLAR, branch frontsida-tabloid)

Genomförde de 5 feedback-punkterna. Mål: framsidan mer som Aftonbladet — visuell,
stora rubriker, en bild per nyhet. Verifierat via headless Chrome mot lokal HTTP-server
(file:// fungerar inte — absoluta /style.css-sökvägar löses mot FS-roten).

**Vad gjordes (per punkt):**
1. `.stories-grid` (3-kol grid) → `.stories-column` (en vertikal spalt, flex-column).
2. Stora story-rubriker (clamp 1.7–2.7rem). Lead kvar prominent överst med hero-bild.
3. Bilder per story: stor bild ÖVER varje rubrik (Antons val), 16:9. Lead får 16:8 hero.
   - `templates/issue.js`: ny `figure()`-helper. Inline `onerror` flippar `<figure>`
     till en branded fallback ("AI-Bladet"-monogram på ink-gradient) — funkar även
     innan app.js laddat. Käll-URL:er 404:ar över tid → fallbacken fångar det.
   - `content/2026-25.md`: backfillade `image:` på lead + 5 stories (exakta URL:er
     ur `pipeline/output/images/2026-25.json`).
   - `pipeline/write.py`: skickar nu HELA bild-URL:en i prompten (förr `[:80]`-trunkerad),
     output-mallen emit:ar `image:` på lead + story, ny regel #12 (kopiera URL exakt,
     utelämna vid avsaknad).
4. "Läs mer" länkade till numret-sidan → nu INLINE-expansion av `s.body` under storyn
   (renderas dold med `hidden`, `aria-controls`/`aria-expanded`).
5. "Läs mindre"-toggle: ny `static/app.js` (event-delegation, ~25 rader), laddas via
   `templates/base.js` (`<script src="/app.js" defer>`). Sajtens första JS.

Permalink-sidan (`/v/ÅÅÅÅ/VV/`) oförändrad i beteende: bilder visas, body alltid synlig,
ingen toggle. Responsiva grid-brytpunkter för gamla `.stories-grid` borttagna.

**Ursprungliga 5 punkterna (för referens):**

**De 5 punkterna:**
1. Story-korten (Modeller/Företag/Säkerhet/Verktyg) ligger i 3-kolumners grid
   (`.stories-grid` i style.css). Gör om till EN vertikal, scrollbar spalt — Aftonbladet-stil.
2. Stora rubriker per nyhet. Viktigaste storyn kvar prominent på huvudomslaget (lead).
3. BILDER per story saknas helt. OBS: pipelinen HAR redan bild-URL:er per story i
   `pipeline/output/images/2026-25.json` (fält `image_url`), men de tappas bort —
   `write.py` skickar bild i prompt-kontexten men emit:ar inget image-fält i YAML,
   och mallen renderar ingen bild. Att göra: (a) write.py emit:ar image per story,
   (b) issue.js renderar bild, (c) backfilla content/2026-25.md med image_url ur
   pipeline-outputen. Snygg fallback krävs (många käll-URL:er blir 404 över tid).
4. "Läs mer" länkar i dag till hela numret-sidan (visar all text). Ändra till INLINE-
   expansion bara under den story man klickar på (storyns body finns som `s.body`).
5. Lägg till "Läs mindre" (toggle). Sajten har INGEN JavaScript i dag — lägg till en
   liten vanilla-JS-snutt (base.js eller separat fil kopierad från static/).

**Arbetssätt:** använd skill:en frontend-design för estetiken. Bygg med `node build.js`,
verifiera i public/ (framsida + permalänk). Ny branch, commit per logisk del.

---

## 2026-06-18 — Steg 7 byggt + full pipeline-test

[... tidigare loggar ...]

---

## 2026-06-18 — UI- och innehållsöversyn (Claude Code, Opus 4.8)

### Uppdrag
Arbetsorder /tmp/claude-ai-bladet-ui.md: fixa buggar, bygg ut framsidan med ingresser, längre artiklar, bättre visuell hierarki. Ordning: Block 1 → 4 → 6 direkt; Block 2 & 3 efter avstämning.

### Block 1 — Buggar
- "Nattupplagan": hårdkodad placeholder i mastheaden (base.js) — bedömd som bugg, borttagen. Visar nu bara "Vecka N · ÅÅÅÅ".
- "Invalid Date": redan åtgärdat av tidigare commit (fix: normalize date) — verifierat live + i build.
- Kategoriribban: bytte separator till sajtens standard " · " för tydligare avgränsning.

### Block 4 — Visuell hierarki
- Sekundära stories: rubrik länkar till numret + konsekvent "Läs mer →".
- Kortnytt: redan egen bakgrund/accent-kant — ingen ändring.

### Block 6 — Redundans
- Tog bort dubbel-CTA:n "Läs hela Vecka N", behöll bara "Bläddra i arkivet".

### Block 2 — Ingresser (separat fält, inte avklippt brödtext)
- write.py: nytt ingress-fält per story (40–60 ord) + redaktionell regel #9.
- issue.js + style.css: renderar ingress på framsida och permalänk.

### Block 3 — Artikellängd (200–300 ord, Sverige/EU villkorlig)
- write.py: regel #10 — 200–300 ord/story, 3-delsstruktur.
- issue.js: brödtext styckeindelad på permalänken.
- Hand-expanderade inte befintligt nummer (skulle kräva fakta utöver research).

### Analys-röst
- write.py: regel #11 + nytt lead.analysis-fält (50–70 ord, "AI-Bladets analys").
- issue.js + style.css: `<aside class="lead-analysis">`-box på toppstoryn.

### validate.py — integration
- DeepSeek-valideringen faktagranskar nu även ingresser och lead.analysis.
- SE/EU-detektorn läser ingresser.
- build.js + issue.js: wordcount/lästid inkluderar nya fält (~2 → ~4 min).

### Innehåll (v.25)
- Backfillade 5 ingresser + analys-box (kondensering av befintliga brödtexter).
- Tog bort stale content/2026-26.md.
- Byggde om public/.

### Commits (branch ui-fixes-block1-4-6, 6 st)
1. 3275c2e Block 1/4/6
2. f9514d9 Block 2 — ingresser
3. 0579893 Block 3 — längre stories
4. 0932505 Analys-box
5. af48db7 validate.py + wordcount
6. 965135a Veckans innehåll + byggd sajt

### Leverans
- PR #1 "UI fixes block1 4 6" → mergad till main av Anton.
- Live verifierat: 5 ingresser + analys-box synliga, "Nattupplagan" borta. Deploy ~15 s.

### Beslut / noteringar
- Ny gren skapades (arbetet startade på main).
- pipeline/ (utom write.py/validate.py) + loggbok.md otrackade i git.
- gh-CLI ogiltig GH_TOKEN; git push via separata credentials, PR skapad manuellt.

### Parkerat
- Block 5 — "I korthet"-box (key_points: [...]) per story. Ej påbörjad.

### Vad som gjordes
- Steg 7 (validering) byggdes — DeepSeek V4 Pro verifierar fakta mot research-briefs
- JSON-parsning fixad i validate.py och dedup.py (hanterar ```json-kodblock)
- Stale 2026-26.md rensad (validate valde fel fil pga alfabetisk sortering)
- Full pipeline kördes 2 gånger — alla 7 steg OK

### Resultat
- 766 kandidater → 566 kluster → 100 AI-scoreade → 15 researchade → 5 stories skrivna
- Validering: 60% pass-rate, FLAGGED — fångade att Sonnet hallucinerade "Grok 4.1"
- Kostnad: ~$0.10/körning
- Tid: ~2 minuter från kandidater till svensk tidningstext

### Beslut
- Anton: OpenRouter/Claude får ENDAST användas till AI-Bladet steg 6. Hård regel i SOUL.md.
- Nästa: cron, Cloudflare deploy, eller valideringströskel-justering

### Pipeline-kommando
```bash
cd ~/ai-bladet/pipeline && \
rm -f seen.db && \
python collect.py && python dedup.py && python score.py && \
python research.py --limit 15 && python images.py && \
python write.py && python validate.py
```

### Kända issues
- Grok 4.1-hallucination — Sonnet hittar på modellnamn som inte finns i research
- "122 dagar Colossus" — samma problem, siffror som inte stöds
- URL-koll: 1/6 levande — de flesta research-källor är 404 över tid
- VentureBeat RSS ger encoding-varning (harmlös)

## 2026-06-18 — Hallucination-fix via Claude Code (Opus 4.8)

### Vad som gjordes
- Summary fixad: "OpenAI förbereder sig för börsen" → "OpenAI har lämnat in ett S-1-utkast till SEC"
- Claude (Opus 4.8) analyserade valideringsresultatet + research-datan
- Summaryn var den ENDA verkliga hallucinationen

### Insikt: valideringens false positives
DeepSeek valideringen flaggade 3 saker, men bara 1 var en verklig hallucination:
1. **Grok 4.1** — Falsk positiv. Research har en egen story från `x.ai/news/grok-4-1` som bekräftar ALL data (1483 Elo, 31 poäng marginal)
2. **122 dagar Colossus** — Falsk positiv. Series C-briefen har `"122 dagar"` under numbers
3. **Summary "förbereder sig för börsen"** — Rätt flaggad. Research säger "inget beslut om tidpunkt"

### Root cause
Validate.py trunkerar research-briefs till 300 tecken i prompten. DeepSeek får inte se hela briefen inklusive numbers/key_facts, så den flaggar legitima claims som hallucinationer.

### Fix
Summaryn är den enda ändringen. Grok 4.1 och 122 dagar står kvar — de är korrekta.

## 2026-06-18 — Valideringsfix: full research-context

### Problem
Valideringen trunkerade research-briefs till 300 tecken (bara summary), ignorerade key_facts och numbers. Detta orsakade false positives: Grok 4.1 och 122 dagar flaggades som hallucinationer trots att de var korrekt källbelagda.

### Fix
1. `research_ctx` inkluderar nu: summary(500ch) + key_facts(8st) + numbers(8st) + sources(3st) + URL
2. Trunkeringsgräns: 3000 → 18000 tecken
3. Research stories begränsat till 10 (matchar write.py)
4. DeepSeek max_tokens: 1000 → 2000

### Resultat
- False positives borta — Grok 4.1 och 122 dagar valideras korrekt
- Pass-rate: 75%, enbart tolknings-flaggor kvar

## 2026-06-18 — Antons feedback: 7 redaktionella regler implementerade

### Ändrade filer

**write.py** — SYSTEM_PROMPT helt omskriven med 7 regler:
1. Dateringskrav: endast 7 dagar, äldre kräver ny vinkel
2. Inga dubletter: lead ≠ sektion
3. Attribuera prestandasiffror: "enligt Google", "xAI uppger"
4. Kvalitativa skiften > inkrementella släpp
5. Svensk/EU-vinkel i minst en story
6. Teasern får inte ljuga
7. Källhänvisning: allt ska spåras till research

**research.py** — source_date lagt till i fact_brief-strukturen

**validate.py** — datakontroll (#5) + attribueringskontroll (#6) tillagda

### Ej implementerat (kräver större ombyggnad)
- Automatisk dateringsbonus i scoring (kräver source_date i alla briefs först)

## 2026-06-18 — Retry-loop för validering

### Vad som gjordes
- write.py: `--feedback`-flagga — accepterar valideringsfel för rättning
- run_weekly.sh: Retry-loop med 3 försök
  - Om validate FAIL → extraherar issues → skickar till write.py --feedback
  - Sonnet får specifika fel att åtgärda
  - Max 3 försök totalt, sen stop
- Hårda checks (dublett, SE/EU) inkluderas i feedbacken
- Syntax verifierad: OK

### Flow
Pipeline → write → validate → PASS? → build → deploy
                              → FAIL? → feedback → write (retry 2) → validate → ...
                              → FAIL x3? → STOP + notis till Anton
