// Same-origin image relay for the cover particles: WebGL may only sample images that allow CORS.
// GET /cover?u=<https image url> → the image bytes with CORS enabled, cached at the edge for a week.
const MAX_BYTES = 12 * 1024 * 1024;
const ALLOWED_ORIGIN = /^https:\/\/([a-z0-9-]+\.)?ai-bladet\.pages\.dev$|^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/;

function fail(status, msg) {
  return new Response(msg, { status, headers: { 'content-type': 'text/plain; charset=utf-8', 'cache-control': 'no-store' } });
}

export async function onRequestGet(context) {
  const { request } = context;
  const origin = request.headers.get('origin');
  if (origin && !ALLOWED_ORIGIN.test(origin)) return fail(403, 'origin not allowed');
  const raw = new URL(request.url).searchParams.get('u');
  let target;
  try { target = new URL(raw); } catch (e) { return fail(400, 'bad url'); }
  if (target.protocol !== 'https:' || /^(localhost|\d+\.\d+\.\d+\.\d+|\[.*\])$/i.test(target.hostname)) return fail(400, 'https hosts only');

  const cache = caches.default;
  const key = new Request('https://cover-cache.ai-bladet/' + encodeURIComponent(target.href));
  const hit = await cache.match(key);
  if (hit) return hit;

  let upstream;
  try {
    upstream = await fetch(target.href, { headers: { 'user-agent': 'AI-Bladet/1.0 (+https://ai-bladet.pages.dev; cover relay)', accept: 'image/avif,image/webp,image/png,image/jpeg,image/*' }, redirect: 'follow' });
  } catch (e) { return fail(502, 'upstream unreachable'); }
  if (!upstream.ok) return fail(502, 'upstream ' + upstream.status);
  const type = upstream.headers.get('content-type') || '';
  if (!type.startsWith('image/')) return fail(415, 'not an image');
  const length = Number(upstream.headers.get('content-length') || 0);
  if (length > MAX_BYTES) return fail(413, 'too large');
  const body = await upstream.arrayBuffer();
  if (body.byteLength > MAX_BYTES) return fail(413, 'too large');

  const res = new Response(body, {
    headers: {
      'content-type': type,
      'access-control-allow-origin': '*',
      'cache-control': 'public, max-age=604800, immutable',
      'x-content-type-options': 'nosniff',
    },
  });
  context.waitUntil(cache.put(key, res.clone()));
  return res;
}
