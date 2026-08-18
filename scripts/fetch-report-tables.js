// One-off script: fetch live Google Sheets data, filter to Supreme HQ Bandra,
// compute 4 datasets, print JSON to stdout. Run with:
//   node -r dotenv/config /path/to/fetch-report-tables.js dotenv_config_path=/Users/jimmeeygondaa/Report\ Template/.env
'use strict';

const CFG = {
  CLIENT_ID: process.env.VITE_GOOGLE_CLIENT_ID,
  CLIENT_SECRET: process.env.VITE_GOOGLE_CLIENT_SECRET,
  REFRESH_TOKEN: process.env.VITE_GOOGLE_REFRESH_TOKEN,
  TOKEN_URL: process.env.VITE_GOOGLE_TOKEN_URL || 'https://oauth2.googleapis.com/token',
};
const SHEETS = {
  SALES: process.env.VITE_SALES_SPREADSHEET_ID,
  PAYROLL: process.env.VITE_PAYROLL_SPREADSHEET_ID,
  NEW_CLIENTS: process.env.VITE_PAYROLL_SPREADSHEET_ID, // ref repo uses PAYROLL id as fallback for NEW_CLIENTS too
  SESSIONS: process.env.VITE_SESSIONS_SPREADSHEET_ID,
};

const MONTHS = ['Jan 2026','Feb 2026','Mar 2026','Apr 2026','May 2026','Jun 2026','Jul 2026'];
const MONTH_KEYS = ['2026-01','2026-02','2026-03','2026-04','2026-05','2026-06','2026-07'];
const LOCATION_RE = /supreme|bandra/i;

async function getAccessToken() {
  const res = await fetch(CFG.TOKEN_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      client_id: CFG.CLIENT_ID,
      client_secret: CFG.CLIENT_SECRET,
      refresh_token: CFG.REFRESH_TOKEN,
      grant_type: 'refresh_token',
    }),
  });
  if (!res.ok) throw new Error('Token refresh failed: ' + res.status + ' ' + (await res.text()));
  const j = await res.json();
  return j.access_token;
}

async function fetchSheet(token, spreadsheetId, range) {
  const url = `https://sheets.googleapis.com/v4/spreadsheets/${spreadsheetId}/values/${encodeURIComponent(range)}?valueRenderOption=UNFORMATTED_VALUE&dateTimeRenderOption=FORMATTED_STRING`;
  const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  if (!res.ok) throw new Error(`Failed sheet fetch ${spreadsheetId}/${range}: ${res.status} ${await res.text()}`);
  const j = await res.json();
  return j.values || [];
}

function toNumber(v) {
  if (typeof v === 'number') return isNaN(v) ? 0 : v;
  if (!v) return 0;
  const cleaned = String(v).replace(/[^0-9.-]/g, '');
  const n = parseFloat(cleaned);
  return isNaN(n) ? 0 : n;
}

function normHeader(h) {
  return String(h || '').toLowerCase().replace(/&/g, 'and').replace(/[^a-z0-9]/g, '');
}

function rowsToObjects(values) {
  if (!values.length) return { headers: [], objs: [] };
  const headers = values[0].map((h) => String(h || '').trim());
  const normMap = new Map();
  headers.forEach((h, i) => normMap.set(normHeader(h), i));
  const get = (row, ...names) => {
    for (const n of names) {
      const idx = normMap.get(normHeader(n));
      if (typeof idx === 'number') return row[idx] ?? '';
    }
    return '';
  };
  const objs = values.slice(1)
    .filter((r) => r.some((c) => String(c ?? '').trim() !== ''))
    .map((row) => ({ row, get: (...names) => get(row, ...names) }));
  return { headers, objs };
}

function parseDateFlexible(v) {
  if (!v) return null;
  if (typeof v === 'number') {
    const d = new Date(Math.round((v - 25569) * 86400 * 1000));
    return isNaN(d.getTime()) ? null : d;
  }
  const s = String(v).trim();
  // dd/mm/yyyy or mm/dd/yyyy
  const m = s.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})/);
  if (m) {
    const a = Number(m[1]), b = Number(m[2]), y = Number(m[3]);
    // assume dd/mm/yyyy (common in these sheets, India locale)
    const day = a > 12 ? a : a;
    const month = a > 12 ? b : b;
    const d = new Date(y, month - 1, day);
    if (!isNaN(d.getTime())) return d;
  }
  const d2 = new Date(s);
  return isNaN(d2.getTime()) ? null : d2;
}
function monthKey(d) {
  if (!d) return null;
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}

async function main() {
  const token = await getAccessToken();
  console.error('Got access token, length=', token ? token.length : 0);

  const [salesVals, newClientVals, payrollVals, sessionsVals] = await Promise.all([
    fetchSheet(token, SHEETS.SALES, 'Sales'),
    fetchSheet(token, SHEETS.NEW_CLIENTS, 'New'),
    fetchSheet(token, SHEETS.PAYROLL, 'Payroll'),
    fetchSheet(token, SHEETS.SESSIONS, 'Sessions'),
  ]);
  console.error('Row counts: sales', salesVals.length, 'new', newClientVals.length, 'payroll', payrollVals.length, 'sessions', sessionsVals.length);

  // ---- Inspect location columns ----
  const { objs: newObjs } = rowsToObjects(newClientVals);
  const locSet = new Set();
  newObjs.forEach((o) => {
    const loc = o.get('First Visit Location', 'Location', 'Home Location', 'Studio') || '';
    if (loc) locSet.add(String(loc));
  });
  console.error('Unique New-client locations sample:', [...locSet].slice(0, 20));

  const payrollLocSet = new Set();
  payrollVals.slice(1).forEach((row) => { if (row[3]) payrollLocSet.add(String(row[3])); });
  console.error('Unique Payroll locations sample:', [...payrollLocSet].slice(0, 20));

  const { objs: sessObjs, headers: sessHeaders } = rowsToObjects(sessionsVals);
  console.error('Session headers:', sessHeaders);
  const sessLocSet = new Set();
  sessObjs.forEach((o) => {
    const loc = o.get('Location', 'Studio', 'Home Location') || (o.row[11] ?? '');
    if (loc) sessLocSet.add(String(loc));
  });
  console.error('Unique Session locations sample:', [...sessLocSet].slice(0, 20));

  // ---- Filter to Bandra ----
  const newClientsBandra = newObjs.filter((o) => LOCATION_RE.test(String(o.get('First Visit Location', 'Location', 'Home Location', 'Studio') || '')));
  const payrollBandra = payrollVals.slice(1).filter((row) => LOCATION_RE.test(String(row[3] || '')));
  const sessionsBandra = sessObjs.filter((o) => LOCATION_RE.test(String(o.get('Location', 'Studio', 'Home Location') || (o.row[11] ?? ''))));

  console.error('Filtered counts -> newClients:', newClientsBandra.length, 'payroll:', payrollBandra.length, 'sessions:', sessionsBandra.length);

  // Scope everything to the report window (Jan 2026 - Jul 2026), matching window.MOM_DATA months[] in the HTML.
  const inReportWindow = (o) => {
    const fv = parseDateFlexible(o.get('First Visit Date', 'First Visit', 'Trial Date', 'Visit Date'));
    const mk = monthKey(fv);
    return mk && MONTH_KEYS.includes(mk);
  };
  const newClientsWindow = newClientsBandra.filter(inReportWindow);

  const monthAbbrevYear = (my) => {
    // Normalize "Jun-2024" / "Jun 2024" / "2026-06" style strings to MONTH_KEYS style "2026-06"
    const s = String(my || '').trim();
    let m = s.match(/^(\d{4})-(\d{1,2})$/);
    if (m) return `${m[1]}-${String(m[2]).padStart(2, '0')}`;
    m = s.match(/^([A-Za-z]{3,})[\s-]+(\d{4})$/);
    if (m) {
      const names = ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'];
      const idx = names.indexOf(m[1].slice(0,3).toLowerCase());
      if (idx >= 0) return `${m[2]}-${String(idx + 1).padStart(2, '0')}`;
    }
    return null;
  };
  const payrollWindow = payrollBandra.filter((row) => {
    const mk = monthAbbrevYear(row[24]);
    return mk && MONTH_KEYS.includes(mk);
  });
  const sessionsWindow = sessionsBandra.filter((o) => {
    const d = parseDateFlexible(o.get('Date') || o.row[12]);
    const mk = monthKey(d);
    return mk && MONTH_KEYS.includes(mk);
  });
  console.error('Windowed (Jan-Jul 2026) counts -> newClients:', newClientsWindow.length, 'payroll:', payrollWindow.length, 'sessions:', sessionsWindow.length);

  // ============ Dataset 1: New Client Membership Purchases (grouped) ============
  function isConverted(o) {
    const status = String(o.get('Conversion Status', 'Conversion') || '').toLowerCase();
    if (status) return status.includes('convert') && !status.includes('not');
    return toNumber(o.get('Purchase Count Post Trial', 'Post Trial Purchase Count', 'Purchase Count')) > 0;
  }

  const converted = newClientsWindow.filter(isConverted);
  const grouped = {};
  converted.forEach((o) => {
    const key = String(o.get('First Purchase Post Trial', 'First Purchase Made', 'First Purchase', 'Memberships Bought Post Trial') || 'Unknown').trim() || 'Unknown';
    if (!grouped[key]) grouped[key] = { members: new Set(), totalLtv: 0, totalUnits: 0, totalPurchaseCount: 0, totalConvSpan: 0, convSpanCount: 0, totalVisits: 0, visitCount: 0 };
    const g = grouped[key];
    const memberId = String(o.get('Member Id', 'Member ID', 'Client ID', 'Customer ID') || o.get('Email', 'Email Address') || Math.random());
    g.members.add(memberId);
    g.totalLtv += toNumber(o.get('Ltv', 'LTV', 'Lifetime Value'));
    g.totalUnits += 1;
    g.totalPurchaseCount += toNumber(o.get('Purchase Count Post Trial', 'Post Trial Purchase Count', 'Purchase Count')) || 1;
    const firstVisit = parseDateFlexible(o.get('First Visit Date', 'First Visit', 'Trial Date', 'Visit Date'));
    const firstPurchase = parseDateFlexible(o.get('First Purchase Date', 'Purchase Date'));
    if (firstVisit && firstPurchase) {
      const days = Math.max(0, Math.round((firstPurchase - firstVisit) / 86400000));
      g.totalConvSpan += days; g.convSpanCount += 1;
    }
    const visits = toNumber(o.get('Visits Post Trial', 'Post Trial Visits'));
    if (visits > 0) { g.totalVisits += visits; g.visitCount += 1; }
  });

  const newClientPurchases = Object.entries(grouped).map(([name, g]) => {
    const uniqueMembers = g.members.size;
    const unitsSold = g.totalUnits;
    const totalLtv = Math.round(g.totalLtv);
    const atv = unitsSold > 0 ? totalLtv / unitsSold : 0;
    const auv = uniqueMembers > 0 ? totalLtv / uniqueMembers : 0;
    const purchaseFreq = uniqueMembers > 0 ? g.totalPurchaseCount / uniqueMembers : 0;
    const avgConvDays = g.convSpanCount > 0 ? g.totalConvSpan / g.convSpanCount : null;
    const avgVisits = g.visitCount > 0 ? g.totalVisits / g.visitCount : 0;
    return { name, uniqueMembers, unitsSold, totalLtv, atv: Math.round(atv), auv: Math.round(auv), purchaseFreq: +purchaseFreq.toFixed(1), avgConvDays: avgConvDays === null ? null : Math.round(avgConvDays), avgVisits: +avgVisits.toFixed(1) };
  }).sort((a, b) => b.uniqueMembers - a.uniqueMembers).slice(0, 12);

  // ============ Dataset 2: Month-on-Month by Client Type (matrix) ============
  const clientTypesSet = new Set();
  newClientsWindow.forEach((o) => clientTypesSet.add(String(o.get('Is New', 'Client Type', 'Member Type', 'New/Repeat') || 'Unknown') || 'Unknown'));
  let clientTypes = [...clientTypesSet].filter(Boolean);
  if (!clientTypes.length) clientTypes = ['Unknown'];
  clientTypes.sort((a, b) => {
    const an = a.toLowerCase().includes('new'), bn = b.toLowerCase().includes('new');
    if (an && !bn) return -1; if (!an && bn) return 1; return a.localeCompare(b);
  });

  const momByClientType = clientTypes.map((ct) => {
    const values = MONTH_KEYS.map((mk) => {
      const clientsInMonth = newClientsWindow.filter((o) => {
        const type = String(o.get('Is New', 'Client Type', 'Member Type', 'New/Repeat') || 'Unknown') || 'Unknown';
        if (type !== ct) return false;
        const fv = parseDateFlexible(o.get('First Visit Date', 'First Visit', 'Trial Date', 'Visit Date'));
        return fv && monthKey(fv) === mk;
      });
      return clientsInMonth.length;
    });
    return { label: ct, fmt: 'int', agg: 'sum', values };
  });

  // ============ Dataset 3: Teacher Scorecard (Payroll, latest month / totals) ============
  // Payroll columns per usePayrollData.ts (0-indexed):
  // 0 teacherId, 1 teacherName, 2 teacherEmail, 3 location,
  // 19 totalSessions, 20 totalEmptySessions, 21 totalNonEmptySessions, 22 totalCustomers, 23 totalPaid,
  // 24 monthYear, 26 converted, 27 conversionRate, 28 retained, 29 retentionRate, 30 newMembers
  const teacherAgg = {};
  payrollWindow.forEach((row) => {
    const name = String(row[1] || '').trim();
    if (!name) return;
    const monthYear = String(row[24] || '').trim();
    if (!teacherAgg[name]) teacherAgg[name] = { sessions: 0, empty: 0, nonEmpty: 0, customers: 0, paid: 0, converted: 0, retained: 0, newMembers: 0, lateCancels: 0, monthsSeen: new Set() };
    const t = teacherAgg[name];
    t.sessions += toNumber(row[19]);
    t.empty += toNumber(row[20]);
    t.nonEmpty += toNumber(row[21]);
    t.customers += toNumber(row[22]);
    t.paid += toNumber(row[23]);
    t.converted += toNumber(row[26]);
    t.retained += toNumber(row[28]);
    t.newMembers += toNumber(row[30]);
    if (monthYear) t.monthsSeen.add(monthYear);
  });

  // Real fill rate (checked-in / capacity) + late cancels from sessions data
  sessionsWindow.forEach((o) => {
    const name = String(o.get('Trainer Name') || o.row[3] || '').trim();
    if (!name || !teacherAgg[name]) return;
    const t = teacherAgg[name];
    t.lateCancels += toNumber(o.get('Late Cancelled Count') || o.row[8]);
    t.capacity = (t.capacity || 0) + toNumber(o.get('Capacity') || o.row[6]);
    t.checkedIn = (t.checkedIn || 0) + toNumber(o.get('CheckedIn') || o.row[7]);
  });

  // Composite score (0-100), mirrors reference StudioPulse formula:
  // 40% avg class size (normalised, 30 = full) + 30% fill rate + 20% conversion% + 10% retention%
  const teacherScorecard = Object.entries(teacherAgg)
    .filter(([, t]) => t.sessions > 0)
    .map(([name, t]) => {
      const classAvg = t.nonEmpty > 0 ? t.customers / t.nonEmpty : 0;
      const fillRate = t.capacity > 0 ? (t.checkedIn / t.capacity) * 100 : 0;
      const convPct = t.newMembers > 0 ? (t.converted / t.newMembers) * 100 : 0;
      const retPct = t.converted > 0 ? (t.retained / t.converted) * 100 : 0;
      const avgScore = Math.min((classAvg / 30) * 100, 100);
      const score = avgScore * 0.4 + fillRate * 0.3 + convPct * 0.2 + retPct * 0.1;
      return {
        instructor: name, cls: t.sessions, empty: t.empty, active: t.nonEmpty,
        fillRate: +fillRate.toFixed(1), newMembers: t.newMembers, converted: t.converted, retained: t.retained,
        convPct: +convPct.toFixed(1), late: t.lateCancels, pay: Math.round(t.paid), score: Math.round(score),
      };
    })
    .sort((a, b) => b.score - a.score)
    .slice(0, 15);

  // ============ Dataset 4: Month-on-Month Trainer table ============
  const trainerMonthAgg = {};
  payrollWindow.forEach((row) => {
    const name = String(row[1] || '').trim();
    const monthYear = String(row[24] || '').trim();
    if (!name || !monthYear) return;
    // normalize monthYear -> "Mon YYYY" if possible, else keep raw
    if (!trainerMonthAgg[name]) trainerMonthAgg[name] = {};
    if (!trainerMonthAgg[name][monthYear]) trainerMonthAgg[name][monthYear] = { sessions: 0, paid: 0, customers: 0, nonEmpty: 0, converted: 0, newMembers: 0, retained: 0 };
    const m = trainerMonthAgg[name][monthYear];
    m.sessions += toNumber(row[19]);
    m.paid += toNumber(row[23]);
    m.customers += toNumber(row[22]);
    m.nonEmpty += toNumber(row[21]);
    m.converted += toNumber(row[26]);
    m.newMembers += toNumber(row[30]);
    m.retained += toNumber(row[28]);
  });
  const trainerNames = Object.keys(trainerMonthAgg).filter((n) => {
    const total = Object.values(trainerMonthAgg[n]).reduce((s, m) => s + m.sessions, 0);
    return total > 0;
  }).sort((a, b) => {
    const ta = Object.values(trainerMonthAgg[a]).reduce((s, m) => s + m.sessions, 0);
    const tb = Object.values(trainerMonthAgg[b]).reduce((s, m) => s + m.sessions, 0);
    return tb - ta;
  }).slice(0, 12);

  // Discover distinct monthYear raw strings so we can map to canonical months if needed
  const allMonthYearStrings = new Set();
  payrollBandra.forEach((row) => { if (row[24]) allMonthYearStrings.add(String(row[24]).trim()); });

  const momTrainer = trainerNames.map((name) => {
    const values = MONTH_KEYS.map((mk, i) => {
      // try to match by "Mon YYYY" strings appearing in allMonthYearStrings against MONTHS[i]
      const wanted = MONTHS[i];
      const m = trainerMonthAgg[name][wanted];
      if (m) return m.sessions;
      // fallback: try matching any monthYear string containing month short name + year
      const [monShort, yr] = wanted.split(' ');
      const altKey = Object.keys(trainerMonthAgg[name]).find((k) => k.toLowerCase().includes(monShort.toLowerCase()) && k.includes(yr));
      return altKey ? trainerMonthAgg[name][altKey].sessions : 0;
    });
    return { label: name, fmt: 'int', agg: 'sum', values };
  });

  const output = {
    _debug: {
      newClientLocations: [...locSet].slice(0, 20),
      payrollLocations: [...payrollLocSet].slice(0, 20),
      sessionLocations: [...sessLocSet].slice(0, 20),
      payrollMonthYearSamples: [...allMonthYearStrings].slice(0, 20),
      counts: { newClientsBandra: newClientsBandra.length, payrollBandra: payrollBandra.length, sessionsBandra: sessionsBandra.length },
    },
    newClientPurchases,
    momByClientType,
    teacherScorecard,
    momTrainer,
  };

  console.log(JSON.stringify(output, null, 2));
}

main().catch((e) => { console.error('FATAL', e); process.exit(1); });
