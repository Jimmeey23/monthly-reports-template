/* Regression test for the interactions in GENERATED reports (gen_report_v2.py).
   Loads a report the way a browser would and asserts:
     · the Month-on-Month toggle really reveals its table
     · table rows and MoM rows both expand a horizontal drill-down strip
     · the AI copilot posts the report's location + month with each question

   Usage:  node scripts/report-interactions.test.js [url]
*/
/* Emulates a browser closely enough to exercise the report's interactions:
   canvas/matchMedia/IntersectionObserver are stubbed so the report's own chart
   code doesn't abort the script block that installs the drill-downs. */
const { JSDOM, VirtualConsole } = require('jsdom');
const vc = new VirtualConsole();
vc.on('jsdomError', e => { if (!/Could not parse CSS|fonts.googleapis|Not implemented/.test(String(e.message))) console.log('[err]', String(e.message).slice(0,160)); });

const URL_ = process.argv[2]
  || 'http://localhost:3000/report/c7b927f4-d5a2-4ba5-853d-2b680e33c5c0/Kwality_House_Performance_Report_August_2026.html';

(async () => {
  const html = await (await fetch(URL_)).text();
  const dom = new JSDOM(html, {
    url: URL_, runScripts: 'dangerously', resources: 'usable', pretendToBeVisual: true, virtualConsole: vc,
    beforeParse(w) {
      w.matchMedia = () => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
      w.IntersectionObserver = class { constructor() {} observe() {} unobserve() {} disconnect() {} };
      w.ResizeObserver = class { constructor() {} observe() {} unobserve() {} disconnect() {} };
      w.HTMLCanvasElement.prototype.getContext = function () {
        const noop = () => {};
        return new Proxy({ canvas: this, measureText: () => ({ width: 10 }), createLinearGradient: () => ({ addColorStop: noop }) },
          { get: (t, k) => (k in t ? t[k] : noop) });
      };
    },
  });
  const w = dom.window, d = w.document;
  await new Promise(r => w.addEventListener('load', r));
  await new Promise(r => setTimeout(r, 2500));

  let pass = 0, fail = 0;
  const check = (label, cond, extra) => { if (cond) { pass++; console.log('   ok   ' + label); } else { fail++; console.log('   FAIL ' + label + (extra ? ' → ' + extra : '')); } };

  // 1 — Month-on-Month toggle
  const btn = d.querySelector('.mom-toggle-btn');
  const container = d.getElementById('mom-table-executive-summary');
  check('MoM toggle button exists', !!btn);
  check('MoM container starts hidden', container.style.display === 'none');
  btn.click();
  await new Promise(r => setTimeout(r, 80));
  check('MoM container opens on click', container.style.display === 'block' && container.classList.contains('expanded'),
    'display=' + container.style.display + ' class=' + container.className);
  check('MoM table has rows', container.querySelectorAll('tbody tr').length > 0, container.querySelectorAll('tbody tr').length + ' rows');
  btn.click();
  await new Promise(r => setTimeout(r, 80));
  check('MoM container closes again', container.style.display === 'none');
  btn.click();

  // 2 — drill-down child rows
  const rows = d.querySelectorAll('tr.drill-down-row');
  check('drill-down rows installed', rows.length > 0, rows.length + ' rows');
  const row = rows[0];
  const detail = row && row.nextElementSibling;
  if (row && detail) {
    row.click();
    await new Promise(r => setTimeout(r, 80));
    check('child row expands', /visible/.test(detail.className), detail.className);
    const content = detail.querySelector('.drill-down-content');
    check('child row carries metrics', content && content.querySelectorAll('.drill-down-metric').length > 1,
      content ? content.querySelectorAll('.drill-down-metric').length + ' metrics' : 'none');
    const insight = content && content.querySelector('.drill-down-metric[style*="flex"]');
    check('insight chip is full-width (flex)', !!insight, insight ? insight.getAttribute('style') : 'missing');
    row.click();
  }

  // 2b — drill-down analytics inside the MoM table itself
  const momRow = d.querySelector('.mom-table tr.drill-down-row');
  check('MoM rows are drillable', !!momRow);
  if (momRow) {
    const detail = momRow.nextElementSibling;
    check('MoM row starts collapsed', !/visible/.test(detail.className));
    momRow.click();
    await new Promise(r => setTimeout(r, 60));
    check('MoM row opens its analytics', /visible/.test(detail.className), detail.className);
    const tiles = detail.querySelectorAll('.drill-down-metric');
    check('MoM analytics shows M-1 / M-2 / YoY / avg', tiles.length >= 4, tiles.length + ' tiles');
    check('MoM analytics has an insight chip', !!detail.querySelector('.drill-down-insight'));
    console.log('     e.g. ' + (tiles[0] ? tiles[0].textContent.trim() : '') +
      ' | ' + (detail.querySelector('.drill-down-insight') || { textContent: '' }).textContent.trim().slice(0, 110));
  }

  // 3 — copilot request payload
  const live = [...d.querySelectorAll('script')].map(s => s.textContent).join('\n');
  check('copilot sends location + month', /loc: (ctx|__ctx)\.loc, month: (ctx|__ctx)\.month/.test(live));
  check('toggleMoMTable marks the container', /container\.classList\.add\('expanded'\)/.test(live));

  console.log('\n' + (fail ? fail + ' FAILURES' : 'all ' + pass + ' checks passed'));
  process.exit(fail ? 1 : 0);
})();
