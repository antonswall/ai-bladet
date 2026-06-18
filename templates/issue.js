// issue.js — Front page + permalink rendering
const base = require('./base');

function renderIssue(issue, mode, prev, next) {
  const { year, week, date, title, summary, lead, stories, briefs, categories, sources } = issue;
  const weekLabel = `Vecka ${week} ${year}`;
  // gray-matter may hand us a Date object (unquoted YAML date) or a string.
  // Build a Date safely from either so we never produce "Invalid Date".
  const dateObj = date instanceof Date ? date : new Date(date + 'T12:00:00');
  const dateStr = dateObj.toLocaleDateString('sv-SE', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
  const readTime = Math.max(1, Math.ceil((summary + ' ' + (lead?.ingress || '') + ' ' + (stories || []).map(s => s.body || '').join(' ')).split(/\s+/).length / 200));

  const isPermalink = mode === 'permalink';
  const canonical = `/v/${year}/${week}/`;

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'NewsArticle',
    headline: lead?.headline || title,
    description: summary,
    datePublished: date,
    inLanguage: 'sv-SE'
  };

  let body = '';

  // Lead
  if (lead) {
    body += `<section class="lead">
      <div class="lead-kicker">${esc(lead.kicker || 'VECKANS STÖRSTA')}<span class="lead-sources">${sources ? `· ${sources} källor` : ''}</span></div>
      <h1 class="lead-headline">${isPermalink ? esc(lead.headline || title) : `<a href="/v/${year}/${week}/">${esc(lead.headline || title)}</a>`}</h1>
      <p class="lead-ingress">${esc(lead.ingress || summary || '')}</p>
    </section>`;
  }

  // Sections ribbon
  if ((categories || []).length) {
    body += `<div class="sections"><span class="label">I detta nummer</span>${categories.map(c => `<span class="cat">${esc(c)}</span>`).join('')}</div>`;
  }

  // Secondary grid (front page: max 6, permalink: all)
  const displayStories = isPermalink ? (stories || []) : (stories || []).slice(0, 6);
  if (displayStories.length > 0) {
    const storyLink = `/v/${year}/${week}/`;
    body += `<section class="stories-grid">`;
    for (const s of displayStories) {
      body += `<article class="story-card">
        ${s.kicker ? `<div class="story-kicker">${esc(s.kicker)}</div>` : ''}
        <h2 class="story-headline">${isPermalink ? esc(s.headline) : `<a href="${storyLink}">${esc(s.headline)}</a>`}</h2>
        ${(isPermalink && s.body) ? `<p class="story-body">${esc(s.body)}</p>` : ''}
        ${!isPermalink ? `<a class="story-more" href="${storyLink}">Läs mer →</a>` : ''}
      </article>`;
    }
    body += `</section>`;
  }

  // Briefs
  if ((briefs || []).length > 0) {
    body += `<section class="briefs-section">
      <div class="briefs-header">Kortnytt</div>
      <ul class="briefs-list">`;
    for (const b of briefs) {
      body += `<li>${esc(b)}</li>`;
    }
    body += `</ul></section>`;
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
  }

  const pageTitle = isPermalink ? `${title} — Vecka ${week} ${year}` : `${title} — AI-Bladet`;

  return base({
    title: pageTitle,
    description: summary,
    canonical,
    ogType: 'article',
    jsonLd,
    content: body,
    week,
    year
  });
}

function esc(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

module.exports = { renderIssue };
