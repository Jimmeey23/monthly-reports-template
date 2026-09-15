/* =============================================================================
   agent/context.js — what the agent knows before it asks anything
   -----------------------------------------------------------------------------
   Two descriptions, both derived from the session rather than hand-maintained,
   so they can never drift from the data or the report:

     dataSchema()    a compact shape card for analysis.json — every path, its
                     type, its key sample — enough for the model to write a
                     correct query on the first try instead of probing.
     reportOutline() the rendered report's sections, headings, tables and
                     component anchors, read out of the saved HTML with cheerio.

   Both are cached on file mtime: the schema walk and the 2 MB parse are too
   expensive to repeat on every chat turn.
   ========================================================================== */
'use strict';

const fs = require('fs');
const path = require('path');
const cheerio = require('cheerio');

const MAX_KEYS_SHOWN = 6;
const MAX_DEPTH = 3;
/* The card is a map, not a dump: past this the model is better off probing the
   data with a query than reading more of the shape. */
const MAX_SCHEMA_CHARS = 9000;

const cache = new Map();   // key -> { mtimeMs, value }

function cached(key, file, build) {
  let stat;
  try { stat = fs.statSync(file); } catch (e) { return null; }
  const hit = cache.get(key);
  if (hit && hit.mtimeMs === stat.mtimeMs) return hit.value;
  const value = build();
  cache.set(key, { mtimeMs: stat.mtimeMs, value });
  return value;
}

function typeName(v) {
  if (v === null) return 'null';
  if (Array.isArray(v)) return 'array';
  return typeof v;
}

/* A dict whose keys are data (studio keys, month keys, member ids) is described
   by its sample keys; a dict whose keys are field names is described by walking
   into it. The two are told apart by how uniform the values are. */
function describe(node, depth = 0) {
  const t = typeName(node);
  if (t !== 'object' && t !== 'array') return t;

  if (t === 'array') {
    if (!node.length) return 'array[]';
    return `array[${node.length}] of ${depth >= MAX_DEPTH ? typeName(node[0]) : describe(node[0], depth + 1)}`;
  }

  const keys = Object.keys(node);
  if (!keys.length) return 'object{}';
  if (depth >= MAX_DEPTH) return `object{${keys.length} keys: ${keys.slice(0, MAX_KEYS_SHOWN).join(', ')}}`;

  const shown = keys.slice(0, MAX_KEYS_SHOWN);
  const described = shown.map(k => describe(node[k], depth + 1));

  /* Studio and month dictionaries hold the same shape under every key. Printing
     that shape nine times buries the schema, so collapse it to one sample. */
  const uniform = described.length > 1
    && described.every(d => JSON.stringify(d) === JSON.stringify(described[0]));
  if (uniform) {
    return {
      [`<keys: ${keys.slice(0, 12).join(', ')}${keys.length > 12 ? `, … ${keys.length - 12} more` : ''}>`]:
        described[0],
    };
  }

  const out = {};
  shown.forEach((k, i) => { out[k] = described[i]; });
  if (keys.length > shown.length) out[`… ${keys.length - shown.length} more keys`] = 'same shape';
  return out;
}

function renderSchema(value, indent = '') {
  if (typeof value === 'string') return value;
  return Object.entries(value)
    .map(([k, v]) => (typeof v === 'string'
      ? `${indent}${k}: ${v}`
      : `${indent}${k}:\n${renderSchema(v, indent + '  ')}`))
    .join('\n');
}

/** Shape card for one session's analysis.json. */
function dataSchema(analysisPath) {
  return cached(`schema:${analysisPath}`, analysisPath, () => {
    const analysis = JSON.parse(fs.readFileSync(analysisPath, 'utf8'));
    const text = renderSchema(describe(analysis));
    return text.length > MAX_SCHEMA_CHARS
      ? text.slice(0, MAX_SCHEMA_CHARS)
        + '\n… schema truncated — run a query such as `list(analysis["<key>"].keys())` to explore the rest.'
      : text;
  });
}

/** Names of the CSVs the sandbox can read, with their header rows. */
function csvSchema(csvDir) {
  let files;
  try { files = fs.readdirSync(csvDir).filter(f => f.endsWith('.csv')); } catch (e) { return 'none'; }
  return files.map((f) => {
    let header = '';
    try {
      const fd = fs.openSync(path.join(csvDir, f), 'r');
      const buf = Buffer.alloc(4096);
      const read = fs.readSync(fd, buf, 0, 4096, 0);
      fs.closeSync(fd);
      header = buf.toString('utf8', 0, read).split('\n')[0].trim().slice(0, 600);
    } catch (e) { /* an unreadable CSV is simply not described */ }
    return `  ${f} — columns: ${header}`;
  }).join('\n');
}

/**
 * The report's structure: every section, its heading, and the blocks inside it
 * the agent can target, hide, move or append to.
 */
function reportOutline(reportPath) {
  return cached(`outline:${reportPath}`, reportPath, () => {
    const $ = cheerio.load(fs.readFileSync(reportPath, 'utf8'));
    const sections = [];
    $('section[id], section.section, .report-section[id]').each((_, el) => {
      const $el = $(el);
      const id = $el.attr('id') || '';
      if (!id) return;
      const heading = $el.find('h1,h2,h3').first().text().trim().replace(/\s+/g, ' ').slice(0, 120);
      const blocks = [];
      $el.find('> .container > *, > *').each((__, child) => {
        const $c = $(child);
        const tag = $c.get(0).tagName;
        const cls = ($c.attr('class') || '').split(/\s+/).filter(Boolean).slice(0, 3).join('.');
        const cid = $c.attr('id');
        if (!cls && !cid) return;
        blocks.push(`${tag}${cid ? '#' + cid : ''}${cls ? '.' + cls : ''}`);
      });
      sections.push({
        id,
        heading,
        tables: $el.find('table').length,
        charts: $el.find('[data-chart-type], canvas, svg.chart').length,
        blocks: [...new Set(blocks)].slice(0, 14),
      });
    });
    return sections;
  });
}

function renderOutline(sections) {
  if (!sections || !sections.length) return '(report not parsed yet)';
  return sections.map(s => (
    `  #${s.id} — "${s.heading}" · ${s.tables} tables, ${s.charts} charts\n`
    + `    child blocks: ${s.blocks.join(', ') || '(none)'}`
  )).join('\n');
}

module.exports = { dataSchema, csvSchema, reportOutline, renderOutline };
