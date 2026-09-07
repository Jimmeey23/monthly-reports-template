(function () {
  const ctx = window.__REPORT_CTX__ || {};

  function resolveApiUrl(path) {
    if (ctx.serverUrl) {
      return `${ctx.serverUrl.replace(/\/$/, '')}${path}`;
    }
    if (window.location.protocol.startsWith('http')) {
      return path;
    }
    return `http://localhost:3000${path}`;
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  // ───────────────────────── Per-section AI insights ─────────────────────────

  const CLASS_COLORS = {
    excellent: '#10b981',
    healthy: '#3b82f6',
    opportunity: '#f59e0b',
    watch: '#ef4444',
    warning: '#f59e0b',
    critical: '#ef4444',
  };
  const PRIORITY_COLORS = { high: '#ef4444', medium: '#f59e0b', low: '#10b981' };
  const safeVal = (v) => (v != null && v !== 'undefined' && String(v).trim() !== '') ? String(v) : '—';

  function renderInsightsSection(insights) {
    if (!insights || !insights.length) return '<p style="color:var(--text-muted);font-size:13px;">No insights generated.</p>';
    return insights.map((ins, i) => {
      const cls = (ins.classification || '').toLowerCase();
      const clsColor = CLASS_COLORS[cls] || '#6b7280';
      const badge = cls
        ? `<span class="insight-badge" style="background:${clsColor}22;color:${clsColor};border:1px solid ${clsColor}55;">${cls.toUpperCase()}</span>`
        : '';
      const evidence = ins.data_evidence
        ? `<div class="ai-evidence"><span class="ai-evidence-label">&#128202; Data:</span> ${escapeHtml(ins.data_evidence)}</div>`
        : '';
      return `
      <div class="insight-card">
        <div class="insight-num">${String(i + 1).padStart(2, '0')}</div>
        <div class="insight-body">
          <div class="insight-title-row">${badge}<div class="insight-title">${escapeHtml(ins.title)}</div></div>
          <div class="insight-text">${escapeHtml(ins.text)}</div>
          ${evidence}
        </div>
      </div>`;
    }).join('');
  }

  function renderHighlightsSection(highlights) {
    if (!highlights || !highlights.length) return '<p style="color:var(--text-muted);font-size:13px;">No highlights identified.</p>';
    return `<div class="ai-highlights-grid">${highlights.map(h => {
      const isAchievement = (h.type || '').toLowerCase() === 'achievement';
      const accentColor = isAchievement ? '#10b981' : '#f59e0b';
      const iconChar = isAchievement ? '&#9650;' : '&#9660;';
      const typeLabel = isAchievement ? 'Achievement' : 'Area to Improve';
      return `
      <div class="ai-highlight-card" style="border-left-color:${accentColor}">
        <div class="ai-highlight-header">
          <span class="ai-highlight-icon" style="color:${accentColor}">${iconChar}</span>
          <span class="ai-highlight-metric">${escapeHtml(safeVal(h.metric))}</span>
          <span class="ai-highlight-type-badge" style="background:${accentColor}18;color:${accentColor};border:1px solid ${accentColor}44;">${typeLabel}</span>
        </div>
        <div class="ai-highlight-headline">${escapeHtml(safeVal(h.headline))}</div>
        <div class="ai-highlight-magnitude" style="color:${accentColor}">${escapeHtml(safeVal(h.magnitude))}</div>
        <div class="ai-highlight-detail">${escapeHtml(safeVal(h.detail))}</div>
      </div>`;
    }).join('')}</div>`;
  }

  function renderRecommendationsSection(recs) {
    if (!recs || !recs.length) return '<p style="color:var(--text-muted);font-size:13px;">No recommendations generated.</p>';
    return recs.map((r, i) => {
      const pri = safeVal(r.priority).toLowerCase();
      const priColor = PRIORITY_COLORS[pri] || '#6b7280';
      const priBadge = pri && pri !== '—'
        ? `<span class="meta-pill" style="background:${priColor}18;color:${priColor};border:1px solid ${priColor}44;font-weight:600;">${pri.toUpperCase()}</span>`
        : '';
      return `
      <div class="ai-rec-card">
        <div class="ai-rec-num">${String(i + 1).padStart(2, '0')}</div>
        <div class="ai-rec-content">
          <div class="ai-rec-title">${escapeHtml(safeVal(r.title))}</div>
          <div class="ai-rec-desc">${escapeHtml(safeVal(r.description))}</div>
          <div class="ai-rec-impact">
            <span class="ai-rec-impact-label">&#127919; Expected Impact:</span>
            ${escapeHtml(safeVal(r.expected_impact))}
          </div>
          <div class="ai-rec-meta">
            ${priBadge}
            <span class="meta-pill">&#128197; ${escapeHtml(safeVal(r.timeline))}</span>
            <span class="meta-pill">&#128100; ${escapeHtml(safeVal(r.owner))}</span>
          </div>
        </div>
      </div>`;
    }).join('');
  }

  function renderResult(result) {
    const ps = result.performance_summary;
    const insights = result.key_insights || result.insights || [];
    const highlights = result.highlights || [];
    const recs = result.recommendations || [];
    const narrative = ps && ps.narrative ? `<div class="ai-summary-narrative">${escapeHtml(ps.narrative)}</div>` : '';
    const patternList = (ps && ps.patterns && ps.patterns.length)
      ? `<div class="ai-patterns-wrap"><div class="ai-sub-label">Identified Patterns &amp; Behaviours</div>${ps.patterns.map(p => `
          <div class="ai-pattern-card">
            <div class="ai-pattern-name">&#9670; ${escapeHtml(p.pattern)}</div>
            <div class="ai-pattern-desc">${escapeHtml(p.description)}</div>
          </div>`).join('')}</div>`
      : '';

    return `
      <div class="ai-result ai-result-v2">
        <div class="ai-result-header">
          <div class="ai-result-header-icon">&#10024;</div>
          <div>
            <div class="ai-result-header-title">AI-Powered Analysis</div>
            <div class="ai-result-header-sub">Deep insights generated from your data, presented as one continuous analysis block.</div>
          </div>
        </div>
        ${narrative}
        ${patternList}
        <div class="ai-section">
          <div class="ai-section-toggle is-open" role="button" tabindex="0">
            <span class="ai-section-icon">&#128161;</span>
            <span class="ai-section-label">Key Insights (${insights.length})</span>
            <span class="ai-section-chevron">&#9662;</span>
          </div>
          <div class="ai-section-body is-open">${renderInsightsSection(insights)}</div>
        </div>
        <div class="ai-section">
          <div class="ai-section-toggle is-open" role="button" tabindex="0">
            <span class="ai-section-icon">&#11088;</span>
            <span class="ai-section-label">Highlights &amp; Standouts (${highlights.length})</span>
            <span class="ai-section-chevron">&#9662;</span>
          </div>
          <div class="ai-section-body is-open">${renderHighlightsSection(highlights)}</div>
        </div>
        <div class="ai-section">
          <div class="ai-section-toggle is-open" role="button" tabindex="0">
            <span class="ai-section-icon">&#127919;</span>
            <span class="ai-section-label">Recommendations (${recs.length})</span>
            <span class="ai-section-chevron">&#9662;</span>
          </div>
          <div class="ai-section-body is-open">${renderRecommendationsSection(recs)}</div>
        </div>
      </div>`;
  }

  // ─── Toggle collapsible sections ─────────────────────────
  document.addEventListener('click', (e) => {
    const toggle = e.target.closest('.ai-section-toggle');
    if (!toggle) return;
    const body = toggle.parentElement && toggle.parentElement.querySelector('.ai-section-body');
    if (!body) return;
    toggle.classList.toggle('is-open');
    body.classList.toggle('is-open');
  });

  // ─── AI button click handler ─────────────────────────
  document.querySelectorAll('.ai-info-btn').forEach((btn) => {
    const originalLabel = btn.innerHTML;
    btn.addEventListener('click', async () => {
      const section = btn.dataset.section;
      const slot = document.getElementById(`ai-slot-${section}`);
      if (!slot) return;

      if (!ctx.sessionId) {
        slot.innerHTML = `<div class="ai-result ai-result-v2"><div class="ai-result-error">AI insights require viewing through the report server (missing session ID).</div></div>`;
        return;
      }

      btn.disabled = true;
      btn.classList.add('is-loading');
      btn.innerHTML = '<span class="ai-info-icon spinner">&#8982;</span>';
      slot.innerHTML = '';

      try {
        const aiUrl = resolveApiUrl(`/ai-insights/${ctx.sessionId}/${section}`);
        const res = await fetch(aiUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ loc: ctx.loc, month: ctx.month }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Request failed');
        slot.innerHTML = renderResult(data);
        btn.innerHTML = '<span class="ai-info-icon">i</span>';
      } catch (e) {
        slot.innerHTML = `<div class="ai-result ai-result-v2"><div class="ai-result-error">AI analysis failed: ${escapeHtml(e.message)}</div></div>`;
        btn.innerHTML = originalLabel;
      }

      btn.disabled = false;
      btn.classList.remove('is-loading');
    });
  });

  // ─── Inject minimal CSS for AI insights ─────────
  const styleEl = document.createElement('style');
  styleEl.textContent = `
.ai-info-btn { width: 28px; height: 28px; border-radius: 50%; background: var(--bg-card); border: 1px solid var(--border); color: var(--text-muted); font-family: var(--font-serif); font-style: italic; font-size: 14px; font-weight: 600; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; padding: 0; box-shadow: var(--shadow-sm); }
.ai-info-btn:hover { color: var(--primary); border-color: var(--primary); transform: scale(1.05); }
.ai-info-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.ai-info-btn .spinner { animation: ai-spin 1s linear infinite; font-style: normal; }
.ai-slot { min-height: 0; transition: all 0.3s ease; }
@keyframes ai-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
`;
  document.head.appendChild(styleEl);

  // ───────────────────────── Presenter View ─────────────────────────
  if (typeof io !== 'undefined') {
    const pBar = document.createElement('div');
    pBar.className = 'presenter-bar is-collapsed';
    pBar.innerHTML = `<button type="button" class="presenter-toggle" id="p-toggle" aria-expanded="false" aria-controls="presenter-panel" title="Meeting controls">◉</button><div class="presenter-panel" id="presenter-panel"><div class="presenter-info"><span id="p-status"></span><span class="presenter-badge" id="p-code" style="display:none;"></span></div><div class="annotation-tools" aria-label="Presenter annotation tools"><button type="button" class="annotation-btn annotation-color is-active" data-color="#fff176" title="Yellow highlight">Yellow</button><button type="button" class="annotation-btn annotation-color" data-color="#a7f3d0" title="Green highlight">Green</button><button type="button" class="annotation-btn annotation-color" data-color="#fbcfe8" title="Pink highlight">Pink</button><button type="button" class="annotation-btn" id="p-highlight-btn" title="Highlight selected word or text">Highlight</button><button type="button" class="annotation-btn" id="p-tooltip-btn" title="Add tooltip note to selected text">Tooltip</button><button type="button" class="annotation-btn" id="p-pen-btn" title="Draw on screen">Pen</button><button type="button" class="annotation-btn" id="p-eraser-btn" title="Erase drawings">Eraser</button><button type="button" class="annotation-btn" id="p-clear-annotations-btn" title="Clear annotations">Clear</button></div><div class="presenter-actions"><button type="button" class="presenter-btn" id="p-host-btn">Host</button><button type="button" class="presenter-btn" id="p-join-btn">Join</button><button type="button" class="presenter-btn" id="p-end-btn" style="display:none;">End Hosting</button><button type="button" class="presenter-btn" id="p-leave-btn" style="display:none;">Leave</button></div></div>`;
    document.body.appendChild(pBar);

    const pToggle = document.getElementById('p-toggle');

    const pModal = document.createElement('div');
    pModal.className = 'presenter-modal';
    pModal.innerHTML = `<div class="presenter-modal-title">Join Session</div><input type="text" id="p-input" placeholder="6-digit code" maxlength="6"><div class="presenter-modal-actions"><button class="presenter-btn" id="p-cancel">Cancel</button><button class="presenter-btn" id="p-submit">Join</button></div>`;
    document.body.appendChild(pModal);

    const socket = io(ctx.serverUrl || window.location.origin);
    let myRole = 'idle';
    let myCode = null;
    let annotationColor = '#fff176';
    let annotationMode = 'idle';
    let drawing = false;
    let lastPoint = null;

    const annotationCanvas = document.createElement('canvas');
    annotationCanvas.className = 'annotation-canvas';
    document.body.appendChild(annotationCanvas);
    const annotationCtx = annotationCanvas.getContext('2d');

    function resizeAnnotationCanvas() {
      const dpr = window.devicePixelRatio || 1;
      annotationCanvas.width = Math.round(window.innerWidth * dpr);
      annotationCanvas.height = Math.round(window.innerHeight * dpr);
      annotationCanvas.style.width = `${window.innerWidth}px`;
      annotationCanvas.style.height = `${window.innerHeight}px`;
      annotationCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
      annotationCtx.lineCap = 'round';
      annotationCtx.lineJoin = 'round';
    }
    resizeAnnotationCanvas();
    window.addEventListener('resize', resizeAnnotationCanvas);

    socket.on('room_state', (state) => {
      document.getElementById('p-status').textContent = myRole === 'presenter' ? `${state.viewers} viewers` : 'Viewing host screen';
    });

    socket.on('presenter_sync', (data) => {
      if (myRole !== 'viewer') return;
      if (data.type === 'scroll') {
        window.scrollTo({ top: data.scrollY, behavior: 'instant' });
      }
      if (data.type === 'click') {
        const el = document.elementFromPoint(data.x, data.y);
        if (el && typeof el.click === 'function') {
          document.body.classList.remove('viewer-locked');
          el.click();
          document.body.classList.add('viewer-locked');
        }
      }
      if (data.type === 'draw') drawStroke(data.points, data.color, data.size, data.erase);
      if (data.type === 'clear_annotations') clearAnnotations();
      if (data.type === 'session_ended') resetPresenterSession();
    });

    let scrollTicking = false;
    window.addEventListener('scroll', () => {
      if (myRole === 'presenter' && !scrollTicking) {
        window.requestAnimationFrame(() => {
          socket.emit('presenter_event', { type: 'scroll', scrollY: window.scrollY });
          scrollTicking = false;
        });
        scrollTicking = true;
      }
    });

    document.addEventListener('click', (e) => {
      if (myRole === 'presenter' && e.isTrusted && !e.target.closest('.presenter-bar')) {
        socket.emit('presenter_event', { type: 'click', x: e.clientX, y: e.clientY });
      }
    });

    document.querySelectorAll('.annotation-color').forEach((btn) => {
      btn.addEventListener('click', () => {
        annotationColor = btn.dataset.color || '#fff176';
        document.querySelectorAll('.annotation-color').forEach((colorBtn) => colorBtn.classList.toggle('is-active', colorBtn === btn));
      });
    });

    document.getElementById('p-highlight-btn').addEventListener('click', () => markSelection(annotationColor));
    document.getElementById('p-tooltip-btn').addEventListener('click', () => {
      const note = window.prompt('Tooltip note');
      if (note) markSelection(annotationColor, note.trim());
    });
    document.getElementById('p-pen-btn').addEventListener('click', () => setAnnotationMode(annotationMode === 'draw' ? 'idle' : 'draw'));
    document.getElementById('p-eraser-btn').addEventListener('click', () => setAnnotationMode(annotationMode === 'erase' ? 'idle' : 'erase'));
    document.getElementById('p-clear-annotations-btn').addEventListener('click', () => {
      clearAnnotations();
      socket.emit('presenter_event', { type: 'clear_annotations' });
    });

    annotationCanvas.addEventListener('pointerdown', (e) => {
      if (myRole !== 'presenter' || (annotationMode !== 'draw' && annotationMode !== 'erase')) return;
      drawing = true;
      lastPoint = { x: e.clientX, y: e.clientY };
      annotationCanvas.setPointerCapture(e.pointerId);
    });

    annotationCanvas.addEventListener('pointermove', (e) => {
      if (!drawing || !lastPoint) return;
      const nextPoint = { x: e.clientX, y: e.clientY };
      const stroke = {
        points: [lastPoint, nextPoint],
        color: annotationColor,
        size: annotationMode === 'erase' ? 28 : 4,
        erase: annotationMode === 'erase'
      };
      drawStroke(stroke.points, stroke.color, stroke.size, stroke.erase);
      socket.emit('presenter_event', { type: 'draw', ...stroke });
      lastPoint = nextPoint;
    });

    annotationCanvas.addEventListener('pointerup', (e) => {
      drawing = false;
      lastPoint = null;
      annotationCanvas.releasePointerCapture(e.pointerId);
    });

    function setAnnotationMode(mode) {
      annotationMode = mode;
      document.body.classList.toggle('annotation-draw-mode', mode === 'draw');
      document.body.classList.toggle('annotation-erase-mode', mode === 'erase');
      document.getElementById('p-pen-btn').classList.toggle('is-active', mode === 'draw');
      document.getElementById('p-eraser-btn').classList.toggle('is-active', mode === 'erase');
    }

    function setPresenterPanelOpen(open) {
      pBar.classList.toggle('is-collapsed', !open);
      pBar.classList.toggle('is-open', open);
      pToggle.setAttribute('aria-expanded', String(open));
    }

    function drawStroke(points, color, size, erase) {
      if (!points || points.length < 2) return;
      annotationCtx.save();
      annotationCtx.globalCompositeOperation = erase ? 'destination-out' : 'source-over';
      annotationCtx.strokeStyle = color || '#fff176';
      annotationCtx.lineWidth = size || 4;
      annotationCtx.beginPath();
      annotationCtx.moveTo(points[0].x, points[0].y);
      for (let i = 1; i < points.length; i++) annotationCtx.lineTo(points[i].x, points[i].y);
      annotationCtx.stroke();
      annotationCtx.restore();
    }

    function clearAnnotations() {
      annotationCtx.clearRect(0, 0, annotationCanvas.width, annotationCanvas.height);
      document.querySelectorAll('.annotation-mark, .annotation-tooltip').forEach((node) => {
        const text = document.createTextNode(node.textContent);
        node.replaceWith(text);
      });
    }

    function markSelection(color, note) {
      if (myRole !== 'presenter') return;
      const selection = window.getSelection();
      if (!selection || selection.rangeCount === 0 || selection.isCollapsed) return;
      const range = selection.getRangeAt(0);
      if (pBar.contains(range.commonAncestorContainer)) return;
      const mark = document.createElement('span');
      mark.className = note ? 'annotation-tooltip' : 'annotation-mark';
      mark.style.setProperty('--annotation-color', color || '#fff176');
      if (note) mark.dataset.note = note;
      try {
        range.surroundContents(mark);
        selection.removeAllRanges();
      } catch (err) {
        const contents = range.extractContents();
        mark.appendChild(contents);
        range.insertNode(mark);
        selection.removeAllRanges();
      }
    }

    function joinSession(role, code) {
      myRole = role;
      myCode = code;
      socket.emit('join_room', { role, code, reportUrl: window.location.pathname });
      
      document.getElementById('p-code').textContent = 'Code: ' + code;
      document.getElementById('p-code').style.display = 'inline-block';
      document.getElementById('p-host-btn').style.display = 'none';
      document.getElementById('p-join-btn').style.display = 'none';
      document.getElementById('p-end-btn').style.display = role === 'presenter' ? 'inline-block' : 'none';
      document.getElementById('p-leave-btn').style.display = 'inline-block';
      pBar.classList.add('is-active');
      setPresenterPanelOpen(true);
      document.body.classList.add('presenting');

      if (role === 'viewer') {
        document.body.classList.add('viewer-locked');
      }
    }

    document.getElementById('p-host-btn').addEventListener('click', () => {
      const code = Math.floor(100000 + Math.random() * 900000).toString();
      joinSession('presenter', code);
    });

    pToggle.addEventListener('click', () => {
      setPresenterPanelOpen(pBar.classList.contains('is-collapsed'));
    });

    document.getElementById('p-join-btn').addEventListener('click', () => pModal.classList.add('is-open'));
    document.getElementById('p-cancel').addEventListener('click', () => pModal.classList.remove('is-open'));
    
    document.getElementById('p-submit').addEventListener('click', () => {
      const code = document.getElementById('p-input').value.trim();
      if (code.length === 6) {
        joinSession('viewer', code);
        pModal.classList.remove('is-open');
      }
    });

    function resetPresenterSession() {
      myRole = 'idle';
      myCode = null;
      document.getElementById('p-status').textContent = '';
      document.getElementById('p-code').style.display = 'none';
      document.getElementById('p-host-btn').style.display = 'inline-block';
      document.getElementById('p-join-btn').style.display = 'inline-block';
      document.getElementById('p-end-btn').style.display = 'none';
      document.getElementById('p-leave-btn').style.display = 'none';
      pBar.classList.remove('is-active');
      setPresenterPanelOpen(false);
      document.body.classList.remove('presenting');
      setAnnotationMode('idle');
      clearAnnotations();
      document.body.classList.remove('viewer-locked');
    }

    document.getElementById('p-end-btn').addEventListener('click', () => {
      if (myCode) socket.emit('leave_room', { code: myCode, endSession: true });
      resetPresenterSession();
    });

    document.getElementById('p-leave-btn').addEventListener('click', () => {
      const wasPresenter = myRole === 'presenter';
      if (myCode) socket.emit('leave_room', { code: myCode, endSession: wasPresenter });
      resetPresenterSession();
    });

    const urlParams = new URLSearchParams(window.location.search);
    const initCode = urlParams.get('roomCode');
    if (initCode && initCode.length === 6) {
      joinSession('viewer', initCode);
    }
  }
})();
