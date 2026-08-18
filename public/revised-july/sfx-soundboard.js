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
    ['Sitcom Laugh + Applause', sfxUrl('sitcom-laughing-and-applause.mp3')],
    ['Crowd Cheering Applause', sfxUrl('crowd-cheering-applause.mp3')],
    ['Applause Tony D', sfxUrl('applause-tony-d.mp3')],
    ['Ontiva RzrOcZY', sfxUrl('ontiva-rzroczy.mp3')],
    ['Funny Sad Music', sfxUrl('funny-sad-music.mp3')],
    ['Mac Quack', sfxUrl('mac-quack.mp3')],
    ['Baby Laughing Meme 2', sfxUrl('baby-laughing-meme-2.mp3')],
    ['Bulla', sfxUrl('bulla.mp3')],
    ['Indian Guy Laughing', sfxUrl('indian-guy-laughing.mp3')],
    ['Amitabh Bachchan Clip', sfxUrl('amitabh-bachchan-teri-maa-ka-vosda.mp3')],
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

  var bodyShiftStyle = document.createElement('style');
  bodyShiftStyle.textContent = 'body{transition:background-color 200ms ease,color 200ms ease,padding-right 280ms cubic-bezier(.16,1,.3,1)!important}';
  document.head.appendChild(bodyShiftStyle);

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
    '.p57-speaker-panel{position:fixed!important;top:0!important;right:0!important;bottom:0!important;left:auto!important;display:none!important;width:min(460px,100vw)!important;height:100dvh!important;min-width:320px!important;max-width:100vw!important;overflow:hidden!important;margin:0!important;border:0!important;border-left:1px solid #dce2ea!important;border-radius:0!important;background:#f5f7fa!important;backdrop-filter:none!important;-webkit-backdrop-filter:none!important;box-shadow:-20px 0 54px rgba(20,31,49,.16)!important;color:#0b1a33!important;transform:none!important}',
    '.p57-speaker-panel.is-open{display:flex!important;flex-direction:column!important}',
    '.p57-speaker-head{display:grid!important;grid-template-columns:minmax(0,1fr) auto!important;align-items:center!important;gap:12px!important;min-height:58px!important;padding:12px 16px!important;border-bottom:1px solid #dce2ea!important;background:#fff!important;user-select:none!important}',
    '.p57-speaker-title{min-width:0!important;overflow:hidden!important;text-overflow:ellipsis!important;white-space:nowrap!important;font:750 14px/1.25 sans-serif!important;color:#18243a!important;letter-spacing:-.01em!important}',
    '.p57-speaker-head-tools{display:flex!important;align-items:center!important;gap:6px!important}',
    '.p57-speaker-mode{appearance:none!important;display:inline-flex!important;align-items:center!important;justify-content:center!important;min-height:28px!important;padding:6px 9px!important;border:1px solid rgba(24,32,48,.1)!important;border-radius:999px!important;background:#fff!important;color:#647089!important;font:600 10.5px/1 sans-serif!important;cursor:pointer!important;transition:background .18s ease,color .18s ease!important}',
    '.p57-speaker-mode:hover{background:#f3f5f8!important;color:#0f2c5e!important}',
    '.p57-speaker-mode.is-active{background:#0f2c5e!important;color:#fff!important;border-color:transparent!important;box-shadow:0 4px 10px rgba(15,44,94,.22)!important}',
    '.p57-speaker-close{appearance:none!important;display:inline-flex!important;align-items:center!important;justify-content:center!important;width:26px!important;height:26px!important;border:1px solid #e1e6ef!important;border-radius:999px!important;background:#fff!important;color:#647089!important;font:400 14px/1 sans-serif!important;cursor:pointer!important}',
    '.p57-speaker-body{display:flex!important;flex-direction:column!important;gap:0!important;padding:0!important;overflow:auto!important;scrollbar-gutter:stable!important}',
    '.p57-speaker-context{position:sticky!important;top:0!important;z-index:3!important;padding:15px 18px 14px!important;border:0!important;border-bottom:1px solid #dce2ea!important;border-radius:0!important;background:rgba(245,247,250,.97)!important;backdrop-filter:blur(8px)!important}',
    '.p57-speaker-kicker{margin:0 0 4px!important;color:#647089!important;font:700 9.5px/1.35 sans-serif!important;text-transform:uppercase!important;letter-spacing:.09em!important}',
    '.p57-speaker-h{margin:0!important;color:#0b1a33!important;font:750 17px/1.32 sans-serif!important;letter-spacing:-.02em!important}',
    '.p57-speaker-script{width:100%!important;min-height:0!important;flex:1!important;margin:0!important;padding:22px 22px 48px!important;border:0!important;border-radius:0!important;background:#fff!important;color:#26344b!important;font:400 15px/1.72 sans-serif!important;outline:none!important;overflow:visible!important;white-space:normal!important;box-shadow:none!important}',
    '.p57-speaker-script:focus{border-color:rgba(15,44,94,.4)!important;box-shadow:0 0 0 3px rgba(15,44,94,.08)!important}',
    '.p57-speaker-script h3{margin:24px 0 10px!important;padding-top:18px!important;border-top:1px solid #e2e7ee!important;color:#14213a!important;font:750 16px/1.3 sans-serif!important;letter-spacing:-.01em!important}',
    '.p57-speaker-script h3:first-child{margin-top:0!important;padding-top:0!important;border-top:0!important}',
    '.p57-speaker-script h4{margin:18px 0 8px!important;color:#315f9f!important;font:800 10px/1.3 sans-serif!important;letter-spacing:.1em!important;text-transform:uppercase!important}',
    '.p57-speaker-script p{margin:0 0 16px!important;color:#26344b!important;font:400 15px/1.72 sans-serif!important}',
    '.p57-speaker-script ul,.p57-speaker-script ol{display:grid!important;gap:9px!important;margin:0 0 18px!important;padding-left:21px!important}',
    '.p57-speaker-script li{padding-left:3px!important;color:#26344b!important;font:400 14.5px/1.62 sans-serif!important}',
    '.p57-speaker-script strong{font-weight:700!important;color:#0b1a33!important}',
    '.p57-speaker-script .p57-cue{margin:0 0 10px!important;padding:6px 8px!important;border-left:3px solid rgba(15,44,94,.3)!important;border-radius:5px!important;background:rgba(15,44,94,.05)!important;color:#647089!important;font:400 11.5px/1.42 sans-serif!important;font-style:italic!important}',
    '.p57-speaker-script .p57-break{height:7px!important}',
    '.p57-speaker-actions{display:flex!important;align-items:center!important;justify-content:space-between!important;gap:10px!important;min-height:58px!important;padding:10px 14px!important;border-top:1px solid #dce2ea!important;background:#fff!important}',
    '.p57-speaker-resize{position:absolute!important;z-index:8!important;left:-5px!important;top:0!important;width:10px!important;height:100%!important;border:0!important;background:transparent!important;cursor:ew-resize!important;touch-action:none!important}',
    '.p57-speaker-resize::before{content:""!important;position:absolute!important;left:3px!important;top:50%!important;width:3px!important;height:40px!important;transform:translateY(-50%)!important;border-radius:3px!important;background:rgba(82,97,116,.22)!important;transition:background .15s ease!important}',
    '.p57-speaker-resize:hover::before,.p57-speaker-resize:focus-visible::before{background:#0f2c5e!important}',
    '.p57-speaker-action-group{display:flex!important;align-items:center!important;gap:6px!important}',
    '.p57-speaker-nav{appearance:none!important;display:inline-flex!important;align-items:center!important;justify-content:center!important;min-height:28px!important;min-width:58px!important;padding:5px 9px!important;border:1px solid #e1e6ef!important;border-radius:999px!important;background:#fff!important;color:#3c4a60!important;font:400 11.5px/1 sans-serif!important;text-align:center!important;cursor:pointer!important}',
    '.p57-speaker-count{font:400 10.5px/1 sans-serif!important;color:#8891a2!important}',
    '.p57-speaker-save{appearance:none!important;display:inline-flex!important;align-items:center!important;justify-content:center!important;min-height:28px!important;min-width:48px!important;padding:5px 9px!important;border:1px solid #0f2c5e!important;border-radius:999px!important;background:#0f2c5e!important;color:#fff!important;font:400 11.5px/1 sans-serif!important;text-align:center!important;cursor:pointer!important}',
    '.p57-speaker-reset{appearance:none!important;display:inline-flex!important;align-items:center!important;justify-content:center!important;min-height:28px!important;min-width:48px!important;padding:5px 9px!important;border:1px solid #e1e6ef!important;border-radius:999px!important;background:#fff!important;color:#3c4a60!important;font:400 11.5px/1 sans-serif!important;text-align:center!important;cursor:pointer!important}',
    '.p57-speaker-panel.is-teleprompt{width:min(340px,100vw)!important;border-color:rgba(255,255,255,.09)!important;background:rgba(17,20,29,.98)!important;box-shadow:-16px 0 34px rgba(0,0,0,.22)!important;color:#fff!important;backdrop-filter:blur(20px) saturate(1.08)!important}',
    '.p57-speaker-panel.is-teleprompt .p57-speaker-resize::before{background:rgba(255,255,255,.28)!important}',
    '.p57-speaker-panel.is-teleprompt .p57-speaker-resize:hover::before,.p57-speaker-panel.is-teleprompt .p57-speaker-resize:focus-visible::before{background:#5aa9ff!important}',
    '.p57-speaker-panel.is-teleprompt .p57-speaker-head{padding:14px 18px!important;border-color:rgba(255,255,255,.1)!important;background:rgba(18,21,32,.78)!important}',
    '.p57-speaker-panel.is-teleprompt .p57-speaker-title{color:#fff!important;font-weight:600!important}',
    '.p57-speaker-panel.is-teleprompt .p57-speaker-close{border-color:rgba(255,255,255,.14)!important;background:rgba(255,255,255,.08)!important;color:#fff!important}',
    '.p57-speaker-panel.is-teleprompt .p57-speaker-body{flex:1!important;justify-content:center!important;padding:24px 22px!important;overflow:hidden!important}',
    '.p57-teleprompter{display:flex!important;flex-direction:column!important;justify-content:center!important;gap:18px!important;width:100%!important;margin:auto!important}',
    '.p57-tele-kicker{display:flex!important;align-items:center!important;justify-content:space-between!important;gap:16px!important;margin:0!important;color:#aeb5c7!important;font:700 11px/1.3 sans-serif!important;letter-spacing:.1em!important;text-transform:uppercase!important}',
    '.p57-tele-live{display:inline-flex!important;align-items:center!important;gap:7px!important;padding:6px 10px!important;border:1px solid rgba(255,255,255,.12)!important;border-radius:999px!important;background:rgba(255,255,255,.06)!important;color:#c4cad8!important;letter-spacing:.04em!important}',
    '.p57-tele-live::before{content:""!important;width:7px!important;height:7px!important;border-radius:50%!important;background:#7d8495!important}',
    '.p57-tele-live.is-listening{color:#bcdcff!important;border-color:rgba(120,180,255,.32)!important;background:rgba(15,44,94,.32)!important}',
    '.p57-tele-live.is-listening::before{background:#5aa9ff!important;box-shadow:0 0 0 5px rgba(90,169,255,.13)!important;animation:p57TelePulse 1.4s ease infinite!important}',
    '.p57-tele-current{display:-webkit-box!important;-webkit-box-orient:vertical!important;-webkit-line-clamp:4!important;overflow:hidden!important;margin:0!important;color:#f6f7fb!important;font:500 clamp(21px,1.9vw,29px)/1.38 Georgia,"Times New Roman",serif!important;letter-spacing:-.02em!important;text-wrap:balance!important}',
    '.p57-tele-current .p57-word{color:#747b8c!important;transition:color .16s ease,text-shadow .16s ease!important}',
    '.p57-tele-current .p57-word.is-spoken{color:#8fd0ff!important;text-shadow:0 0 20px rgba(143,208,255,.2)!important}',
    '.p57-tele-current .p57-word.is-active{color:#fff!important}',
    '.p57-tele-next{display:-webkit-box!important;-webkit-box-orient:vertical!important;-webkit-line-clamp:2!important;overflow:hidden!important;margin:0!important;padding-top:16px!important;border-top:1px solid rgba(255,255,255,.09)!important;color:#7f8798!important;font:400 17px/1.45 Georgia,"Times New Roman",serif!important;letter-spacing:-.01em!important}',
    '.p57-tele-controls{display:flex!important;align-items:center!important;justify-content:space-between!important;gap:14px!important;padding:14px 18px!important;border-top:1px solid rgba(255,255,255,.1)!important;background:rgba(18,21,32,.82)!important}',
    '.p57-tele-control-group{display:flex!important;align-items:center!important;gap:8px!important}',
    '.p57-tele-btn{appearance:none!important;min-height:42px!important;padding:9px 15px!important;border:1px solid rgba(255,255,255,.14)!important;border-radius:999px!important;background:rgba(255,255,255,.07)!important;color:#fff!important;font:600 12px/1 sans-serif!important;cursor:pointer!important}',
    '.p57-tele-btn:hover{background:rgba(255,255,255,.14)!important}',
    '.p57-tele-btn.is-primary{border-color:transparent!important;background:#1f4f8f!important;box-shadow:0 6px 18px rgba(31,79,143,.32)!important}',
    '.p57-tele-progress{min-width:100px!important;color:#aeb5c7!important;font:500 12px/1 sans-serif!important;text-align:center!important}',
    '@keyframes p57TelePulse{50%{opacity:.45;transform:scale(.82)}}',
    '@media(max-width:720px){.p57-speaker-resize{display:none!important}.p57-speaker-panel{width:100vw!important;min-width:0!important}.p57-speaker-panel.is-teleprompt{width:100vw!important}.p57-speaker-panel.is-teleprompt .p57-speaker-body{padding:20px 18px!important}.p57-tele-current{font-size:clamp(22px,6.8vw,32px)!important;-webkit-line-clamp:3!important}.p57-tele-next{font-size:16px!important;-webkit-line-clamp:1!important}.p57-tele-controls{flex-wrap:wrap!important}.p57-tele-control-group{flex:1!important}.p57-tele-btn{flex:1!important;padding-inline:10px!important}.p57-tele-progress{order:-1!important;width:100%!important}}',
    '@media(prefers-reduced-motion:reduce){.p57-tele-live.is-listening::before{animation:none!important}.p57-tele-current .p57-word{transition:none!important}}',
    '.p57-sfx-menu{position:absolute!important;right:0!important;bottom:66px!important;display:none!important;width:min(340px,calc(100vw - 36px))!important;height:auto!important;max-height:min(500px,calc(100vh - 104px))!important;overflow:auto!important;margin:0!important;padding:12px!important;border:1px solid #d9e0ec!important;border-radius:8px!important;background:rgba(255,255,255,.98)!important;box-shadow:0 18px 48px rgba(15,44,94,.22)!important;color:#0b1a33!important;transform:none!important}',
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
      '<button class="p57-speaker-resize" type="button" aria-label="Resize speaker notes panel width" title="Drag left/right to resize, or use arrow keys"></button>' +
      '<div class="p57-speaker-head"><div class="p57-speaker-title">Speaker Notes</div><div class="p57-speaker-head-tools"><button class="p57-speaker-mode" type="button" aria-pressed="false">Teleprompter</button><button class="p57-speaker-close" type="button" aria-label="Close speaker notes">×</button></div></div>' +
      '<div class="p57-speaker-body"></div>' +
      '<div class="p57-speaker-actions"><div class="p57-speaker-action-group"><button class="p57-speaker-nav" type="button" data-p57-note-prev>Previous</button><button class="p57-speaker-nav" type="button" data-p57-note-next>Next</button></div><span class="p57-speaker-count"></span><div class="p57-speaker-action-group"><button class="p57-speaker-reset" type="button" data-p57-note-reset>Reset</button><button class="p57-speaker-save" type="button" data-p57-note-save>Save</button></div></div>' +
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
  var notesHead = board.querySelector('.p57-speaker-head');
  var notesResize = board.querySelector('.p57-speaker-resize');
  var notesBody = board.querySelector('.p57-speaker-body');
  var notesCount = board.querySelector('.p57-speaker-count');
  var notesModeButton = board.querySelector('.p57-speaker-mode');
  var notesActions = board.querySelector('.p57-speaker-actions');
  var noteIndex = 0;
  var activeTextarea = null;
  var resizeState = null;
  var externalNotesLoaded = false;
  var externalNotesPromise = null;
  var player = new Audio();
  var activeController = null;
  var teleprompterMode = false;
  var teleprompterIndex = 0;
  var teleprompterStatements = [];
  var speechRecognition = null;
  var speechListening = false;
  var speechTranscript = '';
  var speechResultOffset = 0;
  var lastSpeechResultCount = 0;
  var teleprompterAdvanceTimer = null;

  function cleanText(text) {
    return String(text || '').replace(/\s+/g, ' ').trim();
  }

  function escapeHtml(text) {
    return cleanText(text).replace(/[&<>"']/g, function (char) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char];
    });
  }

  function escapeRawHtml(text) {
    return String(text || '').replace(/[&<>"']/g, function (char) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char];
    });
  }

  function storageKey(suffix) {
    return 'p57-speaker-notes-v5:' + window.location.pathname + ':' + suffix;
  }

  function safeGet(key) {
    try { return window.localStorage && localStorage.getItem(key); } catch (error) { return null; }
  }

  function safeSet(key, value) {
    try { if (window.localStorage) localStorage.setItem(key, value); } catch (error) {}
  }

  function safeRemove(key) {
    try { if (window.localStorage) localStorage.removeItem(key); } catch (error) {}
  }

  function sectionKind(eyebrow, title) {
    var text = (eyebrow + ' ' + title).toLowerCase();
    if (text.indexOf('executive') !== -1) return 'executive';
    if (text.indexOf('revenue') !== -1 || text.indexOf('commercial') !== -1) return 'revenue';
    if (text.indexOf('funnel') !== -1 || text.indexOf('acquisition') !== -1 || text.indexOf('trial') !== -1) return 'funnel';
    if (text.indexOf('delivery') !== -1 || text.indexOf('format') !== -1 || text.indexOf('instructor') !== -1 || text.indexOf('session') !== -1) return 'delivery';
    if (text.indexOf('retention') !== -1 || text.indexOf('churn') !== -1 || text.indexOf('lapsed') !== -1) return 'retention';
    if (text.indexOf('recommend') !== -1 || text.indexOf('decision') !== -1) return 'recommendations';
    if (text.indexOf('outlook') !== -1 || text.indexOf('forecast') !== -1 || text.indexOf('scenario') !== -1) return 'outlook';
    if (text.indexOf('appendix') !== -1 || text.indexOf('methodology') !== -1) return 'appendix';
    return 'general';
  }

  function reportName() {
    var title = cleanText(document.querySelector('.footer-brand-text') && document.querySelector('.footer-brand-text').textContent);
    if (title) return title.replace(' · Studio Pulse', '').replace(' · Bandra Pulse', '');
    return /supreme|bandra/i.test(window.location.pathname + ' ' + document.title) ? 'Bandra' : 'Kemps';
  }

  function reportScriptUrl() {
    var path = window.location.pathname.toLowerCase();
    var footer = cleanText(document.querySelector('.footer-brand-text') && document.querySelector('.footer-brand-text').textContent).toLowerCase();
    var title = cleanText(document.title).toLowerCase();
    var identity = [path, footer, title].join(' ');
    var fileName = /\/july-report\/supreme\b|supreme-hq-bandra|bandra pulse|supreme hq/i.test(identity)
      ? 'speaker-notes-bandra.md'
      : 'speaker-notes-kwality.md';
    return new URL('/revised-july/' + fileName, window.location.origin).href;
  }

  function normalizeMarkdown(text) {
    return String(text || '')
      .replace(/\r\n/g, '\n')
      .replace(/^\s*---+\s*$/gm, '')
      .replace(/[ \t]+\n/g, '\n')
      .replace(/\n{3,}/g, '\n\n')
      .trim();
  }

  function markdownInline(text) {
    return escapeRawHtml(text).replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  }

  function markdownToHtml(markdown) {
    var lines = normalizeMarkdown(markdown).split('\n');
    return lines.map(function (line) {
      var cleaned = line.trim();
      if (!cleaned) return '<div class="p57-break"></div>';
      if (/^#\s+/.test(cleaned)) return '<h3>' + markdownInline(cleaned.replace(/^#\s+/, '')) + '</h3>';
      if (/^##+\s+/.test(cleaned)) return '<h4>' + markdownInline(cleaned.replace(/^##+\s+/, '')) + '</h4>';
      if (/^\[[^\]]+\]$/.test(cleaned)) return '<div class="p57-cue">' + markdownInline(cleaned) + '</div>';
      return '<p>' + markdownInline(cleaned) + '</p>';
    }).join('');
  }

  function headingChunk(markdown, headingPattern, nextPattern) {
    var start = markdown.search(headingPattern);
    if (start === -1) return '';
    var rest = markdown.slice(start);
    var next = rest.search(nextPattern || /^#\s+/m);
    return normalizeMarkdown(next === -1 ? rest : rest.slice(0, next));
  }

  function scriptSectionMap(markdown) {
    var opening = headingChunk(markdown, /^###\s+OPENING\s*$/mi, /^#\s+01\s+/m);
    var map = {
      'executive-summary': [opening, headingChunk(markdown, /^#\s+01\b.*$/mi, /^#\s+02\b/m)].filter(Boolean).join('\n\n'),
      'revenue-performance': headingChunk(markdown, /^#\s+02\b.*$/mi, /^#\s+03\b/m),
      'conversion-funnel': headingChunk(markdown, /^#\s+03\b.*$/mi, /^#\s+04\b/m),
      sessions: headingChunk(markdown, /^#\s+04\b.*$/mi, /^#\s+05\b/m),
      lapsed: headingChunk(markdown, /^#\s+05\b.*$/mi, /^#\s+06\b/m),
      recommendations: headingChunk(markdown, /^#\s+06\b.*$/mi, /^#\s+07\b/m),
      predictions: [headingChunk(markdown, /^#\s+07\b.*$/mi, /^#\s+CLOSING\s*$/mi), headingChunk(markdown, /^#\s+CLOSING\s*$/mi, /^#\s+THIS_HEADING_WILL_NOT_EXIST\s*$/m)].filter(Boolean).join('\n\n')
    };
    return map;
  }

  function loadExternalNotes() {
    if (externalNotesLoaded) return Promise.resolve();
    if (externalNotesPromise) return externalNotesPromise;
    externalNotesPromise = fetch(reportScriptUrl(), { cache: 'no-cache' })
      .then(function (response) {
        if (!response.ok) throw new Error('Speaker notes not found');
        return response.text();
      })
      .then(function (markdown) {
        var bySection = scriptSectionMap(markdown);
        notes.forEach(function (note) {
          if (bySection[note.id]) note.defaultScript = bySection[note.id];
        });
        externalNotesLoaded = true;
      })
      .catch(function () {
        externalNotesLoaded = true;
      });
    return externalNotesPromise;
  }

  function extractSignal(section) {
    var candidates = [
      '.worked-text',
      '.insight-text',
      '.ai-summary-para',
      '.callout',
      '.subsection-deck',
      '.kpi-back-copy'
    ];
    for (var i = 0; i < candidates.length; i++) {
      var node = section.querySelector(candidates[i]);
      var text = cleanText(node && node.textContent);
      if (text) return text;
    }
    return '';
  }

  function trimSentence(text, fallback) {
    var cleaned = cleanText(text);
    if (!cleaned) return fallback;
    var match = cleaned.match(/^(.{80,260}?[.!?])\s/);
    return match ? match[1] : cleaned.slice(0, 260);
  }

  function makeTalkTrack(kind, eyebrow, title, signal) {
    var studio = reportName();
    var firstSignal = trimSentence(signal, 'The point of this page is not just the number itself; it is what that number asks us to do next.');
    var opener = 'Let me frame this section in plain English before we go into the details.';
    var closer = 'The question I want us to carry forward is: what decision do we make from this, and who owns the next action?';

    if (kind === 'executive') {
      opener = 'I would open this report by saying: July was not a one-dimensional month. The headline performance is strong enough to acknowledge, but the operating story underneath needs management attention.';
      closer = 'So the takeaway is balanced: we should recognize the commercial strength, but we should not leave this room without agreeing how we protect conversion, retention, and class quality next month.';
    } else if (kind === 'revenue') {
      opener = 'For the revenue section, I would not just read the sales number. I would explain where the money came from and whether that revenue is repeatable.';
      closer = 'The management question here is whether this mix is healthy enough to scale, or whether we are relying too heavily on a few products, sellers, or buying moments.';
    } else if (kind === 'funnel') {
      opener = 'Here I would slow down, because the funnel is where future revenue is either being created or quietly leaking away.';
      closer = 'The action point is simple: this is not just a marketing metric. It is a follow-up discipline, trial experience, and conversion ownership issue.';
    } else if (kind === 'delivery') {
      opener = 'In this section, I would connect the class schedule to the business result. The schedule is not just an operations grid; it is inventory.';
      closer = 'The decision we need is which formats deserve more prime inventory, which ones need repair, and which ones should stop taking up capacity.';
    } else if (kind === 'retention') {
      opener = 'I would present retention as the health check of the member base. Sales tells us who came in; retention tells us whether the experience is strong enough to keep them.';
      closer = 'The next step should be a named retention workflow, not a general reminder to follow up. The risk clients need owners, timing, and offers.';
    } else if (kind === 'recommendations') {
      opener = 'This is the point where I would shift from analysis to decisions. The report has already shown the evidence; now we need agreement on what changes.';
      closer = 'I would close this section by assigning owners and timelines. A recommendation only matters if it becomes a calendar action.';
    } else if (kind === 'outlook') {
      opener = 'For the outlook, I would make it clear that this is not a prediction to admire; it is a scenario to manage.';
      closer = 'The practical ask is to monitor the leading indicators weekly, because waiting for the month-end report means we are reacting too late.';
    } else if (kind === 'appendix') {
      opener = 'I would treat the appendix as the backup page. We do not need to present every definition unless someone challenges a number.';
      closer = 'If there is a question on methodology, this is where we anchor the answer and keep the discussion factual.';
    }

    return [
      opener,
      '',
      'What I would say verbatim:',
      '"' + title + ' is the headline, but the real message is this: ' + firstSignal + ' In practical terms, this tells us where ' + studio + ' is gaining strength, where performance is fragile, and where the team needs a sharper operating response."',
      '',
      'How to explain it to the room:',
      '1. Start with the business meaning, not the table. Say what this section tells us about revenue quality, member behavior, or operating discipline.',
      '2. Then point to one number on screen as the evidence. Do not read every metric; choose the one that best supports the message.',
      '3. Translate the metric into an action. Use language like, "This means we should..." or "This is why the owner for this needs to be..."',
      '4. Pause after the action point and invite alignment only if the decision needs leadership input.',
      '',
      closer
    ].join('\n');
  }

  function buildSpeakerNotes() {
    var sections = Array.prototype.slice.call(document.querySelectorAll('section.report-section'));
    return sections.map(function (section, index) {
      var eyebrow = cleanText(section.querySelector('.section-eyebrow') && section.querySelector('.section-eyebrow').textContent);
      var title = cleanText(section.querySelector('.section-title') && section.querySelector('.section-title').textContent);
      var kind = sectionKind(eyebrow, title);
      var signal = extractSignal(section);
      if (!title && !eyebrow) return null;
      return {
        id: section.id || 'section-' + index,
        element: section,
        eyebrow: eyebrow || 'Report section',
        title: title || eyebrow,
        defaultScript: makeTalkTrack(kind, eyebrow, title, signal)
      };
    }).filter(Boolean);
  }

  var notes = buildSpeakerNotes();

  function noteKey(note) {
    return storageKey('note:' + (note && note.id ? note.id : noteIndex));
  }

  function getNoteScript(note) {
    return safeGet(noteKey(note)) || markdownToHtml(note.defaultScript || '');
  }

  function normalizeSpeech(text) {
    return cleanText(text).toLowerCase().replace(/[^a-z0-9\s]/g, '');
  }

  function statementList(note) {
    var holder = document.createElement('div');
    holder.innerHTML = getNoteScript(note);
    var blocks = Array.prototype.slice.call(holder.querySelectorAll('p, .p57-cue'));
    var output = [];
    blocks.forEach(function (block) {
      var text = cleanText(block.textContent).replace(/^\d+\.\s*/, '');
      if (!text || /^what i would say verbatim:?$/i.test(text) || /^how to explain it to the room:?$/i.test(text)) return;
      var sentences = text.match(/[^.!?]+[.!?]+(?:[”"])?|[^.!?]+$/g) || [text];
      sentences.forEach(function (sentence) {
        var item = cleanText(sentence).replace(/^['"]|['"]$/g, '');
        if (item.length > 2) output.push(item);
      });
    });
    return output.length ? output : ['No teleprompter statements are available for this section.'];
  }

  function spokenWordCount(statement, transcript) {
    var words = normalizeSpeech(statement).split(/\s+/).filter(Boolean);
    var heard = normalizeSpeech(transcript).split(/\s+/).filter(Boolean);
    if (!words.length || !heard.length) return 0;
    var cursor = 0;
    heard.forEach(function (heardWord) {
      for (var i = cursor; i < Math.min(words.length, cursor + 5); i++) {
        if (words[i] === heardWord || (heardWord.length > 4 && words[i].indexOf(heardWord) === 0)) {
          cursor = i + 1;
          break;
        }
      }
    });
    return cursor;
  }

  function statementWordsHtml(statement, spokenCount) {
    return String(statement || '').split(/\s+/).map(function (word, index) {
      var state = index < spokenCount ? ' is-spoken' : (index === spokenCount ? ' is-active' : '');
      return '<span class="p57-word' + state + '">' + escapeRawHtml(word) + '</span>';
    }).join(' ');
  }

  function renderTeleprompter() {
    if (!notes[noteIndex]) return;
    teleprompterStatements = statementList(notes[noteIndex]);
    teleprompterIndex = Math.max(0, Math.min(teleprompterIndex, teleprompterStatements.length - 1));
    var current = teleprompterStatements[teleprompterIndex] || '';
    var next = teleprompterStatements[teleprompterIndex + 1] || 'End of this section — move to the next report section when ready.';
    var spoken = spokenWordCount(current, speechTranscript);
    notesBody.innerHTML =
      '<div class="p57-teleprompter" aria-live="polite">' +
        '<p class="p57-tele-kicker"><span>' + escapeHtml(notes[noteIndex].eyebrow) + '</span><span class="p57-tele-live' + (speechListening ? ' is-listening' : '') + '">' + (speechListening ? 'Listening live' : 'Manual mode') + '</span></p>' +
        '<p class="p57-tele-current">' + statementWordsHtml(current, spoken) + '</p>' +
        '<p class="p57-tele-next"><strong>Next</strong> · ' + escapeRawHtml(next) + '</p>' +
      '</div>';
    notesCount.textContent = (noteIndex + 1) + ' of ' + notes.length;
    var controls = notesPanel.querySelector('.p57-tele-controls');
    if (!controls) {
      controls = document.createElement('div');
      controls.className = 'p57-tele-controls';
      controls.innerHTML = '<div class="p57-tele-control-group"><button class="p57-tele-btn" type="button" data-p57-tele-prev>Previous</button><button class="p57-tele-btn is-primary" type="button" data-p57-tele-next>Next statement</button></div><span class="p57-tele-progress"></span><div class="p57-tele-control-group"><button class="p57-tele-btn" type="button" data-p57-tele-mic>Start live listening</button><button class="p57-tele-btn" type="button" data-p57-tele-exit>Exit</button></div>';
      notesPanel.appendChild(controls);
      controls.querySelector('[data-p57-tele-prev]').addEventListener('click', previousTeleprompterStatement);
      controls.querySelector('[data-p57-tele-next]').addEventListener('click', nextTeleprompterStatement);
      controls.querySelector('[data-p57-tele-mic]').addEventListener('click', toggleSpeechListening);
      controls.querySelector('[data-p57-tele-exit]').addEventListener('click', exitTeleprompter);
    }
    controls.querySelector('.p57-tele-progress').textContent = (teleprompterIndex + 1) + ' / ' + teleprompterStatements.length;
    controls.querySelector('[data-p57-tele-mic]').textContent = speechListening ? 'Stop listening' : 'Start live listening';
  }

  function nextTeleprompterStatement() {
    if (!teleprompterMode) return;
    if (teleprompterAdvanceTimer) { window.clearTimeout(teleprompterAdvanceTimer); teleprompterAdvanceTimer = null; }
    if (teleprompterIndex < teleprompterStatements.length - 1) {
      teleprompterIndex += 1;
      speechTranscript = '';
      speechResultOffset = lastSpeechResultCount;
      renderTeleprompter();
    } else if (noteIndex < notes.length - 1) {
      noteIndex += 1;
      teleprompterIndex = 0;
      speechTranscript = '';
      speechResultOffset = lastSpeechResultCount;
      renderTeleprompter();
    }
  }

  function previousTeleprompterStatement() {
    if (!teleprompterMode) return;
    if (teleprompterIndex > 0) teleprompterIndex -= 1;
    else if (noteIndex > 0) { noteIndex -= 1; teleprompterIndex = Math.max(0, statementList(notes[noteIndex]).length - 1); }
    speechTranscript = '';
    speechResultOffset = lastSpeechResultCount;
    renderTeleprompter();
  }

  function stopSpeechListening() {
    speechListening = false;
    if (speechRecognition) {
      try { speechRecognition.stop(); } catch (error) {}
    }
    speechRecognition = null;
  }

  function toggleSpeechListening() {
    if (speechListening) {
      stopSpeechListening();
      renderTeleprompter();
      return;
    }
    var Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) {
      window.alert('Live speech recognition is not supported in this browser. Use Space or the Next statement button to advance.');
      return;
    }
    speechRecognition = new Recognition();
    speechRecognition.continuous = true;
    speechRecognition.interimResults = true;
    speechRecognition.maxAlternatives = 1;
    speechRecognition.lang = 'en-IN';
    speechRecognition.onresult = function (event) {
      var finalTranscript = '';
      var interimTranscript = '';
      lastSpeechResultCount = event.results.length;
      for (var i = speechResultOffset; i < event.results.length; i++) {
        if (event.results[i].isFinal) finalTranscript += ' ' + event.results[i][0].transcript;
        else interimTranscript += ' ' + event.results[i][0].transcript;
      }
      speechTranscript = finalTranscript + ' ' + interimTranscript;
      var current = teleprompterStatements[teleprompterIndex] || '';
      var currentWords = normalizeSpeech(current).split(/\s+/).filter(Boolean);
      var spoken = spokenWordCount(current, speechTranscript);
      var currentNode = notesBody.querySelector('.p57-tele-current');
      if (currentNode) currentNode.innerHTML = statementWordsHtml(current, spoken);
      if (currentWords.length && spoken / currentWords.length >= .72 && !teleprompterAdvanceTimer) {
        teleprompterAdvanceTimer = window.setTimeout(nextTeleprompterStatement, 120);
      }
    };
    speechRecognition.onerror = function (event) {
      if (event.error !== 'no-speech') stopSpeechListening();
      if (teleprompterMode) renderTeleprompter();
    };
    speechRecognition.onend = function () {
      if (speechListening && teleprompterMode) {
        try { speechRecognition.start(); } catch (error) { stopSpeechListening(); }
      }
    };
    speechListening = true;
    speechTranscript = '';
    speechResultOffset = 0;
    lastSpeechResultCount = 0;
    try { speechRecognition.start(); } catch (error) { stopSpeechListening(); }
    renderTeleprompter();
  }

  function enterTeleprompter() {
    saveCurrentNote();
    teleprompterMode = true;
    teleprompterIndex = 0;
    speechTranscript = '';
    notesPanel.style.removeProperty('width');
    notesPanel.classList.add('is-teleprompt');
    applySavedPanelSize();
    notesModeButton.classList.add('is-active');
    notesModeButton.setAttribute('aria-pressed', 'true');
    notesModeButton.textContent = 'Notes view';
    notesActions.style.setProperty('display', 'none', 'important');
    syncBodyShift();
    renderTeleprompter();
  }

  function exitTeleprompter() {
    stopSpeechListening();
    teleprompterMode = false;
    speechTranscript = '';
    notesPanel.classList.remove('is-teleprompt');
    notesPanel.style.removeProperty('width');
    notesModeButton.classList.remove('is-active');
    notesModeButton.setAttribute('aria-pressed', 'false');
    notesModeButton.textContent = 'Teleprompter';
    notesActions.style.removeProperty('display');
    var controls = notesPanel.querySelector('.p57-tele-controls');
    if (controls) controls.remove();
    applySavedPanelSize();
    syncBodyShift();
    renderNote();
  }

  var noteDirty = false;

  function saveCurrentNote(force) {
    if (!activeTextarea || !notes[noteIndex]) return;
    if (!force && !noteDirty) return;
    safeSet(noteKey(notes[noteIndex]), activeTextarea.innerHTML);
    noteDirty = false;
    notesCount.textContent = (noteIndex + 1) + ' of ' + notes.length + ' · saved';
  }

  function renderNote() {
    if (teleprompterMode) { renderTeleprompter(); return; }
    if (!notes.length) {
      notesBody.innerHTML = '<p class="p57-speaker-script">No report sections were found for speaker notes.</p>';
      notesCount.textContent = '0 of 0';
      return;
    }
    if (noteIndex < 0) noteIndex = notes.length - 1;
    if (noteIndex >= notes.length) noteIndex = 0;
    var note = notes[noteIndex];
    notesBody.innerHTML =
      '<div class="p57-speaker-context"><p class="p57-speaker-kicker">' + escapeHtml(note.eyebrow) + '</p>' +
      '<h2 class="p57-speaker-h">' + escapeHtml(note.title) + '</h2></div>' +
      '<div class="p57-speaker-script" contenteditable="true" spellcheck="true" aria-label="Editable speaker notes">' + getNoteScript(note) + '</div>';
    activeTextarea = notesBody.querySelector('.p57-speaker-script');
    noteDirty = false;
    activeTextarea.addEventListener('input', function () {
      noteDirty = true;
      notesCount.textContent = (noteIndex + 1) + ' of ' + notes.length + ' · unsaved';
    });
    notesCount.textContent = (noteIndex + 1) + ' of ' + notes.length;
  }

  function openNotesPanel() {
    applySavedPanelSize();
    noteIndex = visibleNoteIndex();
    renderNote();
    notesPanel.classList.add('is-open');
    notesToggle.setAttribute('aria-expanded', 'true');
    syncBodyShift();
    if (!externalNotesLoaded) {
      notesCount.textContent = (noteIndex + 1) + ' of ' + notes.length + ' · loading script';
      loadExternalNotes().then(function () {
        if (notesPanel.classList.contains('is-open')) renderNote();
      });
    }
  }

  function closeNotesPanel() {
    if (teleprompterMode) exitTeleprompter();
    saveCurrentNote();
    notesPanel.classList.remove('is-open');
    notesToggle.setAttribute('aria-expanded', 'false');
    syncBodyShift();
  }

  function switchNote(targetIndex) {
    if (!notes.length || targetIndex === noteIndex) return;
    saveCurrentNote();
    noteIndex = targetIndex;
    renderNote();
  }

  function visibleNoteIndex() {
    var viewportLine = window.innerHeight * 0.42;
    var bestIndex = noteIndex;
    var bestDistance = Infinity;
    notes.forEach(function (note, index) {
      if (!note.element) return;
      var rect = note.element.getBoundingClientRect();
      if (rect.bottom < 0 || rect.top > window.innerHeight) return;
      var distance = Math.abs(rect.top - viewportLine);
      if (rect.top <= viewportLine && rect.bottom >= viewportLine) distance = 0;
      if (distance < bestDistance) {
        bestDistance = distance;
        bestIndex = index;
      }
    });
    return bestIndex;
  }

  function syncNoteToViewport() {
    if (!notesPanel.classList.contains('is-open')) return;
    var nextIndex = visibleNoteIndex();
    if (nextIndex === noteIndex) return;
    if (teleprompterMode) {
      if (speechListening) return;
      noteIndex = nextIndex;
      teleprompterIndex = 0;
      speechTranscript = '';
      speechResultOffset = lastSpeechResultCount;
      renderTeleprompter();
    } else {
      switchNote(nextIndex);
    }
  }

  function sizeStorageKey() {
    return storageKey(teleprompterMode ? 'panel-width-teleprompter' : 'panel-width-notes');
  }

  function constrainPanelWidth(width) {
    return Math.max(300, Math.min(width, window.innerWidth - 24));
  }

  function applyPanelWidth(width) {
    var constrained = constrainPanelWidth(width);
    notesPanel.style.setProperty('width', constrained + 'px', 'important');
    syncBodyShift();
    return constrained;
  }

  function applySavedPanelSize() {
    var raw = safeGet(sizeStorageKey());
    if (!raw || window.innerWidth <= 720) return;
    try {
      var parsed = JSON.parse(raw);
      if (Number(parsed.width)) applyPanelWidth(Number(parsed.width));
    } catch (error) {}
  }

  function contentRightEdge() {
    var maxRight = 0;
    document.querySelectorAll('.container, .hero-content').forEach(function (el) {
      var rect = el.getBoundingClientRect();
      if (rect.right > maxRight) maxRight = rect.right;
    });
    return maxRight;
  }

  function syncBodyShift() {
    var body = document.body;
    if (!(notesPanel.classList.contains('is-open') && window.innerWidth > 720)) {
      body.style.removeProperty('padding-right');
      return;
    }
    var panelWidth = notesPanel.getBoundingClientRect().width;
    var buffer = 20;
    var prevPadding = body.style.getPropertyValue('padding-right');
    body.style.setProperty('transition', 'none', 'important');

    var padding = panelWidth;
    for (var i = 0; i < 5; i++) {
      body.style.setProperty('padding-right', padding + 'px', 'important');
      void body.offsetHeight;
      var panelLeft = window.innerWidth - panelWidth;
      var gap = panelLeft - contentRightEdge();
      if (gap >= 0 && gap <= buffer) break;
      padding = Math.max(0, Math.min(panelWidth, Math.round(padding - (gap - buffer))));
    }
    var finalWidth = padding;

    if (prevPadding) body.style.setProperty('padding-right', prevPadding);
    else body.style.removeProperty('padding-right');
    void body.offsetHeight;
    body.style.removeProperty('transition');
    body.style.setProperty('padding-right', finalWidth + 'px', 'important');
  }

  var noteScrollTicking = false;
  window.addEventListener('scroll', function () {
    if (noteScrollTicking) return;
    noteScrollTicking = true;
    window.requestAnimationFrame(function () {
      syncNoteToViewport();
      noteScrollTicking = false;
    });
  }, { passive: true });

  window.addEventListener('resize', function () {
    if (window.innerWidth <= 720) {
      notesPanel.style.removeProperty('width');
    } else {
      applySavedPanelSize();
    }
    syncBodyShift();
    syncNoteToViewport();
  });

  window.addEventListener('beforeunload', function () { saveCurrentNote(); });

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
  notesModeButton.addEventListener('click', function () {
    if (teleprompterMode) exitTeleprompter();
    else enterTeleprompter();
  });
  board.querySelector('[data-p57-note-prev]').addEventListener('click', function () {
    switchNote(noteIndex - 1);
  });
  board.querySelector('[data-p57-note-next]').addEventListener('click', function () {
    switchNote(noteIndex + 1);
  });
  board.querySelector('[data-p57-note-save]').addEventListener('click', function () { saveCurrentNote(true); });
  board.querySelector('[data-p57-note-reset]').addEventListener('click', function () {
    if (!notes[noteIndex]) return;
    safeRemove(noteKey(notes[noteIndex]));
    renderNote();
    notesCount.textContent = (noteIndex + 1) + ' of ' + notes.length + ' · reset';
  });

  notesResize.addEventListener('pointerdown', function (event) {
    if (window.innerWidth <= 720) return;
    event.preventDefault();
    event.stopPropagation();
    var rect = notesPanel.getBoundingClientRect();
    resizeState = {
      pointerId: event.pointerId,
      startX: event.clientX,
      width: rect.width
    };
    notesResize.setPointerCapture(event.pointerId);
  });

  notesResize.addEventListener('pointermove', function (event) {
    if (!resizeState || resizeState.pointerId !== event.pointerId) return;
    applyPanelWidth(resizeState.width + (resizeState.startX - event.clientX));
  });

  notesResize.addEventListener('pointerup', function (event) {
    if (!resizeState || resizeState.pointerId !== event.pointerId) return;
    var rect = notesPanel.getBoundingClientRect();
    safeSet(sizeStorageKey(), JSON.stringify({ width: Math.round(rect.width) }));
    resizeState = null;
    notesResize.releasePointerCapture(event.pointerId);
  });

  notesResize.addEventListener('pointercancel', function () { resizeState = null; });
  notesResize.addEventListener('keydown', function (event) {
    if (window.innerWidth <= 720 || (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight')) return;
    event.preventDefault();
    var rect = notesPanel.getBoundingClientRect();
    var step = event.shiftKey ? 32 : 12;
    var width = rect.width + (event.key === 'ArrowLeft' ? step : -step);
    var constrained = applyPanelWidth(width);
    safeSet(sizeStorageKey(), JSON.stringify({ width: constrained }));
  });

  document.addEventListener('keydown', function (event) {
    if (!teleprompterMode || !notesPanel.classList.contains('is-open')) return;
    if (event.key === ' ' || event.key === 'ArrowRight' || event.key === 'ArrowDown') {
      event.preventDefault();
      nextTeleprompterStatement();
    } else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') {
      event.preventDefault();
      previousTeleprompterStatement();
    } else if (event.key === 'Escape') {
      event.preventDefault();
      exitTeleprompter();
    }
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
