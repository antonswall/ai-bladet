/* AI-Bladet — dust engine.
 * Hero: the wordmark as GPU particles that condense from stardust, react to pointer/touch and pulverise on scroll.
 * Covers: press images rendered as sand grains that materialise on entry and drift at the viewport edges while
 * scrolling. Third-party images are only copied with drawImage (never read back), so covers without CORS work. */
(function () {
  'use strict';

  const TAU = Math.PI * 2;
  const BAND = 0.3;
  const SAND_X = 24;
  const SAND_Y = 40;
  const ZONE_BOTTOM = 0.36;
  const ZONE_TOP = 0.26;
  const TILT = 0.12;
  const INV255 = 1 / 255;
  const R2K = 0.6 / 255;

  function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }
  function smoothstep(a, b, v) { const t = clamp((v - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); }
  function rng(seed) {
    let s = seed >>> 0;
    return function () { s = (Math.imul(s, 1664525) + 1013904223) >>> 0; return s / 4294967296; };
  }

  function sampleWordmark(data, width, height, maxCount, seed) {
    let filled = 0;
    for (let i = 3; i < data.length; i += 4) if (data[i] > 127) filled++;
    const step = Math.max(1, Math.ceil(Math.sqrt(filled / Math.max(1, maxCount))));
    const random = rng(seed);
    const out = [];
    for (let y = 0; y < height; y += step) {
      for (let x = 0; x < width; x += step) {
        const i = (y * width + x) * 4;
        if (data[i + 3] <= 127) continue;
        out.push(x + random() * step * 0.55, y + random() * step * 0.55, random(), random(), random(), data[i] > data[i + 1] + 60 ? 1 : 0);
      }
    }
    return { step, count: out.length / 6, buffer: Float32Array.from(out) };
  }

  function fitRect(nw, nh, w, h, fit) {
    if (!nw || !nh || fit === 'fill') return { x: 0, y: 0, w, h };
    const s = fit === 'cover' ? Math.max(w / nw, h / nh) : Math.min(w / nw, h / nh);
    const dw = nw * s, dh = nh * s;
    return { x: (w - dw) / 2, y: (h - dh) / 2, w: dw, h: dh };
  }
  function heroProgress(top, height) { const v = -top / (height * 0.62); return v <= 0 ? 0 : v >= 1 ? 1 : v; }
  function edgeZone(vy, vh, bottom, top) {
    return Math.max(smoothstep(vh * (1 - bottom), vh, vy), 1 - smoothstep(0, vh * top, vy));
  }
  function introAmount(th, assemble) { return 1 - smoothstep(th, th + BAND, assemble * (1 + BAND)); }
  function dustAmount(zone, rnd) { return clamp(zone * 1.5 - rnd * 0.6, 0, 1); }
  function floatOffset(rect, vh) {
    if (rect.top > vh * 0.45) { const t = clamp((rect.top - vh * 0.45) / (vh * 0.55), 0, 1); return 34 * t * t; }
    if (rect.top < vh * 0.15) { const t = clamp((vh * 0.15 - rect.top) / (vh * 0.5), 0, 1); return -34 * t * t; }
    return 0;
  }
  function cellSize(cssWidth, dpr, area, maxCells) {
    let g = Math.round(clamp(cssWidth / 160, 3, 5) * dpr);
    if (area / (g * g) > maxCells) g = Math.ceil(Math.sqrt(area / maxCells));
    return Math.max(2, g);
  }
  function grainSize(area, low) { return low || area > 1600000 ? 2 : 1; }
  function kickBand(ny, progress) { const q = (ny - (1.15 - 1.3 * progress)) / 0.09; return Math.exp(-q * q); }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { sampleWordmark, fitRect, heroProgress, edgeZone, introAmount, dustAmount, cellSize, grainSize, kickBand, floatOffset };
    return;
  }

  const root = document.documentElement;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const saveData = Boolean(navigator.connection && navigator.connection.saveData);
  const coarse = matchMedia('(pointer: coarse)').matches;
  const lowPower = (navigator.hardwareConcurrency || 8) <= 4 || (navigator.deviceMemory || 8) <= 4;
  let storage = null;
  try { storage = window.localStorage; } catch (e) { storage = null; }
  let paused = Boolean(storage && storage.getItem('ab-motion') === 'off');
  const toggles = Array.from(document.querySelectorAll('.motion-toggle'));
  const styles = getComputedStyle(root);
  const INK = styles.getPropertyValue('--ink').trim() || '#1C1C1C';
  const ACCENT = styles.getPropertyValue('--accent').trim() || '#C41230';
  const heroEl = document.querySelector('[data-hero]');
  const covers = [];
  let dustBudget = 0;
  const perf = { n: 0, sum: 0, max: 0 };
  let hero = null, raf = 0, lastNow = 0, lastScroll = window.scrollY, activity = 0, scrollDir = 1, lastHeroVar = '';

  function motionOff() { return paused || reduced.matches || saveData; }
  function setHeroVar(p) { const s = p.toFixed(3); if (s !== lastHeroVar) { root.style.setProperty('--hero-p', s); lastHeroVar = s; } }
  function rgb(hex) {
    const h = hex.replace('#', '');
    const n = parseInt(h.length === 3 ? h.split('').map(c => c + c).join('') : h, 16);
    return [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255];
  }

  function schedule() { if (!raf && !document.hidden) raf = requestAnimationFrame(tick); }
  function tick(now) {
    raf = 0;
    const dt = lastNow ? clamp((now - lastNow) / 1000, 0.001, 0.05) : 1 / 60;
    lastNow = now;
    const y = window.scrollY, v = (y - lastScroll) / dt;
    lastScroll = y;
    if (Math.abs(v) > 6) scrollDir = v > 0 ? 1 : -1;
    const target = motionOff() ? 0 : clamp(Math.abs(v) / 1500, 0, 1);
    activity += (target - activity) * Math.min(1, dt * (target > activity ? 7 : 2.6));
    if (activity < 0.004) activity = 0;
    let busy = activity > 0;
    if (hero && hero.built) { if (hero.frame(dt)) busy = true; }
    else if (heroEl) { const r = heroEl.getBoundingClientRect(); setHeroVar(heroProgress(r.top, r.height)); }
    dustBudget = coarse || lowPower ? 2900 : 6300;
    const t0 = performance.now();
    for (let i = 0; i < covers.length; i++) if (covers[i].visible && covers[i].frame(dt)) busy = true;
    const spent = performance.now() - t0;
    if (spent > 0.05) { perf.n += 1; perf.sum += spent; if (spent > perf.max) perf.max = spent; }
    if (busy) schedule(); else lastNow = 0;
  }

  /* ---------- Hero wordmark (WebGL points) ---------- */
  const VERT = `
attribute vec2 aHome; attribute vec3 aSeed; attribute float aColor;
uniform vec2 uRes; uniform vec2 uOrigin; uniform vec2 uLogo;
uniform float uTime; uniform float uIntro; uniform float uDissolve; uniform float uRadius; uniform float uPoint; uniform float uWind;
uniform vec3 uPointer; uniform vec4 uBurst;
varying float vAlpha; varying float vColor;
void main() {
  vec2 n = aHome / uLogo;
  vec2 pos = uOrigin + aHome;
  pos += vec2(sin(uTime * 1.9 + aSeed.x * 60.0), cos(uTime * 1.6 + aSeed.y * 60.0)) * 0.45;
  float wave = fract(uTime * 0.11) * 1.7 - 0.35;
  float wd = n.x - wave;
  float w = exp(-wd * wd * 80.0);
  pos.y += sin(n.x * 38.0 + uTime * 2.4) * w * 4.0;
  pos.x += w * (aSeed.z - 0.5) * 6.0;
  vec2 d = pos - uPointer.xy;
  float dist = length(d) + 0.001;
  float infl = exp(-(dist * dist) / (uRadius * uRadius)) * uPointer.z;
  vec2 dir = d / dist;
  pos += dir * infl * (12.0 + 34.0 * aSeed.y) + vec2(-dir.y, dir.x) * infl * (aSeed.x - 0.5) * 26.0;
  vec2 bd = pos - uBurst.xy;
  float bdist = length(bd) + 0.001;
  float q = (bdist - uBurst.z * 1100.0) / 80.0;
  pos += bd / bdist * exp(-q * q) * uBurst.w * (14.0 + 30.0 * aSeed.z);
  float ti = clamp((uIntro - aSeed.z * 0.42 - n.x * 0.22) / 0.36, 0.0, 1.0);
  float e = 1.0 - pow(1.0 - ti, 3.0);
  float a0 = aSeed.x * 6.2831853;
  vec2 start = uOrigin + uLogo * 0.5 + vec2(cos(a0), sin(a0)) * (0.15 + aSeed.y) * vec2(uRes.x * 0.6, uRes.y * 0.5);
  pos = mix(start, pos, e);
  float th = n.x * 0.55 + (1.0 - n.y) * 0.12 + aSeed.x * 0.33;
  float local = smoothstep(th, th + 0.26, uDissolve * 1.38);
  float k = local * local;
  float ang = aSeed.y * 6.2831853 + uTime * (0.4 + aSeed.z) + local * 6.0;
  pos += vec2(0.45 + aSeed.y * 0.8, -0.7 - aSeed.z * 0.9) * k * uWind + vec2(cos(ang), sin(ang)) * k * (24.0 + 72.0 * aSeed.z);
  vAlpha = ti * (1.0 - smoothstep(0.55, 1.0, local)) * (1.0 - w * 0.12);
  vColor = aColor;
  gl_PointSize = max(1.0, uPoint * mix(1.0, 0.42, local) * mix(1.8, 1.0, e));
  vec2 clip = pos / uRes * 2.0 - 1.0;
  gl_Position = vec4(clip.x, -clip.y, 0.0, 1.0);
}`;
  const FRAG = `
precision mediump float;
uniform vec3 uInk; uniform vec3 uAccent;
varying float vAlpha; varying float vColor;
void main() {
  if (vAlpha < 0.01) discard;
  gl_FragColor = vec4(mix(uInk, uAccent, vColor) * vAlpha, vAlpha);
}`;

  function compile(gl, type, source) {
    const s = gl.createShader(type);
    gl.shaderSource(s, source);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) { console.warn('AI-Bladet dust shader:', gl.getShaderInfoLog(s)); return null; }
    return s;
  }

  function createHero(section) {
    const logo = section.querySelector('.hero-logo');
    const canvas = document.createElement('canvas');
    canvas.className = 'hero-dust';
    canvas.setAttribute('aria-hidden', 'true');
    let gl = null;
    try { gl = canvas.getContext('webgl', { alpha: true, premultipliedAlpha: true, antialias: false, depth: false, stencil: false, powerPreference: 'high-performance' }); } catch (e) { gl = null; }
    if (!logo || !gl) return null;
    const vs = compile(gl, gl.VERTEX_SHADER, VERT), fs = compile(gl, gl.FRAGMENT_SHADER, FRAG);
    if (!vs || !fs) return null;
    const program = gl.createProgram();
    gl.attachShader(program, vs); gl.attachShader(program, fs); gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) return null;
    const loc = {};
    ['uRes', 'uOrigin', 'uLogo', 'uTime', 'uIntro', 'uDissolve', 'uRadius', 'uPoint', 'uWind', 'uPointer', 'uBurst', 'uInk', 'uAccent']
      .forEach(name => { loc[name] = gl.getUniformLocation(program, name); });
    const aHome = gl.getAttribLocation(program, 'aHome'), aSeed = gl.getAttribLocation(program, 'aSeed'), aColor = gl.getAttribLocation(program, 'aColor');
    const buffer = gl.createBuffer();
    const ink = rgb(INK), accent = rgb(ACCENT);
    const maxParticles = Math.round((coarse ? (innerWidth < 520 ? 42000 : 64000) : (innerWidth > 1700 ? 170000 : 125000)) * (lowPower ? 0.6 : 1));
    const ptr = { x: 0, y: 0, tx: 0, ty: 0, s: 0, ts: 0 };
    const burst = { x: -9999, y: -9999, age: 9 };
    const api = { canvas, built: false, count: 0, grain: 1, width: 0, height: 0, time: 0, intro: 0, p: 0, frames: 0, bursts: 0, lost: false };
    document.body.appendChild(canvas);

    api.build = function () {
      const rect = logo.getBoundingClientRect();
      if (rect.width < 20 || rect.height < 10) return false;
      const scale = Math.min(2, Math.max(1.5, window.devicePixelRatio || 1));
      const w = Math.ceil(rect.width * scale), h = Math.ceil(rect.height * scale);
      const off = document.createElement('canvas');
      off.width = w; off.height = h;
      const ctx = off.getContext('2d', { willReadFrequently: true });
      const cs = getComputedStyle(logo);
      const ls = parseFloat(cs.letterSpacing) || 0;
      ctx.setTransform(scale, 0, 0, scale, 0, 0);
      ctx.font = cs.fontWeight + ' ' + cs.fontSize + ' ' + cs.fontFamily;
      ctx.textBaseline = 'alphabetic';
      const spacing = 'letterSpacing' in ctx;
      if (spacing) ctx.letterSpacing = ls + 'px';
      const ascent = ctx.measureText('AIBladet').fontBoundingBoxAscent || parseFloat(cs.fontSize) * 0.92;
      const range = document.createRange();
      const walker = document.createTreeWalker(logo, NodeFilter.SHOW_TEXT);
      let node;
      while ((node = walker.nextNode())) {
        if (!node.nodeValue.trim()) continue;
        range.selectNodeContents(node);
        const r = range.getBoundingClientRect();
        ctx.fillStyle = node.parentElement.closest('.bladet') ? ACCENT : INK;
        let x = r.left - rect.left;
        const y = r.top - rect.top + ascent;
        if (spacing) ctx.fillText(node.nodeValue, x, y);
        else for (const ch of node.nodeValue) { ctx.fillText(ch, x, y); x += ctx.measureText(ch).width + ls; }
      }
      const sample = sampleWordmark(ctx.getImageData(0, 0, w, h).data, w, h, maxParticles, 11);
      const buf = sample.buffer;
      for (let i = 0; i < buf.length; i += 6) { buf[i] /= scale; buf[i + 1] /= scale; }
      gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
      gl.bufferData(gl.ARRAY_BUFFER, buf, gl.STATIC_DRAW);
      api.count = sample.count; api.grain = sample.step / scale; api.width = rect.width; api.height = rect.height;
      canvas.dataset.particles = String(sample.count);
      return sample.count > 0;
    };
    api.replay = function () { api.intro = 0; };
    api.frame = function (dt) {
      if (api.lost) return false;
      const r = section.getBoundingClientRect();
      const target = heroProgress(r.top, r.height);
      api.p += (target - api.p) * Math.min(1, dt * 8);
      if (Math.abs(target - api.p) < 0.0008) api.p = target;
      setHeroVar(api.p);
      canvas.dataset.p = api.p.toFixed(3);
      if (motionOff()) return false;
      const spent = api.p > 0.995 && target > 0.995;
      canvas.style.visibility = spent ? 'hidden' : '';
      if (spent) return false;
      const lr = logo.getBoundingClientRect();
      if (Math.abs(lr.width - api.width) > 2 && !api.build()) return false;
      api.time += dt;
      api.intro = Math.min(1, api.intro + dt / 2.5);
      ptr.s += (ptr.ts - ptr.s) * Math.min(1, dt * 5);
      ptr.x += (ptr.tx - ptr.x) * Math.min(1, dt * 12);
      ptr.y += (ptr.ty - ptr.y) * Math.min(1, dt * 12);
      burst.age += dt;
      const dpr = Math.min(window.devicePixelRatio || 1, coarse ? 2 : 1.75);
      const W = canvas.clientWidth, H = canvas.clientHeight;
      const bw = Math.round(W * dpr), bh = Math.round(H * dpr);
      if (canvas.width !== bw || canvas.height !== bh) { canvas.width = bw; canvas.height = bh; }
      gl.viewport(0, 0, bw, bh);
      gl.clearColor(0, 0, 0, 0);
      gl.clear(gl.COLOR_BUFFER_BIT);
      gl.useProgram(program);
      gl.enable(gl.BLEND);
      gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
      gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
      gl.enableVertexAttribArray(aHome); gl.vertexAttribPointer(aHome, 2, gl.FLOAT, false, 24, 0);
      gl.enableVertexAttribArray(aSeed); gl.vertexAttribPointer(aSeed, 3, gl.FLOAT, false, 24, 8);
      gl.enableVertexAttribArray(aColor); gl.vertexAttribPointer(aColor, 1, gl.FLOAT, false, 24, 20);
      gl.uniform2f(loc.uRes, W, H);
      gl.uniform2f(loc.uOrigin, lr.left, lr.top);
      gl.uniform2f(loc.uLogo, api.width, api.height);
      gl.uniform1f(loc.uTime, api.time);
      gl.uniform1f(loc.uIntro, api.intro);
      gl.uniform1f(loc.uDissolve, api.p);
      gl.uniform1f(loc.uRadius, Math.max(70, api.height * 0.32));
      gl.uniform1f(loc.uPoint, Math.max(1, api.grain * dpr * 1.4));
      gl.uniform1f(loc.uWind, H * 0.85);
      gl.uniform3f(loc.uPointer, ptr.x, ptr.y, ptr.s);
      gl.uniform4f(loc.uBurst, burst.x, burst.y, burst.age, Math.max(0, 1 - burst.age / 1.3));
      gl.uniform3f(loc.uInk, ink[0], ink[1], ink[2]);
      gl.uniform3f(loc.uAccent, accent[0], accent[1], accent[2]);
      gl.drawArrays(gl.POINTS, 0, api.count);
      api.frames += 1;
      canvas.dataset.frames = String(api.frames);
      canvas.dataset.pointer = ptr.s.toFixed(2);
      return true;
    };

    section.addEventListener('pointermove', e => {
      ptr.tx = e.clientX; ptr.ty = e.clientY;
      if (ptr.s < 0.02) { ptr.x = ptr.tx; ptr.y = ptr.ty; }
      ptr.ts = 1; schedule();
    }, { passive: true });
    section.addEventListener('pointerleave', () => { ptr.ts = 0; schedule(); });
    section.addEventListener('pointerdown', e => {
      if (e.target.closest('a, button')) return;
      burst.x = e.clientX; burst.y = e.clientY; burst.age = 0;
      api.bursts += 1; canvas.dataset.bursts = String(api.bursts);
      schedule();
    });
    canvas.addEventListener('webglcontextlost', e => {
      e.preventDefault(); api.lost = true; api.built = false;
      root.classList.remove('dust-live'); canvas.style.visibility = 'hidden';
    });
    return api;
  }

  function ensureHero() {
    if (hero || !heroEl || motionOff()) return;
    hero = createHero(heroEl);
    if (!hero) { root.classList.remove('dust-pending'); return; }
    const cs = getComputedStyle(heroEl.querySelector('.hero-logo'));
    const fonts = document.fonts;
    Promise.resolve(fonts && fonts.load ? fonts.load(cs.fontWeight + ' ' + cs.fontSize + ' ' + cs.fontFamily, 'AI-Bladet') : null)
      .catch(() => null)
      .then(() => (fonts ? fonts.ready : null))
      .then(() => {
        if (hero && hero.build()) { hero.built = true; if (!motionOff()) root.classList.add('dust-live'); }
        root.classList.remove('dust-pending');
        schedule();
      });
  }

  /* ---------- Cover sand (Canvas 2D, CORS-free, device-pixel grains) ---------- */
  function createCover(frameEl, index) {
    const img = frameEl.querySelector('.figure-img');
    if (!img) return null;
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) return null;
    canvas.className = 'cover-sand';
    canvas.setAttribute('aria-hidden', 'true');
    frameEl.appendChild(canvas);
    const src = document.createElement('canvas');
    const sctx = src.getContext('2d');
    const maskCanvas = document.createElement('canvas');
    const mctx = maskCanvas.getContext('2d');
    const c = { el: frameEl, canvas, visible: false, ready: false, started: false, cleared: false, settled: false, held: false, heldZ: 0, holdAcc: 0, assemble: 0, kick: 0, kicks: 0, time: 0, frames: 0 };
    let dpr = 1, gm = 1, mw = 0, mh = 0, ix = 0, iy = 0, iw = 0, ih = 0, radius = 0, mask = null, data = null, noise = null, noise2 = null, rowState = null;
    let em = 0, ex = null, ey = null, eang = null, esp = null;

    c.layout = function () {
      if (!img.isConnected || !img.complete || !img.naturalWidth) return false;
      const fr = frameEl.getBoundingClientRect();
      const W = fr.width, H = fr.height;
      if (W < 8 || H < 8) return false;
      dpr = Math.min(window.devicePixelRatio || 1, coarse ? 1.25 : 1.5);
      const rightPad = Math.max(SAND_X, Math.ceil(window.innerWidth - (fr.left + W) + SAND_X));
      canvas.style.left = -SAND_X + 'px';
      canvas.style.top = -SAND_Y + 'px';
      canvas.style.width = (W + SAND_X + rightPad) + 'px';
      canvas.style.height = (H + SAND_Y * 2) + 'px';
      canvas.width = Math.round((W + SAND_X + rightPad) * dpr);
      canvas.height = Math.round((H + SAND_Y * 2) * dpr);
      src.width = Math.round(W * dpr);
      src.height = Math.round(H * dpr);
      const r = fitRect(img.naturalWidth, img.naturalHeight, W, H, getComputedStyle(img).objectFit);
      sctx.clearRect(0, 0, src.width, src.height);
      try { sctx.drawImage(img, r.x * dpr, r.y * dpr, r.w * dpr, r.h * dpr); } catch (e) { return false; }
      ix = Math.max(0, Math.round(r.x * dpr));
      iy = Math.max(0, Math.round(r.y * dpr));
      iw = Math.min(src.width, Math.round((r.x + r.w) * dpr)) - ix;
      ih = Math.min(src.height, Math.round((r.y + r.h) * dpr)) - iy;
      gm = grainSize(iw * ih, lowPower);
      mw = Math.ceil(iw / gm); mh = Math.ceil(ih / gm);
      maskCanvas.width = mw; maskCanvas.height = mh;
      mask = mctx.createImageData(mw, mh);
      data = mask.data;
      noise = new Uint8Array(mw * mh); noise2 = new Uint8Array(mw * mh);
      rowState = new Uint8Array(mh);
      const random = rng(97 + index * 7919);
      for (let i = 0; i < noise.length; i++) { noise[i] = (random() * 256) | 0; noise2[i] = (random() * 256) | 0; }

      em = Math.round(clamp(W * H * (coarse ? 0.075 : 0.062), 3200, coarse || lowPower ? 6500 : 19000));
      ex = new Float32Array(em); ey = new Float32Array(em); eang = new Float32Array(em); esp = new Float32Array(em);
      for (let k = 0; k < em; k++) { ex[k] = Math.floor(random() * mw); ey[k] = Math.floor(random() * mh); eang[k] = random() * TAU; esp[k] = random(); }
      radius = (parseFloat(getComputedStyle(frameEl).borderTopLeftRadius) || 0) * dpr;
      c.ready = true; c.settled = false; c.cleared = false;
      if (!motionOff()) frameEl.classList.add('is-sand');
      canvas.dataset.cells = String(mw * mh);
      canvas.dataset.grain = String(gm);
      canvas.dataset.emitters = String(em);
      return true;
    };

    function clipImage() {
      const x = SAND_X * dpr + ix, y = SAND_Y * dpr + iy;
      ctx.beginPath();
      if (ctx.roundRect) ctx.roundRect(x, y, iw, ih, Math.min(radius, iw / 2, ih / 2)); else ctx.rect(x, y, iw, ih);
      ctx.clip();
    }
    function drawFull() {
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.save(); clipImage();
      ctx.drawImage(src, ix, iy, iw, ih, SAND_X * dpr + ix, SAND_Y * dpr + iy, iw, ih);
      ctx.restore();
    }
    function amount(n, r2, rowFrac, A, introLive, zone, kickW) {
      let d = 0;
      if (introLive) { const th = 0.62 * rowFrac + 0.38 * n; d = 1 - smoothstep(th, th + BAND, A); }
      if (d < 1) {
        { const dd = dustAmount(zone, r2); if (dd > d) d = dd; }
        if (kickW > 0) { const dk = clamp(kickW * 1.25 - r2 * 0.55, 0, 1); if (dk > d) d = dk; }
      }
      return d;
    }
    function fillAlpha(start, x0, x1, v) { for (let i = (start + x0) * 4 + 3, end = (start + x1) * 4 + 3; i < end; i += 4) data[i] = v; }
    function driftSpan(start, x0, x1, zone, tz) {
      for (let mx = x0, p = start + x0, i = p * 4 + 3; mx < x1; mx++, p++, i += 4) {
        let z = zone + (mx - mw * 0.5) * tz; if (z < 0) z = 0; else if (z > 1) z = 1;
        data[i] = z * 1.5 - noise2[p] * R2K < 0.04 ? 255 : 0;
      }
    }
    function drawGrains(fr, vh) {
      const A = c.assemble * (1 + BAND), introLive = c.assemble < 1, kicking = c.kick > 0;
      let lo = mh, hi = -1;
      for (let my = 0; my < mh; my++) {
        const vy = fr.top + (iy + my * gm + gm / 2) / dpr;
        if (vy < -60 || vy > vh + 60) continue;
        const rowFrac = my / mh;
        const rowIntro = introLive && A < 0.62 * rowFrac + 0.38 + BAND;
        const kickW = kicking ? kickBand(rowFrac, 1 - c.kick) : 0;
        const start = my * mw;
        const still = activity === 0 && kickW < 0.01;
        const zone = edgeZone(vy, vh, ZONE_BOTTOM, ZONE_TOP);
        const tz = -TILT * iw * ((edgeZone(vy + 8, vh, ZONE_BOTTOM, ZONE_TOP) - edgeZone(vy - 8, vh, ZONE_BOTTOM, ZONE_TOP)) / 16) / mw;
        if (still && rowIntro) {
          if (A <= 0.62 * rowFrac) { if (rowState[my] !== 2) { fillAlpha(start, 0, mw, 0); rowState[my] = 2; if (my < lo) lo = my; if (my > hi) hi = my; } continue; }
          rowState[my] = 0;
          const base = 0.62 * rowFrac + 0.264;
          for (let p = start, i = p * 4 + 3, end = start + mw; p < end; p++, i += 4) data[i] = A > base + 0.38 * noise[p] * INV255 ? 255 : 0;
          if (my < lo) lo = my; if (my > hi) hi = my;
          continue;
        }
        if (still) {
          if (zone === 0 && tz === 0) {
            if (rowState[my] !== 1) { fillAlpha(start, 0, mw, 255); rowState[my] = 1; if (my < lo) lo = my; if (my > hi) hi = my; }
            continue;
          }
          rowState[my] = 0;
          driftSpan(start, 0, mw, zone, tz);
          if (my < lo) lo = my; if (my > hi) hi = my;
          continue;
        }
        if (my < lo) lo = my; if (my > hi) hi = my;
        rowState[my] = 0;
        for (let mx = 0, p = start, i = p * 4 + 3; mx < mw; mx++, p++, i += 4) {
          let z = zone + (mx - mw * 0.5) * tz; if (z < 0) z = 0; else if (z > 1) z = 1;
          data[i] = amount(noise[p] * INV255, noise2[p] * INV255, rowFrac, A, rowIntro, z, kickW) < 0.04 ? 255 : 0;
        }
      }
      if (hi >= lo) mctx.putImageData(mask, 0, 0, 0, lo, mw, hi - lo + 1);
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const ox = SAND_X * dpr + ix, oy = SAND_Y * dpr + iy;
      ctx.save(); clipImage();
      ctx.drawImage(src, ix, iy, iw, ih, ox, oy, iw, ih);
      ctx.globalCompositeOperation = 'destination-in';
      ctx.imageSmoothingEnabled = false;
      ctx.drawImage(maskCanvas, 0, 0, mw, mh, ox, oy, mw * gm, mh * gm);
      ctx.restore();
      const t = c.time;
      for (let k = 0; k < em; k++) {
        const mx = ex[k], my = ey[k], st = rowState[my];
        if (st === 1 || st === 2) continue;
        const vy = fr.top + (iy + my * gm) / dpr;
        if (vy < -60 || vy > vh + 60) continue;
        const rowFrac = my / mh;
        const rowIntro = introLive && A < 0.62 * rowFrac + 0.38 + BAND;
        const kickW = kicking ? kickBand(rowFrac, 1 - c.kick) : 0;
        const ez = edgeZone(vy, vh, ZONE_BOTTOM, ZONE_TOP);
        if (!rowIntro && activity === 0 && kickW < 0.01 && ez === 0) continue;
        const p = my * mw + mx;
        const d = amount(noise[p] * INV255, noise2[p] * INV255, rowFrac, A, rowIntro, ez, kickW);
        if (d <= 0.04 || d >= 0.995) continue;
        const e = d * d;
        const spread = (6 + 46 * esp[k]) * dpr * e;
        const wob = 0.2 + 0.8 * activity;
        let dx = Math.cos(eang[k]) * spread * 0.9 + Math.cos(eang[k] + t * 0.8) * spread * 0.6 * wob;
        let dy = Math.sin(eang[k]) * spread * 0.9 + Math.sin(eang[k] + t * 0.8) * spread * 0.6 * wob;
        if (rowIntro) dy += 46 * dpr * e;
        else if (kickW >= 0.01) dy -= 34 * dpr * e;
        else { dx += (90 + 210 * esp[k]) * dpr * e; dy += (-26 + 52 * esp[k]) * dpr * e; }
        if (dustBudget <= 0) break;
        dustBudget -= 1;
        const s = gm * (1.1 - 0.6 * d);
        ctx.globalAlpha = Math.max(0.14, 1 - Math.pow(d, 2.4));
        ctx.drawImage(src, ix + mx * gm, iy + my * gm, 1, 1, ox + mx * gm + dx, oy + my * gm + dy, s, s);
      }
      ctx.globalAlpha = 1;
    }

    c.frame = function (dt) {
      if (!c.ready || motionOff()) return false;
      const fr = frameEl.getBoundingClientRect();
      const vh = window.innerHeight;
      if (!c.started) {
        if (fr.top < vh * 0.88 && fr.bottom > vh * 0.03) { c.started = true; rowState.fill(0); canvas.dataset.state = 'assembling'; }
        else {
          if (!c.cleared) { ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, canvas.width, canvas.height); c.cleared = true; }
          return false;
        }
      }
      c.time += dt;
      if (c.assemble < 1) c.assemble = Math.min(1, c.assemble + dt / 1.6);
      if (c.kick > 0) c.kick = Math.max(0, c.kick - dt / 1.25);
      const off = floatOffset(fr, vh);
      canvas.style.transform = off ? 'translateY(' + off.toFixed(1) + 'px)' : '';
      const zoneEdges = Math.max(edgeZone(fr.top, vh, ZONE_BOTTOM, ZONE_TOP), edgeZone(fr.bottom, vh, ZONE_BOTTOM, ZONE_TOP));
      if (c.assemble >= 1 && activity === 0 && c.kick === 0) {
        if (zoneEdges < 0.035) {
          if (!c.settled) { drawFull(); c.settled = true; c.held = false; rowState.fill(0); canvas.dataset.state = 'settled'; }
          return off !== 0;
        }
        c.settled = false;
        c.holdAcc += dt;
        if (c.held && Math.abs(zoneEdges - c.heldZ) < 0.004 && c.holdAcc < 0.25) return true;
        c.held = true; c.heldZ = zoneEdges; c.holdAcc = 0;
        canvas.dataset.state = 'drifting';
        drawGrains(fr, vh);
        c.frames += 1;
        canvas.dataset.frames = String(c.frames);
        return true;
      }
      c.settled = false; c.held = false;
      canvas.dataset.state = c.assemble < 1 ? 'assembling' : c.kick > 0 ? 'rippling' : 'drifting';
      drawGrains(fr, vh);
      c.frames += 1;
      canvas.dataset.frames = String(c.frames);
      return true;
    };
    c.ripple = function () {
      if (!c.ready || motionOff()) return;
      c.kick = 1; c.kicks += 1; canvas.dataset.kicks = String(c.kicks);
      schedule();
    };
    return c;
  }

  function setupCovers() {
    const frames = Array.from(document.querySelectorAll('.lead-figure .figure-frame, .story-figure .figure-frame'));
    if (!frames.length || !('IntersectionObserver' in window)) return;
    const find = el => covers.find(c => c.el === el);
    const io = new IntersectionObserver(entries => {
      entries.forEach(entry => { const c = find(entry.target); if (c) c.visible = entry.isIntersecting; });
      schedule();
    }, { rootMargin: '30% 0px' });
    const ro = 'ResizeObserver' in window ? new ResizeObserver(entries => {
      entries.forEach(entry => { const c = find(entry.target); if (c && c.ready) c.layout(); });
      schedule();
    }) : null;
    frames.forEach((frameEl, i) => {
      const c = createCover(frameEl, i);
      if (!c) return;
      covers.push(c);
      io.observe(frameEl);
      if (ro) ro.observe(frameEl);
      const img = frameEl.querySelector('.figure-img');
      const ready = () => { if (c.layout()) schedule(); };
      if (img.complete && img.naturalWidth) ready(); else img.addEventListener('load', ready, { once: true });
      img.addEventListener('error', () => { frameEl.classList.remove('is-sand'); c.ready = false; }, { once: true });
    });
  }

  function syncMotion() {
    const off = motionOff();
    toggles.forEach(btn => {
      btn.hidden = reduced.matches || saveData;
      btn.setAttribute('aria-pressed', String(paused));
      btn.textContent = paused ? 'Starta rörelse' : 'Pausa rörelse';
    });
    root.classList.toggle('motion-paused', off);
    if (off) {
      root.classList.remove('dust-live', 'dust-pending');
      if (hero) hero.canvas.style.visibility = 'hidden';
      covers.forEach(c => c.el.classList.remove('is-sand'));
    } else {
      ensureHero();
      if (hero && hero.built) { root.classList.add('dust-live'); hero.canvas.style.visibility = ''; hero.replay(); }
      covers.forEach(c => {
        c.settled = false; c.started = false; c.cleared = false; c.held = false; c.holdAcc = 0; c.assemble = 0;
        if (c.ready || c.layout()) c.el.classList.add('is-sand');
      });
    }
    lastNow = 0;
    schedule();
  }

  document.addEventListener('click', e => {
    const btn = e.target.closest && e.target.closest('.story-more');
    if (!btn || motionOff()) return;
    const wrap = document.getElementById(btn.getAttribute('aria-controls'));
    if (!wrap || !wrap.animate) return;
    const card = btn.closest('.story-card');
    const cover = card && covers.find(c => card.contains(c.el));
    const open = btn.getAttribute('aria-expanded') === 'true';
    const ease = 'cubic-bezier(.23, 1, .32, 1)';
    wrap.getAnimations().forEach(a => a.cancel());
    wrap.hidden = false;
    wrap.style.overflow = 'hidden';
    const h = wrap.scrollHeight;
    const anim = open
      ? wrap.animate([{ height: '0px', opacity: 0 }, { height: h + 'px', opacity: 1 }], { duration: 560, easing: ease })
      : wrap.animate([{ height: h + 'px', opacity: 1 }, { height: '0px', opacity: 0 }], { duration: 380, easing: 'cubic-bezier(.4, 0, .2, 1)' });
    anim.onfinish = () => {
      wrap.style.overflow = '';
      if (btn.getAttribute('aria-expanded') === 'false') wrap.hidden = true;
    };
    if (open) Array.from(wrap.children).forEach((el, i) => el.animate(
      [{ opacity: 0, transform: 'translateY(14px)', filter: 'blur(7px)' }, { opacity: 1, transform: 'none', filter: 'blur(0px)' }],
      { duration: 640, delay: 90 + i * 75, easing: ease, fill: 'backwards' }));
    if (cover) cover.ripple();
  });
  root.classList.add('dust-ready');
  setupCovers();
  syncMotion();
  toggles.forEach(btn => btn.addEventListener('click', () => {
    paused = !paused;
    try { if (storage) storage.setItem('ab-motion', paused ? 'off' : 'on'); } catch (e) { /* private mode */ }
    syncMotion();
  }));
  if (reduced.addEventListener) reduced.addEventListener('change', syncMotion); else if (reduced.addListener) reduced.addListener(syncMotion);
  const bar = document.querySelector('.site-bar'), sentinel = document.querySelector('.bar-sentinel');
  if (bar && sentinel && 'IntersectionObserver' in window) {
    new IntersectionObserver(([entry]) => {
      bar.classList.toggle('is-stuck', !entry.isIntersecting && entry.boundingClientRect.top < 0);
    }).observe(sentinel);
  }
  addEventListener('scroll', schedule, { passive: true });
  let lastInnerW = window.innerWidth;
  addEventListener('resize', () => { lastNow = 0; if (window.innerWidth !== lastInnerW) { lastInnerW = window.innerWidth; covers.forEach(cv2 => { if (cv2.ready) cv2.layout(); }); } schedule(); }, { passive: true });
  document.addEventListener('visibilitychange', () => { lastNow = 0; schedule(); });
  window.AIBladetDust = Object.freeze({ get activity() { return activity; }, get motionOff() { return motionOff(); }, get coverFrame() { return { avg: perf.n ? +(perf.sum / perf.n).toFixed(2) : 0, max: +perf.max.toFixed(2), n: perf.n }; }, resetPerf() { perf.n = 0; perf.sum = 0; perf.max = 0; } });
})();
