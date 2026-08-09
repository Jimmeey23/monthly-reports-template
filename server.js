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

const PORT = process.env.PORT || 3000;
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

// sessionId -> { dir, analysisPath, locations, months }
const sessions = new Map();

function getSession(sessionId) {
  if (!sessionId) return null;
  if (sessions.has(sessionId)) return sessions.get(sessionId);

  // Fallback: reload from disk if in-memory map was cleared (e.g. server restart)
  const sessionDir = path.join(UPLOADS_DIR, sessionId);
  const sessionFile = path.join(sessionDir, 'session.json');
  if (fs.existsSync(sessionFile)) {
    try {
      const data = JSON.parse(fs.readFileSync(sessionFile, 'utf8'));
      sessions.set(sessionId, data);
      return data;
    } catch (e) {}
  }
  return null;
}

function saveSession(sessionId, sessionData) {
  sessions.set(sessionId, sessionData);
  try {
    const sessionFile = path.join(sessionData.dir, 'session.json');
    fs.writeFileSync(sessionFile, JSON.stringify(sessionData));
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

    const sessionData = { dir: sessionDir, analysisPath, locations, months };
    saveSession(sessionId, sessionData);

    res.json({ ok: true, redirectUrl: `/select?sessionId=${sessionId}` });
  });
});

app.post('/generate', (req, res) => {
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

  runPythonScript(
    GEN_REPORT_SCRIPT,
    [session.analysisPath, selectedLocs.join(','), selectedMonths.join(','), outputPath],
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
        const host = req.headers.host || `localhost:${PORT}`;
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
    const host = req.headers.host || `localhost:${PORT}`;
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

  socket.on('disconnect', () => {
    if (socket.roomCode && presenterRooms[socket.roomCode]) {
      if (socket.role === 'presenter') {
        presenterRooms[socket.roomCode].presenterId = null;
      } else {
        presenterRooms[socket.roomCode].viewers = Math.max(0, presenterRooms[socket.roomCode].viewers - 1);
      }
      io.to(socket.roomCode).emit('room_state', presenterRooms[socket.roomCode]);
      if (!presenterRooms[socket.roomCode].presenterId && presenterRooms[socket.roomCode].viewers === 0) {
        delete presenterRooms[socket.roomCode];
      }
    }
  });
});

if (require.main === module) {
  server.listen(PORT, () => {
    console.log(`Studio performance report app running at http://localhost:${PORT}`);
  });
}

module.exports = { app, server, io };
