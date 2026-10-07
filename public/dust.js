/* AI-Bladet — dust engine.
 * Hero: the wordmark as GPU particles that condense from stardust, react to pointer/touch and pulverise on scroll.
 * Covers: every press image is rendered with the wordmark's exact particle shader (same wind, swirl, fade and shrink),
 * coloured by the image as a WebGL texture, and stays particles (shimmer + wave) even mid-view and at rest. Its dissolve is
 * driven by the cover's position at the viewport edges, the way the wordmark's is driven by the hero's scroll. The wind
 * blows mostly rightwards (shallower than the wordmark's) and is mirrored at the bottom edge so the dust stays off-screen. Images without CORS are fetched through the same-origin /cover proxy. */
(function () {
  'use strict';

  const ZONE_BOTTOM = 0.26;
  const ZONE_TOP = 0.18;

  function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }
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
  function coverProgress(top, bottom, vh) {
    const h = Math.max(1, bottom - top);
    const up = (ZONE_TOP * vh - top) / (ZONE_TOP * vh + h);
    const down = (bottom - (1 - ZONE_BOTTOM) * vh) / (ZONE_BOTTOM * vh + h);
    return clamp(Math.max(up, down), 0, 1);
  }
  function coverGrid(r, W, H, radius, budget, seed) {
    const x0 = Math.max(0, r.x), y0 = Math.max(0, r.y), x1 = Math.min(W, r.x + r.w), y1 = Math.min(H, r.y + r.h);
    if (x1 <= x0 || y1 <= y0) return { step: 1, count: 0, buffer: new Float32Array(0) };
    const step = Math.max(1, Math.sqrt(((x1 - x0) * (y1 - y0)) / Math.max(1, budget)));
    const random = rng(seed);
    const rad = Math.min(radius, (x1 - x0) / 2, (y1 - y0) / 2);
    const out = [];
    for (let fy = y0; fy < y1; fy += step) {
      for (let fx = x0; fx < x1; fx += step) {
        const px = Math.min(x1 - 0.01, fx + random() * step * 0.55), py = Math.min(y1 - 0.01, fy + random() * step * 0.55);
        if (rad > 0) {
          const cx = px < x0 + rad ? x0 + rad : px > x1 - rad ? x1 - rad : px;
          const cy = py < y0 + rad ? y0 + rad : py > y1 - rad ? y1 - rad : py;
          const dx = px - cx, dy = py - cy;
          if (dx * dx + dy * dy > rad * rad) { random(); random(); random(); continue; }
        }
        out.push(px - r.x, py - r.y, random(), random(), random());
      }
    }
    return { step, count: out.length / 5, buffer: Float32Array.from(out) };
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { sampleWordmark, fitRect, heroProgress, coverProgress, coverGrid };
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
  const perf = { n: 0, sum: 0, max: 0 };
  let hero = null, raf = 0, lastNow = 0, lastScroll = window.scrollY, activity = 0, lastHeroVar = '';

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
    const target = motionOff() ? 0 : clamp(Math.abs(v) / 1500, 0, 1);
    activity += (target - activity) * Math.min(1, dt * (target > activity ? 7 : 2.6));
    if (activity < 0.004) activity = 0;
    let busy = false;
    if (hero && hero.built) { if (hero.frame(dt)) busy = true; }
    else if (heroEl) { const r = heroEl.getBoundingClientRect(); setHeroVar(heroProgress(r.top, r.height)); }
    const t0 = performance.now();
    if (drawCovers(dt)) busy = true;
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

  /* ---------- Cover dust (WebGL points — the wordmark's exact particle shader, coloured by the press image) ---------- */
  const COVER_VERT = `
attribute vec2 aHome; attribute vec3 aSeed;
uniform vec2 uRes; uniform vec2 uOrigin; uniform vec2 uLogo;
uniform float uTime; uniform float uDissolve; uniform float uRadius; uniform float uPoint; uniform float uWind; uniform float uFlip;
uniform vec3 uPointer; uniform vec4 uBurst;
varying float vAlpha; varying vec2 vUv;
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
  float th = n.x * 0.55 + (1.0 - n.y) * 0.12 + aSeed.x * 0.33;
  float local = smoothstep(th, th + 0.26, uDissolve * 1.38);
  float k = local * local;
  float ang = aSeed.y * 6.2831853 + uTime * (0.4 + aSeed.z) + local * 6.0;
  pos += vec2(1.25 + aSeed.y * 0.8, (-0.35 - aSeed.z * 0.35) * uFlip) * k * uWind + vec2(cos(ang), sin(ang)) * k * (24.0 + 72.0 * aSeed.z);
  vAlpha = (1.0 - smoothstep(0.55, 1.0, local)) * (1.0 - w * 0.12);
  vUv = n;
  gl_PointSize = max(1.0, uPoint * mix(1.0, 0.42, local));
  vec2 clip = pos / uRes * 2.0 - 1.0;
  gl_Position = vec4(clip.x, -clip.y, 0.0, 1.0);
}`;
  const COVER_FRAG = `
precision mediump float;
uniform sampler2D uTex;
varying float vAlpha; varying vec2 vUv;
void main() {
  if (vAlpha < 0.01) discard;
  gl_FragColor = texture2D(uTex, vUv) * vAlpha;
}`;
  const COVER_STRIDE = 5;
  let coverGL = null;
  let coverTime = 0;

  function createCoverGL() {
    const canvas = document.createElement('canvas');
    canvas.className = 'cover-dust';
    canvas.setAttribute('aria-hidden', 'true');
    let gl = null;
    try { gl = canvas.getContext('webgl', { alpha: true, premultipliedAlpha: true, antialias: false, depth: false, stencil: false, powerPreference: 'high-performance' }); } catch (e) { gl = null; }
    if (!gl) return null;
    const vs = compile(gl, gl.VERTEX_SHADER, COVER_VERT), fs = compile(gl, gl.FRAGMENT_SHADER, COVER_FRAG);
    if (!vs || !fs) return null;
    const program = gl.createProgram();
    gl.attachShader(program, vs); gl.attachShader(program, fs); gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) return null;
    const loc = {};
    ['uRes', 'uOrigin', 'uLogo', 'uTime', 'uDissolve', 'uRadius', 'uPoint', 'uWind', 'uFlip', 'uPointer', 'uBurst', 'uTex']
      .forEach(name => { loc[name] = gl.getUniformLocation(program, name); });
    const g = { gl, canvas, program, loc, aHome: gl.getAttribLocation(program, 'aHome'), aSeed: gl.getAttribLocation(program, 'aSeed'), dirty: false, lost: false, W: 0, H: 0, dpr: 1 };
    canvas.addEventListener('webglcontextlost', e => {
      e.preventDefault(); g.lost = true;
      covers.forEach(c => { c.el.classList.remove('is-dust'); c.ready = false; });
    });
    document.body.appendChild(canvas);
    return g;
  }

  function loadCoverImage(url) {
    const attempt = src => new Promise((resolve, reject) => {
      const im = new Image();
      im.crossOrigin = 'anonymous';
      im.decoding = 'async';
      im.onload = () => resolve(im);
      im.onerror = reject;
      im.src = src;
    });
    if (new URL(url, location.href).origin === location.origin) return attempt(url);
    return attempt('/cover?u=' + encodeURIComponent(url));
  }

  function createCover(frameEl, index) {
    const img = frameEl.querySelector('.figure-img');
    if (!img || !coverGL) return null;
    const { gl } = coverGL;
    const c = { el: frameEl, visible: false, ready: false, loading: false, failed: false, p: 0, dust: false, frames: 0, kicks: 0, count: 0, step: 1, rect: null, tex: null, buffer: null, w: 0, h: 0, nw: 0, nh: 0 };
    const burst = { x: -9999, y: -9999, age: 9 };

    function upload(source) {
      const max = 1600;
      const s = Math.min(1, max / Math.max(source.naturalWidth, source.naturalHeight));
      const cw = Math.max(1, Math.round(source.naturalWidth * s)), ch = Math.max(1, Math.round(source.naturalHeight * s));
      const off = document.createElement('canvas');
      off.width = cw; off.height = ch;
      off.getContext('2d').drawImage(source, 0, 0, cw, ch);
      c.nw = source.naturalWidth; c.nh = source.naturalHeight;
      c.tex = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, c.tex);
      gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, true);
      gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, off);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    }

    c.load = function () {
      if (c.loading || c.tex || c.failed || !img.isConnected) return;
      c.loading = true;
      loadCoverImage(img.currentSrc || img.src).then(im => {
        if (coverGL.lost) return;
        upload(im);
        c.loading = false;
        if (c.layout()) schedule();
      }).catch(() => { c.loading = false; c.failed = true; frameEl.dataset.dust = 'unavailable'; });
    };

    c.layout = function () {
      if (!c.tex || !c.nw) return false;
      const fr = frameEl.getBoundingClientRect();
      const W = fr.width, H = fr.height;
      if (W < 8 || H < 8) return false;
      const r = fitRect(c.nw, c.nh, W, H, getComputedStyle(img).objectFit);
      const radius = parseFloat(getComputedStyle(frameEl).borderTopLeftRadius) || 0;
      const budget = Math.round((coarse ? 60000 : 150000) * (lowPower ? 0.6 : 1));
      const grid = coverGrid(r, W, H, radius, budget, 101 + index * 7919);
      c.buffer = c.buffer || gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, c.buffer);
      gl.bufferData(gl.ARRAY_BUFFER, grid.buffer, gl.STATIC_DRAW);
      c.count = grid.count; c.step = grid.step; c.rect = r; c.w = W; c.h = H;
      c.ready = c.count > 0;
      frameEl.dataset.particles = String(c.count);
      if (c.ready && !motionOff()) frameEl.classList.add('is-sand');
      return c.ready;
    };

    c.frame = function (dt, g) {
      if (!c.ready || motionOff()) return false;
      const fr = frameEl.getBoundingClientRect();
      if (Math.abs(fr.width - c.w) > 1 || Math.abs(fr.height - c.h) > 1) { if (!c.layout()) return false; }
      const target = coverProgress(fr.top, fr.bottom, window.innerHeight);
      c.p += (target - c.p) * Math.min(1, dt * 8);
      if (Math.abs(target - c.p) < 0.0008) c.p = target;
      burst.age += dt;
      const bursting = burst.age < 1.3;
      if (!c.dust) { c.dust = true; frameEl.classList.add('is-dust'); }
      frameEl.dataset.p = c.p.toFixed(3);
      frameEl.dataset.state = bursting ? 'burst' : c.p > 0.002 ? 'dust' : 'live';
      if (c.p >= 0.915 && !bursting) return Math.abs(target - c.p) > 0;
      const { gl: ctx, loc } = g;
      ctx.bindBuffer(ctx.ARRAY_BUFFER, c.buffer);
      ctx.enableVertexAttribArray(g.aHome); ctx.vertexAttribPointer(g.aHome, 2, ctx.FLOAT, false, COVER_STRIDE * 4, 0);
      ctx.enableVertexAttribArray(g.aSeed); ctx.vertexAttribPointer(g.aSeed, 3, ctx.FLOAT, false, COVER_STRIDE * 4, 8);
      ctx.activeTexture(ctx.TEXTURE0);
      ctx.bindTexture(ctx.TEXTURE_2D, c.tex);
      ctx.uniform1i(loc.uTex, 0);
      ctx.uniform2f(loc.uOrigin, fr.left + c.rect.x, fr.top + c.rect.y);
      ctx.uniform2f(loc.uLogo, c.rect.w, c.rect.h);
      ctx.uniform1f(loc.uDissolve, c.p);
      ctx.uniform1f(loc.uFlip, (fr.top + fr.bottom) / 2 > window.innerHeight / 2 ? -1 : 1);
      ctx.uniform1f(loc.uRadius, Math.max(70, c.h * 0.32));
      ctx.uniform1f(loc.uPoint, Math.max(1, (c.step * 1.7 + 0.6) * g.dpr));
      ctx.uniform4f(loc.uBurst, burst.x, burst.y, burst.age, Math.max(0, 1 - burst.age / 1.3));
      ctx.drawArrays(ctx.POINTS, 0, c.count);
      c.frames += 1;
      frameEl.dataset.frames = String(c.frames);
      return true;
    };

    c.ripple = function (x, y) {
      if (!c.ready || motionOff()) return;
      const fr = frameEl.getBoundingClientRect();
      burst.x = x == null ? fr.left + fr.width / 2 : x;
      burst.y = y == null ? fr.bottom : y;
      burst.age = 0;
      c.kicks += 1; frameEl.dataset.kicks = String(c.kicks);
      schedule();
    };
    c.reset = function () { const fr = frameEl.getBoundingClientRect(); c.p = coverProgress(fr.top, fr.bottom, window.innerHeight); burst.age = 9; };
    return c;
  }

  function drawCovers(dt) {
    const g = coverGL;
    if (!g || g.lost) return false;
    const { gl, canvas, loc } = g;
    let active = false;
    for (let i = 0; i < covers.length; i++) if (covers[i].visible && covers[i].ready && !motionOff()) { active = true; break; }
    if (!active) {
      if (g.dirty) { gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT); g.dirty = false; }
      covers.forEach(c => { if (c.dust && !c.visible) { c.dust = false; c.el.classList.remove('is-dust'); } });
      return false;
    }
    coverTime += dt;
    g.dpr = Math.min(window.devicePixelRatio || 1, coarse ? 2 : 1.75);
    const W = canvas.clientWidth, H = canvas.clientHeight;
    const bw = Math.round(W * g.dpr), bh = Math.round(H * g.dpr);
    if (canvas.width !== bw || canvas.height !== bh) { canvas.width = bw; canvas.height = bh; }
    gl.viewport(0, 0, bw, bh);
    gl.clearColor(0, 0, 0, 0);
    gl.clear(gl.COLOR_BUFFER_BIT);
    gl.useProgram(g.program);
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
    gl.uniform2f(loc.uRes, W, H);
    gl.uniform1f(loc.uTime, coverTime);
    gl.uniform1f(loc.uWind, H * 0.85);
    gl.uniform3f(loc.uPointer, 0, 0, 0);
    let busy = false;
    for (let i = 0; i < covers.length; i++) {
      const c = covers[i];
      if (!c.visible) { if (c.dust) { c.dust = false; c.el.classList.remove('is-dust'); } continue; }
      if (c.frame(dt, g)) busy = true;
    }
    g.dirty = true;
    return busy;
  }

  function setupCovers() {
    const frames = Array.from(document.querySelectorAll('.lead-figure .figure-frame, .story-figure .figure-frame'));
    if (!frames.length || !('IntersectionObserver' in window)) return;
    coverGL = createCoverGL();
    if (!coverGL) return;
    const find = el => covers.find(c => c.el === el);
    const io = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        const c = find(entry.target);
        if (!c) return;
        c.visible = entry.isIntersecting;
        if (c.visible && !motionOff()) c.load();
      });
      schedule();
    }, { rootMargin: '60% 0px' });
    frames.forEach((frameEl, i) => {
      const c = createCover(frameEl, i);
      if (!c) return;
      covers.push(c);
      io.observe(frameEl);
      const img = frameEl.querySelector('.figure-img');
      img.addEventListener('error', () => { frameEl.classList.remove('is-sand', 'is-dust'); c.ready = false; c.failed = true; }, { once: true });
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
      covers.forEach(c => { c.dust = false; c.el.classList.remove('is-sand', 'is-dust'); });
      if (coverGL && !coverGL.lost) { coverGL.gl.clearColor(0, 0, 0, 0); coverGL.gl.clear(coverGL.gl.COLOR_BUFFER_BIT); coverGL.dirty = false; }
    } else {
      ensureHero();
      if (hero && hero.built) { root.classList.add('dust-live'); hero.canvas.style.visibility = ''; hero.replay(); }
      covers.forEach(c => {
        if (c.ready) { c.reset(); c.el.classList.add('is-sand'); } else if (c.visible) c.load();
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
    if (cover) cover.ripple(e.clientX || null, e.clientY || null);
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
