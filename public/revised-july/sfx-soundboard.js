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
    '.p57-speaker-toggle{appearance:none!important;position:absolute!important;right:5px!important;bottom:112px!important;display:flex!important;align-items:center!important;justify-content:center!important;width:44px!important;height:44px!important;min-width:44px!important;min-height:44px!important;margin:0!important;padding:0!important;border:1px solid rgba(15,44,94,.16)!important;border-radius:50%!important;background:#fff!important;color:#0f2c5e!important;box-shadow:0 12px 28px rgba(15,44,94,.22)!important;font:400 13px/1 sans-serif!important;text-align:center!important;cursor:pointer!important;transform:none!important}',
    '.p57-sfx-board.has-active-audio .p57-sfx-mini{display:flex!important}',
    '.p57-sfx-board.has-active-audio .p57-speaker-toggle{bottom:112px!important}',
    '.p57-sfx-board.has-active-audio .p57-sfx-mini{bottom:162px!important}',
    '.p57-sfx-board.is-open .p57-sfx-mini{bottom:488px!important}',
    '.p57-sfx-board.is-open .p57-speaker-toggle{bottom:438px!important}',
    '.p57-sfx-board.is-open.has-active-audio .p57-sfx-mini{bottom:488px!important}',
    '@media(max-height:620px){.p57-sfx-board.is-open .p57-sfx-mini{bottom:calc(min(420px,calc(100vh - 104px)) + 72px)!important}}',
    '@media(max-height:620px){.p57-sfx-board.is-open .p57-speaker-toggle{bottom:calc(min(420px,calc(100vh - 104px)) + 22px)!important}}',
    '.p57-speaker-panel{position:absolute!important;right:58px!important;bottom:0!important;display:none!important;width:min(340px,calc(100vw - 92px))!important;max-height:min(470px,calc(100vh - 36px))!important;overflow:hidden!important;margin:0!important;border:1px solid #d9e0ec!important;border-radius:8px!important;background:rgba(255,255,255,.98)!important;box-shadow:0 18px 48px rgba(15,44,94,.24)!important;color:#0b1a33!important;transform:none!important}',
    '.p57-speaker-panel.is-open{display:flex!important;flex-direction:column!important}',
    '.p57-speaker-head{display:grid!important;grid-template-columns:minmax(0,1fr) auto!important;align-items:center!important;gap:8px!important;padding:10px 12px!important;border-bottom:1px solid #d9e0ec!important;background:#fff!important}',
    '.p57-speaker-title{min-width:0!important;overflow:hidden!important;text-overflow:ellipsis!important;white-space:nowrap!important;font:400 13px/1.25 sans-serif!important;color:#0b1a33!important}',
    '.p57-speaker-close{appearance:none!important;display:inline-flex!important;align-items:center!important;justify-content:center!important;width:30px!important;height:30px!important;border:1px solid #d9e0ec!important;border-radius:999px!important;background:#fff!important;color:#0b1a33!important;font:400 16px/1 sans-serif!important;cursor:pointer!important}',
    '.p57-speaker-body{padding:12px!important;overflow:auto!important}',
    '.p57-speaker-kicker{margin:0 0 8px!important;color:#526174!important;font:400 11px/1.35 sans-serif!important;text-transform:uppercase!important;letter-spacing:.08em!important}',
    '.p57-speaker-h{margin:0 0 8px!important;color:#0b1a33!important;font:400 15px/1.28 sans-serif!important}',
    '.p57-speaker-script{margin:0 0 10px!important;color:#1d2b44!important;font:400 13px/1.45 sans-serif!important}',
    '.p57-speaker-list{margin:0!important;padding:0 0 0 17px!important;color:#1d2b44!important;font:400 12.5px/1.42 sans-serif!important}',
    '.p57-speaker-list li{margin:0 0 6px!important;padding:0!important}',
    '.p57-speaker-actions{display:flex!important;align-items:center!important;justify-content:space-between!important;gap:8px!important;padding:10px 12px!important;border-top:1px solid #d9e0ec!important;background:#fff!important}',
    '.p57-speaker-nav{appearance:none!important;display:inline-flex!important;align-items:center!important;justify-content:center!important;min-height:30px!important;min-width:64px!important;padding:6px 10px!important;border:1px solid #d9e0ec!important;border-radius:999px!important;background:#fff!important;color:#0b1a33!important;font:400 12px/1 sans-serif!important;text-align:center!important;cursor:pointer!important}',
    '.p57-speaker-count{font:400 11px/1 sans-serif!important;color:#526174!important}',
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
    '<button class="p57-speaker-toggle" type="button" aria-expanded="false" aria-controls="p57-speaker-panel" title="Speaker notes">SN</button>' +
    '<aside class="p57-speaker-panel" id="p57-speaker-panel" aria-label="Speaker notes">' +
      '<div class="p57-speaker-head"><div class="p57-speaker-title">Speaker Notes</div><button class="p57-speaker-close" type="button" aria-label="Close speaker notes">×</button></div>' +
      '<div class="p57-speaker-body"></div>' +
      '<div class="p57-speaker-actions"><button class="p57-speaker-nav" type="button" data-p57-note-prev>Previous</button><span class="p57-speaker-count"></span><button class="p57-speaker-nav" type="button" data-p57-note-next>Next</button></div>' +
    '</aside>' +
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
  var notesToggle = board.querySelector('.p57-speaker-toggle');
  var notesPanel = board.querySelector('.p57-speaker-panel');
  var notesBody = board.querySelector('.p57-speaker-body');
  var notesCount = board.querySelector('.p57-speaker-count');
  var noteIndex = 0;
  var player = new Audio();
  var activeController = null;

  function cleanText(text) {
    return String(text || '').replace(/\s+/g, ' ').trim();
  }

  function escapeHtml(text) {
    return cleanText(text).replace(/[&<>"']/g, function (char) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char];
    });
  }

  function buildSpeakerNotes() {
    var sections = Array.prototype.slice.call(document.querySelectorAll('section.report-section'));
    return sections.map(function (section) {
      var eyebrow = cleanText(section.querySelector('.section-eyebrow') && section.querySelector('.section-eyebrow').textContent);
      var title = cleanText(section.querySelector('.section-title') && section.querySelector('.section-title').textContent);
      var deck = cleanText(section.querySelector('.section-deck') && section.querySelector('.section-deck').textContent);
      var summary = cleanText(section.querySelector('.ai-summary-para, .insight-text, .worked-text, .callout') && section.querySelector('.ai-summary-para, .insight-text, .worked-text, .callout').textContent);
      if (!title && !eyebrow) return null;
      return {
        eyebrow: eyebrow || 'Report section',
        title: title || eyebrow,
        script: deck || summary || 'Use this section to connect the headline metric to the management action on screen.',
        bullets: [
          'Open with the headline and pause for the number on screen.',
          'Explain what changed, why it matters, and what decision it needs.',
          'Close by pointing to the action or risk the leadership team should remember.'
        ]
      };
    }).filter(Boolean);
  }

  var notes = buildSpeakerNotes();

  function renderNote() {
    if (!notes.length) {
      notesBody.innerHTML = '<p class="p57-speaker-script">No report sections were found for speaker notes.</p>';
      notesCount.textContent = '0 of 0';
      return;
    }
    if (noteIndex < 0) noteIndex = notes.length - 1;
    if (noteIndex >= notes.length) noteIndex = 0;
    var note = notes[noteIndex];
    notesBody.innerHTML =
      '<p class="p57-speaker-kicker">' + escapeHtml(note.eyebrow) + '</p>' +
      '<h2 class="p57-speaker-h">' + escapeHtml(note.title) + '</h2>' +
      '<p class="p57-speaker-script">' + escapeHtml(note.script) + '</p>' +
      '<ol class="p57-speaker-list">' + note.bullets.map(function (bullet) {
        return '<li>' + escapeHtml(bullet) + '</li>';
      }).join('') + '</ol>';
    notesCount.textContent = (noteIndex + 1) + ' of ' + notes.length;
  }

  function openNotesPanel() {
    renderNote();
    notesPanel.classList.add('is-open');
    notesToggle.setAttribute('aria-expanded', 'true');
  }

  function closeNotesPanel() {
    notesPanel.classList.remove('is-open');
    notesToggle.setAttribute('aria-expanded', 'false');
  }

  function unlockNotes() {
    try {
      if (window.sessionStorage && sessionStorage.getItem('p57-speaker-notes-unlocked') === 'true') return true;
    } catch (error) {}
    var code = window.prompt('Enter speaker notes code');
    if (code === '9818') {
      try {
        if (window.sessionStorage) sessionStorage.setItem('p57-speaker-notes-unlocked', 'true');
      } catch (error) {}
      return true;
    }
    if (code !== null) window.alert('Incorrect code');
    return false;
  }

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

  notesToggle.addEventListener('click', function () {
    if (!unlockNotes()) return;
    if (notesPanel.classList.contains('is-open')) closeNotesPanel();
    else openNotesPanel();
  });

  board.querySelector('.p57-speaker-close').addEventListener('click', closeNotesPanel);
  board.querySelector('[data-p57-note-prev]').addEventListener('click', function () {
    noteIndex -= 1;
    renderNote();
  });
  board.querySelector('[data-p57-note-next]').addEventListener('click', function () {
    noteIndex += 1;
    renderNote();
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
