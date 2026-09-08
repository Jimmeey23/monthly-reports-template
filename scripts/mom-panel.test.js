/* Smoke test: load each revised July report in jsdom, run mom-panel.js and
   assert the panels render in-section with working drill-downs.
   Run: node scripts/mom-panel.test.js  (requires: npm i --no-save jsdom) */
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const ROOT = path.join(__dirname, '..');
const FILES = [
  'public/revised-july/kwality-house-july-2026.html',
  'public/revised-july/supreme-hq-bandra-july-2026.html',
];
const MODULE = fs.readFileSync(path.join(ROOT, 'public/revised-july/mom-panel.js'), 'utf8');

let failures = 0;
function check(label, cond, extra) {
  if (cond) console.log('   ok   ' + label);
  else { failures++; console.log('   FAIL ' + label + (extra ? ' → ' + extra : '')); }
}

async function run(file) {
  console.log('\n=== ' + file);
  const html = fs.readFileSync(path.join(ROOT, file), 'utf8');
  const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true });
  const { window } = dom;
  const doc = window.document;

  const dataKeys = Object.keys(window.MOM_DATA || {});
  check('MOM_DATA present (' + dataKeys.length + ' keys)', dataKeys.length > 0);

  let errors = [];
  window.addEventListener('error', (e) => errors.push(e.message));
  const script = doc.createElement('script');
  script.textContent = MODULE;
  doc.body.appendChild(script);
  if (doc.readyState === 'loading') {
    await new Promise((resolve) => window.addEventListener('load', resolve));
  }

  const panels = [...doc.querySelectorAll('.momp-panel')];
  check('panels built: ' + panels.length, panels.length === dataKeys.length,
    'expected ' + dataKeys.length);

  panels.forEach((p) => {
    const key = p.getAttribute('data-mom-key');
    const section = p.closest('.report-section');
    check('panel "' + key + '" lives inside #' + (section && section.id), !!section);
    const btn = doc.querySelector('.mom-info-btn[data-mom="' + key + '"]');
    if (btn) {
      check('panel "' + key + '" shares a section with its trigger button',
        btn.closest('.report-section') === section);
    }
    const table = p.querySelector('table.momp-table');
    check('panel "' + key + '" table rows = ' + (table ? table.tBodies[0].querySelectorAll('tr.momp-data-row').length : 0),
      !!table && table.tBodies[0].querySelectorAll('tr.momp-data-row').length > 0);
    const chips = table ? table.querySelectorAll('.momp-cell-delta').length : 0;
    const withDelta = table ? [...table.querySelectorAll('.momp-cell-delta')]
      .filter((c) => !/—/.test(c.textContent)).length : 0;
    check('panel "' + key + '" cells carry MoM chips (' + withDelta + '/' + chips + ')', withDelta > 0);
  });

  // toggle open
  const btn = doc.querySelector('.mom-info-btn[data-mom]');
  btn.click();
  const firstPanel = doc.querySelector('.momp-panel');
  check('clicking "i" opens the panel in place', firstPanel.classList.contains('is-open'));
  check('toggle button label flips to Hide', /Hide/.test(firstPanel.querySelector('.momp-toggle').textContent));

  // cell drill-down
  const cell = firstPanel.querySelector('.momp-cell[data-idx="6"]');
  cell.click();
  const drawer = firstPanel.querySelector('.momp-drawer');
  check('cell click opens a drill-down drawer', !!drawer);
  if (drawer) {
    const txt = drawer.textContent;
    check('drawer shows MoM change', /MoM change/.test(txt));
    check('drawer shows rank', /of 7/.test(txt));
    check('drawer shows a written insight', /is the/.test(txt));
    check('drawer shows sparkline', drawer.querySelectorAll('.momp-spark-bar').length === 7);
    check('drawer shows stat cards', drawer.querySelectorAll('.momp-stat').length >= 5);
    check('cell marked active', cell.classList.contains('is-active'));
  }

  // metric (row) drill-down
  const metric = firstPanel.querySelector('.momp-metric-btn');
  metric.click();
  const rowDrawer = firstPanel.querySelector('.momp-drawer');
  check('metric click opens row analytics', /Metric drill-down/.test(rowDrawer.textContent));
  check('row analytics show volatility', /Volatility/.test(rowDrawer.textContent));

  // extras tab (Bandra)
  const drillTab = [...doc.querySelectorAll('.momp-tab[data-tab="drill"]')][0];
  if (drillTab) {
    drillTab.click();
    const wrap = drillTab.closest('.momp-panel').querySelector('.momp-drill-wrap');
    check('drill tab reveals extra tables', !wrap.hidden && wrap.querySelectorAll('table').length >= 2,
      wrap.querySelectorAll('table').length + ' tables');
    const extraCell = wrap.querySelector('.momp-cell[data-idx="6"]');
    if (extraCell) {
      extraCell.click();
      check('extra matrix cell drill-down works', !!wrap.querySelector('.momp-drawer'));
    }
  }

  // category breakdown (Bandra only)
  if (window.SALES_CATEGORY_MATRIX) {
    const c = [...doc.querySelectorAll('.momp-cell[data-idx="6"]')][0];
    c.click();
    const d = c.closest('table').querySelector('.momp-drawer');
    check('month breakdown renders category mix', !!d && /Category mix/.test(d.textContent),
      d ? d.textContent.slice(0, 80) : 'no drawer');
  }

  // closing (clicking the same cell twice must collapse it again)
  const sameCell = firstPanel.querySelector('.momp-cell[data-idx="6"]');
  sameCell.click();
  const after1 = !!firstPanel.querySelector('.momp-drawer');
  sameCell.click();
  const after2 = !!firstPanel.querySelector('.momp-drawer');
  check('clicking the same cell toggles its drawer', after1 !== after2,
    'open=' + after1 + ' then open=' + after2);

  check('no runtime errors', errors.length === 0, errors.join(' | '));
  window.close();
}

(async () => {
  for (const f of FILES) await run(f);
  console.log('\n' + (failures ? failures + ' FAILURES' : 'all checks passed'));
  process.exit(failures ? 1 : 0);
})();
