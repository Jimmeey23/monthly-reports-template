/* Member-level expiration book: outcome filters, free-text search and a
   per-member drill-down. Scoped per block so a multi-studio bundle works. */
(function () {
  'use strict';

  function init(book) {
    var rows = Array.prototype.slice.call(book.querySelectorAll('.member-row'));
    var chips = Array.prototype.slice.call(book.querySelectorAll('[data-member-filter]'));
    var search = book.querySelector('[data-member-search-input]');
    var count = book.querySelector('[data-member-count]');
    var filter = 'all';
    var term = '';

    function apply() {
      var shown = 0;
      rows.forEach(function (row) {
        var statusOk = filter === 'all' || row.getAttribute('data-member-status') === filter;
        var textOk = !term || (row.getAttribute('data-member-search') || '').indexOf(term) !== -1;
        var on = statusOk && textOk;
        row.hidden = !on;
        if (on) shown++;
      });
      if (count) {
        count.textContent = shown === rows.length
          ? 'Showing all ' + rows.length + ' memberships.'
          : 'Showing ' + shown + ' of ' + rows.length + ' memberships.';
      }
    }

    chips.forEach(function (chip) {
      chip.addEventListener('click', function () {
        filter = chip.getAttribute('data-member-filter');
        chips.forEach(function (c) { c.classList.toggle('is-active', c === chip); });
        apply();
      });
    });

    if (search) {
      search.addEventListener('input', function () {
        term = search.value.trim().toLowerCase();
        apply();
      });
    }

    /* Row drill-down comes from the shared modal via each row's data-drill
       payload, so there is only one row-detail behaviour in the report. */

    apply();
  }

  function start() { document.querySelectorAll('[data-member-book]').forEach(init); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
