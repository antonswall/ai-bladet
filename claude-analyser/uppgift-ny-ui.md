# AI-Bladet — ny UI från scratch

Du ska designa en helt ny frontend för AI-Bladet (svensk AI-nyhetssajt, veckovis). Använd din `frontend-design` skill.

## Projektkontext
- AI-Bladet = veckotidning om AI, ny utgåva varje söndag
- Statisk sajt byggd med `node build.js` → genererar `public/`
- Innehåll kommer från markdown-filer med YAML-frontmatter (lead, stories[], briefs[], categories, sources)
- Cloudflare Pages deploy
- Layout ska kännas som en tidning, inte en blogg

## Uppgift
Designa en helt ny UI från grunden. Du får fria händer — inga tidigare designbeslut gäller. Välj ny palett, ny typografi, ny layout, nytt allt.

Det enda jag vill behålla: namnet AI-Bladet och strukturen (förstasida med lead+grid+briefs, arkiv, om-sida, RSS).

## Output
1. Skriv en helt ny `style.css` med `@font-face` för self-hostade fonter i `/fonts/`
2. Uppdatera `templates/base.js`, `templates/issue.js`, `templates/archive.js`, `templates/about.js`
3. Använd dina egna fonter — specificera vilka Google Fonts att ladda ner (jag laddar ner dem efteråt)
4. Inkludera favicon-instruktioner (enkel SVG-ruta räcker)
5. Inga bilder i v1

## Arbeta i
~/ai-bladet/

## Viktigt
- Ladda och använd din `frontend-design` skill
- LÄS de befintliga filerna först så du förstår datamodellen (build.js, content/*.md)
- Skriv över befintliga templates/ och static/style.css
- Kör `node build.js` efteråt för att verifiera
- Gör allt i en körning — fråga inte om lov för något
