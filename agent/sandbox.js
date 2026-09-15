/* =============================================================================
   agent/sandbox.js — run one agent-written Python query
   -----------------------------------------------------------------------------
   The chat agent does no arithmetic itself. When it needs a number it writes a
   snippet, this module runs it in a throwaway `python3 -I` process with the
   session's analysis.json and CSVs in scope, and the printed JSON comes back as
   the tool result. Limits are layered: rlimits inside runner.py, a wall-clock
   kill here, and a cap on how much stdout is read.

   The jail is a process boundary, not a container: a snippet cannot fork or
   write large files, but it could in principle open a socket. Only the agent
   writes these snippets and only the report editor can reach the endpoint, so
   the exposure is the same as the app's own outbound LLM calls.
   ========================================================================== */
'use strict';

const { execFile } = require('child_process');
const crypto = require('crypto');
const fs = require('fs');
const os = require('os');
const path = require('path');

const PYTHON = process.env.PYTHON || 'python3';
const RUNNER = path.join(__dirname, 'runner.py');
const TIMEOUT_MS = Number(process.env.AGENT_SANDBOX_TIMEOUT_MS) || 45000;
const MAX_BUFFER = 4 * 1024 * 1024;

/**
 * @param {object} opts
 * @param {string} opts.code      Python written by the model.
 * @param {string} opts.analysisPath  session analysis.json
 * @param {string} opts.csvDir    directory holding the session's CSVs
 * @returns {Promise<{ok:boolean, result?:*, stdout?:string, error?:string, ms:number}>}
 */
function runQuery({ code, analysisPath, csvDir } = {}) {
  const started = Date.now();
  const jobPath = path.join(os.tmpdir(), `agent-job-${crypto.randomUUID()}.json`);
  fs.writeFileSync(jobPath, JSON.stringify({ code, analysis: analysisPath, csv_dir: csvDir }));

  return new Promise((resolve) => {
    execFile(
      PYTHON,
      ['-I', RUNNER, jobPath],
      { timeout: TIMEOUT_MS, maxBuffer: MAX_BUFFER, killSignal: 'SIGKILL', cwd: os.tmpdir() },
      (err, stdout, stderr) => {
        fs.unlink(jobPath, () => {});
        const ms = Date.now() - started;

        if (err && err.killed) {
          return resolve({ ok: false, error: `query timed out after ${TIMEOUT_MS}ms — narrow it`, ms });
        }
        const text = String(stdout || '').trim();
        if (!text) {
          return resolve({
            ok: false,
            error: (stderr || (err && err.message) || 'the query produced no output').toString().slice(0, 2000),
            ms,
          });
        }
        try {
          // runner.py prints exactly one JSON object, on the last line.
          const line = text.split('\n').filter(Boolean).pop();
          resolve(Object.assign(JSON.parse(line), { ms }));
        } catch (parseErr) {
          resolve({ ok: false, error: `unreadable sandbox output: ${text.slice(0, 1000)}`, ms });
        }
      },
    );
  });
}

module.exports = { runQuery, TIMEOUT_MS };
