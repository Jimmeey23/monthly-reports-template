const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
const OPENAI_MODEL = process.env.OPENAI_MODEL || 'gpt-4o-mini';

const SECTION_LABELS = {
  'executive-summary': 'Executive Summary',
  'revenue-performance': 'Revenue & Sales Performance',
  'conversion-funnel': 'Leads, Trials & Conversion Funnel',
  sessions: 'Sessions, Classes & Trainer Performance',
  lapsed: 'Lapsed Memberships & Retention',
  recommendations: 'Strategic Recommendations',
  predictions: 'Forecast & Forward View',
};

const RANDOM_ANGLES = [
  'Focus especially on risk factors and what could go wrong if trends continue.',
  'Focus especially on the single biggest opportunity hiding in the numbers.',
  'Focus especially on how this month compares to the baseline trend, not just MoM.',
  'Focus especially on operational efficiency and where effort is being wasted.',
  'Focus especially on what a studio manager should personally check this week.',
  'Focus especially on outliers and anomalies in the data worth investigating.',
];

function pick(obj, keys) {
  const out = {};
  for (const k of keys) if (obj && obj[k] !== undefined) out[k] = obj[k];
  return out;
}

function topN(dict, n, sortKey = 'sessions') {
  return Object.entries(dict || {})
    .sort((a, b) => (b[1][sortKey] || 0) - (a[1][sortKey] || 0))
    .slice(0, n)
    .map(([name, v]) => ({ name, ...pick(v, ['sessions', 'visits', 'capacity', 'revenue', 'fill', 'total', 'gross', 'net', 'churn', 'renewed']) }));
}

function baseCtx(analysis, locKey, month) {
  const get = (section) => (analysis[section] || {})[locKey] || {};
  return {
    studio: analysis.meta.locations[locKey],
    month,
    baseline_months: analysis.meta.baseline_months,
    get,
  };
}

/** Build a digest scoped to what one section actually shows, so the AI call
 * stays cheap and the insights stay relevant to that section only. */
function buildDigest(analysis, locKey, month, section) {
  const { studio, get, baseline_months } = baseCtx(analysis, locKey, month);
  const baseline = (analysis.baseline || {})[locKey] || {};
  const common = { studio, month, baseline_months };

  switch (section) {
    case 'revenue-performance':
      return {
        ...common,
        sales: get('sales')[month] || {},
        prev_sales: get('sales')[prevMonthKey(month)] || {},
        baseline_sales: baseline.sales || {},
        top_categories: topN(get('sales_breakdowns')[month]?.category, 5, 'gross'),
        top_products: topN(get('sales_breakdowns')[month]?.product, 8, 'gross'),
        top_sellers: topN(get('sales_breakdowns')[month]?.seller, 5, 'gross'),
      };

    case 'conversion-funnel':
      return {
        ...common,
        leads: get('leads')[month] || {},
        prev_leads: get('leads')[prevMonthKey(month)] || {},
        baseline_leads: baseline.leads || {},
        trials: get('new')[month] || {},
        leads_by_source: topN(get('leads_by_source')[month], 6, 'total'),
      };

    case 'sessions':
      return {
        ...common,
        sessions: get('sessions')[month] || {},
        baseline_sessions: baseline.sessions || {},
        top_formats: topN(get('sessions_by_format')[month], 3),
        top_classes: topN(get('sessions_by_class')[month], 8),
        top_trainers: topN(get('sessions_by_trainer')[month], 8),
      };

    case 'lapsed':
      return {
        ...common,
        lapsed: get('lapsed')[month] || {},
        baseline_lapsed: baseline.lapsed || {},
        cumulative_lapsed: (get('lapsed_cumulative') || {})[month],
        top_lapsed_products: topN(get('lapsed_by_product')[month], 6, 'total'),
      };

    case 'predictions':
      return {
        ...common,
        sales: get('sales')[month] || {},
        prev_sales: get('sales')[prevMonthKey(month)] || {},
        baseline_sales: baseline.sales || {},
        leads: get('leads')[month] || {},
        checkins: get('checkins')[month] || {},
      };

    case 'recommendations':
    case 'executive-summary':
    default:
      return {
        ...common,
        sales: get('sales')[month] || {},
        sessions: get('sessions')[month] || {},
        leads: get('leads')[month] || {},
        trials: get('new')[month] || {},
        lapsed: get('lapsed')[month] || {},
        checkins: get('checkins')[month] || {},
        active_memberships: (get('active') || {}).total,
        baseline,
        top_formats: topN(get('sessions_by_format')[month], 3),
        top_trainers: topN(get('sessions_by_trainer')[month], 6),
      };
  }
}

function prevMonthKey(month) {
  const [y, m] = month.split('-').map(Number);
  const py = m > 1 ? y : y - 1;
  const pm = m > 1 ? m - 1 : 12;
  return `${py}-${String(pm).padStart(2, '0')}`;
}

function systemPrompt(sectionLabel, angle) {
  return `You are a fitness-studio business analyst reviewing the "${sectionLabel}" section of one studio's monthly performance report. You will be given a JSON digest of just the metrics relevant to this section.

Write 5-7 data-backed insights and 3-5 concrete action items specific to this section only — do not discuss other parts of the business. Every insight and action must cite a specific number from the digest — no generic advice. ${angle}

Vary your phrasing and structure from a typical templated report — write like an analyst who actually looked at these specific numbers, not a boilerplate generator. Respond ONLY with JSON matching this shape:
{
  "summary": "1-2 sentence takeaway for this section",
  "insights": [{"title": "short headline", "text": "1-2 sentences with specific numbers"}],
  "actions": [{"action": "specific action", "rationale": "why, with a number", "impact": "expected effect", "timeline": "e.g. 2 weeks", "owner": "e.g. Studio Manager"}]
}`;
}

async function generateInsights(analysis, locKey, month, section = 'executive-summary') {
  if (!OPENAI_API_KEY) {
    const err = new Error('OPENAI_API_KEY is not configured on the server.');
    err.code = 'NO_API_KEY';
    throw err;
  }

  const digest = buildDigest(analysis, locKey, month, section);
  const sectionLabel = SECTION_LABELS[section] || section;
  const angle = RANDOM_ANGLES[Math.floor(Math.random() * RANDOM_ANGLES.length)];

  const res = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${OPENAI_API_KEY}`,
    },
    body: JSON.stringify({
      model: OPENAI_MODEL,
      response_format: { type: 'json_object' },
      messages: [
        { role: 'system', content: systemPrompt(sectionLabel, angle) },
        { role: 'user', content: JSON.stringify(digest) },
      ],
      temperature: 0.9,
      presence_penalty: 0.4,
    }),
  });

  if (!res.ok) {
    const errText = await res.text().catch(() => res.statusText);
    throw new Error(`OpenAI API error ${res.status}: ${errText}`);
  }

  const json = await res.json();
  const content = json.choices?.[0]?.message?.content;
  if (!content) throw new Error('OpenAI returned no content');
  return JSON.parse(content);
}

module.exports = { generateInsights, SECTION_LABELS };
