// issue.js — Front page + permalink rendering
const base = require('./base');

function renderIssue(issue, mode, prev, next) {
  const { year, week, date, title, summary, lead, stories, briefs, categories, sources } = issue;
  const weekLabel = `Vecka ${week} ${year}`;
  const dateStr = new Date(date + 'T12:00:00').toLocaleDateString('sv-SE', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
  const readTime = Math.max(1, Math.ceil((summary + ' ' + (lead?.ingress || '') + ' ' + (stories || []).map(s => s.body || '').join(' ')).split(/\s+/).length / 200));

  const isPermalink = mode === 'permalink';
  const canonical = isPermalink ? `/v/${year}/${week}/` : `/v/${year}/${week}/`;

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
      <div class="lead-kicker">${esc(lead.kicker || 'VECKANS STÖRSTA')}<span class="lead-sources"> · ${sources || 0} källor</span></div>
      <h1 class="lead-headline">${isPermalink ? esc(lead.headline || title) : `<a href="/v/${year}/${week}/">${esc(lead.headline || title)}</a>`}</h1>
      <div class="lead-ingress">${esc(lead.ingress || '')}</div>
    </section>`;
  }

  // Secondary grid (front page: max 6, permalink: all)
  const displayStories = isPermalink ? (stories || []) : (stories || []).slice(0, 6);
  if (displayStories.length > 0) {
    body += `<section class="stories-grid">`;
    for (const s of displayStories) {
      body += `<div class="story-card">
        ${s.kicker ? `<div class="story-kicker">${esc(s.kicker)}</div>` : ''}
        <h2 class="story-headline">${esc(s.headline)}</h2>
        ${(isPermalink && s.body) ? `<div class="story-body">${esc(s.body)}</div>` : ''}
      </div>`;
    }
    body += `</section>`;
  }

  // Briefs
  if ((briefs || []).length > 0) {
    body += `<section class="briefs-section">
      <div class="briefs-header">KORTNYTT</div>
      <ul class="briefs-list">`;
    for (const b of briefs) {
      body += `<li>${esc(b)}</li>`;
    }
    body += `</ul></section>`;
  }

  // Meta footer
  body += `<div class="bottom-nav">`;
  if (prev) body += `<a href="/v/${prev.year}/${prev.week}/">← Vecka ${prev.week}</a>`;
  body += ` <span style="color:var(--muted)">${weekLabel} · ${sources || 0} källor · ~${readTime} min</span> `;
  if (next) body += `<a href="/v/${next.year}/${next.week}/">Vecka ${next.week} →</a>`;
  body += `</div>`;

  if (!isPermalink) {
    body += `<div class="bottom-nav"><a href="/v/${year}/${week}/">Läs hela ${weekLabel} →</a> &nbsp;·&nbsp; <a href="/arkiv/">Arkiv →</a></div>`;
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
