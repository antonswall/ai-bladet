// archive.js — Issue archive grouped by year
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
    for (const i of list) {
      // i.date is normally normalized to a 'YYYY-MM-DD' string in build.js, but
      // accept a Date object too so we never render "Invalid Date" next to a link.
      const dObj = i.date instanceof Date ? i.date : new Date(i.date + 'T12:00:00');
      const dateStr = dObj.toLocaleDateString('sv-SE', { day: 'numeric', month: 'long' });
      const cats = (i.categories || []).slice(0, 4).map(c => `<span class="cat">${esc(c)}</span>`).join(' ');
      body += `<article class="issue-card">
        <div class="issue-card-week">
          <a href="/v/${i.year}/${i.week}/">Vecka ${i.week}</a>
          <span class="date">${dateStr}</span>
        </div>
        <div>
          <a href="/v/${i.year}/${i.week}/" class="issue-card-title">${esc(i.title)}</a>
          ${cats ? `<span class="issue-card-cats">${cats}</span>` : ''}
        </div>
      </article>`;
    }
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
