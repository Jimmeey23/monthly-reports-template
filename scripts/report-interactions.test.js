/* Regression test for the interactions in GENERATED reports (gen_report_v2.py).

   Loads a generated report the way a browser would and asserts the behaviours
   the document shell is responsible for:
     · table rows expand a horizontal drill-down strip
     · the heatmap's metric toggle and day filter are wired to the grid
     · the hero KPI cards flip and carry their sparkline data
     · each section header gets its narration button

   Month-on-month panels are covered separately by mom-panel.test.js, which
   drives the same module this report inlines.

   Usage:  node scripts/report-interactions.test.js [file-or-url]
*/
const fs = require('fs');
const path = require('path');
const { JSDOM, VirtualConsole } = require('jsdom');

const ROOT = path.join(__dirname, '..');
const DEFAULT_FILE = 'public/revised-july/supreme-hq-bandra-july-2026.html';

const vc = new VirtualConsole();
vc.on('jsdomError', e => {
  if (!/Could not parse CSS|fonts\.googleapis|Not implemented/.test(String(e.message))) {
    console.log('[err]', String(e.message).slice(0, 160));
  }
});

/* Emulates a browser closely enough to exercise the report's interactions:
   canvas/matchMedia/IntersectionObserver are stubbed so the report's own chart
   code doesn't abort the script block that installs the drill-downs. */
function beforeParse(w) {
  w.matchMedia = () => ({
    matches: false, addListener() {}, removeListener() {},
    addEventListener() {}, removeEventListener() {},
  });
  w.IntersectionObserver = class { observe() {} unobserve() {} disconnect() {} };
  w.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} };
  w.HTMLCanvasElement.prototype.getContext = function () {
    const noop = () => {};
    return new Proxy(
      { canvas: this, measureText: () => ({ width: 10 }), createLinearGradient: () => ({ addColorStop: noop }) },
      { get: (t, k) => (k in t ? t[k] : noop) });
  };
}

async function loadReport(target) {
  const isUrl = /^https?:/.test(target);
  const html = isUrl
    ? await (await fetch(target)).text()
    : fs.readFileSync(path.join(ROOT, target), 'utf8');
  const url = isUrl ? target : 'https://reports.local/' + path.basename(target);
  const dom = new JSDOM(html, {
    url, runScripts: 'dangerously', resources: 'usable',
    pretendToBeVisual: true, virtualConsole: vc, beforeParse,
  });
  await new Promise(r => dom.window.addEventListener('load', r));
  await new Promise(r => setTimeout(r, 2500));
  return dom;
}

(async () => {
  const target = process.argv[2] || DEFAULT_FILE;
  const dom = await loadReport(target);
  const w = dom.window;
  const d = w.document;

  let pass = 0, fail = 0;
  const check = (label, cond, extra) => {
    if (cond) { pass++; console.log('   ok   ' + label); }
    else { fail++; console.log('   FAIL ' + label + (extra ? ' → ' + extra : '')); }
  };

  console.log('\n=== ' + target);

  // 1 — the document shell
  check('body carries the report class', d.body.classList.contains('sp-report'), d.body.className);
  const ids = [...d.querySelectorAll('section.report-section')].map(s => s.id);
  check('seven chapters in narrative order',
    ids.join(',') === 'executive-summary,revenue-performance,conversion-funnel,sessions,lapsed,recommendations,predictions',
    ids.join(','));
  check('every chapter has a marquee', d.querySelectorAll('.section-marquee').length === 7,
    String(d.querySelectorAll('.section-marquee').length));

  // 2 — metric cards (the hero grid and the compact cards inside sections are
  // the same component, so both are checked here)
  const heroCards = d.querySelectorAll('.hero-kpi-grid .kpi-card');
  const cards = d.querySelectorAll('.kpi-card');
  check('hero shows a full KPI grid', heroCards.length >= 6, String(heroCards.length));
  check('sections reuse the hero metric card',
    d.querySelectorAll('.kpi-card.is-compact').length > 0,
    d.querySelectorAll('.kpi-card.is-compact').length + ' compact');
  check('KPI cards have a back face',
    d.querySelectorAll('.kpi-card-back').length === cards.length);
  check('metric cards explain their formula',
    d.querySelectorAll('.kpi-back-formula').length > 0,
    d.querySelectorAll('.kpi-back-formula').length + ' formulas');
  const charted = [...d.querySelectorAll('.kpi-chart')].filter(c => c.dataset.series);
  check('KPI sparklines carry their series', charted.length > 0, charted.length + ' charted');
  if (cards.length) {
    cards[0].click();
    await new Promise(r => setTimeout(r, 80));
    check('clicking a KPI card flips it', cards[0].classList.contains('is-flipped'), cards[0].className);
    cards[0].click();
  }

  // 3 — row drill-downs now open the shared modal rather than an inline strip
  const rows = d.querySelectorAll('tr.drill-down-row');
  check('drill-down rows installed', rows.length > 0, rows.length + ' rows');
  const overlay = d.querySelector('.drill-modal-overlay');
  check('drill-down modal installed', !!overlay);
  if (rows.length && overlay) {
    rows[0].click();
    await new Promise(r => setTimeout(r, 80));
    check('row opens the drill-down modal', overlay.hidden === false, String(overlay.hidden));
    check('modal carries the row metrics',
      d.querySelectorAll('.drill-stat').length > 1,
      d.querySelectorAll('.drill-stat').length + ' stats');
    check('modal ranks the row against its peers',
      d.querySelectorAll('.drill-bar').length > 0,
      d.querySelectorAll('.drill-bar').length + ' bars');
    overlay.querySelector('.drill-modal-close').click();
  }

  // 3b — nested tables open their children
  const nested = d.querySelector('table.nested-table tr.group-row.has-children');
  if (nested) {
    const groupId = nested.querySelector('.row-toggle').getAttribute('aria-controls');
    const kids = d.querySelectorAll(`tr.child-row[data-parent="${groupId}"]`);
    check('nested children start closed', kids.length > 0 && kids[0].hidden, kids.length + ' children');
    nested.click();
    await new Promise(r => setTimeout(r, 40));
    check('nested parent row opens its children', kids.length > 0 && !kids[0].hidden);
    nested.click();
    await new Promise(r => setTimeout(r, 40));
    check('nested parent row closes again', kids.length > 0 && kids[0].hidden);
  }

  // 3c — ranking boards are the one ranking surface
  check('ranking boards render their items',
    d.querySelectorAll('.rank-board').length > 1 && d.querySelectorAll('.rank-item').length > 0,
    d.querySelectorAll('.rank-board').length + ' boards, ' +
    d.querySelectorAll('.rank-item').length + ' items');

  // 4 — heatmap controls
  const heatmap = d.getElementById('demand-heatmap');
  check('heatmap grid is present', !!heatmap);
  if (heatmap) {
    const cells = heatmap.querySelectorAll('.heat-cell[data-v]');
    check('heat cells carry their value', cells.length > 0, cells.length + ' cells');
    check('slot totals row present', !!heatmap.querySelector('tr.hm-totals'));
    check('grand total present', !!heatmap.querySelector('.hm-grand'));

    const metricBtns = [...d.querySelectorAll('.hm-btn')];
    check('heatmap offers three metrics', metricBtns.length === 3, String(metricBtns.length));
    if (metricBtns.length > 1) {
      const before = cells[0].textContent;
      metricBtns[1].click();
      await new Promise(r => setTimeout(r, 60));
      check('switching metric rewrites the cells', cells[0].textContent !== before,
        before + ' → ' + cells[0].textContent);
      metricBtns[0].click();
    }

    const dayBtns = [...d.querySelectorAll('.hm-day-btn')];
    check('heatmap offers a day filter', dayBtns.length === 8, String(dayBtns.length));
    if (dayBtns.length > 1) {
      dayBtns[1].click();
      await new Promise(r => setTimeout(r, 60));
      check('day filter marks its button', dayBtns[1].classList.contains('is-active'));
      dayBtns[0].click();
    }
  }

  // 5 — narration buttons
  check('each chapter gets a narration button',
    d.querySelectorAll('.section-audio-btn').length === 7,
    String(d.querySelectorAll('.section-audio-btn').length));

  // 6 — export chrome
  check('PDF export button present', !!d.getElementById('pdf-export-btn'));
  check('PDF progress dialog present', !!d.getElementById('pdf-export-overlay'));
  check('back-to-top present', !!d.getElementById('back-to-top'));

  console.log('\n' + (fail ? fail + ' FAILURES' : 'ALL ' + pass + ' CHECKS PASS'));
  dom.window.close();
  process.exit(fail ? 1 : 0);
})();
