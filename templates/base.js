// base.js — HTML shell: landing hero (front page) or masthead, sticky bar, footer, SEO
function base({ title, description, canonical, ogType, ogImage, jsonLd, content, week, year, bodyClass, hero, heroTeaser }) {
  const w = week || '';
  const y = year || '';
  const editionLabel = w ? `Vecka ${w} · ${y}` : 'Veckotidning om AI';
  const descr = description || 'Sveriges veckotidning om artificiell intelligens. En utgåva i veckan, rankat efter vad som faktiskt betyder något.';
  const ogImg = ogImage || 'https://ai-bladet.pages.dev/favicon.svg';
  const tagline = 'Sveriges veckotidning om artificiell intelligens — en utgåva i veckan.';
  const top = `<div class="masthead-top">
      <span>${editionLabel}</span>
      <button class="motion-toggle" type="button" aria-pressed="false">Pausa rörelse</button>
    </div>`;
  const header = hero
    ? `<header class="hero" data-hero>
    ${top}
    <div class="hero-logo"><span class="hero-ai">AI</span><span class="bladet"><span class="hero-dash">-</span><span class="hero-word">Bladet</span></span></div>
    <div class="hero-foot">
      <p class="hero-tag">${tagline}</p>
      <a class="hero-cue" href="#main"><span>${heroTeaser ? `Vecka ${w}: ${heroTeaser}` : 'Till veckans nummer'}</span><span class="hero-cue-line" aria-hidden="true"></span></a>
    </div>
  </header>`
    : `<header class="masthead">
    ${top}
    <div class="masthead-brand">
      <div class="masthead-name"><a href="/">AI<span class="bladet">-Bladet</span></a></div>
      <p class="masthead-tag">${tagline}</p>
    </div>
  </header>`;

  return `<!DOCTYPE html>
<html lang="sv">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${title}${title.includes('AI-Bladet') ? '' : ' — AI-Bladet'}</title>
  <meta name="description" content="${descr}">
  <link rel="canonical" href="${canonical || '/'}">
  <meta name="theme-color" content="#FFF8F0">
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
  <link rel="preload" href="/fonts/FamiljenGrotesk-Bold.ttf" as="font" type="font/ttf" crossorigin>
  <link rel="preload" href="/fonts/Newsreader-SemiBold.ttf" as="font" type="font/ttf" crossorigin>
  <link rel="stylesheet" href="/style.css">
  <link rel="stylesheet" href="/dust.css">
  <script>(function(){var d=document.documentElement;try{if(localStorage.getItem('ab-motion')==='off')return}catch(e){}if(window.matchMedia&&!matchMedia('(prefers-reduced-motion: reduce)').matches&&!(navigator.connection&&navigator.connection.saveData))d.classList.add('dust-pending')})()</script>
  ${jsonLd ? `<script type="application/ld+json">${JSON.stringify(jsonLd)}</script>` : ''}
</head>
<body${bodyClass ? ` class="${bodyClass}"` : ''}>
  <a class="skip-link" href="#main">Till innehållet</a>
  ${header}
  <div class="bar-sentinel" aria-hidden="true"></div>
  <div class="site-bar">
    <a class="bar-logo" href="/" aria-label="AI-Bladet, startsidan">AI<span class="bladet">-Bladet</span></a>
    <div class="edition-meta">Redaktör <b>Anton Swall</b> · Nästa nummer söndag</div>
    <nav class="nav" aria-label="Huvudmeny">
      <a href="/arkiv/">Arkiv</a>
      <a href="/om/">Om</a>
      <a href="/feed.xml">RSS</a>
    </nav>
  </div>
  <main class="sheet" id="main">
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
  <script src="/dust.js" defer></script>
</body>
</html>`;
}

module.exports = base;
