# AI-Bladet — Loggbok

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
