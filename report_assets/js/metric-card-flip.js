
(function () {
  'use strict';
  document.querySelectorAll('.hero-kpi-grid .kpi-card').forEach(function (card) {
    function setFlipped(next) {
      card.classList.toggle('is-flipped', next);
      card.setAttribute('aria-pressed', next ? 'true' : 'false');
      var label = card.querySelector('.kpi-label');
      card.setAttribute('aria-label', (next ? 'Showing details for ' : 'Show details for ') + (label ? label.textContent.trim() : 'metric'));
    }
    card.setAttribute('role', 'button');
    card.setAttribute('aria-pressed', 'false');
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
})();
