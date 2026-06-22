// issue.js — Front page + permalink rendering
const base = require('./base');

function renderIssue(issue, mode, prev, next, allIssues) {
  const { year, week, date, title, summary, lead, stories, briefs, categories, sources } = issue;
  // gray-matter may hand us a Date object (unquoted YAML date) or a string.
  // Build a Date safely from either so we never produce "Invalid Date".
  const dateObj = date instanceof Date ? date : new Date(date + 'T12:00:00');
  const dateStr = dateObj.toLocaleDateString('sv-SE', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
  const readTime = Math.max(1, Math.ceil((summary + ' ' + (lead?.ingress || '') + ' ' + (lead?.analysis || '') + ' ' + (stories || []).map(s => (s.ingress || '') + ' ' + (s.body || '')).join(' ')).split(/\s+/).length / 200));

  const isPermalink = mode === 'permalink';
  const canonical = `/v/${year}/${week}/`;
  const pageUrl = `https://aibladet.se${canonical}`;
  const leadImage = lead?.image || (stories && stories[0]?.image) || '';

  // SEO: Fullständig JSON-LD för Google News + Search
  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'NewsArticle',
    headline: lead?.headline || title,
    description: summary || '',
    datePublished: date,
    dateModified: date,
    inLanguage: 'sv-SE',
    isAccessibleForFree: true,
    url: pageUrl,
    mainEntityOfPage: { '@type': 'WebPage', '@id': pageUrl },
    image: leadImage ? [leadImage] : [],
    author: { '@type': 'Person', 'name': 'Anton Swall' },
    publisher: {
      '@type': 'Organization',
      'name': 'AI-Bladet',
      'logo': {
        '@type': 'ImageObject',
        'url': 'https://aibladet.se/favicon.svg'
      }
    }
  };
  // Villkorliga fält — undvik tomma arrays/strängar
  if ((categories || []).length > 0) {
    jsonLd.about = categories.map(c => ({ '@type': 'Thing', 'name': c }));
    jsonLd.keywords = categories.join(', ');
  }

  let body = '';

  // Lead
  if (lead) {
    body += `<section class="lead">
      ${figure(lead.image, lead.headline || title, 'lead-figure', lead.credit)}
      <div class="lead-kicker">${esc(lead.kicker || 'VECKANS STÖRSTA')}<span class="lead-sources">${sources ? `· ${sources} källor` : ''}</span></div>
      <h1 class="lead-headline">${isPermalink ? esc(lead.headline || title) : `<a href="/v/${year}/${week}/">${esc(lead.headline || title)}</a>`}</h1>
      <p class="lead-ingress">${esc(lead.ingress || summary || '')}</p>
      ${lead.analysis ? `<aside class="lead-analysis"><span class="lead-analysis-label">AI-Bladets analys</span><p>${esc(lead.analysis)}</p></aside>` : ''}
    </section>`;
  }

  // Sections ribbon
  if ((categories || []).length) {
    body += `<div class="sections"><span class="label">I detta nummer</span>${categories.map(c => `<span class="cat">${esc(c)}</span>`).join('')}</div>`;
  }

  // Story column (front page: max 6 in one scrollable column, permalink: all)
  const displayStories = isPermalink ? (stories || []) : (stories || []).slice(0, 6);
  if (displayStories.length > 0) {
    body += `<section class="stories-column">`;
    displayStories.forEach((s, i) => {
      const paras = (s.body || '').split(/\n\n+/).map(p => p.trim()).filter(Boolean);
      const bodyHtml = paras.map(p => `<p class="story-body">${esc(p)}</p>`).join('');
      const tid = `story-body-${week}-${i}`;
      const quote = (s.quote && s.quote.text)
        ? `<blockquote class="story-quote"><p>${esc(s.quote.text)}</p>${s.quote.speaker ? `<cite>${esc(s.quote.speaker)}</cite>` : ''}</blockquote>`
        : '';
      // SEO: Unique id per article for anchor links / Google
      const storyId = `story-${week}-${i}`;
      body += `<article class="story-card" id="${storyId}">
        ${figure(s.image, s.headline, 'story-figure', s.credit)}
        <div class="story-text">
          ${s.kicker ? `<div class="story-kicker">${esc(s.kicker)}</div>` : ''}
          <h2 class="story-headline">${esc(s.headline)}</h2>
          ${s.ingress ? `<p class="story-ingress">${esc(s.ingress)}</p>` : ''}
          ${quote}`;
      if (isPermalink) {
        body += bodyHtml;
      } else if (bodyHtml) {
        body += `<div class="story-body-wrap" id="${tid}" hidden>${bodyHtml}</div>
          <button class="story-more" type="button" aria-expanded="false" aria-controls="${tid}">
            <span class="story-more-label">Läs mer</span><span class="story-more-arrow" aria-hidden="true">→</span>
          </button>`;
      }
      body += `</div></article>`;
    });
    body += `</section>`;
  }

  // Briefs — SEO: använd <h2> för rubrik
  if ((briefs || []).length > 0) {
    body += `<section class="briefs-section">
      <h2 class="briefs-header">Kortnytt</h2>
      <ul class="briefs-list">`;
    for (const b of briefs) {
      body += `<li>${esc(b)}</li>`;
    }
    body += `</ul></section>`;
  }

  // Related stories widget — bygger interna länkar baserat på kategori-överlapp
  if (allIssues && allIssues.length > 1) {
    const currentCats = (categories || []).map(c => c.toLowerCase());
    const related = [];

    for (const older of allIssues) {
      if (older.week === week && older.year === year) continue;
      const olderCats = (older.categories || []).map(c => c.toLowerCase());
      const overlap = currentCats.filter(c => olderCats.includes(c));
      if (overlap.length > 0) {
        related.push({ issue: older, overlap: overlap.length, shared: overlap.slice(0, 2) });
        if (related.length >= 3) break;
      }
    }

    if (related.length > 0) {
      body += `<section class="related-stories">
        <h2 class="related-stories-title">Relaterade artiklar</h2>
        <div class="related-stories-grid">`;
      for (const r of related) {
        const ri = r.issue;
        body += `<a href="/v/${ri.year}/${ri.week}/" class="related-card">
          <span class="related-card-week">Vecka ${ri.week} · ${ri.shared.map(c => c.charAt(0).toUpperCase() + c.slice(1)).join(', ')}</span>
          <span class="related-card-title">${esc(ri.title || '')}</span>
        </a>`;
      }
      body += `</div></section>`;
    }
  }

  // Bottom navigation / folio
  body += `<nav class="bottom-nav">`;
  body += prev ? `<a href="/v/${prev.year}/${prev.week}/">← Vecka ${prev.week}</a>` : `<span class="folio">Äldsta numret</span>`;
  body += `<span class="folio">${dateStr} · ${sources || 0} källor · ~${readTime} min</span>`;
  body += next ? `<a href="/v/${next.year}/${next.week}/">Vecka ${next.week} →</a>` : `<span class="folio">Senaste numret</span>`;
  body += `</nav>`;

  if (!isPermalink) {
    body += `<nav class="bottom-nav bottom-nav--cta">
      <a href="/arkiv/">Bläddra i arkivet →</a>
    </nav>`;

    // "Tidigare nummer" — visa upp till 3 tidigare utgåvor som miniatyrkort
    const prevIssues = (allIssues || []).filter(i => i.week !== week || i.year !== year).slice(0, 3);
    if (prevIssues.length > 0) {
      body += `<section class="previous-issues">
        <h2 class="previous-issues-title">Tidigare nummer</h2>
        <div class="previous-issues-grid">`;
      for (const pi of prevIssues) {
        const piDate = pi.date instanceof Date ? pi.date : new Date(pi.date + 'T12:00:00');
        const piDateStr = piDate.toLocaleDateString('sv-SE', { day: 'numeric', month: 'long' });
        const piImg = pi.lead?.image || (pi.stories && pi.stories[0]?.image) || '';
        const piAlt = pi.title || `AI-Bladet Vecka ${pi.week}`;
        body += `<a href="/v/${pi.year}/${pi.week}/" class="previous-card">
          <div class="previous-card-img">
            ${piImg ? `<img src="${esc(piImg)}" alt="${esc(piAlt)}" loading="lazy" decoding="async" onerror="this.parentElement.remove()">` : ''}
            <span class="previous-card-fallback" aria-hidden="true">AI<span class="previous-card-fallback-b">-Bladet</span></span>
          </div>
          <div class="previous-card-text">
            <span class="previous-card-week">Vecka ${pi.week} · ${piDateStr}</span>
            <span class="previous-card-title">${esc(pi.title || '')}</span>
            ${pi.summary ? `<span class="previous-card-ingress">${esc(pi.summary)}</span>` : ''}
          </div>
        </a>`;
      }
      body += `</div></section>`;
    }
  }

  const pageTitle = isPermalink ? `${title} — Vecka ${week} ${year}` : `${title} — AI-Bladet`;

  // SEO: Rikare frontpage-description
  const pageDescription = summary
    ? `${summary} — AI-Bladet vecka ${week} ${year}.`
    : `AI-Bladet vecka ${week} ${year}: ${title}. Sveriges veckotidning om AI.`;

  return base({
    title: pageTitle,
    description: pageDescription,
    canonical,
    ogType: 'article',
    jsonLd,
    content: body,
    week,
    year,
    ogImage: leadImage || undefined
  });
}

function esc(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// Image block with a built-in fallback + press credit. Many source image URLs
// 404 over time; the branded placeholder always sits behind the image, so a
// broken <img> simply removes itself (inline onerror — works before app.js) and
// the placeholder shows through. `credit` renders a newspaper-style photo byline.
function figure(url, alt, cls, credit) {
  const img = url
    ? `<img class="figure-img" src="${esc(url)}" alt="${esc(alt || '')}" loading="lazy" decoding="async" onerror="this.remove()">`
    : '';
  const cap = credit ? `<figcaption class="figure-credit">${esc(credit)}</figcaption>` : '';
  return `<figure class="figure ${cls}">
    <span class="figure-frame">${img}<span class="figure-fallback" aria-hidden="true">AI<span class="figure-fallback-b">-Bladet</span></span></span>
    ${cap}
  </figure>`;
}

module.exports = { renderIssue };
