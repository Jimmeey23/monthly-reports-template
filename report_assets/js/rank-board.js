/* Top / bottom ranking boards.

   The section ships one JSON payload per board and this re-ranks it in the
   page, so switching the metric or lengthening the list never costs a round
   trip and the two columns can never disagree about the same ledger. */
(function () {
  var FORMATTERS = {
    lakh: function (v) {
      if (Math.abs(v) >= 1e7) return '₹' + (v / 1e7).toFixed(2) + 'Cr';
      if (Math.abs(v) >= 1e5) return '₹' + (v / 1e5).toFixed(2) + 'L';
      if (Math.abs(v) >= 1e3) return '₹' + (v / 1e3).toFixed(1) + 'K';
      return '₹' + Math.round(v).toLocaleString('en-IN');
    },
    rupee: function (v) { return '₹' + Math.round(v).toLocaleString('en-IN'); },
    int: function (v) { return Math.round(v).toLocaleString('en-IN'); },
    pct: function (v) { return v.toFixed(1) + '%'; },
    pp: function (v) { return (v >= 0 ? '+' : '') + v.toFixed(1) + 'pp'; },
    dec1: function (v) { return v.toFixed(1); },
    dec2: function (v) { return v.toFixed(2); },
    mult: function (v) { return v.toFixed(2) + '×'; }
  };

  function fmt(kind, value) {
    var f = FORMATTERS[kind] || FORMATTERS.int;
    return f(Number(value) || 0);
  }

  function render(board, state) {
    var metric = state.metrics.filter(function (m) { return m.key === state.metric; })[0]
      || state.metrics[0];
    var sorted = state.items.slice().sort(function (a, b) {
      return (Number(b[metric.key]) || 0) - (Number(a[metric.key]) || 0);
    });

    var size = Math.min(state.size, Math.floor(sorted.length / 2) || sorted.length);
    if (size < 1) size = 1;

    var highest = sorted.slice(0, size);              // largest first
    var lowest = sorted.slice(-size).reverse();       // smallest first
    // For a metric where less is better (discount, discount rate), the best
    // performers are the small numbers — so the columns swap ends, and each
    // still leads with its most extreme row.
    var top = metric.better === 'low' ? lowest : highest;
    var bottom = metric.better === 'low' ? highest : lowest;

    var scale = Math.max.apply(null, sorted.map(function (i) {
      return Math.abs(Number(i[metric.key]) || 0);
    }).concat([1]));

    fill(board.querySelector('[data-rank-list="top"]'), top, metric, scale, 'good', state);
    fill(board.querySelector('[data-rank-list="bottom"]'), bottom, metric, scale, 'bad', state);

    var topNote = board.querySelector('[data-rank-top-note]');
    var bottomNote = board.querySelector('[data-rank-bottom-note]');
    var best = metric.better === 'low' ? 'Lowest ' : 'Highest ';
    var worst = metric.better === 'low' ? 'Highest ' : 'Lowest ';
    if (topNote) topNote.textContent = best + metric.label + ' · ' + size;
    if (bottomNote) bottomNote.textContent = worst + metric.label + ' · ' + size;
    var name = board.querySelector('[data-rank-metric-name]');
    if (name) name.textContent = metric.label;
  }

  /* The meta strip under each name is described by the payload, so a trainer
     board and a product board use the same renderer with different columns. */
  var DEFAULT_META = [
    { key: 'units', fmt: 'int', suffix: ' units' },
    { key: 'txns', fmt: 'int', suffix: ' txns' },
    { key: 'aov', fmt: 'rupee', suffix: ' AOV' },
    { key: 'share', fmt: 'pct', suffix: ' of revenue' }
  ];

  function metaLine(item, spec) {
    return (spec || DEFAULT_META).map(function (m) {
      var value = fmt(m.fmt, item[m.key]);
      return (m.prefix || '') + value + (m.suffix || '');
    }).join(' · ');
  }

  /* Every metric in the payload goes into the drill payload, so opening an
     item shows the full ledger row rather than only the ranked figure. */
  function drillPayload(item, state, position, total) {
    return {
      kicker: state.kicker || 'Ranking',
      title: item.name,
      subtitle: 'Position ' + position + ' of ' + total + ' by ' +
        (state.metrics.filter(function (m) { return m.key === state.metric; })[0] || {}).label,
      stats: state.metrics.map(function (m) {
        return { label: m.label, value: fmt(m.fmt, item[m.key]) };
      }),
      bars: state.items.slice()
        .sort(function (a, b) { return (Number(b[state.metric]) || 0) - (Number(a[state.metric]) || 0); })
        .slice(0, 12)
        .map(function (i) {
          return { label: i.name, value: Number(i[state.metric]) || 0,
                   display: fmt((state.metrics.filter(function (m) { return m.key === state.metric; })[0] || {}).fmt, i[state.metric]) };
        }),
      barsTitle: 'Every ranked item on this metric',
      footnote: 'Esc or click outside to close.'
    };
  }

  function fill(list, items, metric, scale, tone, state) {
    if (!list) return;
    list.className = 'rank-list tone-' + tone;
    var total = state.items.length;
    list.innerHTML = items.map(function (item, i) {
      var value = Number(item[metric.key]) || 0;
      var width = Math.max(2, Math.abs(value) / scale * 100);
      var position = state.items.slice()
        .sort(function (a, b) { return (Number(b[metric.key]) || 0) - (Number(a[metric.key]) || 0); })
        .map(function (x) { return x.name; }).indexOf(item.name) + 1;
      var drill = escapeAttr(JSON.stringify(drillPayload(item, state, position, total)));
      return '<li class="rank-item" data-drill="' + drill + '">' +
        '<span class="rank-index">' + (i + 1 < 10 ? '0' : '') + (i + 1) + '</span>' +
        '<span class="rank-body">' +
          '<span class="rank-name" title="' + escapeAttr(item.name) + '">' + escapeHtml(item.name) + '</span>' +
          '<span class="rank-meta">' + escapeHtml(metaLine(item, state.meta)) + '</span>' +
          '<span class="rank-track"><i style="width:' + width.toFixed(1) + '%"></i></span>' +
        '</span>' +
        '<span class="rank-value">' + fmt(metric.fmt, value) +
          '<small>' + escapeHtml(metric.label) + '</small></span>' +
      '</li>';
    }).join('');
  }

  function escapeHtml(s) {
    return String(s == null ? '' : s).replace(/[&<>]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c];
    });
  }
  function escapeAttr(s) {
    return escapeHtml(s).replace(/"/g, '&quot;');
  }

  function initBoard(board) {
    var payloadEl = board.querySelector('.rank-board-data');
    if (!payloadEl) return;
    var payload;
    try { payload = JSON.parse(payloadEl.textContent); } catch (e) { return; }
    if (!payload || !payload.items || !payload.items.length) return;

    var state = {
      metrics: payload.metrics || [],
      meta: payload.meta || null,
      kicker: payload.kicker || 'Ranking',
      items: payload.items,
      metric: (payload.metrics && payload.metrics[0] && payload.metrics[0].key) || 'net',
      size: payload.size || 5
    };

    board.addEventListener('click', function (event) {
      var btn = event.target.closest('button[data-rank-metric], button[data-rank-size]');
      if (!btn || !board.contains(btn)) return;
      var group = btn.parentNode;
      Array.prototype.forEach.call(group.querySelectorAll('button'), function (b) {
        b.classList.toggle('is-active', b === btn);
      });
      if (btn.hasAttribute('data-rank-metric')) state.metric = btn.getAttribute('data-rank-metric');
      else state.size = parseInt(btn.getAttribute('data-rank-size'), 10) || 5;
      render(board, state);
    });

    render(board, state);
  }

  /* Nested tables are owned by table-behaviour.js. */

  function init() {
    document.querySelectorAll('[data-rank-board]').forEach(initBoard);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
