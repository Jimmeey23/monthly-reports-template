
(function () {
  'use strict';
  // Every metric card in the report flips — the hero grid and the compact
  // cards inside sections are the same component at two sizes.
  document.querySelectorAll('.kpi-card').forEach(function (card) {
    function setFlipped(next) {
      card.classList.toggle('is-flipped', next);
      card.setAttribute('aria-pressed', next ? 'true' : 'false');
      var label = card.querySelector('.kpi-label');
      card.setAttribute('aria-label', (next ? 'Showing details for ' : 'Show details for ') + (label ? label.textContent.trim() : 'metric'));
    }
    card.setAttribute('role', 'button');
    card.setAttribute('aria-pressed', 'false');
    if (!card.hasAttribute('tabindex')) card.setAttribute('tabindex', '0');
    setFlipped(false);
    card.addEventListener('click', function (event) {
      if (event.target.closest('a, button')) return;
      setFlipped(!card.classList.contains('is-flipped'));
    });
    card.addEventListener('keydown', function (event) {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        setFlipped(!card.classList.contains('is-flipped'));
      } else if (event.key === 'Escape') {
        setFlipped(false);
      }
    });
  });

  // The back face carries the full breakdown behind one button, so a flip
  // explains the metric and a second click opens its item-level data.
  document.addEventListener('click', function (event) {
    var btn = event.target.closest('.kpi-drill-btn');
    if (!btn) return;
    event.preventDefault();
    event.stopPropagation();
    var raw = btn.getAttribute('data-drill');
    if (!raw || !window.__p57DrillModal) return;
    try { window.__p57DrillModal.open(JSON.parse(raw), btn); } catch (e) { /* malformed payload */ }
  });
})();
