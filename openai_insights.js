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
  'ANALYTICAL LENS: LEADING vs LAGGING INDICATORS. Separate metrics that PREDICT the future (lead volume trend, trial conversion momentum, churn velocity) from metrics that REPORT the past (total revenue, member count). Your insights must explicitly label which type each metric is. For every lagging indicator you cite, connect it to the leading indicator that caused it. Identify at minimum one leading indicator that is flashing a warning the lagging indicators haven\'t caught up to yet.',

  'ANALYTICAL LENS: REVENUE QUALITY DECOMPOSITION. Revenue can grow for bad reasons (discounts buying volume, one-off spikes, unsustainable promotional dependency). Decompose this month\'s revenue into: (a) organic growth vs promotional lift, (b) recurring/membership revenue vs transactional, (c) price-driven vs volume-driven. Quantify each component. Flag any growth that is "hollow" — top-line expansion masking structural weakness.',

  'ANALYTICAL LENS: UNIT ECONOMICS & EFFICIENCY. Ignore total numbers entirely. Focus ONLY on per-unit metrics: revenue per member, revenue per session, cost of acquisition (leads needed per new member), lifetime value signals (churn rate × average monthly value), capacity utilization. Compare these ratios across months to find efficiency trends the totals hide. A studio can grow revenue while destroying unit economics — find out if that\'s happening.',

  'ANALYTICAL LENS: COHORT BEHAVIOR SIGNALS. Even without explicit cohort data, the relationship between new joins, lapsed, active base, and check-in frequency reveals cohort behavior. Are new members sticking (check-in frequency stable despite growth)? Is the lapsed pool growing faster than acquisition (negative net flow)? Is the "active" base actually active or just technically subscribed? Build a narrative about member lifecycle health.',

  'ANALYTICAL LENS: STRUCTURAL CEILINGS & BOTTLENECKS. Find the constraint that will cap growth BEFORE the studio hits it. Is it class capacity (fill rates approaching limits)? Trainer bandwidth (top 3 trainers overloaded)? Sales pipeline thinness (not enough leads to sustain conversion targets)? Facility throughput (check-ins per day approaching physical limits)? Identify the binding constraint and quantify how close the studio is to hitting it.',

  'ANALYTICAL LENS: MOMENTUM & VELOCITY. Don\'t just compare month-to-month — compute the RATE OF CHANGE of the rate of change. Is growth accelerating or decelerating? A metric can be "up" month-over-month but losing momentum (growth rate slowing). Plot the trajectory: if current velocity continues, where does each metric land in 3 months? Flag any metric where velocity is diverging from the headline number (e.g., revenue up but growth rate halving each month).',

  'ANALYTICAL LENS: HIDDEN CORRELATIONS & CONTRADICTIONS. Find metrics that SHOULD move together but aren\'t. Revenue up but transactions down = price increase or mix shift. Leads up but conversions flat = acquisition quality problem. Sessions up but check-ins flat = ghost classes. New members up but active base flat = churn eating growth. Identify at least 3 such tensions and explain what each reveals about the underlying business dynamics.',
];

// Industry benchmarks for fitness studios
const FITNESS_INDUSTRY_CONTEXT = `
FITNESS STUDIO INDUSTRY BENCHMARKS (use these to contextualise every metric):
- Lead → Trial conversion: 30-45% is healthy; below 25% signals a sales process problem
- Trial → Member conversion: 50-65% is strong; below 40% means the trial experience is weak
- Monthly churn rate: <3% is excellent; 3-6% is average; >8% is crisis territory
- Class fill rate: >65% is healthy; >80% on peak sessions indicates capacity ceiling
- Revenue per active member (monthly): ₹8,000-12,000 is healthy for premium studios
- Net Promoter Score proxy: check-in frequency per member — active members visit 8-12x/month
- Membership to new-trial ratio: if new trials < 20% of active member count, pipeline is thin
- Lapsed recovery: if lapsed > new joins in any month, the studio is shrinking in real terms
- Discount rate: >20% gross-to-net gap signals promotional dependency, margin erosion risk
- Top trainer concentration: if top 3 trainers > 50% of sessions, there's key-person risk
- Late cancellation rate: >10% of check-ins indicates scheduling friction or commitment issues
- Healthy growth: net member change should be positive and accelerating quarter-over-quarter
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
    .map(([name, v]) => ({ name, ...pick(v, ['sessions', 'visits', 'capacity', 'revenue', 'fill', 'total', 'gross', 'net', 'churn', 'renewed', 'lapsed', 'frozen']) }));
}

function pct(a, b) {
  if (!b || b === 0) return null;
  return Math.round(((a - b) / b) * 1000) / 10;
}

function ratio(a, b, decimals = 2) {
  if (!b || b === 0) return null;
  return Math.round((a / b) * Math.pow(10, decimals)) / Math.pow(10, decimals);
}

/** Compute trend direction and velocity from an array of values */
function trendAnalysis(values) {
  if (!values || values.length < 3) return null;
  const recent3 = values.slice(-3);
  const deltas = [];
  for (let i = 1; i < values.length; i++) {
    if (values[i - 1] !== 0 && values[i - 1] != null) {
      deltas.push(((values[i] - values[i - 1]) / values[i - 1]) * 100);
    }
  }
  const avgDelta = deltas.length ? deltas.reduce((s, d) => s + d, 0) / deltas.length : 0;
  const recentDelta = deltas.length >= 2 ? deltas[deltas.length - 1] : null;
  const prevDelta = deltas.length >= 2 ? deltas[deltas.length - 2] : null;

  let acceleration = null;
  if (recentDelta != null && prevDelta != null) {
    acceleration = Math.round((recentDelta - prevDelta) * 10) / 10;
  }

  // Linear regression for 3-month projection
  let projected_3mo = null;
  if (values.length >= 3) {
    const n = values.length;
    const xMean = (n - 1) / 2;
    const yMean = values.reduce((s, v) => s + v, 0) / n;
    let num = 0, den = 0;
    for (let i = 0; i < n; i++) {
      num += (i - xMean) * (values[i] - yMean);
      den += (i - xMean) * (i - xMean);
    }
    const slope = den !== 0 ? num / den : 0;
    projected_3mo = Math.round(values[n - 1] + slope * 3);
  }

  return {
    direction: avgDelta > 2 ? 'upward' : avgDelta < -2 ? 'downward' : 'flat',
    avg_mom_change_pct: Math.round(avgDelta * 10) / 10,
    recent_mom_change_pct: recentDelta != null ? Math.round(recentDelta * 10) / 10 : null,
    acceleration_pct_pts: acceleration,
    momentum: acceleration != null ? (acceleration > 1 ? 'accelerating' : acceleration < -1 ? 'decelerating' : 'steady') : null,
    projected_3mo_if_trend_continues: projected_3mo,
    values_last_6mo: values.slice(-6).map(v => Math.round(v)),
  };
}

/** Build multi-month time series for a metric */
function buildTimeSeries(data, months, key) {
  return months.map(m => (data[m] || {})[key] || 0);
}

/** Detect anomalies — values that deviate significantly from recent average */
function detectAnomalies(values, label) {
  if (!values || values.length < 4) return [];
  const recent = values.slice(-4, -1); // last 3 months excluding current
  const avg = recent.reduce((s, v) => s + v, 0) / recent.length;
  const current = values[values.length - 1];
  if (avg === 0) return [];
  const deviation = ((current - avg) / avg) * 100;
  if (Math.abs(deviation) > 15) {
    return [{
      metric: label,
      current_value: Math.round(current),
      recent_3mo_avg: Math.round(avg),
      deviation_pct: Math.round(deviation * 10) / 10,
      type: deviation > 0 ? 'spike' : 'drop',
    }];
  }
  return [];
}

/** Compute cross-metric correlations and tensions */
function computeCrossMetrics(salesData, leadsData, sessionsData, lapsedData, newData, checkinsData, activeTotal, months) {
  const crossMetrics = {};
  const curMonth = months[months.length - 1];
  const prevMonth = months.length > 1 ? months[months.length - 2] : null;

  const curSales = salesData[curMonth] || {};
  const prevSales = prevMonth ? (salesData[prevMonth] || {}) : {};
  const curLeads = leadsData[curMonth] || {};
  const prevLeads = prevMonth ? (leadsData[prevMonth] || {}) : {};
  const curSessions = sessionsData[curMonth] || {};
  const curLapsed = lapsedData[curMonth] || {};
  const prevLapsed = prevMonth ? (lapsedData[prevMonth] || {}) : {};
  const curNew = newData[curMonth] || {};
  const prevNew = prevMonth ? (newData[prevMonth] || {}) : {};
  const curCheckins = checkinsData[curMonth] || {};

  // Revenue per active member
  if (activeTotal && curSales.net) {
    crossMetrics.revenue_per_active_member = Math.round(curSales.net / activeTotal);
  }

  // Revenue per session (class economics)
  if (curSessions.sessions && curSales.net) {
    crossMetrics.revenue_per_session = Math.round(curSales.net / curSessions.sessions);
  }

  // Acquisition efficiency: leads needed per new member
  if (curLeads.total && curNew.total) {
    crossMetrics.leads_per_new_member = Math.round((curLeads.total / curNew.total) * 10) / 10;
  }

  // Net member flow: new joins minus lapsed
  crossMetrics.net_member_flow = (curNew.total || 0) - (curLapsed.total || 0);
  if (prevMonth) {
    crossMetrics.prev_net_member_flow = (prevNew.total || 0) - (prevLapsed.total || 0);
  }

  // Check-in intensity: visits per member per month
  if (curCheckins.total && activeTotal) {
    crossMetrics.checkins_per_member = Math.round((curCheckins.total / activeTotal) * 10) / 10;
  }

  // Late cancellation rate
  if (curCheckins.total && curCheckins.late_cancel) {
    crossMetrics.late_cancel_rate_pct = Math.round((curCheckins.late_cancel / (curCheckins.total + curCheckins.late_cancel)) * 1000) / 10;
    crossMetrics.late_cancel_member_pct = curCheckins.lc_member_count && activeTotal
      ? Math.round((curCheckins.lc_member_count / activeTotal) * 1000) / 10
      : null;
  }

  // Revenue composition: membership vs non-membership (needs breakdown data)

  // Capacity utilization
  if (curSessions.capacity && curSessions.visits) {
    crossMetrics.capacity_utilization_pct = Math.round((curSessions.visits / curSessions.capacity) * 1000) / 10;
  }

  // Churn replacement ratio: how many new members to replace one churned
  if (curLapsed.total && curNew.total && curLapsed.total > 0) {
    crossMetrics.churn_replacement_ratio = Math.round((curNew.total / curLapsed.total) * 100) / 100;
    crossMetrics.churn_replacement_label = crossMetrics.churn_replacement_ratio > 1
      ? 'growing (acquiring faster than losing)'
      : crossMetrics.churn_replacement_ratio === 1
        ? 'treading water'
        : 'shrinking (losing faster than acquiring)';
  }

  // Revenue volatility: standard deviation of monthly gross over available months
  const grossValues = months.map(m => (salesData[m] || {}).gross || 0).filter(v => v > 0);
  if (grossValues.length >= 3) {
    const mean = grossValues.reduce((s, v) => s + v, 0) / grossValues.length;
    const variance = grossValues.reduce((s, v) => s + Math.pow(v - mean, 2), 0) / grossValues.length;
    crossMetrics.revenue_volatility_cv = Math.round((Math.sqrt(variance) / mean) * 1000) / 10;
    crossMetrics.revenue_volatility_label = crossMetrics.revenue_volatility_cv < 10
      ? 'very stable'
      : crossMetrics.revenue_volatility_cv < 20
        ? 'moderately stable'
        : crossMetrics.revenue_volatility_cv < 35
          ? 'volatile'
          : 'highly volatile — needs investigation';
  }

  // Discount dependency trend
  const discRates = months.map(m => {
    const s = salesData[m] || {};
    return s.gross ? Math.round(((s.gross - s.net) / s.gross) * 1000) / 10 : null;
  }).filter(v => v != null);
  if (discRates.length >= 2) {
    crossMetrics.discount_rate_trend = discRates;
    crossMetrics.discount_dependency_direction = discRates[discRates.length - 1] > discRates[discRates.length - 2] ? 'increasing' : 'decreasing';
  }

  return crossMetrics;
}

/** Enrich data with derived ratios and MoM/baseline deltas */
function enrichSales(cur, prev, base) {
  return {
    ...cur,
    prev_gross: prev.gross,
    prev_net: prev.net,
    prev_transactions: prev.sales,
    gross_mom_pct: pct(cur.gross, prev.gross),
    gross_vs_baseline_pct: pct(cur.gross, base.gross),
    net_mom_pct: pct(cur.net, prev.net),
    net_vs_baseline_pct: pct(cur.net, base.net),
    discount_rate_pct: cur.gross ? Math.round(((cur.gross - cur.net) / cur.gross) * 1000) / 10 : null,
    prev_discount_rate_pct: prev.gross ? Math.round(((prev.gross - prev.net) / prev.gross) * 1000) / 10 : null,
    baseline_discount_rate_pct: base.gross ? Math.round(((base.gross - base.net) / base.gross) * 1000) / 10 : null,
    transactions_mom_pct: pct(cur.sales, prev.sales),
    atv_mom_pct: pct(cur.atv, prev.atv),
    atv_vs_baseline_pct: pct(cur.atv, base.atv),
    revenue_per_member: cur.members ? ratio(cur.net, cur.members) : null,
    prev_revenue_per_member: prev.members ? ratio(prev.net, prev.members) : null,
    // Revenue growth decomposition
    volume_driven_growth: prev.gross && cur.sales && prev.sales
      ? Math.round((cur.sales - prev.sales) * prev.atv)
      : null,
    price_driven_growth: prev.gross && cur.atv && prev.atv
      ? Math.round((cur.atv - prev.atv) * prev.sales)
      : null,
  };
}

function enrichLeads(cur, prev, base) {
  return {
    ...cur,
    prev_total: prev.total,
    prev_converted: prev.converted,
    leads_mom_pct: pct(cur.total, prev.total),
    leads_vs_baseline_pct: pct(cur.total, base.total),
    lead_to_trial_rate_pct: cur.total ? Math.round((cur.converted / cur.total) * 1000) / 10 : null,
    prev_lead_to_trial_rate_pct: prev.total ? Math.round((prev.converted / prev.total) * 1000) / 10 : null,
    baseline_conversion_rate_pct: base.rate || null,
    conversion_rate_vs_baseline: base.rate && cur.total
      ? Math.round(((cur.converted / cur.total) * 100 - base.rate) * 10) / 10
      : null,
  };
}

function enrichSessions(cur, base) {
  return {
    ...cur,
    sessions_vs_baseline_pct: pct(cur.sessions, base.sessions),
    avg_fill_rate_pct: cur.capacity && cur.visits ? ratio(cur.visits, cur.capacity, 1) * 100 : null,
    baseline_fill_rate_pct: base.fill || null,
    visits_per_session: cur.sessions ? ratio(cur.visits, cur.sessions) : null,
    baseline_visits_per_session: base.sessions ? ratio(base.visits, base.sessions) : null,
    empty_sessions: cur.empty || 0,
    revenue_per_session: cur.sessions && cur.revenue ? Math.round(cur.revenue / cur.sessions) : null,
  };
}

function enrichLapsed(cur, prev, base) {
  return {
    ...cur,
    prev_total: prev.total,
    prev_renewed: prev.renewed,
    prev_lapsed: prev.lapsed,
    lapsed_mom_pct: pct(cur.total, prev.total),
    lapsed_vs_baseline_pct: pct(cur.total, base.total),
    churn_rate_pct: cur.active_base ? ratio(cur.total, cur.active_base, 3) * 100 : null,
    renewal_rate_pct: cur.total ? Math.round((cur.renewed / cur.total) * 1000) / 10 : null,
    prev_renewal_rate_pct: prev.total ? Math.round((prev.renewed / prev.total) * 1000) / 10 : null,
    baseline_renewal_rate_pct: base.renewal_rate || null,
    hard_churn_rate_pct: cur.total ? Math.round((cur.lapsed / cur.total) * 1000) / 10 : null,
  };
}

function prevMonthKey(month) {
  const [y, m] = month.split('-').map(Number);
  const py = m > 1 ? y : y - 1;
  const pm = m > 1 ? m - 1 : 12;
  return `${py}-${String(pm).padStart(2, '0')}`;
}

/** Get all sorted month keys available for a location's sales data */
function getAvailableMonths(analysis, locKey) {
  const salesData = (analysis.sales || {})[locKey] || {};
  return Object.keys(salesData).sort();
}

function baseCtx(analysis, locKey, month) {
  const get = (section) => (analysis[section] || {})[locKey] || {};
  return { studio: (analysis.meta || {}).locations ? analysis.meta.locations[locKey] : locKey, month, baseline_months: (analysis.meta || {}).baseline_months, get };
}

function buildDigest(analysis, locKey, month, section) {
  const { studio, get, baseline_months } = baseCtx(analysis, locKey, month);
  const baseline = (analysis.baseline || {})[locKey] || {};
  const common = { studio, month, baseline_months };
  const prevMonth = prevMonthKey(month);

  // Get ALL available months for trend analysis
  const allMonths = getAvailableMonths(analysis, locKey);
  const salesData = get('sales');
  const leadsData = get('leads');
  const sessionsData = get('sessions');
  const lapsedData = get('lapsed');
  const newData = get('new');
  const checkinsData = get('checkins');
  const activeTotal = (get('active') || {}).total;

  // Build multi-month trend analysis
  const trendData = {
    gross_revenue_trend: trendAnalysis(buildTimeSeries(salesData, allMonths, 'gross')),
    net_revenue_trend: trendAnalysis(buildTimeSeries(salesData, allMonths, 'net')),
    transactions_trend: trendAnalysis(buildTimeSeries(salesData, allMonths, 'sales')),
    atv_trend: trendAnalysis(buildTimeSeries(salesData, allMonths, 'atv')),
    members_trend: trendAnalysis(buildTimeSeries(salesData, allMonths, 'members')),
    leads_trend: trendAnalysis(buildTimeSeries(leadsData, allMonths, 'total')),
    sessions_trend: trendAnalysis(buildTimeSeries(sessionsData, allMonths, 'sessions')),
    visits_trend: trendAnalysis(buildTimeSeries(sessionsData, allMonths, 'visits')),
    lapsed_trend: trendAnalysis(buildTimeSeries(lapsedData, allMonths, 'total')),
    new_joins_trend: trendAnalysis(buildTimeSeries(newData, allMonths, 'total')),
    checkins_trend: trendAnalysis(buildTimeSeries(checkinsData, allMonths, 'total')),
  };

  // Detect anomalies
  const anomalies = [
    ...detectAnomalies(buildTimeSeries(salesData, allMonths, 'gross'), 'gross_revenue'),
    ...detectAnomalies(buildTimeSeries(salesData, allMonths, 'sales'), 'transaction_count'),
    ...detectAnomalies(buildTimeSeries(salesData, allMonths, 'atv'), 'average_transaction_value'),
    ...detectAnomalies(buildTimeSeries(leadsData, allMonths, 'total'), 'lead_volume'),
    ...detectAnomalies(buildTimeSeries(lapsedData, allMonths, 'total'), 'lapsed_members'),
    ...detectAnomalies(buildTimeSeries(checkinsData, allMonths, 'total'), 'checkins'),
    ...detectAnomalies(buildTimeSeries(checkinsData, allMonths, 'late_cancel'), 'late_cancellations'),
  ];

  // Cross-metric analysis
  const crossMetrics = computeCrossMetrics(salesData, leadsData, sessionsData, lapsedData, newData, checkinsData, activeTotal, allMonths);

  switch (section) {
    case 'revenue-performance': {
      const cur = salesData[month] || {};
      const prev = salesData[prevMonth] || {};
      const base = baseline.sales || {};

      // Monthly gross revenue values for sparkline context
      const monthlyGross = {};
      allMonths.forEach(m => { monthlyGross[m] = (salesData[m] || {}).gross || 0; });

      return {
        ...common,
        sales: enrichSales(cur, prev, base),
        baseline_sales: base,
        top_categories: topN(get('sales_breakdowns')[month]?.category, 8, 'gross'),
        top_products: topN(get('sales_breakdowns')[month]?.product, 10, 'gross'),
        top_sellers: topN(get('sales_breakdowns')[month]?.seller, 8, 'gross'),
        prev_top_categories: topN(get('sales_breakdowns')[prevMonth]?.category, 8, 'gross'),
        prev_top_products: topN(get('sales_breakdowns')[prevMonth]?.product, 10, 'gross'),
        trends: pick(trendData, ['gross_revenue_trend', 'net_revenue_trend', 'transactions_trend', 'atv_trend', 'members_trend']),
        anomalies: anomalies.filter(a => ['gross_revenue', 'transaction_count', 'average_transaction_value'].includes(a.metric)),
        cross_metrics: pick(crossMetrics, ['revenue_per_active_member', 'revenue_per_session', 'revenue_volatility_cv', 'revenue_volatility_label', 'discount_rate_trend', 'discount_dependency_direction']),
        monthly_revenue_history: monthlyGross,
        active_member_count: activeTotal,
      };
    }

    case 'conversion-funnel': {
      const curLeads = leadsData[month] || {};
      const prevLeads = leadsData[prevMonth] || {};
      const baseLeads = baseline.leads || {};
      const curTrials = newData[month] || {};
      const prevTrials = newData[prevMonth] || {};
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
        leads_by_source: topN(get('leads_by_source')[month], 10, 'total'),
        prev_leads_by_source: topN(get('leads_by_source')[prevMonth], 10, 'total'),
        new_by_type: topN(get('new_by_type')[month], 10, 'total'),
        prev_new_by_type: topN(get('new_by_type')[prevMonth], 10, 'total'),
        trends: pick(trendData, ['leads_trend', 'new_joins_trend']),
        anomalies: anomalies.filter(a => ['lead_volume'].includes(a.metric)),
        cross_metrics: pick(crossMetrics, ['leads_per_new_member', 'net_member_flow', 'prev_net_member_flow', 'churn_replacement_ratio', 'churn_replacement_label']),
        active_member_count: activeTotal,
      };
    }

    case 'sessions': {
      const curSess = sessionsData[month] || {};
      const baseSess = baseline.sessions || {};
      const trainers = topN(get('sessions_by_trainer')[month], 12);
      const prevTrainers = topN(get('sessions_by_trainer')[prevMonth], 12);
      const totalTrainerSessions = trainers.reduce((s, t) => s + (t.sessions || 0), 0);
      const top3Sessions = trainers.slice(0, 3).reduce((s, t) => s + (t.sessions || 0), 0);
      const curCheckins = checkinsData[month] || {};
      return {
        ...common,
        sessions: enrichSessions(curSess, baseSess),
        baseline_sessions: baseSess,
        top_formats: topN(get('sessions_by_format')[month], 8),
        prev_top_formats: topN(get('sessions_by_format')[prevMonth], 8),
        top_classes: topN(get('sessions_by_class')[month], 12),
        prev_top_classes: topN(get('sessions_by_class')[prevMonth], 12),
        top_trainers: trainers,
        prev_top_trainers: prevTrainers,
        trainer_concentration_risk: totalTrainerSessions
          ? {
              top3_share_pct: Math.round((top3Sessions / totalTrainerSessions) * 100),
              total_trainers: trainers.length,
              top3_sessions: top3Sessions,
              total_sessions: totalTrainerSessions,
            }
          : null,
        checkins: curCheckins,
        trends: pick(trendData, ['sessions_trend', 'visits_trend', 'checkins_trend']),
        anomalies: anomalies.filter(a => ['checkins', 'late_cancellations'].includes(a.metric)),
        cross_metrics: pick(crossMetrics, ['capacity_utilization_pct', 'checkins_per_member', 'late_cancel_rate_pct', 'late_cancel_member_pct', 'revenue_per_session']),
        active_member_count: activeTotal,
      };
    }

    case 'lapsed': {
      const curLapsed = lapsedData[month] || {};
      const prevLapsed = lapsedData[prevMonth] || {};
      const baseLapsed = baseline.lapsed || {};
      const newJoins = (newData[month] || {}).total || 0;
      const prevNewJoins = (newData[prevMonth] || {}).total || 0;

      // Multi-month net member flow
      const netFlowHistory = {};
      allMonths.forEach(m => {
        const nj = (newData[m] || {}).total || 0;
        const lp = (lapsedData[m] || {}).total || 0;
        netFlowHistory[m] = nj - lp;
      });

      return {
        ...common,
        lapsed: enrichLapsed(curLapsed, prevLapsed, baseLapsed),
        baseline_lapsed: baseLapsed,
        cumulative_lapsed: (get('lapsed_cumulative') || {})[month],
        top_lapsed_products: topN(get('lapsed_by_product')[month], 10, 'total'),
        prev_top_lapsed_products: topN(get('lapsed_by_product')[prevMonth], 10, 'total'),
        net_member_change: newJoins - (curLapsed.total || 0),
        prev_net_member_change: prevNewJoins - (prevLapsed.total || 0),
        new_joins_this_month: newJoins,
        prev_new_joins: prevNewJoins,
        lapsed_to_new_ratio: newJoins ? ratio(curLapsed.total || 0, newJoins) : null,
        trends: pick(trendData, ['lapsed_trend', 'new_joins_trend']),
        anomalies: anomalies.filter(a => ['lapsed_members'].includes(a.metric)),
        cross_metrics: pick(crossMetrics, ['net_member_flow', 'prev_net_member_flow', 'churn_replacement_ratio', 'churn_replacement_label']),
        net_flow_history: netFlowHistory,
        active_member_count: activeTotal,
      };
    }

    case 'predictions': {
      const cur = salesData[month] || {};
      const prev = salesData[prevMonth] || {};
      const base = baseline.sales || {};
      return {
        ...common,
        sales: enrichSales(cur, prev, base),
        baseline_sales: base,
        leads: enrichLeads(leadsData[month] || {}, leadsData[prevMonth] || {}, baseline.leads || {}),
        sessions: sessionsData[month] || {},
        checkins: checkinsData[month] || {},
        lapsed: lapsedData[month] || {},
        new_joins: (newData[month] || {}).total,
        active_memberships: activeTotal,
        trends: trendData,
        anomalies,
        cross_metrics: crossMetrics,
      };
    }

    case 'recommendations':
    case 'executive-summary':
    default: {
      const cur = salesData[month] || {};
      const prev = salesData[prevMonth] || {};
      const base = baseline.sales || {};
      const curLapsed = lapsedData[month] || {};
      const newJoins = (newData[month] || {}).total || 0;
      return {
        ...common,
        sales: enrichSales(cur, prev, base),
        baseline_sales: base,
        sessions: enrichSessions(sessionsData[month] || {}, baseline.sessions || {}),
        leads: enrichLeads(leadsData[month] || {}, leadsData[prevMonth] || {}, baseline.leads || {}),
        trials: newData[month] || {},
        lapsed: enrichLapsed(curLapsed, lapsedData[prevMonth] || {}, baseline.lapsed || {}),
        checkins: checkinsData[month] || {},
        active_memberships: activeTotal,
        net_member_change: newJoins - (curLapsed.total || 0),
        top_formats: topN(get('sessions_by_format')[month], 5),
        top_trainers: topN(get('sessions_by_trainer')[month], 8),
        top_categories: topN(get('sales_breakdowns')[month]?.category, 6, 'gross'),
        top_products: topN(get('sales_breakdowns')[month]?.product, 8, 'gross'),
        trends: trendData,
        anomalies,
        cross_metrics: crossMetrics,
      };
    }
  }
}

function systemPrompt(sectionLabel, angle) {
  return `You are a SENIOR FITNESS-STUDIO BUSINESS STRATEGIST and trusted advisor with 15 years of experience helping premium boutique fitness studios grow. You are producing the "${sectionLabel}" analysis for a monthly management performance report.

${FITNESS_INDUSTRY_CONTEXT}

${angle}

═══════════════════════════════════════════════════════════════
WHAT THE DASHBOARD ALREADY SHOWS (DO NOT SIMPLY RESTATE):
═══════════════════════════════════════════════════════════════
The report dashboard already displays raw numbers, KPI cards, charts, and tables with:
- Gross/net sales, discounts, transaction count, ATV — current vs previous month
- Top categories, products, and sellers
- Lead counts, conversion rates, source breakdowns
- Session counts, fill rates, trainer leaderboards
- Lapsed member counts, renewal rates, product breakdowns
- Month-over-month and baseline percentage changes

Your job is to go DEEPER — explain the WHY, the WHAT NEXT, and the SO WHAT. Don't restate numbers the user can already read.

═══════════════════════════════════════════════════════════════
TONE & FRAMING — CRITICAL:
═══════════════════════════════════════════════════════════════

You are a TRUSTED ADVISOR. Your job is to EMPOWER and MOTIVATE, not alarm.

1. LEAD with wins and strengths — celebrate with specificity, not generic praise.
2. Frame every gap as an OPPORTUNITY with quantified upside: "Lead conversion at 12% is the studio's single biggest growth lever — moving to 25% doubles the pipeline without additional spend."
3. For every dip or underperformance, ALWAYS pair it with a concrete fix and the expected outcome of implementing it.
4. Use CONSTRUCTIVE language: "opportunity to capture", "room to unlock", "next growth lever", "potential upside", "quick win available."
5. NEVER use: "alarming", "crisis", "failing", "dangerous", "problematic", "concerning", "troubling."
6. The reader should finish feeling ENERGISED and clear on what to do next.

═══════════════════════════════════════════════════════════════
DEPTH MODEL — WHAT SEPARATES BASIC FROM ADVANCED:
═══════════════════════════════════════════════════════════════

❌ BASIC (UNACCEPTABLE):
"Gross sales increased 18.3% to ₹2,580,029"

✅ ADVANCED (THE MINIMUM BAR):
"This month's 18.3% revenue growth is primarily volume-driven — transactions jumped 23.8% while ATV dipped 4.4%. This means the studio is attracting more customers (a strong sign of market pull), and the next unlock is stabilising ATV through premium upsells or package restructuring, which could add an estimated ₹95K/month in recovered margin."

═══════════════════════════════════════════════════════════════
ANALYTICAL FRAMEWORKS:
═══════════════════════════════════════════════════════════════

1. DECOMPOSITION: Revenue = Volume × Price. Growth = Organic + Promotional. Report which component drives the aggregate.
2. CROSS-REFERENCING: Connect 2+ metrics that reveal something new when combined.
3. TREND VELOCITY: Use multi-month trend data — is momentum accelerating or decelerating?
4. COUNTERFACTUAL: "If X had stayed at last month's level, Y would have been Z."
5. OPPORTUNITY SIZING: Quantify the upside of closing each gap.
6. PATTERN RECOGNITION: Identify repeating behaviors, seasonal signals, or structural shifts across the multi-month data.

═══════════════════════════════════════════════════════════════
HARD RULES:
═══════════════════════════════════════════════════════════════

1. Every claim MUST cite specific numbers from the data to back it up.
2. Every insight MUST cross-reference at least 2 metrics.
3. Use ₹ for currency. Format large numbers with commas (e.g., ₹25,80,029).
4. No hedging — state conclusions confidently with evidence inline.
5. Never repeat the same insight in different words.
6. Use the "trends" data for trajectory-based statements.
7. Use the "cross_metrics" and "anomalies" data to anchor analysis.
8. Write like a strategic advisor — dense, precise, evidence-backed, but warm and encouraging.

═══════════════════════════════════════════════════════════════
REQUIRED OUTPUT — EXACTLY 4 SECTIONS in valid JSON:
Every field is MANDATORY. Do NOT omit or leave any field empty/null.
═══════════════════════════════════════════════════════════════

{
  "performance_summary": {
    "title": "Performance Overview — [Month Year]",
    "narrative": "A 4-6 sentence written narrative summarising overall performance for this period. Cover the big picture: how did the studio perform relative to last month, the baseline, and its own trajectory? Identify 2-3 key patterns or behavioral shifts observed in the data (e.g., 'volume-driven growth pattern', 'improving retention cycle', 'seasonal acquisition surge'). This should read like an analyst's opening paragraph — confident, data-rich, and forward-looking. Always acknowledge the positives first.",
    "patterns": [
      {
        "pattern": "Short name for the pattern (e.g., 'Volume-Over-Price Growth Pattern')",
        "description": "2-3 sentences explaining what this pattern is, the evidence for it in the data, and what it implies going forward. Frame constructively."
      }
    ]
  },

  "key_insights": [
    {
      "title": "Short punchy headline (max 8 words)",
      "text": "3-4 sentences. Cross-reference 2+ metrics. Cite specific ₹ numbers. Explain the mechanism AND the opportunity. Back every claim with data.",
      "classification": "excellent|healthy|opportunity|watch",
      "data_evidence": "The specific numbers that support this insight, e.g., '₹25,80,029 gross (+18.3% MoM) driven by 349 transactions (+23.8%) while ATV compressed 4.4%'"
    }
  ],

  "highlights": [
    {
      "type": "achievement|dip",
      "metric": "The specific metric (e.g., 'Gross Revenue', 'Member Count', 'Transaction Volume')",
      "headline": "Short description (e.g., 'Record Transaction Volume')",
      "detail": "2-3 sentences explaining what happened, WHY it likely happened (cite possible causes), and what it means. For achievements, explain what's working and how to sustain it. For dips, explain likely causes and the specific fix. ALWAYS end on a constructive note.",
      "magnitude": "The specific number and % change (e.g., '+23.8% to 349 transactions')"
    }
  ],

  "recommendations": [
    {
      "title": "Clear, specific action title (e.g., 'Launch Premium Package Upsell at Check-in')",
      "description": "3-4 sentences. What EXACTLY to do, step by step. Be specific — name the metric to move, the lever to pull, the process to implement. Include the data that justifies this recommendation.",
      "expected_impact": "Quantified outcome (e.g., 'Recovering ATV from ₹7,393 to ₹8,000 adds ~₹2.1L/month in gross revenue')",
      "timeline": "This week / Next 2 weeks / By end of month / This quarter",
      "priority": "high|medium|low",
      "owner": "Specific role (e.g., Studio Manager, Head Coach, Sales Lead, Front Desk Team)"
    }
  ]
}

QUANTITIES:
- performance_summary.patterns: 2-3 patterns (MAXIMUM)
- key_insights: 4-5 insights (quality over quantity — each must earn its place)
- highlights: 3-4 highlights (mix of achievements AND dips, always with constructive framing)
- recommendations: 4-5 recommendations (specific, detailed, actionable)

CONCISENESS RULE:
- BE EXTREMELY CONCISE. Keep all descriptions to 2-3 short sentences maximum.
- Do not write long paragraphs. Get straight to the point.
- If you exceed the token limit, the JSON will truncate and fail.

CLASSIFICATION LABELS:
- Use "excellent" for metrics significantly above benchmark/baseline
- Use "healthy" for metrics tracking well
- Use "opportunity" (NOT "warning") for metrics below benchmark — frame as upside to capture
- Use "watch" (NOT "critical") for metrics needing attention — frame as areas to monitor with a clear fix`;
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
        {
          role: 'user',
          content: `Analyse the following data digest for ${month}. The "trends" object has multi-month trajectory data with acceleration signals. The "anomalies" array flags statistical deviations. The "cross_metrics" object has pre-computed cross-references. Use ALL of these to produce deep, context-aware, data-backed analysis.\n\n${JSON.stringify(digest)}`,
        },
      ],
      temperature: 0.5,
      presence_penalty: 0.5,
      frequency_penalty: 0.4,
      max_tokens: 4096, // Reduced to standard max_tokens for gpt-4o compatibility
    }),
  });

  if (!res.ok) {
    const errText = await res.text().catch(() => res.statusText);
    throw new Error(`OpenAI API error ${res.status}: ${errText}`);
  }

  const json = await res.json();
  const content = json.choices?.[0]?.message?.content;
  if (!content) throw new Error('OpenAI returned no content');
  const parsed = JSON.parse(content);

  // ── Sanitize performance_summary ──
  if (!parsed.performance_summary || typeof parsed.performance_summary !== 'object') {
    parsed.performance_summary = { title: 'Performance Overview', narrative: '', patterns: [] };
  }
  parsed.performance_summary.title = parsed.performance_summary.title || 'Performance Overview';
  parsed.performance_summary.narrative = parsed.performance_summary.narrative || '';
  if (Array.isArray(parsed.performance_summary.patterns)) {
    parsed.performance_summary.patterns = parsed.performance_summary.patterns
      .filter(p => p && p.pattern && p.description)
      .map(p => ({ pattern: p.pattern, description: p.description }));
  } else {
    parsed.performance_summary.patterns = [];
  }

  // ── Sanitize key_insights ──
  if (Array.isArray(parsed.key_insights)) {
    parsed.key_insights = parsed.key_insights
      .filter(ins => ins && ins.title && ins.text)
      .map(ins => ({
        title: ins.title || '—',
        text: ins.text || '—',
        classification: ins.classification || 'healthy',
        data_evidence: ins.data_evidence || '',
      }));
  } else {
    parsed.key_insights = [];
  }

  // ── Sanitize highlights ──
  if (Array.isArray(parsed.highlights)) {
    parsed.highlights = parsed.highlights
      .filter(h => h && h.headline && h.detail)
      .map(h => ({
        type: h.type || 'achievement',
        metric: h.metric || '—',
        headline: h.headline || '—',
        detail: h.detail || '—',
        magnitude: h.magnitude || '—',
      }));
  } else {
    parsed.highlights = [];
  }

  // ── Sanitize recommendations ──
  if (Array.isArray(parsed.recommendations)) {
    parsed.recommendations = parsed.recommendations
      .filter(r => r && r.title)
      .map(r => ({
        title: r.title || '—',
        description: r.description || '—',
        expected_impact: r.expected_impact || '—',
        timeline: r.timeline || '—',
        priority: r.priority || 'medium',
        owner: r.owner || '—',
      }));
  } else {
    parsed.recommendations = [];
  }

  // ── Backward compat: also populate legacy fields so old clients don't break ──
  if (!parsed.summary) {
    parsed.summary = parsed.performance_summary.narrative;
  }
  if (!parsed.insights) {
    parsed.insights = parsed.key_insights;
  }
  if (!parsed.actions) {
    parsed.actions = parsed.recommendations.map(r => ({
      action: r.title,
      rationale: r.description,
      impact: r.expected_impact,
      timeline: r.timeline,
      owner: r.owner,
      priority: r.priority,
    }));
  }

  return parsed;
}

module.exports = { generateInsights, SECTION_LABELS };

