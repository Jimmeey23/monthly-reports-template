/* ─────────────────────────────────────────────────────────────────────────
   Presenter mode for a served report: hosting a live session, and annotating
   the page while people watch.

   Two things the old implementation got wrong and this one fixes:

   1. Annotations lived in viewport coordinates on a fixed canvas, so every
      scroll moved the ink away from what it was pointing at. Every mark here
      is stored in *document* coordinates and redrawn on scroll, resize and
      theme change, so a circle drawn around a number stays around that number.

   2. There was no model behind the strokes — nothing could be undone, replayed
      for someone who joined late, or exported. Annotations are now a list of
      ops, which gives undo/redo, late-joiner replay and PNG export for free.

   Requires socket.io (`io`) to be on the page; without it nothing is created.
   ───────────────────────────────────────────────────────────────────────── */
(function () {
  'use strict';
  if (typeof io === 'undefined' || window.__p57Presenter) return;

  var DEFAULTS = { color: '#f6c344', size: 4, tool: 'pen' };
  var PALETTE = [
    { color: '#f6c344', label: 'Amber' },
    { color: '#ef4d5a', label: 'Red' },
    { color: '#2f6fd0', label: 'Blue' },
    { color: '#19a974', label: 'Green' },
    { color: '#111827', label: 'Ink' }
  ];
  var TOOLS = [
    { key: 'pointer', label: 'Pointer', hint: 'Move without drawing (Esc)' },
    { key: 'pen', label: 'Pen', hint: 'Freehand (P)' },
    { key: 'marker', label: 'Marker', hint: 'Translucent highlighter (M)' },
    { key: 'arrow', label: 'Arrow', hint: 'Point at a number (A)' },
    { key: 'box', label: 'Box', hint: 'Frame a region (B)' },
    { key: 'ellipse', label: 'Circle', hint: 'Ring a value (O)' },
    { key: 'text', label: 'Note', hint: 'Type a label (T)' },
    { key: 'eraser', label: 'Eraser', hint: 'Remove marks (E)' }
  ];

  /* ─── State ─────────────────────────────────────────────────────────── */
  var state = {
    role: 'idle',           // idle | presenter | viewer
    code: null,
    name: '',
    tool: DEFAULTS.tool,
    color: DEFAULTS.color,
    size: DEFAULTS.size,
    ops: [],                // committed annotation ops, in document space
    redo: [],
    following: true,        // viewers only
    laser: false,
    spotlight: false,
    paused: false,
    participants: [],
    startedAt: null
  };

  var socket = io((window.__REPORT_META__ && window.__REPORT_META__.serverUrl) || window.location.origin);

  /* ─── Canvas in document space ──────────────────────────────────────── */
  var canvas = document.createElement('canvas');
  canvas.className = 'p57-annotation-canvas';
  document.body.appendChild(canvas);
  var ctx = canvas.getContext('2d');

  function sizeCanvas() {
    var dpr = window.devicePixelRatio || 1;
    canvas.width = Math.round(window.innerWidth * dpr);
    canvas.height = Math.round(window.innerHeight * dpr);
    canvas.style.width = window.innerWidth + 'px';
    canvas.style.height = window.innerHeight + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    redraw();
  }

  function toDoc(e) { return { x: e.clientX + window.scrollX, y: e.clientY + window.scrollY }; }

  function drawOp(op) {
    // Ops are stored in document space; paint them relative to the viewport.
    var ox = -window.scrollX, oy = -window.scrollY;
    ctx.save();
    ctx.translate(ox, oy);
    ctx.strokeStyle = op.color;
    ctx.fillStyle = op.color;
    ctx.lineWidth = op.size;
    ctx.globalAlpha = op.tool === 'marker' ? 0.32 : 1;
    if (op.tool === 'marker') { ctx.lineWidth = op.size * 4; ctx.lineCap = 'butt'; }
    else { ctx.lineCap = 'round'; }

    if (op.tool === 'pen' || op.tool === 'marker') {
      if (!op.points || op.points.length < 2) { ctx.restore(); return; }
      ctx.beginPath();
      ctx.moveTo(op.points[0].x, op.points[0].y);
      for (var i = 1; i < op.points.length; i++) ctx.lineTo(op.points[i].x, op.points[i].y);
      ctx.stroke();
    } else if (op.tool === 'box') {
      ctx.strokeRect(op.from.x, op.from.y, op.to.x - op.from.x, op.to.y - op.from.y);
    } else if (op.tool === 'ellipse') {
      var cx = (op.from.x + op.to.x) / 2, cy = (op.from.y + op.to.y) / 2;
      ctx.beginPath();
      ctx.ellipse(cx, cy, Math.abs(op.to.x - op.from.x) / 2, Math.abs(op.to.y - op.from.y) / 2, 0, 0, Math.PI * 2);
      ctx.stroke();
    } else if (op.tool === 'arrow') {
      var dx = op.to.x - op.from.x, dy = op.to.y - op.from.y;
      var ang = Math.atan2(dy, dx), head = Math.max(12, op.size * 3.5);
      ctx.beginPath();
      ctx.moveTo(op.from.x, op.from.y);
      ctx.lineTo(op.to.x, op.to.y);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(op.to.x, op.to.y);
      ctx.lineTo(op.to.x - head * Math.cos(ang - Math.PI / 7), op.to.y - head * Math.sin(ang - Math.PI / 7));
      ctx.lineTo(op.to.x - head * Math.cos(ang + Math.PI / 7), op.to.y - head * Math.sin(ang + Math.PI / 7));
      ctx.closePath();
      ctx.fill();
    } else if (op.tool === 'text') {
      var pad = 8, fontSize = Math.max(13, op.size * 3.4);
      ctx.font = '600 ' + fontSize + 'px Inter, system-ui, sans-serif';
      var w = ctx.measureText(op.text).width;
      ctx.globalAlpha = 0.96;
      ctx.fillStyle = op.color;
      roundRect(ctx, op.from.x, op.from.y - fontSize - pad, w + pad * 2, fontSize + pad * 1.5, 8);
      ctx.fill();
      ctx.fillStyle = contrastOn(op.color);
      ctx.fillText(op.text, op.from.x + pad, op.from.y - pad * 0.7);
    }
    ctx.restore();
  }

  function roundRect(c, x, y, w, h, r) {
    c.beginPath();
    c.moveTo(x + r, y);
    c.arcTo(x + w, y, x + w, y + h, r);
    c.arcTo(x + w, y + h, x, y + h, r);
    c.arcTo(x, y + h, x, y, r);
    c.arcTo(x, y, x + w, y, r);
    c.closePath();
  }

  function contrastOn(hex) {
    var n = parseInt(hex.slice(1), 16);
    var l = (0.299 * ((n >> 16) & 255) + 0.587 * ((n >> 8) & 255) + 0.114 * (n & 255)) / 255;
    return l > 0.6 ? '#101828' : '#ffffff';
  }

  var live = null;   // op being drawn right now
  function redraw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    state.ops.forEach(drawOp);
    if (live) drawOp(live);
    // Mirrored on the element so the mark count is inspectable without
    // reaching into module state.
    canvas.dataset.ops = String(state.ops.length);
  }

  /* ─── Drawing ───────────────────────────────────────────────────────── */
  var drawingId = null;

  function canDraw() { return state.role === 'presenter' && state.tool !== 'pointer'; }

  function hitOp(pt) {
    // Eraser: topmost op whose ink is near the pointer.
    for (var i = state.ops.length - 1; i >= 0; i--) {
      var op = state.ops[i];
      var pts = op.points || [op.from, op.to].filter(Boolean);
      for (var j = 0; j < pts.length; j++) {
        if (Math.hypot(pts[j].x - pt.x, pts[j].y - pt.y) < Math.max(18, op.size * 4)) return i;
      }
      if (op.from && op.to) {
        var x1 = Math.min(op.from.x, op.to.x), x2 = Math.max(op.from.x, op.to.x);
        var y1 = Math.min(op.from.y, op.to.y), y2 = Math.max(op.from.y, op.to.y);
        if (pt.x > x1 - 10 && pt.x < x2 + 10 && pt.y > y1 - 10 && pt.y < y2 + 10) return i;
      }
    }
    return -1;
  }

  function commit(op) {
    state.ops.push(op);
    state.redo.length = 0;
    redraw();
    emit({ type: 'op_add', op: op });
    renderPanel();
  }

  canvas.addEventListener('pointerdown', function (e) {
    if (!canDraw()) return;
    var pt = toDoc(e);
    drawingId = e.pointerId;
    // Pointer capture is a nicety, not a requirement — a browser that refuses
    // it must not take the whole stroke down with it.
    try { canvas.setPointerCapture(e.pointerId); } catch (err) { /* ignore */ }

    if (state.tool === 'eraser') {
      var idx = hitOp(pt);
      if (idx > -1) {
        var removed = state.ops.splice(idx, 1)[0];
        redraw();
        emit({ type: 'op_remove', id: removed.id });
      }
      return;
    }
    if (state.tool === 'text') {
      var text = window.prompt('Note text');
      drawingId = null;
      if (!text) return;
      commit({ id: uid(), tool: 'text', text: text.trim(), from: pt, color: state.color, size: state.size });
      return;
    }
    live = {
      id: uid(), tool: state.tool, color: state.color, size: state.size,
      from: pt, to: pt
    };
    // Only freehand tools accumulate a point list; shapes carry from/to, and
    // giving them an empty list made the "did this stroke move?" test below
    // read the wrong field and silently drop every shape.
    if (state.tool === 'pen' || state.tool === 'marker') live.points = [pt];
  });

  canvas.addEventListener('pointermove', function (e) {
    if (state.role === 'presenter' && state.laser) {
      emit({ type: 'laser', x: e.clientX / window.innerWidth, y: (e.clientY + window.scrollY) });
    }
    if (drawingId === null || !live) return;
    var pt = toDoc(e);
    if (live.tool === 'pen' || live.tool === 'marker') live.points.push(pt);
    live.to = pt;
    redraw();
  });

  function finishStroke(e) {
    if (drawingId === null) return;
    try {
      if (e && canvas.hasPointerCapture && canvas.hasPointerCapture(e.pointerId)) {
        canvas.releasePointerCapture(e.pointerId);
      }
    } catch (err) { /* ignore */ }
    drawingId = null;
    if (!live) return;
    var op = live;
    live = null;
    var moved = op.points ? op.points.length > 2
      : Math.hypot(op.to.x - op.from.x, op.to.y - op.from.y) > 6;
    if (moved) commit(op); else redraw();
  }
  canvas.addEventListener('pointerup', finishStroke);
  canvas.addEventListener('pointercancel', finishStroke);

  function uid() { return Math.random().toString(36).slice(2, 10); }

  function undo() {
    var op = state.ops.pop();
    if (!op) return;
    state.redo.push(op);
    redraw();
    emit({ type: 'op_remove', id: op.id });
    renderPanel();
  }
  function redoOp() {
    var op = state.redo.pop();
    if (!op) return;
    state.ops.push(op);
    redraw();
    emit({ type: 'op_add', op: op });
    renderPanel();
  }
  function clearAll() {
    state.ops = [];
    state.redo = [];
    redraw();
    emit({ type: 'op_clear' });
    renderPanel();
  }

  function exportPng() {
    // Flatten the visible viewport's marks onto a white sheet for sharing.
    var out = document.createElement('canvas');
    out.width = canvas.width; out.height = canvas.height;
    var octx = out.getContext('2d');
    octx.fillStyle = '#ffffff';
    octx.fillRect(0, 0, out.width, out.height);
    octx.drawImage(canvas, 0, 0);
    var link = document.createElement('a');
    link.download = 'annotations-' + new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-') + '.png';
    link.href = out.toDataURL('image/png');
    link.click();
  }

  /* ─── Transport ─────────────────────────────────────────────────────── */
  function emit(data) {
    if (state.role !== 'presenter' || !state.code || state.paused) return;
    socket.emit('presenter_event', data);
  }

  socket.on('room_state', function (room) {
    state.participants = room.participants || [];
    state.startedAt = room.startedAt;
    renderPanel();
  });

  socket.on('viewer_event', function (data) {
    if (state.role !== 'presenter') return;
    if (data.type === 'request_state') {
      // Replay the session so a late joiner sees the same page and ink.
      socket.emit('presenter_event', {
        type: 'state_replay', to: data.id,
        scrollY: window.scrollY, ops: state.ops, spotlight: state.spotlight
      });
      return;
    }
    if (data.type === 'hand') toast((data.name || 'A guest') + (data.raised ? ' raised a hand' : ' lowered their hand'));
    if (data.type === 'question') toast((data.name || 'Guest') + ': ' + data.text, 6000);
    renderPanel();
  });

  socket.on('presenter_sync', function (data) {
    if (state.role !== 'viewer') return;
    switch (data.type) {
      case 'scroll':
        if (state.following) window.scrollTo({ top: data.scrollY, behavior: 'instant' });
        break;
      case 'state_replay':
        state.ops = data.ops || [];
        setSpotlight(!!data.spotlight, true);
        if (state.following) window.scrollTo({ top: data.scrollY || 0, behavior: 'instant' });
        redraw();
        break;
      case 'op_add':
        state.ops.push(data.op); redraw(); break;
      case 'op_remove':
        state.ops = state.ops.filter(function (o) { return o.id !== data.id; }); redraw(); break;
      case 'op_clear':
        state.ops = []; redraw(); break;
      case 'laser':
        showLaser(data); break;
      case 'spotlight':
        setSpotlight(!!data.on, true); break;
      case 'session_ended':
        toast('The host ended the session.');
        leave(true); break;
    }
  });

  /* ─── Laser pointer + spotlight ─────────────────────────────────────── */
  var laserDot = document.createElement('div');
  laserDot.className = 'p57-laser';
  document.body.appendChild(laserDot);
  var laserTimer;
  function showLaser(data) {
    laserDot.style.left = (data.x * window.innerWidth) + 'px';
    laserDot.style.top = (data.y - window.scrollY) + 'px';
    laserDot.classList.add('is-on');
    clearTimeout(laserTimer);
    laserTimer = setTimeout(function () { laserDot.classList.remove('is-on'); }, 1400);
  }

  function setSpotlight(on, quiet) {
    state.spotlight = on;
    document.body.classList.toggle('p57-spotlight', on);
    if (!quiet) emit({ type: 'spotlight', on: on });
    renderPanel();
  }

  /* ─── UI ────────────────────────────────────────────────────────────── */
  var bar = document.createElement('div');
  bar.className = 'p57-presenter-bar is-collapsed';
  document.body.appendChild(bar);

  var toastEl = document.createElement('div');
  toastEl.className = 'p57-toast';
  document.body.appendChild(toastEl);
  var toastTimer;
  function toast(msg, ms) {
    toastEl.textContent = msg;
    toastEl.classList.add('is-on');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toastEl.classList.remove('is-on'); }, ms || 3200);
  }

  function elapsed() {
    if (!state.startedAt) return '00:00';
    var s = Math.max(0, Math.floor((Date.now() - state.startedAt) / 1000));
    return String(Math.floor(s / 60)).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0');
  }

  function renderPanel() {
    var open = bar.classList.contains('is-open');
    var hosting = state.role === 'presenter';
    var viewing = state.role === 'viewer';
    var hands = state.participants.filter(function (p) { return p.hand; });

    bar.innerHTML =
      '<button class="p57-presenter-toggle" type="button" aria-expanded="' + open + '" title="Presenter tools">' +
        (hosting ? 'LIVE' : viewing ? 'JOIN' : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 5h18v11H3z"/><path d="M8 20h8M12 16v4"/></svg>') +
      '</button>' +
      '<div class="p57-presenter-panel">' +
        (state.role === 'idle' ? idleMarkup() : sessionMarkup(hosting, hands)) +
      '</div>';

    bar.classList.toggle('is-live', hosting || viewing);
    wire();
  }

  function idleMarkup() {
    return '<div class="p57-panel-head"><strong>Present this report</strong>' +
      '<span>Host a live walkthrough, or join one with a code.</span></div>' +
      '<div class="p57-field"><label for="p57-name">Your name</label>' +
      '<input id="p57-name" type="text" maxlength="40" placeholder="e.g. Jimmeey" value="' + escapeAttr(state.name) + '"></div>' +
      '<div class="p57-panel-actions">' +
        '<button class="p57-btn is-primary" data-act="host">Host a session</button>' +
        '<button class="p57-btn" data-act="join">Join with code</button>' +
      '</div>';
  }

  function sessionMarkup(hosting, hands) {
    var roster = state.participants.map(function (p) {
      return '<li class="' + (p.role === 'presenter' ? 'is-host' : '') + '">' +
        '<span class="p57-avatar">' + escapeHtml((p.name || '?').slice(0, 1).toUpperCase()) + '</span>' +
        '<span class="p57-person">' + escapeHtml(p.name || 'Guest') +
        '<small>' + (p.role === 'presenter' ? 'Host' : (p.following ? 'Following' : 'Browsing freely')) + '</small></span>' +
        (p.hand ? '<span class="p57-hand" title="Hand raised">✋</span>' : '') + '</li>';
    }).join('');

    var tools = hosting ? (
      '<div class="p57-tool-row" role="group" aria-label="Annotation tools">' +
        TOOLS.map(function (t) {
          return '<button class="p57-tool' + (state.tool === t.key ? ' is-active' : '') +
            '" data-tool="' + t.key + '" title="' + t.hint + '">' + t.label + '</button>';
        }).join('') +
      '</div>' +
      '<div class="p57-tool-row p57-ink-row">' +
        PALETTE.map(function (c) {
          return '<button class="p57-swatch' + (state.color === c.color ? ' is-active' : '') +
            '" data-color="' + c.color + '" style="--swatch:' + c.color + '" title="' + c.label + '"></button>';
        }).join('') +
        '<label class="p57-size"><span>Width</span>' +
        '<input type="range" min="2" max="14" value="' + state.size + '" data-size></label>' +
        '<button class="p57-btn is-icon" data-act="undo" title="Undo (Ctrl+Z)">↺</button>' +
        '<button class="p57-btn is-icon" data-act="redo" title="Redo (Ctrl+Shift+Z)">↻</button>' +
        '<button class="p57-btn is-icon" data-act="clear" title="Clear all marks">✕</button>' +
        '<button class="p57-btn is-icon" data-act="png" title="Save marks as PNG">⤓</button>' +
      '</div>' +
      '<div class="p57-tool-row">' +
        '<button class="p57-btn' + (state.laser ? ' is-on' : '') + '" data-act="laser">Laser pointer</button>' +
        '<button class="p57-btn' + (state.spotlight ? ' is-on' : '') + '" data-act="spotlight">Spotlight</button>' +
        '<button class="p57-btn' + (state.paused ? ' is-on' : '') + '" data-act="pause">' + (state.paused ? 'Sync paused' : 'Pause sync') + '</button>' +
      '</div>'
    ) : (
      '<div class="p57-tool-row">' +
        '<button class="p57-btn' + (state.following ? ' is-on' : '') + '" data-act="follow">' +
          (state.following ? 'Following host' : 'Browsing freely') + '</button>' +
        '<button class="p57-btn" data-act="hand">Raise hand</button>' +
        '<button class="p57-btn" data-act="question">Ask a question</button>' +
      '</div>'
    );

    return '<div class="p57-panel-head">' +
        '<strong>' + (hosting ? 'You are hosting' : 'In session') + '</strong>' +
        '<span class="p57-session-meta">' +
          '<span class="p57-live-dot"></span>Code <b>' + escapeHtml(state.code || '') + '</b>' +
          ' · ' + state.participants.length + ' in room · ' + elapsed() +
        '</span>' +
      '</div>' +
      (hands.length ? '<div class="p57-hands">' + hands.length + ' hand' + (hands.length > 1 ? 's' : '') + ' raised</div>' : '') +
      '<ul class="p57-roster">' + roster + '</ul>' +
      tools +
      '<div class="p57-panel-actions">' +
        (hosting ? '<button class="p57-btn" data-act="copy">Copy invite link</button>' : '') +
        '<button class="p57-btn is-danger" data-act="leave">' + (hosting ? 'End session' : 'Leave') + '</button>' +
      '</div>';
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }
  function escapeAttr(s) { return escapeHtml(s); }

  function wire() {
    var toggle = bar.querySelector('.p57-presenter-toggle');
    toggle.addEventListener('click', function () {
      var open = !bar.classList.contains('is-open');
      bar.classList.toggle('is-open', open);
      bar.classList.toggle('is-collapsed', !open);
      toggle.setAttribute('aria-expanded', String(open));
    });

    bar.querySelectorAll('[data-tool]').forEach(function (b) {
      b.addEventListener('click', function () { setTool(b.getAttribute('data-tool')); });
    });
    bar.querySelectorAll('[data-color]').forEach(function (b) {
      b.addEventListener('click', function () { state.color = b.getAttribute('data-color'); renderPanel(); });
    });
    var sizeInput = bar.querySelector('[data-size]');
    if (sizeInput) sizeInput.addEventListener('input', function () { state.size = +sizeInput.value; });

    var nameInput = bar.querySelector('#p57-name');
    if (nameInput) nameInput.addEventListener('input', function () { state.name = nameInput.value; });

    bar.querySelectorAll('[data-act]').forEach(function (b) {
      b.addEventListener('click', function () { act(b.getAttribute('data-act')); });
    });
  }

  function setTool(tool) {
    state.tool = tool;
    document.body.classList.toggle('p57-drawing', tool !== 'pointer' && state.role === 'presenter');
    document.body.setAttribute('data-p57-tool', tool);
    renderPanel();
  }

  function act(what) {
    switch (what) {
      case 'host': host(); break;
      case 'join': promptJoin(); break;
      case 'leave': leave(); break;
      case 'undo': undo(); break;
      case 'redo': redoOp(); break;
      case 'clear': clearAll(); break;
      case 'png': exportPng(); break;
      case 'laser': state.laser = !state.laser; renderPanel(); break;
      case 'spotlight': setSpotlight(!state.spotlight); break;
      case 'pause':
        state.paused = !state.paused;
        toast(state.paused ? 'Sync paused — guests stay where they are.' : 'Sync resumed.');
        renderPanel();
        break;
      case 'copy': copyInvite(); break;
      case 'follow':
        state.following = !state.following;
        socket.emit('viewer_event', { type: 'follow', following: state.following });
        renderPanel();
        break;
      case 'hand':
        socket.emit('viewer_event', { type: 'hand', raised: true });
        toast('Hand raised.');
        break;
      case 'question':
        var q = window.prompt('Your question for the host');
        if (q) { socket.emit('viewer_event', { type: 'question', text: q.slice(0, 240) }); toast('Sent.'); }
        break;
    }
  }

  function askName(fallback) {
    var input = bar.querySelector('#p57-name');
    var name = (input && input.value.trim()) || state.name || window.prompt('Your name') || fallback;
    state.name = name;
    return name;
  }

  function host() {
    var name = askName('Host');
    state.code = String(Math.floor(100000 + Math.random() * 900000));
    state.role = 'presenter';
    state.startedAt = Date.now();
    socket.emit('join_room', { role: 'presenter', code: state.code, name: name, reportUrl: window.location.pathname });
    document.body.classList.add('p57-presenting');
    setTool('pointer');
    bar.classList.add('is-open'); bar.classList.remove('is-collapsed');
    renderPanel();
    startClock();
    toast('Session live. Code ' + state.code + ' — share the invite link.');
  }

  function promptJoin() {
    var code = (window.prompt('Six-digit session code') || '').trim();
    if (!/^\d{6}$/.test(code)) return;
    joinAs(code);
  }

  function joinAs(code) {
    var name = askName('Guest');
    state.code = code;
    state.role = 'viewer';
    state.following = true;
    socket.emit('join_room', { role: 'viewer', code: code, name: name });
    document.body.classList.add('p57-viewing');
    bar.classList.add('is-open'); bar.classList.remove('is-collapsed');
    renderPanel();
    startClock();
    toast('Joined session ' + code + '. You are following the host.');
  }

  function copyInvite() {
    var url = window.location.origin + window.location.pathname + '?roomCode=' + state.code;
    if (navigator.clipboard) navigator.clipboard.writeText(url).then(function () { toast('Invite link copied.'); });
    else window.prompt('Invite link', url);
  }

  var clockTimer;
  function startClock() {
    clearInterval(clockTimer);
    clockTimer = setInterval(function () {
      var meta = bar.querySelector('.p57-session-meta');
      if (meta && state.role !== 'idle') renderPanel();
      else clearInterval(clockTimer);
    }, 15000);
  }

  function leave(remote) {
    var wasHost = state.role === 'presenter';
    if (!remote && state.code) socket.emit('leave_room', { code: state.code, endSession: wasHost });
    state.role = 'idle';
    state.code = null;
    state.ops = [];
    state.redo = [];
    state.participants = [];
    state.paused = false;
    state.laser = false;
    setSpotlight(false, true);
    setTool('pointer');
    document.body.classList.remove('p57-presenting', 'p57-viewing', 'p57-drawing');
    redraw();
    renderPanel();
    clearInterval(clockTimer);
  }

  /* ─── Host broadcasts + keyboard ────────────────────────────────────── */
  var scrollTicking = false;
  window.addEventListener('scroll', function () {
    redraw();
    if (state.role === 'presenter' && !scrollTicking) {
      scrollTicking = true;
      requestAnimationFrame(function () {
        emit({ type: 'scroll', scrollY: window.scrollY });
        scrollTicking = false;
      });
    }
  }, { passive: true });

  window.addEventListener('resize', sizeCanvas);

  document.addEventListener('keydown', function (e) {
    if (state.role !== 'presenter') return;
    if (/input|textarea|select/i.test((e.target.tagName || '')) || e.target.isContentEditable) return;
    var key = e.key.toLowerCase();
    if ((e.ctrlKey || e.metaKey) && key === 'z') { e.preventDefault(); e.shiftKey ? redoOp() : undo(); return; }
    var map = { p: 'pen', m: 'marker', a: 'arrow', b: 'box', o: 'ellipse', t: 'text', e: 'eraser' };
    if (map[key]) { e.preventDefault(); setTool(map[key]); }
    if (e.key === 'Escape') setTool('pointer');
    if (key === 'l') { state.laser = !state.laser; renderPanel(); }
    if (key === 's') setSpotlight(!state.spotlight);
  });

  sizeCanvas();
  setTool('pointer');
  renderPanel();

  var initCode = new URLSearchParams(window.location.search).get('roomCode');
  if (initCode && /^\d{6}$/.test(initCode)) joinAs(initCode);

  window.__p57Presenter = { state: state, leave: leave };
})();
