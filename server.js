const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const multer = require('multer');
const { execFile } = require('child_process');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const os = require('os');

// Basic .env file loader
if (fs.existsSync(path.join(__dirname, '.env'))) {
  const envConfig = fs.readFileSync(path.join(__dirname, '.env'), 'utf8');
  for (const line of envConfig.split('\n')) {
    const match = line.match(/^\s*([\w.-]+)\s*=\s*(.*)?\s*$/);
    if (match) {
      const key = match[1];
      let value = (match[2] || '').trim();
      if (value.startsWith('"') && value.endsWith('"')) value = value.slice(1, -1);
      if (value.startsWith("'") && value.endsWith("'")) value = value.slice(1, -1);
      if (!process.env[key]) process.env[key] = value;
    }
  }
}

const { generateInsights } = require('./openai_insights');
const { renderReportToPdf } = require('./pdf_export');

const PORT = Number(process.env.PORT) || 3000;
let activePort = PORT;
const PYTHON = process.env.PYTHON || 'python3';

// Persistent uploads dir — use /uploads inside app dir (works on Railway/Render/VPS)
// Falls back to os.tmpdir() only if /uploads is not writable (e.g. read-only cloud sandbox)
function resolveUploadsDir() {
  const local = path.join(__dirname, 'uploads');
  try {
    fs.mkdirSync(local, { recursive: true });
    fs.accessSync(local, fs.constants.W_OK);
    return local;
  } catch (e) {
    const tmp = path.join(os.tmpdir(), 'report_uploads');
    fs.mkdirSync(tmp, { recursive: true });
    return tmp;
  }
}

const UPLOADS_DIR = resolveUploadsDir();
const ANALYZE_SCRIPT = path.join(__dirname, 'analyze_v2.py');
const GEN_REPORT_SCRIPT = path.join(__dirname, 'gen_report_v2.py');

console.log(`UPLOADS_DIR: ${UPLOADS_DIR}`);

// fieldname -> filename analyze_v2.py expects inside the input dir
const CSV_SLOTS = [
  { field: 'sales', label: 'Sales', filename: 'sales.csv' },
  { field: 'sessions', label: 'Sessions', filename: 'sessions.csv' },
  { field: 'checkins', label: 'Checkins', filename: 'checkins.csv' },
  { field: 'leads', label: 'Leads', filename: 'leads.csv' },
  { field: 'new', label: 'New / Trials', filename: 'new.csv' },
  { field: 'lapsed', label: 'Lapsed', filename: 'lapsed.csv' },
  { field: 'active', label: 'Active', filename: 'active.csv' },
];

// sessionId -> { sessionId, dir, analysisPath, locations, months }
const sessions = new Map();

function getSession(sessionId) {
  if (!sessionId || sessionId === 'undefined') return null;
  if (sessions.has(sessionId)) {
    const s = sessions.get(sessionId);
    s.sessionId = sessionId;
    s.dir = path.join(UPLOADS_DIR, sessionId);
    s.analysisPath = path.join(s.dir, 'analysis.json');
    return s;
  }

  // Fallback: reload from disk if in-memory map was cleared (e.g. server restart)
  const sessionDir = path.join(UPLOADS_DIR, sessionId);
  const sessionFile = path.join(sessionDir, 'session.json');
  if (fs.existsSync(sessionFile)) {
    try {
      const data = JSON.parse(fs.readFileSync(sessionFile, 'utf8'));
      data.sessionId = sessionId;
      data.dir = sessionDir;
      data.analysisPath = path.join(sessionDir, 'analysis.json');
      sessions.set(sessionId, data);
      return data;
    } catch (e) {}
  }

  // Secondary fallback: check if analysis.json exists directly in sessionDir
  const analysisPath = path.join(sessionDir, 'analysis.json');
  if (fs.existsSync(analysisPath)) {
    try {
      const analysis = JSON.parse(fs.readFileSync(analysisPath, 'utf8'));
      if (analysis.meta) {
        const data = {
          sessionId,
          dir: sessionDir,
          analysisPath,
          locations: analysis.meta.locations || {},
          months: analysis.meta.months || [],
        };
        saveSession(sessionId, data);
        return data;
      }
    } catch (e) {}
  }

  return null;
}

const MANIFEST_PATH = path.join(UPLOADS_DIR, 'sessions_manifest.json');

function loadManifest() {
  let manifest = [];
  if (fs.existsSync(MANIFEST_PATH)) {
    try {
      manifest = JSON.parse(fs.readFileSync(MANIFEST_PATH, 'utf8'));
    } catch (e) {
      manifest = [];
    }
  }

  // Filter out any broken items with missing or string 'undefined' sessionId
  manifest = manifest.filter((s) => s && s.sessionId && s.sessionId !== 'undefined');

  // Discover sessions on disk in UPLOADS_DIR
  try {
    if (fs.existsSync(UPLOADS_DIR)) {
      const entries = fs.readdirSync(UPLOADS_DIR, { withFileTypes: true });
      for (const entry of entries) {
        if (entry.isDirectory()) {
          const sid = entry.name;
          const index = manifest.findIndex((s) => s.sessionId === sid);

          const sessionDir = path.join(UPLOADS_DIR, sid);
          const sessionFile = path.join(sessionDir, 'session.json');
          const analysisFile = path.join(sessionDir, 'analysis.json');

          let sData = null;
          if (fs.existsSync(sessionFile)) {
            try {
              sData = JSON.parse(fs.readFileSync(sessionFile, 'utf8'));
            } catch (e) {}
          } else if (fs.existsSync(analysisFile)) {
            try {
              const analysis = JSON.parse(fs.readFileSync(analysisFile, 'utf8'));
              if (analysis.meta) {
                sData = {
                  locations: analysis.meta.locations || {},
                  months: analysis.meta.months || [],
                };
              }
            } catch (e) {}
          }

          if (sData && sData.locations) {
            const locNames = Object.values(sData.locations || {}).map((l) => l.split(',')[0].trim());
            let mtime = Date.now();
            try {
              mtime = fs.statSync(sessionDir).mtimeMs;
            } catch (e) {}

            const item = {
              sessionId: sid,
              locations: sData.locations || {},
              locNames,
              months: sData.months || [],
              created: sData.created || mtime,
            };

            // Fix/update session.json on disk to guarantee sessionId field is present
            try {
              const fullData = {
                sessionId: sid,
                dir: sessionDir,
                analysisPath: analysisFile,
                locations: sData.locations || {},
                months: sData.months || [],
                created: item.created,
              };
              fs.writeFileSync(sessionFile, JSON.stringify(fullData, null, 2));
            } catch (e) {}

            if (index >= 0) {
              manifest[index] = { ...manifest[index], ...item };
            } else {
              manifest.push(item);
            }
          }
        }
      }
    }
  } catch (err) {
    console.error('Error scanning UPLOADS_DIR in loadManifest:', err.message);
  }

  manifest.sort((a, b) => (b.created || 0) - (a.created || 0));

  try {
    fs.writeFileSync(MANIFEST_PATH, JSON.stringify(manifest.slice(0, 30), null, 2));
  } catch (e) {}

  return manifest;
}

function updateManifest(sessionData) {
  if (!sessionData || !sessionData.sessionId) return;
  const manifest = loadManifest();
  const index = manifest.findIndex((s) => s.sessionId === sessionData.sessionId);
  const locNames = Object.values(sessionData.locations || {}).map((l) => l.split(',')[0].trim());
  const item = {
    sessionId: sessionData.sessionId,
    locations: sessionData.locations || {},
    locNames,
    months: sessionData.months || [],
    created: sessionData.created || Date.now(),
  };
  if (index >= 0) {
    manifest[index] = { ...manifest[index], ...item };
  } else {
    manifest.unshift(item);
  }
  try {
    fs.writeFileSync(MANIFEST_PATH, JSON.stringify(manifest.slice(0, 30), null, 2));
  } catch (e) {}
}

function saveSession(sessionId, sessionData) {
  sessionData.sessionId = sessionId;
  sessionData.dir = path.join(UPLOADS_DIR, sessionId);
  sessionData.analysisPath = path.join(sessionData.dir, 'analysis.json');
  sessions.set(sessionId, sessionData);
  try {
    const sessionFile = path.join(sessionData.dir, 'session.json');
    fs.writeFileSync(sessionFile, JSON.stringify(sessionData, null, 2));
    updateManifest(sessionData);
  } catch (e) {}
}

function runPythonScript(scriptPath, args, callback) {
  execFile(PYTHON, [scriptPath, ...args], { maxBuffer: 1024 * 1024 * 100 }, callback);
}

// Use memoryStorage — writes buffers directly to disk avoiding any temp file dependency
const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 10 * 1024 * 1024 }, // 10 MB per chunk — chunks are 1.5 MB each
});

function assignSessionId(req, res, next) {
  req.sessionId = crypto.randomUUID();
  next();
}

const app = express();
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
  res.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  if (req.method === 'OPTIONS') return res.sendStatus(200);
  next();
});

app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));
app.use(express.static(path.join(__dirname, 'public')));
app.use(express.urlencoded({ extended: true }));
app.use(express.json({ limit: '5mb' }));

// ─── Routes ────────────────────────────────────────────────────────────────────

app.get('/july-report/:studio', (req, res) => {
  const files = {
    kwality: path.join('public', 'revised-july', 'kwality-house-july-2026.html'),
    supreme: path.join('public', 'revised-july', 'supreme-hq-bandra-july-2026.html'),
  };
  const filename = files[req.params.studio];
  const isBothView = req.params.studio === 'both';
  if (!filename && !isBothView) return res.status(404).send('Report not found.');
  const shouldEmbed = req.query.embed === '1';
  const protocol = req.headers['x-forwarded-proto'] || req.protocol;
  const host = req.headers.host || `localhost:${activePort}`;
  const serverUrl = process.env.SERVER_URL || `${protocol}://${host}`;
  const embeddedCss = `<style>
    .topbar,
    .editor-toolbar,
    .presenter-bar,
    .presenter-modal,
    .annotation-canvas,
    .pdf-btn,
    .topbar-actions,
    .hm-controls {
      display: none !important;
    }
    body {
      padding-top: 0 !important;
      margin: 0 !important;
      overflow-x: hidden;
      zoom: 1;
    }
    .hero {
      padding-top: 24px !important;
    }
    .hero::before,
    .hero::after,
    .section-hero::after {
      display: none !important;
      content: none !important;
    }
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
    .section-hero.is-stuck .section-title {
      font-size: inherit !important;
    }
    .section-hero.is-stuck .section-deck {
      display: block !important;
    }
    .container {
      max-width: 1560px !important;
      width: min(calc(100% - clamp(140px, 14vw, 320px)), 1560px) !important;
      margin-left: auto !important;
      margin-right: auto !important;
      padding-left: 0 !important;
      padding-right: 0 !important;
      box-sizing: border-box !important;
    }
    .headline-kpi-matrix {
      left: auto !important;
      width: 100% !important;
      max-width: 100% !important;
      transform: none !important;
    }
    .headline-kpi-matrix .table-wrap {
      width: 100% !important;
      max-width: 100% !important;
      overflow-x: auto !important;
    }
    .headline-kpi-matrix table.data-table {
      width: 100% !important;
      min-width: 1320px !important;
    }
    table.data-table {
      table-layout: auto !important;
    }
    table.data-table thead th,
    table.data-table tbody td,
    .appendix-body table.data-table thead th,
    .appendix-body table.data-table tbody td {
      text-align: center !important;
    }
    table.data-table thead th:first-child,
    table.data-table tbody td:first-child,
    table.data-table tbody td.metric-name,
    .appendix-body table.data-table thead th:first-child,
    .appendix-body table.data-table tbody td:first-child {
      width: clamp(190px, 24%, 340px) !important;
      min-width: 190px !important;
      text-align: left !important;
    }
    table.data-table thead th:not(:first-child),
    table.data-table tbody td:not(:first-child) {
      min-width: 96px !important;
    }
    @media (max-width: 760px) {
      .container {
        width: min(calc(100% - 44px), 1680px) !important;
      }
      .headline-kpi-matrix table.data-table {
        min-width: 1120px !important;
      }
    }
    .july-presenter-session-bar {
      position: fixed !important;
      top: 12px !important;
      left: 50% !important;
      transform: translateX(-50%) !important;
      z-index: 99999 !important;
      display: flex !important;
      align-items: center !important;
      justify-content: space-between !important;
      gap: 10px !important;
      width: auto !important;
      max-width: min(620px, calc(100vw - 24px)) !important;
      min-height: 36px !important;
      max-height: 46px !important;
      overflow: hidden !important;
      padding: 5px 8px 5px 12px !important;
      border: 1px solid var(--border) !important;
      border-radius: 999px !important;
      background: color-mix(in srgb, var(--bg-card) 94%, white 6%) !important;
      color: var(--text) !important;
      box-shadow: 0 10px 26px rgba(15, 23, 42, 0.16) !important;
      font: 400 12px var(--font-sans) !important;
      line-height: 1.15 !important;
      white-space: nowrap !important;
    }
    .july-presenter-session-bar > div:first-child {
      min-width: 0 !important;
      overflow: hidden !important;
      text-overflow: ellipsis !important;
    }
    .july-session-actions {
      display: inline-flex !important;
      align-items: center !important;
      gap: 5px !important;
      flex-shrink: 0 !important;
    }
    .july-session-code {
      display: inline-flex !important;
      align-items: center !important;
      justify-content: center !important;
      min-height: 24px !important;
      padding: 2px 8px !important;
      border-radius: 999px !important;
      background: var(--primary-soft) !important;
      color: var(--primary) !important;
      font-family: var(--font-mono) !important;
      font-weight: 400 !important;
      text-align: center !important;
    }
    .july-presenter-session-bar button {
      min-height: 24px !important;
      display: inline-flex !important;
      align-items: center !important;
      justify-content: center !important;
      border: 1px solid var(--border) !important;
      border-radius: 999px !important;
      background: var(--bg-inset) !important;
      color: var(--text) !important;
      padding: 3px 8px !important;
      font: 400 11px/1 var(--font-sans) !important;
      text-align: center !important;
      cursor: pointer !important;
    }
    .july-presenter-session-active {
      padding-top: 44px !important;
    }
    .july-route-controls-visible {
      padding-top: 68px !important;
    }
    .july-route-controls-visible.july-presenter-session-active {
      padding-top: 114px !important;
    }
    .july-presenter-session-active .july-report-route-controls {
      top: 58px !important;
    }
    .july-report-route-controls {
      position: fixed !important;
      top: 12px !important;
      left: 50% !important;
      transform: translateX(-50%) !important;
      z-index: 99998 !important;
      display: flex !important;
      align-items: center !important;
      gap: 8px !important;
      max-width: min(920px, calc(100vw - 24px)) !important;
      padding: 7px !important;
      border: 1px solid var(--border) !important;
      border-radius: 999px !important;
      background: color-mix(in srgb, var(--bg-card) 94%, white 6%) !important;
      color: var(--text) !important;
      box-shadow: 0 16px 38px rgba(15, 23, 42, 0.16) !important;
      backdrop-filter: blur(16px) !important;
      font-family: var(--font-sans) !important;
      white-space: nowrap !important;
    }
    .july-report-route-tabs,
    .july-report-session-actions {
      display: inline-flex !important;
      align-items: center !important;
      gap: 5px !important;
    }
    .july-report-route-controls a,
    .july-report-route-controls button {
      min-height: 30px !important;
      display: inline-flex !important;
      align-items: center !important;
      justify-content: center !important;
      border: 1px solid var(--border) !important;
      border-radius: 999px !important;
      background: var(--bg-inset) !important;
      color: var(--text) !important;
      padding: 6px 11px !important;
      font: 400 11px/1 var(--font-sans) !important;
      line-height: 1 !important;
      text-align: center !important;
      text-decoration: none !important;
      cursor: pointer !important;
    }
    .july-report-route-controls a.is-active,
    .july-report-route-controls button.primary {
      background: var(--primary) !important;
      border-color: var(--primary) !important;
      color: #fff !important;
    }
    .july-report-route-controls input {
      width: 86px !important;
      min-height: 30px !important;
      border: 1px solid var(--border) !important;
      border-radius: 999px !important;
      background: var(--bg-card) !important;
      color: var(--text) !important;
      padding: 5px 10px !important;
      font: 400 12px/1 var(--font-mono) !important;
      text-align: center !important;
      letter-spacing: 0.08em !important;
    }
    .july-report-route-divider {
      width: 1px !important;
      height: 24px !important;
      background: var(--border) !important;
    }
    .july-viewer-locked .july-presenter-session-bar,
    .july-viewer-locked .july-presenter-session-bar * {
      pointer-events: auto !important;
    }
    @media (max-width: 640px) {
      .july-presenter-session-bar {
        top: 8px !important;
        max-width: calc(100vw - 16px) !important;
        max-height: 40px !important;
        gap: 6px !important;
        padding: 4px 6px 4px 10px !important;
      }
      .july-presenter-session-bar strong { display: none !important; }
      .july-report-route-controls {
        top: 8px !important;
        max-width: calc(100vw - 16px) !important;
        overflow-x: auto !important;
        justify-content: flex-start !important;
      }
      .july-report-route-controls a,
      .july-report-route-controls button {
        padding-inline: 9px !important;
      }
    }
  </style>`;
  const embeddedScript = `<script>
    (function () {
      document.documentElement.setAttribute('data-theme', 'light');
      try {
        localStorage.setItem('kh-theme', 'light');
      } catch (error) {}
    })();
  </script>`;
  const routeControlsScript = shouldEmbed ? '' : `<script>
    (function () {
      var current = ${JSON.stringify(req.params.studio)};
      var bar = document.createElement('div');
      bar.className = 'july-report-route-controls';
      bar.innerHTML =
        '<div class="july-report-route-tabs" aria-label="Report view">' +
          '<a href="/july-report/kwality" data-view="kwality">Kemps</a>' +
          '<a href="/july-report/supreme" data-view="supreme">Bandra</a>' +
          '<a href="/july-report/both" data-view="both">Both</a>' +
        '</div>' +
        '<span class="july-report-route-divider" aria-hidden="true"></span>' +
        '<div class="july-report-session-actions">' +
          '<button type="button" class="primary" id="july-host-report">Host</button>' +
          '<input id="july-join-code-input" inputmode="numeric" maxlength="6" placeholder="Code" aria-label="Join code">' +
          '<button type="button" id="july-join-report">Join</button>' +
        '</div>';
      document.body.appendChild(bar);
      document.body.classList.add('july-route-controls-visible');
      bar.querySelectorAll('[data-view]').forEach(function (link) {
        link.classList.toggle('is-active', link.getAttribute('data-view') === current);
      });
      document.getElementById('july-host-report').addEventListener('click', function () {
        var url = new URL(window.location.href);
        url.searchParams.set('host', '1');
        url.searchParams.delete('roomCode');
        window.location.href = url.toString();
      });
      document.getElementById('july-join-report').addEventListener('click', function () {
        var input = document.getElementById('july-join-code-input');
        var code = (input.value || '').replace(/\\D/g, '').slice(0, 6);
        if (code.length === 6) window.location.href = '/join/' + code;
        else input.focus();
      });
    })();
  </script>`;
  const presenterScript = `<script src="/socket.io/socket.io.js"></script>
  <script>
    (function () {
      if (typeof io === 'undefined') return;
      var params = new URLSearchParams(window.location.search);
      var shouldHost = params.get('host') === '1';
      var roomCode = params.get('roomCode');
      if (!shouldHost && !roomCode) return;

      var socket = io(${JSON.stringify(serverUrl)});
      var role = shouldHost ? 'presenter' : 'viewer';
      var code = shouldHost ? String(Math.floor(100000 + Math.random() * 900000)) : roomCode;
      var reportUrl = window.location.pathname;
      var scrollTicking = false;

      var bar = document.createElement('div');
      bar.className = 'july-presenter-session-bar';
      bar.innerHTML =
        '<div><strong>' + (role === 'presenter' ? 'Hosting July report' : 'Joined July report') + '</strong>' +
        '<span id="july-session-status"></span></div>' +
        '<div class="july-session-actions"><span class="july-session-code">Code: ' + code + '</span>' +
        '<button type="button" id="july-copy-code">Copy</button>' +
        (role === 'presenter' ? '<button type="button" id="july-end-session">End Hosting</button>' : '') +
        '<button type="button" id="july-leave-session">Leave</button></div>';
      document.body.appendChild(bar);
      document.body.classList.add('july-presenter-session-active');
      if (role === 'viewer') document.body.classList.add('july-viewer-locked');

      socket.emit('join_room', { role: role, code: code, reportUrl: reportUrl });
      socket.on('room_state', function (state) {
        var status = document.getElementById('july-session-status');
        if (status) status.textContent = role === 'presenter' ? ' · ' + state.viewers + ' viewers' : ' · viewing host screen';
      });
      socket.on('presenter_sync', function (data) {
        if (role !== 'viewer') return;
        if (data.type === 'scroll') window.scrollTo(0, data.scrollY);
        if (data.type === 'click') {
          var el = document.elementFromPoint(data.x, data.y);
          if (el && typeof el.click === 'function' && !el.closest('.july-presenter-session-bar')) el.click();
        }
      });

      window.addEventListener('scroll', function () {
        if (role !== 'presenter' || scrollTicking) return;
        window.requestAnimationFrame(function () {
          socket.emit('presenter_event', { type: 'scroll', scrollY: window.scrollY });
          scrollTicking = false;
        });
        scrollTicking = true;
      });
      document.addEventListener('click', function (event) {
        if (role !== 'presenter' || !event.isTrusted || event.target.closest('.july-presenter-session-bar')) return;
        socket.emit('presenter_event', { type: 'click', x: event.clientX, y: event.clientY });
      });

      document.getElementById('july-copy-code').addEventListener('click', function () {
        if (navigator.clipboard) navigator.clipboard.writeText(code);
      });
      var endButton = document.getElementById('july-end-session');
      if (endButton) {
        endButton.addEventListener('click', function () {
          socket.emit('leave_room', { code: code, endSession: true });
          window.location.href = reportUrl;
        });
      }
      document.getElementById('july-leave-session').addEventListener('click', function () {
        socket.emit('leave_room', { code: code, endSession: role === 'presenter' });
        window.location.href = role === 'presenter' ? reportUrl : '/july-report/' + (reportUrl.indexOf('supreme') !== -1 ? 'supreme' : 'kwality');
      });
    })();
  </script>`;
  if (isBothView) {
    const bothHtml = `<!DOCTYPE html>
<html data-theme="light" lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>July 2026 Reports · Both Studios</title>
  <style>
    :root { --bg:#f2f2f2; --bg-card:#fffefa; --bg-inset:#f1efe8; --border:rgba(21,23,28,.12); --text:#15171c; --text-muted:#62656d; --primary:#005fef; --font-sans:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; --font-mono:"SFMono-Regular",Consolas,monospace; }
    * { box-sizing:border-box; }
    body { margin:0; background:var(--bg); color:var(--text); font-family:var(--font-sans); overflow:hidden; }
    .july-both-grid { display:grid; grid-template-columns:1fr 1fr; gap:1px; height:100vh; padding-top:0; background:var(--border); }
    .july-both-panel { min-width:0; min-height:0; display:flex; flex-direction:column; background:var(--bg-card); }
    .july-both-label { height:32px; display:flex; align-items:center; padding:0 14px; border-bottom:1px solid var(--border); color:var(--text-muted); font:800 11px var(--font-sans); letter-spacing:.08em; text-transform:uppercase; }
    iframe { width:100%; height:100%; border:0; background:white; }
    .july-route-controls-visible .july-both-grid { height:calc(100vh - 68px); }
    @media (max-width:900px) { body { overflow:auto; } .july-both-grid { grid-template-columns:1fr; height:auto; } .july-both-panel { height:80vh; } }
  </style>
  ${embeddedCss}
</head>
<body>
  <div class="july-both-grid">
    <section class="july-both-panel"><div class="july-both-label">Kemps Corner · Kwality House</div><iframe src="/july-report/kwality?embed=1" title="Kemps Corner July 2026 report"></iframe></section>
    <section class="july-both-panel"><div class="july-both-label">Bandra · Supreme HQ</div><iframe src="/july-report/supreme?embed=1" title="Supreme HQ Bandra July 2026 report"></iframe></section>
  </div>
  ${embeddedScript}${routeControlsScript}${presenterScript}
</body>
</html>`;
    return res.type('html').send(bothHtml);
  }

  const reportPath = path.join(__dirname, filename);
  if (!fs.existsSync(reportPath)) return res.status(404).send('Report file missing.');
  let html = fs.readFileSync(reportPath, 'utf8');
  html = html
    .replace(/<html([^>]*?)data-theme=(["'])dark\2([^>]*)>/i, '<html$1data-theme="light"$3>')
    .replace(/<script>window\.__REPORT_CTX__[\s\S]*?<\/script>\s*/g, '')
    .replace(/<script src="\/socket\.io\/socket\.io\.js"><\/script>\s*/g, '')
    .replace(/<script src="\/report-client\.js"><\/script>\s*/g, '')
    .replace(/<script src="\.\/section-audio\.js[^"]*"><\/script>\s*/g, '')
    .replace(/<script src="\.\/sfx-soundboard\.js[^"]*"><\/script>\s*/g, '')
    .replace('</head>', `${embeddedCss}</head>`);
  const bodyCloseIndex = html.lastIndexOf('</body>');
  if (bodyCloseIndex >= 0) {
    html = `${html.slice(0, bodyCloseIndex)}${embeddedScript}<script src="/revised-july/section-audio.js?v=1"></script><script src="/revised-july/sfx-soundboard.js?v=16"></script><script src="/revised-july/card-notes.js?v=2"></script>${routeControlsScript}${presenterScript}${html.slice(bodyCloseIndex)}`;
  }
  res.type('html').send(html);
});

app.get('/api/saved-sessions', (req, res) => {
  const manifest = loadManifest();
  res.json({ sessions: manifest });
});

app.get('/', (req, res) => {
  res.render('upload', { slots: CSV_SLOTS, error: null });
});

app.get('/select', (req, res) => {
  const sessionId = req.query.sessionId;
  const session = getSession(sessionId);
  if (!session) return res.redirect('/');
  res.render('select', {
    sessionId,
    locations: session.locations,
    months: [...session.months].reverse(),
    error: null,
  });
});

// Chunk-based upload: receives 1.5 MB binary blobs and appends them to the target CSV
app.post('/upload-chunk', upload.single('chunk'), (req, res) => {
  const sessionId = req.body.sessionId;
  const slot = req.body.slot;
  const chunkIndex = parseInt(req.body.chunkIndex || '0', 10);

  if (!sessionId || !slot || !req.file) {
    return res.status(400).json({ error: 'Missing sessionId, slot, or chunk file' });
  }

  const sessionDir = path.join(UPLOADS_DIR, sessionId);
  try { fs.mkdirSync(sessionDir, { recursive: true }); } catch (e) {}

  const slotInfo = CSV_SLOTS.find((s) => s.field === slot);
  const targetFilename = slotInfo ? slotInfo.filename : `${slot}.csv`;
  const targetPath = path.join(sessionDir, targetFilename);

  try {
    if (chunkIndex === 0) {
      fs.writeFileSync(targetPath, req.file.buffer);
    } else {
      fs.appendFileSync(targetPath, req.file.buffer);
    }
  } catch (err) {
    console.error(`chunk write error: ${err.message}`);
    return res.status(500).json({ error: `Failed to write chunk: ${err.message}` });
  }

  res.json({ ok: true, slot, chunkIndex });
});

// Trigger analysis after all CSV files are uploaded
app.post('/analyze-session', (req, res) => {
  const { sessionId } = req.body;
  if (!sessionId) return res.status(400).json({ error: 'Missing sessionId' });

  const sessionDir = path.join(UPLOADS_DIR, sessionId);
  const missing = CSV_SLOTS.filter((s) => !fs.existsSync(path.join(sessionDir, s.filename)));
  if (missing.length) {
    return res.status(400).json({
      error: `Missing CSV file(s): ${missing.map((s) => s.label).join(', ')}`,
    });
  }

  const analysisPath = path.join(sessionDir, 'analysis.json');

  runPythonScript(ANALYZE_SCRIPT, [sessionDir, analysisPath], (err, stdout, stderr) => {
    if (err) {
      console.error(stderr || err.message);
      return res.status(500).json({ error: `Analysis failed: ${stderr || err.message}` });
    }

    let analysis;
    try {
      analysis = JSON.parse(fs.readFileSync(analysisPath, 'utf8'));
    } catch (e) {
      return res.status(500).json({ error: `Could not read analysis output: ${e.message}` });
    }

    const locations = analysis.meta.locations;
    const months = analysis.meta.months;

    if (!Object.keys(locations).length || !months.length) {
      return res.status(400).json({ error: 'No studios or months detected in the uploaded CSVs.' });
    }

    const sessionData = { sessionId, dir: sessionDir, analysisPath, locations, months, created: Date.now() };
    saveSession(sessionId, sessionData);

    res.json({ ok: true, redirectUrl: `/select?sessionId=${sessionId}` });
  });
});

app.post('/generate', async (req, res) => {
  const { sessionId } = req.body;
  const session = getSession(sessionId);
  if (!session) {
    return res.status(400).send('Session expired or not found. Please upload your CSVs again.');
  }

  const selectedLocs = [].concat(req.body.loc || []).filter(Boolean);
  const selectedMonths = [].concat(req.body.month || []).filter(Boolean);
  const invalid =
    !selectedLocs.length ||
    !selectedMonths.length ||
    selectedLocs.some((l) => !session.locations[l]) ||
    selectedMonths.some((m) => !session.months.includes(m));

  if (invalid) {
    return res.render('select', {
      sessionId,
      locations: session.locations,
      months: [...session.months].reverse(),
      error: 'Pick at least one valid studio and month.',
    });
  }

  const comboCount = selectedLocs.length * selectedMonths.length;
  let outputFilename;
  if (comboCount === 1) {
    const shortName = session.locations[selectedLocs[0]].split(',')[0].trim();
    const [year, mon] = selectedMonths[0].split('-');
    const monthName = new Date(Number(year), Number(mon) - 1, 1).toLocaleString('en-US', { month: 'long' });
    outputFilename = `${shortName.replace(/ /g, '_')}_Performance_Report_${monthName}_${year}.html`;
  } else {
    outputFilename = `Performance_Report_Bundle_${comboCount}_reports_${Date.now()}.html`;
  }

  const outputPath = path.join(session.dir, outputFilename);

  // Generate AI Insights AOT for this report
  try {
    const analysis = JSON.parse(fs.readFileSync(session.analysisPath, 'utf8'));
    const sections = ['executive-summary', 'sales-funnel', 'revenue', 'studio-utilization', 'member-retention', 'trial-conversion', 'class-attendance'];
    
    // We'll store a big map of locKey|monthKey|section -> insights
    const aiContext = {};
    const promises = [];

    for (const loc of selectedLocs) {
      for (const month of selectedMonths) {
        for (const sec of sections) {
          promises.push((async () => {
            try {
              const res = await generateInsights(analysis, loc, month, sec);
              const key = loc + '|' + month + '|' + sec;
              aiContext[key] = res;
            } catch (err) {
              console.error('Failed to generate AI for ' + sec, err.message);
            }
          })());
        }
      }
    }

    await Promise.all(promises);

    // Save context to pass to Python
    const aiContextPath = path.join(session.dir, 'ai_context_' + Date.now() + '.json');
    fs.writeFileSync(aiContextPath, JSON.stringify(aiContext));

    runPythonScript(
      GEN_REPORT_SCRIPT,
      [session.analysisPath, selectedLocs.join(','), selectedMonths.join(','), outputPath, aiContextPath],
      (err, stdout, stderr) => {
        if (err) {
        console.error(stderr || err.message);
        return res.render('select', {
          sessionId,
          locations: session.locations,
          months: [...session.months].reverse(),
          error: `Report generation failed: ${stderr || err.message}`,
        });
      }

      try {
        const html = fs.readFileSync(outputPath, 'utf8');
        const protocol = req.headers['x-forwarded-proto'] || 'http';
        const host = req.headers.host || `localhost:${activePort}`;
        const bootstrap = `<script>window.__REPORT_CTX__ = ${JSON.stringify({
          sessionId,
          loc: selectedLocs[0],
          month: selectedMonths[0],
          filename: outputFilename,
          serverUrl: process.env.SERVER_URL || `${protocol}://${host}`,
        })};</script>\n<script src="/socket.io/socket.io.js"></script>\n<script src="/report-client.js"></script>`;
        fs.writeFileSync(outputPath, html.replace('<!-- REPORT_CLIENT_PLACEHOLDER -->', bootstrap));
      } catch (spliceErr) {
        console.error('Could not inject report client script:', spliceErr.message);
      }

      res.render('result', {
        sessionId,
        locs: selectedLocs,
        selectedMonths,
        comboCount,
        locations: session.locations,
        months: [...session.months].reverse(),
        reportUrl: `/report/${sessionId}/${encodeURIComponent(outputFilename)}`,
        pdfUrl: `/download-pdf/${sessionId}/${encodeURIComponent(outputFilename)}`,
        filename: outputFilename,
      });
    }
  );
  } catch (err) {
    console.error('AI insights/report generation failed:', err.message);
    return res.render('select', {
      sessionId,
      locations: session.locations,
      months: [...session.months].reverse(),
      error: `Report generation failed: ${err.message}`,
    });
  }
});

app.get('/download-pdf/:sessionId/:filename', async (req, res) => {
  const session = getSession(req.params.sessionId);
  if (!session) return res.status(404).send('Session not found.');

  const filePath = path.join(session.dir, req.params.filename);
  if (!filePath.startsWith(session.dir) || !fs.existsSync(filePath)) {
    return res.status(404).send('Report not found.');
  }

  try {
    const protocol = req.headers['x-forwarded-proto'] || 'http';
    const host = req.headers.host || `localhost:${activePort}`;
    const reportUrl = `${protocol}://${host}/report/${req.params.sessionId}/${encodeURIComponent(req.params.filename)}`;
    const pdf = await renderReportToPdf(reportUrl);
    const pdfName = req.params.filename.replace(/\.html$/i, '.pdf');
    res.set('Content-Type', 'application/pdf');
    res.set('Content-Disposition', `attachment; filename="${pdfName}"`);
    res.send(Buffer.from(pdf));
  } catch (e) {
    console.error('PDF export failed:', e.message);
    res.status(e.code === 'NO_CHROME' ? 501 : 500).send(`PDF export failed: ${e.message}`);
  }
});

app.post('/ai-insights/:sessionId/:section', async (req, res) => {
  const session = getSession(req.params.sessionId);
  if (!session) return res.status(404).json({ error: 'Session not found.' });

  const { loc, month } = req.body || {};
  if (!session.locations[loc] || !session.months.includes(month)) {
    return res.status(400).json({ error: 'Invalid studio/month for this session.' });
  }

  try {
    const analysis = JSON.parse(fs.readFileSync(session.analysisPath, 'utf8'));
    const result = await generateInsights(analysis, loc, month, req.params.section);
    res.json(result);
  } catch (e) {
    const status = e.code === 'NO_API_KEY' ? 501 : 502;
    res.status(status).json({ error: e.message });
  }
});

app.post('/save-report/:sessionId/:filename', (req, res) => {
  const session = getSession(req.params.sessionId);
  if (!session) return res.status(404).json({ error: 'Session not found.' });

  const { html } = req.body || {};
  if (typeof html !== 'string' || !html.trim()) {
    return res.status(400).json({ error: 'No HTML content provided.' });
  }

  const filePath = path.join(session.dir, req.params.filename);
  if (!filePath.startsWith(session.dir)) return res.status(400).json({ error: 'Invalid path.' });

  try {
    fs.writeFileSync(filePath, html);
    res.json({ ok: true });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.get('/report/:sessionId/:filename', (req, res) => {
  const session = getSession(req.params.sessionId);
  if (!session) return res.status(404).send('Session not found.');
  const filePath = path.join(session.dir, req.params.filename);
  if (!filePath.startsWith(session.dir)) return res.status(400).send('Invalid path.');
  res.sendFile(filePath, (err) => {
    if (err) res.status(404).send('Report not found.');
  });
});

app.get('/download/:sessionId/:filename', (req, res) => {
  const session = getSession(req.params.sessionId);
  if (!session) return res.status(404).send('Session not found.');
  const filePath = path.join(session.dir, req.params.filename);
  if (!filePath.startsWith(session.dir)) return res.status(400).send('Invalid path.');
  res.download(filePath, (err) => {
    if (err) res.status(404).send('Report not found.');
  });
});

app.get('/join/:code', (req, res) => {
  const code = req.params.code;
  const room = presenterRooms[code];
  if (room && room.reportUrl) {
    res.redirect(`${room.reportUrl}?roomCode=${code}`);
  } else {
    res.status(404).send('Session not found or host has not started presenting.');
  }
});

// Health check endpoint
app.get('/health', (req, res) => res.json({ status: 'ok', uploadsDir: UPLOADS_DIR }));

const server = http.createServer(app);
const io = new Server(server, { cors: { origin: '*' } });

const presenterRooms = {};

io.on('connection', (socket) => {
  function leavePresenterRoom({ endSession = false } = {}) {
    const roomCode = socket.roomCode;
    if (!roomCode || !presenterRooms[roomCode]) return;

    if (endSession || socket.role === 'presenter') {
      socket.to(roomCode).emit('presenter_sync', { type: 'session_ended' });
      delete presenterRooms[roomCode];
    } else if (socket.role === 'viewer') {
      presenterRooms[roomCode].viewers = Math.max(0, presenterRooms[roomCode].viewers - 1);
      io.to(roomCode).emit('room_state', presenterRooms[roomCode]);
      if (!presenterRooms[roomCode].presenterId && presenterRooms[roomCode].viewers === 0) {
        delete presenterRooms[roomCode];
      }
    }

    socket.leave(roomCode);
    socket.roomCode = null;
    socket.role = null;
  }

  socket.on('join_room', ({ role, code, reportUrl }) => {
    if (!code) return;
    socket.join(code);
    socket.roomCode = code;
    socket.role = role;

    if (!presenterRooms[code]) {
      presenterRooms[code] = { presenterId: null, viewers: 0, reportUrl: null };
    }

    if (role === 'presenter') {
      presenterRooms[code].presenterId = socket.id;
      if (reportUrl) presenterRooms[code].reportUrl = reportUrl;
    } else {
      presenterRooms[code].viewers++;
    }

    io.to(code).emit('room_state', presenterRooms[code]);
  });

  socket.on('presenter_event', (data) => {
    if (socket.role === 'presenter' && socket.roomCode) {
      socket.to(socket.roomCode).emit('presenter_sync', data);
    }
  });

  socket.on('leave_room', ({ endSession } = {}) => {
    leavePresenterRoom({ endSession: Boolean(endSession) });
  });

  socket.on('disconnect', () => {
    leavePresenterRoom();
  });
});

if (require.main === module) {
  const startServer = (port) => {
    const onError = (error) => {
      server.off('listening', onListening);
      if (error.code === 'EADDRINUSE') {
        console.warn(`Port ${port} is in use. Trying ${port + 1}...`);
        startServer(port + 1);
        return;
      }
      throw error;
    };

    const onListening = () => {
      server.off('error', onError);
      activePort = port;
      console.log(`Studio performance report app running at http://localhost:${activePort}`);
    };

    server.once('error', onError);
    server.once('listening', onListening);
    server.listen(port);
  };

  startServer(PORT);
}

module.exports = { app, server, io };
