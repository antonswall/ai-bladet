// issue.js — Front page + permalink rendering
const base = require('./base');

// Fasta segment — utgåvans redaktionella ordning kodas här och i write.py.
// Nyckeln matchar stories[].segment i frontmattern.
const SEGMENT = {
  verktyg: {
    num: '01',
    label: 'Veckans verktyg',
    desc: 'Modeller, releaser och verktyg som ändrar din AI-vardag',
  },
  bransch: {
    num: '02',
    label: 'Bransch i korthet',
    desc: 'Politik, reglering och pengar — med konsekvensen för dig',
  },
  vartattveta: {
    num: '03',
    label: 'Värt att veta',
    desc: 'Forskning och metod som förtjänar en rad',
  },
};

const KONSEKVENS_MARKER = 'Vad betyder det för dig:';

function renderIssue(issue, mode, prev, next, allIssues) {
  const { year, week, date, title, summary, lead, stories, briefs, categories, sources } = issue;
  const briefsBransch = issue.briefs_bransch || [];
  const briefsVartAttVeta = issue.briefs_vart_att_veta || [];
  // Ny segmenterad utgåva? Gamla nummer (utan segment-fält) renderas som förut.
  const segmented = Boolean(
    (lead && lead.segment) ||
    (stories || []).some(s => s.segment) ||
    briefsBransch.length > 0 ||
    briefsVartAttVeta.length > 0
  );
  // gray-matter may hand us a Date object (unquoted YAML date) or a string.
  // Build a Date safely from either so we never produce "Invalid Date".
  const dateObj = (date instanceof Date) ? date : (date ? new Date(date + 'T12:00:00') : new Date());
  const dateStr = dateObj.toLocaleDateString('sv-SE', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
  const readTime = Math.max(1, Math.ceil((summary + ' ' + (lead?.ingress || '') + ' ' + (lead?.analysis || '') + ' ' + (stories || []).map(s => (s.ingress || '') + ' ' + (s.body || '')).join(' ') + ' ' + briefsBransch.join(' ') + ' ' + briefsVartAttVeta.join(' ')).split(/\s+/).length / 200));

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

  // En story-card — delas av segmenterad och legacy rendering
  function storyCard(s, i) {
    const paras = (s.body || '').split(/\n\n+/).map(p => p.trim()).filter(Boolean);
    const bodyHtml = paras.map(p => storyPara(p)).join('');
    const tid = `story-body-${week}-${i}`;
    const quote = (s.quote && s.quote.text)
      ? `<blockquote class="story-quote"><p>${esc(s.quote.text)}</p>${s.quote.speaker ? `<cite>${esc(s.quote.speaker)}</cite>` : ''}</blockquote>`
      : '';
    // SEO: Unique id per article for anchor links / Google
    const storyId = `story-${week}-${i}`;
    let card = `<article class="story-card" id="${storyId}">
      ${figure(s.image, s.headline, 'story-figure', s.credit)}
      <div class="story-text">
        ${s.kicker ? `<div class="story-kicker">${esc(s.kicker)}</div>` : ''}
        <h2 class="story-headline">${esc(s.headline)}</h2>
        ${s.ingress ? `<p class="story-ingress">${esc(s.ingress)}</p>` : (s.body ? `<p class="story-ingress story-ingress--fallback">${esc(s.body.split(/\n\n+/)[0].slice(0, 200))}…</p>` : '')}
        ${quote}`;
    if (isPermalink) {
      card += bodyHtml;
    } else if (bodyHtml) {
      card += `<div class="story-body-wrap" id="${tid}" hidden>${bodyHtml}</div>
        <button class="story-more" type="button" aria-expanded="false" aria-controls="${tid}">
          <span class="story-more-label">Läs mer</span><span class="story-more-arrow" aria-hidden="true">→</span>
        </button>`;
    }
    card += `</div></article>`;
    return card;
  }

  // Brödtextstycke — "Vad betyder det för dig:"-raden får egen konsekvensstil
  function storyPara(p) {
    if (p.startsWith(KONSEKVENS_MARKER)) {
      const tail = p.slice(KONSEKVENS_MARKER.length).trim();
      return `<p class="story-body story-konsekvens"><strong class="konsekvens-label">${KONSEKVENS_MARKER}</strong> ${esc(tail)}</p>`;
    }
    return `<p class="story-body">${esc(p)}</p>`;
  }

  // Bransch-brief — konsekvensraden lyfts fram typografiskt
  function branschBrief(b) {
    const idx = b.indexOf(KONSEKVENS_MARKER);
    if (idx >= 0) {
      const head = b.slice(0, idx).trim();
      const tail = b.slice(idx + KONSEKVENS_MARKER.length).trim();
      return `<li><p class="brief-text">${esc(head)}</p>
        <p class="brief-konsekvens"><strong class="konsekvens-label">${KONSEKVENS_MARKER}</strong> ${esc(tail)}</p></li>`;
    }
    return `<li><p class="brief-text">${esc(b)}</p></li>`;
  }

  // Avdelningsplåt — numrerad segmentheader i broadsheet-stil
  function segmentHeader(key, extraClass) {
    const seg = SEGMENT[key];
    if (!seg) return '';
    return `<header class="segment-header${extraClass ? ' ' + extraClass : ''}">
      <div class="segment-header-row">
        <span class="segment-num" aria-hidden="true">${seg.num}</span>
        <h2 class="segment-label">${esc(seg.label)}</h2>
        <span class="segment-desc">${esc(seg.desc)}</span>
      </div>
    </header>`;
  }

  // Sections ribbon — i segmenterade nummer överst (innehållsrad före segment 01)
  const ribbonClass = segmented ? 'sections sections--top' : 'sections';
  const ribbon = (categories || []).length
    ? `<div class="${ribbonClass}"><span class="label">I detta nummer</span>${categories.map(c => `<span class="cat">${esc(c)}</span>`).join('')}</div>`
    : '';

  // Lead
  const defaultKicker = segmented ? 'VECKANS VERKTYG' : 'VECKANS STÖRSTA';
  const leadHtml = lead ? `<section class="lead">
      ${figure(lead.image, lead.headline || title, 'lead-figure', lead.credit)}
      <div class="lead-kicker">${esc(lead.kicker || defaultKicker)}<span class="lead-sources">${sources ? `· ${sources} källor` : ''}</span></div>
      <h1 class="lead-headline">${isPermalink ? esc(lead.headline || title) : `<a href="/v/${year}/${week}/">${esc(lead.headline || title)}</a>`}</h1>
      <p class="lead-ingress">${esc(lead.ingress || summary || '')}</p>
      ${lead.analysis ? `<aside class="lead-analysis"><span class="lead-analysis-label">AI-Bladets analys</span><p>${esc(lead.analysis)}</p></aside>` : ''}
    </section>` : '';

  if (segmented) {
    // ── Segmenterad utgåva: fast ordning Verktyg → Bransch → Värt att veta ──
    const verktygStories = (stories || []).filter(s => (s.segment || 'verktyg') === 'verktyg');
    const branschStories = (stories || []).filter(s => s.segment === 'bransch');
    let idx = 0;

    body += ribbon;

    // 01 · Veckans verktyg — alltid först, leaden ingår
    body += segmentHeader('verktyg', 'segment-header--first');
    body += leadHtml;
    if (verktygStories.length > 0) {
      body += `<section class="stories-column">`;
      for (const s of verktygStories) body += storyCard(s, idx++);
      body += `</section>`;
    }

    // 02 · Bransch i korthet — max en full story + briefs med konsekvensrad
    if (branschStories.length > 0 || briefsBransch.length > 0) {
      body += segmentHeader('bransch');
      if (branschStories.length > 0) {
        body += `<section class="stories-column">`;
        for (const s of branschStories) body += storyCard(s, idx++);
        body += `</section>`;
      }
      if (briefsBransch.length > 0) {
        body += `<section class="briefs-section briefs-section--bransch">
          <ul class="briefs-list briefs-list--bransch">${briefsBransch.map(b => branschBrief(b)).join('')}</ul>
        </section>`;
      }
    }

    // 03 · Värt att veta — enradiga forskningsnotiser, bara när de finns
    if (briefsVartAttVeta.length > 0) {
      body += segmentHeader('vartattveta');
      body += `<section class="briefs-section briefs-section--veta">
        <ul class="briefs-list">${briefsVartAttVeta.map(b => `<li>${esc(b)}</li>`).join('')}</ul>
      </section>`;
    }

    // Legacy-briefs om de mot förmodan finns i ett segmenterat nummer
    if ((briefs || []).length > 0) {
      body += `<section class="briefs-section">
        <h2 class="briefs-header">Kortnytt</h2>
        <ul class="briefs-list">${briefs.map(b => `<li>${esc(b)}</li>`).join('')}</ul>
      </section>`;
    }
  } else {
    // ── Legacy-rendering: gamla nummer utan segmentdata ──
    body += leadHtml;
    body += ribbon;

    // Story column (front page: max 6 in one scrollable column, permalink: all)
    const displayStories = isPermalink ? (stories || []) : (stories || []).slice(0, 6);
    if (displayStories.length > 0) {
      body += `<section class="stories-column">`;
      displayStories.forEach((s, i) => { body += storyCard(s, i); });
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
          <span class="related-card-week">Vecka ${ri.week} · ${(ri.shared || []).map(c => c.charAt(0).toUpperCase() + c.slice(1)).join(', ')}</span>
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
