/* Reader tools: a compact, focused reading mode and instant report search. */
(function () {
  'use strict';
  var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var body = document.body;

  function button(label, cls, icon) {
    return '<button type="button" class="reader-tool ' + cls + '" aria-label="' + label + '" title="' + label + '"><span aria-hidden="true">' + icon + '</span><b>' + label + '</b></button>';
  }

  var actions = document.querySelector('.topbar-actions');
  if (!actions) return;
  var reader = document.createElement('div');
  reader.className = 'reader-tools';
  reader.innerHTML = button('Focus mode', 'reader-focus-btn', '◐') + button('Find in report', 'reader-search-btn', '⌕');
  actions.insertBefore(reader, actions.firstChild);

  var stored = false;
  try { stored = localStorage.getItem('studio-pulse-focus') === '1'; } catch (e) {}
  function setFocus(on) {
    body.classList.toggle('focus-mode', on);
    var btn = document.querySelector('.reader-focus-btn');
    if (btn) {
      btn.classList.toggle('is-active', on);
      btn.setAttribute('aria-pressed', String(on));
      btn.querySelector('b').textContent = on ? 'Full view' : 'Focus mode';
    }
    try { localStorage.setItem('studio-pulse-focus', on ? '1' : '0'); } catch (e) {}
  }
  setFocus(stored);
  reader.querySelector('.reader-focus-btn').addEventListener('click', function () {
    setFocus(!body.classList.contains('focus-mode'));
  });

  var dialog = document.createElement('div');
  dialog.className = 'report-search-dialog';
  dialog.innerHTML = '<div class="report-search-panel" role="dialog" aria-modal="true" aria-labelledby="report-search-title">' +
    '<div class="report-search-head"><div><span class="section-eyebrow">Navigate faster</span><h2 id="report-search-title">Find in this report</h2></div><button type="button" class="report-search-close" aria-label="Close search">×</button></div>' +
    '<label class="report-search-input-wrap"><span aria-hidden="true">⌕</span><input autocomplete="off" type="search" placeholder="Search metrics, sections, members…" aria-label="Search report"></label>' +
    '<div class="report-search-results" role="listbox" aria-label="Search results"></div><p class="report-search-hint">Press <kbd>⌘</kbd><kbd>K</kbd> or <kbd>Ctrl</kbd><kbd>K</kbd> to open · <kbd>Esc</kbd> to close</p></div>';
  body.appendChild(dialog);
  var input = dialog.querySelector('input');
  var results = dialog.querySelector('.report-search-results');
  var searchable = Array.prototype.slice.call(document.querySelectorAll('section.report-section, .section-hero, .subsection, .table-card, .data-table-wrap'))
    .filter(function (el, i, list) { return list.indexOf(el.parentElement) === -1; });
  function textFor(el) { return (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim(); }
  function titleFor(el) {
    var heading = el.querySelector('h2, h3, .section-title, .subsection-title, caption');
    return heading ? textFor(heading).slice(0, 100) : 'Report detail';
  }
  function openSearch() {
    dialog.classList.add('is-open'); body.classList.add('search-open');
    window.setTimeout(function () { input.focus(); input.select(); }, reduced ? 0 : 120);
    render(input.value);
  }
  function closeSearch() { dialog.classList.remove('is-open'); body.classList.remove('search-open'); }
  function render(query) {
    var q = (query || '').trim().toLowerCase();
    var matches = searchable.filter(function (el) { return !q || textFor(el).toLowerCase().indexOf(q) !== -1; }).slice(0, 12);
    results.innerHTML = matches.length ? matches.map(function (el, i) {
      var section = el.closest('section[id]') || el;
      var anchor = section.id || '';
      var detail = textFor(el).replace(titleFor(el), '').trim().slice(0, 130);
      return '<button type="button" class="report-search-result" data-target="' + anchor + '" role="option"><span class="result-index">' + String(i + 1).padStart(2, '0') + '</span><span><strong>' + titleFor(el) + '</strong><small>' + detail + '</small></span><span aria-hidden="true">↗</span></button>';
    }).join('') : '<div class="report-search-empty">No matching content yet. Try a metric, member, or section name.</div>';
    results.querySelectorAll('.report-search-result').forEach(function (item) {
      item.addEventListener('click', function () {
        var target = item.getAttribute('data-target');
        closeSearch();
        var node = target && document.getElementById(target);
        if (node) node.scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'start' });
      });
    });
  }
  reader.querySelector('.reader-search-btn').addEventListener('click', openSearch);
  dialog.querySelector('.report-search-close').addEventListener('click', closeSearch);
  dialog.addEventListener('click', function (e) { if (e.target === dialog) closeSearch(); });
  input.addEventListener('input', function () { render(input.value); });
  document.addEventListener('keydown', function (e) {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); openSearch(); }
    if (e.key === 'Escape' && dialog.classList.contains('is-open')) closeSearch();
  });
})();
