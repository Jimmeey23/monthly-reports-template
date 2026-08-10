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

  // ───────────────────────── Editor toolbar ─────────────────────────

  const FONT_FAMILIES = [
    ['Inter (default)', "'Inter','Helvetica Neue',Helvetica,Arial,sans-serif"],
    ['Source Serif', "'Source Serif Pro',Georgia,serif"],
    ['Georgia', 'Georgia, serif'],
    ['Arial', 'Arial, Helvetica, sans-serif'],
    ['Courier New', "'Courier New', monospace"],
    ['Verdana', 'Verdana, Geneva, sans-serif'],
  ];
  const FONT_SIZES = [11, 12, 13, 14, 16, 18, 20, 24, 28, 32, 40, 48];
  const BORDER_STYLES = [
    ['None', 'none'],
    ['Thin solid', '1px solid'],
    ['Medium solid', '2px solid'],
    ['Thick solid', '3px solid'],
    ['Dashed', '2px dashed'],
    ['Dotted', '2px dotted'],
  ];

  function iconBtn(command, title, label) {
    return `<button type="button" class="format-btn" data-command="${command}" title="${title}">${label}</button>`;
  }

  const toolbar = document.createElement('div');
  toolbar.className = 'editor-toolbar';
  toolbar.innerHTML =
    '<div class="editor-tools-left">' +
      '<button type="button" id="edit-toggle-btn">&#9998; Edit</button>' +
      '<button type="button" id="save-btn" disabled>&#128190; Save</button>' +
      '<span class="editor-status" id="editor-status"></span>' +
    '</div>' +
    '<div class="editor-format-tools" id="format-tools" style="display:none;">' +

      '<div class="fmt-group">' +
        iconBtn('undo', 'Undo', '&#8630;') +
        iconBtn('redo', 'Redo', '&#8631;') +
      '</div>' +

      '<div class="fmt-group">' +
        `<select id="font-family-select" class="fmt-select" title="Font family">` +
          `<option value="">Font</option>` +
          FONT_FAMILIES.map(([label, val]) => `<option value="${val}">${label}</option>`).join('') +
        `</select>` +
        `<select id="font-size-select" class="fmt-select fmt-select-sm" title="Font size">` +
          `<option value="">Size</option>` +
          FONT_SIZES.map((sz) => `<option value="${sz}">${sz}px</option>`).join('') +
        `</select>` +
      '</div>' +

      '<div class="fmt-group">' +
        iconBtn('bold', 'Bold', '<b>B</b>') +
        iconBtn('italic', 'Italic', '<i>I</i>') +
        iconBtn('underline', 'Underline', '<u>U</u>') +
        iconBtn('strikeThrough', 'Strikethrough', '<s>S</s>') +
      '</div>' +

      '<div class="fmt-group">' +
        `<label class="fmt-color-swatch" title="Text color">A<input type="color" id="text-color-input" value="#0b1a33"></label>` +
        `<label class="fmt-color-swatch" title="Highlight color">&#9635;<input type="color" id="highlight-color-input" value="#fff7d6"></label>` +
      '</div>' +

      '<div class="fmt-group">' +
        iconBtn('justifyLeft', 'Align left', '&#8676;') +
        iconBtn('justifyCenter', 'Align center', '&#8596;') +
        iconBtn('justifyRight', 'Align right', '&#8677;') +
        iconBtn('justifyFull', 'Justify', '&#9776;') +
      '</div>' +

      '<div class="fmt-group">' +
        iconBtn('insertUnorderedList', 'Bullet list', '&#8226;&#8226;&#8226;') +
        iconBtn('insertOrderedList', 'Numbered list', '1.2.3.') +
        iconBtn('outdent', 'Decrease indent (Shift+Tab)', '&#8676;&#124;') +
        iconBtn('indent', 'Increase indent / nest list (Tab)', '&#124;&#8677;') +
      '</div>' +

      '<div class="fmt-group">' +
        `<select id="border-style-select" class="fmt-select fmt-select-sm" title="Border style">` +
          BORDER_STYLES.map(([label, val]) => `<option value="${val}">${label}</option>`).join('') +
        `</select>` +
        `<label class="fmt-color-swatch" title="Border color">&#9633;<input type="color" id="border-color-input" value="#0f2c5e"></label>` +
        `<button type="button" id="apply-border-btn" class="format-btn" title="Apply border to selection">Border</button>` +
      '</div>' +

      '<div class="fmt-group">' +
        `<button type="button" id="clear-format-btn" class="format-btn" title="Clear formatting">Clear</button>` +
      '</div>' +

    '</div>';
  document.body.appendChild(toolbar);

  const editBtn = document.getElementById('edit-toggle-btn');
  const saveBtn = document.getElementById('save-btn');
  const statusEl = document.getElementById('editor-status');
  let editing = false;
  let savedRange = null;

  function setEditing(on) {
    editing = on;
    document.documentElement.setAttribute('data-editing', on ? 'true' : 'false');
    document.querySelectorAll('.container').forEach((el) => {
      el.setAttribute('contenteditable', on ? 'true' : 'false');
    });
    editBtn.classList.toggle('is-active', on);
    editBtn.innerHTML = on ? '&#9998; Editing&hellip;' : '&#9998; Edit';
    saveBtn.disabled = !on;
    if (formatTools) formatTools.style.display = on ? 'flex' : 'none';
    if (on) {
      try { document.execCommand('styleWithCSS', false, true); } catch (e) {}
    }
  }

  editBtn.addEventListener('click', () => setEditing(!editing));

  saveBtn.addEventListener('click', async () => {
    if (!ctx.sessionId) {
      statusEl.textContent = 'Error: Missing session ID';
      return;
    }
    saveBtn.disabled = true;
    statusEl.textContent = 'Saving…';
    try {
      const html = '<!doctype html>\n' + document.documentElement.outerHTML;
      const saveUrl = resolveApiUrl(`/save-report/${ctx.sessionId}/${encodeURIComponent(ctx.filename || 'report.html')}`);
      const res = await fetch(saveUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ html }),
      });
      const data = await res.json();
      statusEl.textContent = data.ok ? 'Saved ✓' : `Error: ${data.error || 'unknown'}`;
    } catch (e) {
      statusEl.textContent = `Error: ${e.message}`;
    }
    saveBtn.disabled = false;
    setTimeout(() => {
      statusEl.textContent = '';
    }, 3000);
  });


  // ─── Format Toolbar Logic ─────────────────────────
  const formatTools = document.getElementById('format-tools');

  function isInsideEditableContainer(node) {
    return !!(node && node.closest && node.closest('.container[contenteditable="true"]'));
  }

  // The page's own selection collapses when focus moves to a toolbar control
  // (a <select> or <input type="color">), so remember the last real range made
  // inside the editable content and restore it before running a command.
  document.addEventListener('selectionchange', () => {
    const sel = window.getSelection();
    if (sel && sel.rangeCount > 0) {
      const range = sel.getRangeAt(0);
      if (isInsideEditableContainer(range.commonAncestorContainer)) {
        savedRange = range.cloneRange();
      }
    }
  });

  function restoreSelection() {
    if (!savedRange) return null;
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(savedRange);
    return sel;
  }

  // Wrap the current selection in a <span> carrying the given inline styles.
  // Used for controls execCommand has no clean equivalent for (font size, border).
  function wrapSelectionWithStyle(styleObj) {
    const sel = restoreSelection();
    if (!sel || sel.rangeCount === 0 || sel.isCollapsed) return;
    const range = sel.getRangeAt(0);
    const span = document.createElement('span');
    Object.assign(span.style, styleObj);
    const frag = range.extractContents();
    span.appendChild(frag);
    range.insertNode(span);
    sel.removeAllRanges();
    const newRange = document.createRange();
    newRange.selectNodeContents(span);
    sel.addRange(newRange);
    savedRange = newRange.cloneRange();
  }

  document.querySelectorAll('.format-btn[data-command]').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      restoreSelection();
      document.execCommand(btn.dataset.command, false, null);
    });
  });

  const fontFamilySelect = document.getElementById('font-family-select');
  fontFamilySelect.addEventListener('change', () => {
    if (!fontFamilySelect.value) return;
    restoreSelection();
    document.execCommand('fontName', false, fontFamilySelect.value);
    fontFamilySelect.value = '';
  });

  const fontSizeSelect = document.getElementById('font-size-select');
  fontSizeSelect.addEventListener('change', () => {
    if (!fontSizeSelect.value) return;
    wrapSelectionWithStyle({ fontSize: fontSizeSelect.value + 'px' });
    fontSizeSelect.value = '';
  });

  const textColorInput = document.getElementById('text-color-input');
  textColorInput.addEventListener('input', () => {
    restoreSelection();
    document.execCommand('foreColor', false, textColorInput.value);
  });

  const highlightColorInput = document.getElementById('highlight-color-input');
  highlightColorInput.addEventListener('input', () => {
    restoreSelection();
    if (!document.execCommand('hiliteColor', false, highlightColorInput.value)) {
      document.execCommand('backColor', false, highlightColorInput.value);
    }
  });

  const borderStyleSelect = document.getElementById('border-style-select');
  const borderColorInput = document.getElementById('border-color-input');
  document.getElementById('apply-border-btn').addEventListener('click', (e) => {
    e.preventDefault();
    const style = borderStyleSelect.value || '1px solid';
    if (style === 'none') {
      wrapSelectionWithStyle({ border: 'none' });
      return;
    }
    wrapSelectionWithStyle({
      border: `${style} ${borderColorInput.value}`,
      borderRadius: '4px',
      padding: '2px 6px',
      display: 'inline-block',
    });
  });

  document.getElementById('clear-format-btn').addEventListener('click', (e) => {
    e.preventDefault();
    restoreSelection();
    document.execCommand('removeFormat', false, null);
  });

  // Tab / Shift+Tab inside a list nests/un-nests it; inside a plain paragraph
  // it indents/outdents the block. Without this, Tab just moves focus away.
  document.addEventListener('keydown', (e) => {
    if (!editing || e.key !== 'Tab') return;
    if (!isInsideEditableContainer(document.activeElement)) return;
    e.preventDefault();
    document.execCommand(e.shiftKey ? 'outdent' : 'indent', false, null);
  });

  setEditing(false);

  // ───────────────────────── Per-section AI insights ─────────────────────────

  const CLASS_COLORS = {
    excellent: '#10b981',
    healthy: '#3b82f6',
    opportunity: '#f59e0b',
    watch: '#ef4444',
    // legacy fallbacks
    warning: '#f59e0b',
    critical: '#ef4444',
  };
  const PRIORITY_COLORS = { high: '#ef4444', medium: '#f59e0b', low: '#10b981' };
  const safeVal = (v) => (v != null && v !== 'undefined' && String(v).trim() !== '') ? String(v) : '—';

  function renderCollapsible(id, icon, title, contentHtml, defaultOpen) {
    return `
    <div class="ai-section" data-section-id="${id}">
      <button type="button" class="ai-section-toggle ${defaultOpen ? 'is-open' : ''}" data-target="${id}">
        <span class="ai-section-icon">${icon}</span>
        <span class="ai-section-label">${title}</span>
        <span class="ai-section-chevron">&#9662;</span>
      </button>
      <div class="ai-section-body ${defaultOpen ? 'is-open' : ''}" id="ai-body-${id}">
        ${contentHtml}
      </div>
    </div>`;
  }

  function renderSummarySection(ps) {
    if (!ps) return '';
    const patternsHtml = (ps.patterns || []).map(p => `
      <div class="ai-pattern-card">
        <div class="ai-pattern-name">&#9670; ${escapeHtml(p.pattern)}</div>
        <div class="ai-pattern-desc">${escapeHtml(p.description)}</div>
      </div>
    `).join('');

    return `
      <div class="ai-summary-narrative">${escapeHtml(ps.narrative || '')}</div>
      ${patternsHtml ? `
        <div class="ai-patterns-wrap">
          <div class="ai-sub-label">Identified Patterns &amp; Behaviours</div>
          ${patternsHtml}
        </div>
      ` : ''}
    `;
  }

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

  window.filterTable = function(inputEl) {
    const targetId = inputEl.getAttribute('data-table-target');
    const query = inputEl.value.toLowerCase().trim();
    let table = targetId ? document.getElementById(targetId) : null;
    if (!table) {
      const card = inputEl.closest('.table-header-card');
      if (card && card.nextElementSibling) {
        table = card.nextElementSibling.querySelector('table');
      }
    }
    if (!table) return;
    const rows = table.querySelectorAll('tbody tr');
    rows.forEach(row => {
      const text = row.textContent.toLowerCase();
      row.style.display = text.includes(query) ? '' : 'none';
    });
  };

  function renderResult(result) {
    if (!result) return '';
    const ps = result.performance_summary || {};
    const insights = result.key_insights || result.insights || [];
    const recs = result.recommendations || [];
    const narrative = escapeHtml(ps.narrative || ps.title || 'Executive Analysis');

    const itemsHtml = insights.slice(0, 4).map(ins => `
      <div class="ai-synthesis-item">
        <span class="ai-synthesis-bullet">&#9670;</span>
        <div><strong>${escapeHtml(ins.title || '')}:</strong> ${escapeHtml(ins.text || '')}</div>
      </div>
    `).join('');

    return `
      <div class="ai-executive-synthesis-card">
        <div class="ai-synthesis-header">
          <span class="ai-synthesis-badge">&#10024; AI Executive Synthesis</span>
          <h3 class="ai-synthesis-title">${escapeHtml(ps.title || 'Strategic Performance Diagnosis')}</h3>
        </div>
        <div class="ai-synthesis-narrative">${narrative}</div>
        ${itemsHtml ? `<div class="ai-synthesis-grid">${itemsHtml}</div>` : ''}
      </div>`;
  }

  // ─── Toggle collapsible sections ─────────────────────────
  document.addEventListener('click', (e) => {
    const toggle = e.target.closest('.ai-section-toggle');
    if (!toggle) return;
    const target = toggle.dataset.target;
    const body = document.getElementById('ai-body-' + target);
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

  // ─── Inject V2 CSS ─────────────────────────
  const styleEl = document.createElement('style');
  styleEl.textContent = `
/* ───────────────────────── AI Insights V2 ───────────────────────── */

.editor-tools-left { display: flex; gap: 8px; align-items: center; }
.editor-format-tools { display: flex; gap: 10px; align-items: center; padding-left: 10px; margin-left: 4px; border-left: 1px solid var(--border); flex-wrap: wrap; row-gap: 6px; }
.fmt-group { display: flex; gap: 3px; align-items: center; padding: 2px 6px; background: var(--bg-inset); border: 1px solid var(--border); border-radius: 7px; }
.editor-toolbar .format-btn { background: transparent; border: 1px solid transparent; min-width: 26px; height: 26px; padding: 0 6px; border-radius: 4px; display: flex; align-items: center; justify-content: center; cursor: pointer; color: var(--text); font-size: 12px; font-weight: 500; white-space: nowrap; }
.editor-toolbar .format-btn:hover { background: var(--bg-card); border-color: var(--border); transform: none; }
.fmt-select {
  height: 26px; border: 1px solid var(--border); border-radius: 4px; background: var(--bg-card);
  color: var(--text); font-size: 11.5px; padding: 0 4px; cursor: pointer; max-width: 108px;
}
.fmt-select-sm { max-width: 68px; }
.fmt-color-swatch {
  position: relative; display: flex; align-items: center; justify-content: center;
  width: 26px; height: 26px; border-radius: 4px; border: 1px solid var(--border);
  background: var(--bg-card); cursor: pointer; font-size: 11px; font-weight: 700; color: var(--text-muted);
  overflow: hidden;
}
.fmt-color-swatch:hover { border-color: var(--border-strong); }
.fmt-color-swatch input[type="color"] {
  position: absolute; inset: 0; opacity: 0; cursor: pointer; border: none; padding: 0;
}


.ai-info-btn { width: 28px; height: 28px; border-radius: 50%; background: var(--bg-card); border: 1px solid var(--border); color: var(--text-muted); font-family: var(--font-serif); font-style: italic; font-size: 14px; font-weight: 600; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; padding: 0; box-shadow: var(--shadow-sm); }
.ai-info-btn:hover { color: var(--primary); border-color: var(--primary); transform: scale(1.05); }
.ai-info-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.ai-info-btn .spinner { animation: ai-spin 1s linear infinite; font-style: normal; }
.ai-slot { min-height: 0; transition: all 0.3s ease; }

.ai-result-v2 { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 24px; position: relative; overflow: hidden; animation: ai-fade-in 400ms ease both; box-shadow: var(--shadow-sm); }
.ai-result-v2::before { content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 4px; background: linear-gradient(180deg, var(--accent), var(--primary)); }
.ai-result-header { display: flex; gap: 16px; margin-bottom: 24px; align-items: center; }
.ai-result-header-icon { font-size: 24px; }
.ai-result-header-title { font-size: 18px; font-weight: 700; color: var(--text); font-family: var(--font-serif); margin-bottom: 2px; }
.ai-result-header-sub { font-size: 13px; color: var(--text-muted); }

.ai-section { margin-bottom: 12px; border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; background: var(--bg-inset); }
.ai-section-toggle { width: 100%; display: flex; align-items: center; gap: 12px; padding: 14px 16px; background: transparent; border: none; cursor: pointer; text-align: left; transition: background 0.2s; }
.ai-section-toggle:hover { background: rgba(0,0,0,0.02); }
[data-theme='dark'] .ai-section-toggle:hover { background: rgba(255,255,255,0.02); }
.ai-section-icon { font-size: 16px; }
.ai-section-label { flex: 1; font-weight: 600; color: var(--text); font-size: 14px; }
.ai-section-chevron { font-size: 12px; color: var(--text-muted); transition: transform 0.2s; }
.ai-section-toggle.is-open .ai-section-chevron { transform: rotate(-180deg); }

.ai-section-body { padding: 0 16px; max-height: 0; overflow: hidden; opacity: 0; transition: max-height 0.3s ease, padding 0.3s ease, opacity 0.3s ease; }
.ai-section-body.is-open { max-height: 2000px; padding: 0 16px 16px 16px; opacity: 1; overflow: visible; }

.ai-summary-narrative { font-size: 14px; line-height: 1.6; color: var(--text); margin-bottom: 16px; font-weight: 500; }
.ai-patterns-wrap { margin-top: 16px; padding-top: 16px; border-top: 1px dashed var(--border); }
.ai-sub-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 700; color: var(--text-muted); margin-bottom: 12px; }
.ai-pattern-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); padding: 12px; margin-bottom: 8px; border-left: 3px solid var(--primary); }
.ai-pattern-name { font-weight: 600; font-size: 13px; color: var(--text); margin-bottom: 4px; display: flex; align-items: center; gap: 6px; }
.ai-pattern-desc { font-size: 12.5px; line-height: 1.5; color: var(--text-muted); }

.ai-evidence { font-size: 11.5px; color: var(--text-muted); margin-top: 8px; padding: 6px 10px; background: rgba(0,0,0,0.02); border-radius: 4px; display: inline-block; }
[data-theme='dark'] .ai-evidence { background: rgba(255,255,255,0.03); }
.ai-evidence-label { font-weight: 600; color: var(--text); }

.ai-highlights-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 768px) { .ai-highlights-grid { grid-template-columns: 1fr; } }
.ai-highlight-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; border-left: 3px solid transparent; }
.ai-highlight-header { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.ai-highlight-icon { font-size: 12px; }
.ai-highlight-metric { font-size: 12px; font-weight: 600; color: var(--text-muted); flex: 1; text-transform: uppercase; letter-spacing: 0.02em; }
.ai-highlight-type-badge { font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 4px; text-transform: uppercase; letter-spacing: 0.02em; }
.ai-highlight-headline { font-size: 14px; font-weight: 600; color: var(--text); margin-bottom: 4px; line-height: 1.3; }
.ai-highlight-magnitude { font-size: 16px; font-weight: 700; font-family: var(--font-mono); margin-bottom: 8px; }
.ai-highlight-detail { font-size: 13px; line-height: 1.5; color: var(--text-muted); }

.ai-rec-card { display: flex; gap: 16px; padding: 16px; background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); margin-bottom: 12px; }
.ai-rec-num { flex-shrink: 0; width: 32px; height: 32px; background: var(--primary-soft); color: var(--primary); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 700; font-family: var(--font-mono); }
[data-theme='dark'] .ai-rec-num { background: var(--primary); color: white; }
.ai-rec-content { flex: 1; }
.ai-rec-title { font-size: 14px; font-weight: 600; color: var(--text); margin-bottom: 6px; }
.ai-rec-desc { font-size: 13px; line-height: 1.5; color: var(--text-muted); margin-bottom: 12px; }
.ai-rec-impact { font-size: 13px; color: var(--good); background: var(--good-soft); padding: 8px 12px; border-radius: 6px; margin-bottom: 12px; font-weight: 500; }
[data-theme='dark'] .ai-rec-impact { background: rgba(16, 185, 129, 0.1); }
.ai-rec-impact-label { font-weight: 700; margin-right: 4px; }
.ai-rec-meta { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
`;
  document.head.appendChild(styleEl);
  // ───────────────────────── Presenter View ─────────────────────────
  if (typeof io !== 'undefined') {
    const pBar = document.createElement('div');
    pBar.className = 'presenter-bar';
    pBar.innerHTML = `<div class="presenter-info"><span id="p-status">Presenter Mode Offline</span><span class="presenter-badge" id="p-code" style="display:none;"></span></div><div class="presenter-actions"><button type="button" class="presenter-btn" id="p-host-btn">Host</button><button type="button" class="presenter-btn" id="p-join-btn">Join</button><button type="button" class="presenter-btn" id="p-leave-btn" style="display:none;">Leave</button></div>`;
    document.body.appendChild(pBar);

    const pOverlay = document.createElement('div');
    pOverlay.className = 'viewer-overlay';
    document.body.appendChild(pOverlay);

    const pModal = document.createElement('div');
    pModal.className = 'presenter-modal';
    pModal.innerHTML = `<div class="presenter-modal-title">Join Session</div><input type="text" id="p-input" placeholder="6-digit code" maxlength="6"><div class="presenter-modal-actions"><button class="presenter-btn" id="p-cancel">Cancel</button><button class="presenter-btn" id="p-submit">Join</button></div>`;
    document.body.appendChild(pModal);

    const socket = io(ctx.serverUrl || window.location.origin);
    let myRole = 'idle';
    let myCode = null;

    socket.on('room_state', (state) => {
      document.getElementById('p-status').textContent = myRole === 'presenter' ? `Broadcasting (${state.viewers} viewers)` : 'Viewing Host Screen';
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
      if (myRole === 'presenter' && e.isTrusted) {
        socket.emit('presenter_event', { type: 'click', x: e.clientX, y: e.clientY });
      }
    });

    function joinSession(role, code) {
      myRole = role;
      myCode = code;
      socket.emit('join_room', { role, code, reportUrl: window.location.pathname });
      
      document.getElementById('p-code').textContent = 'Code: ' + code;
      document.getElementById('p-code').style.display = 'inline-block';
      document.getElementById('p-host-btn').style.display = 'none';
      document.getElementById('p-join-btn').style.display = 'none';
      document.getElementById('p-leave-btn').style.display = 'inline-block';
      pBar.classList.add('is-active');

      if (role === 'viewer') {
        document.body.classList.add('viewer-locked');
      }
    }

    document.getElementById('p-host-btn').addEventListener('click', () => {
      const code = Math.floor(100000 + Math.random() * 900000).toString();
      joinSession('presenter', code);
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

    document.getElementById('p-leave-btn').addEventListener('click', () => {
      socket.disconnect();
      socket.connect();
      myRole = 'idle';
      myCode = null;
      document.getElementById('p-status').textContent = 'Presenter Mode Offline';
      document.getElementById('p-code').style.display = 'none';
      document.getElementById('p-host-btn').style.display = 'inline-block';
      document.getElementById('p-join-btn').style.display = 'inline-block';
      document.getElementById('p-leave-btn').style.display = 'none';
      pBar.classList.remove('is-active');
      document.body.classList.remove('viewer-locked');
    });

    const urlParams = new URLSearchParams(window.location.search);
    const initCode = urlParams.get('roomCode');
    if (initCode && initCode.length === 6) {
      joinSession('viewer', initCode);
    }
  }
})();
