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
    '.p57-speaker-panel{position:absolute!important;right:58px!important;bottom:0!important;display:none!important;width:min(390px,calc(100vw - 92px))!important;max-height:min(560px,calc(100vh - 36px))!important;overflow:hidden!important;margin:0!important;border:1px solid rgba(217,224,236,.76)!important;border-radius:8px!important;background:rgba(255,255,255,.78)!important;backdrop-filter:blur(18px) saturate(1.15)!important;-webkit-backdrop-filter:blur(18px) saturate(1.15)!important;box-shadow:0 18px 48px rgba(15,44,94,.24)!important;color:#0b1a33!important;transform:none!important}',
    '.p57-speaker-panel.is-open{display:flex!important;flex-direction:column!important}',
    '.p57-speaker-head{display:grid!important;grid-template-columns:minmax(0,1fr) auto!important;align-items:center!important;gap:8px!important;padding:10px 12px!important;border-bottom:1px solid rgba(217,224,236,.78)!important;background:rgba(255,255,255,.62)!important;cursor:move!important;touch-action:none!important;user-select:none!important}',
    '.p57-speaker-title{min-width:0!important;overflow:hidden!important;text-overflow:ellipsis!important;white-space:nowrap!important;font:400 13px/1.25 sans-serif!important;color:#0b1a33!important}',
    '.p57-speaker-close{appearance:none!important;display:inline-flex!important;align-items:center!important;justify-content:center!important;width:30px!important;height:30px!important;border:1px solid #d9e0ec!important;border-radius:999px!important;background:#fff!important;color:#0b1a33!important;font:400 16px/1 sans-serif!important;cursor:pointer!important}',
    '.p57-speaker-body{display:flex!important;flex-direction:column!important;gap:10px!important;padding:12px!important;overflow:auto!important}',
    '.p57-speaker-kicker{margin:0 0 8px!important;color:#526174!important;font:400 11px/1.35 sans-serif!important;text-transform:uppercase!important;letter-spacing:.08em!important}',
    '.p57-speaker-h{margin:0 0 8px!important;color:#0b1a33!important;font:400 15px/1.28 sans-serif!important}',
    '.p57-speaker-script{width:100%!important;min-height:300px!important;margin:0!important;padding:12px!important;border:1px solid rgba(217,224,236,.92)!important;border-radius:8px!important;background:rgba(255,255,255,.72)!important;color:#1d2b44!important;font:400 13px/1.48 sans-serif!important;outline:none!important;white-space:normal!important}',
    '.p57-speaker-script:focus{border-color:#0f2c5e!important;box-shadow:0 0 0 3px rgba(15,44,94,.12)!important}',
    '.p57-speaker-script h3{margin:14px 0 9px!important;color:#0b1a33!important;font:600 16px/1.22 sans-serif!important;letter-spacing:0!important}',
    '.p57-speaker-script h4{margin:12px 0 8px!important;color:#0f2c5e!important;font:600 13px/1.28 sans-serif!important;letter-spacing:.02em!important;text-transform:uppercase!important}',
    '.p57-speaker-script p{margin:0 0 10px!important;color:#1d2b44!important;font:400 13px/1.5 sans-serif!important}',
    '.p57-speaker-script strong{font-weight:700!important;color:#0b1a33!important}',
    '.p57-speaker-script .p57-cue{margin:0 0 10px!important;padding:6px 8px!important;border-left:3px solid rgba(15,44,94,.38)!important;border-radius:5px!important;background:rgba(15,44,94,.07)!important;color:#526174!important;font:400 12px/1.42 sans-serif!important;font-style:italic!important}',
    '.p57-speaker-script .p57-break{height:8px!important}',
    '.p57-speaker-meta{margin:0!important;color:#526174!important;font:400 11px/1.35 sans-serif!important}',
    '.p57-speaker-actions{display:flex!important;align-items:center!important;justify-content:space-between!important;gap:8px!important;padding:10px 12px!important;border-top:1px solid rgba(217,224,236,.78)!important;background:rgba(255,255,255,.62)!important}',
    '.p57-speaker-action-group{display:flex!important;align-items:center!important;gap:6px!important}',
    '.p57-speaker-nav{appearance:none!important;display:inline-flex!important;align-items:center!important;justify-content:center!important;min-height:30px!important;min-width:64px!important;padding:6px 10px!important;border:1px solid #d9e0ec!important;border-radius:999px!important;background:#fff!important;color:#0b1a33!important;font:400 12px/1 sans-serif!important;text-align:center!important;cursor:pointer!important}',
    '.p57-speaker-count{font:400 11px/1 sans-serif!important;color:#526174!important}',
    '.p57-speaker-save{appearance:none!important;display:inline-flex!important;align-items:center!important;justify-content:center!important;min-height:30px!important;min-width:52px!important;padding:6px 10px!important;border:1px solid #0f2c5e!important;border-radius:999px!important;background:#0f2c5e!important;color:#fff!important;font:400 12px/1 sans-serif!important;text-align:center!important;cursor:pointer!important}',
    '.p57-speaker-reset{appearance:none!important;display:inline-flex!important;align-items:center!important;justify-content:center!important;min-height:30px!important;min-width:52px!important;padding:6px 10px!important;border:1px solid #d9e0ec!important;border-radius:999px!important;background:#fff!important;color:#0b1a33!important;font:400 12px/1 sans-serif!important;text-align:center!important;cursor:pointer!important}',
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
      '<div class="p57-speaker-head"><div class="p57-speaker-title">Speaker Notes</div><button class="p57-speaker-close" type="button" aria-label="Close speaker notes">×</button></div>' +
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
  var notesBody = board.querySelector('.p57-speaker-body');
  var notesCount = board.querySelector('.p57-speaker-count');
  var noteIndex = 0;
  var activeTextarea = null;
  var dragState = null;
  var externalNotesLoaded = false;
  var externalNotesPromise = null;
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

  function escapeRawHtml(text) {
    return String(text || '').replace(/[&<>"']/g, function (char) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char];
    });
  }

  function storageKey(suffix) {
    return 'p57-speaker-notes-v3:' + window.location.pathname + ':' + suffix;
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
    var text = (window.location.pathname + ' ' + document.title + ' ' + cleanText(document.body && document.body.textContent)).toLowerCase();
    var fileName = text.indexOf('bandra') !== -1 || text.indexOf('supreme') !== -1 ? 'speaker-notes-bandra.md' : 'speaker-notes-kwality.md';
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

  function saveCurrentNote() {
    if (!activeTextarea || !notes[noteIndex]) return;
    safeSet(noteKey(notes[noteIndex]), activeTextarea.innerHTML);
    notesCount.textContent = (noteIndex + 1) + ' of ' + notes.length + ' · saved';
  }

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
      '<div class="p57-speaker-script" contenteditable="true" spellcheck="true" aria-label="Editable speaker notes">' + getNoteScript(note) + '</div>' +
      '<p class="p57-speaker-meta">Drag the header to move this panel. Save keeps edits for this report and section.</p>';
    activeTextarea = notesBody.querySelector('.p57-speaker-script');
    activeTextarea.addEventListener('input', function () {
      notesCount.textContent = (noteIndex + 1) + ' of ' + notes.length + ' · unsaved';
    });
    notesCount.textContent = (noteIndex + 1) + ' of ' + notes.length;
  }

  function openNotesPanel() {
    applySavedPanelPosition();
    noteIndex = visibleNoteIndex();
    renderNote();
    notesPanel.classList.add('is-open');
    notesToggle.setAttribute('aria-expanded', 'true');
    if (!externalNotesLoaded) {
      notesCount.textContent = (noteIndex + 1) + ' of ' + notes.length + ' · loading script';
      loadExternalNotes().then(function () {
        if (notesPanel.classList.contains('is-open')) renderNote();
      });
    }
  }

  function closeNotesPanel() {
    saveCurrentNote();
    notesPanel.classList.remove('is-open');
    notesToggle.setAttribute('aria-expanded', 'false');
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
    if (nextIndex !== noteIndex) switchNote(nextIndex);
  }

  function constrainPanel(left, top) {
    var rect = notesPanel.getBoundingClientRect();
    var width = rect.width || 390;
    var height = rect.height || 480;
    return {
      left: Math.max(12, Math.min(left, window.innerWidth - width - 12)),
      top: Math.max(12, Math.min(top, window.innerHeight - height - 12))
    };
  }

  function applySavedPanelPosition() {
    var raw = safeGet(storageKey('panel-position'));
    if (!raw) return;
    try {
      var parsed = JSON.parse(raw);
      var pos = constrainPanel(parsed.left, parsed.top);
      notesPanel.style.setProperty('position', 'fixed', 'important');
      notesPanel.style.setProperty('left', pos.left + 'px', 'important');
      notesPanel.style.setProperty('top', pos.top + 'px', 'important');
      notesPanel.style.setProperty('right', 'auto', 'important');
      notesPanel.style.setProperty('bottom', 'auto', 'important');
    } catch (error) {}
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
    applySavedPanelPosition();
    syncNoteToViewport();
  });

  window.addEventListener('beforeunload', saveCurrentNote);

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
    switchNote(noteIndex - 1);
  });
  board.querySelector('[data-p57-note-next]').addEventListener('click', function () {
    switchNote(noteIndex + 1);
  });
  board.querySelector('[data-p57-note-save]').addEventListener('click', saveCurrentNote);
  board.querySelector('[data-p57-note-reset]').addEventListener('click', function () {
    if (!notes[noteIndex]) return;
    safeRemove(noteKey(notes[noteIndex]));
    renderNote();
    notesCount.textContent = (noteIndex + 1) + ' of ' + notes.length + ' · reset';
  });

  notesHead.addEventListener('pointerdown', function (event) {
    if (event.target.closest('button')) return;
    var rect = notesPanel.getBoundingClientRect();
    dragState = {
      pointerId: event.pointerId,
      offsetX: event.clientX - rect.left,
      offsetY: event.clientY - rect.top
    };
    notesHead.setPointerCapture(event.pointerId);
  });

  notesHead.addEventListener('pointermove', function (event) {
    if (!dragState || dragState.pointerId !== event.pointerId) return;
    var pos = constrainPanel(event.clientX - dragState.offsetX, event.clientY - dragState.offsetY);
    notesPanel.style.setProperty('position', 'fixed', 'important');
    notesPanel.style.setProperty('left', pos.left + 'px', 'important');
    notesPanel.style.setProperty('top', pos.top + 'px', 'important');
    notesPanel.style.setProperty('right', 'auto', 'important');
    notesPanel.style.setProperty('bottom', 'auto', 'important');
  });

  notesHead.addEventListener('pointerup', function (event) {
    if (!dragState || dragState.pointerId !== event.pointerId) return;
    var rect = notesPanel.getBoundingClientRect();
    safeSet(storageKey('panel-position'), JSON.stringify({ left: rect.left, top: rect.top }));
    dragState = null;
    notesHead.releasePointerCapture(event.pointerId);
  });

  notesHead.addEventListener('pointercancel', function (event) {
    if (!dragState || dragState.pointerId !== event.pointerId) return;
    dragState = null;
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
