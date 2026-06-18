// base.js — HTML shell, masthead, nav, footer, SEO
function base({ title, description, canonical, ogType, jsonLd, content, week, year }) {
  const w = week || '';
  const y = year || '';
  const footerWeek = w ? ` · Vecka ${w} ${y}` : '';
  return `<!DOCTYPE html>
<html lang="sv">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${title}${title.includes('AI-Bladet') ? '' : ' — AI-Bladet'}</title>
  <meta name="description" content="${description || 'Sveriges veckotidning om artificiell intelligens. En utgåva i veckan, rankat efter vad som faktiskt betyder något.'}">
  <link rel="canonical" href="${canonical || '/'}">
  <meta property="og:title" content="${title}">
  <meta property="og:description" content="${description || ''}">
  <meta property="og:type" content="${ogType || 'website'}">
  <meta property="og:locale" content="sv_SE">
  <meta name="twitter:card" content="summary">
  <link rel="alternate" type="application/rss+xml" href="/feed.xml" title="AI-Bladet RSS">
  <link rel="icon" type="image/svg+xml" href="/favicon.svg">
  <link rel="preload" href="/fonts/Archivo.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="/fonts/Fraunces.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="/style.css">
  ${jsonLd ? `<script type="application/ld+json">${JSON.stringify(jsonLd)}</script>` : ''}
</head>
<body>
  <header class="masthead">
    <div class="masthead-name"><a href="/">AI-Bladet</a></div>
    <div class="dateline">Sveriges veckotidning om AI${footerWeek}</div>
    <nav class="nav">
      <a href="/arkiv/">Arkiv</a>
      <a href="/om/">Om</a>
      <a href="/feed.xml">RSS</a>
    </nav>
  </header>
  ${content}
  <footer class="footer">
    AI-Bladet · En automatiserad nyhetstjänst om artificiell intelligens · Nästa nummer söndag · <a href="/feed.xml">RSS</a>
  </footer>
</body>
</html>`;
}

module.exports = base;
