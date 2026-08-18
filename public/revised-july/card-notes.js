(function () {
  if (window.__p57CardNotesLoaded) return;
  window.__p57CardNotesLoaded = true;

  var CARD_SELECTOR = '.kpi-card, .insight-card, .worked-card, .ai-bullet-item';
  var STORE_PREFIX = 'p57-card-notes-v1:' + window.location.pathname + ':';

  function safeGet(key) {
    try { return window.localStorage && localStorage.getItem(key); } catch (error) { return null; }
  }
  function safeSet(key, value) {
    try { if (window.localStorage) localStorage.setItem(key, value); } catch (error) {}
  }
  function safeRemove(key) {
    try { if (window.localStorage) localStorage.removeItem(key); } catch (error) {}
  }

  function escapeHtml(text) {
    return String(text || '').replace(/[&<>"']/g, function (char) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char];
    });
  }

  function cardLabel(card) {
    var heading = card.querySelector('.kpi-back-title, .insight-title, .worked-title, .ai-bullet-title, h3, h4');
    var text = heading ? heading.textContent : card.textContent;
    return String(text || '').replace(/\s+/g, ' ').trim().slice(0, 60) || 'This card';
  }

  function cardType(card) {
    if (card.classList.contains('kpi-card')) return 'kpi';
    if (card.classList.contains('insight-card')) return 'insight';
    if (card.classList.contains('worked-card')) return 'worked';
    return 'bullet';
  }

  function buildCardIds() {
    var counters = {};
    var cards = Array.prototype.slice.call(document.querySelectorAll(CARD_SELECTOR));
    return cards.map(function (card) {
      var section = card.closest('section.report-section');
      var sectionId = (section && section.id) || 'global';
      var type = cardType(card);
      var key = sectionId + '::' + type;
      counters[key] = (counters[key] || 0) + 1;
      var id = key + '::' + (counters[key] - 1);
      return { card: card, id: id };
    });
  }

  function storageKey(id) {
    return STORE_PREFIX + id;
  }

  function readNote(id) {
    var raw = safeGet(storageKey(id));
    if (!raw) return null;
    try { return JSON.parse(raw); } catch (error) { return null; }
  }

  function splitToBullets(text) {
    var lines = String(text || '')
      .split(/\r?\n/)
      .map(function (line) { return line.replace(/^[\s•\-*]+/, '').trim(); })
      .filter(Boolean);
    if (lines.length <= 1) {
      var sentenceSource = String(text || '').trim();
      var sentences = sentenceSource.match(/[^.!?\n]+[.!?]*(?:\n|$)/g);
      if (sentences && sentences.length > 1) {
        lines = sentences.map(function (s) { return s.trim(); }).filter(Boolean);
      } else if (sentenceSource) {
        lines = [sentenceSource];
      }
    }
    return lines;
  }

  function bulletsHtml(lines) {
    if (!lines.length) return '<p class="p57-cardnote-empty">No notes yet for this card.</p>';
    return '<ul class="p57-cardnote-list">' + lines.map(function (line) {
      return '<li>' + escapeHtml(line) + '</li>';
    }).join('') + '</ul>';
  }

  var style = document.createElement('style');
  style.textContent = [
    '.p57-cardnote-btn{all:initial;box-sizing:border-box;position:absolute;z-index:6;top:8px;right:8px;display:flex;align-items:center;justify-content:center;width:22px;height:22px;border:1px solid color-mix(in srgb, var(--primary) 32%, var(--border));border-radius:50%;background:var(--bg-card);color:var(--primary);font:700 12px/1 Georgia,"Times New Roman",serif;font-style:italic;cursor:pointer;box-shadow:0 4px 10px rgba(0,0,0,.1);transition:transform .15s ease,background .15s ease;}',
    '.p57-cardnote-btn:hover{transform:scale(1.12);background:color-mix(in srgb, var(--primary) 12%, var(--bg-card));}',
    '.p57-cardnote-btn.has-note{background:var(--primary);color:#fff;border-color:var(--primary);}',
    '.p57-cardnote-btn.has-note::after{content:"";position:absolute;top:-2px;right:-2px;width:7px;height:7px;border-radius:50%;background:var(--good, #18835a);border:1.5px solid var(--bg-card);}',
    '.kpi-card,.insight-card,.worked-card,.ai-bullet-item{position:relative;}',
    '.p57-cardnote-overlay{position:fixed;inset:0;z-index:2147483200;display:none;align-items:center;justify-content:center;background:rgba(10,12,18,.42);backdrop-filter:blur(3px);-webkit-backdrop-filter:blur(3px);}',
    '.p57-cardnote-overlay.is-open{display:flex;}',
    '.p57-cardnote-modal{display:flex;flex-direction:column;width:min(480px,calc(100vw - 32px));max-height:min(620px,calc(100vh - 40px));border:1px solid var(--border);border-radius:16px;background:var(--bg-card);color:var(--text);box-shadow:0 30px 80px rgba(0,0,0,.28);overflow:hidden;font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;}',
    '.p57-cardnote-head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px;padding:16px 18px;border-bottom:1px solid var(--border);background:color-mix(in srgb, var(--primary) 7%, var(--bg-card));}',
    '.p57-cardnote-kicker{margin:0 0 3px;color:var(--primary);font:700 10px/1.3 sans-serif;text-transform:uppercase;letter-spacing:.08em;}',
    '.p57-cardnote-title{margin:0;color:var(--text);font:700 15px/1.35 sans-serif;}',
    '.p57-cardnote-close{flex-shrink:0;appearance:none;display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;border:1px solid var(--border);border-radius:999px;background:var(--bg-card);color:var(--text);font:16px/1 sans-serif;cursor:pointer;}',
    '.p57-cardnote-body{display:flex;flex-direction:column;gap:12px;padding:16px 18px;overflow:auto;}',
    '.p57-cardnote-label{margin:0;color:var(--text-muted);font:600 10.5px/1.3 sans-serif;text-transform:uppercase;letter-spacing:.07em;}',
    '.p57-cardnote-input{width:100%;min-height:96px;margin:0;padding:11px 12px;border:1px solid var(--border);border-radius:10px;background:var(--bg-inset);color:var(--text);font:400 13.5px/1.55 sans-serif;resize:vertical;outline:none;}',
    '.p57-cardnote-input:focus{border-color:var(--primary);box-shadow:0 0 0 3px color-mix(in srgb, var(--primary) 14%, transparent);}',
    '.p57-cardnote-preview{padding:12px 13px;border:1px solid var(--border);border-radius:10px;background:var(--bg-card);min-height:40px;}',
    '.p57-cardnote-list{margin:0;padding:0 0 0 18px;display:flex;flex-direction:column;gap:6px;}',
    '.p57-cardnote-list li{font-size:13px;line-height:1.55;color:var(--text);}',
    '.p57-cardnote-empty{margin:0;color:var(--text-subtle);font-size:12.5px;font-style:italic;}',
    '.p57-cardnote-actions{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:12px 18px;border-top:1px solid var(--border);background:color-mix(in srgb, var(--primary) 4%, var(--bg-card));}',
    '.p57-cardnote-hint{font-size:11px;color:var(--text-subtle);}',
    '.p57-cardnote-btngroup{display:flex;gap:8px;}',
    '.p57-cardnote-reset,.p57-cardnote-save{appearance:none;display:inline-flex;align-items:center;justify-content:center;min-height:32px;padding:7px 14px;border-radius:999px;font:600 12px/1 sans-serif;cursor:pointer;}',
    '.p57-cardnote-reset{border:1px solid var(--border);background:var(--bg-card);color:var(--text);}',
    '.p57-cardnote-save{border:1px solid var(--primary);background:var(--primary);color:#fff;}'
  ].join('');
  document.head.appendChild(style);

  var overlay = document.createElement('div');
  overlay.className = 'p57-cardnote-overlay';
  overlay.innerHTML =
    '<div class="p57-cardnote-modal" role="dialog" aria-label="Card notes">' +
      '<div class="p57-cardnote-head">' +
        '<div><p class="p57-cardnote-kicker">Card Notes</p><h2 class="p57-cardnote-title"></h2></div>' +
        '<button class="p57-cardnote-close" type="button" aria-label="Close">×</button>' +
      '</div>' +
      '<div class="p57-cardnote-body">' +
        '<div><p class="p57-cardnote-label">Add notes (one point per line)</p>' +
        '<textarea class="p57-cardnote-input" spellcheck="true" placeholder="Type a note per line — it will be saved as a bulleted list."></textarea></div>' +
        '<div><p class="p57-cardnote-label">Formatted preview</p><div class="p57-cardnote-preview"></div></div>' +
      '</div>' +
      '<div class="p57-cardnote-actions">' +
        '<span class="p57-cardnote-hint"></span>' +
        '<div class="p57-cardnote-btngroup">' +
          '<button class="p57-cardnote-reset" type="button">Clear</button>' +
          '<button class="p57-cardnote-save" type="button">Save</button>' +
        '</div>' +
      '</div>' +
    '</div>';
  document.body.appendChild(overlay);

  var modalTitle = overlay.querySelector('.p57-cardnote-title');
  var textarea = overlay.querySelector('.p57-cardnote-input');
  var preview = overlay.querySelector('.p57-cardnote-preview');
  var hint = overlay.querySelector('.p57-cardnote-hint');
  var closeBtn = overlay.querySelector('.p57-cardnote-close');
  var saveBtn = overlay.querySelector('.p57-cardnote-save');
  var resetBtn = overlay.querySelector('.p57-cardnote-reset');
  var activeId = null;
  var activeButton = null;

  function updatePreview() {
    preview.innerHTML = bulletsHtml(splitToBullets(textarea.value));
  }

  function openModal(id, label, button) {
    activeId = id;
    activeButton = button;
    modalTitle.textContent = label;
    var note = readNote(id);
    textarea.value = note ? note.raw : '';
    updatePreview();
    hint.textContent = note && note.savedAt ? 'Saved ' + new Date(note.savedAt).toLocaleString() : 'Not saved yet';
    overlay.classList.add('is-open');
    textarea.focus();
  }

  function closeModal() {
    overlay.classList.remove('is-open');
    activeId = null;
    activeButton = null;
  }

  textarea.addEventListener('input', updatePreview);

  closeBtn.addEventListener('click', closeModal);
  overlay.addEventListener('click', function (event) {
    if (event.target === overlay) closeModal();
  });
  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape' && overlay.classList.contains('is-open')) closeModal();
  });

  saveBtn.addEventListener('click', function () {
    if (!activeId) return;
    var raw = textarea.value;
    var lines = splitToBullets(raw);
    if (!lines.length) {
      safeRemove(storageKey(activeId));
      if (activeButton) activeButton.classList.remove('has-note');
      hint.textContent = 'Not saved yet';
      return;
    }
    var savedAt = Date.now && typeof Date.now === 'function' ? Date.now() : new Date().getTime();
    safeSet(storageKey(activeId), JSON.stringify({ raw: raw, lines: lines, savedAt: savedAt }));
    if (activeButton) activeButton.classList.add('has-note');
    hint.textContent = 'Saved just now';
  });

  resetBtn.addEventListener('click', function () {
    if (!activeId) return;
    textarea.value = '';
    updatePreview();
    safeRemove(storageKey(activeId));
    if (activeButton) activeButton.classList.remove('has-note');
    hint.textContent = 'Not saved yet';
  });

  buildCardIds().forEach(function (entry) {
    var card = entry.card;
    var id = entry.id;
    var button = document.createElement('button');
    button.type = 'button';
    button.className = 'p57-cardnote-btn';
    button.setAttribute('aria-label', 'Add or view notes for this card');
    button.textContent = 'i';
    if (readNote(id)) button.classList.add('has-note');
    button.addEventListener('click', function (event) {
      event.preventDefault();
      event.stopPropagation();
      openModal(id, cardLabel(card), button);
    });
    button.addEventListener('pointerdown', function (event) { event.stopPropagation(); });
    card.appendChild(button);
  });
})();
