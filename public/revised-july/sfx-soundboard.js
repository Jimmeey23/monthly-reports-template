(function () {
  if (window.__p57SfxSoundboardLoaded) return;
  window.__p57SfxSoundboardLoaded = true;

  function sfxUrl(fileName) {
    return new URL('../audio/sfx/' + fileName, document.baseURI).href;
  }

  var sounds = [
    ['Wide Putin Meme', sfxUrl('wide-putin-meme.mp3')],
    ['Haha Funny Laugh', sfxUrl('haha-funny-laugh.mp3')],
    ['Dun Dun Dunnnnnnnn', sfxUrl('dun-dun-dunnnnnnnn.mp3')],
    ['Mario Jump', sfxUrl('mario-jump.mp3')],
    ['Baby Laughing Meme 1', sfxUrl('baby-laughing-meme-1.mp3')],
    ['Applause Cheer', sfxUrl('applause-cheer.mp3')],
    ['Applause', sfxUrl('applause.mp3')],
    ['Fire In The Hole', sfxUrl('fire-in-the-hole.mp3')],
    ['Y2Mate Clip', sfxUrl('y2mate-mp3cut.mp3')],
    ['End Credits', sfxUrl('end-credits.mp3')],
    ['Dun Dun Dun Brass', sfxUrl('dun-dun-dun-brass.mp3')],
    ['Baby Laughing Meme', sfxUrl('baby-laughing-meme.mp3')],
    ['Faaah', sfxUrl('faaah.mp3')],
    ['TF Nemesis', sfxUrl('tf-nemesis.mp3')],
    ['Wow Reaction', sfxUrl('wow-reaction.mp3')],
    ['Failure Trumpet', sfxUrl('failure-trumpet.mp3')],
    ['Mischievous Laugh', sfxUrl('mischievous-laugh.mp3')],
    ['Dramatic Dun Dun Dun', sfxUrl('dramatic-dun-dun-dun.mp3')],
    ['Wait A Minute', sfxUrl('wait-a-minute.mp3')],
    ['Woooooaah', sfxUrl('woooooaah.mp3')],
    ["Isn't That Amazing", sfxUrl('isnt-that-amazing.mp3')],
  ];

  var host = document.createElement('div');
  host.style.position = 'fixed';
  host.style.right = '18px';
  host.style.bottom = '18px';
  host.style.zIndex = '2147483000';
  host.style.width = 'auto';
  host.style.height = 'auto';
  host.style.margin = '0';
  host.style.padding = '0';
  host.style.background = 'transparent';
  document.body.appendChild(host);

  var root = host.attachShadow({ mode: 'open' });
  var style = document.createElement('style');
  style.textContent = [
    '.p57-sfx-board,.p57-sfx-board *{box-sizing:border-box!important}',
    '.p57-sfx-board{position:relative!important;width:auto!important;height:auto!important;margin:0!important;padding:0!important;border:0!important;background:transparent!important;font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif!important;transform:none!important}',
    '.p57-sfx-toggle{appearance:none!important;display:flex!important;align-items:center!important;justify-content:center!important;width:54px!important;height:54px!important;min-width:54px!important;max-width:54px!important;min-height:54px!important;max-height:54px!important;margin:0!important;padding:0!important;border:1px solid rgba(15,44,94,.16)!important;border-radius:50%!important;background:#0f2c5e!important;color:#fff!important;box-shadow:0 14px 30px rgba(15,44,94,.28)!important;font:400 22px/1 sans-serif!important;letter-spacing:0!important;text-align:center!important;cursor:pointer!important;overflow:hidden!important;transform:none!important}',
    '.p57-sfx-mini{appearance:none!important;position:absolute!important;right:5px!important;bottom:62px!important;display:none!important;align-items:center!important;justify-content:center!important;width:44px!important;height:44px!important;min-width:44px!important;min-height:44px!important;margin:0!important;padding:0!important;border:1px solid rgba(15,44,94,.16)!important;border-radius:50%!important;background:#fff!important;color:#0f2c5e!important;box-shadow:0 12px 28px rgba(15,44,94,.24)!important;font:400 18px/1 sans-serif!important;text-align:center!important;cursor:pointer!important;transform:none!important}',
    '.p57-sfx-board.has-active-audio .p57-sfx-mini{display:flex!important}',
    '.p57-sfx-board.is-open .p57-sfx-mini{bottom:488px!important}',
    '@media(max-height:620px){.p57-sfx-board.is-open .p57-sfx-mini{bottom:calc(min(420px,calc(100vh - 104px)) + 72px)!important}}',
    '.p57-sfx-menu{position:absolute!important;right:0!important;bottom:66px!important;display:none!important;width:min(320px,calc(100vw - 36px))!important;height:auto!important;max-height:min(420px,calc(100vh - 104px))!important;overflow:auto!important;margin:0!important;padding:12px!important;border:1px solid #d9e0ec!important;border-radius:8px!important;background:rgba(255,255,255,.98)!important;box-shadow:0 18px 48px rgba(15,44,94,.22)!important;color:#0b1a33!important;transform:none!important}',
    '.p57-sfx-board.is-open .p57-sfx-menu{display:block!important}',
    '.p57-sfx-menu h2{margin:0 0 10px!important;font:400 14px/1.2 sans-serif!important;color:#0b1a33!important}',
    '.p57-sfx-grid{display:grid!important;gap:8px!important}',
    '.p57-sfx-item{display:grid!important;grid-template-columns:minmax(0,1fr) auto!important;align-items:center!important;gap:8px!important;min-height:40px!important;padding:7px 8px!important;border:1px solid #d9e0ec!important;border-radius:6px!important;background:#fff!important}',
    '.p57-sfx-label{overflow:hidden!important;color:#0b1a33!important;font:400 12px/1.25 sans-serif!important;text-overflow:ellipsis!important;white-space:nowrap!important}',
    '.p57-sfx-play{appearance:none!important;display:inline-flex!important;align-items:center!important;justify-content:center!important;min-height:28px!important;min-width:44px!important;margin:0!important;padding:5px 8px!important;border:1px solid #d9e0ec!important;border-radius:5px!important;background:#fff!important;color:#0b1a33!important;font:400 12px/1 sans-serif!important;text-align:center!important;cursor:pointer!important}',
  ].join('');

  var board = document.createElement('div');
  board.className = 'p57-sfx-board';
  board.innerHTML =
    '<button class="p57-sfx-mini" type="button" aria-label="Pause active audio" title="Pause active audio">Ⅱ</button>' +
    '<button class="p57-sfx-toggle" type="button" aria-expanded="false" aria-controls="p57-sfx-menu" title="Open sound effects">:-)</button>' +
    '<div class="p57-sfx-menu" id="p57-sfx-menu" role="dialog" aria-label="Sound effects menu">' +
    '<h2>Sound Effects</h2><div class="p57-sfx-grid">' +
    sounds.map(function (sound) {
      return '<div class="p57-sfx-item"><span class="p57-sfx-label">' + sound[0] + '</span><button class="p57-sfx-play" type="button" data-p57-sfx="' + sound[1] + '">Play</button></div>';
    }).join('') +
    '</div></div>';
  root.appendChild(style);
  root.appendChild(board);

  var toggle = board.querySelector('.p57-sfx-toggle');
  var mini = board.querySelector('.p57-sfx-mini');
  var player = new Audio();
  var activeController = null;

  function updateMiniControl() {
    activeController = window.__p57ActiveAudioController || null;
    var audio = activeController && activeController.audio;
    var hasAudio = Boolean(audio && !audio.ended && audio.src);
    board.classList.toggle('has-active-audio', hasAudio);
    if (!hasAudio) return;
    var isPaused = audio.paused;
    mini.textContent = isPaused ? '▶' : 'Ⅱ';
    mini.setAttribute('aria-label', isPaused ? 'Resume active audio' : 'Pause active audio');
    mini.title = isPaused ? 'Resume active audio' : 'Pause active audio';
  }

  function setActiveAudio(audio, label) {
    window.__p57ActiveAudioController = {
      audio: audio,
      label: label || 'Active audio',
      pause: function () { audio.pause(); },
      play: function () { return audio.play(); }
    };
    updateMiniControl();
    window.dispatchEvent(new CustomEvent('p57-active-audio-change'));
  }

  toggle.addEventListener('click', function () {
    var isOpen = board.classList.toggle('is-open');
    toggle.setAttribute('aria-expanded', String(isOpen));
  });

  board.querySelectorAll('[data-p57-sfx]').forEach(function (button) {
    button.addEventListener('click', function () {
      player.pause();
      player.currentTime = 0;
      player.src = button.dataset.p57Sfx;
      setActiveAudio(player, button.previousElementSibling ? button.previousElementSibling.textContent : 'Sound effect');
      player.play().then(updateMiniControl).catch(updateMiniControl);
    });
  });

  mini.addEventListener('click', function () {
    var controller = window.__p57ActiveAudioController;
    var audio = controller && controller.audio;
    if (!audio) return;
    if (audio.paused) {
      (controller.play ? controller.play() : audio.play()).then(updateMiniControl).catch(updateMiniControl);
    } else {
      if (controller.pause) controller.pause();
      else audio.pause();
      updateMiniControl();
    }
  });

  player.addEventListener('play', updateMiniControl);
  player.addEventListener('pause', updateMiniControl);
  player.addEventListener('ended', updateMiniControl);
  window.addEventListener('p57-active-audio-change', updateMiniControl);

  document.addEventListener('click', function (event) {
    if (event.composedPath && event.composedPath().indexOf(host) !== -1) return;
    if (!host.contains(event.target)) {
      board.classList.remove('is-open');
      toggle.setAttribute('aria-expanded', 'false');
    }
  });
})();
