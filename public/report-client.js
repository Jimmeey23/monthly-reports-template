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
.section-narrative-label {
  display: flex !important;
  align-items: center !important;
  gap: 8px !important;
  margin: 22px 0 8px !important;
  color: var(--primary-3) !important;
  font-size: 9.5px !important;
  font-weight: 850 !important;
  letter-spacing: .12em !important;
  text-transform: uppercase !important;
}
.section-narrative-label::before { content: '' !important; width: 24px !important; height: 1px !important; background: var(--primary-3) !important; }
/* The hero metric cards are styled by report.css, the master stylesheet.
   This client used to re-style them here with ~450 lines of !important
   rules written against an older card DOM (.kpi-card-face, .kpi-icon,
   .kpi-ambient, .kpi-mini-chart — none of which are generated any more),
   which is why a served report looked different from the downloaded file:
   it forced a 3-column grid and half-applied a card design that no longer
   exists. Removed so the served and standalone reports match. */
/* Presenter chrome is styled by public/presenter.css; only the in-text
   annotation marks stay here, since they live inside the report body. */
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
@keyframes ai-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
`;
  document.head.appendChild(styleEl);

  /* Presenter mode (hosting, roster, annotation, laser, spotlight) now lives
     in public/presenter.js, loaded alongside this file. It kept its own socket
     wiring anyway, and it needed a document-space annotation model that did
     not belong in the report client. */
})();
