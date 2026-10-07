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

test('hero pulverises with scroll', () => {
  assert.equal(dust.heroProgress(0, 900), 0);
  assert.equal(dust.heroProgress(-900 * 0.62, 900), 1);
  assert.ok(Math.abs(dust.heroProgress(-279, 900) - 0.5) < 0.01);
});

test('covers dissolve like the wordmark only at the viewport edges, by position', () => {
  const vh = 1000;
  assert.equal(dust.coverProgress(400, 700, vh), 0, 'mid-view the image is whole');
  assert.equal(dust.coverProgress(180, 480, vh), 0, 'touching the top line it has not started');
  assert.equal(dust.coverProgress(440, 740, vh), 0, 'touching the bottom line it has not started');
  const leaving = dust.coverProgress(-60, 240, vh);
  assert.ok(leaving > 0.4 && leaving < 0.6, 'half way out it is half dust: ' + leaving);
  assert.equal(dust.coverProgress(-300, 0, vh), 1, 'gone at the top edge');
  assert.equal(dust.coverProgress(1000, 1300, vh), 1, 'fully below it is still dust and assembles on entry');
  const entering = dust.coverProgress(850, 1150, vh);
  assert.ok(entering > 0.3 && entering < 0.8, 'entering assembles: ' + entering);
  assert.equal(dust.coverProgress(-60, 240, vh), leaving, 'pure function of position: stopping freezes it');
  // the wordmark's local dissolve reaches 1 for every particle once uDissolve * 1.38 >= 1.26
  assert.ok(dust.coverProgress(-260, 40, vh) * 1.38 >= 1.2);
});

test('cover particles fill the visible image rect, respect rounded corners and stay within budget', () => {
  const r = { x: 0, y: 0, w: 400, h: 225 };
  const a = dust.coverGrid(r, 400, 225, 0, 30000, 5);
  const b = dust.coverGrid(r, 400, 225, 0, 30000, 5);
  assert.deepEqual(a.buffer, b.buffer, 'deterministic');
  assert.ok(a.count <= 30000 * 1.05 && a.count > 25000, String(a.count));
  for (let i = 0; i < a.buffer.length; i += 5) {
    assert.ok(a.buffer[i] >= 0 && a.buffer[i] < 400 && a.buffer[i + 1] >= 0 && a.buffer[i + 1] < 225);
    assert.ok(a.buffer[i + 2] >= 0 && a.buffer[i + 2] < 1);
  }
  const round = dust.coverGrid(r, 400, 225, 40, 30000, 5);
  assert.ok(round.count < a.count, 'corners are cut');
  for (let i = 0; i < round.buffer.length; i += 5) {
    const x = round.buffer[i], y = round.buffer[i + 1];
    if (x < 40 && y < 40) assert.ok((x - 40) ** 2 + (y - 40) ** 2 <= 1600 + 1e-6);
  }
  const contain = dust.coverGrid({ x: 0, y: 25, w: 800, h: 450 }, 800, 500, 0, 20000, 1);
  for (let i = 0; i < contain.buffer.length; i += 5) assert.ok(contain.buffer[i + 1] >= 0 && contain.buffer[i + 1] < 450, 'homes are image-relative');
  const cover = dust.coverGrid({ x: -100, y: 0, w: 1000, h: 500 }, 800, 500, 0, 20000, 1);
  for (let i = 0; i < cover.buffer.length; i += 5) assert.ok(cover.buffer[i] >= 100 && cover.buffer[i] < 900, 'clipped to the frame');
  assert.equal(dust.coverGrid({ x: 0, y: 0, w: 10, h: 10 }, 0, 0, 0, 100, 1).count, 0);
});
