#!/usr/bin/env python3
"""
Parameterized Performance Report Generator
Generates 4 separate HTML reports: KW-June, KW-July, Supreme-June, Supreme-July
Based on the May 2026 reference report structure with 7 sections.
"""
import calendar
import json
import os
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

ANALYSIS_JSON = sys.argv[1] if len(sys.argv) > 1 else 'analysis_v2.json'
LOC_KEY_ARG = sys.argv[2] if len(sys.argv) > 2 else None
MONTH_KEY_ARG = sys.argv[3] if len(sys.argv) > 3 else None
OUTPUT_HTML = sys.argv[4] if len(sys.argv) > 4 else None
AI_CONTEXT_JSON = sys.argv[5] if len(sys.argv) > 5 else None

# `--emit-panes <file>` renders the report to nowhere and writes out what each
# insight pane is about, so the caller can have those panes written by a model
# and feed the answers back in as the AI context on a second pass.
EMIT_PANES = None
if '--emit-panes' in sys.argv:
    i = sys.argv.index('--emit-panes')
    EMIT_PANES = sys.argv[i + 1] if len(sys.argv) > i + 1 else 'pane_requests.json'
    del sys.argv[i:i + 2]

import sections_v2
import charts_v2
import report_shell
if AI_CONTEXT_JSON and os.path.exists(AI_CONTEXT_JSON):
    with open(AI_CONTEXT_JSON, 'r') as f:
        sections_v2.AI_CONTEXT = json.load(f)
else:
    sections_v2.AI_CONTEXT = {}


# The stylesheet lives with the rest of the document shell.
CSS = report_shell.CSS

# Load analysis data if file exists (safe for module import)
DATA = {}
if os.path.exists(ANALYSIS_JSON):
    try:
        with open(ANALYSIS_JSON, 'r') as f:
            DATA = json.load(f)
    except Exception:
        pass

def build_location_meta(full_name):
    """Derive short_name/brand_mark from a full location name, e.g.
    'Kwality House, Kemps Corner' -> short 'Kwality House', mark 'KH';
    'Supreme HQ, Bandra' -> short 'Supreme HQ', mark 'SHQ'."""
    short_name = full_name.split(',')[0].strip()
    mark = ''
    for word in short_name.split(' '):
        if not word:
            continue
        mark += word if (word.isupper() and len(word) > 1) else word[0].upper()
    return {
        'full_name': full_name,
        'short_name': short_name,
        'brand_mark': mark,
        # narration files are named by studio; fall back to a slug of the short name
        'audio_prefix': short_name.lower().replace(' ', '-'),
    }


def build_month_meta(month_key):
    """Derive display metadata for a 'YYYY-MM' key via calendar arithmetic."""
    year, mon = (int(x) for x in month_key.split('-'))
    month_name = calendar.month_name[mon]
    month_short = calendar.month_abbr[mon]
    days_in_month = calendar.monthrange(year, mon)[1]

    # M-1 (1 month prior)
    p1_year, p1_mon = (year, mon - 1) if mon > 1 else (year - 1, 12)
    prev1_month_key = f'{p1_year}-{p1_mon:02d}'
    prev1_month_name = f"{calendar.month_abbr[p1_mon]} {p1_year}"

    # M-2 (2 months prior)
    p2_year, p2_mon = (year, mon - 2) if mon > 2 else (year - 1, 12 + mon - 2)
    prev2_month_key = f'{p2_year}-{p2_mon:02d}'
    prev2_month_name = f"{calendar.month_abbr[p2_mon]} {p2_year}"

    next_year, next_mon = (year, mon + 1) if mon < 12 else (year + 1, 1)
    next_month_name = calendar.month_name[next_mon]
    next_month_short = calendar.month_abbr[next_mon]

    yoy_month_key = f'{year - 1}-{mon:02d}'
    yoy_month_name = f'{month_short} {year - 1}'

    return {
        'month_name': month_name,
        'month_short': month_short,
        'year': str(year),
        'last_day': days_in_month,
        'date_range': f'01 {month_name} {year} &mdash; {days_in_month} {month_name} {year}',
        'period_short': f'01 &mdash; {days_in_month} {month_short} {year}',
        'prev_month': prev1_month_key,
        'prev_month_name': prev1_month_name,
        'prev2_month': prev2_month_key,
        'prev2_month_name': prev2_month_name,
        'prev_year': str(p1_year),
        'yoy_month': yoy_month_key,
        'yoy_month_name': yoy_month_name,
        'next_month_name': next_month_name,
        'next_month_short': next_month_short,
        'next_year': str(next_year),
    }

def _init_meta():
    global LOCATIONS, MONTHS
    LOCATIONS = {lk: build_location_meta(full_name)
                 for lk, full_name in DATA.get('meta', {}).get('locations', {}).items()}
    MONTHS = {mk: build_month_meta(mk) for mk in DATA.get('meta', {}).get('months', [])}

LOCATIONS = {}
MONTHS = {}
_init_meta()

def run_generate(analysis_path, loc_keys, month_keys, output_path=None):
    global DATA, LOCATIONS, MONTHS
    with open(analysis_path, 'r') as f:
        DATA = json.load(f)
    _init_meta()
    if isinstance(loc_keys, str):
        loc_keys = [k.strip() for k in loc_keys.split(',') if k.strip()]
    if isinstance(month_keys, str):
        month_keys = [k.strip() for k in month_keys.split(',') if k.strip()]
    html = generate_report(loc_keys, month_keys)
    if output_path:
        with open(output_path, 'w') as f:
            f.write(html)
    return html

# ─── Helpers ──────────────────────────────────────────────────────────────────

def lakh(v):
    """Format a rupee value in lakhs, e.g. 2076834 -> '₹20.77L'"""
    return f"&#8377;{v/1e5:.2f}L"

def lakh_raw(v):
    return f"{v/1e5:.2f}L"

def rupee(v):
    """Format as ₹X,XXX"""
    return f"&#8377;{v:,.0f}"

def pct(v, decimals=1):
    return f"{v:.{decimals}f}%"

def fmt_int(v):
    return f"{int(round(v)):,}"

def pct_change(old, new):
    """Percentage change, returns string like '+18.2%' or '-5.3%'"""
    if old == 0:
        return "n/a"
    change = ((new - old) / old) * 100
    sign = "+" if change >= 0 else ""
    return f"{sign}{change:.1f}%"

def pp_change(old, new):
    """Percentage point change, returns string like '+4.0pp' or '-2.3pp'"""
    diff = new - old
    sign = "+" if diff >= 0 else ""
    return f"{sign}{diff:.1f}pp"

def badge(change_str, higher_is_better=True):
    """Generate a badge class based on a change string"""
    if "n/a" in change_str:
        return "neutral"
    val = float(change_str.replace("+","").replace("%","").replace("pp",""))
    if abs(val) < 0.05:
        return "neutral"
    is_good = (val > 0) == higher_is_better
    return "good" if is_good else "bad"

def badge_from_pp(change_str, higher_is_better=True):
    """Generate badge for pp change"""
    if "n/a" in change_str:
        return "neutral"
    val = float(change_str.replace("+","").replace("pp",""))
    if abs(val) < 0.05:
        return "neutral"
    is_good = (val > 0) == higher_is_better
    return "good" if is_good else "bad"

def mult(v, decimals=1):
    """Format as multiplier like '2.5×'"""
    return f"{v:.{decimals}f}&times;"

# ─── Location & Month Configuration ──────────────────────────────────────────
# Locations and months are derived from analysis_v2.json's 'meta' block
# (itself detected from the uploaded CSVs by analyze_v2.py), not hardcoded.

def build_location_meta(full_name):
    """Derive short_name/brand_mark from a full location name, e.g.
    'Kwality House, Kemps Corner' -> short 'Kwality House', mark 'KH';
    'Supreme HQ, Bandra' -> short 'Supreme HQ', mark 'SHQ'."""
    short_name = full_name.split(',')[0].strip()
    mark = ''
    for word in short_name.split(' '):
        if not word:
            continue
        mark += word if (word.isupper() and len(word) > 1) else word[0].upper()
    return {
        'full_name': full_name,
        'short_name': short_name,
        'brand_mark': mark,
        # narration files are named by studio; fall back to a slug of the short name
        'audio_prefix': short_name.lower().replace(' ', '-'),
    }


def build_month_meta(month_key):
    """Derive display metadata for a 'YYYY-MM' key via calendar arithmetic."""
    year, mon = (int(x) for x in month_key.split('-'))
    month_name = calendar.month_name[mon]
    month_short = calendar.month_abbr[mon]
    days_in_month = calendar.monthrange(year, mon)[1]

    # M-1 (1 month prior)
    p1_year, p1_mon = (year, mon - 1) if mon > 1 else (year - 1, 12)
    prev1_month_key = f'{p1_year}-{p1_mon:02d}'
    prev1_month_name = f"{calendar.month_abbr[p1_mon]} {p1_year}"

    # M-2 (2 months prior)
    p2_year, p2_mon = (year, mon - 2) if mon > 2 else (year - 1, 12 + mon - 2)
    prev2_month_key = f'{p2_year}-{p2_mon:02d}'
    prev2_month_name = f"{calendar.month_abbr[p2_mon]} {p2_year}"

    next_year, next_mon = (year, mon + 1) if mon < 12 else (year + 1, 1)
    next_month_name = calendar.month_name[next_mon]
    next_month_short = calendar.month_abbr[next_mon]

    yoy_month_key = f'{year - 1}-{mon:02d}'
    yoy_month_name = f'{month_short} {year - 1}'

    return {
        'month_name': month_name,
        'month_short': month_short,
        'year': str(year),
        'last_day': days_in_month,
        'date_range': f'01 {month_name} {year} &mdash; {days_in_month} {month_name} {year}',
        'period_short': f'01 &mdash; {days_in_month} {month_short} {year}',
        'prev_month': prev1_month_key,
        'prev_month_name': prev1_month_name,
        'prev2_month': prev2_month_key,
        'prev2_month_name': prev2_month_name,
        'prev_year': str(p1_year),
        'yoy_month': yoy_month_key,
        'yoy_month_name': yoy_month_name,
        'next_month_name': next_month_name,
        'next_month_short': next_month_short,
        'next_year': str(next_year),
    }


LOCATIONS = {lk: build_location_meta(full_name)
             for lk, full_name in DATA.get('meta', {}).get('locations', {}).items()}

MONTHS = {mk: build_month_meta(mk) for mk in DATA.get('meta', {}).get('months', [])}

# ─── Data Access Helpers ──────────────────────────────────────────────────────

def get_sales(loc, month):
    defaults = {'net': 0, 'gross': 0, 'disc': 0, 'sales': 0, 'members': 0, 'atv': 0, 'disc_eff': 0}
    return {**defaults, **(DATA.get('sales', {}).get(loc, {}).get(month, {}) or {})}

def get_sessions(loc, month):
    defaults = {'sessions': 0, 'visits': 0, 'capacity': 0, 'fill': 0, 'revenue': 0, 'avg_visits': 0}
    return {**defaults, **(DATA.get('sessions', {}).get(loc, {}).get(month, {}) or {})}

def get_leads(loc, month):
    defaults = {'total': 0, 'converted': 0, 'rate': 0}
    return {**defaults, **(DATA.get('leads', {}).get(loc, {}).get(month, {}) or {})}

def get_leads_source(loc, month):
    return DATA.get('leads_by_source', {}).get(loc, {}).get(month, {})

def get_new(loc, month):
    """New-client figures, with the two derived ones filled in.

    The upload carries only `trials` and `retained`. Conversion is derived, and
    deriving it here rather than in the report context means the month-on-month
    series and the hero sparkline get real numbers too — they previously read
    the missing `rate` key and charted a flat line of zeros.
    """
    defaults = {'trials': 0, 'retained': 0}
    row = {**defaults, **(DATA.get('new', {}).get(loc, {}).get(month, {}) or {})}
    row.setdefault('converted', row['retained'])
    trials = row.get('trials') or 0
    row.setdefault('rate', (row['converted'] / trials * 100) if trials else 0)
    return row

def get_new_type(loc, month):
    return DATA.get('new_by_type', {}).get(loc, {}).get(month, {})

def get_lapsed(loc, month):
    defaults = {'total': 0, 'renewed': 0, 'lapsed': 0, 'frozen': 0, 'churn': 0, 'renewal_rate': 0}
    return {**defaults, **(DATA.get('lapsed', {}).get(loc, {}).get(month, {}) or {})}

def get_lapsed_product(loc, month):
    return DATA.get('lapsed_by_product', {}).get(loc, {}).get(month, {})

def get_lapsed_cumulative(loc):
    return DATA.get('lapsed_cumulative', {}).get(loc, {})

def get_checkins(loc, month):
    defaults = {'total': 0, 'late_cancel': 0, 'heavy_cancelers': 0, 'lc_member_count': 0}
    return {**defaults, **(DATA.get('checkins', {}).get(loc, {}).get(month, {}) or {})}

def get_active(loc):
    return DATA.get('active', {}).get(loc, {})

def get_baseline(loc):
    return DATA.get('baseline', {}).get(loc, {})

def get_heatmap(loc, month):
    return DATA.get('heatmap', {}).get(loc, {}).get(month, {})

def get_sessions_by_class(loc, month):
    return DATA.get('sessions_by_class', {}).get(loc, {}).get(month, {})

def get_sessions_by_slot(loc, month, with_trainer=False):
    key = 'sessions_by_slot_trainer' if with_trainer else 'sessions_by_slot'
    return DATA.get(key, {}).get(loc, {}).get(month, {})

def get_lapsed_members(loc, month):
    return DATA.get('lapsed_members', {}).get(loc, {}).get(month, []) or []

def get_sessions_by_trainer(loc, month):
    return DATA.get('sessions_by_trainer', {}).get(loc, {}).get(month, {})

def get_sessions_by_format(loc, month):
    return DATA.get('sessions_by_format', {}).get(loc, {}).get(month, {})

def get_sessions_by_trainer_format(loc, month):
    return DATA.get('sessions_by_trainer_format', {}).get(loc, {}).get(month, {})

def get_sales_breakdowns(loc, month):
    return DATA.get('sales_breakdowns', {}).get(loc, {}).get(month, {})


def compute_year_avg(loc_key, month_key):
    """Compute metrics average across all available months in the current year excluding month_key."""
    year_str = month_key.split('-')[0]
    all_months = list(DATA.get('meta', {}).get('months', []))
    other_months = [m for m in all_months if m.startswith(year_str + '-') and m != month_key]

    if not other_months:
        return {
            'sales': get_sales(loc_key, '__missing__'),
            'sessions': get_sessions(loc_key, '__missing__'),
            'leads': get_leads(loc_key, '__missing__'),
            'new': get_new(loc_key, '__missing__'),
            'lapsed': get_lapsed(loc_key, '__missing__'),
            'checkins': get_checkins(loc_key, '__missing__'),
            'months_count': 0
        }

    n = len(other_months)

    net_sum = sum(get_sales(loc_key, m).get('net', 0) for m in other_months)
    gross_sum = sum(get_sales(loc_key, m).get('gross', 0) for m in other_months)
    disc_sum = sum(get_sales(loc_key, m).get('disc', 0) for m in other_months)
    sales_cnt_sum = sum(get_sales(loc_key, m).get('sales', 0) for m in other_months)
    members_sum = sum(get_sales(loc_key, m).get('members', 0) for m in other_months)

    avg_sales = {
        'net': net_sum / n,
        'gross': gross_sum / n,
        'disc': disc_sum / n,
        'sales': sales_cnt_sum / n,
        'members': members_sum / n,
        'atv': (net_sum / sales_cnt_sum) if sales_cnt_sum > 0 else 0,
        'disc_eff': (net_sum / disc_sum) if disc_sum > 0 else 0,
    }

    sess_cnt_sum = sum(get_sessions(loc_key, m).get('sessions', 0) for m in other_months)
    visits_sum = sum(get_sessions(loc_key, m).get('visits', 0) for m in other_months)
    cap_sum = sum(get_sessions(loc_key, m).get('capacity', 0) for m in other_months)
    rev_sum = sum(get_sessions(loc_key, m).get('revenue', 0) for m in other_months)

    avg_sessions = {
        'sessions': sess_cnt_sum / n,
        'visits': visits_sum / n,
        'capacity': cap_sum / n,
        'fill': (visits_sum / cap_sum * 100) if cap_sum > 0 else 0,
        'revenue': rev_sum / n,
    }

    leads_tot_sum = sum(get_leads(loc_key, m).get('total', 0) for m in other_months)
    avg_leads = {
        'total': leads_tot_sum / n,
    }

    trials_sum = sum(get_new(loc_key, m).get('trials', 0) for m in other_months)
    conv_sum = sum(get_new(loc_key, m).get('converted', 0) for m in other_months)
    ret_sum = sum(get_new(loc_key, m).get('retained', 0) for m in other_months)

    avg_new = {
        'trials': trials_sum / n,
        'converted': conv_sum / n,
        'retained': ret_sum / n,
        'rate': (conv_sum / trials_sum * 100) if trials_sum > 0 else 0,
    }

    lapsed_tot_sum = sum(get_lapsed(loc_key, m).get('total', 0) for m in other_months)
    renewed_sum = sum(get_lapsed(loc_key, m).get('renewed', 0) for m in other_months)
    lapsed_cnt_sum = sum(get_lapsed(loc_key, m).get('lapsed', 0) for m in other_months)
    frozen_sum = sum(get_lapsed(loc_key, m).get('frozen', 0) for m in other_months)

    avg_lapsed = {
        'total': lapsed_tot_sum / n,
        'renewed': renewed_sum / n,
        'lapsed': lapsed_cnt_sum / n,
        'frozen': frozen_sum / n,
        'churn': (lapsed_cnt_sum / lapsed_tot_sum * 100) if lapsed_tot_sum > 0 else 0,
        'renewal_rate': (renewed_sum / lapsed_tot_sum * 100) if lapsed_tot_sum > 0 else 0,
    }

    lc_sum = sum(get_checkins(loc_key, m).get('late_cancel', 0) for m in other_months)
    chk_tot_sum = sum(get_checkins(loc_key, m).get('total', 0) for m in other_months)

    avg_checkins = {
        'total': chk_tot_sum / n,
        'late_cancel': lc_sum / n,
    }

    return {
        'sales': avg_sales,
        'sessions': avg_sessions,
        'leads': avg_leads,
        'new': avg_new,
        'lapsed': avg_lapsed,
        'checkins': avg_checkins,
        'months_count': n,
    }


# ─── Report Generation ────────────────────────────────────────────────────────

def build_ctx_for(loc_key, month_key, id_suffix=''):
    """Build the full context dict for one location x month combination."""
    loc = LOCATIONS[loc_key]
    mo = MONTHS[month_key]

    sales = get_sales(loc_key, month_key)
    sessions = get_sessions(loc_key, month_key)
    leads = get_leads(loc_key, month_key)
    new = get_new(loc_key, month_key)
    lapsed = get_lapsed(loc_key, month_key)
    checkins = get_checkins(loc_key, month_key)
    active = get_active(loc_key)

    # M-1 (1 month prior)
    prev_sales = get_sales(loc_key, mo['prev_month'])
    prev_sessions = get_sessions(loc_key, mo['prev_month'])
    prev_leads = get_leads(loc_key, mo['prev_month'])
    prev_new = get_new(loc_key, mo['prev_month'])
    prev_lapsed = get_lapsed(loc_key, mo['prev_month'])
    prev_checkins = get_checkins(loc_key, mo['prev_month'])

    # M-2 (2 months prior)
    prev2_sales = get_sales(loc_key, mo['prev2_month'])
    prev2_sessions = get_sessions(loc_key, mo['prev2_month'])
    prev2_leads = get_leads(loc_key, mo['prev2_month'])
    prev2_new = get_new(loc_key, mo['prev2_month'])
    prev2_lapsed = get_lapsed(loc_key, mo['prev2_month'])
    prev2_checkins = get_checkins(loc_key, mo['prev2_month'])

    # Current year avg (excl. selected month)
    year_avg = compute_year_avg(loc_key, month_key)

    # YoY (Same month last year)
    yoy_sales = get_sales(loc_key, mo['yoy_month'])
    yoy_sessions = get_sessions(loc_key, mo['yoy_month'])
    yoy_leads = get_leads(loc_key, mo['yoy_month'])
    yoy_new = get_new(loc_key, mo['yoy_month'])
    yoy_lapsed = get_lapsed(loc_key, mo['yoy_month'])
    yoy_checkins = get_checkins(loc_key, mo['yoy_month'])

    ctx = build_context(
        loc_key, month_key, loc, mo, sales, sessions, leads, new, lapsed, checkins, active,
        prev_sales, prev_sessions, prev_leads, prev_new, prev_lapsed, prev_checkins,
        prev2_sales, prev2_sessions, prev2_leads, prev2_new, prev2_lapsed, prev2_checkins,
        year_avg,
        yoy_sales, yoy_sessions, yoy_leads, yoy_new, yoy_lapsed, yoy_checkins
    )
    ctx['id_suffix'] = id_suffix
    return ctx


def generate_report(loc_keys, month_keys):
    """Generate a report for the cartesian product of loc_keys x month_keys."""
    if isinstance(loc_keys, str):
        loc_keys = [loc_keys]
    if isinstance(month_keys, str):
        month_keys = [month_keys]

    combos = [(lk, mk) for lk in loc_keys for mk in month_keys]

    if len(combos) == 1:
        ctx = build_ctx_for(combos[0][0], combos[0][1])
        return build_html(ctx)

    ctx_list = [build_ctx_for(lk, mk, id_suffix=f'-{i}') for i, (lk, mk) in enumerate(combos)]
    return build_html_multi(ctx_list)


def build_baseline_label():
    return 'Baseline'


def build_context(loc_key, month_key, loc, mo, sales, sessions, leads, new, lapsed, checkins, active,
                  prev_sales, prev_sessions, prev_leads, prev_new, prev_lapsed, prev_checkins,
                  prev2_sales, prev2_sessions, prev2_leads, prev2_new, prev2_lapsed, prev2_checkins,
                  year_avg,
                  yoy_sales, yoy_sessions, yoy_leads, yoy_new, yoy_lapsed, yoy_checkins):
    """Build a context dict with all computed values for the report."""

    year_avg_label = f"{mo['year']} Avg (excl. {mo['month_short']})"

    ctx = {
        'loc': loc,
        'mo': mo,
        'loc_key': loc_key,
        'month_key': month_key,
        'year_avg_label': year_avg_label,
        'baseline_label': year_avg_label,
        'sales': sales,
        'sessions': sessions,
        'leads': leads,
        'new': new,
        'lapsed': lapsed,
        'checkins': checkins,
        'active': active,
        'baseline': year_avg,

        'prev_sales': prev_sales,
        'prev_sessions': prev_sessions,
        'prev_leads': prev_leads,
        'prev_new': prev_new,
        'prev_lapsed': prev_lapsed,
        'prev_checkins': prev_checkins,

        'prev2_sales': prev2_sales,
        'prev2_sessions': prev2_sessions,
        'prev2_leads': prev2_leads,
        'prev2_new': prev2_new,
        'prev2_lapsed': prev2_lapsed,
        'prev2_checkins': prev2_checkins,

        'year_avg': year_avg,

        'yoy_sales': yoy_sales,
        'yoy_sessions': yoy_sessions,
        'yoy_leads': yoy_leads,
        'yoy_new': yoy_new,
        'yoy_lapsed': yoy_lapsed,
        'yoy_checkins': yoy_checkins,
    }

    # Sales comparators
    ctx['net_mom'] = pct_change(prev_sales.get('net', 0), sales.get('net', 0))
    ctx['net_m2_mom'] = pct_change(prev2_sales.get('net', 0), sales.get('net', 0))
    ctx['net_year_avg'] = pct_change(year_avg['sales'].get('net', 0), sales.get('net', 0))
    ctx['net_yoy'] = pct_change(yoy_sales.get('net', 0), sales.get('net', 0)) if yoy_sales else "n/a"
    ctx['net_baseline'] = ctx['net_year_avg']

    ctx['gross_mom'] = pct_change(prev_sales.get('gross', 0), sales.get('gross', 0))
    ctx['gross_yoy'] = pct_change(yoy_sales.get('gross', 0), sales.get('gross', 0)) if yoy_sales else "n/a"
    ctx['gross_baseline'] = pct_change(year_avg['sales'].get('gross', 0), sales.get('gross', 0))

    ctx['disc_mom'] = pct_change(prev_sales.get('disc', 0), sales.get('disc', 0))
    ctx['disc_baseline'] = pct_change(year_avg['sales'].get('disc', 0), sales.get('disc', 0))

    ctx['sales_count_mom'] = pct_change(prev_sales.get('sales', 0), sales.get('sales', 0))
    ctx['members_mom'] = pct_change(prev_sales.get('members', 0), sales.get('members', 0))
    ctx['atv_mom'] = pct_change(prev_sales.get('atv', 0), sales.get('atv', 0))

    ctx['disc_eff_mom'] = pct_change(prev_sales.get('disc_eff', 0), sales.get('disc_eff', 0))
    ctx['disc_eff_yoy'] = pct_change(yoy_sales.get('disc_eff', 0), sales.get('disc_eff', 0)) if yoy_sales else "n/a"
    ctx['disc_eff_baseline'] = pct_change(year_avg['sales'].get('disc_eff', 0), sales.get('disc_eff', 0))

    # Sessions comparators
    ctx['sessions_mom'] = pct_change(prev_sessions.get('sessions', 0), sessions.get('sessions', 0))
    ctx['visits_mom'] = pct_change(prev_sessions.get('visits', 0), sessions.get('visits', 0))
    ctx['fill_mom'] = pp_change(prev_sessions.get('fill', 0), sessions.get('fill', 0))
    ctx['fill_baseline'] = pp_change(year_avg['sessions'].get('fill', 0), sessions.get('fill', 0))
    ctx['sess_rev_mom'] = pct_change(prev_sessions.get('revenue', 0), sessions.get('revenue', 0))
    ctx['sessions_baseline'] = pct_change(year_avg['sessions'].get('sessions', 0), sessions.get('sessions', 0))
    ctx['visits_baseline'] = pct_change(year_avg['sessions'].get('visits', 0), sessions.get('visits', 0))

    # Leads comparators
    ctx['leads_mom'] = pct_change(prev_leads.get('total', 0), leads.get('total', 0))

    # Conversion
    ctx['conv_mom'] = pp_change(prev_new.get('rate', 0), new.get('rate', 0))
    ctx['conv_baseline'] = pp_change(year_avg['new'].get('rate', 0), new.get('rate', 0))
    ctx['converted_mom'] = pct_change(prev_new.get('converted', 0), new.get('converted', 0))

    # Trials comparators
    ctx['trials_mom'] = pct_change(prev_new.get('trials', 0), new.get('trials', 0))
    ctx['retained_mom'] = pct_change(prev_new.get('retained', 0), new.get('retained', 0))

    # Lapsed comparators
    ctx['lapsed_mom'] = pct_change(prev_lapsed.get('lapsed', 0), lapsed.get('lapsed', 0))
    ctx['churn_mom'] = pp_change(prev_lapsed.get('churn', 0), lapsed.get('churn', 0))
    ctx['churn_baseline'] = pp_change(year_avg['lapsed'].get('churn', 0), lapsed.get('churn', 0))
    ctx['renewal_mom'] = pp_change(prev_lapsed.get('renewal_rate', 0), lapsed.get('renewal_rate', 0))
    ctx['renewal_baseline'] = pp_change(year_avg['lapsed'].get('renewal_rate', 0), lapsed.get('renewal_rate', 0))
    ctx['lapsed_total_mom'] = pct_change(prev_lapsed.get('total', 0), lapsed.get('total', 0))

    # Checkins comparators
    ctx['late_cancel_mom'] = pct_change(prev_checkins.get('late_cancel', 0), checkins.get('late_cancel', 0))
    ctx['lc_rate'] = (checkins.get('late_cancel', 0) / checkins.get('total', 1)) * 100 if checkins.get('total') else 0
    ctx['prev_lc_rate'] = (prev_checkins.get('late_cancel', 0) / prev_checkins.get('total', 1)) * 100 if prev_checkins.get('total') else 0
    ctx['lc_rate_mom'] = pp_change(ctx['prev_lc_rate'], ctx['lc_rate'])

    # Discount penetration
    ctx['disc_penetration'] = (sales.get('disc', 0) / sales.get('gross', 1)) * 100 if sales.get('gross') else 0
    ctx['prev_disc_penetration'] = (prev_sales.get('disc', 0) / prev_sales.get('gross', 1)) * 100 if prev_sales.get('gross') else 0
    ctx['disc_pen_mom'] = pp_change(ctx['prev_disc_penetration'], ctx['disc_penetration'])

    ctx['trial_retention'] = (new.get('retained', 0) / new.get('trials', 1)) * 100 if new.get('trials') else 0
    ctx['cumulative_lapsed'] = get_lapsed_cumulative(loc_key).get(month_key, 0)

    return ctx
    return ctx


def _mom_months(ctx):
    """Return up to 12 real source months ending at the selected report month."""
    return sorted(
        month for month in DATA.get('meta', {}).get('months', [])
        if month <= ctx['month_key']
    )[-12:]


def _mom_row(label, values, fmt='int', agg='sum'):
    return {'label': label, 'values': values, 'fmt': fmt, 'agg': agg}


def build_mom_dataset(ctx):
    """Build section-specific MoM tables from the same normalized report data."""
    months = _mom_months(ctx)
    loc_key = ctx['loc_key']
    month_labels = [datetime.strptime(month, '%Y-%m').strftime('%b %Y') for month in months]

    def series(getter, field):
        return [getter(loc_key, month).get(field, 0) or 0 for month in months]

    sales = lambda field: series(get_sales, field)
    sessions = lambda field: series(get_sessions, field)
    leads = lambda field: series(get_leads, field)
    new = lambda field: series(get_new, field)
    lapsed = lambda field: series(get_lapsed, field)
    checkins = lambda field: series(get_checkins, field)

    section_rows = {
        1: [
            _mom_row('Net Sales', sales('net'), 'currency'),
            _mom_row('Visits', sessions('visits')),
            _mom_row('Fill Rate', sessions('fill'), 'pct', 'avg'),
            _mom_row('Trial Conversion Rate', new('rate'), 'pct', 'avg'),
            _mom_row('Churn Rate', lapsed('churn'), 'pct', 'avg'),
        ],
        2: [
            _mom_row('Gross Sales', sales('gross'), 'currency'),
            _mom_row('Net Sales', sales('net'), 'currency'),
            _mom_row('Discounts', sales('disc'), 'currency'),
            _mom_row('Transactions', sales('sales')),
            _mom_row('Unique Buyers', sales('members')),
            _mom_row('Average Transaction Value', sales('atv'), 'currency', 'avg'),
            _mom_row('Discount Efficiency', sales('disc_eff'), 'decimal', 'avg'),
        ],
        3: [
            _mom_row('Leads', leads('total')),
            _mom_row('Trials', new('trials')),
            _mom_row('Converted', new('converted')),
            _mom_row('Retained', new('retained')),
            _mom_row('Trial Conversion Rate', new('rate'), 'pct', 'avg'),
        ],
        4: [
            _mom_row('Sessions', sessions('sessions')),
            _mom_row('Visits', sessions('visits')),
            _mom_row('Capacity', sessions('capacity')),
            _mom_row('Fill Rate', sessions('fill'), 'pct', 'avg'),
            _mom_row('Session Revenue', sessions('revenue'), 'currency'),
            _mom_row('Late Cancellations', checkins('late_cancel')),
        ],
        5: [
            _mom_row('Memberships Due', lapsed('total')),
            _mom_row('Renewed', lapsed('renewed')),
            _mom_row('New Lapsed Members', lapsed('lapsed')),
            _mom_row('Frozen', lapsed('frozen')),
            _mom_row('Renewal Rate', lapsed('renewal_rate'), 'pct', 'avg'),
            _mom_row('Churn Rate', lapsed('churn'), 'pct', 'avg'),
        ],
        6: [
            _mom_row('Net Sales', sales('net'), 'currency'),
            _mom_row('Trial Conversion Rate', new('rate'), 'pct', 'avg'),
            _mom_row('Fill Rate', sessions('fill'), 'pct', 'avg'),
            _mom_row('New Lapsed Members', lapsed('lapsed')),
            _mom_row('Late Cancellations', checkins('late_cancel')),
        ],
        7: [
            _mom_row('Net Sales', sales('net'), 'currency'),
            _mom_row('Leads', leads('total')),
            _mom_row('Trials', new('trials')),
            _mom_row('Visits', sessions('visits')),
            _mom_row('Fill Rate', sessions('fill'), 'pct', 'avg'),
            _mom_row('Churn Rate', lapsed('churn'), 'pct', 'avg'),
        ],
    }
    titles = {
        1: 'Executive Summary', 2: 'Commercial Revenue', 3: 'Acquisition Funnel',
        4: 'Sessions & Delivery', 5: 'Member Health', 6: 'Decision Agenda',
        7: 'Forward Indicators',
    }
    return {
        section_num: {
            'eyebrow': f'{section_num:02d} · {titles[section_num]}',
            'title': f'{titles[section_num]} — Month on Month',
            'months': month_labels,
            'rows': rows,
        }
        for section_num, rows in section_rows.items()
    }


def build_mom_tables(ctx_list):
    """Emit the three data globals the client scripts read, plus the sales
    matrix dialog they populate. The MoM panels themselves are rendered into
    each section by mom-panel.js."""
    datasets = {}
    for ctx in ctx_list:
        for section_num, block in build_mom_dataset(ctx).items():
            key = report_shell.MOM_KEYS.get(section_num)
            if key:
                datasets[key] = block
    ctx = ctx_list[-1]
    return (report_shell.sales_matrix_modal(ctx)
            + report_shell.data_globals(datasets, build_extra_data(ctx), build_sales_matrix(ctx)))


def build_extra_data(ctx):
    """Drill-down tables hung off the funnel and sessions MoM panels."""
    loc_key = ctx['loc_key']
    months = _mom_months(ctx)
    month_labels = [datetime.strptime(m, '%Y-%m').strftime('%b %Y') for m in months]

    # What new clients bought first, ranked by how many members bought it.
    products = get_sales_breakdowns(loc_key, ctx['month_key']).get('product', {})
    new_client_purchases = []
    for name, v in sorted(products.items(), key=lambda kv: -(kv[1].get('rows', 0) or 0))[:12]:
        units = v.get('rows', 0) or 0
        net = v.get('net', 0) or 0
        new_client_purchases.append({
            'name': name,
            'unitsSold': units,
            'totalLtv': round(net),
            'atv': round(net / units) if units else 0,
            'auv': round(net / units) if units else 0,
        })

    # Client type and trainer, month by month.
    type_names = set()
    for month in months:
        type_names.update(get_new_type(loc_key, month) or {})
    mom_by_client_type = [
        {'label': name, 'fmt': 'int', 'agg': 'sum',
         'values': [(get_new_type(loc_key, m) or {}).get(name, 0) for m in months]}
        for name in sorted(type_names)
    ]

    trainers_now = get_sessions_by_trainer(loc_key, ctx['month_key']) or {}
    teacher_scorecard = []
    for name, v in sorted(trainers_now.items(), key=lambda kv: -(kv[1].get('visits', 0) or 0)):
        capacity = v.get('capacity', 0) or 0
        visits = v.get('visits', 0) or 0
        teacher_scorecard.append({
            'instructor': name,
            'cls': v.get('sessions', 0) or 0,
            'fillRate': round(visits / capacity * 100, 1) if capacity else 0.0,
            'pay': round(v.get('revenue', 0) or 0),
        })

    trainer_names = set()
    for month in months:
        trainer_names.update(get_sessions_by_trainer(loc_key, month) or {})
    mom_trainer = [
        {'label': name, 'fmt': 'int', 'agg': 'sum',
         'values': [((get_sessions_by_trainer(loc_key, m) or {}).get(name) or {}).get('sessions', 0)
                    for m in months]}
        for name in sorted(trainer_names)
    ]

    return {
        'months': month_labels,
        'newClientPurchases': new_client_purchases,
        'momByClientType': mom_by_client_type,
        'teacherScorecard': teacher_scorecard,
        'momTrainer': mom_trainer,
    }


def build_sales_matrix(ctx):
    """Every month of category and product sales, for the sales matrix dialog."""
    loc_key = ctx['loc_key']
    months = sorted(m for m in DATA.get('meta', {}).get('months', []) if m <= ctx['month_key'])
    months.reverse()
    month_labels = {m: datetime.strptime(m, '%Y-%m').strftime('%b %Y') for m in months}

    def cell(v):
        gross = v.get('gross', 0) or 0
        net = v.get('net', 0) or 0
        units = v.get('rows', 0) or 0
        return {
            'net': round(net), 'gross': round(gross), 'units': units, 'txns': units,
            'members': units, 'vat': round(gross - net), 'discount': round(v.get('disc', 0) or 0),
        }

    names = set()
    for month in months:
        names.update(get_sales_breakdowns(loc_key, month).get('category', {}))

    categories = []
    for name in sorted(names):
        values = {}
        for month in months:
            v = get_sales_breakdowns(loc_key, month).get('category', {}).get(name)
            if v:
                values[month] = cell(v)
        categories.append({'name': name, 'values': values})

    totals = {}
    for month in months:
        rows = get_sales_breakdowns(loc_key, month).get('category', {}).values()
        if not rows:
            continue
        gross = sum((r.get('gross', 0) or 0) for r in rows)
        net = sum((r.get('net', 0) or 0) for r in rows)
        units = sum((r.get('rows', 0) or 0) for r in rows)
        totals[month] = {
            'net': round(net), 'gross': round(gross), 'units': units, 'txns': units,
            'members': units, 'vat': round(gross - net),
            'discount': round(sum((r.get('disc', 0) or 0) for r in rows)),
        }

    return {'months': months, 'monthLabels': month_labels,
            'categories': categories, 'totals': totals}


def build_html(ctx):
    """Assemble the full HTML document."""
    html = head(ctx)
    html += topbar(ctx)
    html += cover(ctx)
    html += render_chapters(ctx)
    html += build_mom_tables([ctx])
    html += "\n<!-- REPORT_CLIENT_PLACEHOLDER -->\n"
    html += footer(ctx)
    html += theme_script(ctx)
    html += "\n</body>\n</html>\n"
    return html


def build_multi_title(ctx_list):
    locs = sorted({c['loc']['short_name'] for c in ctx_list})
    months = sorted({f"{c['mo']['month_name']} {c['mo']['year']}" for c in ctx_list})
    loc_part = locs[0] if len(locs) == 1 else f'{len(locs)} Studios'
    month_part = months[0] if len(months) == 1 else f'{len(months)} Months'
    return f'{loc_part} &middot; {month_part}'


def head_multi(ctx, title_suffix):
    """A bundle uses the same document shell as a single report, so the two
    never drift apart; only the title line differs."""
    html = report_shell.head(ctx)
    return html.replace(
        f"<title>{ctx['loc']['short_name']} · Performance Report · "
        f"{ctx['mo']['month_name']} {ctx['mo']['year']}</title>",
        f'<title>Performance Report Bundle · {title_suffix}</title>')


def topbar_multi(ctx, title_suffix, combo_count):
    html = report_shell.topbar(ctx)
    return html.replace(
        f"<small>Performance Report · {ctx['mo']['month_name']} {ctx['mo']['year']}</small>",
        f'<small>{combo_count} reports · {title_suffix}</small>')


def build_toc(ctx_list):
    items = []
    for i, c in enumerate(ctx_list):
        items.append(f'''      <a class="toc-item" href="#combo-{i}">
        <span class="toc-num">{i + 1:02d}</span>
        <span class="toc-label">{c['loc']['short_name']} &middot; {c['mo']['month_name']} {c['mo']['year']}</span>
      </a>''')
    return f'''
<section class="report-section toc-section">
  <div class="container">
    <div class="section-hero" data-num="00">
      <div class="section-header">
        <div class="section-header-left">
          <span class="section-eyebrow">Report Bundle</span>
          <h2 class="section-title">{len(ctx_list)} reports in this document</h2>
          <p class="section-deck">Jump to any studio &amp; month below, or scroll through them in order.</p>
        </div>
      </div>
    </div>
    <div class="toc-grid">
{chr(10).join(items)}
    </div>
  </div>
</section>
'''


def build_html_multi(ctx_list):
    """Assemble a bundled document covering multiple studio x month combos."""
    title_suffix = build_multi_title(ctx_list)
    html = head_multi(ctx_list[0], title_suffix)
    html += topbar_multi(ctx_list[0], title_suffix, len(ctx_list))

    # Group by location for tabs
    locations = {}
    for ctx in ctx_list:
        loc_key = ctx['loc_key']
        if loc_key not in locations:
            locations[loc_key] = []
        locations[loc_key].append(ctx)

    # Add location tabs if multiple locations
    if len(locations) > 1:
        html += '<div class="location-tabs">'
        for i, (loc_key, loc_ctxs) in enumerate(locations.items()):
            loc_name = loc_ctxs[0]['loc']['short_name']
            active_class = 'active' if i == 0 else ''
            html += f'<button class="location-tab {active_class}" data-location="{loc_key}">{loc_name}</button>'
        html += '</div>'

        # Wrap each location's content
        for i, (loc_key, loc_ctxs) in enumerate(locations.items()):
            active_class = 'active' if i == 0 else ''
            html += f'<div id="location-{loc_key}" class="location-content {active_class}">'
            for j, ctx in enumerate(loc_ctxs):
                html += f'\n<div class="report-instance" id="combo-{loc_key}-{j}">\n'
                html += cover(ctx)
                html += render_chapters(ctx)
                html += '\n</div>\n'
            html += '</div>'
    else:
        # Single location, use original TOC approach
        html += build_toc(ctx_list)
        for i, ctx in enumerate(ctx_list):
            style = ' style="page-break-before: always;"' if i > 0 else ''
            html += f'\n<div class="report-instance" id="combo-{i}"{style}>\n'
            html += cover(ctx)
            html += render_chapters(ctx)
            html += '\n</div>\n'

    html += build_mom_tables(ctx_list)
    html += "\n<!-- REPORT_CLIENT_PLACEHOLDER -->\n"
    html += footer(ctx_list[-1])
    html += theme_script(ctx_list[-1])
    html += "\n</body>\n</html>\n"
    return html


def head(ctx):
    return report_shell.head(ctx)


def topbar(ctx):
    return report_shell.topbar(ctx)


def cover(ctx):
    """Opening spread: the month in eight metric cards, each with a year of
    history behind it and a back face explaining what the number means."""
    loc = ctx['loc']
    mo = ctx['mo']
    s = ctx['sales']
    sess = ctx['sessions']
    new = ctx['new']
    lapsed = ctx['lapsed']
    chk = ctx['checkins']

    months = sorted(m for m in DATA.get('meta', {}).get('months', []) if m <= ctx['month_key'])[-3:]
    labels = '|'.join(datetime.strptime(m, '%Y-%m').strftime('%b') for m in months)

    def history(getter, field, scale=1.0, decimals=2):
        return ','.join(
            f"{(float(getter(ctx['loc_key'], month).get(field, 0) or 0) * scale):.{decimals}f}"
            for month in months)

    visits = sess.get('visits', 0) or 0
    rev_per_visit = (s.get('net', 0) or 0) / visits if visits else 0

    # Group revenue is everything sold as class access rather than a membership.
    GROUP_CATEGORIES = ('Class Packages', 'Sessions/Single Classes', 'Newcomers Special')
    categories = get_sales_breakdowns(ctx['loc_key'], ctx['month_key']).get('category', {})
    cat_total = sum((v.get('net', 0) or 0) for v in categories.values()) or 1
    group_share = sum((v.get('net', 0) or 0)
                      for k, v in categories.items() if k in GROUP_CATEGORIES) / cat_total * 100

    def tone(change, higher_is_better=True, is_pp=False):
        return (badge_from_pp if is_pp else badge)(change, higher_is_better)

    cards = [
        {
            'label': 'Net Sales', 'value': lakh(s['net']),
            'sub': f"Gross {lakh(s['gross'])} &middot; Disc {lakh(s['disc'])}",
            'trends': [('MoM', ctx['net_mom'], tone(ctx['net_mom'])),
                       ('YoY', ctx['net_yoy'], tone(ctx['net_yoy']))],
            'labels': labels, 'series': history(get_sales, 'net', 1 / 100000.0),
            'prefix': '&#8377;', 'suffix': 'L', 'decimals': 2,
            'baseline': ctx['net_baseline'], 'kicker': 'Commercial momentum',
            'copy': (f"{mo['month_name']} closed at {lakh(s['net'])} net across "
                     f"{fmt_int(s['sales'])} transactions, an ATV of {rupee(s['atv'])}."),
            'back_stats': [('MoM', ctx['net_mom']), ('YoY', ctx['net_yoy']),
                           ('Vs baseline', ctx['net_baseline'])],
            'focus': 'Broaden the buyer base so growth is not price-dependent.',
            'tip': f"Net revenue against {ctx['baseline_label']}.",
        },
        {
            'label': 'Visits', 'value': fmt_int(sess['visits']),
            'sub': f"Across {fmt_int(sess['sessions'])} sessions",
            'trends': [('MoM', ctx['visits_mom'], tone(ctx['visits_mom'])),
                       ('Sessions', ctx['sessions_mom'], tone(ctx['sessions_mom']))],
            'labels': labels, 'series': history(get_sessions, 'visits', 1, 0),
            'grouping': True, 'decimals': 0,
            'baseline': ctx['visits_baseline'], 'kicker': 'Demand depth',
            'copy': (f"{fmt_int(sess['visits'])} visits across {fmt_int(sess['sessions'])} sessions, "
                     f"averaging {sess['avg_visits']:.1f} per session."),
            'back_stats': [('MoM', ctx['visits_mom']), ('Sessions', ctx['sessions_mom']),
                           ('Vs baseline', ctx['visits_baseline'])],
            'focus': 'Protect the peak slots that carry most of this volume.',
            'tip': 'Total attended visits recorded in the month.',
        },
        {
            'label': 'Fill Rate', 'value': pct(sess['fill']),
            'sub': f"{fmt_int(sess['capacity'])} seats offered",
            'trends': [('MoM', ctx['fill_mom'], tone(ctx['fill_mom'], is_pp=True)),
                       ('Empty', fmt_int(sess['empty']), 'warn' if sess['empty'] else 'good')],
            'labels': labels, 'series': history(get_sessions, 'fill', 1, 1),
            'suffix': '%', 'decimals': 1,
            'baseline': ctx['fill_baseline'], 'kicker': 'Capacity health',
            'copy': (f"{pct(sess['fill'])} of {fmt_int(sess['capacity'])} offered seats were taken; "
                     f"{fmt_int(sess['empty'])} sessions ran empty."),
            'back_stats': [('MoM', ctx['fill_mom']), ('Empty classes', fmt_int(sess['empty'])),
                           ('Vs baseline', ctx['fill_baseline'])],
            'focus': 'Retire or reschedule the slots that never fill.',
            'tip': 'Visits divided by seats offered.',
        },
        {
            'label': 'Conversion Rate', 'value': pct(new['rate']),
            'sub': f"{fmt_int(new['trials'])} trials &rarr; {fmt_int(new.get('converted', 0))} joins",
            'trends': [('MoM', ctx['conv_mom'], tone(ctx['conv_mom'], is_pp=True)),
                       ('Trials', ctx['trials_mom'], tone(ctx['trials_mom']))],
            'labels': labels, 'series': history(get_new, 'rate', 1, 1),
            'suffix': '%', 'decimals': 1,
            'baseline': ctx['conv_baseline'], 'kicker': 'Funnel quality',
            'copy': (f"{fmt_int(new['trials'])} trials produced {fmt_int(new.get('converted', 0))} "
                     f"conversions, a {pct(new['rate'])} rate."),
            'back_stats': [('MoM', ctx['conv_mom']), ('Trials', ctx['trials_mom']),
                           ('Vs baseline', ctx['conv_baseline'])],
            'focus': 'Fix the handover between trial and first purchase.',
            'tip': 'Trials that converted to a paid membership or pack.',
        },
        {
            'label': 'Lapsed Members', 'value': fmt_int(lapsed['lapsed']),
            'sub': f"{fmt_int(lapsed['renewed'])} of {fmt_int(lapsed['total'])} renewed",
            'trends': [('MoM', ctx['lapsed_mom'], tone(ctx['lapsed_mom'], higher_is_better=False)),
                       ('Churn', ctx['churn_mom'], tone(ctx['churn_mom'], False, is_pp=True))],
            'labels': labels, 'series': history(get_lapsed, 'lapsed', 1, 0),
            'decimals': 0,
            'baseline': ctx['churn_baseline'], 'kicker': 'Retention watch',
            'copy': (f"{fmt_int(lapsed['total'])} memberships reached end-of-life; "
                     f"{pct(lapsed['renewal_rate'])} renewed and {pct(lapsed['churn'])} churned."),
            'back_stats': [('Renewal rate', pct(lapsed['renewal_rate'])),
                           ('Churn rate', pct(lapsed['churn'])),
                           ('Frozen', fmt_int(lapsed['frozen']))],
            'focus': 'Work the expiring book before it expires, not after.',
            'tip': 'Memberships that ended without a renewal.',
        },
        {
            'label': 'Discount Efficiency', 'value': f"&#8377;{s['disc_eff']:.2f}",
            'sub': f"{pct(ctx['disc_penetration'])} of gross discounted",
            'trends': [('MoM', ctx['disc_eff_mom'], tone(ctx['disc_eff_mom'])),
                       ('Penetration', ctx['disc_pen_mom'], tone(ctx['disc_pen_mom'], False, is_pp=True))],
            'labels': labels, 'series': history(get_sales, 'disc_eff', 1, 2),
            'prefix': '&#8377;', 'decimals': 2,
            'baseline': ctx['disc_eff_baseline'], 'kicker': 'Promotion return',
            'copy': (f"Every &#8377;1 of discount returned &#8377;{s['disc_eff']:.2f} of net revenue; "
                     f"discount value was {lakh(s['disc'])}."),
            'back_stats': [('MoM', ctx['disc_eff_mom']),
                           ('Discount value', lakh(s['disc'])),
                           ('Penetration', pct(ctx['disc_penetration']))],
            'focus': 'Cap the offers that buy volume without buying margin.',
            'tip': 'Net revenue collected per rupee of discount given.',
        },
        {
            'label': 'Group Revenue Share', 'value': pct(group_share),
            'sub': 'Class packs, single classes &amp; newcomer offers',
            'trends': [('Memberships', pct(100 - group_share), 'warn'),
                       ('Categories', fmt_int(len(categories)), 'good')],
            'labels': '', 'series': '',
            'baseline': '', 'kicker': 'Group contribution',
            'copy': (f"{pct(group_share)} of net revenue came from class access rather than "
                     'memberships, which sets how exposed the month is to pack buyers.'),
            'back_stats': [('Group', pct(group_share)),
                           ('Memberships', pct(100 - group_share)),
                           ('Categories', fmt_int(len(categories)))],
            'focus': 'Convert repeat pack buyers onto memberships.',
            'tip': 'Share of net revenue from class-access products.',
        },
        {
            'label': 'ATV', 'value': rupee(s['atv']),
            'sub': f"Across {fmt_int(s['sales'])} transactions",
            'trends': [('MoM', ctx['atv_mom'], tone(ctx['atv_mom'])),
                       ('Buyers', fmt_int(s['members']), 'good')],
            'labels': labels, 'series': history(get_sales, 'atv', 1, 0),
            'prefix': '&#8377;', 'grouping': True, 'decimals': 0,
            'baseline': '', 'kicker': 'Ticket size',
            'copy': (f"Average transaction value is {rupee(s['atv'])} across "
                     f"{fmt_int(s['sales'])} transactions from {fmt_int(s['members'])} buyers."),
            'back_stats': [('MoM', ctx['atv_mom']), ('Transactions', fmt_int(s['sales'])),
                           ('Unique buyers', fmt_int(s['members']))],
            'focus': 'Move buyers up the price ladder rather than discounting down it.',
            'tip': 'Net revenue divided by the number of transactions.',
        },
        {
            'label': 'Leads', 'value': fmt_int(ctx['leads']['total']),
            'sub': f"{pct(ctx['leads']['rate'])} of leads converted",
            'trends': [('MoM', ctx['leads_mom'], tone(ctx['leads_mom'])),
                       ('Converted', fmt_int(ctx['leads'].get('converted', 0)), 'good')],
            'labels': labels, 'series': history(get_leads, 'total', 1, 0),
            'grouping': True, 'decimals': 0,
            'baseline': '', 'kicker': 'Pipeline volume',
            'copy': (f"{fmt_int(ctx['leads']['total'])} leads entered the funnel and "
                     f"{fmt_int(ctx['leads'].get('converted', 0))} converted, a {pct(ctx['leads']['rate'])} rate."),
            'back_stats': [('MoM', ctx['leads_mom']),
                           ('Converted', fmt_int(ctx['leads'].get('converted', 0))),
                           ('Lead conversion', pct(ctx['leads']['rate']))],
            'focus': 'Pipeline set this month is next month\u2019s trial book.',
            'tip': 'Enquiries recorded against the studio in the month.',
        },
        {
            'label': 'Renewal Rate', 'value': pct(lapsed['renewal_rate']),
            'sub': f"{fmt_int(lapsed['total'])} memberships reached expiry",
            'trends': [('MoM', ctx['renewal_mom'], tone(ctx['renewal_mom'], is_pp=True)),
                       ('Frozen', fmt_int(lapsed['frozen']), 'warn' if lapsed['frozen'] else 'good')],
            'labels': labels, 'series': history(get_lapsed, 'renewal_rate', 1, 1),
            'suffix': '%', 'decimals': 1,
            'baseline': ctx['renewal_baseline'], 'kicker': 'Book retention',
            'copy': (f"{pct(lapsed['renewal_rate'])} of the {fmt_int(lapsed['total'])} memberships that "
                     f"reached expiry were renewed; {fmt_int(lapsed['frozen'])} are frozen."),
            'back_stats': [('MoM', ctx['renewal_mom']), ('Renewed', fmt_int(lapsed['renewed'])),
                           ('Vs baseline', ctx['renewal_baseline'])],
            'focus': 'Renewals are cheaper than replacements — work the expiry list first.',
            'tip': 'Share of expiring memberships that renewed.',
        },
        {
            'label': 'Late Cancel Rate', 'value': pct(ctx['lc_rate']),
            'sub': f"{fmt_int(chk.get('late_cancel', 0))} of {fmt_int(chk.get('total', 0))} bookings",
            'trends': [('MoM', ctx['lc_rate_mom'], tone(ctx['lc_rate_mom'], False, is_pp=True)),
                       ('Volume', ctx['late_cancel_mom'], tone(ctx['late_cancel_mom'], higher_is_better=False))],
            'labels': '', 'series': '',
            'baseline': '', 'kicker': 'Seat leakage',
            'copy': (f"{pct(ctx['lc_rate'])} of bookings were cancelled too late to resell the seat, "
                     f"{fmt_int(chk.get('heavy_cancelers', 0))} of them by repeat cancellers."),
            'back_stats': [('Late cancels', fmt_int(chk.get('late_cancel', 0))),
                           ('Rate', pct(ctx['lc_rate'])),
                           ('Repeat cancellers', fmt_int(chk.get('heavy_cancelers', 0)))],
            'focus': 'A late cancellation is an empty seat nobody could buy.',
            'tip': 'Late cancellations as a share of all bookings.',
        },
        {
            'label': 'Revenue / Visit', 'value': rupee(rev_per_visit),
            'sub': f"{fmt_int(chk.get('late_cancel', 0))} late cancellations",
            'trends': [('Visits', ctx['visits_mom'], tone(ctx['visits_mom'])),
                       ('Late cancels', ctx['late_cancel_mom'],
                        tone(ctx['late_cancel_mom'], higher_is_better=False))],
            'labels': '', 'series': '',
            'baseline': '', 'kicker': 'Visit economics',
            'copy': (f"Each attended visit carried {rupee(rev_per_visit)} of net revenue. "
                     f"{pct(ctx['lc_rate'])} of bookings were cancelled late."),
            'back_stats': [('Revenue / visit', rupee(rev_per_visit)),
                           ('Late cancel rate', pct(ctx['lc_rate'])),
                           ('Visits', fmt_int(sess['visits']))],
            'focus': 'Late cancellations are lost seats — price or penalise them.',
            'tip': 'Net revenue divided by attended visits.',
        },
    ]

    headline = (f"{loc['short_name']} <span class=\"accent-word\">studio performance</span><br/>"
                f"for <span class=\"accent-yellow\">{mo['month_name']} {mo['year']}</span> — "
                'operational rhythm, funnel economics, and the lapsed-member question.')
    sub = (f"A data-led review of the studio&rsquo;s commercial and operational performance in "
           f"{mo['month_name']} {mo['year']}, benchmarked against {mo['prev_month_name']} "
           f"and the <strong>{ctx['baseline_label']} baseline</strong>. "
           'Every section is structured to surface a business decision — class schedule, trainer '
           'deployment, discount discipline, and membership retention — that senior management '
           'can act on this quarter.')

    meta_items = [
        ('Location', loc['full_name']),
        ('Period', f"01 {mo['month_name']} {mo['year']} — {mo['last_day']} {mo['month_name']} {mo['year']}"),
        ('Reporting basis',
         f"Net Sales &middot; {fmt_int(sess['sessions'])} sessions &middot; {fmt_int(s['members'])} unique buyers"),
        ('Comparators', f"{mo['prev_month_name']} &middot; {ctx['baseline_label']} &middot; YoY"),
        ('Audience', 'Senior Management &middot; Board Review'),
    ]

    marquee_items = [
        (ctx['net_mom'], 'Net Sales MoM'),
        (fmt_int(sess['visits']), 'Studio Visits'),
        (pct(sess['fill']), 'Fill Rate'),
        (pct(new['rate']), 'Trial Conversion'),
        (pct(lapsed['renewal_rate']), 'Renewal Rate'),
        (pct(group_share), 'Group Revenue Share'),
        (rupee(rev_per_visit), 'Revenue per Visit'),
    ]

    return report_shell.hero(ctx, headline, sub, meta_items, marquee_items, cards)


# Placeholder for section functions - will be implemented next
def section_01_executive_summary(ctx):
    return section_01(ctx)

def section_02_revenue(ctx):
    return section_02(ctx)

def section_03_funnel(ctx):
    return section_03(ctx)

def section_04_sessions(ctx):
    return section_04(ctx)

def section_05_lapsed(ctx):
    return section_05(ctx)

def section_06_recommendations(ctx):
    return section_06(ctx)

def section_07_predictions(ctx):
    return section_07(ctx)


def section_08_appendix(ctx):
    return section_08(ctx)


# The narrative order: money, demand, funnel, retention, outlook, actions,
# then the month-on-month appendix.
CHAPTERS = [
    section_01_executive_summary,
    section_02_revenue,
    section_03_funnel,
    section_04_sessions,
    section_05_lapsed,
    section_06_recommendations,
    section_07_predictions,
]


def render_chapters(ctx):
    reset_mom_registry()
    # Each chapter carries its own month-on-month grid inline, so this is a
    # straight render in narrative order.
    return ''.join(chapter(ctx) for chapter in CHAPTERS)


def footer(ctx):
    s = ctx['sales']
    sess = ctx['sessions']
    return report_shell.footer(ctx, [
        ('Net Sales', lakh(s['net'])),
        ('Visits', fmt_int(sess['visits'])),
        ('Fill Rate', pct(sess['fill'])),
        ('Conversion', pct(ctx['leads']['rate'])),
        ('Churn Rate', pct(ctx['lapsed']['churn'])),
        ('Discount Penetration', pct(ctx['disc_penetration'])),
    ])


def theme_script(ctx):
    """The report's own scripts. Shared chrome — theme, scroll, KPI charts,
    carousel, PDF export — is inlined by report_shell.scripts()."""
    return report_shell.page_furniture() + report_shell.scripts()


# These will be imported from sections module
from sections_v2 import (
    section_01, section_02, section_03, section_04,
    section_05, section_06, section_07, section_08,
    reset_mom_registry
)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    if not LOC_KEY_ARG or not MONTH_KEY_ARG:
        print("Usage: gen_report_v2.py <analysis.json> <loc_key>[,loc_key...] <month_key>[,month_key...] [output.html]")
        sys.exit(1)

    loc_keys = [k.strip() for k in LOC_KEY_ARG.split(',') if k.strip()]
    month_keys = [k.strip() for k in MONTH_KEY_ARG.split(',') if k.strip()]

    for lk in loc_keys:
        if lk not in LOCATIONS:
            print(f"Unknown loc_key '{lk}'. Available: {', '.join(LOCATIONS)}")
            sys.exit(1)
    for mk in month_keys:
        if mk not in MONTHS:
            print(f"Unknown month_key '{mk}'. Available: {', '.join(MONTHS)}")
            sys.exit(1)

    combo_count = len(loc_keys) * len(month_keys)
    print(f"Generating {combo_count} combo(s): {loc_keys} x {month_keys}...")
    html = generate_report(loc_keys, month_keys)

    if OUTPUT_HTML:
        filename = OUTPUT_HTML
    elif combo_count == 1:
        loc = LOCATIONS[loc_keys[0]]
        mo = MONTHS[month_keys[0]]
        filename = f"{loc['short_name'].replace(' ', '_').replace(',', '')}_Performance_Report_{mo['month_name']}_{mo['year']}.html"
    else:
        filename = f"Performance_Report_Bundle_{combo_count}_reports.html"

    if EMIT_PANES:
        # Deduplicate: a bundle renders the same studio-month once per combo.
        seen, requests = set(), []
        for req in sections_v2.PANE_REQUESTS:
            if req['key'] in seen:
                continue
            seen.add(req['key'])
            requests.append(req)
        with open(EMIT_PANES, 'w') as f:
            json.dump(requests, f, ensure_ascii=False)
        print(f"  → {EMIT_PANES} ({len(requests)} insight panes)")
        return

    with open(filename, 'w') as f:
        f.write(html)
    print(f"  → {filename} ({len(html):,} chars)")


if __name__ == '__main__':
    main()
