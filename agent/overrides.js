/* =============================================================================
   agent/overrides.js — everything the agent changed, kept outside the report
   -----------------------------------------------------------------------------
   A generated report is a 2 MB self-contained file. Rewriting it on every
   styling tweak would be slow and unrecoverable, so agent edits live beside it
   in `<session>/report-overrides.json`, keyed by report filename:

     { "<file>.html": { patches: [...], components: [...] } }

   The dock replays that file on load, which makes every change reversible by
   id and keeps the HTML itself pristine until the user hits Save — at which
   point the client posts the live DOM to /save-report and the edits bake in.

   A component the user marks reusable is also copied to
   `report_assets/components/<slug>.json`, the library future reports read.
   ========================================================================== */
'use strict';

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const LIBRARY_DIR = path.join(__dirname, '..', 'report_assets', 'components');

function fileFor(sessionDir) {
  return path.join(sessionDir, 'report-overrides.json');
}

function readAll(sessionDir) {
  try {
    return JSON.parse(fs.readFileSync(fileFor(sessionDir), 'utf8'));
  } catch (e) {
    return {};
  }
}

function writeAll(sessionDir, data) {
  const target = fileFor(sessionDir);
  const tmp = `${target}.tmp`;
  fs.writeFileSync(tmp, JSON.stringify(data, null, 2));
  fs.renameSync(tmp, target);   // never leave a half-written overrides file behind
}

/** The patch/component set for one report file. */
function load(sessionDir, filename) {
  const all = readAll(sessionDir);
  const entry = all[filename] || {};
  return {
    version: 1,
    patches: Array.isArray(entry.patches) ? entry.patches : [],
    components: Array.isArray(entry.components) ? entry.components : [],
  };
}

function save(sessionDir, filename, entry) {
  const all = readAll(sessionDir);
  all[filename] = { version: 1, patches: entry.patches, components: entry.components };
  writeAll(sessionDir, all);
  return all[filename];
}

const newId = prefix => `${prefix}_${crypto.randomBytes(5).toString('hex')}`;

function addPatch(sessionDir, filename, patch) {
  const entry = load(sessionDir, filename);
  const record = Object.assign({ id: newId('sty'), ts: Date.now() }, patch);
  entry.patches.push(record);
  save(sessionDir, filename, entry);
  return record;
}

function addComponent(sessionDir, filename, component) {
  const entry = load(sessionDir, filename);
  const record = Object.assign({ id: newId('cmp'), ts: Date.now() }, component);
  entry.components.push(record);
  save(sessionDir, filename, entry);
  return record;
}

/** Remove one patch or component by id. Returns what was dropped, or null. */
function remove(sessionDir, filename, id) {
  const entry = load(sessionDir, filename);
  const hit = entry.patches.find(p => p.id === id) || entry.components.find(c => c.id === id);
  if (!hit) return null;
  entry.patches = entry.patches.filter(p => p.id !== id);
  entry.components = entry.components.filter(c => c.id !== id);
  save(sessionDir, filename, entry);
  return hit;
}

function clear(sessionDir, filename) {
  save(sessionDir, filename, { patches: [], components: [] });
}

/* ---------------------------------------------------------------- library -- */

function slugify(text) {
  return String(text || 'component').toLowerCase().replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '').slice(0, 60) || 'component';
}

/** Promote a component to the reusable library future reports pull from. */
function saveToLibrary(component) {
  fs.mkdirSync(LIBRARY_DIR, { recursive: true });
  const slug = slugify(component.title);
  const record = Object.assign({}, component, {
    slug,
    savedAt: Date.now(),
    autoApply: component.autoApply !== false,
  });
  fs.writeFileSync(path.join(LIBRARY_DIR, `${slug}.json`), JSON.stringify(record, null, 2));
  return record;
}

function listLibrary() {
  let files;
  try { files = fs.readdirSync(LIBRARY_DIR).filter(f => f.endsWith('.json')); } catch (e) { return []; }
  return files.map((f) => {
    try { return JSON.parse(fs.readFileSync(path.join(LIBRARY_DIR, f), 'utf8')); } catch (e) { return null; }
  }).filter(Boolean);
}

function removeFromLibrary(slug) {
  const target = path.join(LIBRARY_DIR, `${slugify(slug)}.json`);
  if (!target.startsWith(LIBRARY_DIR)) return false;
  try { fs.unlinkSync(target); return true; } catch (e) { return false; }
}

module.exports = {
  load, save, addPatch, addComponent, remove, clear,
  saveToLibrary, listLibrary, removeFromLibrary, slugify, LIBRARY_DIR,
};
