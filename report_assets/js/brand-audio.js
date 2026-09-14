
(function () {
  var button = document.getElementById('brand-audio-btn');
  var hero = document.querySelector('.hero');
  if (!button || !hero) return;
  var track = new Audio('/audio/fiz-zeek-fifty-seven.mp3');
  var heroVisible = true;
  var cueTimer = 0;
  var lastCue = 0;

  function setPlaying(playing) {
    button.classList.toggle('is-playing', playing);
    button.setAttribute('aria-label', playing ? 'Pause Fiz-zeek Fifty-Seven' : 'Play Fiz-zeek Fifty-Seven');
    button.title = button.getAttribute('aria-label');
  }
  function cueOnScroll() {
    var now = Date.now();
    if (!heroVisible || now - lastCue < 850) return;
    lastCue = now;
    button.classList.remove('is-scroll-cued');
    void button.offsetWidth;
    button.classList.add('is-scroll-cued');
    clearTimeout(cueTimer);
    cueTimer = setTimeout(function () { button.classList.remove('is-scroll-cued'); }, 560);
  }
  new IntersectionObserver(function (entries) { heroVisible = entries[0].isIntersecting; }, { threshold: .12 }).observe(hero);
  window.addEventListener('scroll', cueOnScroll, { passive: true });
  button.addEventListener('click', function () {
    if (track.paused) {
      if (window.__p57ActiveAudioController && window.__p57ActiveAudioController.pause) window.__p57ActiveAudioController.pause();
      track.play().then(function () {
        setPlaying(true);
        window.__p57ActiveAudioController = { audio: track, label: 'Fiz-zeek Fifty-Seven', pause: function () { track.pause(); }, play: function () { return track.play(); } };
        window.dispatchEvent(new CustomEvent('p57-active-audio-change'));
      }).catch(function () { setPlaying(false); });
    } else { track.pause(); }
  });
  track.addEventListener('pause', function () { setPlaying(false); window.dispatchEvent(new CustomEvent('p57-active-audio-change')); });
  track.addEventListener('ended', function () { setPlaying(false); track.currentTime = 0; });
}());
