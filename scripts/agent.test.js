/* Covers the parts of the assistant that must not drift: the sandbox contract,
   the override store, the write-tool confirmation gate, and the dock's DOM ops
   (run against jsdom, since a bad undo is what would corrupt a report). */
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const vm = require('vm');
const { JSDOM } = require('jsdom');

const sandbox = require('../agent/sandbox');
const overrides = require('../agent/overrides');
const tools = require('../agent/tools');

function tmpdir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'agent-test-'));
}

/* ------------------------------------------------------------- sandbox -- */

test('sandbox returns the value of a bare expression', async () => {
  const res = await sandbox.runQuery({ code: '2 + 2' });
  assert.strictEqual(res.ok, true);
  assert.strictEqual(res.result, 4);
});

test('sandbox keeps the trailing expression after statements', async () => {
  const res = await sandbox.runQuery({ code: 'a = 10\nb = 4\n(a - b, a / b)' });
  assert.deepStrictEqual(res.result, [6, 2.5]);
});

test('sandbox exposes the analysis file', async () => {
  const dir = tmpdir();
  const file = path.join(dir, 'analysis.json');
  fs.writeFileSync(file, JSON.stringify({ sales: { kw: { '2026-07': { net: 1234 } } } }));
  const res = await sandbox.runQuery({ code: "analysis['sales']['kw']['2026-07']['net']", analysisPath: file });
  assert.strictEqual(res.result, 1234);
});

test('sandbox reads a CSV by name', async () => {
  const dir = tmpdir();
  fs.writeFileSync(path.join(dir, 'sales.csv'), 'name,amount\nA,100\nB,250\n');
  const res = await sandbox.runQuery({
    code: "sum(int(r['amount']) for r in csv('sales'))",
    csvDir: dir,
  });
  assert.strictEqual(res.result, 350);
});

test('sandbox reports an error instead of throwing', async () => {
  const res = await sandbox.runQuery({ code: "analysis['nope']" });
  assert.strictEqual(res.ok, false);
  assert.match(res.error, /KeyError/);
});

/* ----------------------------------------------------------- overrides -- */

test('overrides round-trip per report file', () => {
  const dir = tmpdir();
  const patch = overrides.addPatch(dir, 'a.html', { kind: 'style', note: 'n', ops: [{ kind: 'hide', selector: '.x' }] });
  overrides.addComponent(dir, 'a.html', { title: 'T', target: '#s', html: '<p>hi</p>' });
  overrides.addPatch(dir, 'b.html', { kind: 'style', note: 'other', ops: [] });

  const a = overrides.load(dir, 'a.html');
  assert.strictEqual(a.patches.length, 1);
  assert.strictEqual(a.components.length, 1);
  assert.strictEqual(overrides.load(dir, 'b.html').patches.length, 1, 'reports must not share overrides');

  assert.ok(overrides.remove(dir, 'a.html', patch.id));
  assert.strictEqual(overrides.load(dir, 'a.html').patches.length, 0);
  assert.strictEqual(overrides.remove(dir, 'a.html', 'missing'), null);
});

/* --------------------------------------------------------------- tools -- */

test('write tools propose rather than save', async () => {
  const dir = tmpdir();
  const ctx = { sessionDir: dir, filename: 'a.html', canEdit: true };
  const res = await tools.runTool('propose_style_patch', {
    note: 'tighten', ops: [{ kind: 'css', selector: '.kpi-card', declarations: { margin: '0' } }],
  }, ctx);

  assert.strictEqual(res.pending, true);
  assert.strictEqual(res.proposal.kind, 'style');
  assert.strictEqual(overrides.load(dir, 'a.html').patches.length, 0, 'nothing may be written before the user confirms');
});

test('write tools refuse a read-only viewer', async () => {
  const res = await tools.runTool('propose_component', {
    title: 'T', componentType: 'table', target: '#s', html: '<table></table>',
  }, { canEdit: false, sessionDir: tmpdir(), filename: 'a.html' });
  assert.strictEqual(res.ok, false);
  assert.match(res.error, /read-only/);
});

test('op validation rejects unknown kinds and missing fields', () => {
  assert.match(tools.validateOps([{ kind: 'nope', selector: '.x' }]), /unknown op kind/);
  assert.match(tools.validateOps([{ kind: 'css', selector: '.x' }]), /declarations/);
  assert.match(tools.validateOps([{ kind: 'move', selector: '.x' }]), /target/);
  assert.strictEqual(tools.validateOps([{ kind: 'hide', selector: '.x' }]), null);
});

/* ----------------------------------------------------------- dock DOM -- */

function loadDock(html, ctx) {
  const dom = new JSDOM(html, { url: 'http://localhost/report/s/f.html' });
  const { window } = dom;
  window.__AGENT_CTX__ = ctx || { sessionId: 's', filename: 'f.html', editToken: 't' };
  window.fetch = () => new Promise(() => {});      // the dock's boot fetch never resolves in tests
  const context = vm.createContext(window);
  const captured = {};
  window.__capture = captured;
  const source = fs.readFileSync(path.join(__dirname, '..', 'public', 'agent-dock.js'), 'utf8')
    // the dock keeps its internals private; the tests need two of them
    .replace('if (document.readyState === \'loading\')',
      'window.__capture.applyPatch = applyPatch; window.__capture.applyComponent = applyComponent;\n  if (document.readyState === \'loading\')');
  vm.runInContext(source, context);
  return { window, captured };
}

const PAGE = `<!DOCTYPE html><html><body>
  <section id="revenue"><div class="container"><p class="lead">Lead</p><div class="block">Block</div></div></section>
  <section id="sessions"><div class="container"><p class="note">Note</p></div></section>
</body></html>`;

test('a style patch applies and undoes exactly', () => {
  const { window, captured } = loadDock(PAGE);
  const doc = window.document;
  const before = doc.body.innerHTML;

  const undo = captured.applyPatch({
    ops: [
      { kind: 'hide', selector: '.lead' },
      { kind: 'addClass', selector: '.block', className: 'is-highlighted' },
      { kind: 'setText', selector: '.note', text: 'Changed' },
      { kind: 'move', selector: '.block', target: '#sessions .container', position: 'append' },
    ],
  }, false);

  assert.strictEqual(doc.querySelector('.lead').style.display, 'none');
  assert.ok(doc.querySelector('.block').classList.contains('is-highlighted'));
  assert.strictEqual(doc.querySelector('.note').textContent, 'Changed');
  assert.ok(doc.querySelector('#sessions .block'), 'the block moved sections');

  undo();
  assert.strictEqual(doc.body.innerHTML, before, 'undo must restore the page exactly');
});

test('a css op writes a rule and removes it on undo', () => {
  const { window, captured } = loadDock(PAGE);
  const undo = captured.applyPatch({
    ops: [{ kind: 'css', selector: '.lead', declarations: { fontSize: '20px', color: 'red' } }],
  }, false);

  const sheet = window.document.getElementById('agent-override-styles');
  assert.match(sheet.textContent, /\.lead\{font-size:20px !important;color:red !important;\}/);
  undo();
  assert.strictEqual(sheet.textContent, '');
});

test('a component inserts at its target and undoes cleanly', () => {
  const { window, captured } = loadDock(PAGE);
  const doc = window.document;
  const before = doc.body.innerHTML;

  const undo = captured.applyComponent({
    title: 'T',
    target: '#revenue .container',
    position: 'append',
    html: '<table class="report-table"><tr><td>7</td></tr></table>',
    css: '.report-table{border:0}',
  }, true, 'cmp_1');

  const node = doc.querySelector('[data-agent-component="cmp_1"]');
  assert.ok(node, 'component was inserted');
  assert.ok(node.classList.contains('is-pending'), 'a preview is marked pending');
  assert.strictEqual(node.closest('.container').parentElement.id, 'revenue');

  undo();
  assert.strictEqual(doc.body.innerHTML, before);
  assert.strictEqual(doc.head.innerHTML.includes('.report-table'), false, 'component css is removed too');
});

test('a component with a missing target reports failure instead of guessing', () => {
  const { captured } = loadDock(PAGE);
  assert.strictEqual(captured.applyComponent({ target: '#nope', html: '<p></p>' }, false, 'x'), null);
});
