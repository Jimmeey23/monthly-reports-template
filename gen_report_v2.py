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

LOCATIONS = DATA.get('meta', {}).get('locations', {})
MONTHS = DATA.get('meta', {}).get('months', {})


def run_generate(analysis_path, loc_keys, month_keys, output_path=None):
    global DATA, LOCATIONS, MONTHS
    with open(analysis_path, 'r') as f:
        DATA = json.load(f)
    LOCATIONS = DATA['meta']['locations']
    MONTHS = DATA['meta']['months']
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

    prev_year, prev_mon = (year, mon - 1) if mon > 1 else (year - 1, 12)
    prev_month_key = f'{prev_year}-{prev_mon:02d}'
    prev_month_name = calendar.month_name[prev_mon]

    next_year, next_mon = (year, mon + 1) if mon < 12 else (year + 1, 1)
    next_month_name = calendar.month_name[next_mon]
    next_month_short = calendar.month_abbr[next_mon]

    yoy_month_key = f'{year - 1}-{mon:02d}'

    return {
        'month_name': month_name,
        'month_short': month_short,
        'year': str(year),
        'date_range': f'01 {month_name} {year} &mdash; {days_in_month} {month_name} {year}',
        'period_short': f'01 &mdash; {days_in_month} {month_short} {year}',
        'prev_month': prev_month_key,
        'prev_month_name': prev_month_name,
        'prev_year': str(prev_year),
        'yoy_month': yoy_month_key,
        'yoy_month_name': f'{month_short} {year - 1}',
        'next_month_name': next_month_name,
        'next_month_short': next_month_short,
        'next_year': str(next_year),
    }


LOCATIONS = {lk: build_location_meta(full_name)
             for lk, full_name in DATA.get('meta', {}).get('locations', {}).items()}

MONTHS = {mk: build_month_meta(mk) for mk in DATA.get('meta', {}).get('months', [])}

# ─── Data Access Helpers ──────────────────────────────────────────────────────

def get_sales(loc, month):
    return DATA['sales'][loc].get(month, {})

def get_sessions(loc, month):
    return DATA['sessions'][loc].get(month, {})

def get_leads(loc, month):
    return DATA['leads'][loc].get(month, {})

def get_leads_source(loc, month):
    return DATA['leads_by_source'][loc].get(month, {})

def get_new(loc, month):
    return DATA['new'][loc].get(month, {})

def get_new_type(loc, month):
    return DATA['new_by_type'][loc].get(month, {})

def get_lapsed(loc, month):
    return DATA['lapsed'][loc].get(month, {})

def get_lapsed_product(loc, month):
    return DATA['lapsed_by_product'][loc].get(month, {})

def get_lapsed_cumulative(loc):
    return DATA['lapsed_cumulative'].get(loc, {})

def get_checkins(loc, month):
    return DATA['checkins'][loc].get(month, {})

def get_active(loc):
    return DATA['active'].get(loc, {})

def get_baseline(loc):
    return DATA['baseline'].get(loc, {})

def get_heatmap(loc, month):
    return DATA['heatmap'][loc].get(month, {})

def get_sessions_by_class(loc, month):
    return DATA['sessions_by_class'][loc].get(month, {})

def get_sessions_by_trainer(loc, month):
    return DATA['sessions_by_trainer'][loc].get(month, {})

def get_sessions_by_format(loc, month):
    return DATA['sessions_by_format'][loc].get(month, {})

def get_sessions_by_trainer_format(loc, month):
    return DATA.get('sessions_by_trainer_format', {}).get(loc, {}).get(month, {})

def get_sales_breakdowns(loc, month):
    return DATA['sales_breakdowns'][loc].get(month, {})


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
    baseline = get_baseline(loc_key)

    prev_sales = get_sales(loc_key, mo['prev_month'])
    prev_sessions = get_sessions(loc_key, mo['prev_month'])
    prev_leads = get_leads(loc_key, mo['prev_month'])
    prev_new = get_new(loc_key, mo['prev_month'])
    prev_lapsed = get_lapsed(loc_key, mo['prev_month'])
    prev_checkins = get_checkins(loc_key, mo['prev_month'])

    yoy_sales = get_sales(loc_key, mo['yoy_month'])

    ctx = build_context(loc_key, month_key, loc, mo, sales, sessions, leads, new, lapsed, checkins, active, baseline,
                        prev_sales, prev_sessions, prev_leads, prev_new, prev_lapsed, prev_checkins, yoy_sales)
    ctx['id_suffix'] = id_suffix
    return ctx


def generate_report(loc_keys, month_keys):
    """Generate a report for the cartesian product of loc_keys x month_keys.
    A single combo produces the standard single-report document; multiple
    combos are bundled into one document with a cover/TOC and page breaks."""
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
    """Human label for the baseline months, e.g. 'Jun&ndash;Aug 2025' or
    'Dec 2025&ndash;Feb 2026' when the range spans a year boundary."""
    months = DATA.get('meta', {}).get('baseline_months', [])
    if not months:
        return 'baseline'
    first, last = months[0], months[-1]
    fy, fm = (int(x) for x in first.split('-'))
    ly, lm = (int(x) for x in last.split('-'))
    if first == last:
        return f'{calendar.month_abbr[fm]} {fy}'
    if fy == ly:
        return f'{calendar.month_abbr[fm]}&ndash;{calendar.month_abbr[lm]} {fy}'
    return f'{calendar.month_abbr[fm]} {fy}&ndash;{calendar.month_abbr[lm]} {ly}'


def build_context(loc_key, month_key, loc, mo, sales, sessions, leads, new, lapsed, checkins, active, baseline,
                  prev_sales, prev_sessions, prev_leads, prev_new, prev_lapsed, prev_checkins, yoy_sales):
    """Build a context dict with all computed values for the report."""

    ctx = {
        'loc': loc,
        'mo': mo,
        'loc_key': loc_key,
        'month_key': month_key,
        'baseline_label': build_baseline_label(),
        'sales': sales,
        'sessions': sessions,
        'leads': leads,
        'new': new,
        'lapsed': lapsed,
        'checkins': checkins,
        'active': active,
        'baseline': baseline,
        'prev_sales': prev_sales,
        'prev_sessions': prev_sessions,
        'prev_leads': prev_leads,
        'prev_new': prev_new,
        'prev_lapsed': prev_lapsed,
        'prev_checkins': prev_checkins,
        'yoy_sales': yoy_sales,
    }
    
    # Sales comparators
    ctx['net_mom'] = pct_change(prev_sales.get('net', 0), sales.get('net', 0))
    ctx['net_yoy'] = pct_change(yoy_sales.get('net', 0), sales.get('net', 0)) if yoy_sales else "n/a"
    ctx['net_baseline'] = pct_change(baseline['sales']['net'], sales.get('net', 0))
    
    ctx['gross_mom'] = pct_change(prev_sales.get('gross', 0), sales.get('gross', 0))
    ctx['gross_yoy'] = pct_change(yoy_sales.get('gross', 0), sales.get('gross', 0)) if yoy_sales else "n/a"
    ctx['gross_baseline'] = pct_change(baseline['sales']['gross'], sales.get('gross', 0))
    
    ctx['disc_mom'] = pct_change(prev_sales.get('disc', 0), sales.get('disc', 0))
    ctx['disc_baseline'] = pct_change(baseline['sales']['disc'], sales.get('disc', 0))
    
    ctx['sales_count_mom'] = pct_change(prev_sales.get('sales', 0), sales.get('sales', 0))
    ctx['members_mom'] = pct_change(prev_sales.get('members', 0), sales.get('members', 0))
    ctx['atv_mom'] = pct_change(prev_sales.get('atv', 0), sales.get('atv', 0))
    
    ctx['disc_eff_mom'] = pct_change(prev_sales.get('disc_eff', 0), sales.get('disc_eff', 0))
    ctx['disc_eff_yoy'] = pct_change(yoy_sales.get('disc_eff', 0), sales.get('disc_eff', 0)) if yoy_sales else "n/a"
    ctx['disc_eff_baseline'] = pct_change(baseline['sales']['disc_eff'], sales.get('disc_eff', 0))
    
    # Sessions comparators
    ctx['sessions_mom'] = pct_change(prev_sessions.get('sessions', 0), sessions.get('sessions', 0))
    ctx['visits_mom'] = pct_change(prev_sessions.get('visits', 0), sessions.get('visits', 0))
    ctx['fill_mom'] = pp_change(prev_sessions.get('fill', 0), sessions.get('fill', 0))
    ctx['fill_baseline'] = pp_change(baseline['sessions']['fill'], sessions.get('fill', 0))
    ctx['sess_rev_mom'] = pct_change(prev_sessions.get('revenue', 0), sessions.get('revenue', 0))
    ctx['sessions_baseline'] = pct_change(baseline['sessions']['sessions'], sessions.get('sessions', 0))
    ctx['visits_baseline'] = pct_change(baseline['sessions']['visits'], sessions.get('visits', 0))
    
    # Leads comparators
    ctx['leads_mom'] = pct_change(prev_leads.get('total', 0), leads.get('total', 0))
    ctx['conv_mom'] = pp_change(prev_leads.get('rate', 0), leads.get('rate', 0))
    ctx['conv_baseline'] = pp_change(baseline['leads']['rate'], leads.get('rate', 0))
    ctx['converted_mom'] = pct_change(prev_leads.get('converted', 0), leads.get('converted', 0))
    
    # Trials comparators
    ctx['trials_mom'] = pct_change(prev_new.get('trials', 0), new.get('trials', 0))
    ctx['retained_mom'] = pct_change(prev_new.get('retained', 0), new.get('retained', 0))
    
    # Lapsed comparators
    ctx['lapsed_mom'] = pct_change(prev_lapsed.get('lapsed', 0), lapsed.get('lapsed', 0))
    ctx['churn_mom'] = pp_change(prev_lapsed.get('churn', 0), lapsed.get('churn', 0))
    ctx['churn_baseline'] = pp_change(baseline['lapsed']['churn'], lapsed.get('churn', 0))
    ctx['renewal_mom'] = pp_change(prev_lapsed.get('renewal_rate', 0), lapsed.get('renewal_rate', 0))
    ctx['renewal_baseline'] = pp_change(baseline['lapsed']['renewal_rate'], lapsed.get('renewal_rate', 0))
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
    
    # Retention rate of trials
    ctx['trial_retention'] = (new.get('retained', 0) / new.get('trials', 1)) * 100 if new.get('trials') else 0
    
    # Cumulative lapsed
    ctx['cumulative_lapsed'] = get_lapsed_cumulative(loc_key).get(month_key, 0)
    
    return ctx


def build_html(ctx):
    """Assemble the full HTML document."""
    html = head(ctx)
    html += topbar(ctx)
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
    conv_val = pct(ctx['leads']['rate'])
    lapsed_val = fmt_int(ctx['lapsed']['lapsed'])
    disc_eff_val = f"&#8377;{s['disc_eff']:.2f}"
    
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
                ctx['net_mom'], ctx['net_yoy'], ctx['net_baseline'], higher_is_better=True)}
      {kpi_card("Visits", visits_val, f"Across {sess['sessions']} sessions",
                ctx['visits_mom'], "n/a", ctx['visits_baseline'], higher_is_better=True)}
      {kpi_card("Fill Rate", fill_val, "Capacity utilization",
                ctx['fill_mom'], "n/a", ctx['fill_baseline'], higher_is_better=True, is_pp=True)}
      {kpi_card("Conversion Rate", conv_val, f"{ctx['leads']['total']} leads &rarr; {ctx['leads']['converted']} converted",
                ctx['conv_mom'], "n/a", ctx['conv_baseline'], higher_is_better=True, is_pp=True)}
      {kpi_card("Lapsed Members", lapsed_val, f"Churn rate {pct(ctx['lapsed']['churn'])}",
                ctx['lapsed_mom'], "n/a", "Active retention work", higher_is_better=False)}
      {kpi_card("Discount Efficiency", disc_eff_val, "Revenue collected / &#8377;1 discounted",
                ctx['disc_eff_mom'], ctx['disc_eff_yoy'], ctx['disc_eff_baseline'], higher_is_better=True)}
    </div>
  </div>
</section>
'''


def kpi_card(label, value, sub, mom, yoy, baseline_text, higher_is_better=True, is_pp=False):
    """Generate a KPI card."""
    mom_b = badge(mom, higher_is_better) if not is_pp else badge_from_pp(mom, higher_is_better)
    yoy_b = badge(yoy, higher_is_better) if not is_pp else badge_from_pp(yoy, higher_is_better)
    
    yoy_html = ""
    if yoy != "n/a":
        yoy_html = f'''<span class="kpi-trend"><span class="trend-label">YoY</span> <span class='badge {yoy_b}'>{yoy}</span></span>'''
    
    return f'''        <div class="kpi-card">
          <div class="kpi-label">{label}</div>
          <div class="kpi-value">{value}</div>
          <div class="kpi-sub">{sub}</div>
          <div class="kpi-trends">
            <span class="kpi-trend"><span class="trend-label">MoM</span> <span class='badge {mom_b}'>{mom}</span></span>
            {yoy_html}
          </div>
          <div class="kpi-baseline">{baseline_text}</div>
        </div>'''


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
  const root = document.documentElement;
  const toggle = document.getElementById('theme-toggle');
  const label = document.getElementById('theme-label');
  const icon = document.getElementById('theme-icon');

  const saved = localStorage.getItem('kh-theme') || 'dark';
  applyTheme(saved);

  toggle.addEventListener('click', () => {
    const current = root.getAttribute('data-theme') || 'dark';
    const next = current === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    localStorage.setItem('kh-theme', next);
  });

  function applyTheme(theme) {
    root.setAttribute('data-theme', theme);
    if (theme === 'dark') {
      label.textContent = 'Light';
      icon.innerHTML = '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>';
    } else {
      label.textContent = 'Dark';
      icon.innerHTML = '<circle cx="12" cy="12" r="4"></circle><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"></path>';
    }
  }
})();
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
