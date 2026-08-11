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
  const FONT_SIZES = [9, 10, 11, 12, 13, 14, 16, 18, 20, 24, 28, 32, 40, 48, 56];
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
  toolbar.id = 'editor-toolbar';
  toolbar.innerHTML =
    '<div class="editor-tools-left">' +
      '<button type="button" id="edit-toggle-btn">&#9998; Edit</button>' +
      '<button type="button" id="save-btn" disabled>&#128190; Save</button>' +
      '<button type="button" id="toolbar-collapse-btn" class="format-btn" title="Collapse Toolbar">&#9650; Collapse</button>' +
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
        `<select id="line-height-select" class="fmt-select fmt-select-sm" title="Line height">` +
          `<option value="">Line</option>` +
          `<option value="1.1">1.1</option>` +
          `<option value="1.25">1.25</option>` +
          `<option value="1.5">1.5</option>` +
          `<option value="1.75">1.75</option>` +
          `<option value="2">2.0</option>` +
        `</select>` +
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
        `<button type="button" id="insert-image-btn" class="format-btn" title="Insert Image">&#128444; Image</button>` +
        `<select id="insert-shape-select" class="fmt-select" title="Insert Visual Shape">` +
          `<option value="">+ Shape</option>` +
          `<option value="callout">Callout Box</option>` +
          `<option value="badge">Stat Badge</option>` +
          `<option value="card">Highlight Card</option>` +
          `<option value="divider">Divider Line</option>` +
        `</select>` +
      '</div>' +

      '<div class="fmt-group">' +
        `<button type="button" id="add-global-section-btn" class="format-btn" title="Add New Section">+ Section</button>` +
        `<button type="button" id="clear-format-btn" class="format-btn" title="Clear formatting">Clear</button>` +
      '</div>' +

    '</div>';
  document.body.appendChild(toolbar);

  const editBtn = document.getElementById('edit-toggle-btn');
  const saveBtn = document.getElementById('save-btn');
  const collapseBtn = document.getElementById('toolbar-collapse-btn');
  const statusEl = document.getElementById('editor-status');
  let editing = false;
  let isToolbarCollapsed = false;
  let savedRange = null;

  collapseBtn.addEventListener('click', () => {
    isToolbarCollapsed = !isToolbarCollapsed;
    toolbar.classList.toggle('is-collapsed', isToolbarCollapsed);
    collapseBtn.innerHTML = isToolbarCollapsed ? '&#9660; Expand' : '&#9650; Collapse';
    if (formatTools && editing) {
      formatTools.style.display = isToolbarCollapsed ? 'none' : 'flex';
    }
  });

  function renderSectionControls() {
    document.querySelectorAll('.report-section').forEach((sec) => {
      let bar = sec.querySelector('.section-edit-bar');
      if (editing) {
        if (!bar) {
          bar = document.createElement('div');
          bar.className = 'section-edit-bar';
          bar.setAttribute('contenteditable', 'false');
          bar.innerHTML =
            '<span class="sec-bar-title">&#9776; Section Controls</span>' +
            '<button type="button" class="sec-bar-btn move-up-btn" title="Move Section Up">&#8593; Move Up</button>' +
            '<button type="button" class="sec-bar-btn move-down-btn" title="Move Section Down">&#8595; Move Down</button>' +
            '<button type="button" class="sec-bar-btn add-sec-btn" title="Add Section Below">+ Add Section</button>' +
            '<button type="button" class="sec-bar-btn del-sec-btn danger" title="Delete Section">&#128465; Delete</button>';
          sec.insertBefore(bar, sec.firstChild);

          bar.querySelector('.move-up-btn').addEventListener('click', (e) => {
            e.preventDefault();
            const prev = sec.previousElementSibling;
            if (prev && prev.classList.contains('report-section')) {
              sec.parentNode.insertBefore(sec, prev);
            }
          });

          bar.querySelector('.move-down-btn').addEventListener('click', (e) => {
            e.preventDefault();
            const next = sec.nextElementSibling;
            if (next && next.classList.contains('report-section')) {
              sec.parentNode.insertBefore(next, sec);
            }
          });

          bar.querySelector('.add-sec-btn').addEventListener('click', (e) => {
            e.preventDefault();
            createNewSection(sec);
          });

          bar.querySelector('.del-sec-btn').addEventListener('click', (e) => {
            e.preventDefault();
            if (confirm('Are you sure you want to delete this section?')) {
              sec.remove();
            }
          });
        }
        bar.style.display = 'flex';
      } else if (bar) {
        bar.style.display = 'none';
      }
    });
  }

  function createNewSection(afterElem) {
    const titleText = prompt('Enter section title:', 'New Performance Section') || 'New Performance Section';
    const subText = prompt('Enter section deck/subtitle:', 'Detailed analysis and strategic recommendations.') || 'Detailed analysis and strategic recommendations.';

    const newSec = document.createElement('section');
    newSec.className = 'report-section custom-added-section';
    newSec.innerHTML =
      '<div class="container" contenteditable="true">' +
        '<div class="section-header">' +
          '<div class="eyebrow">CUSTOM SECTION</div>' +
          `<h2 class="section-title">${escapeHtml(titleText)}</h2>` +
          `<p class="section-deck">${escapeHtml(subText)}</p>` +
        '</div>' +
        '<div class="card" style="padding:24px; margin-top:20px; background:var(--bg-card); border:1px solid var(--border); border-radius:12px;">' +
          '<p>Click here to type your new section content, add tables, or insert images and visual shapes.</p>' +
        '</div>' +
      '</div>';

    if (afterElem && afterElem.parentNode) {
      afterElem.parentNode.insertBefore(newSec, afterElem.nextElementSibling);
    } else {
      const main = document.querySelector('main') || document.body;
      main.appendChild(newSec);
    }
    renderSectionControls();
  }

  document.getElementById('add-global-section-btn').addEventListener('click', (e) => {
    e.preventDefault();
    createNewSection(null);
  });

  function setEditing(on) {
    editing = on;
    document.documentElement.setAttribute('data-editing', on ? 'true' : 'false');
    document.querySelectorAll('.container').forEach((el) => {
      el.setAttribute('contenteditable', on ? 'true' : 'false');
    });
    editBtn.classList.toggle('is-active', on);
    editBtn.innerHTML = on ? '&#9998; Editing&hellip;' : '&#9998; Edit';
    saveBtn.disabled = !on;
    if (formatTools) formatTools.style.display = (on && !isToolbarCollapsed) ? 'flex' : 'none';
    renderSectionControls();
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

  const lineHeightSelect = document.getElementById('line-height-select');
  lineHeightSelect.addEventListener('change', () => {
    if (!lineHeightSelect.value) return;
    wrapSelectionWithStyle({ lineHeight: lineHeightSelect.value });
    lineHeightSelect.value = '';
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

  document.getElementById('insert-image-btn').addEventListener('click', (e) => {
    e.preventDefault();
    const url = prompt('Enter Image URL (or paste image web link):');
    if (url) {
      restoreSelection();
      document.execCommand('insertImage', false, url);
    }
  });

  const insertShapeSelect = document.getElementById('insert-shape-select');
  insertShapeSelect.addEventListener('change', () => {
    const shape = insertShapeSelect.value;
    if (!shape) return;
    restoreSelection();
    let html = '';
    if (shape === 'callout') {
      html = '<div class="report-callout" style="padding:16px 20px; background:var(--bg-inset, #f0f4f9); border-left:4px solid var(--primary, #0f2c5e); border-radius:8px; margin:16px 0;"><strong>💡 Key Takeaway:</strong> Type your custom callout text here.</div>';
    } else if (shape === 'badge') {
      html = '<span class="report-badge" style="display:inline-block; padding:4px 12px; background:var(--accent-soft, #e6f0ff); color:var(--primary, #0f2c5e); font-weight:700; border-radius:999px; font-size:12px;">★ Highlight Badge</span>';
    } else if (shape === 'card') {
      html = '<div class="report-card" style="padding:20px; border:1px solid var(--border, #e2e8f0); border-radius:12px; background:var(--bg-card, #ffffff); margin:16px 0;"><h4 style="margin:0 0 8px 0; font-size:16px;">Highlight Card Title</h4><p style="margin:0;">Add key details or descriptions inside this highlight card block.</p></div>';
    } else if (shape === 'divider') {
      html = '<hr style="border:none; border-top:2px dashed var(--border, #cbd5e1); margin:24px 0;" />';
    }
    if (html) {
      document.execCommand('insertHTML', false, html);
    }
    insertShapeSelect.value = '';
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
    const summaryTitle = (ps && ps.title) ? ps.title : 'Performance Overview';
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

.ai-result-v2 { background: linear-gradient(180deg, var(--bg-card), var(--bg-inset)); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 24px; position: relative; overflow: hidden; animation: ai-fade-in 400ms ease both; box-shadow: var(--shadow-sm); }
.ai-result-v2::before { content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 4px; background: linear-gradient(180deg, var(--accent), var(--primary)); }
.ai-result-header { display: flex; gap: 16px; margin-bottom: 20px; align-items: center; }
.ai-result-header-icon { font-size: 24px; }
.ai-result-header-title { font-size: 18px; font-weight: 700; color: var(--text); font-family: var(--font-serif); margin-bottom: 2px; }
.ai-result-header-sub { font-size: 13px; color: var(--text-muted); }

.ai-section { margin-bottom: 0; border: none; border-top: 1px solid var(--border); border-radius: 0; overflow: visible; background: transparent; }
.ai-section-toggle { width: 100%; display: flex; align-items: center; gap: 12px; padding: 14px 16px; background: transparent; border: none; cursor: pointer; text-align: left; transition: background 0.2s; border-radius: 12px; }
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

body { padding-top: 0 !important; }
.topbar { top: 0 !important; }
section.report-section .section-hero,
details.appendix-details > summary.section-hero,
.section-hero {
  position: relative !important;
  top: auto !important;
  z-index: auto !important;
}
.section-hero.is-stuck {
  padding-top: inherit !important;
  padding-bottom: inherit !important;
}
.section-hero.is-stuck .section-title { font-size: inherit !important; }
.section-hero.is-stuck .section-deck { display: block !important; }
.hero-kpi-grid { display: grid !important; grid-template-columns: repeat(5, minmax(0, 1fr)) !important; grid-auto-rows: minmax(0, auto) !important; gap: 12px !important; align-items: stretch; }
.kpi-card {
  position: relative !important;
  overflow: hidden !important;
  min-height: 136px !important;
  padding: 16px 16px 14px !important;
  border: 1px solid rgba(255,255,255,0.5) !important;
  border-radius: 22px !important;
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--bg-card) 96%, white 4%), var(--bg-card)) padding-box,
    linear-gradient(180deg, rgba(255,255,255,0.55), rgba(255,255,255,0.08)) border-box !important;
  box-shadow: 0 18px 36px -14px rgba(15,23,42,0.16), 0 2px 8px rgba(15,23,42,0.08), inset 0 1px 0 rgba(255,255,255,0.55) !important;
  transform: none !important;
}
[data-theme='dark'] .kpi-card {
  border-color: rgba(255,255,255,0.08) !important;
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--bg-card) 94%, white 6%), var(--bg-card)) padding-box,
    linear-gradient(180deg, rgba(255,255,255,0.14), rgba(255,255,255,0.03)) border-box !important;
  box-shadow: 0 25px 50px -12px rgba(0,0,0,0.42), 0 2px 8px rgba(0,0,0,0.22), inset 0 1px 0 rgba(255,255,255,0.06) !important;
}
.kpi-card::before {
  content: '' !important;
  position: absolute !important;
  inset: 1px 1px auto 1px !important;
  height: 48% !important;
  border-radius: 21px 21px 14px 14px !important;
  background: linear-gradient(180deg, rgba(255,255,255,0.42), rgba(255,255,255,0)) !important;
  opacity: 0.8 !important;
  pointer-events: none !important;
}
.kpi-card::after {
  content: '' !important;
  position: absolute !important;
  right: -28px !important;
  top: -28px !important;
  width: 96px !important;
  height: 96px !important;
  border-radius: 999px !important;
  background: radial-gradient(circle, color-mix(in srgb, var(--accent) 40%, transparent), transparent 68%) !important;
  opacity: 0.42 !important;
  pointer-events: none !important;
}
.kpi-label, .kpi-value, .kpi-sub, .kpi-trends, .kpi-baseline { position: relative !important; z-index: 1 !important; }
.kpi-label { font-size: 13px !important; font-weight: 700 !important; letter-spacing: 0.025em !important; text-transform: none !important; color: var(--text-muted) !important; margin-bottom: 6px !important; }
.kpi-label::before { display: none !important; }
.kpi-value { font-size: clamp(24px, 2.3vw, 32px) !important; font-weight: 650 !important; line-height: 1 !important; letter-spacing: 0 !important; margin-bottom: 8px !important; }
.kpi-sub { font-size: 12.5px !important; color: var(--text-muted) !important; margin-bottom: 6px !important; }
.kpi-trends { display: flex !important; gap: 8px !important; margin-bottom: 6px !important; flex-wrap: wrap !important; align-items: center !important; }
.kpi-trend {
  display: inline-flex !important;
  align-items: center !important;
  gap: 6px !important;
  padding: 4px 7px !important;
  border: 1px solid var(--border) !important;
  border-radius: 999px !important;
  background: color-mix(in srgb, var(--bg) 46%, transparent) !important;
  box-shadow: 0 1px 3px rgba(15,23,42,0.05) !important;
}
.kpi-trend .trend-label { color: var(--text-muted) !important; font-weight: 800 !important; letter-spacing: 0.04em !important; text-transform: uppercase !important; }
.kpi-trend .badge { border-radius: 999px !important; padding: 2px 7px !important; font-weight: 900 !important; }
.kpi-baseline {
  display: inline-flex !important;
  width: fit-content !important;
  max-width: 100% !important;
  align-items: center !important;
  gap: 8px !important;
  padding: 5px 9px !important;
  border: 1px solid var(--border) !important;
  border-radius: 999px !important;
  background: color-mix(in srgb, var(--bg) 48%, transparent) !important;
  color: var(--text) !important;
  box-shadow: 0 1px 3px rgba(15,23,42,0.05), 0 4px 12px rgba(15,23,42,0.04) !important;
  white-space: normal !important;
}
.kpi-baseline::before { content: none !important; }
.kpi-card .kpi-chart {
  position: relative !important;
  z-index: 1 !important;
  width: calc(100% + 32px) !important;
  height: 48px !important;
  margin: 4px -16px 0 !important;
}
.kpi-card .kpi-chart svg {
  width: 100% !important;
  height: 100% !important;
  display: block !important;
}
.kpi-card .kpi-chart-grid {
  stroke: var(--border);
  stroke-width: 1;
  stroke-dasharray: 3 5;
  opacity: 0.58;
}
.kpi-card .kpi-chart-area { fill: color-mix(in srgb, var(--primary) 24%, transparent); }
.kpi-card .kpi-chart-line { fill: none; stroke: var(--primary); stroke-width: 3; stroke-linecap: round; stroke-linejoin: round; }
.kpi-card .kpi-chart-line { stroke-dasharray: 260; stroke-dashoffset: 260; animation: kpiDraw 900ms ease forwards; }
.kpi-card .kpi-chart-area { opacity: 0; animation: kpiFade 700ms ease 220ms forwards; }
.kpi-card .kpi-chart-dot { fill: var(--bg-card); stroke: var(--primary); stroke-width: 3; filter: drop-shadow(0 3px 7px rgba(79,70,229,0.26)); }
.kpi-card .kpi-chart-tip {
  position: absolute !important;
  right: 18px !important;
  top: 2px !important;
  padding: 5px 9px !important;
  border-radius: 10px !important;
  background: color-mix(in srgb, var(--text) 88%, transparent) !important;
  color: var(--bg-card) !important;
  font: 800 11px var(--font-sans) !important;
  box-shadow: 0 4px 16px rgba(0,0,0,0.2) !important;
}
.kpi-card .kpi-illustration {
  position: absolute !important;
  right: 12px !important;
  top: 14px !important;
  z-index: 1 !important;
  width: 48px !important;
  height: 44px !important;
  opacity: 0.82 !important;
  pointer-events: none !important;
}
.kpi-card .kpi-illustration svg { width: 100%; height: 100%; display: block; }
.kpi-hover-tooltip, .kpi-drill {
  position: relative !important;
  z-index: 2 !important;
  border: 1px solid var(--border) !important;
  border-radius: 14px !important;
  background: color-mix(in srgb, var(--bg-card) 96%, transparent) !important;
  box-shadow: 0 14px 32px rgba(15,23,42,0.12) !important;
}
.kpi-hover-tooltip {
  position: absolute !important;
  left: 16px !important;
  right: 16px !important;
  bottom: 14px !important;
  padding: 9px 10px !important;
  font-size: 11.5px !important;
  color: var(--text-muted) !important;
  opacity: 0 !important;
  transform: translateY(6px) !important;
  transition: opacity 160ms ease, transform 160ms ease !important;
  pointer-events: none !important;
}
.kpi-card:hover .kpi-hover-tooltip { opacity: 1 !important; transform: translateY(0) !important; }
.kpi-card.is-drilled .kpi-drill { display: grid !important; }
.kpi-drill {
  display: none !important;
  grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
  gap: 8px !important;
  margin-top: 10px !important;
  padding: 10px !important;
}
.kpi-drill-item span { display: block !important; font-size: 10px !important; color: var(--text-muted) !important; text-transform: uppercase !important; letter-spacing: 0.06em !important; }
.kpi-drill-item strong { display: block !important; margin-top: 2px !important; font-size: 12px !important; color: var(--text) !important; }
@keyframes kpiDraw { to { stroke-dashoffset: 0; } }
@keyframes kpiFade { to { opacity: 1; } }
@media (max-width: 1500px) { .hero-kpi-grid { grid-template-columns: repeat(5, minmax(180px, 1fr)) !important; } }
.presenter-bar {
  position: fixed;
  right: 14px;
  bottom: 14px;
  z-index: 3200;
  display: flex;
  align-items: center;
  gap: 8px;
  max-width: calc(100vw - 28px);
  padding: 8px;
  background: color-mix(in srgb, var(--bg-card) 92%, transparent);
  border: 1px solid var(--border);
  border-radius: 999px;
  box-shadow: var(--shadow-lg);
  backdrop-filter: blur(10px);
}
.presenter-bar.is-active {
  left: 14px;
  right: 14px;
  bottom: 14px;
  border-radius: 14px;
  justify-content: space-between;
}
.presenter-info { display: none; align-items: center; gap: 8px; color: var(--text); font-size: 12px; font-weight: 700; }
.presenter-bar.is-active .presenter-info { display: flex; }
.presenter-badge { display: inline-flex; align-items: center; min-height: 24px; padding: 2px 8px; border-radius: 999px; background: var(--primary-soft); color: var(--primary); font-family: var(--font-mono); font-weight: 800; }
.presenter-actions, .annotation-tools { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.annotation-tools { display: none; }
.presenter-bar.is-active .annotation-tools { display: flex; }
.presenter-btn, .annotation-btn {
  min-height: 30px;
  padding: 6px 10px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--bg-card);
  color: var(--text);
  cursor: pointer;
  font: 800 12px var(--font-sans);
}
.presenter-btn:hover, .annotation-btn:hover, .annotation-btn.is-active { border-color: var(--primary); color: var(--primary); background: var(--primary-soft); }
.annotation-color {
  width: 30px;
  min-width: 30px;
  padding: 0;
  color: transparent;
  border-color: var(--border-strong);
}
.annotation-color[data-color="#fff176"] { background: #fff176; }
.annotation-color[data-color="#a7f3d0"] { background: #a7f3d0; }
.annotation-color[data-color="#fbcfe8"] { background: #fbcfe8; }
.annotation-mark {
  border-radius: 4px;
  padding: 0 2px;
  background: var(--annotation-color, #fff176);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--annotation-color, #fff176) 35%, transparent);
}
.annotation-tooltip {
  position: relative;
  border-bottom: 2px dotted var(--primary);
  background: rgba(245, 197, 24, 0.22);
  cursor: help;
}
.annotation-tooltip:hover::after {
  content: attr(data-note);
  position: absolute;
  left: 0;
  bottom: calc(100% + 8px);
  z-index: 5000;
  width: max-content;
  max-width: 280px;
  padding: 8px 10px;
  border-radius: 8px;
  background: #111827;
  color: #fff;
  font: 700 12px var(--font-sans);
  line-height: 1.35;
  box-shadow: var(--shadow-lg);
}
.annotation-canvas {
  position: fixed;
  inset: 0;
  z-index: 3000;
  pointer-events: none;
}
body.annotation-draw-mode .annotation-canvas,
body.annotation-erase-mode .annotation-canvas {
  pointer-events: auto;
  cursor: crosshair;
}
`;
  document.head.appendChild(styleEl);

  function decorateMetricCards() {
    const paths = [
      'M10 66 C32 54 38 30 58 38 C78 46 78 18 100 26 C122 34 126 16 146 24',
      'M10 58 C34 66 40 30 62 34 C84 38 84 58 104 46 C124 34 130 26 146 20',
      'M10 62 C30 44 44 48 62 36 C82 22 90 52 110 40 C130 28 136 20 146 26',
      'M10 54 C28 30 44 34 60 44 C76 54 86 22 106 28 C126 34 132 52 146 38'
    ];
    const icons = [
      '<path d="M22 58h76M34 44h52M46 30h28" stroke="var(--primary)" stroke-width="7" stroke-linecap="round"/><circle cx="84" cy="28" r="16" fill="var(--accent)"/><path d="M78 28h12M84 22v12" stroke="var(--bg-card)" stroke-width="4" stroke-linecap="round"/>',
      '<path d="M30 70 52 44l17 15 25-32" fill="none" stroke="var(--primary)" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/><path d="M83 27h11v11" fill="none" stroke="var(--primary)" stroke-width="7" stroke-linecap="round"/>',
      '<circle cx="58" cy="50" r="28" fill="var(--accent)" opacity=".25"/><path d="M58 28v22l18 12" fill="none" stroke="var(--primary)" stroke-width="8" stroke-linecap="round"/>',
      '<rect x="30" y="28" width="64" height="50" rx="14" fill="var(--accent)" opacity=".22"/><path d="M42 62h40M42 48h30M42 36h18" stroke="var(--primary)" stroke-width="7" stroke-linecap="round"/>',
      '<path d="M38 74c5-30 18-46 38-50 10 17 8 34-4 50" fill="none" stroke="var(--primary)" stroke-width="8" stroke-linecap="round"/><circle cx="76" cy="24" r="12" fill="var(--accent)"/>',
      '<path d="M30 34h60v42H30z" fill="var(--accent)" opacity=".2"/><path d="M40 66V48M58 66V36M76 66V54" stroke="var(--primary)" stroke-width="8" stroke-linecap="round"/>',
      '<path d="M28 54c18-24 42-24 64 0-22 24-46 24-64 0Z" fill="var(--accent)" opacity=".2"/><circle cx="60" cy="54" r="14" fill="none" stroke="var(--primary)" stroke-width="7"/>',
      '<path d="M34 70h52M42 58h36M50 46h20" stroke="var(--primary)" stroke-width="7" stroke-linecap="round"/><path d="M36 26h48l10 18H26z" fill="var(--accent)" opacity=".25"/>',
      '<path d="M62 24 82 62H42z" fill="var(--accent)" opacity=".3"/><path d="M62 34v18M62 64v2" stroke="var(--primary)" stroke-width="7" stroke-linecap="round"/>',
      '<circle cx="60" cy="50" r="30" fill="none" stroke="var(--primary)" stroke-width="8"/><path d="M60 50 78 34M60 50 46 66" stroke="var(--accent)" stroke-width="7" stroke-linecap="round"/>'
    ];
    const grid = document.querySelector('.hero-kpi-grid');
    if (grid) {
      const labels = ['Active Base', 'Avg Ticket', 'Peak Fill', 'Lead Quality', 'Retention Risk', 'Revenue / Visit', 'Trial Velocity', 'Capacity Gap', 'Discount Guard', 'Next Action'];
      while (grid.querySelectorAll('.kpi-card').length < 10) {
        const idx = grid.querySelectorAll('.kpi-card').length;
        const extra = document.createElement('div');
        extra.className = 'kpi-card kpi-card-supplemental';
        extra.innerHTML = `<div class="kpi-label">${labels[idx]}</div><div class="kpi-value">—</div><div class="kpi-sub">Supporting analytics slot</div><div class="kpi-trends"><span class="kpi-trend"><span class="trend-label">View</span> <span class="badge neutral">Drill</span></span></div><div class="kpi-baseline">Click for context</div>`;
        grid.appendChild(extra);
      }
    }
    document.querySelectorAll('.kpi-card').forEach((card, index) => {
      if (card.querySelector('.kpi-chart')) return;
      const path = paths[index % paths.length];
      const label = card.querySelector('.kpi-baseline')?.textContent?.trim() || card.querySelector('.kpi-value')?.textContent?.trim() || '';
      const metricName = card.querySelector('.kpi-label')?.textContent?.trim() || 'Metric';
      const metricValue = card.querySelector('.kpi-value')?.textContent?.trim() || '';
      const metricSub = card.querySelector('.kpi-sub')?.textContent?.trim() || '';
      const trends = Array.from(card.querySelectorAll('.kpi-trend')).map((node) => node.textContent.trim());
      const chart = document.createElement('div');
      chart.className = 'kpi-chart';
      chart.innerHTML = `
        <svg viewBox="0 0 156 82" aria-hidden="true" focusable="false">
          <defs>
            <linearGradient id="kpiArea${index}" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="currentColor" stop-opacity="0.25"></stop>
              <stop offset="62%" stop-color="currentColor" stop-opacity="0.09"></stop>
              <stop offset="100%" stop-color="currentColor" stop-opacity="0"></stop>
            </linearGradient>
          </defs>
          <line class="kpi-chart-grid" x1="10" y1="18" x2="146" y2="18"></line>
          <line class="kpi-chart-grid" x1="10" y1="42" x2="146" y2="42"></line>
          <line class="kpi-chart-grid" x1="10" y1="66" x2="146" y2="66"></line>
          <path class="kpi-chart-area" d="${path} L146 72 L10 72 Z"></path>
          <path class="kpi-chart-line" d="${path}"></path>
          <circle class="kpi-chart-dot" cx="106" cy="${index % 2 ? 46 : 28}" r="6"></circle>
        </svg>
        <span class="kpi-chart-tip">${escapeHtml(label.slice(0, 16))}</span>`;
      const illustration = document.createElement('div');
      illustration.className = 'kpi-illustration';
      illustration.innerHTML = `
        <svg viewBox="0 0 120 96" aria-hidden="true" focusable="false">
          <path d="M24 48c12-25 45-36 70-20 19 12 24 39 8 55-17 17-50 13-70-5-9-8-13-19-8-30Z" fill="var(--accent)" opacity=".18"/>
          ${icons[index % icons.length]}
        </svg>`;
      const baseline = card.querySelector('.kpi-baseline');
      if (baseline) card.insertBefore(chart, baseline);
      else card.appendChild(chart);
      card.appendChild(illustration);
      const tooltip = document.createElement('div');
      tooltip.className = 'kpi-hover-tooltip';
      tooltip.textContent = `Click for drill-down: ${metricName} · ${metricValue}${metricSub ? ` · ${metricSub}` : ''}`;
      card.appendChild(tooltip);
      const drill = document.createElement('div');
      drill.className = 'kpi-drill';
      drill.innerHTML =
        `<div class="kpi-drill-item"><span>Metric</span><strong>${escapeHtml(metricName)}</strong></div>` +
        `<div class="kpi-drill-item"><span>Current</span><strong>${escapeHtml(metricValue)}</strong></div>` +
        `<div class="kpi-drill-item"><span>Analytics</span><strong>${escapeHtml(trends.join(' · ') || label || 'No trend')}</strong></div>`;
      card.appendChild(drill);
      card.addEventListener('click', (event) => {
        if (event.target.closest('button,a,input,select,textarea')) return;
        card.classList.toggle('is-drilled');
      });
    });
  }

  decorateMetricCards();
  // ───────────────────────── Presenter View ─────────────────────────
  if (typeof io !== 'undefined') {
    const pBar = document.createElement('div');
    pBar.className = 'presenter-bar';
    pBar.innerHTML = `<div class="presenter-info"><span id="p-status"></span><span class="presenter-badge" id="p-code" style="display:none;"></span></div><div class="annotation-tools" aria-label="Presenter annotation tools"><button type="button" class="annotation-btn annotation-color is-active" data-color="#fff176" title="Yellow highlight">Yellow</button><button type="button" class="annotation-btn annotation-color" data-color="#a7f3d0" title="Green highlight">Green</button><button type="button" class="annotation-btn annotation-color" data-color="#fbcfe8" title="Pink highlight">Pink</button><button type="button" class="annotation-btn" id="p-highlight-btn" title="Highlight selected word or text">Highlight</button><button type="button" class="annotation-btn" id="p-tooltip-btn" title="Add tooltip note to selected text">Tooltip</button><button type="button" class="annotation-btn" id="p-pen-btn" title="Draw on screen">Pen</button><button type="button" class="annotation-btn" id="p-eraser-btn" title="Erase drawings">Eraser</button><button type="button" class="annotation-btn" id="p-clear-annotations-btn" title="Clear annotations">Clear</button></div><div class="presenter-actions"><button type="button" class="presenter-btn" id="p-host-btn">Host</button><button type="button" class="presenter-btn" id="p-join-btn">Join</button><button type="button" class="presenter-btn" id="p-leave-btn" style="display:none;">Leave</button></div>`;
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
      document.getElementById('p-status').textContent = '';
      document.getElementById('p-code').style.display = 'none';
      document.getElementById('p-host-btn').style.display = 'inline-block';
      document.getElementById('p-join-btn').style.display = 'inline-block';
      document.getElementById('p-leave-btn').style.display = 'none';
      pBar.classList.remove('is-active');
      setAnnotationMode('idle');
      clearAnnotations();
      document.body.classList.remove('viewer-locked');
    });

    const urlParams = new URLSearchParams(window.location.search);
    const initCode = urlParams.get('roomCode');
    if (initCode && initCode.length === 6) {
      joinSession('viewer', initCode);
    }
  }
})();
