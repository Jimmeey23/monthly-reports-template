/* =============================================================================
   agent/tools.js — the agent's hands
   -----------------------------------------------------------------------------
   Two kinds of tool live here and they behave differently on purpose:

     read tools   (run_query, report_outline, inspect_html, list_changes)
                  run immediately and return real data.

     write tools  (propose_style_patch, propose_component, revert_change)
                  never write anything. They validate the request and hand back
                  a *proposal*, which the dock previews live in the page. Only
                  the user's "Keep" click, which comes back as POST /agent/:id/apply,
                  reaches agent/overrides.js. That is the confirmation gate the
                  whole feature hangs on, so it is enforced here rather than in
                  the prompt.
   ========================================================================== */
'use strict';

const fs = require('fs');
const cheerio = require('cheerio');

const sandbox = require('./sandbox');
const context = require('./context');
const overrides = require('./overrides');

const STYLE_OPS = new Set([
  'css',         // { selector, declarations: {prop: value} }
  'hide',        // { selector }
  'show',        // { selector }
  'move',        // { selector, target, position: before|after|prepend|append }
  'reorder',     // { selector, index }
  'setText',     // { selector, text }
  'setHtml',     // { selector, html }
  'addClass',    // { selector, className }
  'removeClass', // { selector, className }
  'setAttr',     // { selector, name, value }
  'remove',      // { selector }
]);

const POSITIONS = new Set(['before', 'after', 'prepend', 'append', 'replace']);

const definitions = [
  {
    type: 'function',
    function: {
      name: 'run_query',
      description:
        'Run Python against this report\'s data and get real numbers back. This is the ONLY '
        + 'acceptable way to produce a figure — never compute or estimate one yourself. '
        + 'In scope: `analysis` (the parsed analysis.json, shape given in the system prompt), '
        + '`csv("sales")` returning that CSV\'s rows as dicts, plus json/math/re/statistics/'
        + 'Counter/defaultdict/datetime. Return a value from a bare expression, call out(x), or '
        + 'assign to `result`. Aggregate before returning — huge row dumps are rejected.',
      parameters: {
        type: 'object',
        properties: {
          code: { type: 'string', description: 'Python expression or statements.' },
          purpose: { type: 'string', description: 'One short line on what this answers, shown to the user.' },
        },
        required: ['code'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'report_outline',
      description:
        'List the report\'s sections with their ids, headings, table/chart counts and child blocks. '
        + 'Call this before any layout, placement or styling change so you target real selectors.',
      parameters: { type: 'object', properties: {} },
    },
  },
  {
    type: 'function',
    function: {
      name: 'inspect_html',
      description:
        'Return the markup of the first few nodes matching a CSS selector. Use it to copy the '
        + 'report\'s existing classes when building a component so it matches the design exactly.',
      parameters: {
        type: 'object',
        properties: {
          selector: { type: 'string' },
          limit: { type: 'integer', description: 'How many matches (default 1, max 3).' },
          maxChars: { type: 'integer', description: 'Cap per match (default 3000).' },
        },
        required: ['selector'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'propose_style_patch',
      description:
        'Propose styling, layout or positioning changes. They are applied to the live page at once '
        + 'so the user can see them, but stay pending until the user keeps them. Prefer several small '
        + 'ops in one patch over many patches.',
      parameters: {
        type: 'object',
        properties: {
          note: { type: 'string', description: 'What this changes, in one line, for the user.' },
          ops: {
            type: 'array',
            description: 'Ordered operations.',
            items: {
              type: 'object',
              properties: {
                kind: { type: 'string', enum: [...STYLE_OPS] },
                selector: { type: 'string' },
                declarations: { type: 'object', description: 'For kind=css: CSS property -> value.' },
                target: { type: 'string', description: 'For kind=move: selector to move next to.' },
                position: { type: 'string', enum: [...POSITIONS] },
                index: { type: 'integer' },
                text: { type: 'string' },
                html: { type: 'string' },
                className: { type: 'string' },
                name: { type: 'string' },
                value: { type: 'string' },
              },
              required: ['kind', 'selector'],
            },
          },
        },
        required: ['ops', 'note'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'propose_component',
      description:
        'Propose a new table, chart, list or card built from real queried numbers. It renders in '
        + 'place immediately for review and is saved only once the user confirms. Write the HTML '
        + 'with the report\'s own classes (check with inspect_html). Put every number in the HTML '
        + 'literally — values must come from run_query results, never from memory.',
      parameters: {
        type: 'object',
        properties: {
          title: { type: 'string' },
          componentType: { type: 'string', enum: ['table', 'chart', 'list', 'card', 'block'] },
          target: { type: 'string', description: 'CSS selector of the anchor element, e.g. "#revenue-performance .container".' },
          position: { type: 'string', enum: [...POSITIONS], description: 'Default "append".' },
          html: { type: 'string', description: 'The component markup.' },
          css: { type: 'string', description: 'Optional scoped CSS.' },
          js: { type: 'string', description: 'Optional init JS. Runs with `root` bound to the inserted element.' },
          query: { type: 'string', description: 'The run_query code whose numbers this renders, so it can be rebuilt next month.' },
          note: { type: 'string', description: 'One line on what it shows.' },
        },
        required: ['title', 'componentType', 'target', 'html'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'list_changes',
      description: 'List the saved patches and components on this report, with their ids.',
      parameters: { type: 'object', properties: {} },
    },
  },
  {
    type: 'function',
    function: {
      name: 'revert_change',
      description: 'Propose removing a previously saved patch or component by id (from list_changes).',
      parameters: {
        type: 'object',
        properties: { id: { type: 'string' } },
        required: ['id'],
      },
    },
  },
];

/* ------------------------------------------------------------ validation -- */

function badRequest(message) {
  return { ok: false, error: message };
}

function validateOps(ops) {
  if (!Array.isArray(ops) || !ops.length) return 'ops must be a non-empty array';
  for (const op of ops) {
    if (!op || !STYLE_OPS.has(op.kind)) return `unknown op kind: ${op && op.kind}`;
    if (typeof op.selector !== 'string' || !op.selector.trim()) return `op ${op.kind} needs a selector`;
    if (op.kind === 'css' && (!op.declarations || typeof op.declarations !== 'object')) {
      return 'css op needs a declarations object';
    }
    if (op.kind === 'move') {
      if (!op.target) return 'move op needs a target selector';
      if (op.position && !POSITIONS.has(op.position)) return `bad position: ${op.position}`;
    }
  }
  return null;
}

/* ---------------------------------------------------------------- runner -- */

/**
 * @param {string} name        tool name the model asked for
 * @param {object} args        parsed arguments
 * @param {object} ctx         { analysisPath, csvDir, reportPath, sessionDir, filename, canEdit }
 * @returns {Promise<object>}  tool result; `proposal` on it is streamed to the dock
 */
async function runTool(name, args, ctx) {
  switch (name) {
    case 'run_query': {
      if (typeof args.code !== 'string' || !args.code.trim()) return badRequest('code is required');
      const res = await sandbox.runQuery({
        code: args.code,
        analysisPath: ctx.analysisPath,
        csvDir: ctx.csvDir,
      });
      return Object.assign({ purpose: args.purpose || '' }, res);
    }

    case 'report_outline':
      return { ok: true, sections: context.reportOutline(ctx.reportPath) || [] };

    case 'inspect_html': {
      if (!args.selector) return badRequest('selector is required');
      const limit = Math.min(Math.max(Number(args.limit) || 1, 1), 3);
      const maxChars = Math.min(Math.max(Number(args.maxChars) || 3000, 200), 8000);
      let $;
      try {
        $ = cheerio.load(fs.readFileSync(ctx.reportPath, 'utf8'));
      } catch (e) {
        return badRequest(`could not read the report: ${e.message}`);
      }
      let matches;
      try {
        matches = $(args.selector);
      } catch (e) {
        return badRequest(`invalid selector: ${e.message}`);
      }
      const html = matches.slice(0, limit).map((_, el) => $.html(el).slice(0, maxChars)).get();
      return { ok: true, count: matches.length, html };
    }

    case 'propose_style_patch': {
      if (!ctx.canEdit) return badRequest('this viewer is read-only; editing is disabled');
      const problem = validateOps(args.ops);
      if (problem) return badRequest(problem);
      return {
        ok: true,
        pending: true,
        message: 'Applied to the page for review. It is not saved until the user keeps it.',
        proposal: { kind: 'style', note: args.note || 'Style change', ops: args.ops },
      };
    }

    case 'propose_component': {
      if (!ctx.canEdit) return badRequest('this viewer is read-only; editing is disabled');
      if (!args.html || !args.target || !args.title) return badRequest('title, target and html are required');
      const position = POSITIONS.has(args.position) ? args.position : 'append';
      return {
        ok: true,
        pending: true,
        message: 'Rendered in place for review. It is not saved until the user confirms the section.',
        proposal: {
          kind: 'component',
          note: args.note || args.title,
          component: {
            title: args.title,
            componentType: args.componentType || 'block',
            target: args.target,
            position,
            html: args.html,
            css: args.css || '',
            js: args.js || '',
            query: args.query || '',
          },
        },
      };
    }

    case 'list_changes': {
      const entry = overrides.load(ctx.sessionDir, ctx.filename);
      return {
        ok: true,
        patches: entry.patches.map(p => ({ id: p.id, note: p.note, ops: p.ops.length })),
        components: entry.components.map(c => ({ id: c.id, title: c.title, target: c.target })),
      };
    }

    case 'revert_change': {
      if (!ctx.canEdit) return badRequest('this viewer is read-only; editing is disabled');
      if (!args.id) return badRequest('id is required');
      const entry = overrides.load(ctx.sessionDir, ctx.filename);
      const known = entry.patches.some(p => p.id === args.id) || entry.components.some(c => c.id === args.id);
      if (!known) return badRequest(`no saved change with id ${args.id}`);
      return {
        ok: true,
        pending: true,
        message: 'Reverted in the page for review; confirm to drop it permanently.',
        proposal: { kind: 'revert', note: `Remove ${args.id}`, id: args.id },
      };
    }

    default:
      return badRequest(`unknown tool: ${name}`);
  }
}

module.exports = { definitions, runTool, validateOps, STYLE_OPS, POSITIONS };
