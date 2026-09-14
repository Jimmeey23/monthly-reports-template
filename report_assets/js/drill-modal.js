/* Context-aware drill-down modal.

   One dialog serves the whole report. Anything that wants to open it carries a
   `data-drill` JSON payload; anything that doesn't gets a payload derived from
   its own DOM (a table row reads its headers, a rank item reads its meta line).
   That way a new list or card becomes drillable without new modal code. */
(function () {
  'use strict';
  if (window.__p57DrillModal) return;

  var FMT = {
    int: function (v) { return Math.round(v).toLocaleString('en-IN'); },
    pct: function (v) { return (Math.round(v * 10) / 10).toFixed(1) + '%'; }
  };

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  /* ─── Shell ──────────────────────────────────────────────────────────── */

  var overlay = null, dialog = null, lastFocus = null;

  function build() {
    overlay = document.createElement('div');
    overlay.className = 'drill-modal-overlay';
    overlay.hidden = true;
    overlay.innerHTML =
      '<div class="drill-modal" role="dialog" aria-modal="true" aria-labelledby="drill-modal-title" tabindex="-1">' +
        '<button class="drill-modal-close" type="button" aria-label="Close details">&times;</button>' +
        '<div class="drill-modal-head">' +
          '<span class="drill-modal-kicker" data-drill-kicker></span>' +
          '<h2 class="drill-modal-title" id="drill-modal-title" data-drill-title></h2>' +
          '<p class="drill-modal-sub" data-drill-sub></p>' +
        '</div>' +
        '<div class="drill-modal-body" data-drill-body></div>' +
        '<div class="drill-modal-foot" data-drill-foot></div>' +
      '</div>';
    document.body.appendChild(overlay);
    dialog = overlay.querySelector('.drill-modal');

    overlay.addEventListener('click', function (e) {
      if (e.target === overlay || e.target.closest('.drill-modal-close')) close();
    });
    document.addEventListener('keydown', function (e) {
      if (overlay.hidden) return;
      if (e.key === 'Escape') { e.preventDefault(); close(); return; }
      if (e.key !== 'Tab') return;
      var focusables = dialog.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
      if (!focusables.length) return;
      var first = focusables[0], last = focusables[focusables.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    });
  }

  function close() {
    if (!overlay || overlay.hidden) return;
    overlay.hidden = true;
    document.body.classList.remove('has-drill-modal');
    if (lastFocus && lastFocus.focus) lastFocus.focus();
    lastFocus = null;
  }

  /* ─── Rendering ──────────────────────────────────────────────────────── */

  function statsHtml(stats) {
    if (!stats || !stats.length) return '';
    return '<div class="drill-stat-grid">' + stats.map(function (s) {
      var tone = s.tone ? ' tone-' + s.tone : '';
      return '<div class="drill-stat' + tone + '">' +
        '<span class="drill-stat-label">' + esc(s.label) + '</span>' +
        '<span class="drill-stat-value">' + (s.html ? s.value : esc(s.value)) + '</span>' +
        (s.sub ? '<span class="drill-stat-sub">' + esc(s.sub) + '</span>' : '') +
      '</div>';
    }).join('') + '</div>';
  }

  function barsHtml(bars, title) {
    var rows = (bars || []).filter(function (b) { return isFinite(Number(b.value)); });
    if (!rows.length) return '';
    var max = Math.max.apply(null, rows.map(function (b) { return Math.abs(Number(b.value)); }).concat([1]));
    return '<div class="drill-block">' +
      (title ? '<div class="drill-block-title">' + esc(title) + '</div>' : '') +
      '<ul class="drill-bars">' + rows.map(function (b) {
        var w = Math.max(2, Math.abs(Number(b.value)) / max * 100);
        return '<li class="drill-bar">' +
          '<span class="drill-bar-name">' + esc(b.label) + '</span>' +
          '<span class="drill-bar-track"><i style="width:' + w.toFixed(1) + '%"></i></span>' +
          '<span class="drill-bar-value">' + esc(b.display != null ? b.display : FMT.int(Number(b.value))) + '</span>' +
        '</li>';
      }).join('') + '</ul></div>';
  }

  function tableHtml(t, title) {
    if (!t || !t.headers || !t.rows || !t.rows.length) return '';
    return '<div class="drill-block">' +
      (title ? '<div class="drill-block-title">' + esc(title) + '</div>' : '') +
      '<div class="table-wrap"><table class="data-table drill-modal-table" data-no-drill>' +
      '<thead><tr>' + t.headers.map(function (h) { return '<th>' + esc(h) + '</th>'; }).join('') + '</tr></thead>' +
      '<tbody>' + t.rows.map(function (r) {
        return '<tr>' + r.map(function (c, i) {
          return '<td class="' + (i === 0 ? 'metric-name' : 'num') + '">' + esc(c) + '</td>';
        }).join('') + '</tr>';
      }).join('') + '</tbody></table></div></div>';
  }

  function notesHtml(notes) {
    if (!notes || !notes.length) return '';
    return '<ul class="drill-notes">' + notes.map(function (n) {
      return '<li>' + n + '</li>';
    }).join('') + '</ul>';
  }

  function open(payload, source) {
    if (!overlay) build();
    lastFocus = source || document.activeElement;
    dialog.querySelector('[data-drill-kicker]').textContent = payload.kicker || 'Detail';
    dialog.querySelector('[data-drill-title]').textContent = payload.title || 'Details';
    var sub = dialog.querySelector('[data-drill-sub]');
    sub.innerHTML = payload.subtitle || '';
    sub.hidden = !payload.subtitle;

    dialog.querySelector('[data-drill-body]').innerHTML =
      statsHtml(payload.stats) +
      barsHtml(payload.bars, payload.barsTitle) +
      tableHtml(payload.table, payload.tableTitle) +
      notesHtml(payload.notes);

    var foot = dialog.querySelector('[data-drill-foot]');
    foot.innerHTML = payload.footnote || '';
    foot.hidden = !payload.footnote;

    overlay.hidden = false;
    document.body.classList.add('has-drill-modal');
    dialog.scrollTop = 0;
    dialog.focus();
  }

  /* ─── Payload derivation ─────────────────────────────────────────────── */

  function parsePayload(el) {
    var raw = el.getAttribute('data-drill');
    if (!raw) return null;
    try { return JSON.parse(raw); } catch (e) { return null; }
  }

  function headerFor(table, index) {
    var head = table.tHead && table.tHead.rows[table.tHead.rows.length - 1];
    var cell = head && head.cells[index];
    return cell ? cell.textContent.trim() : 'Column ' + (index + 1);
  }

  /* A table row becomes: its own figures as stats, plus every sibling row on
     the same column so the reader sees where this row sits in the ledger. */
  function fromRow(row) {
    var table = row.closest('table');
    if (!table) return null;
    var cells = Array.prototype.slice.call(row.cells);
    if (cells.length < 2) return null;
    var label = cells[0].textContent.trim().replace(/\s+/g, ' ');

    var stats = [];
    cells.forEach(function (cell, i) {
      if (i === 0) return;
      var value = cell.textContent.trim().replace(/\s+/g, ' ');
      if (!value || value === '—' || value === 'n/a') return;
      stats.push({ label: headerFor(table, i), value: value });
    });

    // Rank this row against its peers on the first numeric column.
    var bars = [], rankNote = '';
    var numericCol = -1;
    for (var i = 1; i < cells.length; i++) {
      if (parseNum(cells[i].textContent) !== null) { numericCol = i; break; }
    }
    if (numericCol > -1) {
      var peers = [];
      Array.prototype.forEach.call(table.tBodies[0] ? table.tBodies[0].rows : [], function (r) {
        if (r.classList.contains('totals-row') || r.classList.contains('drill-down-detail')) return;
        if (!r.cells[numericCol]) return;
        var n = parseNum(r.cells[numericCol].textContent);
        if (n === null) return;
        peers.push({ label: r.cells[0].textContent.trim().replace(/\s+/g, ' '), value: n,
                     display: r.cells[numericCol].textContent.trim(), self: r === row });
      });
      peers.sort(function (a, b) { return b.value - a.value; });
      var pos = peers.map(function (p) { return p.self; }).indexOf(true);
      if (pos > -1) {
        rankNote = 'Ranked <strong>#' + (pos + 1) + ' of ' + peers.length + '</strong> by ' +
          esc(headerFor(table, numericCol)) + '.';
      }
      bars = peers.slice(0, 12);
    }

    var panel = row.closest('.data-panel, .data-pane, .figure-band');
    var panelTitle = panel && panel.querySelector('.panel-title, .pane-title');

    return {
      kicker: panelTitle ? panelTitle.textContent.trim() : 'Row detail',
      title: label,
      subtitle: stats.length + ' recorded measures for this row.',
      stats: stats,
      bars: bars,
      barsTitle: numericCol > -1 ? headerFor(table, numericCol) + ' across every row' : '',
      notes: rankNote ? [rankNote] : [],
      footnote: 'Esc or click outside to close.'
    };
  }

  function parseNum(text) {
    var cleaned = String(text || '').replace(/[,\s₹%×]/g, '');
    var mult = 1;
    if (/L$/i.test(cleaned)) { mult = 1e5; cleaned = cleaned.slice(0, -1); }
    else if (/Cr$/i.test(cleaned)) { mult = 1e7; cleaned = cleaned.slice(0, -2); }
    else if (/K$/i.test(cleaned)) { mult = 1e3; cleaned = cleaned.slice(0, -1); }
    var n = parseFloat(cleaned);
    return isFinite(n) ? n * mult : null;
  }

  function fromRankItem(item) {
    var name = item.querySelector('.rank-name');
    var meta = item.querySelector('.rank-meta');
    var value = item.querySelector('.rank-value');
    var stats = [];
    if (meta) {
      meta.textContent.split('·').forEach(function (part) {
        var t = part.trim();
        if (!t) return;
        var m = t.match(/^(.+?)\s+([A-Za-z%\s]+)$/);
        if (m) stats.push({ label: m[2].trim(), value: m[1].trim() });
        else stats.push({ label: 'Detail', value: t });
      });
    }
    if (value) {
      stats.unshift({ label: (value.querySelector('small') || {}).textContent || 'Value',
                      value: value.childNodes[0] ? value.childNodes[0].nodeValue.trim() : value.textContent.trim() });
    }
    var board = item.closest('[data-rank-board]');
    return {
      kicker: board ? (board.querySelector('.metric-block-eyebrow') || {}).textContent || 'Ranking' : 'Ranking',
      title: name ? name.textContent.trim() : 'Item',
      subtitle: 'Position ' + ((item.querySelector('.rank-index') || {}).textContent || '') +
                ' in this ranking.',
      stats: stats,
      footnote: 'Esc or click outside to close.'
    };
  }

  function fromBarRow(li) {
    var name = li.querySelector('.bar-name');
    var list = li.closest('.bar-list');
    var bars = list ? Array.prototype.map.call(list.querySelectorAll('.bar-row'), function (r) {
      return {
        label: (r.querySelector('.bar-name') || {}).textContent || '',
        value: parseNum((r.querySelector('.bar-value') || {}).textContent) || 0,
        display: ((r.querySelector('.bar-value') || {}).textContent || '').trim()
      };
    }) : [];
    return {
      kicker: 'Ranked list',
      title: name ? name.textContent.trim() : 'Item',
      stats: [
        { label: 'Value', value: ((li.querySelector('.bar-value') || {}).textContent || '').trim() },
        { label: 'Share of listed total', value: ((li.querySelector('.bar-share') || {}).textContent || '').trim() },
        { label: 'Rank', value: ((li.querySelector('.bar-rank') || {}).textContent || '').trim() }
      ],
      bars: bars,
      barsTitle: 'Every item in this list',
      footnote: 'Esc or click outside to close.'
    };
  }

  /* ─── Delegation ─────────────────────────────────────────────────────── */

  var TRIGGER = '[data-drill], .rank-item, .bar-row, .drill-down-row';

  function shouldIgnore(target) {
    return !!target.closest('a, button, input, select, textarea, .row-toggle, .drill-modal');
  }

  function handle(event) {
    var el = event.target.closest(TRIGGER);
    if (!el || shouldIgnore(event.target)) return;
    var payload = parsePayload(el);
    if (!payload) {
      if (el.matches('.rank-item')) payload = fromRankItem(el);
      else if (el.matches('.bar-row')) payload = fromBarRow(el);
      else if (el.tagName === 'TR') payload = fromRow(el);
    }
    if (!payload) return;
    event.preventDefault();
    open(payload, el);
  }

  function markTriggers() {
    document.querySelectorAll(TRIGGER).forEach(function (el) {
      if (el.hasAttribute('data-drill-ready')) return;
      el.setAttribute('data-drill-ready', '');
      el.classList.add('is-drillable');
      if (el.tagName !== 'TR' && !el.hasAttribute('tabindex')) el.setAttribute('tabindex', '0');
      if (!el.hasAttribute('role') && el.tagName !== 'TR') el.setAttribute('role', 'button');
    });
  }

  function init() {
    build();
    markTriggers();
    document.addEventListener('click', handle);
    document.addEventListener('keydown', function (e) {
      if (e.key !== 'Enter' && e.key !== ' ') return;
      var el = e.target.closest && e.target.closest(TRIGGER);
      if (!el || el.tagName === 'TR') return;
      e.preventDefault();
      handle({ target: e.target, preventDefault: function () {} });
    });
    // Rank boards and sortable tables re-render their lists.
    var mo = new MutationObserver(function () { markTriggers(); });
    document.querySelectorAll('.rank-list, .bar-list, tbody').forEach(function (n) {
      mo.observe(n, { childList: true });
    });
  }

  window.__p57DrillModal = { open: open, close: close };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
