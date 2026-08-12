(function () {
  if (window.__p57SfxSoundboardLoaded) return;
  window.__p57SfxSoundboardLoaded = true;

  var sounds = [
    ['Wide Putin Meme', '/audio/sfx/wide-putin-meme.mp3'],
    ['Haha Funny Laugh', '/audio/sfx/haha-funny-laugh.mp3'],
    ['Dun Dun Dunnnnnnnn', '/audio/sfx/dun-dun-dunnnnnnnn.mp3'],
    ['Mario Jump', '/audio/sfx/mario-jump.mp3'],
    ['Baby Laughing Meme 1', '/audio/sfx/baby-laughing-meme-1.mp3'],
    ['Applause Cheer', '/audio/sfx/applause-cheer.mp3'],
    ['Applause', '/audio/sfx/applause.mp3'],
    ['Fire In The Hole', '/audio/sfx/fire-in-the-hole.mp3'],
    ['Y2Mate Clip', '/audio/sfx/y2mate-mp3cut.mp3'],
    ['End Credits', '/audio/sfx/end-credits.mp3'],
    ['Dun Dun Dun Brass', '/audio/sfx/dun-dun-dun-brass.mp3'],
    ['Baby Laughing Meme', '/audio/sfx/baby-laughing-meme.mp3'],
    ['Faaah', '/audio/sfx/faaah.mp3'],
    ['TF Nemesis', '/audio/sfx/tf-nemesis.mp3'],
    ['Wow Reaction', '/audio/sfx/wow-reaction.mp3'],
    ['Failure Trumpet', '/audio/sfx/failure-trumpet.mp3'],
    ['Mischievous Laugh', '/audio/sfx/mischievous-laugh.mp3'],
    ['Dramatic Dun Dun Dun', '/audio/sfx/dramatic-dun-dun-dun.mp3'],
    ['Wait A Minute', '/audio/sfx/wait-a-minute.mp3'],
    ['Woooooaah', '/audio/sfx/woooooaah.mp3'],
    ["Isn't That Amazing", '/audio/sfx/isnt-that-amazing.mp3'],
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
    '.p57-sfx-toggle{appearance:none!important;display:flex!important;align-items:center!important;justify-content:center!important;width:54px!important;height:54px!important;min-width:54px!important;max-width:54px!important;min-height:54px!important;max-height:54px!important;margin:0!important;padding:0!important;border:1px solid rgba(15,44,94,.16)!important;border-radius:50%!important;background:#0f2c5e!important;color:#fff!important;box-shadow:0 14px 30px rgba(15,44,94,.28)!important;font:800 22px/1 sans-serif!important;letter-spacing:0!important;text-align:center!important;cursor:pointer!important;overflow:hidden!important;transform:none!important}',
    '.p57-sfx-menu{position:absolute!important;right:0!important;bottom:66px!important;display:none!important;width:min(320px,calc(100vw - 36px))!important;height:auto!important;max-height:min(420px,calc(100vh - 104px))!important;overflow:auto!important;margin:0!important;padding:12px!important;border:1px solid #d9e0ec!important;border-radius:8px!important;background:rgba(255,255,255,.98)!important;box-shadow:0 18px 48px rgba(15,44,94,.22)!important;color:#0b1a33!important;transform:none!important}',
    '.p57-sfx-board.is-open .p57-sfx-menu{display:block!important}',
    '.p57-sfx-menu h2{margin:0 0 10px!important;font:800 14px/1.2 sans-serif!important;color:#0b1a33!important}',
    '.p57-sfx-grid{display:grid!important;gap:8px!important}',
    '.p57-sfx-item{display:grid!important;grid-template-columns:minmax(0,1fr) auto!important;align-items:center!important;gap:8px!important;min-height:40px!important;padding:7px 8px!important;border:1px solid #d9e0ec!important;border-radius:6px!important;background:#fff!important}',
    '.p57-sfx-label{overflow:hidden!important;color:#0b1a33!important;font:700 12px/1.25 sans-serif!important;text-overflow:ellipsis!important;white-space:nowrap!important}',
    '.p57-sfx-play{appearance:none!important;min-height:28px!important;min-width:34px!important;margin:0!important;padding:5px 8px!important;border:1px solid #d9e0ec!important;border-radius:5px!important;background:#fff!important;color:#0b1a33!important;font:700 12px/1 sans-serif!important;cursor:pointer!important}',
  ].join('');

  var board = document.createElement('div');
  board.className = 'p57-sfx-board';
  board.innerHTML =
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
  var player = new Audio();

  toggle.addEventListener('click', function () {
    var isOpen = board.classList.toggle('is-open');
    toggle.setAttribute('aria-expanded', String(isOpen));
  });

  board.querySelectorAll('[data-p57-sfx]').forEach(function (button) {
    button.addEventListener('click', function () {
      player.pause();
      player.currentTime = 0;
      player.src = button.dataset.p57Sfx;
      player.play();
    });
  });

  document.addEventListener('click', function (event) {
    if (event.composedPath && event.composedPath().indexOf(host) !== -1) return;
    if (!host.contains(event.target)) {
      board.classList.remove('is-open');
      toggle.setAttribute('aria-expanded', 'false');
    }
  });
})();
