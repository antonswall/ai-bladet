// about.js — Om AI-Bladet
const base = require('./base');

function renderAbout() {
  const body = `<article class="about-section">
    <h1 class="page-title">Om AI-Bladet</h1>
    <p class="page-intro">AI-världen rör sig för snabbt för att följa varje dag, men är för viktig för att missa. Vi läser veckan åt dig.</p>

    <p>AI-Bladet är en svensk nyhetstidning om artificiell intelligens. Varje söndag sammanfattar vi veckans viktigaste händelser inom AI — nya modeller, politik och reglering, verktyg och forskning — rankat efter vad som faktiskt betyder något. En utgåva i veckan, ingen brusig daglig ström.</p>

    <h2>Så fungerar det</h2>

    <p>Varje söndag genomsöks fler än 20 källor automatiskt, och veckans nyheter sammanställs och redigeras av en automatiserad pipeline till den utgåva du läser här. Innehållet produceras med AI-stöd och publiceras utan dröjsmål. Hittar du ett fel eller en nyhet vi missat — hör gärna av dig.</p>

    <h2>Kontakt</h2>

    <p>Redaktör: Anton Swall</p>
    <p>Prenumerera via RSS: <a href="/feed.xml">/feed.xml</a></p>
  </article>`;

  return base({
    title: 'Om AI-Bladet',
    description: 'Om AI-Bladet — Sveriges veckotidning om artificiell intelligens.',
    canonical: '/om/',
    content: body
  });
}

module.exports = { renderAbout };
