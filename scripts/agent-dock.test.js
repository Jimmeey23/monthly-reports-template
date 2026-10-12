const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM } = require('jsdom');
const script = fs.readFileSync(path.join(__dirname, '../public/agent-dock.js'), 'utf8');
const css = fs.readFileSync(path.join(__dirname, '../public/agent-dock.css'), 'utf8');

async function load(reply) {
  const requests = [];
  const dom = new JSDOM('<style>' + css + '</style><body></body>', {
    url: 'http://localhost:3000/report/session/report.html', runScripts: 'outside-only',
  });
  const w = dom.window;
  w.__AGENT_CTX__ = { sessionId: 'session', filename: 'report.html' };
  w.TextDecoder = TextDecoder;
  w.fetch = async (input, options) => {
    const url = new URL(input); // same requirement as browser request hooks
    requests.push({ url, options });
    if (url.pathname.endsWith('/state')) return { ok: true, json: async () => ({ ok: true, aiAvailable: true }) };
    return reply;
  };
  w.eval(script);
  await new Promise(resolve => setImmediate(resolve));
  return { dom, w, requests };
}

function response(events) {
  const encoded = new TextEncoder().encode(events.map(e => 'data: ' + JSON.stringify(e) + '\n\n').join(''));
  let read = false;
  return { ok: true, body: { getReader: () => ({ read: async () => {
    if (read) return { done: true };
    read = true;
    return { done: false, value: encoded };
  } }) } };
}

async function send(w) {
  w.document.querySelector('textarea').value = 'Explain revenue';
  w.document.querySelector('.agent-input').dispatchEvent(new w.Event('submit', { cancelable: true }));
  await new Promise(resolve => setImmediate(resolve));
}

test('analyst starts hidden, opens, closes visibly and closes with Escape', async () => {
  const { dom, w } = await load(response([]));
  try {
    const panel = w.document.querySelector('.agent-panel');
    const display = () => w.getComputedStyle(panel).display;
    assert.equal(display(), 'none');
    w.document.querySelector('.agent-fab').click();
    assert.equal(display(), 'flex');
    w.document.querySelector('[data-act="close"]').click();
    assert.equal(display(), 'none');
    w.document.querySelector('.agent-fab').click();
    w.document.dispatchEvent(new w.KeyboardEvent('keydown', { key: 'Escape' }));
    assert.equal(display(), 'none');
    assert.equal(w.document.activeElement, w.document.querySelector('.agent-fab'));
  } finally { dom.window.close(); }
});

test('analyst streams replies using absolute URLs and tolerates malformed tables', { timeout: 3000 }, async () => {
  const { dom, w, requests } = await load(response([{ type: 'message', text: '| incomplete table\n\n**Revenue** is recorded.' }]));
  try {
    await send(w);
    assert.equal(requests.length, 2);
    assert.ok(requests.every(r => r.url.origin === 'http://localhost:3000'));
    assert.match(w.document.querySelector('.agent-log').textContent, /incomplete table/);
    assert.match(w.document.querySelector('.agent-log').textContent, /Revenue is recorded/);
    assert.equal(w.document.querySelector('.agent-send').disabled, false);
    assert.equal(w.document.querySelector('.agent-status').hidden, true);
  } finally { dom.window.close(); }
});

test('analyst shows HTTP errors and permits retry', async () => {
  const { dom, w } = await load({ ok: false, status: 404, json: async () => ({ error: 'Session not found.' }) });
  try {
    await send(w);
    assert.match(w.document.querySelector('.agent-log').textContent, /Session not found/);
    assert.equal(w.document.querySelector('.agent-send').disabled, false);
  } finally { dom.window.close(); }
});
