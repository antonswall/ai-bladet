// 404.js — Not Found page
const base = require('./base');

function render404() {
  const body = `<article style="text-align:center;margin:4rem 0;">
    <h1 class="page-title">404 — Sidan finns inte</h1>
    <p style="font-size:18px;color:var(--muted);margin:1rem 0 2rem;">Den här sidan har utgått, flyttats eller aldrig funnits.<br>Prova <a href="/arkiv/">arkivet</a> eller gå till <a href="/">förstasidan</a>.</p>
  </article>`;

  return base({
    title: '404 — AI-Bladet',
    description: 'Sidan kunde inte hittas.',
    canonical: '',
    content: body
  });
}

module.exports = { render404 };
