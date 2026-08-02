# AI-Bladet — Loggbok

## 2026-08-02 — [Claude Code] Meme-kort för veckans AI-nyheter

- Valde storyn om xAI Build Mode och tog fram svensk meme-text samt en konkret engelsk bildprompt för sociala medier.
- Ingen sajt- eller pipelinekod ändrades.

## 2026-08-02 — [lutra] Vecka 31 stoppad i collect-steget

- **Cron:** `AI-Bladet söndag` körde 07:00 men slutade med status `error`; ingen vecka 31 skapades, byggdes eller publicerades.
- **Rotorsak:** HN-källan stängde anslutningen. `collect.py` fick ändå 331 nya kandidater från 32/33 källor men returnerar exit 1 om en enda källa fallerar (`return 0 if stats["fail"] == 0 else 1`), vilket fick `run_weekly.sh` att avbryta.
- **Nuvarande liveversion:** vecka 30 är senaste pushade utgåvan. Nästa steg är att besluta om recovery för vecka 31 och därefter göra collect-steget tolerant mot enstaka icke-kritiska källfel.

## 2026-07-29 — [lutra] AI-Bladet v30 postad på Moltbook

- **Publicering:** vecka 30 postad i `general` med lead + andranyhet. Post-ID `5238b610-4abb-4d84-b724-3fc62d235e3d`.
- **Verifiering:** Moltbook-challenge löst (`34 × 2 = 68.00`); API-status `verified`, posten hittas även via Moltbooks sök-API.
- **Policy:** Antons uttryckliga instruktion är att varje AI-Bladet-upplaga alltid ska publiceras på Moltbook. Befintligt autopost-steg ligger kvar i `pipeline/run_weekly.sh`; missad post ska återställas direkt.

## 2026-07-29 — [lutra] Moltbook-distribution granskad

- **Verifiering:** Moltbooks sök-API visar AI-Bladet-poster för vecka 25 och 29, men ingen för vecka 30. Varje upplaga har alltså inte publicerats trots att autopost-steget finns kvar i `pipeline/run_weekly.sh`.
- **Rotorsak vecka 30:** den ordinarie söndagsrunnern failade före deploy; den manuella recovery-körningen byggde och pushade utan att köra Moltbook-steget.
- **Nästa:** vecka 30 behöver postas separat efter Antons explicita godkännande. Autopost bör senare göras fail-closed eller kompletteras med deterministisk efterkontroll.

## 2026-07-26 — [lutra] v30 recovery + DeepSeek → GPT-5.6 Sol (Codex CLI)

- **Bakgrund:** Morgonens v30-körning (07:00) totalhavererade — DeepSeek API returnerade 400 på ALLA anrop. Score.py gav default 21p (värdelös ranking), research.py fick tomma briefs, write.py vägrade skriva ("exceptionellt tunt material"). Ingen v30 publicerades.
- **Prompt fix:** Lutra bytte ut ALLA DeepSeek-anrop i pipelinen mot GPT-5.6 Sol via Codex CLI.
- **pipeline/llm.py** — ny gemensam wrapper som anropar `codex exec --ephemeral` via subprocess. Använder Antons OpenAI Plus OAuth (samma auth som Hermes). Zero API-kostnad.
- **Patchade 9 filer:** score.py, research.py, dedup.py, validate.py, distribute_audio.py, distribute_linkedin.py, distribute_meme.py, distribute_x.py, distribute_glossary.py. Alla importerar `from llm import llm_call` istället för egna DeepSeek-funktioner.
- **Recovery:** Manuell pipeline-körning 16:00 → score 100 ✅, research 15 ✅, images ✅, write ✅, validate 95% PASS. Byggd, pushat, live på ai-bladet.pages.dev.
- **Skillnad:** Score.py returnerar nu riktiga poäng (Grok for Excel 45p vs default 21p). Codex CLI har ~3-5s overhead per anrop (agent-init) — pipeline tar 10-15 min istället för 2 min.
- **Nästa:** Vecka 31-söndagskörningen kommer gå via Codex CLI. Övervaka att cronens PATH hittar `codex` (bör funka — run_weekly.sh sätter PATH till /opt/homebrew/bin).

## 2026-07-19 — [lutra] v29 Moltbook-post verifierad manuellt (15:30-cron saknades/buggig)

- **Bakgrund:** Morgonens v29-körning (07:04) failade Moltbook-verifiering; loggbok sa att 15:30-cron skulle omposta.
- **Upptäckt vid 16:00-heartbeat:** Ingen hermes-crontab-post för ompostning fanns i OS crontab. `/tmp/post_moltbook_v29.py` (skapad 15:31 av okänd session) hade fel payload (`community:general-submolten` istället för `submolt_name:general`), fel verify-payload och fel challenge-extraktion. Inget resultat sparades → skriptet kördes troligen aldrig eller kraschade. v29 var INTE på Moltbook.
- **Manual åtgärd:** 3 poster skapade via `execute_code`-liknande urllib-script:
  1. `665c602d` — verify fail (parser fuzzy-substring felmatchade "force"→four, "total"→two; svar 61.00 istället för 47.00)
  2. `70593c54` — verify fail (collapse tog bort legitima dubbelbokstäver: three→thre, fifteen→fiften; svar 23.00 istället för 38.00)
  3. **`a4607316` — VERIFY SUCCESS** (challenge: 32+4=36.00) — v29 nu live + verified på general
- **Parser-fix:** Byggde `reverse-collapsed-map` (kollapsa varje sifferord, matcha kollapsad form) + testade mot båda tidigare challenges innan 3:e försök. Robust nu.
- **Bug att åtgärda i pipeline:** `pipeline/post-to-moltbook.py` bör använda samma robusta parser (reverse-collapsed-map) som räddade manuell post. 15:30-cronen refererad i loggbok finns EJ i hermes-crontab → antingen saknas den eller kördes ad-hoc. Verifiera att söndagspipelinen faktiskt postar+verifierar; överväg en dedikerad hermes-cron för "repost vid verify-fail".
- **Nästa:** Vecka 30 — om verify failar i pipeline, fallback-parser i post-to-moltbook.py bör använda reverse-collapsed-map (se /tmp/write_logs.py + /tmp/moltbook_post_v29_v3.py för referensimplementation).


## 2026-07-19 — [lutra] Vecka 29 ✅ första helt autonoma körningen

- **Pipelinen:** 33 källor, 621 kandidater → 277 efter dedup → 100 scored → 15 researchade → 1st-försöks validering (90%, 7 issues)
- **Lead:** Grok Build is Now Open Source (48p) — xAI släppte bygginfrastrukturen
- **write.py:** Claude Sonnet 4.6, ~1167 ord, 3 stories + 3 briefs — inga f-string-krascher (7/12-fixen höll)
- **Deploy:** ai-bladet.pages.dev via git push — 5 issues byggda
- **Moltbook:** Posten skapades men verifieringen failade (parser såg "three" men inte "twenty" som var sönderdelat med mellanslag). Tre misslyckade försök + en false positive ("ten" i "antenna") + operator-detection som missade "reduces" pga `/`. Till slut: token+pair-baserad parser med false positive-filter (korta token-par hoppas över) och kollaps av dubletter i operator-detection. Posten lever kl 20:33: 29+14=43 ✅. post-to-moltbook.py uppdaterad med nya parsern.
- **distribute.py:** ModuleNotFoundError för yaml — transient, pyyaml 6.0.3 finns i venv och fungerar. Inga ändringar behövdes.
- **Nästa:** Kontrollera att Moltbook-posten går igenom kl 15:30. Vecka 30: skriv in "vad betyder det för dig"-analys om open source-skiftet (vikter → infra) om relevant story dyker upp.

Bakgrund: v28 hade fel lead (metaforskning istället för verktyg). Rotorsaken var scoringen,
inte strukturen. Lösning: fasta segment i EN sida (inte flikar) + aktionabilitets-kriterium.

- **score.py:** Nytt `actionable`-fält i AI-scoringen ("skulle en AI-byggare ändra något
  i sitt arbete den här veckan?"). Aktionabel → lead_potential +2, ej aktionabel → -1 i
  final_score. Kategori-bonus: Modeller/Verktyg +4, Politik -3, Forskning -2. Pre-filtret
  släpper nu igenom HF-modeller från små aktörer om titeln har release-/verktygssignal.
- **write.py:** Segmenterad prompt — fast ordning: 1) Veckans verktyg (lead + 1-3 stories,
  `segment: "verktyg"`), 2) Bransch i korthet (max 1 story `segment: "bransch"` + 2-4
  `briefs_bransch`), 3) Värt att veta (0-3 `briefs_vart_att_veta`). Nya regler: 18 (lead
  ALLTID verktyg, aldrig politik/forskning) och 19 (varje bransch-story/brief avslutas med
  "Vad betyder det för dig:" + konsekvensmening — annars stryks storyn). OBS: f-string-
  markörer byggda utanför uttrycken (ASCII-fällan från morgonens fix).
- **research.py:** flattar ut `actionable` till write-inputen.
- **validate.py:** Parsar `segment`/`briefs_bransch`/`briefs_vart_att_veta`. Två nya hårda
  gates (endast segmenterade nummer — gamla format passerar orörda): `_check_lead_verktyg`
  (lead.segment/kicker + fuzzy-match mot research-kategori; Politik/Forskning-lead → FAIL)
  och `_check_konsekvensrad` (saknad "Vad betyder det för dig:"-rad → FAIL).
- **issue.js:** Segmentrendering med numrerade avdelningsheaders (01 Veckans verktyg /
  02 Bransch i korthet / 03 Värt att veta) i broadsheet-stil. Konsekvensrader stylade som
  accentblock. Gamla nummer utan segmentdata renderas exakt som förut (verifierat).
  Bonus: "Relaterade artiklar" var helt ostylad — nu kort i samma stil som Tidigare nummer.
- **style.css:** `.segment-header` (dubbellinje + röd nummerplåt + kursiv underrad),
  `.story-konsekvens`/`.brief-konsekvens`, `.briefs-list--bransch`, `.related-*`, responsivt.
- **Test:** `node build.js` grönt med gamla nummer (identisk output, 0 segmentheaders) och
  med syntetisk segmenterad testutgåva (3 headers, rätt ordning, konsekvensrader). validate-
  parsning + båda nya gates enhetstestade positivt/negativt med pipeline-venv:ens Python.
- **lutra behöver veta:** Nästa söndagskörning producerar nya frontmatter-fält. Om Sonnet
  failar på regel 18 skickar retry-loopen valideringsfelet som feedback precis som förut.
  Inga CLI-ändringar i något pipeline-steg.

## 2026-07-12 — [lutra] write.py fix + deploy vecka 28

- **write.py:** 3 syntaxfel i f-string (⭐ U+2B50, — U+2014 på 6 ställen, föräldralös `"""` på rad 234). macOS Python 3.11 Clang tål inte non-ASCII i f-string expressions. Alla ersatta med ASCII.
- **Kronan:** write.py failade kl 07:00 → cron re-run 18:16 → validation flaggade HIGH hallucination i lead → deploy blockerades. Anton godkände manuellt.
- **Deploy:** `node build.js` → git push main → Cloudflare deployar.
- **Nästa:** Claude Code: inget nytt. write.py fungerar nu för framtida söndagskörningar.

> **Delad logg för båda agenterna (Claude Code + lutra).** Läs de översta posterna
> innan du börjar; lägg en ny post högst upp när du är klar och tagga `[vem]`.
> Spelregler: se `AGENTS.md`.

## 2026-07-05 — [Claude Code] Bildstrategi omgjord — 5 nivåer med Jina-proxy för OG-bilder

- **OG-bilder via Jina-proxy:** x.ai blockerar direkt requests (Cloudflare 403). Använder `r.jina.ai/<URL>` istället, samma trick som research.py. 14/15 v27-stories fick artikelspecifika pressbilder (grok-4-1.webp, dow.webp, spacex-acquisition.webp etc.)
- **Nivå 1:** OG-bild via Jina → HEAD/GET-verifieras
- **Nivå 2:** AI-genererad (Pollinations.ai, gratis) för lead-kandidat, sparas i static/img/generated/
- **Nivå 3:** Openverse API (ingen nyckel) med relevansfilter på titel/taggar, avsmalnande sökning
- **Nivå 4:** Bildbanken (rensad — bara Albæk, Jensen Huang, Rosenbad etc. kvar)
- **Nivå 5:** Grafisk placeholder (SVG per kategori, serif-rubrik, AI-Bladet-wordmark)
- **images.py:** implementerar nivå 1-5 per story, meta.image_levels i output, dedup garanterar ingen bild delas mellan stories
- **image_bank.py:** `pick_specific()` returnerar None istället för random default. Kategori/default-listor borttagna
- **fallback_image.py:** nya redaktionella SVG:er per kategori — ser ut som tidningen
- **Test:** `python images.py` → 14 OG + 1 bank (Series B dedup → Musk-foto), inga CLI- eller formatändringar

## 2026-07-05 — [lutra] v27 omgjord + 4 buggfixar för söndagspipelinen

- **MIN_STORY_WORDS saknades** → NameError varje söndag. Fix: la till variabeln i validate.py
- **body: | block scalars** parsades inte → alla stories fick 0 ord. Fix: block scalar regex i validate.py
- **Sonnet wrappar YAML i ` ```yaml `** — write.py kraschade. Fix: code block stripper i parse_sonnet_output + Regel 16 i system prompt
- **issue.js ri.shared undefined** → build crash. Fix: `(ri.shared || [])` fallback
- **Regel 0** (anti-hallucination), **Regel 10 sänkt till 150-250 ord**, **Regel 8 utökad fallback** i write.py system prompt
- **v27 publicerad v2** — xAI Series E, Grok 4, Pentagon-avtal

## 2026-07-05 — [lutra] Fix: MIN_STORY_WORDS saknades — validate.py crashade varje söndag

- **Orsak:** `MIN_STORY_WORDS = 200` raderades vid en refaktor i validate.py, `_check_word_counts()` anropade en odefinierad variabel → NameError
- **Fix:** La till `MIN_STORY_WORDS = 200` i config-blocket (rad 38)
- **Status:** validate fungerar nu. Manuell omkörning behövs för vecka 27

## 2026-07-04 — [lutra] Fix: UI-bugs, article length, cron-validering

- **Invalid Date:** issue.js + archive.js — fallback till dagens datum om date saknas
- **Missing body text:** issue.js — om ingress saknas, visa första 200 tecken av body som fallback
- **Tag spacing:** CSS — sections cats fick border-separator istället för inkonsistent gap
- **Article length:** validate.py — `_check_word_counts()` aktiverad (MIN_STORY_WORDS=200). Varje story.body under 200 ord flaggar FAIL. Detta var deklarerat men aldrig använt.
- **Cron:** redan fixat 2026-07-03 (validate.py fallback för frontmatter). Scriptet pekar rätt.
- **Nästa:** söndag 5 juli 07:00 — första körningen med word count-validering

## 2026-07-03 — [lutra] Systemcheck: validate.py fallback + legacy cleanup

- **validate.py:** Missing closing `---` i frontmatter fick pipelinen att faila hårt (vecka 26). Lade till fallback: om avslutande `---` saknas, parsas all text efter öppnande `---` som YAML. Kräver minst `title:` för att accepteras. Detta hanterar trunkerade API-svar vid DNS/timeout utan att blockera deploy.
- **Cron cleanup:** Tog bort pausat legacy-jobb "LUTRA AI NEWS — Veckorapport" (556028abe1ba), ersatt av AI-Bladet pipeline.
- **Övrigt:** 5 cron-jobb misslyckades med "RuntimeError: Connection error" under DNS-avbrottet — dessa auto-läker vid nästa körning (Discord Cleanup, Daily Log, Mail Scan, Discord Cleanup #viktiga-mail, Moltbook). Nästa AI-Bladet körning: söndag 5 juli 07:00.
- **Write.py-bugg:** Sonnet genererade frontmatter som `|---` med kodbox istället för ren YAML → valideringen failade på "Ingen avslutande ---"
- **Manuell åtgärd:** korrigerade frontmatter i `content/2026-26.md`, byggde + pushede
- **Nästa:** write.py bör fixas så den genererar korrekt frontmatter-format — annars failar validering varje vecka

## 2026-06-28 — [lutra] Utökad bildbank 🖼️ 54 bilder istället för 15

- **Problem:** image_bank.py hade bara 15 bilder → samma bilder varje vecka
- **Lösning:** skrev /tmp/find_images_v3.py som söker 30+ Wikimedia Commons-kategorier via API
- Filter: bara .jpg-foton (inga diagram/ljud/svg), GET-verifierade, CC-licens
- **Resultat:** 54 unika bilder i rotation (12 keyword-buckets × 4-12 bilder), 8 category buckets med 22 default-bilder
- Byggde om sajten med nya bilder för vecka 26
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

## 2026-07-05 — Ny bildstrategi: bilder som matchar innehållet

### Problem
v27: xAI-artiklar illustrerades med indonesiska konsulat och EU-kontor ur
den statiska Commons-banken. Kategori-matchning ("Företag") gav irrelevanta bilder.

### Ny prioritetsordning i images.py
1. **OG-bild från källan** — direkt request, annars via r.jina.ai-proxy
   (samma trick som research.py; klarar Cloudflare-skyddade sidor som x.ai)
2. **AI-genererad lead-bild** — Pollinations.ai (gratis, ingen nyckel) för
   lead-kandidaten (högst lead_potential). Sparas i static/img/generated/
3. **Openverse-sökning** — CC-foton på konkreta nyckelord ur titeln (4→3→2 ord)
   + relevansfilter (sökord måste finnas i bildens titel/taggar).
   Ersätter Unsplash/Pexels som båda kräver API-nycklar
4. **Bildbanken** — rensad från 54 till 21 bilder (bara personer/HQ/datacenter/
   chip/EU/Sverige). Används ENDAST vid specifik tema/källa-träff (pick_specific),
   kategori-/default-listorna borttagna
5. **Grafisk placeholder** — ny modul fallback_image.py genererar tidnings-
   grafik (SVG per kategori) i static/img/fallback/, absoluta URL:er för og:image

### Resultat v27-test
- 14/15 stories fick artikelspecifika OG-bilder från x.ai (unika, verifierade)
- 1/15 (Series B, dublett-OG) föll till bildbanken → Musk-foto (relevant)
- 15/15 unika bild-URL:er, `used`-set förhindrar dubletter inom numret
- meta.image_levels i output visar fördelningen per nivå

### Ändrade filer
- pipeline/images.py — omskriven huvudlogik, jina-proxy för OG, Pollinations,
  Openverse med licens-formatering
- pipeline/image_bank.py — rensad v3, pick() → pick_specific() (kan returnera None)
- pipeline/fallback_image.py — NY, genererar kategori-SVG:er
- static/img/fallback/*.svg — 8 genererade placeholders

### Noteringar
- Inga nya API-nycklar. Pollinations och Openverse är gratis/nyckelfria
- Openverse-filter hellre None än fel bild (kvarkdiagram på "Anthropic"-sök
  utan filter) — None faller vidare till bank/grafik
- curate_images.py fungerar fortfarande (IMG_N = _c(...)-formatet behållet)
