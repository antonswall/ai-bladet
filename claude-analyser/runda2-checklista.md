# AI-Bladet — Analysrunda 2: kodgranskning + launch-checklista

Jag granskade den faktiska koden och byggde sajten (`SITE_URL=… node build.js`), läste den genererade outputen och jämförde mot källfilerna. Bra framsteg — men **rundans flaggskeppsändring (self-hostade fonts) är trasig och inte live**, plus två andra riktiga build-buggar. Detaljer nedan.

## TL;DR

- 🔴 **Fonterna laddas inte.** `@font-face` pekar på filnamn som inte finns → alla tre fonter 404:ar → sidan renderas fortfarande i fallback (system/Georgia). Exakt det du trodde du fixade.
- 🔴 **RSS-feeden har `<pubDate>Invalid Date</pubDate>` på båda numren.**
- 🔴 **`robots.txt` innehåller den literala texten `${SITE_URL}`.**
- 🟡 Archivo används som brödtext på vikt 400, men fontfilen har bara 600–900 → brödtext blir för fet när fonterna väl laddar.
- 🟡 Innehållet i vecka 26 är fortfarande **påhittat** men presenteras som nyheter med "31 källor" — den största varumärkesrisken.

---

## 1. Buggar jag hittade (severity-ordnat)

### 🔴 Bug 1 — `@font-face` pekar på filer som inte finns (KRITISK)
`style.css` rad 21/29/37 har src till Google-hashade filnamn:
```
/fonts/k3kPo8UDI-1M0wlSV9XAw6lQkqWY8Q82sIyfMRWOvQ.woff2      (Archivo)
/fonts/6NU78FyLNQOQZAnv9bYEvDiIdE9Ea92uemAk_WBq8U_9v0c2Wa0K9C1Zf9-V.woff2  (Fraunces)
/fonts/nwpStKy2OAdR1K-IwhWudF-R7w0QYsrd.woff2                 (Source Sans 3)
```
Men de faktiska filerna heter `Archivo.woff2`, `Fraunces.woff2`, `SourceSans3.woff2`.

**Effekt:** alla tre `@font-face` 404:ar → sidan visas i fallback-fonter. Hela "self-hostade fonts"-ändringen är icke-funktionell just nu.
**Orsak:** CSS:en är klistrad från Google Fonts genererade CSS utan att byta src till dina egna filnamn.
**Bonusproblem:** `preload` i `base.js` (rad 21–22) laddar `Archivo.woff2` + `Fraunces.woff2` — filer som finns men som CSS aldrig refererar → webbläsaren varnar "preloaded but not used" och slösar bandbredd. Och `SourceSans3.woff2` (din nya brödtextfont) varken preloadas eller laddas korrekt.
**Fix:** byt `@font-face` src till `/fonts/Archivo.woff2`, `/fonts/Fraunces.woff2`, `/fonts/SourceSans3.woff2`. Verifiera i DevTools → Network att alla tre svarar 200, och att å/ä/ö renderar.

### 🔴 Bug 2 — RSS `pubDate` = "Invalid Date" (båda numren)
Genererad `feed.xml`:
```xml
<pubDate>Invalid Date</pubDate>
```
**Orsak:** YAML/gray-matter tolkar `date: 2026-06-28` som ett **JS Date-objekt**, inte en sträng. I `build.js` rad 99 gör du `new Date(i.date + 'T09:00:00Z')` → Date-objektet stringifieras ("Sun Jun 28 2026 …") + `'T09:00:00Z'` → ogiltig sträng → `Invalid Date`. (Samma sak i JSON-LD bekräftar diagnosen: `datePublished` blev `2026-06-28T00:00:00.000Z`, dvs `date` var redan ett Date-objekt.)
**Effekt:** RSS-läsare kan inte sortera/visa datum; vissa feed-validatorer underkänner feeden. Trasig dag ett.
**Fix:** normalisera vid inläsning, t.ex. `const d = new Date(i.date);` och `d.toUTCString()`. Eller i build.js: `new Date(i.date).toUTCString()` rakt av (Date-objekt funkar direkt i `new Date()`).
**Latent samma bug:** `issue.js` rad 7, `new Date(date + 'T12:00:00')` — men `dateStr` används aldrig (död variabel). Antingen använd den (publiceringsdatum vore fint på sidan) eller städa bort den.

### 🔴 Bug 3 — `robots.txt` innehåller literal `${SITE_URL}`
Genererad `public/robots.txt`:
```
Sitemap: ${SITE_URL}/sitemap.xml
```
**Orsak:** `build.js` rad 118 använder enkla citattecken `'...'` istället för backticks, så template-interpolationen körs aldrig.
**Effekt:** crawlers hittar inte sitemap via robots (sitemap.xml går att nå direkt, men referensen är trasig).
**Fix:** byt raden till backticks.

### 🟡 Bug 4 — Archivo i brödtext på vikt 400, men fonten har bara 600–900
`@font-face` Archivo: `font-weight: 600 900`. Men CSS använder Archivo **utan viktangivelse (=400)** på `.lead-ingress`, `.story-body`, `.briefs-list li`, `.about-section p`. De ligger utanför fontens viktintervall → webbläsaren klampar till 600 (semibold) eller faux-renderar.
**Effekt:** ingress, story-brödtext, kortnytt och om-text blir tyngre än tänkt — när fonterna väl laddar (efter Bug 1).
**Orsak:** Source Sans 3 blev brödtextfont, men många block pekar fortfarande på Archivo.
**Fix:** bestäm hierarkin och var konsekvent — Fraunces = serif-rubriker, Archivo = UI/kickers (600+), Source Sans 3 = all brödtext (400–600). Flytta brödtext-blocken ovan till `'Source Sans 3'` (eller utöka Archivo-subsettet till att inkludera 400).

### 🟡 Innehållet är påhittat men presenteras som nyheter
Vecka 26 innehåller specifika, kontrollerbara påståenden — GPT-5.5-citat, "Ailingo tar in 200 Mkr ledd av EQT Ventures", "Copilot Agent Mode bokar möten", "DeepMind Semantic Consistency Scoring 90%", "Llama 4, 400 mdr parametrar" — märkt "31 källor". Det är fortfarande demo/fabrikat. Det här är precis trovärdighetsrisken jag flaggade förra rundan: en AI-sajt som publicerar plausibelt påhittade fakta med ett källantal är värre än ingen sajt. **Före launch måste innehållet vara verifierat, källhänvisat och faktagranskat.**

### Mindre / verifiera
- **Förstasidans canonical = `/v/2026/26/`, inte `/`** (`issue.js` rad 11 — ternaryn har dessutom identiska grenar). Det kanoniserar bort förstasidan till veckans permalänk. Försvarbart (undviker dubblett), men bekräfta att det är meningen — `/` indexeras då inte separat.
- **canonical/og är relativa, ingen `og:url`.** Google godtar relativ canonical, men absolut (via `SITE_URL`) är säkrare. `base.js` får inte `SITE_URL` idag — skicka in den om du vill ha absoluta URL:er.
- **Favicon:** `<text font-family="Archivo">` i SVG:n renderas med systemets fonter, inte din webbfont → "AI" blir i en fallback-sans. Funkar, men inte exakt brand-font. Ingen PNG/ICO-fallback (äldre Safari/pinned tabs). Litet.
- **Död kod:** `.page-404` i CSS (rad 285–287) används aldrig — `404.js` sätter inte klassen utan inline-stilar + `.page-title`. Använd klassen eller ta bort reglerna.
- **sitemap** saknar `<lastmod>` — liten SEO-nicety.

---

## 2. Konkret launch-checklista (prioriterad)

**🔴 Blockerar publik launch — i denna ordning**
1. Fixa `@font-face`-filnamn (Bug 1). Verifiera 200 i Network + att å/ä/ö renderar.
2. Fixa RSS `Invalid Date` (Bug 2) — annars går du live med trasig feed.
3. Fixa `robots.txt`-interpolationen (Bug 3).
4. Lös Archivo-vikten i brödtext (Bug 4) / lås typografihierarkin.
5. Ersätt demo med verifierat, källhänvisat innehåll — faktagranska varje påstående.
6. Mobilverifiering på riktig telefon (se §3).
7. Git-repo + Cloudflare Pages, med `SITE_URL` satt i build-env (annars hårdkodas `aibladet.se`).

**🟡 Borde före launch**
8. Namngiven ansvarig människa + tydlig AI-disclosure på Om-sidan (se §5).
9. Om-sidan: riktig text i din röst (fortfarande placeholder).
10. Absolut canonical + `og:url` via `SITE_URL`.
11. Cron-felhantering/larm innan du litar på automationen.

**🟢 Kan vänta**
12. Utgivningsbevis (se §5). 13. Analytics (Cloudflare Web Analytics — gratis, privacy-vänligt). 14. Domän. 15. OG-bilder. 16. Tredje testutgåva (§4). 17. Städa död kod.

---

## 3. CSS — font-fallback & mobil (fråga 3)

**Font-fallback:** stacken i sig är vettig (Source Sans 3 → -apple-system; Fraunces → Georgia; Archivo → sans-serif). Problemet är inte fallbacken utan att du *alltid* är i fallback just nu (Bug 1). När den är fixad, åtgärda Bug 4 så brödtexten inte blir för fet.

**Mobil (@max-width 768px ser i grunden rimlig ut), kolla på riktig telefon:**
- **`.bottom-nav` saknar `flex-wrap`.** Den är `display:flex` med `gap`, och mittetiketten är lång ("Vecka 26 2026 · 31 källor · ~X min") plus prev/next på sidorna → kan overflowa horisontellt på små skärmar. Lägg `flex-wrap: wrap`.
- **Drop cap** (`.lead-ingress::first-letter`, 48px på mobil, `float:left`) kan krocka/överlappa vid kort ingress. Verifiera.
- masthead 36px, body max-width 960 + padding 1rem — ok.

---

## 4. Räcker 2 utgåvor? (fråga 4)

Ja, för det mesta. Med 2 testas **båda riktningarna**: v26 visar prev→v25, v25 visar next→v26, arkivet listar två, RSS har två items. Det verifierar prev/next-rendering, arkiv och RSS.

Det enda 2 *inte* testar är **mittenfallet** där en enda permalänk visar både ← och → samtidigt. Skapa gärna en tredje (v24) för full täckning — inte blockerande. Och fixa Bug 2 först, annars "testar" du RSS med trasiga datum.

---

## 5. `public/404.html` på Cloudflare Pages (fråga 5)

**Ja, det räcker — och du är redan klar.** Cloudflare Pages använder automatiskt en `404.html` i **roten** av output-mappen för alla icke-matchande paths. `build.js` skriver den till `public/404.html` (rad 81), dvs exakt rätt plats. Du behöver inte göra något extra. (Verifierat: filen finns i output-roten, inte i en undermapp.) Enda uppstädningen: använd `.page-404`-klassen eller ta bort de döda CSS-reglerna.

---

## Utgivningsbevis (din input-fråga)

*(Jag är inte jurist — verifiera hos Mediemyndigheten.)*

- **Frivilligt.** Du får grundlagsskydd för en webbsajt (yttrandefrihetsgrundlagen, "databasregeln") genom att **ansöka om utgivningsbevis** hos Mediemyndigheten. Kostar en avgift och kräver att du utser en **ansvarig utgivare**.
- **Fördelar:** grundlagsskydd, källskydd, rätten att kalla dig periodisk skrift/tidning, och undantag från delar av GDPR för journalistisk verksamhet.
- **Ansvar:** ansvarig utgivare bär det juridiska ansvaret för allt publicerat. För en **AI-genererad** sajt är detta centralt — en **människa** måste stå som ansvarig och faktiskt kunna granska/stoppa innehåll. Du kan inte sätta "AI" som ansvarig utgivare.
- **Min rekommendation:** inte en launch-blocker juridiskt. Men eftersom du marknadsför det som "Sveriges veckotidning" *och* innehållet är AI-genererat, gör detta **före** publik launch: (a) en namngiven ansvarig människa, (b) tydlig disclosure om att innehållet är AI-genererat och hur det granskas. Ansök om utgivningsbevis när du vill ha grundlagsskydd/källskydd och kalla dig tidning på riktigt.

---

**Sammanfattning:** Strukturen är solid och nästan allt på din lista är på plats — men tre genererings-buggar gör att fonts, RSS och robots inte funkar i den byggda outputen, och innehållet är fortfarande fabrikat. Fixa Bug 1–3 (snabba), lås typografin (Bug 4), gör innehållet på riktigt, och sätt en namngiven ansvarig + AI-disclosure innan du trycker live.
