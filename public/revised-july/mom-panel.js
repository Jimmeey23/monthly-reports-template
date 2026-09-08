/* =============================================================================
   mom-panel.js — in-section Month-on-Month panels with drill-down analytics
   -----------------------------------------------------------------------------
   Renders every MOM_DATA block as a panel INSIDE the section it belongs to
   (previously they opened as an overlay mounted at the bottom of the document).

   • Styled as a report card with generous side padding
   • Every cell carries an inline MoM delta chip (analytics inside the cell)
   • Click any cell  → drill-down: value, MoM Δ, vs-average, rank, share,
                       min/max/median, volatility, sparkline + written insight
   • Click a metric  → row analytics: peak/trough month, average, median,
                       volatility, trend, months above average + narrative
   • "Drill-down" tab (when the report ships EXTRA_DATA) shows the client-type
     and trainer month-on-month matrices with the same drill-down behaviour
   • When SALES_CATEGORY_MATRIX is present, a cell drill-down also breaks the
     selected month into categories and top products (real transaction data)
   ========================================================================== */
(function () {
  'use strict';
  if (window.__MOM_PANEL_V1__) return;
  window.__MOM_PANEL_V1__ = true;

  /* Preserve the entrance-animation hook that used to live in the old modal
     script (the Bandra report gates its reveal animations on `.motion-ready`). */
  try {
    requestAnimationFrame(function () { document.body.classList.add('motion-ready'); });
  } catch (e) { /* noop */ }

  var DATA = window.MOM_DATA || {};
  var EXTRA = window.EXTRA_DATA || null;
  var EXTRA_MONTHS = window.EXTRA_MONTHS || null;
  var MATRIX = window.SALES_CATEGORY_MATRIX || null;

  var SECTION_FOR_KEY = {
    exec: 'executive-summary',
    commercial: 'revenue-performance',
    funnel: 'conversion-funnel',
    sessions: 'sessions',
    retention: 'lapsed'
  };
  var LOWER_IS_BETTER = /lapsed|churn|cancel|late cancel|net change|attrition/i;
  var MONTH_KEY = { jan: '01', feb: '02', mar: '03', apr: '04', may: '05', jun: '06', jul: '07', aug: '08', sep: '09', oct: '10', nov: '11', dec: '12' };

  /* ------------------------------------------------------------------ styles */
  var CSS = [
    '.momp-panel{--momp-pad-x:26px;position:relative;margin:20px 0 24px;border:1px solid var(--border);',
    '  border-radius:14px;background:var(--bg-card);box-shadow:var(--shadow-sm);overflow:hidden}',
    '.momp-panel::before{content:"";position:absolute;top:0;left:0;right:0;height:3px;',
    '  background:linear-gradient(90deg,var(--accent),var(--accent-2,var(--accent)) 55%,transparent);opacity:.85}',
    '.momp-head{display:flex;align-items:flex-start;justify-content:space-between;gap:18px;flex-wrap:wrap;',
    '  padding:18px var(--momp-pad-x) 16px;background:var(--bg-soft);border-bottom:1px solid var(--border)}',
    '.momp-eyebrow{display:block;font-size:10.5px;letter-spacing:.11em;text-transform:uppercase;',
    '  font-weight:700;color:var(--accent);margin-bottom:5px}',
    '.momp-title{margin:0;font-size:16.5px;line-height:1.25;font-weight:700;color:var(--text)}',
    '.momp-sub{margin:5px 0 0;font-size:12px;line-height:1.5;color:var(--text-subtle)}',
    '.momp-head-right{display:flex;align-items:center;gap:10px;flex-wrap:wrap}',
    '.momp-chip{display:inline-flex;align-items:center;gap:6px;padding:5px 11px;border-radius:999px;',
    '  border:1px solid var(--border-strong);background:var(--bg-card);font-size:11.5px;font-weight:600;color:var(--text-muted)}',
    '.momp-chip b{font-weight:700;color:var(--text)}',
    '.momp-chip b.is-up{color:var(--good)}.momp-chip b.is-down{color:var(--bad)}',
    '.momp-tabs{display:inline-flex;padding:3px;gap:3px;border-radius:999px;border:1px solid var(--border);background:var(--bg-inset)}',
    '.momp-tab{border:0;background:transparent;color:var(--text-muted);font:inherit;font-size:11.5px;font-weight:600;',
    '  padding:5px 13px;border-radius:999px;cursor:pointer;transition:background .15s,color .15s}',
    '.momp-tab:hover{color:var(--text)}',
    '.momp-tab.is-active{background:var(--bg-card);color:var(--text);box-shadow:var(--shadow-sm)}',
    '.momp-toggle{display:inline-flex;align-items:center;gap:8px;padding:7px 14px;border-radius:999px;cursor:pointer;',
    '  border:1px solid var(--border-strong);background:var(--bg-card);color:var(--text);',
    '  font:inherit;font-size:12px;font-weight:600;transition:border-color .15s,background .15s}',
    '.momp-toggle:hover{border-color:var(--accent)}',
    '.momp-toggle:focus-visible,.momp-tab:focus-visible{outline:2px solid var(--accent);outline-offset:2px}',
    '.momp-caret{width:10px;height:10px;flex:none;transition:transform .2s ease}',
    '.momp-panel.is-open .momp-toggle .momp-caret{transform:rotate(180deg)}',
    '.momp-body{display:none;padding:8px var(--momp-pad-x) 22px}',
    '.momp-panel.is-open .momp-body{display:block}',
    '.momp-scroll{overflow-x:auto;border:1px solid var(--border);border-radius:12px;background:var(--bg-card)}',
    'table.momp-table{width:100%;border-collapse:separate;border-spacing:0;font-size:13px;font-variant-numeric:tabular-nums}',
    'table.momp-table thead th{position:sticky;top:0;z-index:2;background:var(--bg-soft);color:var(--text-muted);',
    '  font-size:10px;letter-spacing:.07em;text-transform:uppercase;font-weight:700;white-space:nowrap;',
    '  text-align:right;padding:12px 16px;border-bottom:1px solid var(--border-strong)}',
    'table.momp-table thead th:first-child{text-align:left;padding-left:22px;left:0;z-index:3}',
    'table.momp-table thead th:last-child{padding-right:22px}',
    'table.momp-table tbody td{border-bottom:1px solid var(--border);padding:9px 16px;text-align:right;',
    '  background:var(--bg-card);white-space:nowrap;vertical-align:middle}',
    'table.momp-table tbody td:first-child{position:sticky;left:0;z-index:2;text-align:left;padding-left:22px;',
    '  border-right:1px solid var(--border);background:var(--bg-card)}',
    'table.momp-table tbody td:last-child{padding-right:22px}',
    'table.momp-table tbody tr.momp-data-row.is-even td{background:var(--bg-soft)}',
    'table.momp-table tbody tr.momp-data-row:hover td{background:var(--bg-card-hover)}',
    'table.momp-table tbody tr.momp-data-row:last-child td{border-bottom:0}',
    '.momp-metric-btn{display:flex;align-items:center;gap:8px;width:100%;border:0;background:transparent;cursor:pointer;',
    '  font:inherit;font-size:12.5px;font-weight:600;color:var(--text-muted);text-align:left;padding:2px 0}',
    '.momp-metric-btn:hover{color:var(--text)}',
    '.momp-metric-btn:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:4px}',
    '.momp-metric-btn .momp-caret{width:8px;height:8px;opacity:.6}',
    '.momp-metric-btn[aria-expanded="true"]{color:var(--text)}',
    '.momp-metric-btn[aria-expanded="true"] .momp-caret{transform:rotate(180deg);opacity:1}',
    '.momp-cell{cursor:pointer;transition:background .12s}',
    '.momp-cell:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}',
    '.momp-cell-value{display:block;font-size:13px;font-weight:600;color:var(--text);line-height:1.25}',
    '.momp-cell-delta{display:block;margin-top:2px;font-size:10px;font-weight:700;letter-spacing:.01em;line-height:1.2}',
    '.momp-cell-delta.is-up{color:var(--good)}.momp-cell-delta.is-down{color:var(--bad)}',
    '.momp-cell-delta.is-flat{color:var(--text-subtle)}',
    '.momp-cell.is-active{box-shadow:inset 0 0 0 1.5px var(--accent)}',
    '.momp-current-col{background:var(--accent-soft) !important}',
    'table.momp-table thead th.momp-current-col{color:var(--text)}',
    '.momp-star{width:9px;height:9px;vertical-align:-1px;margin-right:4px}',
    '.momp-total-col{background:var(--bg-inset) !important;font-weight:700;color:var(--text)}',
    '.momp-drawer>td{padding:0 !important;background:var(--bg-inset) !important;border-top:1px solid var(--border)}',
    '.momp-drawer-inner{position:sticky;left:0;max-width:min(100%,1180px);padding:12px 22px 16px;',
    '  display:flex;flex-wrap:wrap;align-items:stretch;gap:0}',
    '.momp-drawer-top{flex:1 1 100%;display:flex;align-items:flex-start;justify-content:space-between;gap:14px;',
    '  margin-bottom:10px;padding-bottom:8px;border-bottom:1px solid var(--border)}',
    '.momp-drawer-eyebrow{font-size:10px;letter-spacing:.1em;text-transform:uppercase;font-weight:700;color:var(--accent);margin-bottom:4px}',
    '.momp-drawer-title{margin:0;font-size:15px;font-weight:700;color:var(--text)}',
    '.momp-drawer-close{border:0;background:transparent;color:var(--text-subtle);font-size:20px;line-height:1;cursor:pointer;',
    '  padding:2px 8px;border-radius:6px}',
    '.momp-drawer-close:hover{background:var(--bg-card);color:var(--text)}',
    '.momp-stat-grid{display:flex;flex-direction:row;flex-wrap:wrap;align-items:stretch;gap:0;',
    '  flex:1 1 520px;min-width:0;overflow-x:auto}',
    '.momp-stat{display:flex;flex-direction:column;justify-content:center;flex:1 1 118px;min-width:104px;',
    '  padding:4px 18px;border-right:1px solid var(--border);background:transparent}',
    '.momp-stat:first-child{padding-left:2px}',
    '.momp-stat:last-child{border-right:none}',
    '.momp-stat-label{font-size:9.5px;letter-spacing:.08em;text-transform:uppercase;font-weight:700;color:var(--text-subtle)}',
    '.momp-stat-value{margin-top:4px;font-size:15px;font-weight:700;color:var(--text);line-height:1.2}',
    '.momp-stat-value.is-up{color:var(--good)}.momp-stat-value.is-down{color:var(--bad)}',
    '.momp-stat-note{margin-top:3px;font-size:10.5px;color:var(--text-muted);line-height:1.35}',
    '.momp-spark-wrap{flex:0 1 340px;min-width:260px;margin-left:auto;border:1px solid var(--border);',
    '  border-radius:10px;background:var(--bg-card);padding:12px 14px}',
    '.momp-spark-cap{font-size:10px;letter-spacing:.08em;text-transform:uppercase;font-weight:700;color:var(--text-subtle);margin-bottom:10px}',
    '.momp-spark{display:flex;align-items:flex-end;gap:6px;height:62px}',
    '.momp-spark-col{flex:1 1 0;display:flex;flex-direction:column;justify-content:flex-end;align-items:center;gap:5px;height:100%}',
    '.momp-spark-bar{width:100%;min-height:3px;border-radius:3px 3px 0 0;background:var(--border-strong)}',
    '.momp-spark-col.is-sel .momp-spark-bar{background:linear-gradient(180deg,var(--accent),var(--accent-2,var(--accent)))}',
    '.momp-spark-val{font-size:9.5px;font-weight:700;color:var(--text-subtle);white-space:nowrap}',
    '.momp-spark-col.is-sel .momp-spark-val{color:var(--text)}',
    '.momp-spark-labels{display:flex;gap:6px;margin-top:7px}',
    '.momp-spark-labels span{flex:1 1 0;text-align:center;font-size:9.5px;color:var(--text-subtle);white-space:nowrap;overflow:hidden}',
    '.momp-spark-labels span.is-sel{color:var(--text);font-weight:700}',
    '.momp-insight{flex:1 1 100%;margin-top:12px;border-left:3px solid var(--accent);background:var(--accent-soft);',
    '  border-radius:0 8px 8px 0;padding:10px 14px;font-size:12.5px;line-height:1.6;color:var(--text)}',
    '.momp-insight b{font-weight:700}',
    '.momp-break-title{margin:16px 0 8px;font-size:11.5px;letter-spacing:.06em;text-transform:uppercase;',
    '  font-weight:700;color:var(--text-muted)}',
    '.momp-break-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px;flex:1 1 100%;margin-top:4px}',
    '.momp-break-card{border:1px solid var(--border);border-radius:10px;background:var(--bg-card);padding:12px 4px 4px;overflow:hidden}',
    '.momp-break-card>.momp-break-title{padding:0 12px;margin-top:2px}',
    'table.momp-mini{width:100%;border-collapse:separate;border-spacing:0;font-size:12px;font-variant-numeric:tabular-nums}',
    'table.momp-mini th{text-align:left;font-size:9.5px;letter-spacing:.07em;text-transform:uppercase;color:var(--text-subtle);',
    '  font-weight:700;padding:7px 12px;border-bottom:1px solid var(--border-strong);background:var(--bg-soft)}',
    'table.momp-mini th.num,table.momp-mini td.num{text-align:right}',
    'table.momp-mini td{padding:7px 12px;border-bottom:1px solid var(--border);color:var(--text-muted)}',
    'table.momp-mini td:first-child{color:var(--text);font-weight:600}',
    'table.momp-mini tbody tr:last-child td{border-bottom:0}',
    '.momp-foot{margin:12px 2px 0;font-size:11px;line-height:1.55;color:var(--text-subtle)}',
    '.mom-info-btn.is-open,.momp-panel.is-open ~ .mom-info-btn,',
    'body.kwality-report .mom-info-btn.is-open,body.bandra-report .mom-info-btn.is-open{',
    '  border-color:var(--accent);color:var(--accent);opacity:1;background:var(--accent-soft);',
    '  box-shadow:0 0 0 3px color-mix(in srgb, var(--accent) 22%, transparent)}',
    '@media (max-width:760px){',
    '  .momp-panel{--momp-pad-x:16px}',
    '  .momp-drawer-inner{padding:12px 14px 16px;gap:0}',
    '  .momp-stat{padding:4px 12px;flex:1 1 96px;min-width:92px}',
    '  .momp-spark-wrap{flex:1 1 100%;margin-left:0;margin-top:10px}',
    '  table.momp-table{font-size:12px}',
    '  table.momp-table thead th{padding:10px 12px}',
    '  table.momp-table tbody td{padding:8px 12px}}',
    '@media print{',
    '  .momp-body{display:block !important}',
    '  .momp-mom-wrap[hidden],.momp-drill-wrap[hidden]{display:block !important}',
    '  .momp-toggle,.momp-tabs,.momp-drawer-close{display:none !important}',
    '  .momp-panel{break-inside:avoid;box-shadow:none}}'
  ].join('\n');

  var styleEl = document.createElement('style');
  styleEl.setAttribute('data-mom-panel', 'v1');
  styleEl.textContent = CSS;
  (document.head || document.documentElement).appendChild(styleEl);

  /* ----------------------------------------------------------------- helpers */
  function fmtCurrency(n) {
    n = Math.round(Number(n) || 0);
    var neg = n < 0; n = Math.abs(n);
    var out;
    if (n >= 10000000) out = (n / 10000000).toFixed(2) + 'Cr';
    else if (n >= 100000) out = (n / 100000).toFixed(2) + 'L';
    else {
      var s = String(n), last3 = s.slice(-3), rest = s.slice(0, -3);
      if (rest !== '') last3 = ',' + last3;
      out = rest.replace(/\B(?=(\d{2})+(?!\d))/g, ',') + last3;
    }
    return (neg ? '-' : '') + '₹' + out;
  }
  function fmtInt(n) { return Math.round(Number(n) || 0).toLocaleString('en-IN'); }
  function fmtPct(n) { return (Math.round((Number(n) || 0) * 10) / 10).toFixed(1) + '%'; }
  function fmtValue(v, fmt) {
    if (fmt === 'currency') return fmtCurrency(v);
    if (fmt === 'pct') return fmtPct(v);
    if (fmt === 'x') return (Math.round((Number(v) || 0) * 10) / 10).toFixed(1) + '×';
    if (fmt === 'days') return Math.round(Number(v) || 0) + 'd';
    return fmtInt(v);
  }
  function nums(arr) { return (arr || []).map(Number).filter(function (n) { return !isNaN(n); }); }
  function sum(a) { return a.reduce(function (x, y) { return x + y; }, 0); }
  function mean(a) { return a.length ? sum(a) / a.length : 0; }
  function median(a) {
    if (!a.length) return 0;
    var s = a.slice().sort(function (x, y) { return x - y; });
    var m = Math.floor(s.length / 2);
    return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
  }
  function stdev(a) {
    if (a.length < 2) return 0;
    var mu = mean(a);
    return Math.sqrt(mean(a.map(function (v) { return (v - mu) * (v - mu); })));
  }
  function pctDelta(cur, prev) { return !prev ? null : ((cur - prev) / Math.abs(prev)) * 100; }
  function signedPct(d, isPP) {
    if (d === null || d === undefined || !isFinite(d)) return '—';
    var v = (Math.round(d * 10) / 10).toFixed(1);
    return (d > 0 ? '+' : '') + v + (isPP ? 'pp' : '%');
  }
  function signedAbs(d, fmt) {
    var s = fmtValue(Math.abs(d), fmt);
    return (d > 0 ? '+' : d < 0 ? '−' : '') + s;
  }
  function ordinal(n) {
    var s = ['th', 'st', 'nd', 'rd'], v = n % 100;
    return n + (s[(v - 20) % 10] || s[v] || s[0]);
  }
  function esc(s) {
    return String(s === null || s === undefined ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  function isLowerBetter(label) { return LOWER_IS_BETTER.test(label || ''); }
  function tone(delta, lowerBetter) {
    if (delta === null || delta === undefined || !isFinite(delta) || Math.abs(delta) < 0.05) return 'is-flat';
    var up = delta > 0;
    return (up !== !!lowerBetter) ? 'is-up' : 'is-down';
  }
  function stat(label, value, note, cls) {
    return '<div class="momp-stat"><div class="momp-stat-label">' + label + '</div>' +
      '<div class="momp-stat-value ' + (cls || '') + '">' + value + '</div>' +
      (note ? '<div class="momp-stat-note">' + note + '</div>' : '') + '</div>';
  }
  var STAR = '<svg class="momp-star" fill="currentColor" stroke="none" viewbox="0 0 24 24"><path d="M12 2l2.9 6.6 7.1.6-5.4 4.7 1.7 7-6.3-3.8-6.3 3.8 1.7-7L2 9.2l7.1-.6z"></path></svg>';
  var CARET = '<svg class="momp-caret" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" viewbox="0 0 24 24"><path d="m6 9 6 6 6-6"></path></svg>';

  /* --------------------------------------------------- series-level analytics */
  function analyseRow(row) {
    var vals = nums(row.values);
    if (!vals.length) vals = [0];
    var lower = isLowerBetter(row.label);
    var bestIdx = 0, worstIdx = 0;
    vals.forEach(function (v, i) {
      if (lower ? v < vals[bestIdx] : v > vals[bestIdx]) bestIdx = i;
      if (lower ? v > vals[worstIdx] : v < vals[worstIdx]) worstIdx = i;
    });
    var mu = mean(vals), sd = stdev(vals);
    return {
      vals: vals,
      fmt: row.fmt || 'int',
      agg: row.agg || 'sum',
      lower: lower,
      total: sum(vals),
      avg: mu,
      median: median(vals),
      min: Math.min.apply(null, vals),
      max: Math.max.apply(null, vals),
      sd: sd,
      cv: mu ? (sd / mu) * 100 : 0,
      bestIdx: bestIdx,
      worstIdx: worstIdx,
      first: vals[0],
      last: vals[vals.length - 1],
      above: vals.filter(function (v) { return v > mu; }).length
    };
  }
  function deltaFor(a, i) {
    if (i <= 0) return null;
    var prev = a.vals[i - 1], cur = a.vals[i];
    return { pct: pctDelta(cur, prev), pp: cur - prev, abs: cur - prev, prev: prev };
  }
  function cellChip(a, i) {
    var d = deltaFor(a, i);
    if (!d) return '<span class="momp-cell-delta is-flat">&mdash;</span>';
    var isPP = a.fmt === 'pct';
    var val = isPP ? d.pp : d.pct;
    var txt = signedPct(val, isPP);
    var cls = tone(val, a.lower);
    var arrow = !isPP ? (d.pct > 0 ? '▲' : d.pct < 0 ? '▼' : '•') + ' ' : '';
    return '<span class="momp-cell-delta ' + cls + '">' + arrow + txt + '</span>';
  }
  function sparkline(a, selIdx, months) {
    var max = Math.max.apply(null, a.vals), min = Math.min.apply(null, a.vals);
    var span = (max - min) || 1;
    var cols = a.vals.map(function (v, i) {
      var h = 12 + ((v - min) / span) * 82;
      return '<div class="momp-spark-col' + (i === selIdx ? ' is-sel' : '') + '">' +
        '<span class="momp-spark-val">' + fmtValue(v, a.fmt) + '</span>' +
        '<span class="momp-spark-bar" style="height:' + h.toFixed(1) + '%"></span></div>';
    }).join('');
    var labels = (months || []).map(function (m, i) {
      return '<span class="' + (i === selIdx ? 'is-sel' : '') + '">' +
        esc(String(m).replace(' 20', " '")) + '</span>';
    }).join('');
    return '<div class="momp-spark-wrap">' +
      '<div class="momp-spark-cap">' + (a.lower ? 'Lower is better · ' : '') + 'Seven-month trend</div>' +
      '<div class="momp-spark">' + cols + '</div>' +
      '<div class="momp-spark-labels">' + labels + '</div></div>';
  }

  /* ------------------------------------------- category / product drill-down */
  var matrixByLabel = null;
  function matrixIndex() {
    if (matrixByLabel || !MATRIX) return matrixByLabel;
    matrixByLabel = {};
    var labels = (MATRIX && MATRIX.monthLabels) || {};
    Object.keys(labels).forEach(function (k) { matrixByLabel[labels[k]] = k; });
    return matrixByLabel;
  }
  function monthKeyFromLabel(label) {
    var idx = matrixIndex();
    if (idx && idx[label]) return idx[label];
    var m = String(label || '').trim().match(/^([A-Za-z]{3})\s+(\d{4})$/);
    if (m && MONTH_KEY[m[1].toLowerCase()]) return m[2] + '-' + MONTH_KEY[m[1].toLowerCase()];
    return null;
  }
  function monthBreakdown(monthLabel) {
    if (!MATRIX || !MATRIX.totals) return '';
    var key = monthKeyFromLabel(monthLabel);
    if (!key || !MATRIX.totals[key]) return '';
    var tot = MATRIX.totals[key];
    var cats = (MATRIX.categories || []).map(function (c) {
      var v = c.values && c.values[key];
      return v ? { name: c.name, v: v } : null;
    }).filter(Boolean);
    if (!cats.length) return '';
    cats.sort(function (a, b) { return b.v.net - a.v.net; });
    var rows = cats.slice(0, 8).map(function (c) {
      return '<tr><td>' + esc(c.name) + '</td>' +
        '<td class="num">' + fmtCurrency(c.v.net) + '</td>' +
        '<td class="num">' + (tot.net ? ((c.v.net / tot.net) * 100).toFixed(1) + '%' : '—') + '</td>' +
        '<td class="num">' + fmtInt(c.v.units) + '</td>' +
        '<td class="num">' + fmtInt(c.v.txns) + '</td>' +
        '<td class="num">' + fmtInt(c.v.members) + '</td>' +
        '<td class="num">' + fmtCurrency(c.v.discount) + '</td></tr>';
    }).join('');
    var catTable = '<table class="momp-mini"><thead><tr><th>Category</th><th class="num">Net</th>' +
      '<th class="num">Share</th><th class="num">Units</th><th class="num">Txns</th><th class="num">Buyers</th>' +
      '<th class="num">Discount</th></tr></thead><tbody>' + rows + '</tbody></table>';

    var prods = [];
    cats.forEach(function (c) {
      (c.v && c.products ? c.products : []).forEach(function (p) {
        var v = p.values && p.values[key];
        if (v && v.net > 0) prods.push({ name: p.name, v: v });
      });
    });
    prods.sort(function (a, b) { return b.v.net - a.v.net; });
    var prodRows = prods.slice(0, 8).map(function (p) {
      return '<tr><td>' + esc(p.name) + '</td><td class="num">' + fmtCurrency(p.v.net) + '</td>' +
        '<td class="num">' + fmtInt(p.v.units) + '</td>' +
        '<td class="num">' + (tot.net ? ((p.v.net / tot.net) * 100).toFixed(1) + '%' : '—') + '</td></tr>';
    }).join('');
    var prodTable = prodRows ? '<table class="momp-mini"><thead><tr><th>Top products</th><th class="num">Net</th>' +
      '<th class="num">Units</th><th class="num">Share</th></tr></thead><tbody>' + prodRows + '</tbody></table>' : '';

    return '<div class="momp-break-grid">' +
      '<div class="momp-break-card"><div class="momp-break-title">Category mix · ' + esc(monthLabel) + '</div>' + catTable + '</div>' +
      (prodTable ? '<div class="momp-break-card"><div class="momp-break-title">Product detail · ' + esc(monthLabel) + '</div>' + prodTable + '</div>' : '') +
      '</div>';
  }

  /* ------------------------------------------------------- cell drill-down UI */
  function cellDrawer(section, row, rowIdx, idx) {
    var a = analyseRow(row);
    var months = section.months || [];
    var v = a.vals[idx];
    var d = deltaFor(a, idx);
    var isPP = a.fmt === 'pct';
    var share = a.total ? (v / a.total) * 100 : 0;
    var rank = a.vals.slice().sort(function (x, y) { return y - x; }).indexOf(v) + 1;
    var vsAvg = pctDelta(v, a.avg);
    var prevLabel = idx > 0 ? months[idx - 1] : null;

    var stats = [];
    stats.push(stat('Value', fmtValue(v, a.fmt), esc(months[idx] || ''), ''));
    stats.push(stat('MoM change',
      d ? signedPct(isPP ? d.pp : d.pct, isPP) : '—',
      d ? (signedAbs(d.abs, a.fmt) + ' vs ' + esc(prevLabel)) : 'first month in series',
      d ? tone(isPP ? d.pp : d.pct, a.lower) : ''));
    stats.push(stat('vs 7-month average', signedPct(vsAvg, false), 'average ' + fmtValue(a.avg, a.fmt), tone(vsAvg, a.lower)));
    if (a.agg === 'sum') {
      stats.push(stat('Share of period', share.toFixed(1) + '%', 'of ' + fmtValue(a.total, a.fmt), ''));
    } else {
      var vsMed = pctDelta(v, a.median);
      stats.push(stat('vs median', signedPct(vsMed, false), 'median ' + fmtValue(a.median, a.fmt), tone(vsMed, a.lower)));
    }
    stats.push(stat('Rank', ordinal(rank) + ' of ' + a.vals.length,
      rank === 1 ? (a.lower ? 'lowest month' : 'highest month') : (a.lower ? 'lower is better' : 'higher is better'), ''));
    stats.push(stat('Range', fmtValue(a.min, a.fmt) + ' – ' + fmtValue(a.max, a.fmt), 'median ' + fmtValue(a.median, a.fmt), ''));

    return '<div class="momp-drawer-inner">' +
      '<div class="momp-drawer-top"><div>' +
      '<div class="momp-drawer-eyebrow">Cell drill-down' + (prevLabel ? ' · ' + esc(prevLabel) + ' → ' + esc(months[idx]) : '') + '</div>' +
      '<h5 class="momp-drawer-title">' + esc(row.label) + ' · ' + esc(months[idx] || '') + '</h5>' +
      '</div><button class="momp-drawer-close" type="button" aria-label="Close drill-down">×</button></div>' +
      '<div class="momp-stat-grid">' + stats.join('') + '</div>' +
      sparkline(a, idx, months) +
      '<div class="momp-insight">' + cellInsight(row, a, idx, v, d, isPP, vsAvg, rank, months) + '</div>' +
      monthBreakdown(months[idx]) +
      '</div>';
  }
  function cellInsight(row, a, idx, v, d, isPP, vsAvg, rank, months) {
    var parts = [];
    parts.push('<b>' + esc(months[idx] || '') + '</b> ' + fmtValue(v, a.fmt) +
      ' is the <b>' + ordinal(rank) + (a.lower ? ' lowest' : ' highest') + '</b> of ' + a.vals.length + ' months.');
    if (d) {
      var val = isPP ? d.pp : d.pct;
      var dir = val > 0 ? (a.lower ? 'worsened' : 'improved') : (val < 0 ? (a.lower ? 'improved' : 'declined') : 'held flat');
      parts.push('It ' + dir + ' <b>' + signedPct(val, isPP) + '</b> versus ' + esc(months[idx - 1]) + ' (' + signedAbs(d.abs, a.fmt) + ').');
    }
    parts.push('That is <b>' + signedPct(vsAvg, false) + '</b> against the seven-month average of ' + fmtValue(a.avg, a.fmt) + '.');
    parts.push(a.cv >= 25
      ? 'The series is volatile (σ = ' + a.cv.toFixed(0) + '% of mean), so a single-month move should not be over-read.'
      : (a.cv <= 8
        ? 'The series is stable (σ = ' + a.cv.toFixed(0) + '% of mean), so this move is a genuine signal.'
        : 'Variability is moderate (σ = ' + a.cv.toFixed(0) + '% of mean).'));
    return parts.join(' ');
  }

  /* -------------------------------------------------------- row drill-down UI */
  function rowDrawer(section, row) {
    var a = analyseRow(row);
    var months = section.months || [];
    var trend = pctDelta(a.last, a.first);
    var lastD = deltaFor(a, a.vals.length - 1);
    var stats = [
      stat(a.lower ? 'Best (lowest) month' : 'Peak month', esc(months[a.bestIdx] || ''), fmtValue(a.vals[a.bestIdx], a.fmt), ''),
      stat(a.lower ? 'Worst (highest) month' : 'Weakest month', esc(months[a.worstIdx] || ''), fmtValue(a.vals[a.worstIdx], a.fmt), ''),
      stat(a.agg === 'sum' ? 'Seven-month total' : 'Seven-month average',
        fmtValue(a.agg === 'sum' ? a.total : a.avg, a.fmt),
        a.agg === 'sum' ? 'sum of the seven months' : 'mean of the seven months', ''),
      stat('Median', fmtValue(a.median, a.fmt), 'mid-point of the series', ''),
      stat('Volatility', a.cv.toFixed(1) + '%', 'standard deviation as % of mean', ''),
      stat('Trend first → last', signedPct(trend, false), esc(months[0] || '') + ' vs ' + esc(months[months.length - 1] || ''),
        tone(trend, a.lower))
    ];

    var narrative = '<div class="momp-insight"><b>' + esc(row.label) + '.</b> Across ' +
      esc(months[0] || '') + '–' + esc(months[months.length - 1] || '') + ' the metric ' +
      (a.agg === 'sum' ? 'totals <b>' + fmtValue(a.total, a.fmt) + '</b>' : 'averages <b>' + fmtValue(a.avg, a.fmt) + '</b>') +
      ', ranging from <b>' + fmtValue(a.min, a.fmt) + '</b> to <b>' + fmtValue(a.max, a.fmt) + '</b>. ' +
      (a.lower ? 'Best (lowest) reading' : 'Peak') + ' was <b>' + esc(months[a.bestIdx] || '') + '</b>; the ' +
      (a.lower ? 'worst (highest)' : 'weakest') + ' was <b>' + esc(months[a.worstIdx] || '') + '</b>. ' +
      'The latest month moved <b>' + (lastD ? signedPct(a.fmt === 'pct' ? lastD.pp : lastD.pct, a.fmt === 'pct') : '—') + '</b> month-on-month, ' +
      'with <b>' + a.above + ' of ' + a.vals.length + '</b> months above the average and volatility at <b>' + a.cv.toFixed(0) + '%</b>.' +
      (trend !== null ? ' Net direction over the period is <b>' + signedPct(trend, false) + '</b> (' + (trend > 0 ? 'up' : 'down') + ').' : '') +
      '</div>';

    return '<div class="momp-drawer-inner">' +
      '<div class="momp-drawer-top"><div>' +
      '<div class="momp-drawer-eyebrow">Metric drill-down · ' + esc(months[0] || '') + '–' + esc(months[months.length - 1] || '') + '</div>' +
      '<h5 class="momp-drawer-title">' + esc(row.label) + '</h5>' +
      '</div><button class="momp-drawer-close" type="button" aria-label="Close drill-down">×</button></div>' +
      '<div class="momp-stat-grid">' + stats.join('') + '</div>' +
      sparkline(a, a.vals.length - 1, months) +
      narrative +
      '</div>';
  }

  /* -------------------------------------------------------------- table build */
  function buildTable(section) {
    var months = section.months || [];
    var lastIdx = months.length - 1;
    var rows = section.rows || [];
    var colCount = months.length + 2;

    var head = '<thead><tr><th>Metric</th>' + months.map(function (m, i) {
      return '<th class="' + (i === lastIdx ? 'momp-current-col' : '') + '">' +
        (i === lastIdx ? STAR : '') + esc(m) + '</th>';
    }).join('') + '<th class="momp-total-col">' + esc(section.totalHeader || 'Total / Avg') + '</th></tr></thead>';

    var body = '<tbody>' + rows.map(function (row, r) {
      var a = analyseRow(row);
      var cells = a.vals.map(function (v, i) {
        var cls = 'momp-cell' + (i === lastIdx ? ' momp-current-col' : '');
        return '<td class="' + cls + '" tabindex="0" role="button" data-row="' + r + '" data-idx="' + i + '" ' +
          'aria-label="' + esc(row.label + ' ' + months[i] + ' ' + fmtValue(v, row.fmt) + ' — click for drill-down') + '">' +
          '<span class="momp-cell-value">' + fmtValue(v, row.fmt) + '</span>' + cellChip(a, i) + '</td>';
      }).join('');
      var total = '<td class="momp-total-col">' + fmtValue(row.agg === 'avg' ? a.avg : a.total, row.fmt) + '</td>';
      return '<tr class="momp-data-row' + (r % 2 ? ' is-even' : '') + '" data-row="' + r + '">' +
        '<td><button type="button" class="momp-metric-btn" data-row="' + r + '" aria-expanded="false">' +
        CARET + '<span>' + esc(row.label) + '</span></button></td>' + cells + total + '</tr>';
    }).join('') + '</tbody>';

    var table = document.createElement('table');
    table.className = 'momp-table';
    table.setAttribute('data-cols', String(colCount));
    table.innerHTML = head + body;
    return table;
  }

  /* ------------------------------------------------------------- extra blocks */
  function extrasFor(key) {
    if (!EXTRA) return null;
    var months = EXTRA_MONTHS || (DATA[key] && DATA[key].months) || [];
    if (key === 'funnel') {
      return {
        label: 'Funnel drill-down',
        title: 'New client purchases & client-type detail',
        blocks: [
          {
            title: 'New client membership purchases', type: 'table',
            html: groupedTable(EXTRA.newClientPurchases || [], [
              { key: 'name', label: 'First purchase', fmt: 'text' },
              { key: 'uniqueMembers', label: 'Members' },
              { key: 'unitsSold', label: 'Units' },
              { key: 'totalLtv', label: 'Total LTV', fmt: 'currency' },
              { key: 'atv', label: 'ATV', fmt: 'currency' },
              { key: 'auv', label: 'AUV', fmt: 'currency' },
              { key: 'purchaseFreq', label: 'Freq', fmt: 'x' },
              { key: 'avgConvDays', label: 'Conv days', fmt: 'days' },
              { key: 'avgVisits', label: 'Avg visits', fmt: 'x' }
            ])
          },
          {
            title: 'Month on month by client type', type: 'matrix', rowLabel: 'Client type',
            section: { months: months, rows: EXTRA.momByClientType || [], totalHeader: 'Total' }
          }
        ]
      };
    }
    if (key === 'sessions') {
      return {
        label: 'Delivery drill-down',
        title: 'Teacher scorecard & trainer month-on-month',
        blocks: [
          {
            title: 'Teacher scorecard', type: 'table',
            html: groupedTable(EXTRA.teacherScorecard || [], [
              { key: 'instructor', label: 'Instructor', fmt: 'text' },
              { key: 'cls', label: 'Cls' },
              { key: 'empty', label: 'Empty' },
              { key: 'active', label: 'Active' },
              { key: 'fillRate', label: 'Fill rate', fmt: 'pct', noSumTotal: true },
              { key: 'newMembers', label: 'New' },
              { key: 'converted', label: 'Conv' },
              { key: 'retained', label: 'Ret' },
              { key: 'convPct', label: 'Conv %', fmt: 'pct', noSumTotal: true },
              { key: 'late', label: 'Late' },
              { key: 'pay', label: 'Pay', fmt: 'currency' },
              { key: 'score', label: 'Score' }
            ])
          },
          {
            title: 'Month on month — sessions by trainer', type: 'matrix', rowLabel: 'Trainer',
            section: { months: months, rows: EXTRA.momTrainer || [], totalHeader: 'Total' }
          }
        ]
      };
    }
    return null;
  }
  function groupedTable(rows, cols) {
    if (!rows || !rows.length) return '';
    var totals = {};
    cols.forEach(function (c) { totals[c.key] = 0; });
    var body = rows.map(function (r) {
      return '<tr>' + cols.map(function (c) {
        var v = r[c.key];
        if (typeof v === 'number') totals[c.key] += v;
        var out = (v === null || v === undefined) ? '—' : (c.fmt === 'text' ? esc(v) : fmtValue(v, c.fmt));
        return '<td class="num">' + out + '</td>';
      }).join('') + '</tr>';
    }).join('');
    var totalRow = '<tr><td>Total</td>' + cols.slice(1).map(function (c) {
      if (c.fmt === 'text' || c.noSumTotal) return '<td class="num">—</td>';
      if (c.fmt === 'pct' || c.fmt === 'x' || c.fmt === 'days') return '<td class="num">—</td>';
      return '<td class="num">' + fmtValue(totals[c.key], c.fmt) + '</td>';
    }).join('') + '</tr>';
    return '<div class="momp-break-card"><table class="momp-mini"><thead><tr>' +
      cols.map(function (c) { return '<th class="num">' + esc(c.label) + '</th>'; }).join('') +
      '</tr></thead><tbody>' + body + totalRow + '</tbody></table></div>';
  }
  function renderExtras(container, extra) {
    extra.blocks.forEach(function (b) {
      var title = document.createElement('div');
      title.className = 'momp-break-title';
      title.style.padding = '0 2px';
      title.textContent = b.title;
      container.appendChild(title);
      if (b.type === 'matrix') {
        var wrap = document.createElement('div');
        wrap.className = 'momp-scroll';
        var table = buildTable(b.section);
        var th = table.querySelector('thead th:first-child');
        if (th) th.textContent = b.rowLabel || 'Metric';
        wrap.appendChild(table);
        container.appendChild(wrap);
        bindTable(table, b.section);
      } else {
        var holder = document.createElement('div');
        holder.innerHTML = b.html;
        container.appendChild(holder);
      }
    });
  }

  /* ------------------------------------------------------------- interactions */
  function bindTable(table, section) {
    var tbody = table.tBodies[0];
    if (!tbody) return;
    var colCount = Number(table.getAttribute('data-cols')) || 9;
    var openState = { kind: null, row: null, idx: null };

    function close() {
      var d = tbody.querySelector('.momp-drawer');
      if (d && d.parentNode) d.parentNode.removeChild(d);
      tbody.querySelectorAll('.momp-cell.is-active').forEach(function (c) { c.classList.remove('is-active'); });
      tbody.querySelectorAll('.momp-metric-btn[aria-expanded="true"]').forEach(function (b) { b.setAttribute('aria-expanded', 'false'); });
      openState = { kind: null, row: null, idx: null };
    }
    function clearMarkers() {
      tbody.querySelectorAll('.momp-cell.is-active').forEach(function (c) { c.classList.remove('is-active'); });
      tbody.querySelectorAll('.momp-metric-btn[aria-expanded="true"]').forEach(function (b) { b.setAttribute('aria-expanded', 'false'); });
    }
    function show(rowIdx, idx, html) {
      var d = tbody.querySelector('.momp-drawer');
      if (!d) {
        d = document.createElement('tr');
        d.className = 'momp-drawer';
      }
      d.innerHTML = '<td colspan="' + colCount + '">' + html + '</td>';
      var anchorRow = tbody.querySelector('tr.momp-data-row[data-row="' + rowIdx + '"]');
      if (anchorRow && anchorRow.parentNode) anchorRow.parentNode.insertBefore(d, anchorRow.nextSibling);
      else tbody.appendChild(d);
      clearMarkers();
      if (idx !== null) {
        var cell = tbody.querySelector('.momp-cell[data-row="' + rowIdx + '"][data-idx="' + idx + '"]');
        if (cell) cell.classList.add('is-active');
      } else {
        var btn = tbody.querySelector('.momp-metric-btn[data-row="' + rowIdx + '"]');
        if (btn) btn.setAttribute('aria-expanded', 'true');
      }
    }

    tbody.addEventListener('click', function (e) {
      var t = e.target;
      if (!t || !t.closest) return;
      if (t.closest('.momp-drawer-close')) { close(); return; }
      var cell = t.closest('.momp-cell');
      if (cell) {
        var r = Number(cell.getAttribute('data-row')), i = Number(cell.getAttribute('data-idx'));
        if (openState.kind === 'cell' && openState.row === r && openState.idx === i) { close(); return; }
        openState = { kind: 'cell', row: r, idx: i };
        show(r, i, cellDrawer(section, section.rows[r], r, i));
        return;
      }
      var metric = t.closest('.momp-metric-btn');
      if (metric) {
        var rr = Number(metric.getAttribute('data-row'));
        if (openState.kind === 'row' && openState.row === rr) { close(); return; }
        openState = { kind: 'row', row: rr, idx: null };
        show(rr, null, rowDrawer(section, section.rows[rr]));
      }
    });
    tbody.addEventListener('keydown', function (e) {
      if (e.key !== 'Enter' && e.key !== ' ') return;
      var cell = e.target && e.target.closest ? e.target.closest('.momp-cell') : null;
      if (!cell) return;
      e.preventDefault();
      cell.click();
    });
  }

  /* -------------------------------------------------------------- panel build */
  function headlineChip(section) {
    var rows = section.rows || [];
    if (!rows.length) return '';
    var pick = null;
    for (var i = 0; i < rows.length; i++) {
      if (rows[i].fmt === 'currency' && (rows[i].agg || 'sum') === 'sum' && /net/i.test(rows[i].label || '')) { pick = rows[i]; break; }
    }
    if (!pick) pick = rows[0];
    var a = analyseRow(pick);
    var d = deltaFor(a, a.vals.length - 1);
    if (!d) return '';
    var txt = signedPct(a.fmt === 'pct' ? d.pp : d.pct, a.fmt === 'pct');
    var cls = tone(a.fmt === 'pct' ? d.pp : d.pct, a.lower);
    return '<span class="momp-chip">' + esc(pick.label) + ' <b class="' + cls + '">' + txt + '</b> MoM</span>';
  }
  function sectionFor(key) {
    var btn = document.querySelector('.mom-info-btn[data-mom="' + key + '"]');
    var sec = btn ? (btn.closest('.report-section') || btn.closest('section')) : null;
    if (!sec) {
      var id = SECTION_FOR_KEY[key];
      if (id) sec = document.getElementById(id);
    }
    return sec;
  }
  function insertAfter(section, panel) {
    var hero = section.querySelector('.section-hero');
    if (hero && hero.parentNode) {
      var anchor = hero;
      var next = hero.nextElementSibling;
      if (next && next.classList && next.classList.contains('section-marquee')) anchor = next;
      anchor.parentNode.insertBefore(panel, anchor.nextSibling);
      return;
    }
    var container = section.querySelector('.container') || section;
    container.insertBefore(panel, container.firstChild);
  }

  function buildPanel(key) {
    var section = DATA[key];
    if (!section) return null;
    var host = sectionFor(key);
    if (!host) return null;

    var extra = extrasFor(key);
    var panel = document.createElement('section');
    panel.className = 'momp-panel';
    panel.id = 'momp-panel-' + key;
    panel.setAttribute('data-mom-key', key);

    var rowCount = (section.rows || []).length;
    var months = section.months || [];
    var period = months.length ? esc(months[0]) + ' – ' + esc(months[months.length - 1]) : '';

    var html = '<header class="momp-head"><div>' +
      '<span class="momp-eyebrow">' + esc(section.eyebrow || 'Month on month') + '</span>' +
      '<h4 class="momp-title">' + esc(section.title || 'Month on Month') + '</h4>' +
      '<p class="momp-sub">' + period + ' · ' + rowCount + ' metric' + (rowCount === 1 ? '' : 's') +
      ' · every cell carries its month-on-month move · click a cell or a metric name for the full analytics</p>' +
      '</div><div class="momp-head-right">' +
      headlineChip(section) +
      (extra ? '<div class="momp-tabs" role="tablist">' +
        '<button type="button" class="momp-tab is-active" data-tab="mom">Month on month</button>' +
        '<button type="button" class="momp-tab" data-tab="drill">' + esc(extra.label) + '</button></div>' : '') +
      '<button type="button" class="momp-toggle" aria-expanded="false">Show' + CARET + '</button>' +
      '</div></header>';

    html += '<div class="momp-body">' +
      '<div class="momp-scroll momp-mom-wrap"></div>' +
      (extra ? '<div class="momp-drill-wrap" hidden></div>' : '') +
      '<p class="momp-foot">Month-on-month figures are computed from the studio’s transaction, session, lead and membership records. ' +
      'Each cell shows its own month-on-month movement; click a cell (or a metric name) to expand the underlying analytics — trend, rank, ' +
      'share, volatility and, where available, the category and product mix for that month.</p>' +
      '</div>';

    panel.innerHTML = html;
    insertAfter(host, panel);

    var momWrap = panel.querySelector('.momp-mom-wrap');
    var table = buildTable(section);
    momWrap.appendChild(table);
    bindTable(table, section);

    if (extra) renderExtras(panel.querySelector('.momp-drill-wrap'), extra);

    var toggle = panel.querySelector('.momp-toggle');
    toggle.addEventListener('click', function () {
      setOpen(panel, !panel.classList.contains('is-open'));
    });
    panel.querySelectorAll('.momp-tab').forEach(function (tab) {
      tab.addEventListener('click', function () { selectTab(panel, tab.getAttribute('data-tab')); });
    });

    /* Set window.MOM_PANEL_OPEN_DEFAULT = true before this file loads to have
       every month-on-month panel expanded on load instead of collapsed. */
    if (window.MOM_PANEL_OPEN_DEFAULT) setOpen(panel, true, true);
    return panel;
  }

  function selectTab(panel, tab) {
    panel.querySelectorAll('.momp-tab').forEach(function (t) {
      t.classList.toggle('is-active', t.getAttribute('data-tab') === tab);
    });
    var momWrap = panel.querySelector('.momp-mom-wrap');
    var drillWrap = panel.querySelector('.momp-drill-wrap');
    if (momWrap) momWrap.hidden = tab !== 'mom';
    if (drillWrap) drillWrap.hidden = tab !== 'drill';
  }
  function setOpen(panel, open, silent) {
    panel.classList.toggle('is-open', !!open);
    var toggle = panel.querySelector('.momp-toggle');
    if (toggle) {
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      toggle.innerHTML = (open ? 'Hide' : 'Show') + CARET;
    }
    var key = panel.getAttribute('data-mom-key');
    document.querySelectorAll('.mom-info-btn[data-mom="' + key + '"], .mom-info-btn[data-extra="' + key + '"]')
      .forEach(function (b) {
        b.classList.toggle('is-open', !!open);
        b.setAttribute('aria-expanded', open ? 'true' : 'false');
      });
    if (open && !silent) {
      try { panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); } catch (e) { /* noop */ }
    }
  }

  /* ------------------------------------------------------------------- init */
  var panels = {};
  function ensurePanel(key) {
    if (panels[key]) return panels[key];
    try {
      panels[key] = buildPanel(key);
    } catch (err) {
      if (window.console) console.warn('[mom-panel] could not build panel "' + key + '"', err);
      panels[key] = null;
    }
    return panels[key];
  }

  function init() {
    Object.keys(DATA).forEach(function (key) {
      var btn = document.querySelector('.mom-info-btn[data-mom="' + key + '"]');
      if (!btn) return;
      ensurePanel(key);
      btn.setAttribute('aria-expanded', 'false');
      btn.setAttribute('title', 'Show the month-on-month table for this section');
    });
    document.querySelectorAll('.mom-info-btn[data-extra]').forEach(function (b) {
      b.setAttribute('title', 'Show the drill-down detail for this section');
    });

    document.addEventListener('click', function (e) {
      var t = e.target;
      if (!t || !t.closest) return;
      var momBtn = t.closest('.mom-info-btn[data-mom]');
      if (momBtn) {
        var panel = ensurePanel(momBtn.getAttribute('data-mom'));
        if (!panel) return;
        var wasOpen = panel.classList.contains('is-open');
        var activeTab = panel.querySelector('.momp-tab.is-active');
        selectTab(panel, activeTab ? activeTab.getAttribute('data-tab') : 'mom');
        setOpen(panel, !wasOpen);
        return;
      }
      var extraBtn = t.closest('.mom-info-btn[data-extra]');
      if (extraBtn) {
        var p2 = ensurePanel(extraBtn.getAttribute('data-extra'));
        if (!p2) return;
        var drillTab = p2.querySelector('.momp-tab[data-tab="drill"]');
        selectTab(p2, drillTab ? 'drill' : 'mom');
        setOpen(p2, true);
      }
    });

    document.addEventListener('keydown', function (e) {
      if (e.key !== 'Escape') return;
      document.querySelectorAll('.momp-drawer').forEach(function (d) { if (d.parentNode) d.parentNode.removeChild(d); });
      document.querySelectorAll('.momp-cell.is-active').forEach(function (c) { c.classList.remove('is-active'); });
      document.querySelectorAll('.momp-metric-btn[aria-expanded="true"]').forEach(function (b) { b.setAttribute('aria-expanded', 'false'); });
    });

    function expandAll() {
      Object.keys(panels).forEach(function (k) { if (panels[k]) panels[k].classList.add('is-open'); });
    }
    window.addEventListener('beforeprint', expandAll);

    /* The report builds its A4 PDF by cloning the DOM, so every panel has to be
       open before the clone is taken. Capture phase = runs before the exporter. */
    document.addEventListener('click', function (e) {
      var t = e.target;
      if (!t || !t.closest) return;
      if (t.closest('#pdf-export-btn') || t.closest('.pdf-btn')) expandAll();
    }, true);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
