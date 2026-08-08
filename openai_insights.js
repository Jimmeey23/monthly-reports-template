const OPENAI_MODEL = process.env.OPENAI_MODEL || 'gpt-4o';

const SECTION_LABELS = {
  'executive-summary': 'Executive Summary',
  'revenue-performance': 'Revenue & Sales Performance',
  'conversion-funnel': 'Leads, Trials & Conversion Funnel',
  sessions: 'Sessions, Classes & Trainer Performance',
  lapsed: 'Lapsed Memberships & Retention',
  recommendations: 'Strategic Recommendations',
  predictions: 'Forecast & Forward View',
};

// Randomly varied analytical angles per call — prevents cookie-cutter output
const ANALYTICAL_ANGLES = [
  'Your primary lens is: what early warning signals exist in this data that, if ignored, will become serious problems in 60-90 days? Identify the leading indicators, not just the lagging ones.',
  'Your primary lens is: where is this studio leaving money on the table RIGHT NOW? Find the specific gap between current performance and realistic best-case, and quantify the revenue at stake.',
  'Your primary lens is: what story do the RATIOS tell that the raw numbers hide? Cross-reference metrics against each other — leads per session, revenue per member, churn as % of new joins, etc.',
  'Your primary lens is: where is the studio working HARDER for WORSE results? Find efficiency drains — high-effort, low-yield activities — and contrast with what IS working.',
  'Your primary lens is: what single intervention, if executed this week, would have the highest compounding effect over the next quarter? Reason from the data to a specific decision.',
  'Your primary lens is: what does the baseline trend reveal that this month alone cannot? Identify structural trends vs one-off spikes, and assign confidence to each insight accordingly.',
  'Your primary lens is: what would a private equity owner of this studio find alarming, and what would excite them? Separate vanity metrics from value-driving metrics.',
];

// Industry benchmarks for fitness studios — gives AI grounding for "good/bad"
const FITNESS_INDUSTRY_CONTEXT = `
FITNESS STUDIO INDUSTRY BENCHMARKS (use these to contextualise every metric):
- Lead → Trial conversion: 30-45% is healthy; below 25% signals a sales process problem
- Trial → Member conversion: 50-65% is strong; below 40% means the trial experience is weak
- Monthly churn rate: <3% is excellent; 3-6% is average; >8% is crisis territory
- Class fill rate: >65% is healthy; >80% on peak sessions indicates capacity ceiling
- Revenue per active member (monthly): should be tracked against ATV trends
- Net Promoter Score proxy: check-in frequency per member — active members visit 8-12x/month
- Membership to new-trial ratio: if new trials < 20% of active member count, pipeline is thin
- Lapsed recovery: if lapsed > new joins in any month, the studio is shrinking in real terms
- Discount rate: >20% gross-to-net gap signals promotional dependency, margin erosion risk
- Top trainer concentration: if top 3 trainers > 50% of sessions, there's key-person risk
`;

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

function pct(a, b) {
  if (!b || b === 0) return null;
  return Math.round(((a - b) / b) * 1000) / 10; // e.g. 18.3
}

function ratio(a, b, decimals = 2) {
  if (!b || b === 0) return null;
  return Math.round((a / b) * Math.pow(10, decimals)) / Math.pow(10, decimals);
}

/** Enrich data with derived ratios and MoM/baseline deltas — gives AI the "so what" numbers */
function enrichSales(cur, prev, base) {
  return {
    ...cur,
    prev_gross: prev.gross,
    gross_mom_pct: pct(cur.gross, prev.gross),
    gross_vs_baseline_pct: pct(cur.gross, base.gross),
    net_mom_pct: pct(cur.net, prev.net),
    discount_rate_pct: cur.gross ? Math.round(((cur.gross - cur.net) / cur.gross) * 1000) / 10 : null,
    prev_discount_rate_pct: prev.gross ? Math.round(((prev.gross - prev.net) / prev.gross) * 1000) / 10 : null,
    transactions_mom_pct: pct(cur.transactions, prev.transactions),
    atv_mom_pct: pct(cur.atv, prev.atv),
    revenue_per_member: cur.members ? ratio(cur.net, cur.members) : null,
  };
}

function enrichLeads(cur, prev, base) {
  return {
    ...cur,
    prev_total: prev.total,
    leads_mom_pct: pct(cur.total, prev.total),
    leads_vs_baseline_pct: pct(cur.total, base.total),
    lead_to_trial_rate_pct: cur.total ? Math.round((cur.converted / cur.total) * 1000) / 10 : null,
    prev_lead_to_trial_rate_pct: prev.total ? Math.round((prev.converted / prev.total) * 1000) / 10 : null,
  };
}

function enrichSessions(cur, base) {
  return {
    ...cur,
    sessions_vs_baseline_pct: pct(cur.sessions, base.sessions),
    avg_fill_rate_pct: cur.capacity && cur.visits ? ratio(cur.visits, cur.capacity, 1) * 100 : null,
    visits_per_session: cur.sessions ? ratio(cur.visits, cur.sessions) : null,
  };
}

function enrichLapsed(cur, prev, base) {
  return {
    ...cur,
    prev_total: prev.total,
    lapsed_mom_pct: pct(cur.total, prev.total),
    lapsed_vs_baseline_pct: pct(cur.total, base.total),
    churn_rate_pct: cur.active_base ? ratio(cur.total, cur.active_base, 3) * 100 : null,
  };
}

function baseCtx(analysis, locKey, month) {
  const get = (section) => (analysis[section] || {})[locKey] || {};
  return { studio: analysis.meta.locations[locKey], month, baseline_months: analysis.meta.baseline_months, get };
}

function buildDigest(analysis, locKey, month, section) {
  const { studio, get, baseline_months } = baseCtx(analysis, locKey, month);
  const baseline = (analysis.baseline || {})[locKey] || {};
  const common = { studio, month, baseline_months };
  const prevMonth = prevMonthKey(month);

  switch (section) {
    case 'revenue-performance': {
      const cur = get('sales')[month] || {};
      const prev = get('sales')[prevMonth] || {};
      const base = baseline.sales || {};
      return {
        ...common,
        sales: enrichSales(cur, prev, base),
        baseline_sales: base,
        top_categories: topN(get('sales_breakdowns')[month]?.category, 6, 'gross'),
        top_products: topN(get('sales_breakdowns')[month]?.product, 10, 'gross'),
        top_sellers: topN(get('sales_breakdowns')[month]?.seller, 6, 'gross'),
        prev_top_categories: topN(get('sales_breakdowns')[prevMonth]?.category, 6, 'gross'),
      };
    }

    case 'conversion-funnel': {
      const curLeads = get('leads')[month] || {};
      const prevLeads = get('leads')[prevMonth] || {};
      const baseLeads = baseline.leads || {};
      const curTrials = get('new')[month] || {};
      const prevTrials = get('new')[prevMonth] || {};
      return {
        ...common,
        leads: enrichLeads(curLeads, prevLeads, baseLeads),
        baseline_leads: baseLeads,
        trials: {
          ...curTrials,
          prev_total: prevTrials.total,
          trials_mom_pct: pct(curTrials.total, prevTrials.total),
          trial_to_member_rate_pct: curTrials.total && curLeads.converted
            ? ratio(curLeads.converted, curTrials.total, 3) * 100
            : null,
        },
        leads_by_source: topN(get('leads_by_source')[month], 8, 'total'),
        prev_leads_by_source: topN(get('leads_by_source')[prevMonth], 8, 'total'),
      };
    }

    case 'sessions': {
      const curSess = get('sessions')[month] || {};
      const baseSess = baseline.sessions || {};
      const trainers = topN(get('sessions_by_trainer')[month], 10);
      const totalTrainerSessions = trainers.reduce((s, t) => s + (t.sessions || 0), 0);
      const top3Sessions = trainers.slice(0, 3).reduce((s, t) => s + (t.sessions || 0), 0);
      return {
        ...common,
        sessions: enrichSessions(curSess, baseSess),
        baseline_sessions: baseSess,
        top_formats: topN(get('sessions_by_format')[month], 5),
        top_classes: topN(get('sessions_by_class')[month], 10),
        top_trainers: trainers,
        trainer_concentration_risk: totalTrainerSessions
          ? { top3_share_pct: Math.round((top3Sessions / totalTrainerSessions) * 100) }
          : null,
      };
    }

    case 'lapsed': {
      const curLapsed = get('lapsed')[month] || {};
      const prevLapsed = get('lapsed')[prevMonth] || {};
      const baseLapsed = baseline.lapsed || {};
      const newJoins = (get('new')[month] || {}).total || 0;
      const prevNewJoins = (get('new')[prevMonth] || {}).total || 0;
      return {
        ...common,
        lapsed: enrichLapsed(curLapsed, prevLapsed, baseLapsed),
        baseline_lapsed: baseLapsed,
        cumulative_lapsed: (get('lapsed_cumulative') || {})[month],
        top_lapsed_products: topN(get('lapsed_by_product')[month], 8, 'total'),
        net_member_change: newJoins - (curLapsed.total || 0),
        prev_net_member_change: prevNewJoins - (prevLapsed.total || 0),
        new_joins_this_month: newJoins,
        lapsed_to_new_ratio: newJoins ? ratio(curLapsed.total || 0, newJoins) : null,
      };
    }

    case 'predictions': {
      const cur = get('sales')[month] || {};
      const prev = get('sales')[prevMonth] || {};
      const base = baseline.sales || {};
      return {
        ...common,
        sales: enrichSales(cur, prev, base),
        baseline_sales: base,
        leads: enrichLeads(get('leads')[month] || {}, get('leads')[prevMonth] || {}, baseline.leads || {}),
        sessions: get('sessions')[month] || {},
        checkins: get('checkins')[month] || {},
        lapsed: get('lapsed')[month] || {},
        new_joins: (get('new')[month] || {}).total,
        active_memberships: (get('active') || {}).total,
      };
    }

    case 'recommendations':
    case 'executive-summary':
    default: {
      const cur = get('sales')[month] || {};
      const prev = get('sales')[prevMonth] || {};
      const base = baseline.sales || {};
      const curLapsed = get('lapsed')[month] || {};
      const newJoins = (get('new')[month] || {}).total || 0;
      return {
        ...common,
        sales: enrichSales(cur, prev, base),
        baseline_sales: base,
        sessions: enrichSessions(get('sessions')[month] || {}, baseline.sessions || {}),
        leads: enrichLeads(get('leads')[month] || {}, get('leads')[prevMonth] || {}, baseline.leads || {}),
        trials: get('new')[month] || {},
        lapsed: enrichLapsed(curLapsed, get('lapsed')[prevMonth] || {}, baseline.lapsed || {}),
        checkins: get('checkins')[month] || {},
        active_memberships: (get('active') || {}).total,
        net_member_change: newJoins - (curLapsed.total || 0),
        top_formats: topN(get('sessions_by_format')[month], 4),
        top_trainers: topN(get('sessions_by_trainer')[month], 6),
        top_categories: topN(get('sales_breakdowns')[month]?.category, 5, 'gross'),
      };
    }
  }
}

function prevMonthKey(month) {
  const [y, m] = month.split('-').map(Number);
  const py = m > 1 ? y : y - 1;
  const pm = m > 1 ? m - 1 : 12;
  return `${py}-${String(pm).padStart(2, '0')}`;
}

function systemPrompt(sectionLabel, angle) {
  return `You are a senior fitness-studio business analyst producing the "${sectionLabel}" section of a management performance report.

${FITNESS_INDUSTRY_CONTEXT}

ANALYTICAL DIRECTIVE FOR THIS CALL:
${angle}

RULES — violating any of these makes the output useless:
1. NEVER just restate a number without explaining WHY it matters and WHAT it implies about the business. "Gross sales were X" is worthless. "Gross sales outpaced the baseline by X% while ATV fell 5% — meaning volume is growing but ticket size is softening, likely from product mix shift" is what we want.
2. EVERY insight must connect at least TWO metrics to each other — find correlations, ratios, tensions, contradictions.
3. Compare against BOTH month-on-month AND baseline where available. A metric can look good MoM but be structurally declining vs baseline — call this out.
4. Use the industry benchmarks above to classify each metric as "excellent / healthy / warning / critical". State the classification explicitly.
5. At least 2 of your insights must identify something NON-OBVIOUS that a studio manager would NOT already know just from reading the dashboard numbers.
6. Actions must be SPECIFIC: name the exact metric to move, the lever to pull, the person responsible, and what success looks like numerically.
7. Write like an analyst, not a chatbot. Vary sentence structure. Use precise business language. No hedging phrases like "it appears" or "it seems".
8. Do NOT repeat the same insight in different words across the insights list.

REQUIRED OUTPUT — respond ONLY with valid JSON matching this exact shape:
{
  "summary": "2-3 sentence executive takeaway that captures the most important tension or opportunity this month — not just 'performance was good'",
  "insights": [
    {
      "title": "Short punchy headline (max 8 words)",
      "text": "2-3 sentences. Cite specific numbers. Cross-reference metrics. State classification (excellent/healthy/warning/critical). Explain the implication, not just the observation.",
      "classification": "excellent|healthy|warning|critical"
    }
  ],
  "actions": [
    {
      "action": "Specific action verb + what to do",
      "rationale": "Exact numbers from the data that justify this action",
      "impact": "Specific expected outcome, quantified where possible",
      "timeline": "e.g. This week / Next 2 weeks / By end of month",
      "owner": "Job title of person responsible",
      "priority": "high|medium|low"
    }
  ]
}

Produce 6-8 insights and 4-6 actions. Quality over quantity — each insight must earn its place.`;
}

async function generateInsights(analysis, locKey, month, section = 'executive-summary') {
  const apiKey = process.env.OPENAI_API_KEY;
  const model = process.env.OPENAI_MODEL || 'gpt-4o';

  if (!apiKey) {
    const err = new Error('OPENAI_API_KEY is not configured on the server. Please add OPENAI_API_KEY to your .env file or environment.');
    err.code = 'NO_API_KEY';
    throw err;
  }

  const digest = buildDigest(analysis, locKey, month, section);
  const sectionLabel = SECTION_LABELS[section] || section;
  const angle = ANALYTICAL_ANGLES[Math.floor(Math.random() * ANALYTICAL_ANGLES.length)];

  const res = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model,
      response_format: { type: 'json_object' },
      messages: [
        { role: 'system', content: systemPrompt(sectionLabel, angle) },
        { role: 'user', content: JSON.stringify(digest) },
      ],
      temperature: 0.8,
      presence_penalty: 0.5,
      frequency_penalty: 0.3,
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
