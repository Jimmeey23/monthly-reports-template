
(function () {
  'use strict';
  var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  document.querySelectorAll('.hero-carousel').forEach(function (carousel) {
    var slides = Array.prototype.slice.call(carousel.querySelectorAll('.hero-carousel-slide'));
    var dots = Array.prototype.slice.call(carousel.querySelectorAll('.hero-carousel-dot'));
    var prev = carousel.querySelector('[data-carousel-prev]');
    var next = carousel.querySelector('[data-carousel-next]');
    if (slides.length < 2) return;
    var index = 0, timer = null, paused = false;
    function show(target, restart) {
      index = (target + slides.length) % slides.length;
      slides.forEach(function (slide, i) { slide.classList.toggle('is-active', i === index); slide.setAttribute('aria-hidden', i === index ? 'false' : 'true'); });
      dots.forEach(function (dot, i) { dot.classList.toggle('is-active', i === index); dot.setAttribute('aria-current', i === index ? 'true' : 'false'); });
      carousel.classList.remove('is-playing'); void carousel.offsetWidth;
      if (!reduced && !paused) carousel.classList.add('is-playing');
      if (restart) start();
    }
    function start() { clearInterval(timer); if (!reduced && !paused) timer = setInterval(function () { show(index + 1, false); }, 5500); }
    function setPaused(value) { paused = value; if (paused) { clearInterval(timer); carousel.classList.remove('is-playing'); } else { show(index, true); } }
    if (prev) prev.addEventListener('click', function () { show(index - 1, true); });
    if (next) next.addEventListener('click', function () { show(index + 1, true); });
    dots.forEach(function (dot, i) { dot.addEventListener('click', function () { show(i, true); }); });
    carousel.addEventListener('mouseenter', function () { setPaused(true); });
    carousel.addEventListener('mouseleave', function () { setPaused(false); });
    carousel.addEventListener('focusin', function () { setPaused(true); });
    carousel.addEventListener('focusout', function () { setPaused(false); });
    show(0, true);
  });
})();
