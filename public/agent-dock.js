/* =============================================================================
   agent-dock.js — the chat panel inside every served report
   -----------------------------------------------------------------------------
   Injected by the server when a report is served (see server.js /report route),
   so old and new reports both get it. Three jobs:

     1. Chat: streams a turn from /agent/.../message and renders the steps.
     2. Preview: applies a proposal to the live DOM the moment it arrives,
        outlined and pending, with Keep / Discard.
     3. Replay: on load, re-applies everything saved in report-overrides.json —
        which is why the report file itself stays untouched until Save.

   Applying a style op or a component is the same code path for a preview and
   for a replay; the only difference is whether it is tagged pending.
   ========================================================================== */
(function () {
  'use strict';

  var CTX = window.__AGENT_CTX__ || {};
  if (!CTX.sessionId || !CTX.filename) return;

  var BASE = '/agent/' + encodeURIComponent(CTX.sessionId) + '/' + encodeURIComponent(CTX.filename);
  var canEdit = !!CTX.editToken;
  var state = { open: false, busy: false, pending: null, overrides: { patches: [], components: [] } };

  /* ------------------------------------------------------------- helpers -- */

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text != null) node.textContent = text;
    return node;
  }

  function api(path, options) {
    options = options || {};
    var headers = Object.assign({ 'Content-Type': 'application/json' }, options.headers || {});
    if (CTX.editToken) headers['x-agent-edit-token'] = CTX.editToken;
    return fetch(path, Object.assign({}, options, { headers: headers }));
  }

  function escapeHtml(text) {
    return String(text).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  /* Small markdown subset — tables, bold, code, lists — which is all the model
     is asked to produce. Escaped first, so model output can never inject HTML. */
  function renderMarkdown(src) {
    var text = escapeHtml(src);
    var lines = text.split('\n');
    var out = [];
    var i = 0;

    while (i < lines.length) {
      var line = lines[i];

      if (/^\s*\|.*\|\s*$/.test(line) && /^\s*\|[\s:|-]+\|\s*$/.test(lines[i + 1] || '')) {
        var cells = function (row) {
          return row.trim().replace(/^\||\|$/g, '').split('|').map(function (c) { return c.trim(); });
        };
        var head = cells(line);
        i += 2;
        var body = [];
        while (i < lines.length && /^\s*\|.*\|\s*$/.test(lines[i])) { body.push(cells(lines[i])); i += 1; }
        out.push('<table class="agent-md-table"><thead><tr>'
          + head.map(function (h) { return '<th>' + inline(h) + '</th>'; }).join('')
          + '</tr></thead><tbody>'
          + body.map(function (r) {
            return '<tr>' + r.map(function (c) { return '<td>' + inline(c) + '</td>'; }).join('') + '</tr>';
          }).join('')
          + '</tbody></table>');
        continue;
      }

      if (/^\s*[-*]\s+/.test(line)) {
        var items = [];
        while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) {
          items.push('<li>' + inline(lines[i].replace(/^\s*[-*]\s+/, '')) + '</li>');
          i += 1;
        }
        out.push('<ul>' + items.join('') + '</ul>');
        continue;
      }

      if (/^\s*#{1,4}\s+/.test(line)) {
        out.push('<strong class="agent-md-head">' + inline(line.replace(/^\s*#{1,4}\s+/, '')) + '</strong>');
        i += 1;
        continue;
      }

      if (!line.trim()) { i += 1; continue; }

      var para = [];
      while (i < lines.length && lines[i].trim() && !/^\s*[-*]\s+/.test(lines[i]) && !/^\s*\|/.test(lines[i])) {
        para.push(lines[i]);
        i += 1;
      }
      out.push('<p>' + inline(para.join(' ')) + '</p>');
    }

    function inline(s) {
      return s
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/(^|[^*])\*([^*]+)\*/g, '$1<em>$2</em>');
    }

    return out.join('');
  }

  /* ------------------------------------------------------- applying ops -- */

  var styleSheet = null;
  function sheet() {
    if (!styleSheet) {
      styleSheet = el('style');
      styleSheet.id = 'agent-override-styles';
      document.head.appendChild(styleSheet);
    }
    return styleSheet;
  }

  function cssText(selector, declarations) {
    var body = Object.keys(declarations).map(function (prop) {
      return prop.replace(/[A-Z]/g, function (m) { return '-' + m.toLowerCase(); })
        + ':' + declarations[prop] + ' !important;';
    }).join('');
    return selector + '{' + body + '}';
  }

  function nodes(selector) {
    try { return Array.prototype.slice.call(document.querySelectorAll(selector)); } catch (e) { return []; }
  }

  /**
   * Apply one style patch. Returns an undo function, which is what makes a
   * preview discardable without reloading the page.
   */
  function applyPatch(patch, pending) {
    var undos = [];

    (patch.ops || []).forEach(function (op) {
      var targets = nodes(op.selector);
      switch (op.kind) {
        case 'css': {
          var rule = document.createTextNode(cssText(op.selector, op.declarations || {}));
          sheet().appendChild(rule);
          undos.push(function () { if (rule.parentNode) rule.parentNode.removeChild(rule); });
          break;
        }
        case 'hide':
        case 'show': {
          targets.forEach(function (node) {
            // Restoring `display` alone would leave a `style=""` behind on an
            // element that had no style attribute — enough to dirty the saved
            // HTML on every discarded preview.
            var had = node.hasAttribute('style');
            var prev = node.getAttribute('style');
            node.style.display = op.kind === 'hide' ? 'none' : '';
            undos.push(function () {
              if (had) node.setAttribute('style', prev); else node.removeAttribute('style');
            });
          });
          break;
        }
        case 'remove': {
          targets.forEach(function (node) {
            var parent = node.parentNode;
            var next = node.nextSibling;
            parent.removeChild(node);
            undos.push(function () { parent.insertBefore(node, next); });
          });
          break;
        }
        case 'move': {
          var anchor = nodes(op.target)[0];
          if (!anchor) break;
          targets.forEach(function (node) {
            var parent = node.parentNode;
            var next = node.nextSibling;
            place(node, anchor, op.position || 'after');
            undos.push(function () { parent.insertBefore(node, next); });
          });
          break;
        }
        case 'reorder': {
          targets.forEach(function (node) {
            var parent = node.parentNode;
            var next = node.nextSibling;
            var siblings = Array.prototype.slice.call(parent.children);
            var at = Math.max(0, Math.min(Number(op.index) || 0, siblings.length - 1));
            parent.insertBefore(node, siblings[at] || null);
            undos.push(function () { parent.insertBefore(node, next); });
          });
          break;
        }
        case 'setText':
        case 'setHtml': {
          targets.forEach(function (node) {
            var prev = node.innerHTML;
            if (op.kind === 'setText') node.textContent = op.text || '';
            else node.innerHTML = op.html || '';
            undos.push(function () { node.innerHTML = prev; });
          });
          break;
        }
        case 'addClass':
        case 'removeClass': {
          targets.forEach(function (node) {
            var had = node.classList.contains(op.className);
            node.classList[op.kind === 'addClass' ? 'add' : 'remove'](op.className);
            undos.push(function () { node.classList[had ? 'add' : 'remove'](op.className); });
          });
          break;
        }
        case 'setAttr': {
          targets.forEach(function (node) {
            var prev = node.getAttribute(op.name);
            node.setAttribute(op.name, op.value == null ? '' : op.value);
            undos.push(function () {
              if (prev === null) node.removeAttribute(op.name); else node.setAttribute(op.name, prev);
            });
          });
          break;
        }
        default:
          break;
      }
    });

    if (pending) {
      nodes((patch.ops || []).map(function (o) { return o.selector; }).join(',')).forEach(function (node) {
        node.classList.add('agent-pending-target');
        undos.push(function () { node.classList.remove('agent-pending-target'); });
      });
    }

    return function undo() { undos.reverse().forEach(function (fn) { fn(); }); };
  }

  function place(node, anchor, position) {
    if (position === 'before') anchor.parentNode.insertBefore(node, anchor);
    else if (position === 'after') anchor.parentNode.insertBefore(node, anchor.nextSibling);
    else if (position === 'prepend') anchor.insertBefore(node, anchor.firstChild);
    else if (position === 'replace') anchor.parentNode.replaceChild(node, anchor);
    else anchor.appendChild(node);
  }

  /** Insert a component. Returns an undo function, same contract as applyPatch. */
  function applyComponent(component, pending, id) {
    var anchor = nodes(component.target)[0];
    if (!anchor) return null;

    var wrapper = el('div', 'agent-component' + (pending ? ' is-pending' : ''));
    wrapper.setAttribute('data-agent-component', id || component.id || 'preview');
    wrapper.innerHTML = component.html;

    var styleNode = null;
    if (component.css) {
      styleNode = el('style');
      styleNode.textContent = component.css;
      document.head.appendChild(styleNode);
    }

    place(wrapper, anchor, component.position || 'append');

    if (component.js) {
      try {
        // eslint-disable-next-line no-new-func
        new Function('root', 'document', component.js)(wrapper, document);
      } catch (e) {
        console.warn('agent component script failed:', e);
      }
    }

    return function undo() {
      if (wrapper.parentNode) wrapper.parentNode.removeChild(wrapper);
      if (styleNode && styleNode.parentNode) styleNode.parentNode.removeChild(styleNode);
    };
  }

  /* --------------------------------------------------------------- panel -- */

  var dock, log, input, sendBtn, pendingBar, statusLine;

  function build() {
    dock = el('div', 'agent-dock');
    dock.innerHTML = ''
      + '<button class="agent-fab" type="button" aria-label="Ask the report">'
      + '  <span class="agent-fab-dot"></span>Ask the report'
      + '</button>'
      + '<section class="agent-panel" aria-label="Report assistant" hidden>'
      + '  <header class="agent-head">'
      + '    <div><strong>Report Analyst</strong><small>' + (canEdit ? 'Ask, build, restyle' : 'Read-only · questions welcome') + '</small></div>'
      + '    <div class="agent-head-actions">'
      + '      <button class="agent-icon-btn" data-act="changes" title="Saved changes">⋯</button>'
      + (canEdit ? '      <button class="agent-icon-btn" data-act="save" title="Bake changes into the report file">Save</button>' : '')
      + '      <button class="agent-icon-btn" data-act="close" title="Close">✕</button>'
      + '    </div>'
      + '  </header>'
      + '  <div class="agent-log" role="log"></div>'
      + '  <div class="agent-pending" hidden></div>'
      + '  <div class="agent-status" hidden></div>'
      + '  <form class="agent-input">'
      + '    <textarea rows="1" placeholder="' + (canEdit ? 'Ask about the data, or ask for a table, chart or restyle…' : 'Ask anything about this report…') + '"></textarea>'
      + '    <button type="submit" class="agent-send">Send</button>'
      + '  </form>'
      + '</section>';
    document.body.appendChild(dock);

    log = dock.querySelector('.agent-log');
    input = dock.querySelector('textarea');
    sendBtn = dock.querySelector('.agent-send');
    pendingBar = dock.querySelector('.agent-pending');
    statusLine = dock.querySelector('.agent-status');

    dock.querySelector('.agent-fab').addEventListener('click', toggle);
    dock.querySelector('[data-act="close"]').addEventListener('click', toggle);
    dock.querySelector('[data-act="changes"]').addEventListener('click', showChanges);
    var saveBtn = dock.querySelector('[data-act="save"]');
    if (saveBtn) saveBtn.addEventListener('click', saveReport);

    dock.querySelector('.agent-input').addEventListener('submit', function (e) {
      e.preventDefault();
      send();
    });
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
    });
    input.addEventListener('input', function () {
      input.style.height = 'auto';
      input.style.height = Math.min(input.scrollHeight, 140) + 'px';
    });

    say('assistant', canEdit
      ? 'Ask me anything about this month — I query the underlying data rather than reading the page, so the numbers are exact. I can also build a table or chart into any section, or restyle it.'
      : 'Ask me anything about this month. I query the underlying data directly, so the numbers are exact.');
  }

  function toggle() {
    state.open = !state.open;
    dock.querySelector('.agent-panel').hidden = !state.open;
    dock.classList.toggle('is-open', state.open);
    if (state.open) input.focus();
  }

  function say(role, text, isHtml) {
    var row = el('div', 'agent-msg agent-msg-' + role);
    var bubble = el('div', 'agent-bubble');
    if (isHtml) bubble.innerHTML = text; else bubble.textContent = text;
    row.appendChild(bubble);
    log.appendChild(row);
    log.scrollTop = log.scrollHeight;
    return bubble;
  }

  /** A collapsed line for each tool call, expandable to the code and result. */
  function toolChip(name, args) {
    var wrap = el('details', 'agent-tool');
    var label = name === 'run_query'
      ? (args.purpose || 'Querying the data')
      : name.replace(/_/g, ' ');
    wrap.appendChild(el('summary', null, '⚙ ' + label));
    if (args.code) {
      var pre = el('pre', 'agent-code', args.code);
      wrap.appendChild(pre);
    }
    log.appendChild(wrap);
    log.scrollTop = log.scrollHeight;
    return wrap;
  }

  function status(text) {
    statusLine.hidden = !text;
    statusLine.textContent = text || '';
  }

  /* ---------------------------------------------------------- the turn -- */

  function send() {
    var text = input.value.trim();
    if (!text || state.busy) return;
    input.value = '';
    input.style.height = 'auto';
    say('user', text);
    stream(text);
  }

  function stream(message) {
    state.busy = true;
    sendBtn.disabled = true;
    status('Thinking…');

    var lastChip = null;

    fetch(BASE + '/message', {
      method: 'POST',
      headers: Object.assign(
        { 'Content-Type': 'application/json' },
        CTX.editToken ? { 'x-agent-edit-token': CTX.editToken } : {},
      ),
      body: JSON.stringify({ message: message }),
    }).then(function (res) {
      if (!res.body) throw new Error('Streaming is not supported by this browser.');
      var reader = res.body.getReader();
      var decoder = new TextDecoder();
      var buffer = '';

      function pump() {
        return reader.read().then(function (chunk) {
          if (chunk.done) return finish();
          buffer += decoder.decode(chunk.value, { stream: true });
          var parts = buffer.split('\n\n');
          buffer = parts.pop();
          parts.forEach(function (part) {
            var line = part.replace(/^data: /, '').trim();
            if (!line) return;
            var event;
            try { event = JSON.parse(line); } catch (e) { return; }
            handle(event);
          });
          return pump();
        });
      }

      function handle(event) {
        if (event.type === 'status') status(event.text);
        else if (event.type === 'tool') lastChip = toolChip(event.name, event.args || {});
        else if (event.type === 'tool_result' && lastChip) {
          var result = event.result || {};
          var body = result.ok === false
            ? 'Error: ' + result.error
            : JSON.stringify(result.result !== undefined ? result.result : result, null, 2);
          lastChip.appendChild(el('pre', 'agent-code agent-result', String(body).slice(0, 4000)));
          if (result.ok === false) lastChip.classList.add('is-error');
        } else if (event.type === 'proposal') showProposal(event.proposal);
        else if (event.type === 'message') say('assistant', renderMarkdown(event.text), true);
        else if (event.type === 'error') say('assistant', 'Error: ' + event.error);
      }

      function finish() {
        state.busy = false;
        sendBtn.disabled = false;
        status('');
      }

      return pump();
    }).catch(function (err) {
      say('assistant', 'Error: ' + err.message);
      state.busy = false;
      sendBtn.disabled = false;
      status('');
    });
  }

  /* ------------------------------------------------------- the edit gate -- */

  function showProposal(proposal) {
    clearPending();

    var undo = null;
    if (proposal.kind === 'style') undo = applyPatch(proposal, true);
    else if (proposal.kind === 'component') {
      undo = applyComponent(proposal.component, true, 'preview');
      if (!undo) { say('assistant', 'I could not find "' + proposal.component.target + '" on the page.'); return; }
    } else if (proposal.kind === 'revert') {
      undo = previewRevert(proposal.id);
    }

    state.pending = { proposal: proposal, undo: undo };

    pendingBar.hidden = false;
    pendingBar.innerHTML = '';
    pendingBar.appendChild(el('div', 'agent-pending-note', proposal.note || 'Pending change'));

    var row = el('div', 'agent-pending-actions');
    var keep = el('button', 'agent-keep', proposal.kind === 'revert' ? 'Remove for good' : 'Keep');
    keep.addEventListener('click', function () { keepPending(false); });
    row.appendChild(keep);

    if (proposal.kind === 'component') {
      var reuse = el('button', 'agent-keep agent-keep-reuse', 'Keep + reuse monthly');
      reuse.title = 'Also save the recipe to the component library so future reports can include it';
      reuse.addEventListener('click', function () { keepPending(true); });
      row.appendChild(reuse);
    }

    var discard = el('button', 'agent-discard', 'Discard');
    discard.addEventListener('click', function () {
      clearPending();
      say('assistant', 'Discarded — the page is back as it was.');
    });
    row.appendChild(discard);
    pendingBar.appendChild(row);

    var target = document.querySelector('[data-agent-component="preview"]')
      || (proposal.ops && proposal.ops[0] && nodes(proposal.ops[0].selector)[0]);
    if (target && target.scrollIntoView) target.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  function previewRevert(id) {
    var node = document.querySelector('[data-agent-component="' + id + '"]');
    if (node) {
      var parent = node.parentNode;
      var next = node.nextSibling;
      parent.removeChild(node);
      return function () { parent.insertBefore(node, next); };
    }
    return null;
  }

  function clearPending() {
    if (state.pending && state.pending.undo) state.pending.undo();
    state.pending = null;
    pendingBar.hidden = true;
    pendingBar.innerHTML = '';
  }

  function keepPending(reusable) {
    if (!state.pending) return;
    var proposal = state.pending.proposal;

    api(BASE + '/apply', {
      method: 'POST',
      body: JSON.stringify({ proposal: proposal, reusable: !!reusable }),
    }).then(function (r) { return r.json(); }).then(function (data) {
      if (!data.ok) { say('assistant', 'Could not save: ' + (data.error || 'unknown error')); return; }

      // Drop the pending styling and re-apply it as a saved change, so the
      // outline goes away and the undo handle belongs to the stored record.
      if (state.pending && state.pending.undo) state.pending.undo();
      state.pending = null;
      pendingBar.hidden = true;
      pendingBar.innerHTML = '';

      if (proposal.kind === 'style') {
        applyPatch(data.saved, false);
        state.overrides.patches.push(data.saved);
      } else if (proposal.kind === 'component') {
        applyComponent(data.saved, false, data.saved.id);
        state.overrides.components.push(data.saved);
      } else if (proposal.kind === 'revert') {
        state.overrides.patches = state.overrides.patches.filter(function (p) { return p.id !== proposal.id; });
        state.overrides.components = state.overrides.components.filter(function (c) { return c.id !== proposal.id; });
      }

      say('assistant', proposal.kind === 'revert'
        ? 'Removed.'
        : 'Saved' + (reusable ? ' — and added to the component library for future reports.' : ' to this report.'));
    }).catch(function (err) {
      say('assistant', 'Could not save: ' + err.message);
    });
  }

  function showChanges() {
    var all = []
      .concat(state.overrides.patches.map(function (p) { return { id: p.id, label: p.note || 'Style change' }; }))
      .concat(state.overrides.components.map(function (c) { return { id: c.id, label: c.title }; }));

    if (!all.length) { say('assistant', 'No saved changes on this report yet.'); return; }

    var bubble = say('assistant', '<strong>Saved changes</strong>', true);
    all.forEach(function (item) {
      var row = el('div', 'agent-change-row');
      row.appendChild(el('span', null, item.label));
      if (canEdit) {
        var drop = el('button', 'agent-discard', 'Remove');
        drop.addEventListener('click', function () {
          api(BASE + '/change/' + item.id, { method: 'DELETE' })
            .then(function (r) { return r.json(); })
            .then(function () { row.remove(); location.reload(); });
        });
        row.appendChild(drop);
      }
      bubble.appendChild(row);
    });
  }

  function saveReport() {
    var clone = document.documentElement.cloneNode(true);
    ['.agent-dock', '#agent-override-styles', 'script[data-agent-dock]', 'link[data-agent-dock]']
      .forEach(function (sel) {
        Array.prototype.slice.call(clone.querySelectorAll(sel)).forEach(function (n) { n.remove(); });
      });
    Array.prototype.slice.call(clone.querySelectorAll('.agent-component')).forEach(function (n) {
      n.classList.remove('is-pending');
    });

    status('Saving…');
    api('/save-report/' + encodeURIComponent(CTX.sessionId) + '/' + encodeURIComponent(CTX.filename), {
      method: 'POST',
      body: JSON.stringify({ html: '<!DOCTYPE html>' + clone.outerHTML }),
    }).then(function (r) { return r.json(); }).then(function (data) {
      status('');
      say('assistant', data.ok ? 'Baked every change into the report file.' : 'Save failed: ' + data.error);
    }).catch(function (err) { status(''); say('assistant', 'Save failed: ' + err.message); });
  }

  /* --------------------------------------------------------------- boot -- */

  function replay() {
    api(BASE + '/state').then(function (r) { return r.json(); }).then(function (data) {
      if (!data.ok) return;
      state.overrides = data.overrides || { patches: [], components: [] };

      (state.overrides.components || []).forEach(function (component) {
        applyComponent(component, false, component.id);
      });
      (state.overrides.patches || []).forEach(function (patch) {
        applyPatch(patch, false);
      });

      /* Components promoted to the library are opted in for every report, so
         apply any whose target section exists here and which is not already
         saved on this report. */
      var seen = {};
      (state.overrides.components || []).forEach(function (c) { seen[c.title] = true; });
      (data.library || []).forEach(function (component) {
        if (seen[component.title]) return;
        if (!nodes(component.target).length) return;
        applyComponent(component, false, 'lib_' + component.slug);
      });

      if (!data.aiAvailable) {
        say('assistant', 'No LLM provider is configured, so I cannot answer yet — set OPENAI_API_KEY or DEEPSEEK_API_KEY on the server.');
      }
    }).catch(function () { /* a report opened without its server simply has no dock data */ });
  }

  function boot() {
    build();
    replay();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
}());
