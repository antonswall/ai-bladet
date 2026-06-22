// base.js — HTML shell, masthead, edition strip, nav, footer, SEO
function base({ title, description, canonical, ogType, ogImage, jsonLd, content, week, year, bodyClass }) {
  const w = week || '';
  const y = year || '';
  const editionLabel = w ? `Vecka ${w} · ${y}` : 'Veckotidning om AI';
  const descr = description || 'Sveriges veckotidning om artificiell intelligens. En utgåva i veckan, rankat efter vad som faktiskt betyder något.';
  const ogImg = ogImage || 'https://aibladet.se/favicon.svg';

  return `<!DOCTYPE html>
<html lang="sv">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${title}${title.includes('AI-Bladet') ? '' : ' — AI-Bladet'}</title>
  <meta name="description" content="${descr}">
  <link rel="canonical" href="${canonical || '/'}">
  <meta name="theme-color" content="#16130d">
  <meta property="og:title" content="${title}">
  <meta property="og:description" content="${descr}">
  <meta property="og:type" content="${ogType || 'website'}">
  <meta property="og:image" content="${ogImg}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:locale" content="sv_SE">
  <meta property="og:site_name" content="AI-Bladet">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="${title}">
  <meta name="twitter:description" content="${descr}">
  <meta name="twitter:image" content="${ogImg}">
  <link rel="alternate" type="application/rss+xml" href="/feed.xml" title="AI-Bladet RSS">
  <link rel="icon" type="image/svg+xml" href="/favicon.svg">
  <link rel="preload" href="/fonts/FamiljenGrotesk-Bold.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="/fonts/Newsreader-SemiBold.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="/style.css">
  ${jsonLd ? `<script type="application/ld+json">${JSON.stringify(jsonLd)}</script>` : ''}
</head>
<body${bodyClass ? ` class="${bodyClass}"` : ''}>
  <header class="masthead">
    <div class="masthead-top">
      <span>${editionLabel}</span>
    </div>
    <div class="masthead-brand">
      <div class="masthead-name"><a href="/">AI<span class="bladet">-Bladet</span></a></div>
      <p class="masthead-tag">Sveriges veckotidning om artificiell intelligens — en utgåva i veckan.</p>
    </div>
  </header>
  <div class="masthead-rule"></div>
  <div class="edition">
    <div class="edition-meta">Redaktör <b>Anton Swall</b> · Nästa nummer söndag</div>
    <nav class="nav">
      <a href="/arkiv/">Arkiv</a>
      <a href="/om/">Om</a>
      <a href="/feed.xml">RSS</a>
    </nav>
  </div>
  <main class="sheet">
  ${content}
  </main>
  <footer class="footer">
    <span>AI-Bladet</span>
    <span class="spacer"></span>
    <span>En automatiserad nyhetstjänst om AI</span>
    <a href="/feed.xml">RSS</a>
    <a href="/arkiv/">Arkiv</a>
    <a href="/om/">Om</a>
  </footer>
  <script src="/app.js" defer></script>
</body>
</html>`;
}

module.exports = base;
