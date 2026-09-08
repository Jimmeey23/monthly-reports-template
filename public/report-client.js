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
.hero-kpi-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
  gap: 12px !important;
  perspective: 1800px;
}
.kpi-card:has(.kpi-card-inner) {
  min-height: 232px !important;
  padding: 0 !important;
  overflow: visible !important;
  border: 0 !important;
  border-radius: 20px !important;
  background: transparent !important;
  box-shadow: none !important;
  cursor: pointer;
  outline: none;
  transition: transform 220ms cubic-bezier(.2,.8,.2,1) !important;
  animation: kpiCardEnter 480ms cubic-bezier(.2,.8,.2,1) both;
  animation-delay: calc(var(--card-index, 0) * 55ms);
}
.kpi-card:has(.kpi-card-inner)::before,
.kpi-card:has(.kpi-card-inner)::after { display: none !important; }
.kpi-card:has(.kpi-card-inner):focus-visible .kpi-card-face {
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary) 32%, transparent), var(--shadow-lg) !important;
}
.kpi-card-inner {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 232px;
  transform-style: preserve-3d;
  transition: transform 360ms cubic-bezier(.2,.75,.25,1);
}
.kpi-card.is-flipped .kpi-card-inner { transform: rotateY(180deg); }
.kpi-card-face {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  min-height: 232px;
  padding: 19px 20px;
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: 16px;
  background: linear-gradient(155deg, var(--bg-card), color-mix(in srgb, var(--bg-inset) 42%, var(--bg-card)));
  box-shadow: 0 12px 32px -24px rgba(15,23,42,.55), 0 3px 10px -7px rgba(15,23,42,.2);
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
}
.kpi-card-face::after {
  content: '';
  position: absolute;
  width: 96px;
  height: 96px;
  right: -45px;
  top: -48px;
  border-radius: 50%;
  background: color-mix(in srgb, var(--primary) 10%, transparent);
  pointer-events: none;
}
.kpi-card-front { justify-content: flex-start; }
.kpi-card-front::before {
  content: '';
  position: absolute;
  left: 20px;
  top: 0;
  width: 42px;
  height: 2px;
  border-radius: 0 0 2px 2px;
  background: linear-gradient(90deg, var(--primary-3), var(--accent));
  transition: width 240ms ease;
}
.kpi-card-back {
  transform: rotateY(180deg);
  gap: 8px;
  background: linear-gradient(150deg, color-mix(in srgb, var(--primary-soft) 44%, var(--bg-card)), var(--bg-card) 58%);
}
.kpi-card-kicker, .kpi-back-period {
  color: var(--text-subtle);
  font-size: 9.5px;
  font-weight: 800;
  letter-spacing: .12em;
  text-transform: uppercase;
}
.kpi-card-front .kpi-label { margin-top: 17px !important; font-size: 12px !important; }
.kpi-card-front .kpi-value { margin-top: 4px !important; font-size: clamp(31px, 2.7vw, 40px) !important; letter-spacing: -.04em !important; }
.kpi-card-front .kpi-sub { max-width: 90%; margin-top: 5px !important; font-size: 11.5px !important; line-height: 1.4 !important; }
.kpi-card-action {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-top: auto;
  padding-top: 11px;
  border-top: 1px solid var(--border);
  color: var(--primary-3);
  font-size: 10.5px;
  font-weight: 750;
}
.kpi-back-header, .kpi-comparison-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.kpi-back-header { color: var(--text); font-size: 13px; font-weight: 750; }
.kpi-comparison {
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: color-mix(in srgb, var(--bg-card) 76%, transparent);
}
.kpi-comparison-top > span:first-child {
  color: var(--text-muted);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: .06em;
  text-transform: uppercase;
}
.kpi-comparison p { margin: 5px 0 0; color: var(--text-muted); font-size: 9.75px; line-height: 1.38; }
.kpi-benchmark { display: flex; flex-direction: column; gap: 3px; }
.kpi-benchmark span { color: var(--text-subtle); font-size: 9px; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }
.kpi-benchmark strong { color: var(--text); font-size: 11px; line-height: 1.4; }
.kpi-card-back .kpi-card-action { padding-top: 7px; }
@media (hover: hover) {
  .kpi-card:has(.kpi-card-inner):hover { transform: translateY(-4px) !important; }
  .kpi-card:has(.kpi-card-inner):hover .kpi-card-face {
    border-color: color-mix(in srgb, var(--primary) 34%, var(--border));
    box-shadow: 0 22px 42px -27px rgba(15,23,42,.55), 0 8px 16px -12px rgba(15,23,42,.22);
  }
  .kpi-card:has(.kpi-card-inner):hover .kpi-card-front::before { width: 72px; }
}
@keyframes kpiCardEnter {
  from { opacity: 0; transform: translateY(12px) scale(.985); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
@media (max-width: 980px) { .hero-kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)) !important; } }
@media (max-width: 620px) {
  .hero-kpi-grid { grid-template-columns: 1fr !important; }
  .kpi-card:has(.kpi-card-inner), .kpi-card-inner, .kpi-card-face { min-height: 232px !important; }
}
@media (prefers-reduced-motion: reduce) {
  .kpi-card:has(.kpi-card-inner) { animation: none; }
  .kpi-card-inner { transition: none; }
}

/* Studio Pulse metric cards */
.hero-kpi-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
  justify-content: stretch !important;
  gap: 14px !important;
}
.kpi-card:has(.kpi-card-inner), .kpi-card-inner, .kpi-card-face {
  width: 100% !important;
  max-width: none !important;
  min-height: 224px !important;
}
.kpi-card-face {
  padding: 0 !important;
  border: 1px solid color-mix(in srgb, var(--border) 70%, transparent) !important;
  border-radius: 16px !important;
  background: var(--bg-card) !important;
  box-shadow: 0 8px 24px rgba(15,23,42,.10), 0 2px 8px rgba(15,23,42,.06) !important;
  overflow: hidden !important;
}
.kpi-card-face::after, .kpi-card-front::before { display: none !important; }
.kpi-card-front {
  display: flex !important;
  flex-direction: column !important;
}
.kpi-ambient { position: absolute; inset: 0; overflow: hidden; pointer-events: none; opacity: .7; }
.kpi-ambient span { position: absolute; border-radius: 999px; border: 1px solid color-mix(in srgb, var(--primary) 10%, transparent); }
.kpi-ambient span:nth-child(1) { width: 116px; height: 116px; right: -74px; top: -72px; }
.kpi-ambient span:nth-child(2) { width: 72px; height: 72px; right: -43px; top: -42px; }
.kpi-ambient span:nth-child(3) { width: 5px; height: 5px; right: 18px; top: 18px; border: 0; background: var(--accent); box-shadow: 0 0 0 6px color-mix(in srgb, var(--accent) 10%, transparent); animation: kpiAmbientPulse 2.8s ease-in-out infinite; }
.kpi-front-header {
  min-height: 64px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px 11px;
  border-bottom: 1px solid color-mix(in srgb, var(--border) 68%, transparent);
  box-shadow: inset 0 -1px 0 color-mix(in srgb, var(--text) 5%, transparent);
}
.kpi-title-lockup { display: flex; align-items: center; gap: 8px; min-width: 0; flex: 1 1 auto; }
.kpi-icon {
  width: 29px; height: 29px; flex: 0 0 29px; display: grid; place-items: center;
  border-radius: 9px; color: #fff;
  background: linear-gradient(145deg, var(--primary-2), var(--primary));
  box-shadow: 0 5px 12px color-mix(in srgb, var(--primary) 26%, transparent), inset 0 1px rgba(255,255,255,.28);
}
.kpi-card:nth-child(2n) .kpi-icon { background: linear-gradient(145deg, var(--accent), var(--primary-2)); }
.kpi-card:nth-child(3n) .kpi-icon { background: linear-gradient(145deg, var(--primary-3), var(--primary)); }
.kpi-icon svg { width: 15px; height: 15px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.kpi-card-front .kpi-label {
  display: block !important;
  min-width: 0;
  margin: 0 !important;
  color: var(--text) !important;
  font-size: 13px !important;
  font-weight: 750 !important;
  line-height: 1.15 !important;
  letter-spacing: -.01em !important;
  text-transform: none !important;
  overflow-wrap: anywhere;
}
.kpi-card-front .kpi-value {
  display: block !important;
  position: relative !important;
  z-index: 2 !important;
  flex: 0 0 auto;
  max-width: 48%;
  margin: 0 !important;
  color: var(--text) !important;
  font-size: clamp(20px, 1.8vw, 28px) !important;
  font-weight: 850 !important;
  line-height: 1 !important;
  letter-spacing: -.045em !important;
  white-space: nowrap;
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.kpi-front-body { position: relative; z-index: 1; flex: 1; display: flex; flex-direction: column; padding: 9px 14px 4px; }
.kpi-chart-heading { display: flex; align-items: center; justify-content: space-between; gap: 8px; color: var(--text-muted); font-size: 8px; font-weight: 800; letter-spacing: .08em; line-height: 1; text-transform: uppercase; }
.kpi-chart-heading strong { color: var(--text-subtle); font: inherit; letter-spacing: .02em; }
.kpi-mini-chart {
  display: flex;
  align-items: end;
  gap: 3px;
  height: 92px;
  width: 100%;
  margin: 0;
  padding: 7px 0 0;
  border: 0;
}
.kpi-bar-column { height: 100%; min-width: 0; flex: 1; display: flex; flex-direction: column; align-items: stretch; justify-content: end; gap: 3px; }
.kpi-bar-column i {
  display: block; width: 100%; height: var(--height); min-height: 8px;
  border-radius: 4px 4px 1px 1px;
  background: color-mix(in srgb, var(--primary-2) 27%, var(--border));
  opacity: .62; transform-origin: bottom;
  animation: kpiBarRise 720ms cubic-bezier(.16,1,.3,1) both;
  animation-delay: calc(45ms * var(--bar-index, 0));
}
.kpi-bar-column:nth-child(2) { --bar-index: 1; } .kpi-bar-column:nth-child(3) { --bar-index: 2; }
.kpi-bar-column:nth-child(4) { --bar-index: 3; } .kpi-bar-column:nth-child(5) { --bar-index: 4; }
.kpi-bar-column:nth-child(6) { --bar-index: 5; } .kpi-bar-column:nth-child(7) { --bar-index: 6; }
.kpi-bar-column:nth-child(8) { --bar-index: 7; } .kpi-bar-column:nth-child(9) { --bar-index: 8; }
.kpi-bar-column:nth-child(10) { --bar-index: 9; } .kpi-bar-column:nth-child(11) { --bar-index: 10; }
.kpi-bar-column:nth-child(12) { --bar-index: 11; }
.kpi-bar-column small { color: var(--text-subtle); font: 700 7px/1 var(--font-mono); text-align: center; text-transform: uppercase; }
.kpi-bar-column.is-current i { background: var(--primary); opacity: 1; box-shadow: 0 4px 10px color-mix(in srgb, var(--primary) 22%, transparent); }
.kpi-bar-column.is-current small { color: var(--text); }
.kpi-card-action {
  margin: 0 14px 10px !important;
  padding-top: 7px !important;
  border-top-color: color-mix(in srgb, var(--border) 70%, transparent) !important;
  color: var(--text-muted) !important;
  font-size: 9px !important; letter-spacing: .02em;
}
.kpi-card-back {
  display: grid !important;
  grid-template-columns: 1fr 1fr !important;
  grid-template-rows: auto auto 1fr auto auto !important;
  gap: 8px !important;
  padding: 13px 14px 10px !important;
  background: var(--bg-card) !important;
}
.kpi-back-header { grid-column: 1 / -1; display: flex !important; align-items: center; justify-content: space-between; font-size: 11px !important; }
.kpi-back-header b { width: 23px; height: 23px; display: grid; place-items: center; border-radius: 50%; background: var(--bg-inset); color: var(--text-subtle); font-size: 15px; font-weight: 500; }
.kpi-back-description { grid-column: 1 / -1; margin: 0 !important; color: var(--text-muted); font-size: 9px; line-height: 1.35; }
.kpi-comparison { padding: 8px !important; border: 1px solid color-mix(in srgb, var(--border) 70%, transparent) !important; border-radius: 10px !important; background: color-mix(in srgb, var(--bg-inset) 62%, transparent) !important; box-shadow: inset 0 1px rgba(255,255,255,.05); }
.kpi-comparison-top > span:first-child { font-size: 8px !important; letter-spacing: .08em; }
.kpi-comparison-top strong.badge { min-width: 0; min-height: 21px; padding: 3px 6px; border-radius: 7px; font: 850 9px/1 var(--font-mono); }
.kpi-comparison-top strong.good { color: var(--good); }
.kpi-comparison-top strong.bad { color: var(--bad); }
.kpi-comparison-top strong.warn { color: var(--warn); }
.kpi-comparison-top strong.neutral { color: var(--text-muted); }
.kpi-comparison p { margin: 5px 0 0 !important; color: var(--text-muted) !important; font-size: 8px !important; line-height: 1.3 !important; }
.kpi-benchmark { grid-column: 1 / -1; min-width: 0; }
.kpi-benchmark span { font-size: 7.5px !important; }
.kpi-benchmark strong { overflow: hidden; font-size: 9px !important; text-overflow: ellipsis; white-space: nowrap; }
.kpi-card-back .kpi-card-action { grid-column: 1 / -1; margin: 0 !important; padding-top: 7px !important; }
@keyframes kpiBarRise { from { transform: scaleY(.08); opacity: .15; } to { transform: scaleY(1); } }
@keyframes kpiAmbientPulse { 0%,100% { transform: scale(.88); opacity: .55; } 50% { transform: scale(1.15); opacity: 1; } }
@media (hover: hover) {
  .kpi-card:has(.kpi-card-inner):hover { transform: translateY(-4px) scale(1.018) !important; }
  .kpi-card:has(.kpi-card-inner):hover .kpi-card-face { border-color: color-mix(in srgb, var(--primary) 25%, var(--border)) !important; box-shadow: 0 14px 30px rgba(15,23,42,.14), 0 4px 10px rgba(15,23,42,.07) !important; }
  .kpi-bar-column:hover i { opacity: 1; transform: scaleY(1) translateY(-2px); }
}
@media (max-width: 900px) { .hero-kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)) !important; } }
@media (max-width: 520px) {
  .hero-kpi-grid { grid-template-columns: 1fr !important; }
  .kpi-card:has(.kpi-card-inner), .kpi-card-inner, .kpi-card-face { min-height: 224px !important; }
}
@media (prefers-reduced-motion: reduce) { .kpi-bar-column i, .kpi-ambient span:nth-child(3) { animation: none; } }
.presenter-bar {
  position: fixed;
  left: 14px;
  bottom: 14px;
  z-index: 3200;
  display: flex;
  align-items: center;
  gap: 0;
  max-width: min(680px, calc(100vw - 28px));
  padding: 0;
  background: transparent;
  border: 0;
  border-radius: 0;
  box-shadow: none;
  backdrop-filter: none;
}
.presenter-toggle {
  width: 42px;
  height: 42px;
  min-width: 42px;
  min-height: 42px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: color-mix(in srgb, var(--bg-card) 92%, transparent);
  color: var(--text);
  box-shadow: var(--shadow-lg);
  backdrop-filter: blur(10px);
  cursor: pointer;
  font: 900 15px/1 var(--font-sans);
}
.presenter-bar.is-active .presenter-toggle {
  border-color: rgba(255, 99, 99, 0.35);
}
.presenter-panel {
  display: none;
  align-items: center;
  gap: 8px;
  margin-left: 8px;
  max-width: calc(100vw - 82px);
  padding: 8px;
  background: color-mix(in srgb, var(--bg-card) 92%, transparent);
  border: 1px solid var(--border);
  border-radius: 999px;
  box-shadow: var(--shadow-lg);
  backdrop-filter: blur(10px);
}
.presenter-bar.is-open .presenter-panel,
.presenter-bar.is-active .presenter-panel { display: flex; }
.presenter-info { display: none; align-items: center; gap: 8px; color: var(--text); font-size: 12px; font-weight: 400; }
.presenter-bar.is-active .presenter-info { display: flex; }
.presenter-badge { display: inline-flex; align-items: center; justify-content: center; min-height: 24px; padding: 2px 8px; border-radius: 999px; background: var(--primary-soft); color: var(--primary); font-family: var(--font-mono); font-weight: 400; text-align: center; }
.presenter-actions, .annotation-tools { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.annotation-tools { display: none; }
.presenter-bar.is-active .annotation-tools { display: flex; }
.presenter-btn, .annotation-btn {
  min-height: 30px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6px 10px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--bg-card);
  color: var(--text);
  cursor: pointer;
  font: 400 12px/1 var(--font-sans);
  text-align: center;
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
.presenting::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  z-index: 3300;
  background: linear-gradient(90deg, #e11d48, #fb7185, #ef4444);
  box-shadow: 0 1px 0 rgba(255,255,255,0.15) inset;
}
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
