const test = require('node:test');
const assert = require('node:assert/strict');
const dust = require('../static/dust.js');

test('wordmark sampling is capped, deterministic and keeps ink and accent apart', () => {
  const w = 200, h = 60, data = new Uint8ClampedArray(w * h * 4);
  for (let y = 10; y < 50; y++) {
    for (let x = 0; x < w; x++) {
      const i = (y * w + x) * 4;
      if (x < 80) data.set([28, 28, 28, 255], i);
      else if (x >= 100) data.set([196, 18, 48, 255], i);
    }
  }
  const a = dust.sampleWordmark(data, w, h, 1500, 7);
  const b = dust.sampleWordmark(data, w, h, 1500, 7);
  assert.deepEqual(a.buffer, b.buffer);
  assert.ok(a.count >= 600 && a.count <= 1650, String(a.count));
  let ink = 0, red = 0;
  for (let i = 0; i < a.buffer.length; i += 6) {
    const x = a.buffer[i], y = a.buffer[i + 1];
    assert.ok(y >= 10 && y <= 50 + a.step);
    if (a.buffer[i + 5] === 1) { red++; assert.ok(x >= 100); } else { ink++; assert.ok(x < 80 + a.step); }
  }
  assert.ok(ink > 0 && red > 0);
});

test('cover geometry keeps lettering whole in contain mode', () => {
  assert.deepEqual(dust.fitRect(1600, 900, 800, 500, 'contain'), { x: 0, y: 25, w: 800, h: 450 });
  const cover = dust.fitRect(1600, 900, 800, 500, 'cover');
  assert.ok(cover.w >= 800 && cover.h >= 500);
});

test('grains assemble on entry and drift only at the viewport edges while scrolling', () => {
  assert.equal(dust.introAmount(0.4, 0), 1);
  assert.equal(dust.introAmount(0.4, 1), 0);
  assert.equal(dust.edgeZone(500, 1000, 0.22, 0.16), 0);
  assert.ok(dust.edgeZone(990, 1000, 0.22, 0.16) > 0.9);
  assert.ok(dust.edgeZone(5, 1000, 0.22, 0.16) > 0.9);
  assert.ok(dust.dustAmount(1, 0.2, 0) > 0.9, 'a covered edge stays dissolved at rest');
  assert.ok(dust.dustAmount(0.6, 0.2, 0) > dust.dustAmount(0.6, 0.9, 0), 'noise keeps it grainy');
  assert.ok(dust.dustAmount(0.4, 0.1, 1) >= dust.dustAmount(0.4, 0.1, 0), 'scrolling adds a transient burst');
  assert.equal(dust.dustAmount(0, 0.2, 1), 0, 'clear of the band the image stays crisp while scrolling');
});

test('hero pulverises with scroll and grain budgets stay bounded', () => {
  assert.equal(dust.heroProgress(0, 900), 0);
  assert.equal(dust.heroProgress(-900 * 0.62, 900), 1);
  assert.ok(Math.abs(dust.heroProgress(-279, 900) - 0.5) < 0.01);
  const g = dust.cellSize(720, 2, 1440 * 900, 16000);
  assert.ok((1440 * 900) / (g * g) <= 16000);
  assert.ok(dust.cellSize(360, 2, 720 * 405, 8000) >= 6);
});

test('cover grains are device-pixel fine and the read-more ripple sweeps upward', () => {
  assert.equal(dust.grainSize(700 * 394, false), 1);
  assert.equal(dust.grainSize(700 * 394, true), 2);
  assert.ok(dust.kickBand(1, 0.1) > 0.5 && dust.kickBand(0, 0.1) < 0.01);
  assert.ok(dust.kickBand(0, 0.9) > 0.5 && dust.kickBand(1, 0.9) < 0.01);
});

test('float drift is zero mid-view and follows the crossing edge', () => {
  assert.equal(dust.floatOffset({ top: 400, height: 200 }, 1000), 0);
  assert.equal(dust.floatOffset({ top: 240, height: 920 }, 900), 0);
  const entering = dust.floatOffset({ top: 880, height: 300 }, 1000);
  const leaving = dust.floatOffset({ top: -260, height: 300 }, 1000);
  assert.ok(entering > 8, 'entering floats up from below: ' + entering);
  assert.ok(leaving <= -12, 'leaving drifts away upward: ' + leaving);
  assert.ok(entering <= 34 && leaving >= -34);
});
