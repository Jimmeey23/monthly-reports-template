/* =============================================================================
   agent/index.js — HTTP surface for the in-report agent
   -----------------------------------------------------------------------------
   Mounted at /agent by server.js. Question answering streams over SSE so the
   dock can show each query as it runs; everything that writes is a plain POST
   guarded by the session's edit token.

   The token is the editor gate: it is minted per session on disk and injected
   into the page only when the report is opened by its owner, never when a
   presentation viewer follows a /join/:code link. A read-only viewer still gets
   the full chat — it simply cannot reach the write routes.
   ========================================================================== */
'use strict';

const crypto = require('crypto');
const express = require('express');
const fs = require('fs');
const path = require('path');

const loop = require('./loop');
const overrides = require('./overrides');
const { hasAnyProvider } = require('../llm_providers');

const CSV_NAMES = ['sales', 'sessions', 'checkins', 'leads', 'new', 'lapsed', 'active'];

/** Per-session secret, created on first use and kept beside the uploads. */
function editToken(sessionDir) {
  const file = path.join(sessionDir, 'agent-edit-token');
  try {
    return fs.readFileSync(file, 'utf8').trim();
  } catch (e) {
    const token = crypto.randomBytes(24).toString('hex');
    try { fs.writeFileSync(file, token); } catch (writeErr) { /* fall through to a volatile token */ }
    return token;
  }
}

function tokenFrom(req) {
  return String(
    req.get('x-agent-edit-token')
    || (req.body && req.body.editToken)
    || req.query.editToken
    || '',
  ).trim();
}

function createAgentRouter({ getSession }) {
  const router = express.Router();

  /* Resolve :sessionId/:filename once for every route below. */
  function withCtx(req, res, next) {
    const session = getSession(req.params.sessionId);
    if (!session) return res.status(404).json({ error: 'Session not found.' });

    const filename = path.basename(req.params.filename || '');
    const reportPath = path.join(session.dir, filename);
    if (!reportPath.startsWith(session.dir)) return res.status(400).json({ error: 'Invalid path.' });
    if (!fs.existsSync(reportPath)) return res.status(404).json({ error: 'Report not found.' });

    const expected = editToken(session.dir);
    const meta = readReportMeta(session, filename);

    req.agent = {
      sessionId: session.sessionId,
      sessionDir: session.dir,
      filename,
      reportPath,
      analysisPath: session.analysisPath,
      csvDir: session.dir,
      canEdit: tokenFrom(req) === expected,
      locKey: meta.locKey,
      monthKey: meta.monthKey,
      locName: meta.locName,
      monthLabel: meta.monthLabel,
    };
    next();
  }

  /* The studio/month the report is about, taken from the bootstrap the
     generator already writes into the file. */
  function readReportMeta(session, filename) {
    try {
      const head = fs.readFileSync(path.join(session.dir, filename), 'utf8').slice(0, 400000);
      const match = head.match(/window\.__REPORT_META__\s*=\s*(\{[\s\S]*?\});/);
      if (match) {
        const meta = JSON.parse(match[1]);
        return {
          locKey: meta.locKey,
          monthKey: meta.monthKey,
          locName: meta.shortName,
          monthLabel: meta.monthKey,
        };
      }
    } catch (e) { /* a report without the bootstrap still chats, just less grounded */ }
    return {};
  }

  function requireEdit(req, res, next) {
    if (!req.agent.canEdit) return res.status(403).json({ error: 'Read-only viewer: editing is disabled.' });
    next();
  }

  /* -------------------------------------------------------------- state -- */

  router.get('/:sessionId/:filename/state', withCtx, (req, res) => {
    const { sessionDir, filename, canEdit } = req.agent;
    res.json({
      ok: true,
      canEdit,
      aiAvailable: hasAnyProvider(),
      overrides: overrides.load(sessionDir, filename),
      library: overrides.listLibrary().filter(c => c.autoApply),
      csvs: CSV_NAMES.filter(n => fs.existsSync(path.join(sessionDir, `${n}.csv`))),
    });
  });

  /* ---------------------------------------------------------- chat (SSE) -- */

  router.post('/:sessionId/:filename/message', withCtx, async (req, res) => {
    const message = String((req.body && req.body.message) || '').trim();
    if (!message) return res.status(400).json({ error: 'Empty message.' });

    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache, no-transform',
      Connection: 'keep-alive',
      'X-Accel-Buffering': 'no',
    });
    const send = (event) => {
      res.write(`data: ${JSON.stringify(event).replace(/\n/g, ' ')}\n\n`);
    };

    try {
      await loop.runTurn({ message, ctx: req.agent, emit: send });
    } catch (e) {
      send({ type: 'error', error: e.message, code: e.code || null });
    }
    res.end();
  });

  router.post('/:sessionId/:filename/reset', withCtx, (req, res) => {
    loop.resetThread(req.agent.sessionId, req.agent.filename);
    res.json({ ok: true });
  });

  /* ------------------------------------------------------------- writes -- */

  /** The user pressed Keep: turn a pending proposal into a stored override. */
  router.post('/:sessionId/:filename/apply', withCtx, requireEdit, (req, res) => {
    const { sessionDir, filename } = req.agent;
    const proposal = (req.body && req.body.proposal) || {};

    try {
      if (proposal.kind === 'style') {
        const problem = require('./tools').validateOps(proposal.ops);
        if (problem) return res.status(400).json({ error: problem });
        return res.json({ ok: true, saved: overrides.addPatch(sessionDir, filename, {
          kind: 'style', note: proposal.note || 'Style change', ops: proposal.ops,
        }) });
      }

      if (proposal.kind === 'component') {
        const c = proposal.component || {};
        if (!c.html || !c.target || !c.title) {
          return res.status(400).json({ error: 'component needs title, target and html' });
        }
        const saved = overrides.addComponent(sessionDir, filename, c);
        if (req.body.reusable) overrides.saveToLibrary(Object.assign({}, c, { sourceId: saved.id }));
        return res.json({ ok: true, saved, reusable: !!req.body.reusable });
      }

      if (proposal.kind === 'revert') {
        const dropped = overrides.remove(sessionDir, filename, proposal.id);
        if (!dropped) return res.status(404).json({ error: `no change with id ${proposal.id}` });
        return res.json({ ok: true, removed: dropped });
      }

      return res.status(400).json({ error: `unknown proposal kind: ${proposal.kind}` });
    } catch (e) {
      return res.status(500).json({ error: e.message });
    }
  });

  router.delete('/:sessionId/:filename/change/:id', withCtx, requireEdit, (req, res) => {
    const removed = overrides.remove(req.agent.sessionDir, req.agent.filename, req.params.id);
    if (!removed) return res.status(404).json({ error: 'No such change.' });
    res.json({ ok: true, removed });
  });

  /** Promote an already-saved component to the reusable library. */
  router.post('/:sessionId/:filename/library', withCtx, requireEdit, (req, res) => {
    const entry = overrides.load(req.agent.sessionDir, req.agent.filename);
    const component = entry.components.find(c => c.id === req.body.componentId);
    if (!component) return res.status(404).json({ error: 'No such component.' });
    res.json({ ok: true, library: overrides.saveToLibrary(component) });
  });

  router.get('/library', (req, res) => res.json({ ok: true, components: overrides.listLibrary() }));

  router.delete('/library/:slug', (req, res) => {
    res.json({ ok: overrides.removeFromLibrary(req.params.slug) });
  });

  return router;
}

module.exports = { createAgentRouter, editToken };
