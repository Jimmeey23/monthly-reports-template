
(function () {
  'use strict';
  var prefersReduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var progress = document.getElementById('scroll-progress');
  var toTop = document.getElementById('back-to-top');
  var ticking = false;

  function syncScrollUI() {
    var max = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
    var ratio = Math.min(1, Math.max(0, window.scrollY / max));
    if (progress) progress.style.width = (ratio * 100).toFixed(2) + '%';
    if (toTop) toTop.classList.toggle('is-visible', window.scrollY > 720);
    ticking = false;
  }
  window.addEventListener('scroll', function () {
    if (!ticking) { requestAnimationFrame(syncScrollUI); ticking = true; }
  }, { passive: true });
  syncScrollUI();

  if (toTop) toTop.addEventListener('click', function () {
    window.scrollTo({ top: 0, behavior: prefersReduced ? 'auto' : 'smooth' });
  });

  // Reveal major content groups only when they enter the reading flow.
  var revealNodes = Array.prototype.slice.call(document.querySelectorAll(
    '.ai-result-v2, .split-grid, .subsection, .worked-grid, .action-grid, .funnel-stages, .conclusions-block'
  ));
  revealNodes.forEach(function (el) {
    el.classList.add('reveal');
    if (el.classList.contains('split-grid')) el.classList.add('reveal-left');
  });

  if (!prefersReduced && 'IntersectionObserver' in window) {
    var revealObserver = new IntersectionObserver(function (entries, observer) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.06 });
    revealNodes.forEach(function (el) {
      if (el.getBoundingClientRect().top < window.innerHeight * .92) el.classList.add('is-visible');
      else revealObserver.observe(el);
    });
  } else {
    revealNodes.forEach(function (el) { el.classList.add('is-visible'); });
  }

  // Animate headline KPI values once, preserving Indian-number formatting and suffixes.
  function animateMetric(el) {
    var original = (el.textContent || '').trim();
    var match = original.match(/^([^\d-]*)(-?[\d,]+(?:\.\d+)?)(.*)$/);
    if (!match) return;
    var prefix = match[1], numericText = match[2], suffix = match[3];
    var target = parseFloat(numericText.replace(/,/g, ''));
    if (!isFinite(target)) return;
    var decimals = (numericText.split('.')[1] || '').length;
    var useGrouping = numericText.indexOf(',') > -1;
    var start = performance.now(), duration = 1150;
    function frame(now) {
      var p = Math.min(1, (now - start) / duration);
      var eased = 1 - Math.pow(1 - p, 4);
      var value = target * eased;
      var formatted = useGrouping
        ? value.toLocaleString('en-IN', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
        : value.toFixed(decimals);
      el.textContent = prefix + formatted + suffix;
      if (p < 1) requestAnimationFrame(frame);
      else el.textContent = original;
    }
    requestAnimationFrame(frame);
  }
  if (!prefersReduced) {
    document.querySelectorAll('.hero-kpi-grid .kpi-value').forEach(function (el, index) {
      window.setTimeout(function () { animateMetric(el); }, 360 + index * 70);
    });
  }

  // Pointer-responsive light on KPI cards (subtle, no layout movement).
  if (!prefersReduced && window.matchMedia('(pointer:fine)').matches) {
    document.querySelectorAll('.kpi-card').forEach(function (card) {
      card.addEventListener('pointermove', function (event) {
        var r = card.getBoundingClientRect();
        card.style.setProperty('--mx', ((event.clientX - r.left) / r.width * 100).toFixed(1) + '%');
        card.style.setProperty('--my', ((event.clientY - r.top) / r.height * 100).toFixed(1) + '%');
      });
      card.addEventListener('pointerleave', function () {
        card.style.setProperty('--mx', '70%');
        card.style.setProperty('--my', '10%');
      });
    });
  }

  // Current-section state in the compact navigation.
  var navLinks = Array.prototype.slice.call(document.querySelectorAll('.topnav a, .side-quicknav a'));
  var sectionMap = navLinks.map(function (link) {
    return { link: link, section: document.querySelector(link.getAttribute('href')) };
  }).filter(function (item) { return item.section; });
  if ('IntersectionObserver' in window) {
    var activeObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          var current = sectionMap.find(function (item) { return item.section === entry.target; });
          if (!current) return;
          sectionMap.forEach(function (item) {
            item.link.classList.toggle('is-active', item.link.getAttribute('href') === current.link.getAttribute('href'));
          });
        }
      });
    }, { rootMargin: '-28% 0px -64% 0px', threshold: 0 });
    sectionMap.forEach(function (item) { activeObserver.observe(item.section); });
  }
})();
