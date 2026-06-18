# AI-Bladet — Analysrunda 2

Hej Claude! Jag har applicerat dina insikter från förra svaret. Här är vad jag gjort:

## Genomförda ändringar

1. **Parametriserad bas-URL** — `build.js` läser `SITE_URL` env var, default `https://aibladet.se`
2. **Self-hostade fonts** — Archivo, Fraunces, Source Sans 3 som woff2 i `static/fonts/` med `@font-face`-regler och `preload` i `<head>`
3. **Source Sans 3** som body-font (ersätter Archivo för brödtext)
4. **Favicon** — röd SVG med "AI"
5. **Vecka 26** — nytt demo-innehåll med GPT-5.5, AI Act, Ailingo, Copilot Agent Mode, DeepMind-hallucinationsmetod + 5 briefs
6. **404-sida** — genereras av `build.js` via `templates/404.js`
7. **JSON-LD NewsArticle** — redan implementerat i `issue.js`, bekräftat i output
8. **Källantal** — syns nu i lead-kickern ("VECKANS STÖRSTA · 31 källor")
9. **Footer** — uppdaterad med "Nästa nummer söndag · RSS"

## Vad jag INTE gjort än

- Utgivningsbevis (behöver din input)
- Analytics
- Domänregistrering
- OG-bilder
- Cron-felhantering/larm

## Nuvarande state

- 2 utgåvor byggda (Vecka 25 demo + Vecka 26)
- Bygget går igenom: `node build.js` → `2 utgåvor byggda, senaste: Vecka 26 2026`
- Siten servas via cloudflared tunnel på trycloudflare.com
- Fonts laddas från `static/fonts/` (totalt ~300KB för 3 woff2-filer)

## Frågor till dig

1. Granska den uppdaterade koden — vad har jag missat eller gjort fel?
2. Ge mig en konkret checklista på vad som återstår innan publik launch, prioriterat
3. Är det något i CSS:en som ser konstigt ut? (speciellt font-fallback, mobil-layout)
4. Räcker 2 utgåvor för att testa arkiv, RSS och prev/next, eller bör jag skapa en tredje?
5. Bör jag skapa `public/404.html` som Cloudflare Pages auto-använder, eller räcker det att den genereras av build.js? (Cloudflare Pages använder `404.html` i output-mappen automatiskt)

Skriv svaret till `/tmp/ai-bladet-analys2.md`
