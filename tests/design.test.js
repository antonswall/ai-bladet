const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { renderIssue } = require('../templates/issue');
const matter = require('gray-matter');
const issue = matter.read(path.join(__dirname, '../content/2026-40.md')).data;

test('front page opens on the landing hero; permalinks start at the masthead', () => {
  const html = renderIssue(issue, 'frontpage');
  assert.match(html, /class="skip-link" href="#main"/);
  assert.match(html, /<header class="hero" data-hero>/);
  assert.match(html, /class="hero-logo"><span class="hero-ai">AI<\/span><span class="bladet"><span class="hero-dash">-<\/span><span class="hero-word">Bladet<\/span><\/span><\/div>/);
  assert.match(html, /class="hero-cue" href="#main"/);
  assert.match(html, /<script src="\/dust\.js" defer><\/script>/);
  assert.ok(!html.includes('<canvas'), 'canvases are created by the engine, not shipped in markup');
  assert.ok(!html.includes('data-nano') && !html.includes('/nano.'), 'previous nano layer removed');
  assert.match(html, /class="site-bar"/);
  assert.match(html, /class="lead-copy"/);
  assert.match(html, /id="main"/);
  for (const [, target] of html.matchAll(/href="#(segment-[^"]+)"/g)) assert.ok(html.includes(`id="${target}"`));
  assert.match(html, /href="#segment-verktyg"/);
  assert.match(html, /aria-controls="story-body-/);
  const permalink = renderIssue(issue, 'permalink');
  assert.match(permalink, /<header class="hero" data-hero>/);
  assert.ok(!permalink.includes('<header class="masthead">'));
});

test('lead image loads eagerly but secondary images stay lazy', () => {
  const html = renderIssue(issue, 'frontpage');
  const lead = html.match(/<figure class="figure lead-figure">([\s\S]*?)<\/figure>/)[1];
  assert.ok(lead.includes('loading="eager"'), 'lead must load eagerly');
  assert.ok(lead.includes('fetchpriority="high"'), 'lead is the priority image');
  const secondary = html.match(/<figure class="figure story-figure">([\s\S]*?)<\/figure>/)[1];
  assert.ok(secondary.includes('loading="lazy"'));
});

test('all existing editions render with unique IDs and valid section anchors', () => {
  const files = fs.readdirSync(path.join(__dirname, '../content')).filter(f => f.endsWith('.md'));
  assert.ok(files.length >= 16, 'content files: ' + files.length);
  for (const file of files) {
    const data = matter.read(path.join(__dirname, '../content', file)).data;
    for (const mode of ['frontpage', 'permalink']) {
      const html = renderIssue(data, mode);
      const ids = [...html.matchAll(/\sid="([^"]+)"/g)].map(m => m[1]);
      assert.equal(new Set(ids).size, ids.length, file + ': duplicate IDs');
      for (const match of html.matchAll(/href="#([^"]+)"/g)) assert.ok(ids.includes(match[1]), file + ': broken anchor');
      assert.ok(html.includes(data.lead.headline.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')));
      if (mode === 'permalink') assert.ok(!html.includes('class="story-more"'));
    }
  }
});
