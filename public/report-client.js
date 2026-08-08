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

  const toolbar = document.createElement('div');
  toolbar.className = 'editor-toolbar';
  toolbar.innerHTML =
    '<button type="button" id="edit-toggle-btn">&#9998; Edit</button>' +
    '<button type="button" id="save-btn" disabled>&#128190; Save</button>' +
    '<span class="editor-status" id="editor-status"></span>';
  document.body.appendChild(toolbar);

  const editBtn = document.getElementById('edit-toggle-btn');
  const saveBtn = document.getElementById('save-btn');
  const statusEl = document.getElementById('editor-status');
  let editing = false;

  function setEditing(on) {
    editing = on;
    document.documentElement.setAttribute('data-editing', on ? 'true' : 'false');
    document.querySelectorAll('.container').forEach((el) => {
      el.setAttribute('contenteditable', on ? 'true' : 'false');
    });
    editBtn.classList.toggle('is-active', on);
    editBtn.innerHTML = on ? '&#9998; Editing&hellip;' : '&#9998; Edit';
    saveBtn.disabled = !on;
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

  setEditing(false);

  // ───────────────────────── Per-section AI insights ─────────────────────────

  function renderResult(result) {
    const insightCards = (result.insights || [])
      .map(
        (ins, i) => `
      <div class="insight-card">
        <div class="insight-num">${String(i + 1).padStart(2, '0')}</div>
        <div class="insight-body">
          <div class="insight-title">${escapeHtml(ins.title)}</div>
          <div class="insight-text">${escapeHtml(ins.text)}</div>
        </div>
      </div>`
      )
      .join('');

    const actions = result.actions || [];
    const actionRows = actions
      .map(
        (a) => `
      <tr>
        <td>${escapeHtml(a.action)}</td>
        <td>${escapeHtml(a.rationale)}</td>
        <td>${escapeHtml(a.impact)}</td>
        <td>${escapeHtml(a.timeline)}</td>
        <td>${escapeHtml(a.owner)}</td>
      </tr>`
      )
      .join('');

    return `
      <div class="ai-result">
        <div class="pane-title">AI Insights</div>
        ${result.summary ? `<p class="ai-result-summary">${escapeHtml(result.summary)}</p>` : ''}
        ${insightCards}
        ${
          actions.length
            ? `<div class="table-wrap" style="margin-top:20px;">
                <table class="data-table">
                  <thead><tr><th>Action</th><th>Rationale</th><th>Impact</th><th>Timeline</th><th>Owner</th></tr></thead>
                  <tbody>${actionRows}</tbody>
                </table>
              </div>`
            : ''
        }
      </div>`;
  }

  document.querySelectorAll('.ai-btn').forEach((btn) => {
    const originalLabel = btn.innerHTML;
    btn.addEventListener('click', async () => {
      const section = btn.dataset.section;
      const slot = document.getElementById(`ai-slot-${section}`);
      if (!slot) return;

      if (!ctx.sessionId) {
        slot.innerHTML = `<div class="ai-result"><div class="ai-result-error">AI insights require viewing through the report server (missing session ID).</div></div>`;
        return;
      }

      btn.disabled = true;
      btn.classList.add('is-loading');
      btn.innerHTML = '<span class="ai-btn-icon">&#10024;</span> Generating&hellip;';
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
        btn.innerHTML = '<span class="ai-btn-icon">&#10024;</span> Regenerate Insights';
      } catch (e) {
        slot.innerHTML = `<div class="ai-result"><div class="ai-result-error">AI insights failed: ${escapeHtml(e.message)}</div></div>`;
        btn.innerHTML = originalLabel;
      }

      btn.disabled = false;
      btn.classList.remove('is-loading');
    });
  });
})();
