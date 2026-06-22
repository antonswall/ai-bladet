// build.js — AI-Bladet static site generator
// SEO-uppdaterad: rik sitemap, bevarar distributions-tillgångar vid ombygg
const fs = require('fs');
const path = require('path');
const matter = require('gray-matter');
const { renderIssue } = require('./templates/issue');
const { renderArchive } = require('./templates/archive');
const { renderAbout } = require('./templates/about');
const { render404 } = require('./templates/404');

const SITE_URL = process.env.SITE_URL || 'https://aibladet.se';
const CONTENT_DIR = path.join(__dirname, 'content');
const PUBLIC_DIR = path.join(__dirname, 'public');
const STATIC_DIR = path.join(__dirname, 'static');

// Helper
const TODAY_ISO = new Date().toISOString().slice(0, 10);
function escXml(s) { if (!s) return ''; return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&apos;'); }

// SEO: Bevara distributions-tillgångar vid ombygg (distribution skriver direkt
// till public/{ordbok,audio,memes,feed} — vi sparar dem till /tmp före wipe)
const os = require('os');
const DIST_DIRS = ['ordbok', 'audio', 'memes', 'feed'];
const tmpBackup = path.join(os.tmpdir(), 'ai-bladet-dist-backup');
let savedDirs = {};
for (const d of DIST_DIRS) {
  const src = path.join(PUBLIC_DIR, d);
  if (fs.existsSync(src)) {
    const dest = path.join(tmpBackup, d);
    fs.cpSync(src, dest, { recursive: true });
    savedDirs[d] = true;
  }
}

// Ensure public dir is clean
if (fs.existsSync(PUBLIC_DIR)) fs.rmSync(PUBLIC_DIR, { recursive: true });
fs.mkdirSync(PUBLIC_DIR, { recursive: true });

// Restore saved distribution assets from /tmp
for (const d of Object.keys(savedDirs)) {
  const src = path.join(tmpBackup, d);
  const dest = path.join(PUBLIC_DIR, d);
  if (fs.existsSync(src)) {
    fs.cpSync(src, dest, { recursive: true });
  }
}
// Städa tmp
try { fs.rmSync(tmpBackup, { recursive: true }); } catch (_) {}

// 1. LOAD
const issueFiles = fs.readdirSync(CONTENT_DIR).filter(f => f.endsWith('.md'));
const issues = [];

for (const file of issueFiles) {
  const raw = fs.readFileSync(path.join(CONTENT_DIR, file), 'utf8');
  const { data, content } = matter(raw);
  // gray-matter parses unquoted YAML dates (date: 2026-06-21) into JS Date
  // objects. Normalize to a 'YYYY-MM-DD' string so every consumer (folio
  // formatting, JSON-LD datePublished, RSS pubDate) gets a predictable value.
  if (data.date instanceof Date) data.date = data.date.toISOString().slice(0, 10);
  data.slug = `v/${data.year}/${data.week}`;
  data.url = `/${data.slug}/`;
  data.bodyHtml = content.trim();
  if (!data.wordcount) {
    const text = (data.lead?.ingress || '') + ' ' + (data.lead?.analysis || '') + ' ' + (data.stories || []).map(s => (s.ingress || '') + ' ' + (s.body || '')).join(' ') + ' ' + (data.briefs || []).join(' ');
    data.wordcount = text.split(/\s+/).filter(Boolean).length;
  }
  issues.push(data);
}

// 2. SORT
issues.sort((a, b) => {
  if (a.year !== b.year) return b.year - a.year;
  return b.week - a.week;
});

// Compute prev/next
for (let i = 0; i < issues.length; i++) {
  issues[i]._prev = issues[i + 1] || null;
  issues[i]._next = issues[i - 1] || null;
}

const latest = issues[0];

// 3. RENDER
// a) Homepage = front page of latest
const homeHtml = renderIssue(latest, 'frontpage', latest._prev, latest._next, issues);
fs.mkdirSync(PUBLIC_DIR, { recursive: true });
fs.writeFileSync(path.join(PUBLIC_DIR, 'index.html'), homeHtml);

// b) Issue pages
for (const issue of issues) {
  const dir = path.join(PUBLIC_DIR, 'v', String(issue.year), String(issue.week));
  fs.mkdirSync(dir, { recursive: true });
  const html = renderIssue(issue, 'permalink', issue._prev, issue._next);
  fs.writeFileSync(path.join(dir, 'index.html'), html);
}

// c) Archive
const archiveHtml = renderArchive(issues);
const archiveDir = path.join(PUBLIC_DIR, 'arkiv');
fs.mkdirSync(archiveDir, { recursive: true });
fs.writeFileSync(path.join(archiveDir, 'index.html'), archiveHtml);

// d) About
const aboutHtml = renderAbout();
const aboutDir = path.join(PUBLIC_DIR, 'om');
fs.mkdirSync(aboutDir, { recursive: true });
fs.writeFileSync(path.join(aboutDir, 'index.html'), aboutHtml);

// d2) 404
const notFoundHtml = render404();
fs.writeFileSync(path.join(PUBLIC_DIR, '404.html'), notFoundHtml);

// e) RSS
let rss = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
<title>AI-Bladet</title>
<description>Sveriges veckotidning om artificiell intelligens — en utgåva i veckan</description>
<link>${SITE_URL}/</link>
<atom:link href="${SITE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
<language>sv</language>`;
for (const i of issues.slice(0, 20)) {
  rss += `
<item>
  <title>${escXml(i.title)} — Vecka ${i.week} ${i.year}</title>
  <description>${escXml(i.summary || '')}</description>
  <link>${SITE_URL}/v/${i.year}/${i.week}/</link>
  <guid>${SITE_URL}/v/${i.year}/${i.week}/</guid>
  <pubDate>${new Date(i.date).toUTCString()}</pubDate>
</item>`;
}
rss += '\n</channel>\n</rss>';
fs.writeFileSync(path.join(PUBLIC_DIR, 'feed.xml'), rss);

// f) Sitemap — SEO: lastmod, changefreq, alla sidor inkl. ordbok/audio/memes
function sitemapUrl(loc, lastmod, changefreq, priority) {
  let entry = `<url>\n    <loc>${loc}</loc>`;
  if (lastmod) entry += `\n    <lastmod>${lastmod}</lastmod>`;
  if (changefreq) entry += `\n    <changefreq>${changefreq}</changefreq>`;
  if (priority) entry += `\n    <priority>${priority}</priority>`;
  entry += `\n  </url>`;
  return entry;
}

let sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">
  ${sitemapUrl(`${SITE_URL}/`, TODAY_ISO, 'daily', '1.0')}
  ${sitemapUrl(`${SITE_URL}/arkiv/`, TODAY_ISO, 'weekly', '0.8')}
  ${sitemapUrl(`${SITE_URL}/om/`, TODAY_ISO, 'monthly', '0.6')}`;

// Issue pages — använd issue-datum som lastmod
for (const i of issues) {
  const issueDate = i.date || TODAY_ISO;
  sitemap += `\n  ${sitemapUrl(`${SITE_URL}/v/${i.year}/${i.week}/`, issueDate, 'weekly', '0.9')}`;
}

// Ordbokssidor — om de finns (skapade av distribution)
const glossaryDir = path.join(PUBLIC_DIR, 'ordbok');
if (fs.existsSync(glossaryDir)) {
  const glossaryFiles = fs.readdirSync(glossaryDir).filter(f => f.endsWith('.html'));
  for (const gf of glossaryFiles) {
    const slug = gf.replace('.html', '');
    sitemap += `\n  ${sitemapUrl(`${SITE_URL}/ordbok/${slug}`, TODAY_ISO, 'weekly', '0.7')}`;
  }
}

// Ljudfiler — om de finns
const audioDir = path.join(PUBLIC_DIR, 'audio');
if (fs.existsSync(audioDir)) {
  const audioFiles = fs.readdirSync(audioDir).filter(f => f.endsWith('.mp3'));
  for (const af of audioFiles) {
    sitemap += `\n  ${sitemapUrl(`${SITE_URL}/audio/${af}`, TODAY_ISO, 'weekly', '0.5')}`;
  }
}

// Memes
const memesDir = path.join(PUBLIC_DIR, 'memes');
if (fs.existsSync(memesDir)) {
  const memeFiles = fs.readdirSync(memesDir).filter(f => f.endsWith('.png'));
  for (const mf of memeFiles) {
    sitemap += `\n  ${sitemapUrl(`${SITE_URL}/memes/${mf}`, TODAY_ISO, 'weekly', '0.5')}`;
  }
}

// Podcast-RSS
const feedDir = path.join(PUBLIC_DIR, 'feed');
if (fs.existsSync(path.join(feedDir || '', 'podcast.xml'))) {
  sitemap += `\n  ${sitemapUrl(`${SITE_URL}/feed/podcast.xml`, TODAY_ISO, 'weekly', '0.6')}`;
}

sitemap += '\n</urlset>';
fs.writeFileSync(path.join(PUBLIC_DIR, 'sitemap.xml'), sitemap);

// g) robots.txt
fs.writeFileSync(path.join(PUBLIC_DIR, 'robots.txt'), 
  `User-agent: *\nAllow: /\nSitemap: ${SITE_URL}/sitemap.xml\n\n# AI-Bladet — full indexing allowed`);

// 4. STATIC
function copyDir(src, dest) {
  if (!fs.existsSync(dest)) fs.mkdirSync(dest, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) copyDir(srcPath, destPath);
    else fs.copyFileSync(srcPath, destPath);
  }
}
if (fs.existsSync(STATIC_DIR)) copyDir(STATIC_DIR, PUBLIC_DIR);

// 5. DONE
const w = latest ? latest.week : '?';
const y = latest ? latest.year : '?';
console.log(`${issues.length} utgåvor byggda, senaste: Vecka ${w} ${y}`);
console.log(`Output: ${PUBLIC_DIR}`);

// SEO: logga sitemap-urls
const sitemapUrls = (sitemap.match(/<loc>/g) || []).length;
console.log(`Sitemap: ${sitemapUrls} URLs`);
