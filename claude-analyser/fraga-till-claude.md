# AI-Bladet — publiceringsklarering

Hej Claude! Du byggde arkitekturen för AI-Bladet (veckovis AI-nyhetssajt, custom Node build.js + Cloudflare Pages). Siten är byggd och jag har kollat preview — ser bra ut.

Innan vi trycker på publicera vill jag ha dina tankar om prioriteringslistan. Vad är rimligt att fixa nu vs sen? Något jag missat?

## Demo-läge just nu
- ~/ai-bladet/ med content/2026-25.md (demo), build.js, templates, style.css
- public/ fullt genererad och serveras via cloudflare tunnel (trycloudflare.com)
- Inget git-repo än, ingen Cloudflare Pages-deploy
- Inget skarpt innehåll — bara demo-text

## Anton föreslår denna prio-ordning

### Måsten (blockerar publicering)
1. **Fonts** — Archivo + Fraunces + Source Sans 3 self-hostade. Utan dem ser sidan generisk ut.
2. **Favicon** — enkel röd "AI"-ruta för v1.
3. **Git-repo + Cloudflare Pages** — behövs för riktig deploy med cron → push → live.
4. **Mobilverifiering** — CSS har media queries men inte systematiskt testad på riktig telefon.

### Borde fixas (inte blockerande men pinsamt utan)
5. **Riktigt innehåll** — demo är placeholder. Vecka 26 (22–28 juni) kan bli första skarpa numret.
6. **Om-sidan** — placeholder-text, behöver Antons röst.
7. **Footer** — Source-länkar, RSS, "Nästa nummer söndag".

### Kan vänta
8. **Domän aibladet.se**
9. **OG-bilder**
10. **Nyhetsbrev/prenumeration**

## Frågor till dig
1. Håller du med om prio-ordningen? Något jag satt för högt eller lågt?
2. Något jag missat som borde vara med?
3. Har du nån idé om hur vi kan self-hosta fonts snyggt utan Google Fonts?
4. Cloudflare Pages — är det git push-triggerad deploy eller behöver vi nån annan mekanism?
5. När är en bra tidpunkt att generera första skarpa numret Vecka 26 — och hur ska det skapas? Manuellt första gången eller redan nu bygga cron-prompten?

Tack!
