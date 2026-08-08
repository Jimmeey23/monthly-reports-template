const express = require('express');
const multer = require('multer');
const { execFile } = require('child_process');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const os = require('os');

// Basic .env file loader if process.env.OPENAI_API_KEY is not already set
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

// Use OS tmpdir on serverless hosts like Vercel so filesystem writes never fail
const UPLOADS_DIR = path.join(os.tmpdir(), 'report_uploads');
const ANALYZE_SCRIPT = path.join(__dirname, 'analyze_v2.py');
const GEN_REPORT_SCRIPT = path.join(__dirname, 'gen_report_v2.py');

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

fs.mkdirSync(UPLOADS_DIR, { recursive: true });

// sessionId -> { dir, analysisPath, locations, months }
const sessions = new Map();

function getSession(sessionId) {
  if (!sessionId) return null;
  if (sessions.has(sessionId)) return sessions.get(sessionId);

  // Fallback: reload from disk in /tmp if running in stateless serverless instance
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

function runPythonScript(scriptType, payload, reqHost, callback) {
  if (!process.env.VERCEL) {
    const scriptPath = scriptType === 'analyze' ? ANALYZE_SCRIPT : GEN_REPORT_SCRIPT;
    const args =
      scriptType === 'analyze'
        ? [payload.sessionDir, payload.analysisPath]
        : [payload.analysisPath, payload.locKeys.join(','), payload.monthKeys.join(','), payload.outputPath];

    execFile(PYTHON, [scriptPath, ...args], { maxBuffer: 1024 * 1024 * 50 }, (err, stdout, stderr) => {
      if (!err) return callback(null, stdout, stderr);
      callVercelPythonApi(scriptType, payload, reqHost, callback);
    });
  } else {
    callVercelPythonApi(scriptType, payload, reqHost, callback);
  }
}

function callVercelPythonApi(scriptType, payload, reqHost, callback) {
  const host = reqHost || process.env.VERCEL_URL || 'localhost:3000';
  const protocol = host.includes('localhost') ? 'http' : 'https';
  const url = `${protocol}://${host}/api/${scriptType}`;

  fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
    .then(async (res) => {
      const data = await res.json().catch(() => ({}));
      if (!res.ok || data.error) {
        return callback(new Error(data.error || `Python serverless function error ${res.status}`));
      }
      callback(null, '', '');
    })
    .catch((err) => callback(err));
}

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    const dir = path.join(UPLOADS_DIR, req.sessionId);
    fs.mkdirSync(dir, { recursive: true });
    cb(null, dir);
  },
  filename: (req, file, cb) => {
    const slot = CSV_SLOTS.find((s) => s.field === file.fieldname);
    cb(null, slot ? slot.filename : file.originalname);
  },
});
const upload = multer({ storage, limits: { fileSize: 200 * 1024 * 1024 } });

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
app.use(express.json({ limit: '20mb' }));

app.get('/', (req, res) => {
  res.render('upload', { slots: CSV_SLOTS, error: null });
});

app.post(
  '/upload',
  assignSessionId,
  upload.fields(CSV_SLOTS.map((s) => ({ name: s.field, maxCount: 1 }))),
  (req, res) => {
    const missing = CSV_SLOTS.filter((s) => !req.files || !req.files[s.field]);
    if (missing.length) {
      return res.render('upload', {
        slots: CSV_SLOTS,
        error: `Missing file(s): ${missing.map((s) => s.label).join(', ')}`,
      });
    }

    const sessionDir = path.join(UPLOADS_DIR, req.sessionId);
    const analysisPath = path.join(sessionDir, 'analysis.json');

    runPythonScript('analyze', { sessionDir, analysisPath }, req.headers.host, (err, stdout, stderr) => {
      if (err) {
        console.error(stderr || err.message);
        return res.render('upload', {
          slots: CSV_SLOTS,
          error: `Analysis failed: ${stderr || err.message}`,
        });
      }

      let analysis;
      try {
        analysis = JSON.parse(fs.readFileSync(analysisPath, 'utf8'));
      } catch (e) {
        return res.render('upload', {
          slots: CSV_SLOTS,
          error: `Could not read analysis output: ${e.message}`,
        });
      }

      const locations = analysis.meta.locations; // { loc_key: full_name }
      const months = analysis.meta.months; // ["2026-01", ...]

      if (!Object.keys(locations).length || !months.length) {
        return res.render('upload', {
          slots: CSV_SLOTS,
          error: 'No studios or months detected in the uploaded CSVs.',
        });
      }

      const sessionData = { dir: sessionDir, analysisPath, locations, months };
      saveSession(req.sessionId, sessionData);

      res.render('select', {
        sessionId: req.sessionId,
        locations,
        months: [...months].reverse(),
        error: null,
      });
    });
  }
);

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

  const payload = {
    analysisPath: session.analysisPath,
    locKeys: selectedLocs,
    monthKeys: selectedMonths,
    outputPath,
  };

  runPythonScript('generate', payload, req.headers.host, (err, stdout, stderr) => {
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
      })};</script>\n<script src="/report-client.js"></script>`;
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
  });
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

if (require.main === module) {
  app.listen(PORT, () => {
    console.log(`Studio performance report app running at http://localhost:${PORT}`);
  });
}

module.exports = app;
