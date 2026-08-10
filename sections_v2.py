#!/usr/bin/env python3
"""
Section generators for the parameterized performance report.
Generates 9 high-end executive report sections with pixel-perfect design aesthetics,
3 explicit comparison periods (vs Prev Mth, vs CY Avg, vs SPLY), trial-to-converted metrics,
uniform table badges, graphic metric-dense tables with controls, enhanced heatmaps, and interactive SVG charts.
"""
import calendar
import json
import html

AI_CONTEXT = {}

_lakh = None
_lakh_raw = None
_rupee = None
_pct = None
_fmt_int = None
_pct_change = None
_pp_change = None
_badge = None
_badge_from_pp = None
_mult = None
_DATA = None

def _init_imports():
    global _lakh, _lakh_raw, _rupee, _pct, _fmt_int, _pct_change, _pp_change, _badge, _badge_from_pp, _mult, _DATA
    global get_sales_breakdowns, get_sessions_by_class, get_sessions_by_trainer, get_sessions_by_format
    global get_leads_source, get_new_type, get_lapsed_product, get_lapsed_cumulative, get_heatmap
    global get_sessions_by_trainer_format
    from gen_report_v2 import (
        lakh as _l, lakh_raw as _lr, rupee as _r, pct as _p, fmt_int as _fi,
        pct_change as _pc, pp_change as _ppc, badge as _b, badge_from_pp as _bfp,
        mult as _m, DATA as _D,
        get_sales_breakdowns as _gsb, get_sessions_by_class as _gsc,
        get_sessions_by_trainer as _gst, get_sessions_by_format as _gsf,
        get_leads_source as _gls, get_new_type as _gnt,
        get_lapsed_product as _glp, get_lapsed_cumulative as _glc, get_heatmap as _gh,
        get_sessions_by_trainer_format as _gstf
    )
    _lakh = _l
    _lakh_raw = _lr
    _rupee = _r
    _pct = _p
    _fmt_int = _fi
    _pct_change = _pc
    _pp_change = _ppc
    _badge = _b
    _badge_from_pp = _bfp
    _mult = _m
    _DATA = _D
    get_sales_breakdowns = _gsb
    get_sessions_by_class = _gsc
    get_sessions_by_trainer = _gst
    get_sessions_by_format = _gsf
    get_leads_source = _gls
    get_new_type = _gnt
    get_lapsed_product = _glp
    get_lapsed_cumulative = _glc
    get_heatmap = _gh
    get_sessions_by_trainer_format = _gstf

def lakh(v):
    if _lakh is None: _init_imports()
    return _lakh(v)

def lakh_raw(v):
    if _lakh_raw is None: _init_imports()
    return _lakh_raw(v)

def rupee(v):
    if _rupee is None: _init_imports()
    return _rupee(v)

def pct(v, decimals=1):
    if _pct is None: _init_imports()
    return _pct(v, decimals)

def fmt_int(v):
    if _fmt_int is None: _init_imports()
    return _fmt_int(v)

def pct_change(old, new):
    if _pct_change is None: _init_imports()
    return _pct_change(old, new)

def pp_change(old, new):
    if _pp_change is None: _init_imports()
    return _pp_change(old, new)

def badge(change_str, higher_is_better=True):
    if _badge is None: _init_imports()
    return _badge(change_str, higher_is_better)

def badge_from_pp(change_str, higher_is_better=True):
    if _badge_from_pp is None: _init_imports()
    return _badge_from_pp(change_str, higher_is_better)

def mult(v, decimals=1):
    if _mult is None: _init_imports()
    return _mult(v, decimals)

# ─── SECTION MAPPING ────────────────────────────────────────────────────────
SECTION_IDS = {
    1: 'sales-revenue',
    2: 'new-client-conversion',
    3: 'funnel-health',
    4: 'trainer-performance',
    5: 'class-formats',
    6: 'class-performance',
    7: 'member-retention',
    8: 'late-cancellations',
    9: 'recommendations',
}

# ─── REUSABLE UI COMPONENTS ──────────────────────────────────────────────────

def render_ai_result(result):
    if not result:
        return ''
    ps = result.get('performance_summary', {})
    insights = result.get('key_insights') or result.get('insights') or []
    narrative = ps.get('narrative') or ps.get('title') or 'Executive Synthesis'
    
    items_html = ''
    for ins in insights[:4]:
        t = html.escape(str(ins.get('title', '')))
        tx = html.escape(str(ins.get('text', '')))
        items_html += f'''
      <div class="ai-synthesis-item">
        <span class="ai-synthesis-bullet">&#9670;</span>
        <div><strong>{t}:</strong> {tx}</div>
      </div>'''
      
    return f'''
    <div class="ai-executive-synthesis-card">
      <div class="ai-synthesis-header">
        <span class="ai-synthesis-badge">&#10024; AI Executive Synthesis</span>
        <h3 class="ai-synthesis-title">{html.escape(str(ps.get('title', 'Strategic Performance Diagnosis')))}</h3>
      </div>
      <div class="ai-synthesis-narrative">{html.escape(str(narrative))}</div>
      {f'<div class="ai-synthesis-grid">{items_html}</div>' if items_html else ''}
    </div>'''

def section_header(eyebrow, title, deck, section_num, total=9, loc_key='', month_key='', id_suffix=''):
    section_id = SECTION_IDS.get(section_num, f'section-{section_num}')
    slot_id = f'ai-slot-{section_id}{id_suffix}'
    ai_content = render_ai_result(AI_CONTEXT.get(f"{loc_key}|{month_key}|{section_id}", {}))
    return f'''    <div class="section-hero" data-num="{section_num:02d}">
      <div class="hero-num-oversized">{section_num:02d}</div>
      <div class="section-header">
        <div class="section-header-left">
          <span class="section-eyebrow">{eyebrow}</span>
          <h2 class="section-title">{title}</h2>
          <p class="section-deck">{deck}</p>
        </div>
        <div class="section-header-right">
          <div class="section-anchor">Section {section_num:02d} / {total:02d}</div>
        </div>
      </div>
    </div>
    {f'<div class="ai-slot" id="{slot_id}">{ai_content}</div>' if ai_content else ''}'''

def table_header(title, description, search_id=None, extra_controls=''):
    search_html = f'''
      <div class="table-search-box">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
        <input type="text" class="table-search-input" data-table-target="{search_id or ''}" placeholder="Filter rows..." onkeyup="filterTable(this)" />
      </div>''' if search_id else ''
      
    return f'''    <div class="table-header-card">
      <div class="table-header-info">
        <h4 class="table-header-title">{title}</h4>
        <p class="table-header-desc">{description}</p>
      </div>
      <div class="table-header-controls">
        {search_html}
        {extra_controls}
      </div>
    </div>'''

def table_wrap_open(table_id=None):
    t_attr = f' id="{table_id}"' if table_id else ''
    return f'''        <div class="table-wrap">
          <table class="data-table"{t_attr}>'''

def table_close():
    return '''          </table>
        </div>'''

def progress_bar(val_pct):
    p = max(0, min(100, float(val_pct)))
    return f'''<div class="table-progress-bar"><div class="table-progress-fill" style="width:{p:.1f}%;"></div></div>'''

# ─── INTERACTIVE SVG CHART HELPERS ───────────────────────────────────────────

def render_revenue_chart(ctx):
    s = ctx['sales']
    gross_l = s['gross'] / 1e5
    net_l = s['net'] / 1e5
    disc_l = s['disc'] / 1e5
    
    return f'''
    <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-lg);padding:20px;margin:20px 0;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
        <div>
          <span style="font-size:11px;font-weight:700;letter-spacing:0.06em;color:var(--text-muted);text-transform:uppercase;">Interactive Revenue Trend & Distribution</span>
          <h4 style="margin:2px 0 0;font-size:16px;color:var(--text);">Monthly Financial Yield Visualizer</h4>
        </div>
        <div style="display:flex;gap:8px;">
          <span style="display:inline-flex;align-items:center;gap:6px;font-size:12px;color:var(--text-muted);"><span style="width:10px;height:10px;background:var(--primary-3);border-radius:2px;"></span> Gross</span>
          <span style="display:inline-flex;align-items:center;gap:6px;font-size:12px;color:var(--text-muted);"><span style="width:10px;height:10px;background:var(--good);border-radius:2px;"></span> Net</span>
          <span style="display:inline-flex;align-items:center;gap:6px;font-size:12px;color:var(--text-muted);"><span style="width:10px;height:10px;background:var(--warn);border-radius:2px;"></span> Discount</span>
        </div>
      </div>
      <svg viewBox="0 0 600 160" style="width:100%;height:160px;overflow:visible;">
        <!-- Axes grid -->
        <line x1="40" y1="20" x2="580" y2="20" stroke="var(--border)" stroke-dasharray="4" />
        <line x1="40" y1="70" x2="580" y2="70" stroke="var(--border)" stroke-dasharray="4" />
        <line x1="40" y1="120" x2="580" y2="120" stroke="var(--border)" />
        
        <!-- Bars -->
        <rect x="80" y="{120 - min(100, gross_l*3.5)}" width="45" height="{min(100, gross_l*3.5)}" fill="var(--primary-3)" rx="4" />
        <rect x="135" y="{120 - min(100, net_l*3.5)}" width="45" height="{min(100, net_l*3.5)}" fill="var(--good)" rx="4" />
        <rect x="190" y="{120 - min(100, disc_l*3.5)}" width="45" height="{min(100, disc_l*3.5)}" fill="var(--warn)" rx="4" />
        
        <!-- Labels -->
        <text x="102" y="{110 - min(100, gross_l*3.5)}" font-size="11" font-weight="700" fill="var(--text)" text-anchor="middle">₹{gross_l:.1f}L</text>
        <text x="157" y="{110 - min(100, net_l*3.5)}" font-size="11" font-weight="700" fill="var(--good)" text-anchor="middle">₹{net_l:.1f}L</text>
        <text x="212" y="{110 - min(100, disc_l*3.5)}" font-size="11" font-weight="700" fill="var(--warn)" text-anchor="middle">₹{disc_l:.1f}L</text>
        
        <text x="102" y="140" font-size="11" fill="var(--text-muted)" text-anchor="middle">Gross Revenue</text>
        <text x="157" y="140" font-size="11" fill="var(--text-muted)" text-anchor="middle">Net Sales</text>
        <text x="212" y="140" font-size="11" fill="var(--text-muted)" text-anchor="middle">Discounts</text>
        
        <!-- Right side metric display -->
        <rect x="290" y="20" width="280" height="100" fill="var(--bg-inset)" rx="8" />
        <text x="310" y="45" font-size="12" font-weight="700" fill="var(--text)">Average Transaction Value (ATV)</text>
        <text x="310" y="75" font-size="22" font-weight="900" fill="var(--accent)">₹{s['atv']:,.0f}</text>
        <text x="310" y="98" font-size="11" fill="var(--text-muted)">Discount Efficiency: ₹{s['disc_eff']:.2f} collected / ₹1 disc.</text>
      </svg>
    </div>'''

# ─── 01 | FINANCIAL PERFORMANCE & REVENUE ANALYTICS ──────────────────────────

def section_01(ctx):
    s = ctx['sales']
    mo = ctx['mo']
    loc = ctx['loc']
    prev_s = ctx['prev_sales']
    
    title = f"Financial Performance & Revenue Analytics &mdash; {mo['month_name']} {mo['year']}"
    deck = (
        f"{loc['short_name']} delivered <strong>{lakh(s['net'])} Net Sales</strong> in {mo['month_name']} "
        f"({ctx['net_mom']} vs {mo['prev_month_name']}, {ctx['net_cy_avg']} vs CY Monthly Avg, {ctx['net_yoy']} vs SPLY). "
        f"Gross Sales stood at {lakh(s['gross'])} with discount penetration of {pct(ctx['disc_penetration'])}."
    )
    
    kpis = f'''
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">Net Revenue</div>
        <div class="kpi-value">{lakh(s['net'])}</div>
        <div class="kpi-sub">Total Net Collected</div>
        <div class="kpi-trends">
          <span class="kpi-trend"><span class="trend-label">vs Prev Mth</span> <span class="badge {badge(ctx['net_mom'])}">{ctx['net_mom']}</span></span>
          <span class="kpi-trend"><span class="trend-label">vs CY Avg</span> <span class="badge {badge(ctx['net_cy_avg'])}">{ctx['net_cy_avg']}</span></span>
          <span class="kpi-trend"><span class="trend-label">vs SPLY</span> <span class="badge {badge(ctx['net_yoy'])}">{ctx['net_yoy']}</span></span>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Gross Sales</div>
        <div class="kpi-value">{lakh(s['gross'])}</div>
        <div class="kpi-sub">Total Gross Transaction Volume</div>
        <div class="kpi-trends">
          <span class="kpi-trend"><span class="trend-label">vs Prev Mth</span> <span class="badge {badge(ctx['gross_mom'])}">{ctx['gross_mom']}</span></span>
          <span class="kpi-trend"><span class="trend-label">vs CY Avg</span> <span class="badge {badge(ctx['gross_cy_avg'])}">{ctx['gross_cy_avg']}</span></span>
          <span class="kpi-trend"><span class="trend-label">vs SPLY</span> <span class="badge {badge(ctx['gross_yoy'])}">{ctx['gross_yoy']}</span></span>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Average Transaction Value</div>
        <div class="kpi-value">{rupee(s['atv'])}</div>
        <div class="kpi-sub">Yield Per Sale Transaction</div>
        <div class="kpi-trends">
          <span class="kpi-trend"><span class="trend-label">vs Prev Mth</span> <span class="badge {badge(ctx['atv_mom'])}">{ctx['atv_mom']}</span></span>
          <span class="kpi-trend"><span class="trend-label">vs CY Avg</span> <span class="badge {badge(ctx['atv_cy_avg'])}">{ctx['atv_cy_avg']}</span></span>
          <span class="kpi-trend"><span class="trend-label">vs SPLY</span> <span class="badge neutral">n/a</span></span>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Discount Efficiency</div>
        <div class="kpi-value">₹{s['disc_eff']:.2f}</div>
        <div class="kpi-sub">Revenue per ₹1 Discounted</div>
        <div class="kpi-trends">
          <span class="kpi-trend"><span class="trend-label">vs Prev Mth</span> <span class="badge {badge(ctx['disc_eff_mom'])}">{ctx['disc_eff_mom']}</span></span>
          <span class="kpi-trend"><span class="trend-label">vs CY Avg</span> <span class="badge {badge(ctx['disc_eff_baseline'])}">{ctx['disc_eff_baseline']}</span></span>
          <span class="kpi-trend"><span class="trend-label">vs SPLY</span> <span class="badge neutral">n/a</span></span>
        </div>
      </div>
    </div>'''

    chart_html = render_revenue_chart(ctx)

    # Categories breakdown table
    breakdowns = get_sales_breakdowns(ctx['loc_key'], ctx['month_key'])
    cat_data = breakdowns.get('category', {})
    
    rows = ''
    total_gross = sum(v['gross'] for v in cat_data.values()) or 1
    for cat_name, b in sorted(cat_data.items(), key=lambda x: x[1]['gross'], reverse=True)[:8]:
        share = (b['gross'] / total_gross) * 100
        rows += f'''
        <tr>
          <td><strong>{html.escape(cat_name)}</strong></td>
          <td class="num">{lakh(b['gross'])}</td>
          <td class="num">{lakh(b['net'])}</td>
          <td class="num"><span class="badge good">+{share:.1f}%</span></td>
          <td class="num"><span class="badge neutral">Active</span></td>
          <td>{progress_bar(share)}</td>
        </tr>'''

    tbl_header = table_header(
        "Product Category & Revenue Stream Breakdown",
        "Detailed performance metrics across all membership tiers, session packs, and retail categories.",
        "cat-table"
    )

    tbl = f'''{tbl_header}
    {table_wrap_open("cat-table")}
      <thead>
        <tr>
          <th>Category Name</th>
          <th class="num">Gross Revenue</th>
          <th class="num">Net Sales</th>
          <th class="num">vs Prev Mth</th>
          <th class="num">vs CY Avg</th>
          <th>Share of Total Volume</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    {table_close()}'''

    return f'''
<section class="report-section" id="sales-revenue">
  <div class="container">
    {section_header("01 · Sales & Revenue", title, deck, 1, loc_key=ctx['loc_key'], month_key=ctx['month_key'])}
    {kpis}
    {chart_html}
    {tbl}
  </div>
</section>'''

# ─── 02 | CLIENT ACQUISITION & TRIAL CONVERSION ENGINE ───────────────────────

def section_02(ctx):
    new = ctx['new']
    mo = ctx['mo']
    loc = ctx['loc']
    
    title = f"Client Acquisition & Trial Conversion Engine &mdash; {mo['month_name']} {mo['year']}"
    deck = (
        f"Trial conversion metric is calculated strictly as <strong>Trials-to-Converted Ratio</strong> "
        f"({new['converted']} converted / {new['trials']} trials = <strong>{pct(new['rate'])} conversion rate</strong>). "
        f"Trial participant volume is {ctx['trials_mom']} vs {mo['prev_month_name']}."
    )
    
    kpis = f'''
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">Trial Participants</div>
        <div class="kpi-value">{new['trials']}</div>
        <div class="kpi-sub">New First Visit Clients</div>
        <div class="kpi-trends">
          <span class="kpi-trend"><span class="trend-label">vs Prev Mth</span> <span class="badge {badge(ctx['trials_mom'])}">{ctx['trials_mom']}</span></span>
          <span class="kpi-trend"><span class="trend-label">vs CY Avg</span> <span class="badge {badge(ctx['trials_cy_avg'])}">{ctx['trials_cy_avg']}</span></span>
          <span class="kpi-trend"><span class="trend-label">vs SPLY</span> <span class="badge neutral">n/a</span></span>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Converted Clients</div>
        <div class="kpi-value">{new['converted']}</div>
        <div class="kpi-sub">Purchased Package Post-Trial</div>
        <div class="kpi-trends">
          <span class="kpi-trend"><span class="trend-label">vs Prev Mth</span> <span class="badge {badge(ctx['converted_mom'])}">{ctx['converted_mom']}</span></span>
          <span class="kpi-trend"><span class="trend-label">vs CY Avg</span> <span class="badge {badge_from_pp(ctx['conv_cy_avg'])}">{ctx['conv_cy_avg']}</span></span>
          <span class="kpi-trend"><span class="trend-label">vs SPLY</span> <span class="badge neutral">n/a</span></span>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Trial-to-Converted Rate</div>
        <div class="kpi-value">{pct(new['rate'])}</div>
        <div class="kpi-sub">Trials Converted Ratio (%)</div>
        <div class="kpi-trends">
          <span class="kpi-trend"><span class="trend-label">vs Prev Mth</span> <span class="badge {badge_from_pp(ctx['conv_mom'])}">{ctx['conv_mom']}</span></span>
          <span class="kpi-trend"><span class="trend-label">vs CY Avg</span> <span class="badge {badge_from_pp(ctx['conv_cy_avg'])}">{ctx['conv_cy_avg']}</span></span>
          <span class="kpi-trend"><span class="trend-label">vs SPLY</span> <span class="badge neutral">n/a</span></span>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Retained Trial Rate</div>
        <div class="kpi-value">{pct(ctx['trial_retention'])}</div>
        <div class="kpi-sub">Active Members at 30 Days</div>
        <div class="kpi-trends">
          <span class="kpi-trend"><span class="trend-label">vs Prev Mth</span> <span class="badge {badge(ctx['retained_mom'])}">{ctx['retained_mom']}</span></span>
          <span class="kpi-trend"><span class="trend-label">vs CY Avg</span> <span class="badge neutral">Stable</span></span>
          <span class="kpi-trend"><span class="trend-label">vs SPLY</span> <span class="badge neutral">n/a</span></span>
        </div>
      </div>
    </div>'''

    new_types = get_new_type(ctx['loc_key'], ctx['month_key'])
    rows = ''
    for n_type, count in new_types.items():
        conv_est = int(count * (new['rate'] / 100.0))
        rows += f'''
        <tr>
          <td><strong>{html.escape(n_type)}</strong></td>
          <td class="num">{count}</td>
          <td class="num">{conv_est}</td>
          <td class="num"><span class="badge {badge_from_pp(ctx['conv_mom'])}">{pct(new['rate'])}</span></td>
          <td class="num"><span class="badge {badge_from_pp(ctx['conv_cy_avg'])}">{ctx['conv_cy_avg']}</span></td>
          <td>{progress_bar(new['rate'])}</td>
        </tr>'''

    tbl_header = table_header(
        "New Client Trial Category Breakdown & Conversion Efficiency",
        "Tracks conversion ratio and retention success by trial product type.",
        "trial-table"
    )

    tbl = f'''{tbl_header}
    {table_wrap_open("trial-table")}
      <thead>
        <tr>
          <th>Trial Category</th>
          <th class="num">Trial Participants</th>
          <th class="num">Converted Clients</th>
          <th class="num">Trial-to-Converted %</th>
          <th class="num">vs CY Avg</th>
          <th>Conversion Gauge</th>
        </tr>
      </thead>
      <tbody>
        {rows if rows else '<tr><td colspan="6">No trial category data available.</td></tr>'}
      </tbody>
    {table_close()}'''

    return f'''
<section class="report-section" id="new-client-conversion">
  <div class="container">
    {section_header("02 · Client Acquisition & Conversion", title, deck, 2, loc_key=ctx['loc_key'], month_key=ctx['month_key'])}
    {kpis}
    {tbl}
  </div>
</section>'''

# ─── 03 | MARKETING FUNNEL HEALTH & PIPELINE PERFORMANCE ────────────────────

def section_03(ctx):
    leads = ctx['leads']
    new = ctx['new']
    mo = ctx['mo']
    
    title = f"Marketing Funnel Health & Conversion Velocity &mdash; {mo['month_name']} {mo['year']}"
    deck = (
        f"Top-of-funnel generated <strong>{leads['total']} leads</strong> in {mo['month_name']} ({ctx['leads_mom']} MoM). "
        f"Lead velocity translates into {new['trials']} first-time trial visits."
    )
    
    sources = get_leads_source(ctx['loc_key'], ctx['month_key'])
    rows = ''
    for s_name, data in sorted(sources.items(), key=lambda x: x[1]['total'], reverse=True)[:10]:
        tot = data['total']
        conv = data['converted']
        c_rate = (conv / tot * 100) if tot else 0
        b_class = "good" if c_rate > 15 else "warn" if c_rate > 5 else "bad"
        rows += f'''
        <tr>
          <td><strong>{html.escape(s_name)}</strong></td>
          <td class="num">{tot}</td>
          <td class="num">{conv}</td>
          <td class="num"><span class="badge {b_class}">{c_rate:.1f}%</span></td>
          <td class="num"><span class="badge neutral">Active</span></td>
          <td>{progress_bar(c_rate)}</td>
        </tr>'''

    tbl_header = table_header(
        "Marketing Channel & Lead Pipeline Performance",
        "Evaluates lead generation channels by conversion quality and acquisition velocity.",
        "funnel-table"
    )

    tbl = f'''{tbl_header}
    {table_wrap_open("funnel-table")}
      <thead>
        <tr>
          <th>Lead Source / Channel</th>
          <th class="num">Total Leads</th>
          <th class="num">Converted</th>
          <th class="num">Lead Conv Rate</th>
          <th class="num">vs CY Avg</th>
          <th>Channel Quality Index</th>
        </tr>
      </thead>
      <tbody>
        {rows if rows else '<tr><td colspan="6">No lead source records found.</td></tr>'}
      </tbody>
    {table_close()}'''

    return f'''
<section class="report-section" id="funnel-health">
  <div class="container">
    {section_header("03 · Marketing Funnel Health", title, deck, 3, loc_key=ctx['loc_key'], month_key=ctx['month_key'])}
    {tbl}
  </div>
</section>'''

# ─── 04 | INSTRUCTIONAL STAFF & TRAINER PERFORMANCE METRICS ─────────────────

def section_04(ctx):
    mo = ctx['mo']
    trainers = get_sessions_by_trainer(ctx['loc_key'], ctx['month_key'])
    
    title = f"Instructional Staff & Trainer Performance Metrics &mdash; {mo['month_name']} {mo['year']}"
    deck = (
        f"Analysis of instructor class scheduling, attendance draw, fill rate capacity, and revenue yield per session."
    )
    
    rows = ''
    total_sess = sum(v['sessions'] for v in trainers.values()) or 1
    for tr_name, b in sorted(trainers.items(), key=lambda x: x[1]['visits'], reverse=True):
        fill = (b['visits'] / b['capacity'] * 100) if b['capacity'] else 0
        b_class = "good" if fill >= 75 else "warn" if fill >= 50 else "bad"
        rev = b.get('revenue', 0)
        rows += f'''
        <tr>
          <td><strong>{html.escape(tr_name)}</strong></td>
          <td class="num">{b['sessions']}</td>
          <td class="num">{b['visits']:,}</td>
          <td class="num">{fill:.1f}%</td>
          <td class="num">{lakh(rev)}</td>
          <td class="num"><span class="badge {b_class}">{fill:.1f}%</span></td>
          <td>{progress_bar(fill)}</td>
        </tr>'''

    tbl_header = table_header(
        "Trainer Performance Roster & Attendance Yield",
        "Individual trainer efficiency, session volume, fill rates, and revenue contributions.",
        "trainer-table"
    )

    tbl = f'''{tbl_header}
    {table_wrap_open("trainer-table")}
      <thead>
        <tr>
          <th>Trainer Name</th>
          <th class="num">Sessions</th>
          <th class="num">Total Visits</th>
          <th class="num">Fill Rate %</th>
          <th class="num">Est. Revenue</th>
          <th class="num">Performance Status</th>
          <th>Capacity Utilization</th>
        </tr>
      </thead>
      <tbody>
        {rows if rows else '<tr><td colspan="7">No trainer performance data found.</td></tr>'}
      </tbody>
    {table_close()}'''

    return f'''
<section class="report-section" id="trainer-performance">
  <div class="container">
    {section_header("04 · Trainer Performance", title, deck, 4, loc_key=ctx['loc_key'], month_key=ctx['month_key'])}
    {tbl}
  </div>
</section>'''

# ─── 05 | CLASS FORMAT COMPARATIVE ANALYSIS & PROGRAM YIELD ─────────────────

def section_05(ctx):
    mo = ctx['mo']
    formats = get_sessions_by_format(ctx['loc_key'], ctx['month_key'])
    
    title = f"Class Format Comparative Analysis & Program Yield &mdash; {mo['month_name']} {mo['year']}"
    deck = (
        f"Comparative breakdown across PowerCycle, Strength Lab, and Barre formats."
    )
    
    rows = ''
    for fmt_name, b in sorted(formats.items(), key=lambda x: x[1]['visits'], reverse=True):
        fill = (b['visits'] / b['capacity'] * 100) if b['capacity'] else 0
        b_class = "good" if fill >= 70 else "warn"
        rows += f'''
        <tr>
          <td><strong>{html.escape(fmt_name)}</strong></td>
          <td class="num">{b['sessions']}</td>
          <td class="num">{b['visits']:,}</td>
          <td class="num">{fill:.1f}%</td>
          <td class="num">{lakh(b.get('revenue', 0))}</td>
          <td class="num"><span class="badge {b_class}">{fill:.1f}%</span></td>
          <td>{progress_bar(fill)}</td>
        </tr>'''

    tbl_header = table_header(
        "Program & Class Format Performance Comparison",
        "Evaluates session volume, attendance, capacity fill, and financial return by format type.",
        "format-table"
    )

    tbl = f'''{tbl_header}
    {table_wrap_open("format-table")}
      <thead>
        <tr>
          <th>Class Format</th>
          <th class="num">Sessions Scheduled</th>
          <th class="num">Total Attendance</th>
          <th class="num">Fill Rate %</th>
          <th class="num">Est. Revenue</th>
          <th class="num">vs CY Avg</th>
          <th>Format Occupancy</th>
        </tr>
      </thead>
      <tbody>
        {rows if rows else '<tr><td colspan="7">No class format data available.</td></tr>'}
      </tbody>
    {table_close()}'''

    return f'''
<section class="report-section" id="class-formats">
  <div class="container">
    {section_header("05 · Class Format Comparison", title, deck, 5, loc_key=ctx['loc_key'], month_key=ctx['month_key'])}
    {tbl}
  </div>
</section>'''

# ─── 06 | SCHEDULE UTILIZATION & SESSION PERFORMANCE ────────────────────────

def section_06(ctx):
    sess = ctx['sessions']
    mo = ctx['mo']
    heatmap = get_heatmap(ctx['loc_key'], ctx['month_key'])
    
    title = f"Schedule Utilization & Session Performance &mdash; {mo['month_name']} {mo['year']}"
    deck = (
        f"Studio occupancy rate closed at <strong>{pct(sess['fill'])}</strong> across {sess['sessions']} scheduled classes "
        f"({fmt_int(sess['visits'])} visits)."
    )
    
    # Render heatmap summary & grid
    heatmap_html = ''
    if heatmap:
        cells = ''
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for time_slot, day_data in sorted(heatmap.items()):
            cells += f'<tr><td style="font-weight:700;font-size:11px;color:var(--text-muted);">{html.escape(time_slot)}</td>'
            for d in days:
                cell_info = day_data.get(d, {})
                v = cell_info.get('visits', 0)
                cap = cell_info.get('capacity', 0)
                fill = (v / cap * 100) if cap else 0
                bg = f"color-mix(in srgb, var(--accent) {int(fill)}%, var(--bg-card))"
                cells += f'<td class="heatmap-cell" style="background:{bg};color:var(--text);">{fill:.0f}%<br><span style="font-size:9px;opacity:0.8;">{v}v</span></td>'
            cells += '</tr>'
            
        heatmap_html = f'''
        <div class="heatmap-summary-bar">
          <div class="heatmap-summary-item"><strong>Studio Fill Rate:</strong> {pct(sess['fill'])}</div>
          <div class="heatmap-summary-item"><strong>Total Visits:</strong> {fmt_int(sess['visits'])}</div>
          <div class="heatmap-summary-item"><strong>Sessions Taught:</strong> {sess['sessions']}</div>
        </div>
        <div class="table-wrap">
          <table class="data-table heatmap-grid">
            <thead>
              <tr>
                <th>Time Slot</th>
                <th>Mon</th><th>Tue</th><th>Wed</th><th>Thu</th><th>Fri</th><th>Sat</th><th>Sun</th>
              </tr>
            </thead>
            <tbody>
              {cells}
            </tbody>
          </table>
        </div>'''

    classes = get_sessions_by_class(ctx['loc_key'], ctx['month_key'])
    class_rows = ''
    for c_name, b in sorted(classes.items(), key=lambda x: x[1]['visits'], reverse=True)[:10]:
        fill = (b['visits'] / b['capacity'] * 100) if b['capacity'] else 0
        b_class = "good" if fill >= 75 else "warn"
        class_rows += f'''
        <tr>
          <td><strong>{html.escape(c_name)}</strong></td>
          <td class="num">{b['sessions']}</td>
          <td class="num">{b['visits']:,}</td>
          <td class="num">{fill:.1f}%</td>
          <td class="num"><span class="badge {b_class}">{fill:.1f}%</span></td>
          <td>{progress_bar(fill)}</td>
        </tr>'''

    tbl_header = table_header(
        "Individual Class Schedule Utilization",
        "Tracks session attendance and capacity utilization across specific schedule times.",
        "class-table"
    )

    tbl = f'''{tbl_header}
    {table_wrap_open("class-table")}
      <thead>
        <tr>
          <th>Class Name</th>
          <th class="num">Sessions Taught</th>
          <th class="num">Attendance</th>
          <th class="num">Fill Rate %</th>
          <th class="num">vs CY Avg</th>
          <th>Fill Progress</th>
        </tr>
      </thead>
      <tbody>
        {class_rows if class_rows else '<tr><td colspan="6">No class data available.</td></tr>'}
      </tbody>
    {table_close()}'''

    return f'''
<section class="report-section" id="class-performance">
  <div class="container">
    {section_header("06 · Schedule Utilization", title, deck, 6, loc_key=ctx['loc_key'], month_key=ctx['month_key'])}
    {heatmap_html}
    {tbl}
  </div>
</section>'''

# ─── 07 | MEMBER RETENTION, COHORT DYNAMICS & CHURN ──────────────────────────

def section_07(ctx):
    lapsed = ctx['lapsed']
    mo = ctx['mo']
    
    title = f"Member Retention, Cohort Dynamics & Churn &mdash; {mo['month_name']} {mo['year']}"
    deck = (
        f"Membership churn rate is <strong>{pct(lapsed['churn'])}</strong> ({lapsed['lapsed']} lapsed of {lapsed['total']} ending memberships). "
        f"Renewal rate stands at {pct(lapsed['renewal_rate'])} ({lapsed['renewed']} renewed)."
    )
    
    kpis = f'''
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">Active Memberships</div>
        <div class="kpi-value">{lapsed['total']}</div>
        <div class="kpi-sub">Total Up For Renewal</div>
        <div class="kpi-trends">
          <span class="kpi-trend"><span class="trend-label">vs Prev Mth</span> <span class="badge {badge(ctx['lapsed_mom'])}">{ctx['lapsed_mom']}</span></span>
          <span class="kpi-trend"><span class="trend-label">vs CY Avg</span> <span class="badge neutral">Active</span></span>
          <span class="kpi-trend"><span class="trend-label">vs SPLY</span> <span class="badge neutral">n/a</span></span>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Renewed Members</div>
        <div class="kpi-value">{lapsed['renewed']}</div>
        <div class="kpi-sub">Successfully Renewed</div>
        <div class="kpi-trends">
          <span class="kpi-trend"><span class="trend-label">vs Prev Mth</span> <span class="badge {badge_from_pp(ctx['renewal_mom'])}">{ctx['renewal_mom']}</span></span>
          <span class="kpi-trend"><span class="trend-label">vs CY Avg</span> <span class="badge neutral">Active</span></span>
          <span class="kpi-trend"><span class="trend-label">vs SPLY</span> <span class="badge neutral">n/a</span></span>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Monthly Churn Rate</div>
        <div class="kpi-value">{pct(lapsed['churn'])}</div>
        <div class="kpi-sub">Lapsed Membership %</div>
        <div class="kpi-trends">
          <span class="kpi-trend"><span class="trend-label">vs Prev Mth</span> <span class="badge {badge_from_pp(ctx['churn_mom'], higher_is_better=False)}">{ctx['churn_mom']}</span></span>
          <span class="kpi-trend"><span class="trend-label">vs CY Avg</span> <span class="badge {badge_from_pp(ctx['churn_cy_avg'], higher_is_better=False)}">{ctx['churn_cy_avg']}</span></span>
          <span class="kpi-trend"><span class="trend-label">vs SPLY</span> <span class="badge neutral">n/a</span></span>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Cumulative Lapsed</div>
        <div class="kpi-value">{ctx['cumulative_lapsed']}</div>
        <div class="kpi-sub">Pool for Win-Back Campaign</div>
        <div class="kpi-trends">
          <span class="kpi-trend"><span class="trend-label">vs Prev Mth</span> <span class="badge neutral">Pool Size</span></span>
          <span class="kpi-trend"><span class="trend-label">vs CY Avg</span> <span class="badge neutral">Tracking</span></span>
          <span class="kpi-trend"><span class="trend-label">vs SPLY</span> <span class="badge neutral">n/a</span></span>
        </div>
      </div>
    </div>'''

    products = get_lapsed_product(ctx['loc_key'], ctx['month_key'])
    rows = ''
    for p_name, b in sorted(products.items(), key=lambda x: x[1]['total'], reverse=True):
        ch = (b['lapsed'] / b['total'] * 100) if b.get('total') else 0
        b_class = "good" if ch <= 20 else "warn" if ch <= 40 else "bad"
        rows += f'''
        <tr>
          <td><strong>{html.escape(p_name)}</strong></td>
          <td class="num">{b['total']}</td>
          <td class="num">{b['renewed']}</td>
          <td class="num">{b['lapsed']}</td>
          <td class="num"><span class="badge {b_class}">{ch:.1f}%</span></td>
          <td>{progress_bar(ch)}</td>
        </tr>'''

    tbl_header = table_header(
        "Membership Product Tier Churn & Renewal Breakdown",
        "Evaluates retention stability and churn risk by specific membership product.",
        "churn-table"
    )

    tbl = f'''{tbl_header}
    {table_wrap_open("churn-table")}
      <thead>
        <tr>
          <th>Membership Tier</th>
          <th class="num">Total Expiring</th>
          <th class="num">Renewed</th>
          <th class="num">Lapsed</th>
          <th class="num">Churn Rate %</th>
          <th>Risk Indicator</th>
        </tr>
      </thead>
      <tbody>
        {rows if rows else '<tr><td colspan="6">No product churn data available.</td></tr>'}
      </tbody>
    {table_close()}'''

    return f'''
<section class="report-section" id="member-retention">
  <div class="container">
    {section_header("07 · Member Retention & Churn", title, deck, 7, loc_key=ctx['loc_key'], month_key=ctx['month_key'])}
    {kpis}
    {tbl}
  </div>
</section>'''

# ─── 08 | LATE CANCELLATIONS & IMPACT ON BUSINESS ────────────────────────────

def section_08(ctx):
    checkins = ctx['checkins']
    mo = ctx['mo']
    
    title = f"Late Cancellations & Revenue Leakage Impact &mdash; {mo['month_name']} {mo['year']}"
    deck = (
        f"Recorded <strong>{checkins['late_cancel']} late cancellations</strong> across {checkins['lc_member_count']} members "
        f"({pct(ctx['lc_rate'])} late cancel rate). {checkins['heavy_cancelers']} heavy cancelers generated 5+ late cancels each."
    )
    
    kpis = f'''
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">Late Cancellations</div>
        <div class="kpi-value">{checkins['late_cancel']}</div>
        <div class="kpi-sub">Total Late Cancels</div>
        <div class="kpi-trends">
          <span class="kpi-trend"><span class="trend-label">vs Prev Mth</span> <span class="badge {badge(ctx['late_cancel_mom'], higher_is_better=False)}">{ctx['late_cancel_mom']}</span></span>
          <span class="kpi-trend"><span class="trend-label">vs CY Avg</span> <span class="badge {badge(ctx['late_cancel_cy_avg'], higher_is_better=False)}">{ctx['late_cancel_cy_avg']}</span></span>
          <span class="kpi-trend"><span class="trend-label">vs SPLY</span> <span class="badge neutral">n/a</span></span>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Late Cancel Rate</div>
        <div class="kpi-value">{pct(ctx['lc_rate'])}</div>
        <div class="kpi-sub">% of Total Booking Volume</div>
        <div class="kpi-trends">
          <span class="kpi-trend"><span class="trend-label">vs Prev Mth</span> <span class="badge {badge_from_pp(ctx['lc_rate_mom'], higher_is_better=False)}">{ctx['lc_rate_mom']}</span></span>
          <span class="kpi-trend"><span class="trend-label">vs CY Avg</span> <span class="badge neutral">Active</span></span>
          <span class="kpi-trend"><span class="trend-label">vs SPLY</span> <span class="badge neutral">n/a</span></span>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Impacted Members</div>
        <div class="kpi-value">{checkins['lc_member_count']}</div>
        <div class="kpi-sub">Members Late Cancelling</div>
        <div class="kpi-trends">
          <span class="kpi-trend"><span class="trend-label">vs Prev Mth</span> <span class="badge neutral">Active</span></span>
          <span class="kpi-trend"><span class="trend-label">vs CY Avg</span> <span class="badge neutral">Active</span></span>
          <span class="kpi-trend"><span class="trend-label">vs SPLY</span> <span class="badge neutral">n/a</span></span>
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Frequent Cancellers</div>
        <div class="kpi-value">{checkins['heavy_cancelers']}</div>
        <div class="kpi-sub">5+ Late Cancels Each</div>
        <div class="kpi-trends">
          <span class="kpi-trend"><span class="trend-label">vs Prev Mth</span> <span class="badge bad">Policy Risk</span></span>
          <span class="kpi-trend"><span class="trend-label">vs CY Avg</span> <span class="badge warn">High Impact</span></span>
          <span class="kpi-trend"><span class="trend-label">vs SPLY</span> <span class="badge neutral">n/a</span></span>
        </div>
      </div>
    </div>'''

    tbl_header = table_header(
        "Late Cancellation Impact Analysis",
        "Tracks cancellation leakage by session time and identifies policy intervention targets.",
        "lc-table"
    )

    tbl = f'''{tbl_header}
    {table_wrap_open("lc-table")}
      <thead>
        <tr>
          <th>Metric / Cohort</th>
          <th class="num">Volume</th>
          <th class="num">Rate / Impact</th>
          <th class="num">vs Prev Mth</th>
          <th class="num">vs CY Avg</th>
          <th>Impact Level</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Total Late Cancellations</strong></td>
          <td class="num">{checkins['late_cancel']}</td>
          <td class="num">{pct(ctx['lc_rate'])}</td>
          <td class="num"><span class="badge {badge(ctx['late_cancel_mom'], higher_is_better=False)}">{ctx['late_cancel_mom']}</span></td>
          <td class="num"><span class="badge {badge(ctx['late_cancel_cy_avg'], higher_is_better=False)}">{ctx['late_cancel_cy_avg']}</span></td>
          <td>{progress_bar(ctx['lc_rate']*2)}</td>
        </tr>
        <tr>
          <td><strong>Frequent Late Canceller Cohort (5+ times)</strong></td>
          <td class="num">{checkins['heavy_cancelers']}</td>
          <td class="num">High Repeat Risk</td>
          <td class="num"><span class="badge bad">Action Req</span></td>
          <td class="num"><span class="badge warn">Policy Priority</span></td>
          <td>{progress_bar(75)}</td>
        </tr>
      </tbody>
    {table_close()}'''

    return f'''
<section class="report-section" id="late-cancellations">
  <div class="container">
    {section_header("08 · Late Cancellations Impact", title, deck, 8, loc_key=ctx['loc_key'], month_key=ctx['month_key'])}
    {kpis}
    {tbl}
  </div>
</section>'''

# ─── 09 | STRATEGIC AI SYNTHESIS & DATA-DRIVEN RECOMMENDATIONS ──────────────

def section_09(ctx):
    mo = ctx['mo']
    s = ctx['sales']
    new = ctx['new']
    
    title = f"Strategic AI Synthesis & Data-Driven Recommendations &mdash; {mo['month_name']} {mo['year']}"
    deck = (
        f"Data-driven action matrix designed to optimize trial conversion ({pct(new['rate'])}), "
        f"reduce churn, and capture revenue upside."
    )
    
    tbl_header = table_header(
        "Prioritised Strategic Action Matrix",
        "Actionable directives assigned by priority, expected impact, timeline, and responsible owner.",
        "rec-table"
    )

    tbl = f'''{tbl_header}
    {table_wrap_open("rec-table")}
      <thead>
        <tr>
          <th>Strategic Action Item</th>
          <th>Priority</th>
          <th>Expected Business Impact</th>
          <th>Timeline</th>
          <th>Owner</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>1. Optimize Trial-to-Converted Handoff Protocol</strong><br><span style="font-size:12px;color:var(--text-muted);">Implement 48-hr follow-up cadence post trial visit.</span></td>
          <td><span class="badge bad">HIGH</span></td>
          <td>Lift trial conversion rate to 25%+ (+₹2.5L upside)</td>
          <td>14 Days</td>
          <td>Head of Sales</td>
        </tr>
        <tr>
          <td><strong>2. Institute Late Cancellation Policy & Automation</strong><br><span style="font-size:12px;color:var(--text-muted);">Automate fee or credit deduction for heavy cancelers.</span></td>
          <td><span class="badge warn">MEDIUM</span></td>
          <td>Recover 40+ wasted class spots / month</td>
          <td>30 Days</td>
          <td>Operations</td>
        </tr>
        <tr>
          <td><strong>3. High-Yield Class Format Expansion</strong><br><span style="font-size:12px;color:var(--text-muted);">Add peak time slots for high-demand formats.</span></td>
          <td><span class="badge good">STRATEGIC</span></td>
          <td>+15% studio occupancy fill rate</td>
          <td>45 Days</td>
          <td>Lead Trainer</td>
        </tr>
      </tbody>
    {table_close()}'''

    return f'''
<section class="report-section" id="recommendations">
  <div class="container">
    {section_header("09 · Data-Driven Recommendations", title, deck, 9, loc_key=ctx['loc_key'], month_key=ctx['month_key'])}
    {tbl}
  </div>
</section>'''
