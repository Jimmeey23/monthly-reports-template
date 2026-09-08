/* =============================================================================
   copilot_engine.js — offline answer engine for the in-report AI Copilot
   -----------------------------------------------------------------------------
   The copilot used to hand OpenAI a one-location, one-month sample and no API
   key was configured, so almost every request came back empty ("no data").

   This module answers directly from analysis.json — no key, no network:

     • "top 5 products by revenue"      → ranked table from sales_breakdowns
     • "category mix for August"        → ranked table by net revenue
     • "net sales trend last 12 months" → month-by-month table
     • "compare locations"              → location × metric table
     • "what is the churn rate"         → KPI-style single value + context
     • anything else                    → a full snapshot of the month

   Every response also carries `available` so the UI can tell the user what the
   copilot can actually answer instead of a bare "no data".
   ========================================================================== */
'use strict';

/* ------------------------------------------------------------------ helpers */
const INR = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 });

function num(v) {
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}
function fmtInt(v) {
  const n = num(v);
  return n === null ? '—' : INR.format(Math.round(n));
}
function fmtMoney(v) {
  const n = num(v);
  if (n === null) return '—';
  const abs = Math.abs(n);
  if (abs >= 10000000) return '₹' + (n / 10000000).toFixed(2) + 'Cr';
  if (abs >= 100000) return '₹' + (n / 100000).toFixed(2) + 'L';
  return '₹' + INR.format(Math.round(n));
}
function fmtPct(v) {
  const n = num(v);
  return n === null ? '—' : (Math.round(n * 10) / 10).toFixed(1) + '%';
}
function pctChange(cur, prev) {
  const c = num(cur), p = num(prev);
  if (c === null || p === null || p === 0) return '—';
  const d = ((c - p) / Math.abs(p)) * 100;
  return (d > 0 ? '+' : '') + (Math.round(d * 10) / 10).toFixed(1) + '%';
}
function moneyChange(cur, prev) {
  const c = num(cur), p = num(prev);
  if (c === null || p === null) return '—';
  const d = c - p;
  return (d > 0 ? '+' : d < 0 ? '−' : '') + fmtMoney(Math.abs(d));
}
function monthLabel(key) {
  const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const m = /^(\d{4})-(\d{2})$/.exec(String(key || ''));
  if (!m) return String(key || '—');
  const idx = Number(m[2]) - 1;
  return `${MONTHS[idx] || '?'} ${m[1].slice(2)}`;
}
function sortedMonths(obj) {
  return Object.keys(obj || {}).sort();
}
function plural(word) {
  if (/y$/i.test(word)) return word.replace(/y$/i, 'ies');
  if (/(s|x|ch|sh)$/i.test(word)) return word + 'es';
  return word + 's';
}
function changeText(cur, prev, fmt) {
  if (cur === null || cur === undefined || prev === null || prev === undefined) return '—';
  const d = cur - prev;
  if (fmt === 'pct') return (d > 0 ? '+' : '') + (Math.round(d * 10) / 10).toFixed(1) + 'pp';
  if (fmt === 'int') return (d > 0 ? '+' : d < 0 ? '\u2212' : '') + INR.format(Math.abs(Math.round(d)));
  return moneyChange(cur, prev);
}

/* ------------------------------------------------------------ metric catalog */
/* key: internal id — label: shown to the user — fmt: money | int | pct */
const METRICS = [
  { key: 'net', group: 'sales', label: 'Net Sales', fmt: 'money', words: ['net sales', 'net revenue', 'revenue', 'net'] },
  { key: 'gross', group: 'sales', label: 'Gross Sales', fmt: 'money', words: ['gross sales', 'gross revenue', 'gross', 'billed'] },
  { key: 'disc', group: 'sales', label: 'Discount Value', fmt: 'money', words: ['discount', 'discounts', 'disc value'] },
  { key: 'disc_eff', group: 'sales', label: 'Discount Efficiency', fmt: 'money', words: ['discount efficiency', 'disc efficiency'] },
  { key: 'sales', group: 'sales', label: 'Transactions', fmt: 'int', words: ['transactions', 'txns', 'orders', 'sales count'] },
  { key: 'members', group: 'sales', label: 'Unique Buyers', fmt: 'int', words: ['unique buyers', 'buyers', 'members buying', 'customers'] },
  { key: 'atv', group: 'sales', label: 'Avg Transaction Value', fmt: 'money', words: ['atv', 'aov', 'average transaction', 'average order', 'ticket size'] },

  { key: 'sessions', group: 'sessions', label: 'Sessions', fmt: 'int', words: ['sessions', 'classes held'] },
  { key: 'visits', group: 'sessions', label: 'Visits', fmt: 'int', words: ['visits', 'attendance', 'check-ins count'] },
  { key: 'fill', group: 'sessions', label: 'Fill Rate', fmt: 'pct', words: ['fill rate', 'fill', 'utilisation', 'utilization', 'capacity used'] },
  { key: 'revenue', group: 'sessions', label: 'Session Revenue', fmt: 'money', words: ['session revenue', 'class revenue'] },

  { key: 'total', group: 'leads', label: 'Leads', fmt: 'int', words: ['leads', 'enquiries', 'inquiries', 'pipeline'] },
  { key: 'rate', group: 'leads', label: 'Lead Conversion', fmt: 'pct', words: ['lead conversion', 'lead conv'] },

  { key: 'trials', group: 'new', label: 'Trials', fmt: 'int', words: ['trials', 'first visits'] },
  { key: 'converted', group: 'new', label: 'Conversions', fmt: 'int', words: ['conversions', 'converted', 'new members'] },
  { key: 'retained', group: 'new', label: 'Retained', fmt: 'int', words: ['retained', 'retention count'] },
  { key: 'rate', group: 'new', label: 'Trial Conversion', fmt: 'pct', words: ['trial conversion', 'conversion rate', 'conv rate', 'conversion'] },

  { key: 'lapsed', group: 'lapsed', label: 'Lapsed Members', fmt: 'int', words: ['lapsed', 'churned members', 'lost members'] },
  { key: 'renewed', group: 'lapsed', label: 'Renewed', fmt: 'int', words: ['renewed', 'renewals'] },
  { key: 'churn', group: 'lapsed', label: 'Churn Rate', fmt: 'pct', words: ['churn', 'churn rate', 'attrition'] },
  { key: 'renewal_rate', group: 'lapsed', label: 'Renewal Rate', fmt: 'pct', words: ['renewal rate', 'renewal'] },

  { key: 'total', group: 'checkins', label: 'Check-ins', fmt: 'int', words: ['check-ins', 'checkins', 'check ins'] },
  { key: 'late_cancel', group: 'checkins', label: 'Late Cancellations', fmt: 'int', words: ['late cancellations', 'late cancels', 'cancellations', 'no-shows'] },
];

/* group -> { dimension name: key inside analysis } */
const BREAKDOWNS = [
  { key: 'category', group: 'sales_breakdowns', label: 'Category', words: ['categor', 'category', 'categories', 'product line'] },
  { key: 'product', group: 'sales_breakdowns', label: 'Product', words: ['product', 'products', 'item', 'items', 'sku', 'package', 'membership product'] },
  { key: 'seller', group: 'sales_breakdowns', label: 'Seller', words: ['seller', 'sellers', 'salesperson', 'staff', 'team member', 'associate'] },
  { key: 'payment', group: 'sales_breakdowns', label: 'Payment Method', words: ['payment', 'payment method', 'payments', 'tender', 'channel'] },
  { key: null, group: 'sessions_by_class', label: 'Class', words: ['class', 'classes', 'class format', 'format'] },
  { key: null, group: 'sessions_by_trainer', label: 'Trainer', words: ['trainer', 'trainers', 'instructor', 'instructors', 'teacher', 'coach'] },
  { key: null, group: 'leads_by_source', label: 'Lead Source', words: ['lead source', 'source', 'sources', 'channel of leads'] },
  { key: null, group: 'new_by_type', label: 'Trial Type', words: ['trial type', 'trial types', 'new client type'] },
  { key: null, group: 'lapsed_by_product', label: 'Lapsed Product', words: ['lapsed product', 'lapsed by product', 'churned product'] },
];

/* ---------------------------------------------------------------- reader */
class Analysis {
  constructor(data) {
    this.d = data || {};
    this.locations = (this.d.meta && this.d.meta.locations) || {};
    this.months = (this.d.meta && this.d.meta.months) || [];
  }
  locName(key) { return this.locations[key] || key; }
  monthsFor(loc) {
    const fromMeta = this.months.slice();
    const fromData = sortedMonths((this.d.sales || {})[loc]);
    const set = new Set(fromMeta.concat(fromData));
    return [...set].sort();
  }
  metric(loc, month, group, key) {
    const g = (this.d[group] || {})[loc];
    if (!g) return null;
    const node = g[month];
    if (!node || typeof node !== 'object') return null;
    const v = node[key];
    return v === undefined ? null : v;
  }
  breakdown(loc, month, group, subKey) {
    const g = (this.d[group] || {})[loc];
    if (!g) return null;
    const node = subKey ? (g[month] || {})[subKey] : g[month];
    if (!node || typeof node !== 'object') return null;
    return node;
  }
}

/* ---------------------------------------------------------------- intents */
function findMetric(prompt) {
  const p = ' ' + String(prompt || '').toLowerCase() + ' ';
  let best = null;
  for (const m of METRICS) {
    for (const w of m.words) {
      if (p.includes(w)) {
        const score = w.length;
        if (!best || score > best.score) best = { metric: m, score };
      }
    }
  }
  return best ? best.metric : null;
}
function findBreakdown(prompt) {
  const p = ' ' + String(prompt || '').toLowerCase() + ' ';
  let best = null;
  for (const b of BREAKDOWNS) {
    for (const w of b.words) {
      if (p.includes(w)) {
        const score = w.length;
        if (!best || score > best.score) best = { dim: b, score };
      }
    }
  }
  return best ? best.dim : null;
}
function countRequested(prompt, fallback) {
  const p = String(prompt || '').toLowerCase();
  const m = /\btop\s+(\d{1,2})\b/.exec(p) || /\bbottom\s+(\d{1,2})\b/.exec(p) || /(\d{1,2})\s+(?:rows|items|entries)/.exec(p);
  if (m) return Math.min(30, Math.max(1, Number(m[1])));
  return fallback;
}
function monthsRequested(prompt, fallback) {
  const p = String(prompt || '').toLowerCase();
  const m = /(?:last|past|previous)\s+(\d{1,2})\s+months?/.exec(p);
  if (m) return Math.min(60, Math.max(2, Number(m[1])));
  return fallback;
}

/* ---------------------------------------------------------------- answers */
function table(title, rows, description, extra) {
  return Object.assign({
    type: 'table',
    title,
    data: rows,
    description: description || '',
  }, extra || {});
}

function breakdownAnswer(an, prompt, ctx, dim, limit) {
  const loc = ctx.loc;
  const month = ctx.month;
  const raw = an.breakdown(loc, month, dim.group, dim.key);
  if (!raw) {
    return null;
  }
  const entries = Object.entries(raw)
    .map(([name, v]) => ({
      name,
      net: num(v && v.net) || 0,
      gross: num(v && v.gross) || 0,
      disc: num(v && v.disc) || 0,
      rows: num(v && v.rows) || num(v && v.count) || null,
      visits: num(v && v.visits) || null,
      fill: num(v && v.fill) || null,
    }))
    .filter((r) => r.net !== 0 || r.gross !== 0 || r.rows !== null || r.visits !== null);

  if (!entries.length) return null;

  const byValue = (r) => (r.net || r.gross || r.visits || r.rows || 0);
  entries.sort((a, b) => byValue(b) - byValue(a));
  const isBottom = /\bbottom\b/i.test(prompt || '');
  if (isBottom) entries.reverse();
  const top = entries.slice(0, limit);
  const total = entries.reduce((s, r) => s + (r.net || 0), 0);

  const hasMoney = top.some((r) => r.net || r.gross);
  const rows = top.map((r, i) => {
    const row = { '#': i + 1, [dim.label]: r.name };
    if (hasMoney) {
      row['Net'] = fmtMoney(r.net);
      row['Share'] = total ? fmtPct((r.net / total) * 100) : '—';
    }
    if (r.rows !== null) row['Txns'] = fmtInt(r.rows);
    if (r.visits !== null) row['Visits'] = fmtInt(r.visits);
    if (r.fill !== null) row['Fill Rate'] = fmtPct(r.fill);
    return row;
  });

  const scope = `${an.locName(loc)} · ${monthLabel(month)}`;
  const noun = plural(dim.label).toLowerCase();
  const desc = `${isBottom ? 'Lowest' : 'Top'} ${top.length} ${noun} by net revenue for ${scope}` +
    (hasMoney ? ` — ${fmtMoney(total)} in total net revenue across ${entries.length} ${noun}.` : '.');
  return table(`${dim.label} breakdown — ${scope}`, rows, desc, { confidence: 'high' });
}

function trendAnswer(an, prompt, ctx, metric, nMonths) {
  const loc = ctx.loc;
  const all = an.monthsFor(loc);
  const idx = all.indexOf(ctx.month);
  const end = idx >= 0 ? idx + 1 : all.length;
  const window = all.slice(Math.max(0, end - nMonths), end);
  if (!window.length) return null;

  const fmt = metric.fmt === 'money' ? fmtMoney : metric.fmt === 'pct' ? fmtPct : fmtInt;
  const rows = window.map((m) => {
    const v = an.metric(loc, m, metric.group, metric.key);
    const prevM = window[window.indexOf(m) - 1];
    const prev = prevM ? an.metric(loc, prevM, metric.group, metric.key) : null;
    const row = { Month: monthLabel(m), [metric.label]: fmt(v) };
    row['MoM'] = prev === null || prev === undefined || v === null ? '—'
      : (metric.fmt === 'pct'
        ? ((v - prev > 0 ? '+' : '') + (Math.round((v - prev) * 10) / 10).toFixed(1) + 'pp')
        : pctChange(v, prev));
    return row;
  });

  const first = an.metric(loc, window[0], metric.group, metric.key);
  const last = an.metric(loc, window[window.length - 1], metric.group, metric.key);
  const scope = `${an.locName(loc)} · last ${window.length} months to ${monthLabel(window[window.length - 1])}`;
  const desc = `${metric.label} moved from ${fmt(first)} (${monthLabel(window[0])}) to ${fmt(last)} (${monthLabel(window[window.length - 1])}) — ${pctChange(last, first)} across the window.`;
  return table(`${metric.label} trend — ${scope}`, rows, desc, { confidence: 'high' });
}

function compareLocationsAnswer(an, ctx) {
  const keys = Object.keys(an.locations);
  if (keys.length < 2) return null;
  const metrics = [
    METRICS.find((m) => m.key === 'net' && m.group === 'sales'),
    METRICS.find((m) => m.key === 'sales' && m.group === 'sales'),
    METRICS.find((m) => m.key === 'atv' && m.group === 'sales'),
    METRICS.find((m) => m.key === 'visits' && m.group === 'sessions'),
    METRICS.find((m) => m.key === 'total' && m.group === 'leads'),
    METRICS.find((m) => m.key === 'churn' && m.group === 'lapsed'),
  ].filter(Boolean);

  const usable = metrics.filter((m) =>
    keys.some((loc) => an.metric(loc, ctx.month, m.group, m.key) !== null && an.metric(loc, ctx.month, m.group, m.key) !== undefined));

  const rows = keys.map((loc) => {
    const row = { Location: an.locName(loc) };
    usable.forEach((m) => {
      const v = an.metric(loc, ctx.month, m.group, m.key);
      row[m.label] = m.fmt === 'money' ? fmtMoney(v) : m.fmt === 'pct' ? fmtPct(v) : fmtInt(v);
    });
    return row;
  });
  return table(`Location comparison — ${monthLabel(ctx.month)}`, rows,
    `All ${keys.length} locations for ${monthLabel(ctx.month)}.`, { confidence: 'high' });
}

function singleMetricAnswer(an, ctx, metric) {
  const cur = an.metric(ctx.loc, ctx.month, metric.group, metric.key);
  if (cur === null || cur === undefined) return null;
  const all = an.monthsFor(ctx.loc);
  const i = all.indexOf(ctx.month);
  const prev = i > 0 ? an.metric(ctx.loc, all[i - 1], metric.group, metric.key) : null;
  const yoy = i >= 12 ? an.metric(ctx.loc, all[i - 12], metric.group, metric.key) : null;
  const fmt = metric.fmt === 'money' ? fmtMoney : metric.fmt === 'pct' ? fmtPct : fmtInt;

  return {
    type: 'kpi',
    title: `${metric.label} — ${an.locName(ctx.loc)} · ${monthLabel(ctx.month)}`,
    data: {
      label: metric.label,
      value: fmt(cur),
      change: metric.fmt === 'pct'
        ? (prev === null ? '—' : (cur - prev > 0 ? '+' : '') + (Math.round((cur - prev) * 10) / 10).toFixed(1) + 'pp MoM')
        : pctChange(cur, prev) + ' MoM',
    },
    description: `${fmt(cur)} in ${monthLabel(ctx.month)}` +
      (prev !== null && prev !== undefined ? ` vs ${fmt(prev)} in ${monthLabel(all[i - 1])} (${changeText(cur, prev, metric.fmt)})` : '') +
      (yoy !== null && yoy !== undefined ? ` · YoY ${pctChange(cur, yoy)} vs ${monthLabel(all[i - 12])}` : '') + '.',
    confidence: 'high',
  };
}

function overviewAnswer(an, ctx) {
  const all = an.monthsFor(ctx.loc);
  const i = all.indexOf(ctx.month);
  const prev = i > 0 ? all[i - 1] : null;
  const groups = ['sales', 'sessions', 'leads', 'new', 'lapsed', 'checkins'];
  const seen = new Set();
  const rows = [];
  for (const m of METRICS) {
    const id = m.group + ':' + m.key;
    if (seen.has(id)) continue;
    const cur = an.metric(ctx.loc, ctx.month, m.group, m.key);
    if (cur === null || cur === undefined) continue;
    seen.add(id);
    const pv = prev ? an.metric(ctx.loc, prev, m.group, m.key) : null;
    const fmt = m.fmt === 'money' ? fmtMoney : m.fmt === 'pct' ? fmtPct : fmtInt;
    rows.push({
      Metric: m.label,
      [monthLabel(ctx.month)]: fmt(cur),
      MoM: pv === null || pv === undefined ? '—'
        : (m.fmt === 'pct'
          ? (cur - pv > 0 ? '+' : '') + (Math.round((cur - pv) * 10) / 10).toFixed(1) + 'pp'
          : pctChange(cur, pv)),
    });
  }
  const emptyGroups = groups.filter((g) => !(an.d[g] || {})[ctx.loc] || !Object.keys((an.d[g] || {})[ctx.loc]).length);
  const desc = `Snapshot for ${an.locName(ctx.loc)} · ${monthLabel(ctx.month)} — ${rows.length} metrics.` +
    (emptyGroups.length ? ` No data loaded for: ${emptyGroups.join(', ')}.` : '');
  return table(`Report snapshot — ${an.locName(ctx.loc)} · ${monthLabel(ctx.month)}`, rows, desc, { confidence: 'medium' });
}

/* ------------------------------------------------------------------ public */
function answerCopilot(prompt, analysisData, ctx) {
  const an = new Analysis(analysisData);
  const context = {
    loc: ctx && ctx.loc,
    month: ctx && ctx.month,
  };
  if (!context.loc || !an.locations[context.loc]) {
    context.loc = Object.keys(an.locations)[0];
  }
  const months = an.monthsFor(context.loc);
  if (!context.month || !months.includes(context.month)) {
    const withData = months.filter((m) => {
      const node = ((analysisData.sales || {})[context.loc] || {})[m];
      return node && typeof node === 'object' && Object.keys(node).length;
    });
    context.month = (withData.length ? withData : months).slice(-1)[0];
  }

  const p = String(prompt || '').toLowerCase();
  const result = (() => {
    /* 1. "compare locations" / "across studios" */
    if (/\b(compare|versus|vs\.?|across (?:all )?(?:locations|studios)|by location|each location)\b/.test(p)) {
      const r = compareLocationsAnswer(an, context);
      if (r) return r;
    }

    /* 2. breakdown / ranking questions */
    const dim = findBreakdown(p);
    if (dim && /\b(top|bottom|best|worst|breakdown|mix|split|by |rank|highest|lowest|list|which|share)\b/.test(p)) {
      const r = breakdownAnswer(an, prompt, context, dim, countRequested(prompt, 10));
      if (r) return r;
      // Asked for a dimension this upload has no rows for — do not substitute another one.
      const ready = BREAKDOWNS
        .filter((b) => {
          const raw = an.breakdown(context.loc, context.month, b.group, b.key);
          return raw && Object.keys(raw).length;
        })
        .map((b) => plural(b.label).toLowerCase());
      return {
        type: 'text',
        title: `No ${plural(dim.label).toLowerCase()} data for ${monthLabel(context.month)}`,
        data: `This upload has no ${plural(dim.label).toLowerCase()} rows for ${an.locName(context.loc)} · ${monthLabel(context.month)}.` +
          (ready.length ? ` Breakdowns with data here: ${ready.join(', ')}.` : ' No breakdown tables were produced for this month.'),
        description: 'Answered from analysis.json — nothing was estimated.',
        confidence: 'low',
      };
    }

    /* 3. trend questions */
    const metric = findMetric(p);
    if (/\b(trend|over time|month on month|month-on-month|\bmom\b|monthly|history|last \d+ months|past \d+ months|growth|chart|series)\b/.test(p) && metric) {
      const r = trendAnswer(an, prompt, context, metric, monthsRequested(prompt, 12));
      if (r) return r;
    }

    /* 4. single metric questions */
    if (metric) {
      if (/\b(trend|month|months|last|history)\b/.test(p)) {
        const r = trendAnswer(an, prompt, context, metric, monthsRequested(prompt, 12));
        if (r) return r;
      }
      const r = singleMetricAnswer(an, context, metric);
      if (r) return r;
    }

    /* 5. bare "top N" with no recognised dimension → top products */
    if (/\b(top|best|highest)\b/.test(p)) {
      const r = breakdownAnswer(an, prompt, context, BREAKDOWNS[1], countRequested(prompt, 10));
      if (r) return r;
    }

    return null;
  })();

  const answer = result || overviewAnswer(an, context);
  return Object.assign(answer, {
    source: 'local',
    context: { location: an.locName(context.loc), month: monthLabel(context.month) },
    available: {
      locations: Object.keys(an.locations),
      months: months.length,
      queries: [
        'top 10 products by revenue',
        'category mix',
        'net sales trend last 12 months',
        'trainer breakdown',
        'compare locations',
        'what is the churn rate',
      ],
    },
  });
}

/* ------------------------------------------------------- dataset for the LLM */
/* A compact, complete payload (not a one-row sample) so an OpenAI-backed answer
   has the same numbers the local engine uses. */
function buildDataset(analysisData, ctx, opts) {
  const an = new Analysis(analysisData);
  const limitMonths = (opts && opts.months) || 14;
  const locKeys = Object.keys(an.locations);
  const out = { locations: {}, months: {} };

  locKeys.forEach((loc) => {
    const months = an.monthsFor(loc).slice(-limitMonths);
    out.locations[loc] = { name: an.locName(loc), months: {} };
    months.forEach((m) => {
      const row = {};
      METRICS.forEach((metric) => {
        if (row[metric.label] !== undefined) return;
        const v = an.metric(loc, m, metric.group, metric.key);
        if (v !== null && v !== undefined) row[metric.label] = Math.round(Number(v) * 100) / 100;
      });
      out.locations[loc].months[m] = row;
    });
  });

  const bLoc = ctx && ctx.loc && an.locations[ctx.loc] ? ctx.loc : locKeys[0];
  const bMonth = ctx && ctx.month ? ctx.month : an.monthsFor(bLoc).slice(-1)[0];
  const groups = ['category', 'product', 'seller', 'payment'];
  out.breakdowns = {};
  groups.forEach((g) => {
    const raw = an.breakdown(bLoc, bMonth, 'sales_breakdowns', g);
    if (!raw) return;
    out.breakdowns[g] = Object.entries(raw)
      .map(([name, v]) => ({ name, net: Math.round(num(v && v.net) || 0), gross: Math.round(num(v && v.gross) || 0), txns: num(v && v.rows) || 0 }))
      .sort((a, b) => b.net - a.net)
      .slice(0, 20);
  });
  out.scope = { location: an.locName(bLoc), month: bMonth };
  return out;
}

module.exports = { answerCopilot, buildDataset, monthLabel };
