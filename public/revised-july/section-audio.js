(function () {
  'use strict';
  if (window.__p57SectionAudioLoaded) return;
  window.__p57SectionAudioLoaded = true;

  var isBandra = /supreme|bandra/i.test(window.location.pathname + ' ' + document.title);
  var prefix = isBandra ? 'supreme' : 'kemps';
  var audioIndex = 0;
  var currentAudio = null;
  var currentButton = null;
  var playIcon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M11 5 6 9H3v6h3l5 4V5Z"></path><path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path><path d="M19.07 4.93a10 10 0 0 1 0 14.14"></path></svg>';
  var pauseIcon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="6" y="4" width="4" height="16" rx="1"></rect><rect x="14" y="4" width="4" height="16" rx="1"></rect></svg>';

  var style = document.createElement('style');
  style.textContent =
    '.section-audio-btn{width:24px;height:24px;border:1px solid var(--border-strong,var(--border));border-radius:999px;display:inline-flex;align-items:center;justify-content:center;background:transparent;color:var(--text-subtle,var(--primary));opacity:.75;cursor:pointer;transition:transform 160ms ease,border-color 160ms ease,color 160ms ease,opacity 160ms ease}' +
    '.section-audio-btn:hover,.section-audio-btn:focus-visible{opacity:1;border-color:var(--accent);color:var(--accent);outline:none}' +
    '.section-audio-btn svg{width:12px;height:12px;pointer-events:none}' +
    '.section-audio-btn.is-playing{color:white;border-color:var(--accent);background:var(--accent);box-shadow:0 10px 28px color-mix(in srgb,var(--accent) 28%,transparent)}' +
    '.section-audio-btn.is-loading{animation:p57SectionAudioPulse 900ms ease-in-out infinite}' +
    '@keyframes p57SectionAudioPulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.72;transform:scale(.96)}}';
  document.head.appendChild(style);

  function audioUrl(fileName) {
    return new URL('../audio/' + fileName, document.baseURI).href;
  }

  function resetButton(button) {
    if (!button) return;
    button.classList.remove('is-playing', 'is-loading');
    button.setAttribute('aria-label', button.dataset.audioLabel || 'Play section audio');
    button.innerHTML = playIcon;
  }

  function setActiveAudio(audio, button) {
    window.__p57ActiveAudioController = {
      audio: audio,
      label: button && button.dataset.audioLabel ? button.dataset.audioLabel : 'Section audio',
      pause: function () {
        audio.pause();
        resetButton(button);
      },
      play: function () {
        if (button) {
          button.classList.add('is-loading');
          button.setAttribute('aria-label', 'Pause section audio');
          button.innerHTML = pauseIcon;
        }
        return audio.play();
      }
    };
    window.dispatchEvent(new CustomEvent('p57-active-audio-change'));
  }

  function attachButton(headerRight, title) {
    if (!headerRight || headerRight.querySelector('.section-audio-btn')) return;
    audioIndex += 1;
    var button = document.createElement('button');
    button.type = 'button';
    button.className = 'section-audio-btn';
    button.dataset.audioSrc = audioUrl(prefix + '-' + audioIndex + '.mp3');
    button.dataset.audioLabel = 'Play ' + (title || 'section') + ' audio';
    button.setAttribute('aria-label', button.dataset.audioLabel);
    button.title = button.dataset.audioLabel;
    button.innerHTML = playIcon;
    headerRight.insertBefore(button, headerRight.firstChild);
  }

  document.querySelectorAll('section.report-section .section-hero').forEach(function (hero) {
    var headerRight = hero.querySelector('.section-header-right');
    var titleNode = hero.querySelector('.section-title');
    attachButton(headerRight, titleNode ? titleNode.textContent.trim() : '');
  });

  document.querySelectorAll('.section-audio-btn').forEach(function (button) {
    button.addEventListener('click', function (event) {
      event.preventDefault();
      event.stopPropagation();
      var src = button.dataset.audioSrc;
      if (!src) return;

      if (currentButton === button && currentAudio && !currentAudio.paused) {
        currentAudio.pause();
        resetButton(button);
        window.dispatchEvent(new CustomEvent('p57-active-audio-change'));
        return;
      }

      if (currentAudio) currentAudio.pause();
      resetButton(currentButton);
      currentButton = button;
      currentAudio = new Audio(src);
      setActiveAudio(currentAudio, button);
      button.classList.add('is-loading');
      button.setAttribute('aria-label', 'Pause section audio');
      button.innerHTML = pauseIcon;

      currentAudio.addEventListener('playing', function () {
        button.classList.remove('is-loading');
        button.classList.add('is-playing');
        window.dispatchEvent(new CustomEvent('p57-active-audio-change'));
      });
      currentAudio.addEventListener('pause', function () {
        if (!currentAudio.ended) window.dispatchEvent(new CustomEvent('p57-active-audio-change'));
      });
      currentAudio.addEventListener('ended', function () {
        resetButton(button);
        window.dispatchEvent(new CustomEvent('p57-active-audio-change'));
      });
      currentAudio.addEventListener('error', function () {
        resetButton(button);
        window.dispatchEvent(new CustomEvent('p57-active-audio-change'));
      });
      currentAudio.play().catch(function () { resetButton(button); });
    });
  });
})();
