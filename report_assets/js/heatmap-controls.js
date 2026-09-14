/* Demand heatmap: metric swap, day / band / spotlight filters and a per-slot
   drill-down.

   Everything is scoped to one `[data-heatmap-block]` at a time. It used to hang
   off `#demand-heatmap` and `document.querySelectorAll('.hm-band-btn')`, so in
   a bundle covering several studios every control drove the first heatmap and
   the rest looked dead. */
(function () {
  'use strict';

  function initHeatmap(block) {
    var heatmap = block.querySelector('[data-demand-heatmap]');
    if (!heatmap) return;
    var selection = block.querySelector('[data-hm-selection]');
    var metricLabel = block.querySelector('[data-hm-metric-label]');
    var RPV = (window.__REPORT_META__ && window.__REPORT_META__.revenuePerVisit) || 0;
    var list = function (sel) { return Array.prototype.slice.call(block.querySelectorAll(sel)); };

    var cells = list('[data-demand-heatmap] td[data-v]');
    var metricBtns = list('.hm-btn');
    var headers = Array.prototype.slice.call(heatmap.querySelectorAll('thead th'));
    var heatRows = Array.prototype.slice.call(heatmap.querySelectorAll('tbody tr:not(.hm-totals)'));
    var selectableCells = Array.prototype.slice.call(
      heatmap.querySelectorAll('tbody tr:not(.hm-totals) .heat-cell[data-v]'));

    /* ---- Metric swap ---- */
    if (cells.length && metricBtns.length) {
      var grand = heatmap.querySelector('.hm-grand');
      var TOTAL = grand ? +grand.getAttribute('data-v') : 0;
      if (!TOTAL) cells.forEach(function (c) { TOTAL += +c.getAttribute('data-v'); });
      var fmt = {
        visits: function (v) { return v.toLocaleString('en-IN'); },
        revenue: function (v) {
          var r = v * RPV;
          return r >= 100000 ? '₹' + (r / 100000).toFixed(r >= 1000000 ? 1 : 2) + 'L'
                             : '₹' + (r / 1000).toFixed(1) + 'K';
        },
        share: function (v) { return TOTAL ? (v / TOTAL * 100).toFixed(1) + '%' : '0%'; }
      };
      metricBtns.forEach(function (b) {
        b.addEventListener('click', function () {
          metricBtns.forEach(function (x) { x.classList.toggle('is-active', x === b); });
          var f = fmt[b.getAttribute('data-metric')] || fmt.visits;
          cells.forEach(function (c) {
            if (c.childNodes.length && c.childNodes[0].nodeType === 3) {
              c.childNodes[0].nodeValue = f(+c.getAttribute('data-v'));
            }
          });
          if (metricLabel) metricLabel.innerHTML = b.getAttribute('data-label');
        });
      });
    }

    /* ---- Selection + drill-down ---- */
    function clearSelection() {
      heatmap.classList.remove('has-selection');
      heatmap.querySelectorAll('.is-selected,.is-context-row,.is-context-column').forEach(function (node) {
        node.classList.remove('is-selected', 'is-context-row', 'is-context-column');
      });
    }
    function say(html) { if (selection) selection.innerHTML = html; }

    function columnIndexOf(cell) {
      return Array.prototype.indexOf.call(cell.closest('tr').children, cell);
    }

    function selectCell(cell) {
      clearSelection();
      var row = cell.closest('tr');
      var day = row.querySelector('.row-label').textContent.trim();
      var i = columnIndexOf(cell);
      var time = headers[i] ? headers[i].textContent.trim() : 'Slot';
      var detail = cell.querySelector('.heat-sub');
      cell.classList.add('is-selected');
      row.classList.add('is-context-row');
      if (headers[i]) headers[i].classList.add('is-context-column');
      heatmap.classList.add('has-selection');
      say('<strong>' + day + ' · ' + time + '</strong> — ' +
          (+cell.getAttribute('data-v')).toLocaleString('en-IN') + ' visits · ' +
          (detail ? detail.textContent.trim() : 'No format detail recorded'));
    }

    /* Opening a slot shows it against the same slot on every other day and the
       rest of its own day, which is the comparison a scheduler actually makes. */
    function openCell(cell) {
      if (!window.__p57DrillModal) return;
      var row = cell.closest('tr');
      var day = row.querySelector('.row-label').textContent.trim();
      var i = columnIndexOf(cell);
      var time = headers[i] ? headers[i].textContent.trim() : 'Slot';
      var visits = +cell.getAttribute('data-v');
      var grandTotal = 0;
      selectableCells.forEach(function (c) { grandTotal += +c.getAttribute('data-v'); });

      var sameSlot = heatRows.map(function (r) {
        var c = r.children[i];
        if (!c || !c.hasAttribute('data-v')) return null;
        return { label: r.querySelector('.row-label').textContent.trim(), value: +c.getAttribute('data-v') };
      }).filter(Boolean);

      var sameDay = Array.prototype.slice.call(row.children).map(function (c, idx) {
        if (!c.hasAttribute('data-v') || c.classList.contains('hm-grand') || idx === i) return null;
        if (!headers[idx] || headers[idx].classList.contains('total-col')) return null;
        return { label: headers[idx].textContent.trim(), value: +c.getAttribute('data-v') };
      }).filter(Boolean);

      var sub = cell.querySelector('.heat-sub');
      var stats = [
        { label: 'Visits', value: visits.toLocaleString('en-IN') },
        { label: 'Share of week', value: grandTotal ? (visits / grandTotal * 100).toFixed(1) + '%' : '—' },
        { label: 'Day', value: day },
        { label: 'Slot', value: time }
      ];
      if (sub) stats.push({ label: 'Leading format · trainer', value: sub.textContent.trim() });
      var slotPeak = Math.max.apply(null, sameSlot.map(function (s) { return s.value; }).concat([0]));
      if (slotPeak) stats.push({ label: 'vs best day in this slot', value: (visits - slotPeak) + ' visits' });

      window.__p57DrillModal.open({
        kicker: 'Demand heatmap',
        title: day + ' · ' + time,
        subtitle: 'How this slot compares across the week and within its own day.',
        stats: stats,
        bars: sameSlot,
        barsTitle: time + ' on every day',
        table: sameDay.length ? {
          headers: ['Slot', 'Visits'],
          rows: sameDay.map(function (s) { return [s.label, s.value.toLocaleString('en-IN')]; })
        } : null,
        tableTitle: 'The rest of ' + day,
        footnote: 'Esc or click outside to close.'
      }, cell);
    }

    selectableCells.forEach(function (cell) {
      var row = cell.closest('tr');
      var day = row.querySelector('.row-label').textContent.trim();
      var i = columnIndexOf(cell);
      var time = headers[i] ? headers[i].textContent.trim() : 'slot';
      cell.tabIndex = 0;
      cell.setAttribute('role', 'button');
      cell.setAttribute('aria-label', day + ' ' + time + ', ' + cell.getAttribute('data-v') +
        ' visits. Select for details.');
      cell.addEventListener('click', function () { selectCell(cell); openCell(cell); });
      cell.addEventListener('keydown', function (event) {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault(); selectCell(cell); openCell(cell);
        }
      });
    });

    /* ---- Filters: time band, spotlight, single day ---- */
    function bandFor(label) {
      var h = parseInt(String(label).split(':')[0], 10);
      if (!isFinite(h)) return 'all';
      if (h < 12) return 'morning';
      if (h < 17) return 'midday';
      return 'evening';
    }
    var columnBands = headers.map(function (th) { return bandFor(th.textContent.trim()); });

    function applyBand(band) {
      heatmap.querySelectorAll('tr').forEach(function (row) {
        Array.prototype.forEach.call(row.children, function (cell, i) {
          if (i === 0 || i >= headers.length) return;
          var off = band !== 'all' && columnBands[i] !== band;
          cell.classList.toggle('is-dimmed', off);
          if (headers[i]) headers[i].classList.toggle('is-dimmed', off);
        });
      });
    }

    var values = selectableCells.map(function (c) { return +c.getAttribute('data-v'); })
      .sort(function (a, b) { return b - a; });
    function applySpotlight(mode) {
      var cut;
      if (mode === 'peak') cut = values[Math.min(values.length - 1, Math.floor(values.length * 0.2))];
      if (mode === 'quiet') cut = values[Math.max(0, Math.floor(values.length * 0.8))];
      selectableCells.forEach(function (cell) {
        var v = +cell.getAttribute('data-v');
        var on = mode === 'off' || (mode === 'peak' ? v >= cut : v <= cut);
        cell.classList.toggle('is-muted', !on);
      });
    }

    function group(selector, handler) {
      var buttons = list(selector);
      buttons.forEach(function (button) {
        button.setAttribute('aria-pressed', String(button.classList.contains('is-active')));
        button.addEventListener('click', function () {
          buttons.forEach(function (b) {
            var active = b === button;
            b.classList.toggle('is-active', active);
            b.setAttribute('aria-pressed', String(active));
          });
          handler(button);
        });
      });
    }

    group('.hm-band-btn', function (b) { applyBand(b.getAttribute('data-band')); });
    group('.hm-spot-btn', function (b) {
      var mode = b.getAttribute('data-spot');
      applySpotlight(mode);
      say(mode === 'off'
        ? '<strong>All slots shown.</strong> Select a populated slot for detail.'
        : '<strong>' + (mode === 'peak' ? 'Top 20% of slots' : 'Bottom 20% of slots') +
          '</strong> highlighted. Select one to open its breakdown.');
    });
    group('.hm-day-btn', function (b) {
      var day = b.getAttribute('data-day');
      heatRows.forEach(function (row) {
        var rowDay = row.querySelector('.row-label').textContent.trim();
        row.hidden = day !== 'all' && rowDay !== day;
      });
      clearSelection();
      say(day === 'all'
        ? '<strong>All days visible.</strong> Select a populated slot for detail.'
        : '<strong>' + day + ' isolated.</strong> Select a populated slot for detail.');
    });

    heatmap.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') {
        clearSelection();
        say('<strong>Selection cleared.</strong> Choose another populated slot.');
      }
    });
  }

  function init() {
    document.querySelectorAll('[data-heatmap-block]').forEach(initHeatmap);

    // ---- Appendix hint wording ----
    var app = document.getElementById('metric-appendix');
    if (app) {
      app.addEventListener('toggle', function () {
        var l = document.getElementById('app-hint-label');
        if (l) l.textContent = app.open ? 'Collapse metric dictionary' : 'Expand metric dictionary';
      });
    }

    // ---- Expand collapsed appendix for print/PDF export ----
    var closed = [];
    window.addEventListener('beforeprint', function () {
      closed = Array.prototype.slice.call(document.querySelectorAll('details:not([open])'));
      closed.forEach(function (d) { d.open = true; });
    });
    window.addEventListener('afterprint', function () {
      closed.forEach(function (d) { d.open = false; });
      closed = [];
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
