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

import sections_v2
if AI_CONTEXT_JSON and os.path.exists(AI_CONTEXT_JSON):
    with open(AI_CONTEXT_JSON, 'r') as f:
        sections_v2.AI_CONTEXT = json.load(f)
else:
    sections_v2.AI_CONTEXT = {}


# Load CSS from reference (co-located with this script, not the caller's cwd)
with open(os.path.join(SCRIPT_DIR, 'full_css.txt'), 'r') as f:
    CSS = f.read()

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
    data = DATA.get('sales', {}).get(loc, {}).get(month, {})
    if not data:
        return {'net': 0, 'gross': 0, 'disc': 0, 'sales': 0, 'members': 0, 'atv': 0, 'disc_eff': 0}
    return data

def get_sessions(loc, month):
    data = DATA.get('sessions', {}).get(loc, {}).get(month, {})
    if not data:
        return {'sessions': 0, 'visits': 0, 'capacity': 0, 'fill': 0, 'revenue': 0, 'avg_visits': 0}
    return data

def get_leads(loc, month):
    data = DATA.get('leads', {}).get(loc, {}).get(month, {})
    if not data:
        return {'total': 0, 'converted': 0, 'rate': 0}
    # Ensure required keys exist even if data is partial
    data.setdefault('total', 0)
    data.setdefault('converted', 0)
    data.setdefault('rate', 0)
    return data

def get_leads_source(loc, month):
    return DATA.get('leads_by_source', {}).get(loc, {}).get(month, {})

def get_new(loc, month):
    data = DATA.get('new', {}).get(loc, {}).get(month, {})
    if not data:
        return {'rate': 0, 'converted': 0, 'trials': 0, 'retained': 0}
    return data

def get_new_type(loc, month):
    return DATA.get('new_by_type', {}).get(loc, {}).get(month, {})

def get_lapsed(loc, month):
    data = DATA.get('lapsed', {}).get(loc, {}).get(month, {})
    if not data:
        return {'total': 0, 'renewed': 0, 'lapsed': 0, 'frozen': 0, 'churn': 0, 'renewal_rate': 0}
    return data

def get_lapsed_product(loc, month):
    return DATA.get('lapsed_by_product', {}).get(loc, {}).get(month, {})

def get_lapsed_cumulative(loc):
    return DATA.get('lapsed_cumulative', {}).get(loc, {})

def get_checkins(loc, month):
    data = DATA.get('checkins', {}).get(loc, {}).get(month, {})
    if not data:
        return {'late_cancel': 0, 'heavy_cancelers': 0}
    return data

def get_active(loc):
    return DATA.get('active', {}).get(loc, {})

def get_baseline(loc):
    return DATA.get('baseline', {}).get(loc, {})

def get_heatmap(loc, month):
    return DATA.get('heatmap', {}).get(loc, {}).get(month, {})

def get_sessions_by_class(loc, month):
    return DATA.get('sessions_by_class', {}).get(loc, {}).get(month, {})

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
            'sales': {}, 'sessions': {}, 'leads': {}, 'new': {}, 'lapsed': {}, 'checkins': {},
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

    ctx['new']['converted'] = new.get('retained', 0)
    ctx['new']['rate'] = (new.get('converted', 0) / new.get('trials', 1)) * 100 if new.get('trials') else 0
    ctx['trial_retention'] = (new.get('retained', 0) / new.get('trials', 1)) * 100 if new.get('trials') else 0
    ctx['cumulative_lapsed'] = get_lapsed_cumulative(loc_key).get(month_key, 0)

    return ctx
    return ctx


def build_cover_page(ctx):
    """Generate a stunning cover page for the report."""
    loc = ctx['loc']
    mo = ctx['mo']
    s = ctx['sales']
    sess = ctx['sessions']
    leads = ctx['leads']
    new = ctx['new']
    lapsed = ctx['lapsed']

    return f'''
<div class="report-cover">
  <div class="report-cover-brand">
    <span class="brand-mark"></span>
    Studio Pulse · Performance Intelligence
  </div>
  <h1 class="report-cover-title">{loc['short_name']}</h1>
  <p class="report-cover-subtitle">
    Performance Report · <span class="accent-yellow">{mo['month_name']} {mo['year']}</span>
  </p>
  <div class="report-cover-meta">
    <div class="report-cover-meta-item">
      <span class="label">Location</span>
      <span class="value">{loc['full_name']}</span>
    </div>
    <div class="report-cover-meta-item">
      <span class="label">Period</span>
      <span class="value">{mo['date_range']}</span>
    </div>
    <div class="report-cover-meta-item">
      <span class="label">Reporting Basis</span>
      <span class="value">{sess['sessions']} sessions · {s['members']} unique buyers</span>
    </div>
    <div class="report-cover-meta-item">
      <span class="label">Audience</span>
      <span class="value">Senior Management · Board Review</span>
    </div>
  </div>
  <div class="report-cover-kpis">
    <div class="report-cover-kpi">
      <div class="kpi-label">Net Revenue</div>
      <div class="kpi-value">{lakh(s['net'])}</div>
    </div>
    <div class="report-cover-kpi">
      <div class="kpi-label">Sessions</div>
      <div class="kpi-value">{fmt_int(sess['sessions'])}</div>
    </div>
    <div class="report-cover-kpi">
      <div class="kpi-label">Fill Rate</div>
      <div class="kpi-value">{pct(sess['fill'])}</div>
    </div>
    <div class="report-cover-kpi">
      <div class="kpi-label">Conversion</div>
      <div class="kpi-value">{pct(new['rate'])}</div>
    </div>
    <div class="report-cover-kpi">
      <div class="kpi-label">Churn Rate</div>
      <div class="kpi-value">{pct(lapsed['churn'])}</div>
    </div>
  </div>
  <div class="report-cover-footer">
    Confidential · For Internal Use Only · Generated {datetime.now().strftime('%B %d, %Y')}
  </div>
</div>
'''


def build_html(ctx):
    """Assemble the full HTML document."""
    html = head(ctx)
    html += topbar(ctx)
    html += build_cover_page(ctx)
    html += hero(ctx)
    html += section_01_executive_summary(ctx)
    html += section_02_revenue(ctx)
    html += section_03_funnel(ctx)
    html += section_04_sessions(ctx)
    html += section_05_lapsed(ctx)
    html += section_06_recommendations(ctx)
    html += section_07_predictions(ctx)
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


def head_multi(title_suffix):
    return f'''<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Performance Report Bundle &middot; {title_suffix}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Source+Serif+Pro:wght@400;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
{CSS}
  </style>
</head>
<body>
<div class="print-frame"></div>
'''


def topbar_multi(title_suffix, combo_count):
    return f'''
<div class="topbar">
  <div class="topbar-inner">
    <div class="brand">
      <div class="brand-mark"></div>
      <div class="brand-text">
        Studio Pulse &middot; Report Bundle
        <small>{combo_count} reports &middot; {title_suffix}</small>
      </div>
    </div>
    <button class="theme-toggle" id="theme-toggle" aria-label="Toggle theme">
      <svg id="theme-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="4"></circle>
        <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"></path>
      </svg>
      <span id="theme-label">Dark</span>
    </button>
  </div>
</div>
'''


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
    html = head_multi(title_suffix)
    html += topbar_multi(title_suffix, len(ctx_list))

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
                html += hero(ctx)
                html += section_01_executive_summary(ctx)
                html += section_02_revenue(ctx)
                html += section_03_funnel(ctx)
                html += section_04_sessions(ctx)
                html += section_05_lapsed(ctx)
                html += section_06_recommendations(ctx)
                html += section_07_predictions(ctx)
                html += '\n</div>\n'
            html += '</div>'
    else:
        # Single location, use original TOC approach
        html += build_toc(ctx_list)
        for i, ctx in enumerate(ctx_list):
            style = ' style="page-break-before: always;"' if i > 0 else ''
            html += f'\n<div class="report-instance" id="combo-{i}"{style}>\n'
            html += hero(ctx)
            html += section_01_executive_summary(ctx)
            html += section_02_revenue(ctx)
            html += section_03_funnel(ctx)
            html += section_04_sessions(ctx)
            html += section_05_lapsed(ctx)
            html += section_06_recommendations(ctx)
            html += section_07_predictions(ctx)
            html += '\n</div>\n'

    html += "\n<!-- REPORT_CLIENT_PLACEHOLDER -->\n"
    html += footer(ctx_list[-1])
    html += theme_script(ctx_list[-1])
    html += "\n</body>\n</html>\n"
    return html


def head(ctx):
    loc = ctx['loc']
    mo = ctx['mo']
    return f'''<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{loc['short_name']} &middot; Performance Report &middot; {mo['month_name']} {mo['year']}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Source+Serif+Pro:wght@400;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
{CSS}
  </style>
</head>
<body>
<div class="print-frame"></div>
'''


def topbar(ctx):
    loc = ctx['loc']
    mo = ctx['mo']
    return f'''
<div class="topbar">
  <div class="topbar-inner">
    <div class="brand">
      <div class="brand-mark"></div>
      <div class="brand-text">
        {loc['short_name']} &middot; Studio Pulse
        <small>Performance Report &middot; {mo['month_name']} {mo['year']}</small>
      </div>
    </div>
    <button class="theme-toggle" id="theme-toggle" aria-label="Toggle theme">
      <svg id="theme-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="4"></circle>
        <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"></path>
      </svg>
      <span id="theme-label">Dark</span>
    </button>
  </div>
</div>
'''


def hero(ctx):
    loc = ctx['loc']
    mo = ctx['mo']
    s = ctx['sales']
    sess = ctx['sessions']

    # KPI cards
    net_val = lakh(s['net'])
    gross_val = lakh(s['gross'])
    disc_val = lakh(s['disc'])
    visits_val = fmt_int(sess['visits'])
    fill_val = pct(sess['fill'])
    conv_val = pct(ctx['new']['rate'])
    lapsed_val = fmt_int(ctx['lapsed']['lapsed'])
    disc_eff_val = f"&#8377;{s['disc_eff']:.2f}"

    available_months = sorted(m for m in DATA.get('meta', {}).get('months', []) if m <= ctx['month_key'])[-12:]

    def history(getter, field):
        return [(month, float(getter(ctx['loc_key'], month).get(field, 0) or 0)) for month in available_months]

    return f'''
<section class="hero">
  <div class="container hero-content">
    <div class="hero-eyebrow">
      <span class="dot">{loc['brand_mark']}</span>
      Senior Management Review &middot; Period: {mo['period_short']}
    </div>
    <h1>
      {loc['short_name']} <span class="accent-word">studio performance</span><br>
      for <span class="accent-yellow">{mo['month_name']} {mo['year']}</span> &mdash; operational rhythm, funnel economics, and the lapsed-member question.
    </h1>
    <p class="hero-sub">
      A data-led review of the studio&rsquo;s commercial and operational performance in {mo['month_name']} {mo['year']}, benchmarked against {mo['prev_month_name']} {mo['prev_year']}
      and the <strong>{ctx['baseline_label']} baseline</strong>.
      Every section is structured to surface a business decision &mdash; class schedule, trainer deployment, discount discipline,
      and membership retention &mdash; that senior management can act on this quarter.
    </p>

    <div class="hero-meta">
      <div class="hero-meta-item">
        <span class="label">Location</span>
        <span class="value">{loc['full_name']}</span>
      </div>
      <div class="hero-meta-item">
        <span class="label">Period</span>
        <span class="value">{mo['date_range']}</span>
      </div>
      <div class="hero-meta-item">
        <span class="label">Reporting basis</span>
        <span class="value">Net Sales &middot; {sess['sessions']} sessions &middot; {s['members']} unique buyers</span>
      </div>
      <div class="hero-meta-item">
        <span class="label">Comparators</span>
        <span class="value">{mo['prev_month_name']} {mo['prev_year']} &middot; {ctx['baseline_label']} avg &middot; YoY</span>
      </div>
      <div class="hero-meta-item">
        <span class="label">Audience</span>
        <span class="value">Senior Management &middot; Board Review</span>
      </div>
    </div>

    <div class="hero-kpi-grid">
      {kpi_card("Net Sales", net_val, f"Gross {gross_val} &middot; Disc {disc_val}",
                ctx['net_mom'], ctx['net_yoy'], ctx['net_baseline'], higher_is_better=True, chart_values=history(get_sales, 'net'))}
      {kpi_card("Visits", visits_val, f"Across {sess['sessions']} sessions",
                ctx['visits_mom'], "n/a", ctx['visits_baseline'], higher_is_better=True, chart_values=history(get_sessions, 'visits'))}
      {kpi_card("Fill Rate", fill_val, "Capacity utilization",
                ctx['fill_mom'], "n/a", ctx['fill_baseline'], higher_is_better=True, is_pp=True, chart_values=history(get_sessions, 'fill'))}
      {kpi_card("Conversion Rate", conv_val, f"{ctx['new']['trials']} trials &rarr; {ctx['new']['converted']} converted",
                ctx['conv_mom'], "n/a", ctx['conv_baseline'], higher_is_better=True, is_pp=True, chart_values=history(get_new, 'rate'))}
      {kpi_card("Lapsed Members", lapsed_val, f"Churn rate {pct(ctx['lapsed']['churn'])}",
                ctx['lapsed_mom'], "n/a", "Active retention work", higher_is_better=False, chart_values=history(get_lapsed, 'lapsed'))}
      {kpi_card("Discount Efficiency", disc_eff_val, "Revenue collected / &#8377;1 discounted",
                ctx['disc_eff_mom'], ctx['disc_eff_yoy'], ctx['disc_eff_baseline'], higher_is_better=True, chart_values=history(get_sales, 'disc_eff'))}
    </div>
  </div>
</section>
'''


def kpi_card(label, value, sub, mom, yoy, baseline_text, higher_is_better=True, is_pp=False, chart_values=None):
    """Generate an accessible two-sided KPI card with comparative context."""
    mom_b = badge(mom, higher_is_better) if not is_pp else badge_from_pp(mom, higher_is_better)
    yoy_b = badge(yoy, higher_is_better) if not is_pp else badge_from_pp(yoy, higher_is_better)

    def comparison_description(period, change):
        if change == 'n/a':
            return f"{period} comparison is unavailable for this reporting period."
        direction = 'improved' if change.startswith('+') else 'declined' if change.startswith('-') else 'was unchanged'
        if not higher_is_better and direction != 'was unchanged':
            implication = 'This reduces operating risk.' if direction == 'declined' else 'This increases operating risk.'
        else:
            implication = 'This is positive momentum.' if direction == 'improved' else 'This needs attention.' if direction == 'declined' else 'Performance is stable.'
        unit = ' percentage points' if is_pp else ''
        return f"Performance {direction} by {change}{unit} versus {period}. {implication}"

    icons = {
        'Net Sales': '<path d="M5 8h14M7 5h10M8 12c0 2 1.8 3.5 4 3.5s4-1.5 4-3.5-1.8-3.5-4-3.5S8 7 8 5"/>',
        'Visits': '<path d="M16 20v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 10a4 4 0 1 0 0-8 4 4 0 0 0 0 8M22 20v-2a4 4 0 0 0-3-3.87M16 2.13a4 4 0 0 1 0 7.75"/>',
        'Fill Rate': '<path d="M4 19V5M4 19h16M8 16v-5M12 16V8M16 16V4"/>',
        'Conversion Rate': '<path d="M3 12h13M12 7l5 5-5 5M21 5v14"/>',
        'Lapsed Members': '<path d="M12 8v4l3 2M21 12a9 9 0 1 1-3-6.7M21 3v6h-6"/>',
        'Discount Efficiency': '<path d="M19 5 5 19M7 5h.01M17 19h.01M7 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6M17 22a3 3 0 1 0 0-6 3 3 0 0 0 0 6"/>',
    }
    icon = icons.get(label, '<path d="M4 19V5M4 19h16M8 15l3-3 3 2 5-7"/>')
    chart_values = chart_values or []
    chart_max = max((point[1] for point in chart_values), default=0)
    bar_heights = [max(8, value / chart_max * 94) if chart_max else 8 for _, value in chart_values]
    bars = ''.join(
        f'<span class="kpi-bar-column{(" is-current" if i == len(bar_heights) - 1 else "")}" '
        f'title="{chart_values[i][0]}: {chart_values[i][1]:,.1f}"><i style="--height:{height:.1f}%"></i>'
        f'<small>{datetime.strptime(chart_values[i][0], "%Y-%m").strftime("%b")[0]}</small></span>'
        for i, height in enumerate(bar_heights)
    )

    return f'''        <article class="kpi-card" role="button" tabindex="0" aria-pressed="false" aria-label="{label}: {value}. Flip for growth details">
          <div class="kpi-card-inner">
            <div class="kpi-card-face kpi-card-front">
              <div class="kpi-ambient" aria-hidden="true"><span></span><span></span><span></span></div>
              <div class="kpi-front-header">
                <div class="kpi-title-lockup"><span class="kpi-icon" aria-hidden="true"><svg viewBox="0 0 24 24">{icon}</svg></span><div class="kpi-label">{label}</div></div>
                <div class="kpi-value">{value}</div>
              </div>
              <div class="kpi-front-body">
                <div class="kpi-chart-heading"><span>12-month trend</span><strong>{chart_values[0][0] if chart_values else ''} &ndash; {chart_values[-1][0] if chart_values else ''}</strong></div>
                <div class="kpi-mini-chart" role="img" aria-label="12-month bar chart for {label}">{bars}</div>
              </div>
              <div class="kpi-card-action">View growth details <span aria-hidden="true">&rarr;</span></div>
            </div>
            <div class="kpi-card-face kpi-card-back">
              <div class="kpi-back-header"><span>{label}</span><b aria-hidden="true">&times;</b></div>
              <p class="kpi-back-description">{sub}</p>
              <div class="kpi-comparison">
                <div class="kpi-comparison-top"><span>MoM</span><strong class="badge {mom_b}">{mom}</strong></div>
                <p>{comparison_description('last month', mom)}</p>
              </div>
              <div class="kpi-comparison">
                <div class="kpi-comparison-top"><span>YoY</span><strong class="badge {yoy_b if yoy != 'n/a' else 'neutral'}">{yoy}</strong></div>
                <p>{comparison_description('last year', yoy)}</p>
              </div>
              <div class="kpi-benchmark" title="{baseline_text}"><span>Benchmark</span><strong>{baseline_text}</strong></div>
              <div class="kpi-card-action">Back <span aria-hidden="true">&larr;</span></div>
            </div>
          </div>
        </article>'''


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


def footer(ctx):
    loc = ctx['loc']
    mo = ctx['mo']
    s = ctx['sales']
    sess = ctx['sessions']
    return f'''

<footer class="footer">
  <div class="container">
    <div class="footer-grid">
      <div>
        <div class="footer-brand-text">{loc['short_name']} &middot; Studio Pulse</div>
        <p class="footer-text">
          Performance Report &middot; {mo['month_name']} {mo['year']}<br>
          Compiled from studio sales, sessions, leads, membership, and check-in records.<br>
          Net Sales excludes tax; Gross Sales reflects amount collected per transaction.
          Compared against the {ctx['baseline_label']} baseline.
        </p>
      </div>
      <div>
        <div class="footer-label">Contents</div>
        <p class="footer-text">
          01 Executive Summary<br>
          02 Revenue &amp; Sales Performance<br>
          03 New Client Conversion Funnel<br>
          04 Sessions &amp; Class Performance<br>
          05 Lapsed Memberships Deep Dive<br>
          06 Strategic Recommendations<br>
          07 Predictions &amp; Forward View
        </p>
      </div>
      <div>
        <div class="footer-label">Headline Metrics</div>
        <p class="footer-text">
          Net Sales: {lakh(s['net'])}<br>
          Visits: {fmt_int(sess['visits'])}<br>
          Fill Rate: {pct(sess['fill'])}<br>
          Conversion: {pct(ctx['leads']['rate'])}<br>
          Churn Rate: {pct(ctx['lapsed']['churn'])}<br>
          Discount Penetration: {pct(ctx['disc_penetration'])}
        </p>
      </div>
    </div>
  </div>
</footer>
'''


def theme_script(ctx):
    return '''

<script>
(function() {
  /* ─── Theme Toggle ─────────────────────────────────────────── */
  const root = document.documentElement;
  const toggle = document.getElementById('theme-toggle');
  const label = document.getElementById('theme-label');
  const icon = document.getElementById('theme-icon');

  const saved = localStorage.getItem('kh-theme') || 'dark';
  applyTheme(saved);

  if (toggle) toggle.addEventListener('click', () => {
    const current = root.getAttribute('data-theme') || 'dark';
    const next = current === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    localStorage.setItem('kh-theme', next);
  });

  function applyTheme(theme) {
    root.setAttribute('data-theme', theme);
    if (!label || !icon) return;
    if (theme === 'dark') {
      label.textContent = 'Light';
      icon.innerHTML = '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>';
    } else {
      label.textContent = 'Dark';
      icon.innerHTML = '<circle cx="12" cy="12" r="4"></circle><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"></path>';
    }
  }

  /* ─── Reading Progress Bar ─────────────────────────────────── */
  const progressBar = document.createElement('div');
  progressBar.className = 'reading-progress';
  progressBar.style.width = '0%';
  document.body.appendChild(progressBar);

  function updateProgress() {
    const scrollTop = window.scrollY;
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    const pct = docHeight > 0 ? Math.min(100, (scrollTop / docHeight) * 100) : 0;
    progressBar.style.width = pct + '%';
  }

  /* ─── Scroll-Triggered Section Animations ──────────────────── */
  const sections = document.querySelectorAll('.report-section');
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
      }
    });
  }, { threshold: 0.08, rootMargin: '0px 0px -60px 0px' });

  sections.forEach(sec => observer.observe(sec));

  /* ─── Quick Navigation Bar ──────────────────────────────────── */
  const sectionLabels = [
    { id: 'executive-summary', label: 'Executive Summary', short: '01' },
    { id: 'revenue-performance', label: 'Revenue', short: '02' },
    { id: 'conversion-funnel', label: 'Conversion', short: '03' },
    { id: 'sessions', label: 'Sessions', short: '04' },
    { id: 'lapsed', label: 'Lapsed', short: '05' },
    { id: 'recommendations', label: 'Recommendations', short: '06' },
    { id: 'predictions', label: 'Predictions', short: '07' }
  ];

  const quickNav = document.createElement('nav');
  quickNav.className = 'quick-nav-bar';
  quickNav.setAttribute('aria-label', 'Quick navigation');

  // Add progress indicator
  const progressDiv = document.createElement('div');
  progressDiv.className = 'quick-nav-progress';
  const progressFill = document.createElement('div');
  progressFill.className = 'quick-nav-progress-fill';
  progressDiv.appendChild(progressFill);
  quickNav.appendChild(progressDiv);

  sectionLabels.forEach((sec, i) => {
    const navItem = document.createElement('button');
    navItem.className = 'quick-nav-item';
    navItem.setAttribute('data-section', sec.short);
    navItem.setAttribute('data-target', sec.id);
    navItem.setAttribute('aria-label', 'Jump to ' + sec.label);

    const tooltip = document.createElement('span');
    tooltip.className = 'quick-nav-tooltip';
    tooltip.textContent = sec.label;
    navItem.appendChild(tooltip);

    navItem.addEventListener('click', () => {
      const target = document.getElementById(sec.id);
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });

    quickNav.appendChild(navItem);
  });

  document.body.appendChild(quickNav);

  function updateActiveNav() {
    const navItems = quickNav.querySelectorAll('.quick-nav-item');
    let activeIdx = 0;
    sections.forEach((sec, i) => {
      const rect = sec.getBoundingClientRect();
      if (rect.top <= window.innerHeight * 0.4) activeIdx = i;
    });
    navItems.forEach((item, i) => item.classList.toggle('active', i === activeIdx));

    // Update progress fill
    const scrollTop = window.scrollY;
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    const pct = docHeight > 0 ? Math.min(100, (scrollTop / docHeight) * 100) : 0;
    progressFill.style.height = pct + '%';
  }

  /* ─── Drill-Down Functionality ──────────────────────────────── */
  function initDrillDown() {
    const tables = document.querySelectorAll('.data-table:not(.heatmap-table):not(.mom-table)');

    tables.forEach(table => {
      const rows = table.querySelectorAll('tbody tr:not(.totals-row):not(.drill-down-detail)');

      rows.forEach(row => {
        // Only add drill-down to rows with meaningful data
        const cells = row.querySelectorAll('td');
        if (cells.length < 3) return;

        // Add drill-down class
        row.classList.add('drill-down-row');

        // Create detail row
        const detailRow = document.createElement('tr');
        detailRow.className = 'drill-down-detail';
        const detailCell = document.createElement('td');
        detailCell.colSpan = cells.length;

        // Build drill-down content from row data
        const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent.trim());
        const drillContent = document.createElement('div');
        drillContent.className = 'drill-down-content';

        cells.forEach((cell, idx) => {
          if (idx === 0) return; // Skip first column (label)
          const header = headers[idx] || 'Metric ' + idx;
          const value = cell.textContent.trim();

          if (value && value !== '—' && value !== 'n/a') {
            const metric = document.createElement('div');
            metric.className = 'drill-down-metric';
            metric.innerHTML = `<span class="drill-down-metric-label">${header}</span><span class="drill-down-metric-value">${value}</span>`;
            drillContent.appendChild(metric);
          }
        });

        // Add context-aware insights
        const insights = document.createElement('div');
        insights.className = 'drill-down-metric drill-down-insight';
        insights.style.flex = '1 1 100%';
        insights.style.background = 'var(--primary-soft)';
        insights.style.borderLeft = '3px solid var(--primary)';
        insights.style.marginTop = 'var(--space-2)';

        const rowLabel = cells[0]?.textContent.trim() || '';
        insights.innerHTML = `<span class="drill-down-metric-label">💡 Insight</span><span class="drill-down-metric-value" style="font-size:12px;font-family:var(--font-sans)">Click to expand detailed analytics for ${rowLabel}</span>`;
        drillContent.appendChild(insights);

        detailCell.appendChild(drillContent);
        detailRow.appendChild(detailCell);

        // Insert detail row after current row
        row.parentNode.insertBefore(detailRow, row.nextSibling);

        // Add click handler
        row.addEventListener('click', () => {
          row.classList.toggle('expanded');
          detailRow.classList.toggle('visible');
        });
      });
    });
  }

  /* ─── Mobile Table Card View ───────────────────────────────── */
  if (window.innerWidth <= 768) {
    document.querySelectorAll('table.data-table').forEach(table => {
      if (table.closest('.heatmap-table')) return;
      table.classList.add('mobile-cards');
      const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent.trim());
      table.querySelectorAll('tbody td').forEach(td => {
        const idx = Array.from(td.parentNode.children).indexOf(td);
        if (headers[idx]) td.setAttribute('data-label', headers[idx]);
      });
    });
  }

  /* ─── Unified Scroll Handler ───────────────────────────────── */
  let scrollTicking = false;
  window.addEventListener('scroll', () => {
    if (!scrollTicking) {
      window.requestAnimationFrame(() => {
        updateProgress();
        updateActiveNav();
        scrollTicking = false;
      });
      scrollTicking = true;
    }
  }, { passive: true });

  updateProgress();
  updateActiveNav();

  // Initialize drill-down after DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDrillDown);
  } else {
    initDrillDown();
  }
})();
</script>

<!-- AI Copilot Button -->
<button id="ai-copilot-btn" aria-label="AI Data Copilot">
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <path d="M12 2L2 7l10 5 10-5-10-5z"/>
    <path d="M2 17l10 5 10-5"/>
    <path d="M2 12l10 5 10-5"/>
  </svg>
</button>

<!-- AI Copilot Modal -->
<div id="ai-copilot-backdrop" aria-hidden="true"></div>
<div id="ai-copilot-modal" role="dialog" aria-modal="true" aria-label="AI Data Copilot">
  <div class="copilot-header">
    <h3>🤖 AI Data Copilot</h3>
    <button id="ai-copilot-close" aria-label="Close">&times;</button>
  </div>
  <div class="copilot-modes" role="tablist" aria-label="Copilot mode">
    <button class="copilot-mode-btn is-active" id="copilot-mode-build" data-mode="build" role="tab" aria-selected="true">Build</button>
    <button class="copilot-mode-btn" id="copilot-mode-chat" data-mode="chat" role="tab" aria-selected="false">Chat</button>
    <span class="copilot-scope" id="copilot-scope"></span>
  </div>
  <div class="copilot-body">
    <p class="copilot-hint" id="copilot-hint"></p>
    <div id="ai-copilot-transcript" hidden></div>
    <textarea id="ai-copilot-input" placeholder="Describe the table or KPI you want..."></textarea>
    <div class="copilot-actions">
      <button id="ai-copilot-send">Build element</button>
      <button id="ai-copilot-clear" class="copilot-ghost-btn" title="Clear this conversation">Clear</button>
    </div>
    <div id="ai-copilot-output"></div>
  </div>
</div>

<script>
// MoM Toggle Table
function toggleMoMTable(sectionId) {
  const container = document.getElementById('mom-table-' + sectionId);
  if (!container) return;
  const btn = container.closest('.mom-toggle-wrapper')?.querySelector('.mom-toggle-btn, .mom-toggle')
    || container.previousElementSibling;

  // The wrapper is collapsed with `max-height: 0`, so the .expanded class has to
  // land on the CONTAINER (not just the button) or nothing becomes visible.
  const isExpanded = container.classList.contains('expanded')
    || (container.style.display !== 'none' && container.style.maxHeight !== '0px');

  if (isExpanded) {
    container.classList.remove('expanded');
    container.style.display = 'none';
  } else {
    container.classList.add('expanded');
    container.style.display = 'block';
    container.style.maxHeight = 'none';
  }
  btn?.setAttribute('aria-expanded', String(!isExpanded));
  btn?.classList.toggle('expanded', !isExpanded);
}

/* ─── MoM grid: metric tabs, month range, per-cell analytics ─────── */
function momFmtValue(v, fmt) {
  if (v === null || v === undefined || isNaN(v)) return '\u2014';
  if (fmt === 'pct') return (Math.round(v * 10) / 10).toFixed(1) + '%';
  if (fmt === 'num') return v.toFixed(2);
  if (fmt === 'money') {
    var a = Math.abs(v);
    if (a >= 1e7) return '\u20b9' + (v / 1e7).toFixed(2) + 'Cr';
    if (a >= 1e5) return '\u20b9' + (v / 1e5).toFixed(2) + 'L';
    return '\u20b9' + Math.round(v).toLocaleString('en-IN');
  }
  return Math.round(v).toLocaleString('en-IN');
}

function momFmtDelta(cur, prev, fmt) {
  if (prev === null || prev === undefined || isNaN(prev) || !prev) return '\u2014';
  // Rate metrics are stored as percentages already, so their movement is in
  // percentage points; everything else is a relative change.
  var d = fmt === 'pct' ? (cur - prev) : (cur - prev) / Math.abs(prev) * 100;
  var txt = (d >= 0 ? '+' : '') + d.toFixed(1);
  return txt + (fmt === 'pct' ? 'pp' : '%');
}

function momCellDrill(container, cell) {
  var panel = container.querySelector('.mom-drill-panel');
  if (!panel) return;
  var body = cell.closest('tbody');
  var row = cell.closest('tr');
  var fmt = cell.dataset.fmt || 'int';
  var metric = body ? body.dataset.metric : '';

  container.querySelectorAll('.mom-cell.is-selected').forEach(function (c) { c.classList.remove('is-selected'); });
  cell.classList.add('is-selected');

  var cells = Array.prototype.slice.call(row.querySelectorAll('td.mom-cell[data-v]'))
    .filter(function (c) { return !c.hidden && c.dataset.v !== ''; });
  var entries = cells.map(function (c) { return { month: c.dataset.month, v: Number(c.dataset.v) }; })
    .filter(function (e) { return !isNaN(e.v); });
  if (!entries.length) return;

  var cur = Number(cell.dataset.v);
  var i = entries.findIndex(function (e) { return e.month === cell.dataset.month; });
  var prev = i > 0 ? entries[i - 1].v : null;
  var vals = entries.map(function (e) { return e.v; });
  var total = vals.reduce(function (a, b) { return a + b; }, 0);
  var mean = total / vals.length;
  var best = entries.reduce(function (a, b) { return b.v > a.v ? b : a; });
  var worst = entries.reduce(function (a, b) { return b.v < a.v ? b : a; });
  var rank = vals.slice().sort(function (a, b) { return b - a; }).indexOf(cur) + 1;
  var spread = mean ? Math.abs(best.v - worst.v) / Math.abs(mean) * 100 : 0;

  function tile(label, value, note) {
    return '<div class="drill-down-metric">' +
      '<span class="drill-down-metric-label">' + label + '</span>' +
      '<span class="drill-down-metric-value">' + value + '</span>' +
      (note ? '<span class="drill-down-metric-label">' + note + '</span>' : '') +
      '</div>';
  }

  var html = '<div class="drill-down-content">' +
    tile(metric || 'Value', momFmtValue(cur, fmt), cell.dataset.month) +
    tile('vs previous month', momFmtDelta(cur, prev, fmt), prev === null ? 'first month shown' : 'vs ' + entries[i - 1].month) +
    tile('Rank in window', rank + ' of ' + entries.length, 'highest = 1') +
    (fmt === 'pct' ? '' : tile('Share of window', (total ? (cur / total * 100) : 0).toFixed(1) + '%', 'of ' + entries.length + ' months')) +
    tile('Window average', momFmtValue(mean, fmt), fmt === 'pct' ? entries.length + ' months' : momFmtValue(total, fmt) + ' total') +
    tile('Highest', momFmtValue(best.v, fmt), best.month) +
    tile('Lowest', momFmtValue(worst.v, fmt), worst.month) +
    '<div class="drill-down-metric drill-down-insight" style="flex:1 1 100%;margin-top:var(--space-2);border-left:3px solid var(--primary);background:var(--primary-soft);padding:8px 14px">' +
    '<span class="drill-down-metric-label">Analytics</span>' +
    '<span class="drill-down-metric-value" style="font-size:12px;font-family:var(--font-sans);font-weight:500">' +
    (metric || 'Metric') + ' in ' + cell.dataset.month + ' is ' + momFmtValue(cur, fmt) +
    (prev !== null ? ', ' + momFmtDelta(cur, prev, fmt) + ' against ' + entries[i - 1].month : '') +
    '. It ranks ' + rank + ' of ' + entries.length + ' months in view and sits ' +
    (cur >= mean ? (mean ? ((cur / mean - 1) * 100).toFixed(1) : '0') + '% above' : ((1 - cur / mean) * 100).toFixed(1) + '% below') +
    ' the window average of ' + momFmtValue(mean, fmt) +
    '. Spread between best and worst is ' + spread.toFixed(0) + '% of the mean \u2014 ' +
    (spread < 15 ? 'a tight, predictable band.' : spread > 40 ? 'a wide swing, so treat single months with care.' : 'moderate month-to-month variation.') +
    '</span></div></div>';

  panel.innerHTML = html;
  panel.hidden = false;
}

function initMoMGrids() {
  document.querySelectorAll('.mom-table-container').forEach(function (container) {
    var panels = Array.prototype.slice.call(container.querySelectorAll('tbody.mom-panel'));
    if (!panels.length) return;

    function clearDrill() {
      var drill = container.querySelector('.mom-drill-panel');
      if (drill) { drill.hidden = true; drill.innerHTML = ''; }
      container.querySelectorAll('.mom-cell.is-selected').forEach(function (c) { c.classList.remove('is-selected'); });
    }

    container.querySelectorAll('.mom-metric-tab').forEach(function (tab) {
      tab.addEventListener('click', function () {
        container.querySelectorAll('.mom-metric-tab').forEach(function (t) { t.classList.remove('is-active'); });
        panels.forEach(function (p) { p.classList.remove('is-active'); });
        tab.classList.add('is-active');
        var target = document.getElementById(tab.dataset.panel);
        if (target) target.classList.add('is-active');
        clearDrill();
      });
    });

    function applyRange(range) {
      var heads = container.querySelectorAll('thead th[data-col]');
      var total = heads.length;
      var keep = range === 'all' ? total : Math.min(parseInt(range, 10) || 12, total);
      var first = total - keep;
      container.querySelectorAll('[data-col]').forEach(function (cell) {
        cell.hidden = Number(cell.dataset.col) < first;
      });
      clearDrill();
    }

    container.querySelectorAll('.mom-range-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        container.querySelectorAll('.mom-range-btn').forEach(function (b) { b.classList.remove('is-active'); });
        btn.classList.add('is-active');
        container.dataset.range = btn.dataset.range;
        applyRange(btn.dataset.range);
      });
    });
    applyRange(container.dataset.range || '12');

    container.querySelectorAll('td.mom-cell[data-v]').forEach(function (cell) {
      cell.addEventListener('click', function () { momCellDrill(container, cell); });
    });
  });
}


// The MoM grid lives in a later script block, so wire it up from here.
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initMoMGrids);
} else {
  initMoMGrids();
}

// Multi-Location Tabs
document.addEventListener('DOMContentLoaded', () => {
  const tabs = document.querySelectorAll('.location-tab');
  const contents = document.querySelectorAll('.location-content');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const targetId = tab.dataset.location;

      tabs.forEach(t => t.classList.remove('active'));
      contents.forEach(c => c.classList.remove('active'));

      tab.classList.add('active');
      document.getElementById('location-' + targetId)?.classList.add('active');
    });
  });

  // Activate first tab by default
  if (tabs.length > 0 && !document.querySelector('.location-tab.active')) {
    tabs[0].click();
  }

  // AI Copilot — two modes: Build (an element for the report) and Chat (Q&A)
  const copilotBtn = document.getElementById('ai-copilot-btn');
  const copilotModal = document.getElementById('ai-copilot-modal');
  const copilotBackdrop = document.getElementById('ai-copilot-backdrop');
  const copilotClose = document.getElementById('ai-copilot-close');
  const copilotInput = document.getElementById('ai-copilot-input');
  const copilotSend = document.getElementById('ai-copilot-send');
  const copilotClear = document.getElementById('ai-copilot-clear');
  const copilotOutput = document.getElementById('ai-copilot-output');
  const copilotTranscript = document.getElementById('ai-copilot-transcript');
  const copilotHint = document.getElementById('copilot-hint');
  let copilotMode = 'build';

  function openCopilot() {
    copilotModal.classList.add('active');
    copilotBackdrop.classList.add('active');
    copilotInput.focus();
  }

  // Escape, and any click that lands outside the panel, shut it immediately.
  function closeCopilot() {
    copilotModal.classList.remove('active');
    copilotBackdrop.classList.remove('active');
  }

  copilotBtn?.addEventListener('click', (e) => {
    e.stopPropagation();
    if (copilotModal.classList.contains('active')) closeCopilot();
    else openCopilot();
  });

  copilotClose?.addEventListener('click', closeCopilot);
  copilotBackdrop?.addEventListener('mousedown', closeCopilot);
  document.addEventListener('mousedown', (e) => {
    if (!copilotModal.classList.contains('active')) return;
    if (copilotModal.contains(e.target) || (copilotBtn && copilotBtn.contains(e.target))) return;
    closeCopilot();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && copilotModal.classList.contains('active')) {
      e.preventDefault();
      closeCopilot();
    }
  });

  const COPILOT_HINTS = {
    build: 'Describe the table, KPI or breakdown you want. It is computed from the uploaded data and can be saved straight into a section of this report.',
    chat: 'Ask anything about this report\u2019s data. Answers come from the analysis file for this upload, with the supporting table and follow-ups you can click.',
  };

  function setCopilotMode(mode) {
    copilotMode = mode === 'chat' ? 'chat' : 'build';
    document.querySelectorAll('.copilot-mode-btn').forEach((b) => {
      const on = b.dataset.mode === copilotMode;
      b.classList.toggle('is-active', on);
      b.setAttribute('aria-selected', String(on));
    });
    copilotHint.textContent = COPILOT_HINTS[copilotMode];
    copilotSend.textContent = copilotMode === 'chat' ? 'Ask' : 'Build element';
    copilotInput.placeholder = copilotMode === 'chat'
      ? 'Ask a question about this month\u2019s data...'
      : 'Describe the table or KPI you want...';
    copilotTranscript.hidden = copilotMode !== 'chat';
    copilotOutput.innerHTML = '';
  }

  document.querySelectorAll('.copilot-mode-btn').forEach((b) => {
    b.addEventListener('click', () => setCopilotMode(b.dataset.mode));
  });
  setCopilotMode('build');
  const ctxNow = window.__REPORT_CTX__ || {};
  const scopeEl = document.getElementById('copilot-scope');
  if (scopeEl && ctxNow.locName) scopeEl.textContent = ctxNow.locName + ' \u00b7 ' + (ctxNow.monthLabel || '');

  copilotClear?.addEventListener('click', () => {
    copilotOutput.innerHTML = '';
    if (copilotTranscript) copilotTranscript.innerHTML = '';
    copilotInput.value = '';
  });

  copilotSend?.addEventListener('click', async () => {
    const prompt = copilotInput.value.trim();
    if (!prompt) return;

    copilotSend.disabled = true;
    copilotSend.textContent = 'Analyzing...';
    copilotOutput.innerHTML = '<div class="copilot-loading">Processing your request...</div>';

    try {
      const sessionId = window.location.pathname.split('/')[2];
      const ctx = window.__REPORT_CTX__ || {};
      const response = await fetch('/ai-copilot/' + sessionId, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, loc: ctx.loc, month: ctx.month, mode: copilotMode })
      });

      const result = await response.json();
      renderCopilotResult(result, prompt);
    } catch (err) {
      copilotOutput.innerHTML = '<div class="copilot-error">Error: ' + err.message + '</div>';
    }

    copilotSend.disabled = false;
    copilotSend.textContent = 'Analyze Data';
  });

  copilotInput?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      copilotSend.click();
    }
  });

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  }

  function renderTable(rows) {
    if (!Array.isArray(rows) || !rows.length) return '';
    const cols = Object.keys(rows[0]);
    let out = '<div class="copilot-table-wrap"><table class="data-table"><thead><tr>';
    cols.forEach((c) => { out += '<th>' + esc(c) + '</th>'; });
    out += '</tr></thead><tbody>';
    rows.slice(0, 25).forEach((row) => {
      out += '<tr>';
      cols.forEach((c) => { out += '<td>' + esc(row[c]) + '</td>'; });
      out += '</tr>';
    });
    out += '</tbody></table></div>';
    if (rows.length > 25) out += '<p class="copilot-note">' + (rows.length - 25) + ' more rows not shown.</p>';
    return out;
  }

  /* Chat mode: a transcript of question / answer turns, with follow-up chips. */
  function renderChatTurn(result, prompt) {
    const turn = document.createElement('div');
    turn.className = 'copilot-turn';
    let html = '<div class="copilot-user-line">' + esc(prompt) + '</div>';
    html += '<div class="copilot-answer">';
    html += '<div class="copilot-answer-title">' + esc(result.title || 'Answer') + '</div>';
    html += '<div class="copilot-answer-body">' + esc(result.answer || result.description || '') + '</div>';
    if (result.kpi) {
      html += '<div class="kpi-cards"><div class="kpi-card">' +
        '<div class="kpi-label">' + esc(result.kpi.label || 'Metric') + '</div>' +
        '<div class="kpi-value">' + esc(result.kpi.value || '\u2014') + '</div>' +
        (result.kpi.change ? '<div class="kpi-change">' + esc(result.kpi.change) + '</div>' : '') +
        '</div></div>';
    }
    if (result.table && Array.isArray(result.table.data)) html += renderTable(result.table.data);
    if (result.confidence) {
      html += '<div class="copilot-meta">Answered from this upload\u2019s analysis file \u00b7 confidence: ' + esc(result.confidence) + '</div>';
    }
    if (Array.isArray(result.followUps) && result.followUps.length) {
      html += '<div class="copilot-chips">';
      result.followUps.forEach((f) => {
        html += '<button class="copilot-chip" data-q="' + esc(f) + '">' + esc(f) + '</button>';
      });
      html += '</div>';
    }
    html += '</div>';
    turn.innerHTML = html;
    turn.querySelectorAll('.copilot-chip').forEach((chip) => {
      chip.addEventListener('click', () => {
        copilotInput.value = chip.dataset.q;
        copilotSend.click();
      });
    });
    copilotTranscript.hidden = false;
    copilotTranscript.appendChild(turn);
    copilotTranscript.scrollTop = copilotTranscript.scrollHeight;
  }

  function renderCopilotResult(result, prompt) {
    if (result && (result.type === 'chat' || copilotMode === 'chat')) {
      renderChatTurn(result, prompt);
      return;
    }
    let html = '<div class="copilot-result">';
    html += '<div class="copilot-prompt">' + prompt + '</div>';

    if (result.type === 'table' && Array.isArray(result.data)) {
      html += '<h4>' + (result.title || 'Data Table') + '</h4>';
      if (result.data.length > 0) {
        const cols = Object.keys(result.data[0]);
        html += '<table class="data-table"><thead><tr>';
        cols.forEach(col => html += '<th>' + col + '</th>');
        html += '</tr></thead><tbody>';
        result.data.slice(0, 20).forEach(row => {
          html += '<tr>';
          cols.forEach(col => html += '<td>' + (row[col] || '') + '</td>');
          html += '</tr>';
        });
        html += '</tbody></table>';
      }
    } else if (result.type === 'kpi' && result.data) {
      html += '<div class="kpi-cards">';
      html += '<div class="kpi-card">';
      html += '<div class="kpi-label">' + (result.data.label || 'Metric') + '</div>';
      html += '<div class="kpi-value">' + (result.data.value || '—') + '</div>';
      if (result.data.change) {
        html += '<div class="kpi-change ' + (result.data.change.startsWith('+') ? 'positive' : 'negative') + '">' + result.data.change + '</div>';
      }
      html += '</div></div>';
    } else if (result.type === 'chart') {
      html += '<div class="chart-placeholder">Chart visualization would render here</div>';
    } else {
      html += '<div class="copilot-text">' + (result.data || result.description || 'No data') + '</div>';
    }

    if (result.description) {
      html += '<div class="copilot-description">' + result.description + '</div>';
    }

    // Build mode: pick the section and drop the element straight in.
    html += '<div class="copilot-save-row">' +
      '<select class="copilot-section-select" aria-label="Section to add this to">' +
      '<option value="">Add to section\u2026</option>' +
      '<option value="1">1 — Executive summary</option>' +
      '<option value="2">2 — Revenue performance</option>' +
      '<option value="3">3 — Conversion funnel</option>' +
      '<option value="4">4 — Sessions</option>' +
      '<option value="5">5 — Lapsed members</option>' +
      '<option value="6">6 — Recommendations</option>' +
      '<option value="7">7 — Predictions</option>' +
      '</select>' +
      '<button class="copilot-save-btn" onclick="saveCopilotResult(this)">Save to Report</button>' +
      '</div>';
    html += '</div>';

    copilotOutput.innerHTML = html;
    const sel = copilotOutput.querySelector('.copilot-section-select');
    const saveBtn = copilotOutput.querySelector('.copilot-save-btn');
    sel?.addEventListener('change', () => {
      saveBtn.dataset.section = sel.value;
      saveBtn.disabled = !sel.value;
    });
    if (saveBtn) saveBtn.disabled = true;
  }
});

function saveCopilotResult(btn) {
  const result = btn.closest('.copilot-result');
  const section = btn.dataset.section || prompt('Which section? (1=Executive, 2=Revenue, 3=Funnel, 4=Sessions, 5=Lapsed, 6=Recommendations, 7=Predictions)');
  if (!section) return;

  const savedElement = document.createElement('div');
  savedElement.className = 'saved-copilot-element';
  savedElement.innerHTML = result.innerHTML;
  savedElement.querySelector('.copilot-save-btn')?.remove();

  const sectionMap = {
    '1': 'executive-summary',
    '2': 'revenue-performance',
    '3': 'conversion-funnel',
    '4': 'sessions',
    '5': 'lapsed',
    '6': 'recommendations',
    '7': 'predictions'
  };

  const targetSection = document.getElementById(sectionMap[section]);
  if (targetSection) {
    targetSection.querySelector('.container')?.appendChild(savedElement);
    btn.textContent = 'Saved ✓';
    btn.disabled = true;
  }
}
</script>

</body>
</html>
'''


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION FUNCTIONS — These are the main content generators
# ═══════════════════════════════════════════════════════════════════════════════

# These will be imported from sections module
from sections_v2 import (
    section_01, section_02, section_03, section_04,
    section_05, section_06, section_07
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

    with open(filename, 'w') as f:
        f.write(html)
    print(f"  → {filename} ({len(html):,} chars)")


if __name__ == '__main__':
    main()
