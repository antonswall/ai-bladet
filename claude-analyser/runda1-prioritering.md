# AI-Bladet — mina tankar om prio-ordningen

Jag tittade inte bara på din lista — jag öppnade `build.js`, `templates/base.js`, `style.css` och `content/2026-25.md`. Det ändrar några av svaren, så jag börjar där.

## Vad koden faktiskt säger (grundar resten)

- **Fonts:** `style.css` refererar `Archivo` och `Fraunces`, men det finns **ingen `@font-face`** och mapparna `public/fonts/` + `static/fonts/` är **tomma**. Just nu renderas allt i fallback (Georgia/system-sans). Dessutom: **Source Sans 3 nämns inte alls i CSS** — den finns i din plan men inte i koden. Så "fonts" är mer jobb än "släng in filerna", och du måste bestämma om Source Sans 3 ska in eller strykas.
- **OG-taggar finns redan.** `base.js` sätter `og:title`, `og:description`, `og:type`, `og:locale` och `twitter:card`. Det som saknas är bara **og:image**. Det betyder att "OG-bilder = kan vänta" är *helt rätt prioriterat* — länkdelning funkar redan, bara utan tumnagel.
- **RSS, sitemap och robots.txt genereras redan** av `build.js`, och RSS är länkad i `<head>` och nav. Footer-punkten "RSS" är alltså till hälften klar.
- **Favicon saknas** — ingen `<link rel="icon">` i `base.js`. Bekräftat, men trivialt.
- **Hårdkodad domän:** `build.js` skriver `https://aibladet.se/` rakt in i `feed.xml` och `sitemap.xml`. Den domänen äger/deployar du inte än. Soft-launchar du på `*.pages.dev` eller trycloudflare så pekar din RSS och sitemap på fel URL. Det här är en riktig bugg, inte kosmetik (se "missat" nedan).

## Håller jag med om ordningen? Mestadels — med ett stort undantag

**"Riktigt innehåll" (#5) är inte ett "borde", det är måste #1.**
Det här är en nyhetstidning. Att publicera med demo-text är inte "pinsamt" — det är meningslöst och aktivt skadligt för varumärket. Allt annat på listan (fonts, favicon, mobil) är polish på en sida som inte har något att säga. Flytta upp den till toppen av "måsten".

**Git + Cloudflare Pages (#3) är egentligen det tekniska fundamentet — gör det först.**
Det är din faktiska publiceringsmekanism (cron → push → live). Innehåll, fonts och allt annat blir bara "live" genom den. Sätt upp den tidigt så du deployar på riktigt under hela resten av arbetet istället för att jaga en trycloudflare-tunnel.

Resten av "måsten" håller jag med om:
- **Fonts** — rimligt högt eftersom det definierar brandet och är billigt *när* filerna väl är på plats. Men se ovan: det är inte gjort, det är inte ens påbörjat i CSS.
- **Mobilverifiering** — behåll som måste. Merparten av nyhetstrafik är mobil; en tidning som ser trasig ut på telefon är värre än en utan favicon.
- **Favicon** — degradera mentalt till "trevligt", men det tar 5 min så gör det ändå.

### Min omsorterade lista

**Måsten (blockerar publicering)**
1. Riktigt innehåll (vecka 26) — *uppflyttad*
2. Git-repo + Cloudflare Pages (fundamentet — gör tekniskt först)
3. Parametrisera bas-URL i `build.js` (annars fel i RSS/sitemap — se missat)
4. Fonts (self-hostade, @font-face saknas helt idag)
5. Mobilverifiering på riktig telefon

**Borde fixas**
6. Om-sidan (din röst)
7. Footer-länkar / källor / "Nästa nummer söndag"
8. Favicon
9. Redaktionell transparens + källhantering (se nedan — viktigare än det låter)
10. Cron-felhantering / larm

**Kan vänta**
11. Domän aibladet.se
12. OG-bilder (taggarna finns redan)
13. Analytics (gärna Cloudflare Web Analytics — gratis, privacy-vänligt)
14. Nyhetsbrev/prenumeration

## Vad du har missat

1. **Bas-URL är hårdkodad till en domän du inte har.** `feed.xml`/`sitemap.xml` pekar på `aibladet.se`. Fixa genom att läsa bas-URL från en env-variabel (`SITE_URL`) i `build.js` med fallback till `*.pages.dev`. Liten ändring, men annars blir feed/sitemap fel vid soft-launch — och feeds cachas hos läsare.
2. **Redaktionell trovärdighet är din största risk, inte typografin.** En AI-genererad nyhetssajt lever och dör på källhantering och faktagranskning. Din frontmatter har `sources: 28` — men *visas* och *länkas* källorna? Hallucinerade fakta eller påhittade citat sänker projektet snabbare än en generisk font. Footern säger redan "automatiserad nyhetstjänst" — bra disclosure, behåll och var tydlig.
3. **Utgivningsbevis / ansvarig utgivare.** Du kallar det "Sveriges veckotidning". I svensk presskontext är utgivningsbevis frivilligt men ger grundlagsskydd och rätten att kalla sig tidning. Minimum innan publik launch: kontaktuppgifter och vem som ansvarar för innehållet. Värt att kolla upp.
4. **Felhantering i cron-pipelinen.** Vad händer om bygget eller pushen failar en söndag morgon? Utan larm publicerar du tyst antingen skräp eller ingenting. Lägg till en notis (mail/Slack/webhook) vid fel innan du litar på automationen.
5. **404-sida.** Liten men hör till en "riktig" sajt.
6. **JSON-LD `NewsArticle`** på issue-sidorna. `base.js` stödjer redan `jsonLd`-parametern — skickas den in? Billig SEO-vinst för en nyhetssajt.

## Svar på dina frågor

**1. Prio-ordningen?** Se ovan. Enda stora felet: innehåll ligger för lågt. Git+Pages bör göras tekniskt först. Du har faktiskt prioriterat OG-bilder *rätt* lågt eftersom taggarna redan finns.

**2. Missat?** Bas-URL-parametriseringen, redaktionell transparens/källhantering, utgivningsbevis, cron-felhantering, analytics. Den viktigaste är källhantering — den skyddar varumärket mer än fonts.

**3. Self-hosta fonts snyggt utan Google Fonts?**
- Både **Archivo och Fraunces är open source (OFL) variabla fonts**. Hämta woff2 från deras GitHub-repon (eller via `google-webfonts-helper`/`fontsource`). Variabel font = **en fil per familj** för alla vikter → mindre och snyggare än att ladda 4 statiska vikter.
- **Subsetta** till `latin` + `latin-ext` (du behöver åäö) — sparar mycket. `glyphhanger` eller fontsources färdiga subset duger.
- Lägg `@font-face` i `style.css` med `font-display: swap` och **preload** de 1–2 viktigaste i `base.js` `<head>` (`<link rel="preload" as="font" type="font/woff2" crossorigin>`).
- **Bestäm Source Sans 3-frågan nu:** den finns i planen men inte i CSS. Antingen lägg in den som brödtext-font eller stryk den ur listan så du inte laddar något du inte använder.
- Bonus: self-hostade fonts = inga tredjepartsanrop till Google = enklare GDPR-story. Bra för en svensk publikation.

**4. Cloudflare Pages — git push eller annan mekanism?**
Ja, **git-push-triggad deploy är standard och det jag rekommenderar.** Koppla repot till Pages; varje push till produktionsgrenen kör build-kommandot (`node build.js`) och deployar `public/`. Det ger dig historik och rollback gratis.
- Alternativ: `wrangler pages deploy public/` direkt utan git — funkar men du tappar historiken.
- För cron: enklast är **GitHub Actions på schema** → kör `build.js` → committa/pusha det nya numret → Pages auto-deployar. Alternativt låter du cron-jobbet köra `wrangler` direkt. Jag skulle ta git-push-modellen.

**5. När och hur för första skarpa numret (vecka 26)?**
Idag är torsdag 18 juni. Vecka 26 = 22–28 juni, söndag = **28 juni**.
- **Gör det första numret manuellt (eller halvautomatiskt).** Kör pipelinen för hand en gång: sätt den redaktionella ribban, se vad som faktiskt blir bra, fånga felen. **Bygg inte cron-prompten först** — du vet inte vad den ska producera förrän du gjort ett nummer du är nöjd med.
- **Reverse-engineera cron-prompten** från det manuella numret. Då blir prompten konkret istället för gissad.
- **Tidpunkt:** generera innehållet ett par dagar före söndag (t.ex. fre 26/27 juni) så du hinner redigera och faktagranska innan publicering söndag 28/6. Soft-launcha gärna på `*.pages.dev` innan domänen är på plats.

---

**TL;DR:** Sätt upp git+Pages först (fundamentet), gör ett riktigt vecka 26-nummer manuellt (det är ett måste, inte ett borde), fixa den hårdkodade bas-URL:en, och lägg lika mycket omsorg på källhantering/transparens som på fonts. Fonts är inte påbörjade i CSS — räkna med lite mer jobb där än "släng in filerna".
