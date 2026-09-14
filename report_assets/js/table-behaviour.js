/* Table behaviour: nested row expansion, column sorting, and the mobile card
   view. Row drill-downs are handled by drill-modal.js — this file only marks
   the rows that qualify, so there is one click owner per behaviour. */
(function () {
  'use strict';

  /* ─── Nested rows ───────────────────────────────────────────────────────
     A parent row carries `.group-row.has-children` (or `.child-row.has-children`
     one level down) and a toggle whose aria-controls names the group; its
     children are `.child-row[data-parent]`. Closing a branch closes everything
     beneath it, so a deep tree never springs fully open. */

  function cssEscape(s) {
    return String(s).replace(/["\\]/g, '\\$&');
  }

  function childrenOf(table, id) {
    if (!id) return [];
    return Array.prototype.slice.call(
      table.querySelectorAll('tr.child-row[data-parent="' + cssEscape(id) + '"]'));
  }

  function setOpen(table, row, open) {
    var btn = row.querySelector('.row-toggle');
    var id = btn ? btn.getAttribute('aria-controls') : row.getAttribute('data-group');
    if (btn) btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    row.classList.toggle('is-open', open);
    childrenOf(table, id).forEach(function (child) {
      child.hidden = !open;
      if (!open && child.classList.contains('has-children')) setOpen(table, child, false);
    });
  }

  function initNested(table) {
    if (table.hasAttribute('data-nested-ready')) return;
    table.setAttribute('data-nested-ready', '');
    table.querySelectorAll('tr.has-children').forEach(function (row) {
      setOpen(table, row, row.classList.contains('is-open'));
    });
    table.addEventListener('click', function (event) {
      var row = event.target.closest('tr.has-children');
      if (!row || !table.contains(row)) return;
      // A click anywhere on a parent row toggles it — the caret is an
      // affordance, not the only target. Stop here so the drill modal does
      // not also fire for the same click.
      event.stopPropagation();
      setOpen(table, row, !row.classList.contains('is-open'));
    });
    table.addEventListener('keydown', function (event) {
      if (event.key !== 'Enter' && event.key !== ' ') return;
      var btn = event.target.closest('.row-toggle');
      if (!btn) return;
      event.preventDefault();
      var row = btn.closest('tr.has-children');
      if (row) setOpen(table, row, !row.classList.contains('is-open'));
    });
  }

  function initNestedControls() {
    document.addEventListener('click', function (event) {
      var btn = event.target.closest('[data-nested-expand], [data-nested-collapse]');
      if (!btn) return;
      var open = btn.hasAttribute('data-nested-expand');
      var scope = btn.closest('.data-panel, .data-pane, section') || document;
      scope.querySelectorAll('table.nested-table').forEach(function (table) {
        table.querySelectorAll('tr.has-children').forEach(function (row) {
          setOpen(table, row, open);
        });
      });
      var group = btn.parentNode;
      if (group) group.querySelectorAll('button').forEach(function (b) {
        b.classList.toggle('is-active', b === btn);
      });
    });
  }

  /* ─── Column sorting ────────────────────────────────────────────────────
     Any table marked `data-sortable` gets clickable headers. Nested tables
     opt out: sorting would tear children away from their parents. */

  function cellValue(row, index) {
    var cell = row.cells[index];
    if (!cell) return { n: null, s: '' };
    var explicit = cell.getAttribute('data-sort-value');
    var text = (explicit != null ? explicit : cell.textContent).trim();
    var cleaned = text.replace(/[,\s₹%×+]/g, '');
    var mult = 1;
    if (/^-?[\d.]+L$/i.test(cleaned)) { mult = 1e5; cleaned = cleaned.slice(0, -1); }
    else if (/^-?[\d.]+Cr$/i.test(cleaned)) { mult = 1e7; cleaned = cleaned.slice(0, -2); }
    else if (/^-?[\d.]+K$/i.test(cleaned)) { mult = 1e3; cleaned = cleaned.slice(0, -1); }
    else if (/^-?[\d.]+pp$/i.test(cleaned)) { cleaned = cleaned.slice(0, -2); }
    var n = parseFloat(cleaned);
    return { n: isFinite(n) ? n * mult : null, s: text.toLowerCase() };
  }

  function sortTable(table, index, dir) {
    var body = table.tBodies[0];
    var head = table.tHead && table.tHead.rows[table.tHead.rows.length - 1];
    if (!body || !head) return;
    var rows = Array.prototype.slice.call(body.rows);
    var totals = rows.filter(function (r) { return r.classList.contains('totals-row'); });
    var data = rows.filter(function (r) { return !r.classList.contains('totals-row'); });

    data.sort(function (a, b) {
      var av = cellValue(a, index), bv = cellValue(b, index);
      if (av.n !== null && bv.n !== null) return dir * (av.n - bv.n);
      return dir * av.s.localeCompare(bv.s);
    });

    data.concat(totals).forEach(function (r) { body.appendChild(r); });
    Array.prototype.forEach.call(head.cells, function (th, i) {
      th.classList.toggle('is-sorted', i === index);
      th.classList.toggle('is-desc', i === index && dir < 0);
      th.setAttribute('aria-sort', i !== index ? 'none' : (dir > 0 ? 'ascending' : 'descending'));
    });
  }

  function initSortable(table) {
    if (table.hasAttribute('data-sortable-ready')) return;
    table.setAttribute('data-sortable-ready', '');
    var head = table.tHead && table.tHead.rows[table.tHead.rows.length - 1];
    if (!head) return;
    Array.prototype.forEach.call(head.cells, function (th, index) {
      if (th.hasAttribute('data-no-sort')) return;
      th.classList.add('is-sortable');
      th.setAttribute('tabindex', '0');
      th.setAttribute('aria-sort', 'none');
      var activate = function () {
        // First click on a metric column shows the largest first, which is
        // what a reader ranking a scorecard actually wants.
        var desc = !th.classList.contains('is-sorted') ? index !== 0 : !th.classList.contains('is-desc');
        sortTable(table, index, desc ? -1 : 1);
      };
      th.addEventListener('click', activate);
      th.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); activate(); }
      });
    });
  }

  /* External sort chips: `data-sort-table="<id>" data-sort-col="<n>"`. */
  function initSortChips() {
    document.addEventListener('click', function (event) {
      var chip = event.target.closest('[data-sort-table]');
      if (!chip) return;
      var table = document.getElementById(chip.getAttribute('data-sort-table'));
      if (!table) return;
      var index = parseInt(chip.getAttribute('data-sort-col'), 10) || 0;
      var dir = chip.getAttribute('data-sort-dir') === 'asc' ? 1 : -1;
      if (chip.classList.contains('is-active')) dir = -dir;
      chip.setAttribute('data-sort-dir', dir > 0 ? 'asc' : 'desc');
      sortTable(table, index, dir);
      var group = chip.parentNode;
      if (group) group.querySelectorAll('button').forEach(function (b) {
        b.classList.toggle('is-active', b === chip);
      });
    });
  }

  /* ─── Drill-down eligibility ────────────────────────────────────────── */

  function markDrillRows() {
    document.querySelectorAll(
      '.data-table:not(.heatmap-table):not(.mom-table):not(.drill-modal-table):not([data-no-drill])'
    ).forEach(function (table) {
      var body = table.tBodies[0];
      if (!body) return;
      Array.prototype.forEach.call(body.rows, function (row) {
        if (row.classList.contains('totals-row')) return;
        if (row.cells.length < 3) return;
        row.classList.add('drill-down-row');
      });
    });
  }

  /* ─── Mobile card view ──────────────────────────────────────────────── */

  function initMobileCards() {
    if (window.innerWidth > 768) return;
    document.querySelectorAll('table.data-table').forEach(function (table) {
      if (table.classList.contains('heatmap-table')) return;
      table.classList.add('mobile-cards');
      var headers = Array.prototype.map.call(
        table.querySelectorAll('thead tr:last-child th'),
        function (th) { return th.textContent.trim(); });
      table.querySelectorAll('tbody td').forEach(function (td) {
        var idx = Array.prototype.indexOf.call(td.parentNode.children, td);
        if (headers[idx]) td.setAttribute('data-label', headers[idx]);
      });
    });
  }

  function init() {
    document.querySelectorAll('table.nested-table').forEach(initNested);
    // Every plain ledger sorts. Nested tables opt out because sorting would
    // separate children from their parents; the heatmap and MoM grids are not
    // ledgers at all.
    document.querySelectorAll(
      'table.data-table:not(.nested-table):not(.heatmap-table):not(.mom-table):not(.drill-modal-table):not([data-no-sort])'
    ).forEach(initSortable);
    initNestedControls();
    initSortChips();
    markDrillRows();
    initMobileCards();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
