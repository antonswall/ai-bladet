# AI-Bladet — SEO-plan

> Analys och åtgärdsplan för de 6 SEO-punkterna.
> Inga API-nycklar, inga kostnader. Bara kodändringar i build.js + templates.

---

## Nulägesanalys

| Punkt | Status | Notering |
|-------|--------|----------|
| 1. Meta descriptions | 🟡 Delvis | Issue-sidor har unik meta via `summary`. Frontpage har generisk fallback. |
| 2. JSON-LD | 🟡 Tunt | `NewsArticle` finns men saknar `image`, `author`, `publisher`, `keywords` — Google kräver dessa för att visa stories i "news carousel" |
| 3. Titlar & rubrik-hierarki | 🟢 Bra | `<h1>` för lead, `<h2>` för sektioner. Frontpage-link i h1 är suboptimalt men accepterat |
| 4. Alt-text på bilder | 🟡 Delvis | Lead/story-bilder har korrekt alt. Tidigare-nummer-kort + arkivkort har `alt=""` (tomma) |
| 5. Interna länkar | 🟡 Delvis | Prev/next-navigation finns. Inga korsreferenser i brödtext (skulle kräva ändring i write.py) |
| 6. Sitemap + robots.txt | 🟢 Finns | robots.txt pekar redan till sitemap.xml. Sitemap saknar `lastmod`, `changefreq`, audio-sidor, ordbok |

---

## Åtgärder — per punkt, i prioritetsordning

### Punkt 6: Sitemap + robots.txt (redan 80% klart)

**Vad som saknas:**
- `lastmod` och `changefreq` per URL (Google prioriterar sidor med datum)
- Ordbokssidor, meme-sida, ljudfiler saknas i sitemap
- Sitemap bör inkludera även statiska sidor (arkiv, om, ordbok-index)

**Kodändring:** `build.js`, sitemap-sektionen (rad 109–119)

```javascript
// Lägg till lastmod + changefreq per URL
// Inkludera dynamiskt genererade sidor från public/ordbok/ och public/audio/
// Lägg till alla statiska undersidor
```

**Resultat:** Google hittar + indexerar alla sidor snabbare. Särskilt ordbokssidor.

---

### Punkt 2: JSON-LD (störst genomslag)

**Vad som saknas för Google News-visning:**
```json
{
  "@context": "https://schema.org",
  "@type": "NewsArticle",
  "headline": "...",                                          // ✅ finns
  "description": "...",                                       // ✅ finns
  "datePublished": "...",                                     // ✅ finns
  "image": "URL till lead-bild",                              // ❌ SAKNAS — Google kräver bild
  "author": { "@type": "Person", "name": "Anton Swall" },     // ❌ SAKNAS
  "publisher": {                                              // ❌ SAKNAS
    "@type": "Organization",
    "name": "AI-Bladet",
    "logo": { "@type": "ImageObject", "url": "favicon-url" }
  },
  "inLanguage": "sv-SE",                                      // ✅ finns
  "dateModified": "...",                                      // ❌ SAKNAS
  "keywords": [...],                                          // ❌ SAKNAS — kategorier från frontmatter
  "mainEntityOfPage": { "@type": "WebPage", "@id": "..." },   // ❌ SAKNAS
  "isAccessibleForFree": true,                                // ❌ SAKNAS — krävs för Google News
  "url": "https://aibladet.se/v/2026/25/"                     // ❌ SAKNAS
}
```

**Kodändring:** `templates/issue.js`, rad 16–23

**Resultat:** Kvalificerar för Google News + "news carousel" i sökresultat. Detta är den enskilt största SEO-vinsten.

---

### Punkt 1: Meta descriptions (liten fix)

**Problem:** Frontpage har generisk `"Sveriges veckotidning om AI"` istället för sammanfattning av senaste numret.

**Kodändring:** Redan korrekt i praktiken — `base.js` använder `description`-parametern från `issue.summary`. Frontpage = senaste numret, så beskrivningen är redan unik. Ingen ändring behövs här.

Om vi vill optimera ytterligare: skapa en separat frontpage-meta som är "Sveriges AI-veckotidning — vecka X: [sammanfattning]".

---

### Punkt 3: Titlar & rubrik-hierarki (redan OK)

**Analys:**
- `<h1>` = lead-headline (frontpage: i länk, permalink: plain text)
- `<h2>` = story-headlines
- `<h3>` = ingen (briefs är i `<ul>` utan rubrik-tagg)

**Rekommendation:** Lägg till `<h2>` för KORTNYTT-sektionen och "Tidigare nummer"-sektionen. Inga övriga ändringar — strukturen är redan bra.

**Kodändring:** `templates/issue.js`, rad 77 och rad 101

---

### Punkt 4: Alt-text på bilder (liten men viktig)

**Tomma alt-attribut:**
- Tidigare-nummer-kort: `alt=""` (rad 110)
- Arkivkort: sannolikt samma

**Åtgärd:** Använd issue-titel som alt-text istället för tom sträng.

**Kodändring:** `templates/issue.js`, rad 110: `alt="${esc(pi.title || 'AI-Bladet')}"`

---

### Punkt 5: Interna länkar mellan nummer (störst jobb)

**Nuläge:** Prev/next navigation finns. Inga korsreferenser i brödtext.

**Vad som skulle ge SEO-värde:**
- När en story bygger vidare på en tidigare nyhet → länka till tidigare nummer
- En "vi har tidigare bevakat detta"-sektion i slutet av relevanta stories

**Implementationsalternativ:**
1. **Enkelt:** Lägg till en automatisk "related" widget i botten som länkar till tidigare nummer med överlappande kategorier
2. **Svårt:** Modda write.py att uppmuntra Claude att inkludera interna korsreferenser

**Rekommendation:** Alternativ 1 först. $0 kostnad. Bygg en enkel matchningsalgoritm i `build.js` som för varje story kollar om någon tidigare story har samma kategori och lägger till en "Läs också"-länk.

---

## Implementationsplan

### Fas 1 — Hög effekt, låg insats (30 min)

1. **JSON-LD enrichment** → `templates/issue.js`
   - Lägg till `image`, `author`, `publisher`, `keywords`, `isAccessibleForFree`, `url`
2. **Sitemap-förbättring** → `build.js`
   - Lägg till `lastmod`, `changefreq`
   - Inkludera ordbokssidor, ljudfiler, memes
3. **Alt-text fix** → `templates/issue.js`
   - Byt `alt=""` till `alt="issue-titel"` för tidigare-nummer-kort

### Fas 2 — Medel effekt, medel insats (20 min)

4. **Rubrik-hierarki** → `templates/issue.js`
   - `<h2>` för KORTNYTT och Tidigare nummer
5. **Frontpage meta description** → `build.js`
   - Rikare fallback för startsidan

### Fas 3 — Korsreferenser (30 min)

6. **Auto-related-widget** → `build.js`
   - Matchningsalgoritm baserat på kategori-överlapp
   - "Läs också"-länkar i botten av varje issue

---

## Förväntat resultat

| Tidsram | Förväntan |
|---------|-----------|
| Direkt (dag 1) | Sitemap med lastmod → Google börjar indexera snabbare |
| 1–2 veckor | Google News Showcase kan börja visa stories (kräver JSON-LD) |
| 2–4 veckor | Sökresultat för AI-termer via ordboken börjar synas |
| 1–3 månader | "AI-Bladet" som varumärke i sök, stabil organisk trafik |
| 6–12 månader | 52+ ordbokssidor → långsvanssökningar på svenska AI-termer |
