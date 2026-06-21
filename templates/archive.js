// archive.js — Issue archive grouped by year with rich cards
const base = require('./base');

function renderArchive(issues) {
  const grouped = {};
  for (const i of issues) {
    const y = i.year;
    if (!grouped[y]) grouped[y] = [];
    grouped[y].push(i);
  }

  let body = `<h1 class="page-title">Arkiv</h1>
    <p class="page-intro">Varje nummer av AI-Bladet, hela vägen tillbaka. ${issues.length} ${issues.length === 1 ? 'utgåva' : 'utgåvor'} och räknar.</p>`;

  const years = Object.keys(grouped).sort((a, b) => b - a);

  for (const year of years) {
    const list = grouped[year];
    body += `<h2 class="archive-year">${year}<span>${list.length} ${list.length === 1 ? 'utgåva' : 'utgåvor'}</span></h2>`;
    body += `<div class="archive-grid">`;
    for (const i of list) {
      const dObj = i.date instanceof Date ? i.date : new Date(i.date + 'T12:00:00');
      const dateStr = dObj.toLocaleDateString('sv-SE', { day: 'numeric', month: 'long' });
      const cats = (i.categories || []).slice(0, 4).map(c => `<span class="cat">${esc(c)}</span>`).join(' ');
      const img = i.lead?.image || (i.stories && i.stories[0]?.image) || '';
      const credit = i.lead?.credit || (i.stories && i.stories[0]?.credit) || '';

      body += `<article class="archive-card">
        <a href="/v/${i.year}/${i.week}/" class="archive-card-link">
          <div class="archive-card-img">
            ${img ? `<img src="${esc(img)}" alt="" loading="lazy" decoding="async" onerror="this.parentElement.remove()">` : ''}
            <span class="archive-card-fallback" aria-hidden="true">AI<span class="archive-card-fallback-b">-Bladet</span></span>
          </div>
          <div class="archive-card-body">
            <span class="archive-card-week">Vecka ${i.week} · ${dateStr}</span>
            <h3 class="archive-card-title">${esc(i.title)}</h3>
            ${i.summary ? `<p class="archive-card-ingress">${esc(i.summary)}</p>` : ''}
            ${cats ? `<span class="archive-card-cats">${cats}</span>` : ''}
          </div>
        </a>
      </article>`;
    }
    body += `</div>`;
  }

  return base({
    title: 'Arkiv — AI-Bladet',
    description: 'Alla utgåvor av AI-Bladet, Sveriges veckotidning om AI.',
    canonical: '/arkiv/',
    content: body
  });
}

function esc(s) { if (!s) return ''; return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }

module.exports = { renderArchive };
