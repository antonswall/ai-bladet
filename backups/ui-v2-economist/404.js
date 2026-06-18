// 404.js — Not Found page
const base = require('./base');

function render404() {
  const body = `<article class="notfound">
    <h1 class="page-title">404</h1>
    <p>Den här sidan har utgått, flyttats eller aldrig funnits. Prova <a href="/arkiv/">arkivet</a> eller gå till <a href="/">förstasidan</a>.</p>
  </article>`;

  return base({
    title: '404 — AI-Bladet',
    description: 'Sidan kunde inte hittas.',
    canonical: '',
    content: body
  });
}

module.exports = { render404 };
