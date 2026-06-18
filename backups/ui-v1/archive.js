// archive.js — Issue archive grouped by year
const base = require('./base');

function renderArchive(issues) {
  const grouped = {};
  for (const i of issues) {
    const y = i.year;
    if (!grouped[y]) grouped[y] = [];
    grouped[y].push(i);
  }

  let body = `<h1 class="page-title">Arkiv</h1>`;
  const years = Object.keys(grouped).sort((a, b) => b - a);

  for (const year of years) {
    const list = grouped[year];
    body += `<h2 style="font-family:'Fraunces',Georgia,serif;font-size:24px;margin:1.5rem 0 0.5rem;border-bottom:2px solid #ccc;padding-bottom:0.25rem;">${year} — ${list.length} utgåvor</h2>`;
    for (const i of list) {
      const dateStr = new Date(i.date + 'T12:00:00').toLocaleDateString('sv-SE', { day: 'numeric', month: 'long' });
      const catChips = (i.categories || []).map(c => `<span style="font-size:11px;text-transform:uppercase;letter-spacing:1px;color:var(--accent-blue);margin-right:0.5rem;">${c}</span>`).join('');
      body += `<div class="issue-card">
        <div class="issue-card-week"><a href="/v/${i.year}/${i.week}/">Vecka ${i.week} · ${dateStr}</a></div>
        <div class="issue-card-title">${esc(i.title)} · ${catChips}</div>
      </div>`;
    }
  }

  return base({
    title: 'Arkiv — AI-Bladet',
    description: 'Alla utgåvor av AI-Bladet, Sveriges veckotidning om AI.',
    canonical: '/arkiv/',
    content: body
  });
}

function esc(s) { if (!s) return ''; return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

module.exports = { renderArchive };
