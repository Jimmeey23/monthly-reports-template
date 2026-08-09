#!/usr/bin/env python3
"""
Section generators for the parameterized performance report.
Each function takes a context dict and returns HTML for one section.
"""
import calendar
import json
import html

AI_CONTEXT = {}

# Import helpers and data access functions from gen_report_v2
# These are imported lazily to avoid circular import issues

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

# Wrapper functions that use the lazily-imported versions
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

# ─── Reusable HTML components ─────────────────────────────────────────────────

SECTION_IDS = {
    1: 'executive-summary', 2: 'revenue-performance', 3: 'conversion-funnel',
    4: 'sessions', 5: 'lapsed', 6: 'recommendations', 7: 'predictions',
}



def render_ai_result(result):
    if not result:
        return ''
    
    ps = result.get('performance_summary', {})
    insights = result.get('key_insights') or result.get('insights') or []
    highlights = result.get('highlights', [])
    recs = result.get('recommendations', [])
    
    def safe_html(s):
        if s is None: return ''
        return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
    def safe_val(s):
        if not s or str(s).strip() == '—': return '—'
        return str(s).strip()

    # Summary
    title = safe_html(ps.get('title', 'Performance Overview'))
    narrative = safe_html(ps.get('narrative', ''))
    patterns_html = ''
    if ps.get('patterns'):
        patterns_html = '<div class="ai-patterns-wrap"><div class="ai-sub-label">Identified Patterns</div>'
        for p in ps['patterns']:
            patterns_html += f'<div class="ai-pattern-card"><div class="ai-pattern-name">&#128269; {safe_html(p.get("pattern", ""))}</div><div class="ai-pattern-desc">{safe_html(p.get("description", ""))}</div></div>'
        patterns_html += '</div>'
    summary_html = f'<div class="ai-summary-narrative">{narrative}</div>{patterns_html}'

    # Insights
    insights_html = ''
    for i, ins in enumerate(insights):
        badge = f'<span class="ai-insight-badge {safe_html(ins.get("classification", "")).lower()}">{safe_html(ins.get("classification", ""))}</span>' if ins.get("classification") else ''
        evidence = f'<div class="ai-evidence"><span class="ai-evidence-label">&#128202; Data:</span> {safe_html(ins.get("data_evidence", ""))}</div>' if ins.get("data_evidence") else ''
        insights_html += f'<div class="insight-card"><div class="insight-num">{str(i+1).zfill(2)}</div><div class="insight-body"><div class="insight-title-row">{badge}<div class="insight-title">{safe_html(ins.get("title", ""))}</div></div><div class="insight-text">{safe_html(ins.get("text", ""))}</div>{evidence}</div></div>'

    # Highlights
    highlights_html = '<div class="ai-highlights-grid">'
    for h in highlights:
        is_ach = str(h.get('type', '')).lower() == 'achievement'
        color = '#10b981' if is_ach else '#f59e0b'
        icon = '&#9650;' if is_ach else '&#9660;'
        t_label = 'Achievement' if is_ach else 'Area to Improve'
        highlights_html += f'<div class="ai-highlight-card" style="border-left-color:{color}"><div class="ai-highlight-header"><span class="ai-highlight-icon" style="color:{color}">{icon}</span><span class="ai-highlight-metric">{safe_html(safe_val(h.get("metric")))}</span><span class="ai-highlight-type-badge" style="background:{color}18;color:{color};border:1px solid {color}44;">{t_label}</span></div><div class="ai-highlight-headline">{safe_html(safe_val(h.get("headline")))}</div><div class="ai-highlight-magnitude" style="color:{color}">{safe_html(safe_val(h.get("magnitude")))}</div><div class="ai-highlight-detail">{safe_html(safe_val(h.get("detail")))}</div></div>'
    highlights_html += '</div>'

    # Recs
    recs_html = ''
    for i, r in enumerate(recs):
        pri = safe_val(r.get('priority', '')).lower()
        pri_badge = f'<span class="meta-pill" style="background:var(--bg-inset);color:var(--text);border:1px solid var(--border);font-weight:600;">{pri.upper()}</span>' if pri and pri != '—' else ''
        recs_html += f'<div class="ai-rec-card"><div class="ai-rec-num">{str(i+1).zfill(2)}</div><div class="ai-rec-content"><div class="ai-rec-title">{safe_html(safe_val(r.get("title")))}</div><div class="ai-rec-desc">{safe_html(safe_val(r.get("description")))}</div><div class="ai-rec-impact"><span class="ai-rec-impact-label">&#127919; Expected Impact:</span> {safe_html(safe_val(r.get("expected_impact")))}</div><div class="ai-rec-meta">{pri_badge}<span class="meta-pill">&#128197; {safe_html(safe_val(r.get("timeline")))}</span><span class="meta-pill">&#128100; {safe_html(safe_val(r.get("owner")))}</span></div></div></div>'

    sections_arr = [
        f'<div class="ai-section"><button type="button" class="ai-section-toggle is-open" data-target="summary"><span class="ai-section-icon">&#128203;</span><span class="ai-section-label">{title}</span><span class="ai-section-chevron">&#9660;</span></button><div class="ai-section-body is-open" id="ai-body-summary">{summary_html}</div></div>',
        f'<div class="ai-section"><button type="button" class="ai-section-toggle is-open" data-target="insights"><span class="ai-section-icon">&#128161;</span><span class="ai-section-label">Key Insights ({len(insights)})</span><span class="ai-section-chevron">&#9660;</span></button><div class="ai-section-body is-open" id="ai-body-insights">{insights_html}</div></div>',
        f'<div class="ai-section"><button type="button" class="ai-section-toggle is-open" data-target="highlights"><span class="ai-section-icon">&#11088;</span><span class="ai-section-label">Highlights & Standouts ({len(highlights)})</span><span class="ai-section-chevron">&#9660;</span></button><div class="ai-section-body is-open" id="ai-body-highlights">{highlights_html}</div></div>',
        f'<div class="ai-section"><button type="button" class="ai-section-toggle" data-target="recs"><span class="ai-section-icon">&#127919;</span><span class="ai-section-label">Recommendations ({len(recs)})</span><span class="ai-section-chevron">&#9660;</span></button><div class="ai-section-body" id="ai-body-recs">{recs_html}</div></div>'
    ]

    inner = "".join(sections_arr)
    return f'<div class="ai-result ai-result-v2"><div class="ai-result-header"><div class="ai-result-header-icon">&#10024;</div><div><div class="ai-result-header-title">AI-Powered Analysis</div><div class="ai-result-header-sub">Deep insights generated from your data — fully curated.</div></div></div>{inner}</div>'


def section_header(eyebrow, title, deck, section_num, total=7, loc_key='', month_key='', id_suffix=''):
    section_id = SECTION_IDS.get(section_num, f'section-{section_num}')
    slot_id = f'ai-slot-{section_id}{id_suffix}'
    return f'''    <div class="section-hero" data-num="{section_num:02d}">
      <div class="section-header">
        <div class="section-header-left">
          <span class="section-eyebrow">{eyebrow}</span>
          <h2 class="section-title">{title}</h2>
          <p class="section-deck">{deck}</p>
        </div>
        <div class="section-header-right">
          <div class="section-anchor">Section {section_num} / {total:02d}</div>
        </div>
      </div>
    </div>
    <div class="ai-slot" id="{slot_id}">{render_ai_result(AI_CONTEXT.get(f"{loc_key}|{month_key}|{section_id}", {}))}</div>'''


def subsection(title, deck):
    return f'''    <div class="subsection">
      <h3 class="subsection-title">{title}</h3>
      <p class="subsection-deck">{deck}</p>
    </div>'''


def insight_card(num, title, text):
    return f'''    <div class="insight-card">
      <div class="insight-num">{num}</div>
      <div class="insight-body">
        <div class="insight-title">{title}</div>
        <div class="insight-text">{text}</div>
      </div>
    </div>'''


def callout(text):
    return f'''    <div class="callout">{text}</div>'''


def split_open(pane_title, data_title):
    return f'''    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">{pane_title}</div>
'''

def split_mid(data_title):
    return f'''      </div>
      <div class="data-pane">
        <div class="pane-title" style="padding: 16px 16px 8px;">{data_title}</div>
'''

def split_close():
    return '''      </div>
    </div>'''


def table_wrap_open():
    return '''        <div class="table-wrap">
          <table class="data-table">'''

def table_close():
    return '''          </table>
        </div>'''


def funnel_stages(stages):
    """stages = [(num, label, sub, is_conv), ...]"""
    html = '    <div class="funnel-stages">\n'
    for num, label, sub, is_conv in stages:
        cls = 'funnel-stage conv' if is_conv else 'funnel-stage'
        html += f'      <div class="{cls}">\n'
        html += f'        <div class="funnel-stage-num">{num}</div>\n'
        html += f'        <div class="funnel-stage-label">{label}</div>\n'
        html += f'        <div class="funnel-stage-sub">{sub}</div>\n'
        html += f'      </div>\n'
    html += '    </div>\n'
    return html


# ─── Section 01: Executive Summary ────────────────────────────────────────────

def section_01(ctx):
    loc = ctx['loc']
    mo = ctx['mo']
    s = ctx['sales']
    sess = ctx['sessions']
    leads = ctx['leads']
    new = ctx['new']
    lapsed = ctx['lapsed']
    baseline = ctx['baseline']
    
    loc_name = loc['short_name']
    month_name = mo['month_name']
    prev_name = mo['prev_month_name']
    
    # Build insights based on actual data
    insights = build_section_01_insights(ctx)
    
    # Build KPI table
    kpi_table = build_section_01_kpi_table(ctx)
    
    # Build executive narrative
    net_baseline_diff = ((s['net'] - baseline['sales']['net']) / baseline['sales']['net']) * 100
    
    title = f"{month_name} delivered {'strong' if net_baseline_diff > 5 else 'steady' if net_baseline_diff > -5 else 'soft'} revenue at {lakh(s['net'])} net &mdash; {'above' if net_baseline_diff > 0 else 'below'} the {ctx['baseline_label']} baseline, with {'improving' if ctx['conv_mom'].startswith('+') else 'declining'} conversion and {'stabilising' if ctx['churn_mom'].startswith('-') else 'rising'} churn as the key watchpoints."
    
    deck = (
        f"Headline revenue closed at <strong>{lakh(s['net'])} net</strong> "
        f"({lakh(s['gross'])} gross, {lakh(s['disc'])} discount), which is "
        f"<strong>{ctx['net_baseline']} vs the {ctx['baseline_label']} baseline</strong> of {lakh(baseline['sales']['net'])}. "
        f"The MoM figure is {ctx['net_mom']} vs {prev_name}. "
        f"Conversion rate is {pct(leads['rate'])} ({leads['converted']} of {leads['total']} leads), "
        f"{'up' if ctx['conv_mom'].startswith('+') else 'down'} {ctx['conv_mom']} MoM. "
        f"Churn rate stands at {pct(lapsed['churn'])}, {'improving' if ctx['churn_mom'].startswith('-') else 'deteriorating'} {ctx['churn_mom']} MoM. "
        f"Discount efficiency is &#8377;{s['disc_eff']:.2f} of revenue collected per &#8377;1 discounted."
    )
    
    html = f'''
<section class="report-section" id="executive-summary{ctx.get('id_suffix', '')}">
  <div class="container">
{section_header(f"01 &middot; Executive Summary", title, deck, 1, loc_key=ctx["loc_key"], month_key=ctx["month_key"], id_suffix=ctx.get("id_suffix", ""))}

    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">Key Insights &middot; {month_name} {ctx['mo']['year']}</div>

{insights}
      </div>

      <div class="data-pane">
        <div class="pane-title" style="padding: 16px 16px 8px;">Headline KPI Table &middot; {month_name} vs {prev_name} vs {ctx['baseline_label']} Baseline</div>
{kpi_table}
      </div>
    </div>
  </div>
</section>
'''
    return html


def build_section_01_insights(ctx):
    """Generate 7 insight cards for executive summary based on actual data."""
    s = ctx['sales']
    sess = ctx['sessions']
    leads = ctx['leads']
    new = ctx['new']
    lapsed = ctx['lapsed']
    checkins = ctx['checkins']
    baseline = ctx['baseline']
    mo = ctx['mo']
    
    insights = []
    
    # 01: Revenue vs baseline
    net_bl = baseline['sales']['net']
    bl_diff = pct_change(net_bl, s['net'])
    insights.append(insight_card(
        "01",
        f"{'Baseline-plus' if s['net'] > net_bl else 'Below-baseline'} revenue at {lakh(s['net'])} net.",
        f"Net sales of <strong>{lakh(s['net'])}</strong> sit <strong>{bl_diff} vs the {ctx['baseline_label']} average</strong> of {lakh(net_bl)}. "
        f"The MoM figure is {ctx['net_mom']} vs {mo['prev_month_name']}. "
        f"Gross sales of {lakh(s['gross'])} on {int(s['sales'])} transactions at an ATV of {rupee(s['atv'])}."
    ))
    
    # 02: Conversion & funnel
    conv_rate = leads['rate']
    conv_bl = baseline['leads']['rate']
    conv_bl_diff = pp_change(conv_bl, conv_rate)
    insights.append(insight_card(
        "02",
        f"Conversion rate at {pct(conv_rate)} &mdash; {conv_bl_diff} vs baseline.",
        f"{leads['converted']} of {leads['total']} leads converted ({pct(conv_rate)}), "
        f"{'up' if ctx['conv_mom'].startswith('+') else 'down'} {ctx['conv_mom']} MoM and {conv_bl_diff} vs the {ctx['baseline_label']} baseline of {pct(conv_bl)}. "
        f"Trials: {new['trials']}, retained: {new['retained']} ({pct(ctx['trial_retention'])} retention)."
    ))
    
    # 03: Churn
    churn = lapsed['churn']
    churn_bl = baseline['lapsed']['churn']
    churn_bl_diff = pp_change(churn_bl, churn)
    insights.append(insight_card(
        "03",
        f"Churn rate at {pct(churn)} &mdash; {ctx['churn_mom']} MoM, {churn_bl_diff} vs baseline.",
        f"Of {lapsed['total']} memberships reaching end-of-life, {lapsed['renewed']} renewed ({pct(lapsed['renewal_rate'])}), "
        f"{lapsed['lapsed']} lapsed ({pct(churn)} churn). "
        f"Renewal rate is {ctx['renewal_baseline']} vs the {ctx['baseline_label']} baseline of {pct(baseline['lapsed']['renewal_rate'])}."
    ))
    
    # 04: Discount efficiency
    disc_eff = s['disc_eff']
    disc_eff_bl = baseline['sales']['disc_eff']
    insights.append(insight_card(
        "04",
        f"Discount efficiency at &#8377;{disc_eff:.2f} per &#8377;1 discounted.",
        f"Discount value of {lakh(s['disc'])} against {lakh(s['gross'])} gross &mdash; "
        f"discount penetration of {pct(ctx['disc_penetration'])}. "
        f"Efficiency is {ctx['disc_eff_baseline']} vs the {ctx['baseline_label']} baseline of &#8377;{disc_eff_bl:.2f}. "
        f"{'Discipline is holding' if disc_eff >= disc_eff_bl else 'Efficiency has eroded vs baseline'}."
    ))
    
    # 05: Sessions & fill
    insights.append(insight_card(
        "05",
        f"{sess['sessions']} sessions, {fmt_int(sess['visits'])} visits, {pct(sess['fill'])} fill rate.",
        f"Session volume is {ctx['sessions_mom']} MoM and {ctx['sessions_baseline']} vs baseline. "
        f"Fill rate is {ctx['fill_mom']} MoM and {ctx['fill_baseline']} vs the {ctx['baseline_label']} baseline of {pct(baseline['sessions']['fill'])}. "
        f"Average class size: {sess['avg_visits']:.1f} visits/session."
    ))
    
    # 06: Lead pipeline
    leads_bl = baseline['leads']['total']
    leads_bl_diff = pct_change(leads_bl, leads['total'])
    insights.append(insight_card(
        "06",
        f"Lead pipeline at {leads['total']} leads &mdash; {leads_bl_diff} vs baseline.",
        f"Leads are {ctx['leads_mom']} MoM vs {mo['prev_month_name']} and {leads_bl_diff} vs the {ctx['baseline_label']} baseline of {leads_bl:.0f}. "
        f"The pipeline {'needs replenishment' if leads['total'] < leads_bl else 'is healthy vs baseline'}. "
        f"Top source: {get_top_lead_source(ctx)}."
    ))
    
    # 07: Late cancels
    lc = checkins['late_cancel']
    lc_members = checkins['lc_member_count']
    heavy = checkins['heavy_cancelers']
    insights.append(insight_card(
        "07",
        f"{lc} late cancels across {lc_members} members &mdash; {heavy} heavy cancelers.",
        f"Late-cancel rate is {pct(ctx['lc_rate'])} of all check-ins ({ctx['lc_rate_mom']} MoM). "
        f"{heavy} members account for 5+ cancels each. "
        f"Total penalty collected: <strong>&#8377;0</strong>. A policy intervention here is a near-zero-risk win."
    ))
    
    return "\n".join(insights)


def get_top_lead_source(ctx):
    """Get the top lead source by volume."""
    sources = get_leads_source(ctx['loc_key'], ctx['month_key'])
    if not sources:
        return "n/a"
    top = max(sources.items(), key=lambda x: x[1]['total'])
    return f"{top[0]} ({top[1]['total']} leads, {top[1]['converted']} converted)"


def build_section_01_kpi_table(ctx):
    """Build the headline KPI comparison table."""
    s = ctx['sales']
    sess = ctx['sessions']
    leads = ctx['leads']
    new = ctx['new']
    lapsed = ctx['lapsed']
    checkins = ctx['checkins']
    baseline = ctx['baseline']
    prev_s = ctx['prev_sales']
    prev_sess = ctx['prev_sessions']
    prev_leads = ctx['prev_leads']
    prev_new = ctx['prev_new']
    prev_lapsed = ctx['prev_lapsed']
    prev_checkins = ctx['prev_checkins']
    
    def row(metric, current_disp, prev_disp, baseline_disp, mom_str, current_raw=None, baseline_raw=None, higher_better=True):
        mom_b = badge(mom_str, higher_better)
        if baseline_raw is not None and current_raw is not None:
            bl_str = pct_change(baseline_raw, current_raw)
            bl_b = badge(bl_str, higher_better)
        else:
            bl_str = "n/a"
            bl_b = "neutral"
        return f'''            <tr>
              <td>{metric}</td>
              <td class="num">{current_disp}</td>
              <td class="num">{prev_disp}</td>
              <td class="num">{baseline_disp}</td>
              <td><span class='badge {mom_b}'>{mom_str}</span></td>
              <td><span class='badge {bl_b}'>{bl_str}</span></td>
            </tr>'''
    
    def row_pp(metric, current_disp, prev_disp, baseline_disp, mom_str, current_raw=None, baseline_raw=None, higher_better=True):
        mom_b = badge_from_pp(mom_str, higher_better)
        if baseline_raw is not None and current_raw is not None:
            bl_str = pp_change(baseline_raw, current_raw)
            bl_b = badge_from_pp(bl_str, higher_better)
        else:
            bl_str = "n/a"
            bl_b = "neutral"
        return f'''            <tr>
              <td>{metric}</td>
              <td class="num">{current_disp}</td>
              <td class="num">{prev_disp}</td>
              <td class="num">{baseline_disp}</td>
              <td><span class='badge {mom_b}'>{mom_str}</span></td>
              <td><span class='badge {bl_b}'>{bl_str}</span></td>
            </tr>'''
    
    rows = []
    rows.append(row("Net Sales", lakh(s['net']), lakh(prev_s.get('net',0)), lakh(baseline['sales']['net']), ctx['net_mom'], current_raw=s['net'], baseline_raw=baseline['sales']['net']))
    rows.append(row("Gross Sales", lakh(s['gross']), lakh(prev_s.get('gross',0)), lakh(baseline['sales']['gross']), ctx['gross_mom'], current_raw=s['gross'], baseline_raw=baseline['sales']['gross']))
    rows.append(row("Discount Value", lakh(s['disc']), lakh(prev_s.get('disc',0)), lakh(baseline['sales']['disc']), ctx['disc_mom'], current_raw=s['disc'], baseline_raw=baseline['sales']['disc'], higher_better=False))
    rows.append(row("Transactions", fmt_int(s['sales']), fmt_int(prev_s.get('sales',0)), f"{baseline['sales']['sales']:.0f}", ctx['sales_count_mom'], current_raw=s['sales'], baseline_raw=baseline['sales']['sales']))
    rows.append(row("Unique Buyers", fmt_int(s['members']), fmt_int(prev_s.get('members',0)), f"{baseline['sales']['members']:.0f}", ctx['members_mom'], current_raw=s['members'], baseline_raw=baseline['sales']['members']))
    rows.append(row("ATV", rupee(s['atv']), rupee(prev_s.get('atv',0)), rupee(baseline['sales']['atv']), ctx['atv_mom'], current_raw=s['atv'], baseline_raw=baseline['sales']['atv']))
    rows.append(row("Disc Efficiency", f"&#8377;{s['disc_eff']:.2f}", f"&#8377;{prev_s.get('disc_eff',0):.2f}", f"&#8377;{baseline['sales']['disc_eff']:.2f}", ctx['disc_eff_mom'], current_raw=s['disc_eff'], baseline_raw=baseline['sales']['disc_eff']))
    rows.append(row("Sessions", fmt_int(sess['sessions']), fmt_int(prev_sess.get('sessions',0)), f"{baseline['sessions']['sessions']:.0f}", ctx['sessions_mom'], current_raw=sess['sessions'], baseline_raw=baseline['sessions']['sessions']))
    rows.append(row("Visits", fmt_int(sess['visits']), fmt_int(prev_sess.get('visits',0)), f"{baseline['sessions']['visits']:.0f}", ctx['visits_mom'], current_raw=sess['visits'], baseline_raw=baseline['sessions']['visits']))
    rows.append(row_pp("Fill Rate", pct(sess['fill']), pct(prev_sess.get('fill',0)), pct(baseline['sessions']['fill']), ctx['fill_mom'], current_raw=sess['fill'], baseline_raw=baseline['sessions']['fill']))
    rows.append(row("Leads", fmt_int(leads['total']), fmt_int(prev_leads.get('total',0)), f"{baseline['leads']['total']:.0f}", ctx['leads_mom'], current_raw=leads['total'], baseline_raw=baseline['leads']['total']))
    rows.append(row_pp("Conv Rate", pct(leads['rate']), pct(prev_leads.get('rate',0)), pct(baseline['leads']['rate']), ctx['conv_mom'], current_raw=leads['rate'], baseline_raw=baseline['leads']['rate']))
    rows.append(row("Converted", fmt_int(leads['converted']), fmt_int(prev_leads.get('converted',0)), f"{baseline['leads']['converted']:.0f}", ctx['converted_mom'], current_raw=leads['converted'], baseline_raw=baseline['leads']['converted']))
    rows.append(row("Trials", fmt_int(new['trials']), fmt_int(prev_new.get('trials',0)), "n/a", ctx['trials_mom']))
    rows.append(row("Retained", fmt_int(new['retained']), fmt_int(prev_new.get('retained',0)), "n/a", ctx['retained_mom']))
    rows.append(row_pp("Churn Rate", pct(lapsed['churn']), pct(prev_lapsed.get('churn',0)), pct(baseline['lapsed']['churn']), ctx['churn_mom'], current_raw=lapsed['churn'], baseline_raw=baseline['lapsed']['churn'], higher_better=False))
    rows.append(row_pp("Renewal Rate", pct(lapsed['renewal_rate']), pct(prev_lapsed.get('renewal_rate',0)), pct(baseline['lapsed']['renewal_rate']), ctx['renewal_mom'], current_raw=lapsed['renewal_rate'], baseline_raw=baseline['lapsed']['renewal_rate']))
    rows.append(row("Lapsed Members", fmt_int(lapsed['lapsed']), fmt_int(prev_lapsed.get('lapsed',0)), f"{baseline['lapsed']['lapsed']:.0f}", ctx['lapsed_mom'], current_raw=lapsed['lapsed'], baseline_raw=baseline['lapsed']['lapsed'], higher_better=False))
    rows.append(row("Late Cancels", fmt_int(checkins['late_cancel']), fmt_int(prev_checkins.get('late_cancel',0)), "n/a", ctx['late_cancel_mom'], higher_better=False))
    
    return f'''        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Metric</th>
                <th>{ctx['mo']['month_short']} {ctx['mo']['year']}</th>
                <th>{ctx['mo']['prev_month_name']}</th>
                <th>{ctx['baseline_label']} avg</th>
                <th>MoM</th>
                <th>vs Baseline</th>
              </tr>
            </thead>
            <tbody>
{chr(10).join(rows)}
            </tbody>
          </table>
        </div>'''


# ─── Section 02: Revenue & Sales Performance ──────────────────────────────────

def section_02(ctx):
    loc = ctx['loc']
    mo = ctx['mo']
    s = ctx['sales']
    
    loc_name = loc['short_name']
    month_name = mo['month_name']
    
    bd = get_sales_breakdowns(ctx['loc_key'], ctx['month_key'])
    cat_bd = bd.get('category', {})
    prod_bd = bd.get('product', {})
    seller_bd = bd.get('seller', {})
    payment_bd = bd.get('payment', {})
    
    # Sort categories by net revenue
    cats = sorted(cat_bd.items(), key=lambda x: -x[1]['net'])
    total_net = sum(v['net'] for v in cat_bd.values())
    
    # Build category insights
    cat_insights = build_category_insights(ctx, cats, total_net)
    
    # Build category table
    cat_table = build_category_table(ctx, cats, total_net)
    
    # Build product table (top 10)
    prods = sorted(prod_bd.items(), key=lambda x: -x[1]['net'])[:10]
    prod_table = build_product_table(ctx, prods, total_net)
    
    # Build seller table
    sellers = sorted(seller_bd.items(), key=lambda x: -x[1]['gross'])
    seller_table = build_seller_table(ctx, sellers, s['gross'])
    
    # Build payment table
    payments = sorted(payment_bd.items(), key=lambda x: -x[1]['gross'])
    payment_table = build_payment_table(ctx, payments, s['gross'])
    
    # Top category name for title
    top_cat = cats[0] if cats else ("n/a", {'net':0})
    top_cat_name = top_cat[0]
    top_cat_share = (top_cat[1]['net'] / total_net * 100) if total_net else 0
    
    title = (f"{top_cat_name} carry {pct(top_cat_share, 0)} of revenue, "
             f"{'with healthy category diversification across the portfolio' if len(cats) > 4 else 'with concentration in a few lines'}, "
             f"and the studio&rsquo;s payment mix is {'diverse' if len(payments) > 3 else 'concentrated'} at {len(payments)} methods.")
    
    deck = (f"{month_name} {ctx['mo']['year']} closed at <strong>{lakh(s['net'])} net</strong> on {int(s['sales'])} transactions, "
            f"an ATV of <strong>{rupee(s['atv'])}</strong>. "
            f"{top_cat_name} and {cats[1][0] if len(cats)>1 else 'Class Packages'} together account for "
            f"<strong>{pct((cats[0][1]['net']+cats[1][1]['net'])/total_net*100, 0) if len(cats)>1 else pct(top_cat_share,0)} of revenue</strong>. "
            f"Discount value of {lakh(s['disc'])} represents {pct(ctx['disc_penetration'])} of gross. "
            f"Payment mix: {', '.join(payment_share_str(payments[:3], s['gross']))}.")
    
    html = f'''
<section class="report-section" id="revenue-performance{ctx.get('id_suffix', '')}">
  <div class="container">
{section_header("02 &middot; Revenue &amp; Sales Performance", title, deck, 2, loc_key=ctx["loc_key"], month_key=ctx["month_key"], id_suffix=ctx.get("id_suffix", ""))}

{subsection("Sales by Category &mdash; revenue mix and unit economics",
    "The category table below holds every metric available &mdash; revenue, units, ATV, share of revenue &mdash; so each line can be evaluated on absolute size and per-unit economics.")}

    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">Category-level insights</div>

{cat_insights}
      </div>

      <div class="data-pane">
        <div class="pane-title" style="padding: 16px 16px 8px;">Sales by Category &middot; {month_name} {ctx['mo']['year']}</div>
{cat_table}
      </div>
    </div>

{subsection("Top products &mdash; the revenue drivers",
    f"The product-level view below shows the top 10 SKUs by net revenue, with gross, discount, units, and ATV for each.")}

    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">Product-level insights</div>

{build_product_insights(ctx, prods, total_net)}
      </div>

      <div class="data-pane">
        <div class="pane-title" style="padding: 16px 16px 8px;">Top 10 Products by Net Revenue &middot; {month_name} {ctx['mo']['year']}</div>
{prod_table}
      </div>
    </div>

{subsection("Seller attribution &mdash; who drove the revenue",
    "Sales attributed to individual sellers (front desk / sales staff). The '-' row represents online/self-service transactions with no attributed seller.")}

    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">Seller-level insights</div>

{build_seller_insights(ctx, sellers, s['gross'])}
      </div>

      <div class="data-pane">
        <div class="pane-title" style="padding: 16px 16px 8px;">Sales by Seller &middot; {month_name} {ctx['mo']['year']}</div>
{seller_table}
      </div>
    </div>

{subsection("Payment method mix &mdash; how customers paid",
    "The payment method breakdown shows the split between in-studio (custom/cash), online (stripe), and split payments.")}

    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">Payment-level insights</div>

{build_payment_insights(ctx, payments, s['gross'])}
      </div>

      <div class="data-pane">
        <div class="pane-title" style="padding: 16px 16px 8px;">Sales by Payment Method &middot; {month_name} {ctx['mo']['year']}</div>
{payment_table}
      </div>
    </div>
  </div>
</section>
'''
    return html


def payment_share_str(payments, total_gross):
    """Helper to build payment share strings without f-string backslash issues."""
    result = []
    for k, v in payments:
        share = (v['gross'] / total_gross * 100) if total_gross else 0
        display = k.replace('-', ' ').title() if k != '-' else 'Other'
        result.append(f"{display} ({pct(share, 0)})")
    return result


def build_category_insights(ctx, cats, total_net):
    insights = []
    for i, (name, v) in enumerate(cats[:7], 1):
        share = (v['net'] / total_net * 100) if total_net else 0
        atv = v['net'] / v['rows'] if v['rows'] else 0
        disc_ratio = (v['disc'] / v['gross'] * 100) if v['gross'] else 0
        
        if i == 1:
            title = f"{name} anchor {pct(share, 0)} of revenue."
            text = (f"{name} contributed <strong>{lakh(v['net'])} ({pct(share, 0)})</strong> of total net revenue "
                    f"on {v['rows']} units at an ATV of {rupee(atv)}. "
                    f"Discount intensity is {pct(disc_ratio)} ({lakh(v['disc'])} of {lakh(v['gross'])} gross). "
                    f"This is the {'highest' if share > 30 else 'core'}-leverage line in the studio.")
        elif disc_ratio > 50:
            title = f"{name} are structurally over-discounted."
            text = (f"{v['rows']} units sold for {lakh(v['net'])} revenue against <strong>{lakh(v['disc'])} in discounts</strong> "
                    f"&mdash; the discount is {mult(v['disc']/v['net']) if v['net'] else 'n/a'} the net revenue. "
                    f"This line should be repriced or reviewed for discount discipline.")
        elif share < 5:
            title = f"{name} is a minor but present line."
            text = (f"{v['rows']} units at {rupee(atv)} ATV for {lakh(v['net'])} ({pct(share, 0)}). "
                    f"{'Discount intensity is clean at ' + pct(disc_ratio) + '.' if disc_ratio < 5 else 'Discount intensity at ' + pct(disc_ratio) + ' warrants review.'}")
        else:
            title = f"{name} contribute {pct(share, 0)} of revenue."
            text = (f"{v['rows']} units at {rupee(atv)} ATV produced <strong>{lakh(v['net'])} ({pct(share, 0)})</strong>. "
                    f"Discount intensity is {pct(disc_ratio)} &mdash; "
                    f"{'the cleanest line in the portfolio.' if disc_ratio < 5 else 'moderate discount pressure.'}")
        
        insights.append(insight_card(f"{i:02d}", title, text))
    
    return "\n".join(insights)


def build_category_table(ctx, cats, total_net):
    rows = []
    for name, v in cats:
        share = (v['net'] / total_net * 100) if total_net else 0
        atv = v['net'] / v['rows'] if v['rows'] else 0
        disc_ratio = (v['disc'] / v['gross'] * 100) if v['gross'] else 0
        rows.append(f'''            <tr>
              <td>{name}</td>
              <td class="num">{lakh(v['net'])}</td>
              <td class="num">{lakh(v['gross'])}</td>
              <td class="num">{lakh(v['disc'])}</td>
              <td class="num">{v['rows']}</td>
              <td class="num">{rupee(atv)}</td>
              <td class="num">{pct(share, 0)}</td>
              <td class="num">{pct(disc_ratio)}</td>
            </tr>''')
    
    total_gross = sum(v['gross'] for v in cat_bd_values(cats))
    total_disc = sum(v['disc'] for v in cat_bd_values(cats))
    total_rows = sum(v['rows'] for v in cat_bd_values(cats))
    
    rows.append(f'''            <tr class="total-row">
              <td>Total</td>
              <td class="num">{lakh(total_net)}</td>
              <td class="num">{lakh(total_gross)}</td>
              <td class="num">{lakh(total_disc)}</td>
              <td class="num">{total_rows}</td>
              <td class="num">{rupee(total_net/total_rows) if total_rows else 'n/a'}</td>
              <td class="num">100%</td>
              <td class="num">{pct(total_disc/total_gross*100) if total_gross else 'n/a'}</td>
            </tr>''')
    
    return f'''        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Category</th>
                <th>Net Rev</th>
                <th>Gross Rev</th>
                <th>Discount</th>
                <th>Units</th>
                <th>ATV</th>
                <th>Share</th>
                <th>Disc %</th>
              </tr>
            </thead>
            <tbody>
{chr(10).join(rows)}
            </tbody>
          </table>
        </div>'''


def cat_bd_values(cats):
    return [v for _, v in cats]


def build_product_table(ctx, prods, total_net):
    rows = []
    for name, v in prods:
        share = (v['net'] / total_net * 100) if total_net else 0
        atv = v['net'] / v['rows'] if v['rows'] else 0
        disc_ratio = (v['disc'] / v['gross'] * 100) if v['gross'] else 0
        rows.append(f'''            <tr>
              <td>{name}</td>
              <td class="num">{lakh(v['net'])}</td>
              <td class="num">{lakh(v['gross'])}</td>
              <td class="num">{lakh(v['disc'])}</td>
              <td class="num">{v['rows']}</td>
              <td class="num">{rupee(atv)}</td>
              <td class="num">{pct(share, 0)}</td>
            </tr>''')
    
    return f'''        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Net Rev</th>
                <th>Gross Rev</th>
                <th>Discount</th>
                <th>Units</th>
                <th>ATV</th>
                <th>Share</th>
              </tr>
            </thead>
            <tbody>
{chr(10).join(rows)}
            </tbody>
          </table>
        </div>'''


def build_product_insights(ctx, prods, total_net):
    insights = []
    for i, (name, v) in enumerate(prods[:6], 1):
        share = (v['net'] / total_net * 100) if total_net else 0
        atv = v['net'] / v['rows'] if v['rows'] else 0
        
        if i == 1:
            title = f"{name} is the single largest revenue SKU."
            text = (f"{v['rows']} units at {rupee(atv)} ATV produced <strong>{lakh(v['net'])} ({pct(share, 0)} of total)</strong>. "
                    f"Discount of {lakh(v['disc'])} on {lakh(v['gross'])} gross.")
        elif i <= 3:
            title = f"{name} is a top-3 revenue driver."
            text = (f"{v['rows']} units at {rupee(atv)} ATV for {lakh(v['net'])} ({pct(share, 0)}). "
                    f"{'Clean pricing' if v['disc'] < v['net']*0.1 else 'Discount pressure visible'}.")
        else:
            title = f"{name} contributes {pct(share, 0)} of revenue."
            text = (f"{v['rows']} units at {rupee(atv)} ATV for {lakh(v['net'])}. "
                    f"Gross {lakh(v['gross'])}, discount {lakh(v['disc'])}.")
        
        insights.append(insight_card(f"{i:02d}", title, text))
    
    return "\n".join(insights)


def build_seller_table(ctx, sellers, total_gross):
    rows = []
    for name, v in sellers:
        share = (v['gross'] / total_gross * 100) if total_gross else 0
        atv = v['gross'] / v['rows'] if v['rows'] else 0
        display_name = name if name != '-' else '&mdash; (online / self-service)'
        rows.append(f'''            <tr>
              <td>{display_name}</td>
              <td class="num">{lakh(v['gross'])}</td>
              <td class="num">{lakh(v['net'])}</td>
              <td class="num">{v['rows']}</td>
              <td class="num">{rupee(atv)}</td>
              <td class="num">{pct(share, 0)}</td>
            </tr>''')
    
    return f'''        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Seller</th>
                <th>Gross Rev</th>
                <th>Net Rev</th>
                <th>Units</th>
                <th>ATV</th>
                <th>Share</th>
              </tr>
            </thead>
            <tbody>
{chr(10).join(rows)}
            </tbody>
          </table>
        </div>'''


def build_seller_insights(ctx, sellers, total_gross):
    insights = []
    attributed = [(n,v) for n,v in sellers if n != '-']
    top2_share = sum(v['gross'] for _,v in attributed[:2]) / total_gross * 100 if total_gross else 0
    online = next((v for n,v in sellers if n == '-'), None)
    online_share = (online['gross'] / total_gross * 100) if online and total_gross else 0
    
    insights.append(insight_card("01",
        f"Top 2 sellers drove {pct(top2_share, 0)} of attributed revenue." if attributed else "Seller attribution is limited.",
        f"{' and '.join(n for n,_ in attributed[:2])} together drove <strong>{pct(top2_share, 0)} of attributed sales</strong>. " if attributed else "Most sales have no attributed seller. "
        f"The seller mix is {'healthy at the top' if len(attributed) >= 3 else 'concentrated'} with {len(attributed)} active sellers."))
    
    if online:
        insights.append(insight_card("02",
            f"Online / self-service transactions are {pct(online_share, 0)} of gross.",
            f"<strong>{lakh(online['gross'])}</strong> in {online['rows']} units came through with no attributed seller &mdash; "
            f"these are online or self-service transactions. "
            f"{'This is a healthy digital channel' if online_share > 10 else 'The digital channel is small but present'}."))
    
    for i, (name, v) in enumerate(attributed[:4], 3 if online else 2):
        share = (v['gross'] / total_gross * 100) if total_gross else 0
        insights.append(insight_card(f"{i:02d}",
            f"{name} contributed {pct(share, 0)} of gross revenue.",
            f"{v['rows']} units at {rupee(v['gross']/v['rows']) if v['rows'] else 0} ATV for {lakh(v['gross'])}. "
            f"Net revenue: {lakh(v['net'])}."))
    
    return "\n".join(insights)


def build_payment_table(ctx, payments, total_gross):
    rows = []
    for name, v in payments:
        share = (v['gross'] / total_gross * 100) if total_gross else 0
        display = name.replace('-', ' ').title() if name != '-' else 'Other'
        rows.append(f'''            <tr>
              <td>{display}</td>
              <td class="num">{lakh(v['gross'])}</td>
              <td class="num">{lakh(v['net'])}</td>
              <td class="num">{v['rows']}</td>
              <td class="num">{pct(share, 0)}</td>
            </tr>''')
    
    return f'''        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Payment Method</th>
                <th>Gross Rev</th>
                <th>Net Rev</th>
                <th>Units</th>
                <th>Share</th>
              </tr>
            </thead>
            <tbody>
{chr(10).join(rows)}
            </tbody>
          </table>
        </div>'''


def build_payment_insights(ctx, payments, total_gross):
    insights = []
    for i, (name, v) in enumerate(payments[:5], 1):
        share = (v['gross'] / total_gross * 100) if total_gross else 0
        display = name.replace('-', ' ').title() if name != '-' else 'Other'
        
        if i == 1:
            title = f"{display} is the primary payment method at {pct(share, 0)}."
            text = (f"<strong>{lakh(v['gross'])}</strong> ({pct(share, 0)} of gross) processed via {display.lower()}. "
                    f"{v['rows']} units at {rupee(v['gross']/v['rows']) if v['rows'] else 0} average ticket.")
        else:
            title = f"{display} accounts for {pct(share, 0)} of gross."
            text = (f"{lakh(v['gross'])} across {v['rows']} units. "
                    f"{'A secondary channel with meaningful volume.' if share > 15 else 'A smaller but present channel.'}")
        
        insights.append(insight_card(f"{i:02d}", title, text))
    
    return "\n".join(insights)


# ─── Section 03: New Client Conversion Funnel ─────────────────────────────────

def section_03(ctx):
    loc = ctx['loc']
    mo = ctx['mo']
    s = ctx['sales']
    leads = ctx['leads']
    new = ctx['new']
    
    loc_name = loc['short_name']
    month_name = mo['month_name']
    
    lead_count = leads['total']
    trial_count = new['trials']
    conv_count = leads['converted']
    retained_count = new['retained']
    conv_rate = leads['rate']
    
    # Get lead sources
    sources = get_leads_source(ctx['loc_key'], ctx['month_key'])
    sources_sorted = sorted(sources.items(), key=lambda x: -x[1]['total'])
    
    # Get trial types
    trial_types = get_new_type(ctx['loc_key'], ctx['month_key'])
    
    title = (f"{lead_count} leads &rarr; {trial_count} trials &rarr; {conv_count} conversions &rarr; {retained_count} retained. "
             f"The funnel converts at {pct(conv_rate)} &mdash; "
             f"{'the constraint is top-of-pipeline volume, not conversion mechanics.' if conv_rate > 15 else 'conversion mechanics need attention alongside pipeline volume.'}")
    
    deck = (f"The conversion story in {month_name} {ctx['mo']['year']}: {lead_count} leads generated, {trial_count} first visits / trials, "
            f"{conv_count} converted ({pct(conv_rate)} conversion rate), and {retained_count} retained "
            f"({pct(ctx['trial_retention'])} of trials). "
            f"Leads are {ctx['leads_mom']} MoM, conversions {ctx['converted_mom']} MoM. "
            f"{'The referral channel' if sources_sorted else 'The pipeline'} "
            f"{'is the highest-quality lead source' if sources_sorted else 'needs attention'}. "
            f"Below we walk the funnel source-by-source with all available metrics.")
    
    # Funnel stages
    stages = [
        (fmt_int(lead_count), "Leads", f"{ctx['leads_mom']} MoM", False),
        (fmt_int(trial_count), "First Visits / Trials", f"{ctx['trials_mom']} MoM", False),
        (fmt_int(conv_count), "Converted", f"{ctx['converted_mom']} MoM &middot; {pct(conv_rate)} conv rate", True),
        (fmt_int(retained_count), "Retained", f"{ctx['retained_mom']} MoM &middot; {pct(ctx['trial_retention'])} of trials", True),
    ]
    
    # Build funnel insights
    funnel_insights = build_funnel_insights(ctx, sources_sorted)
    
    # Build lead source table
    source_table = build_lead_source_table(ctx, sources_sorted, lead_count)
    
    # Build trial type breakdown
    trial_type_html = build_trial_type_section(ctx, trial_types, trial_count)
    
    html = f'''
<section class="report-section" id="conversion-funnel{ctx.get('id_suffix', '')}">
  <div class="container">
{section_header("03 &middot; New Client Conversion Funnel", title, deck, 3, loc_key=ctx["loc_key"], month_key=ctx["month_key"], id_suffix=ctx.get("id_suffix", ""))}

{subsection("Funnel at a glance &mdash; stage-by-stage view",
    "The four-stage visual below traces the headline funnel from leads through retention.")}

{funnel_stages(stages)}

{callout("<strong>How to read this section:</strong> the funnel table on the right is sorted by lead volume; conversion and retention rates are calculated off the leads column. The insight pane on the left narrates the KPIs &mdash; what each number <em>indicates</em> and <em>why</em> it matters for the business decision.")}

    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">Funnel-level insights</div>

{funnel_insights}
      </div>

      <div class="data-pane">
        <div class="pane-title" style="padding: 16px 16px 8px;">Leads by Source &middot; {month_name} {ctx['mo']['year']}</div>
{source_table}
      </div>
    </div>

{trial_type_html}
  </div>
</section>
'''
    return html


def build_funnel_insights(ctx, sources_sorted):
    insights = []
    leads = ctx['leads']
    new = ctx['new']
    
    # Top source by conversion
    if sources_sorted:
        # Highest conversion rate source (min 3 leads)
        conv_sources = [(n, v) for n, v in sources_sorted if v['total'] >= 3 and v['converted'] > 0]
        if conv_sources:
            best_conv = max(conv_sources, key=lambda x: x[1]['converted']/x[1]['total'])
            rate = best_conv[1]['converted'] / best_conv[1]['total'] * 100
            insights.append(insight_card("01",
                f"{best_conv[0]} is the highest-quality channel at {pct(rate)} conversion.",
                f"{best_conv[1]['total']} leads &rarr; {best_conv[1]['converted']} conversions ({pct(rate)}). "
                f"This is {mult(rate / leads['rate']) if leads['rate'] else 'n/a'} the portfolio average of {pct(leads['rate'])}."))
        
        # Top source by volume
        top_vol = sources_sorted[0]
        vol_conv_rate = top_vol[1]['converted']/top_vol[1]['total']*100 if top_vol[1]['total'] else 0
        vol_quality = 'high quality' if vol_conv_rate > 15 else 'but conversion needs work'
        insights.append(insight_card("02",
            f"{top_vol[0]} is the largest lead source at {top_vol[1]['total']} leads.",
            f"{top_vol[1]['total']} leads ({pct(top_vol[1]['total']/leads['total']*100)} of total) &rarr; "
            f"{top_vol[1]['converted']} conversions ({pct(vol_conv_rate)}). "
            f"High volume, {vol_quality}."))
        
        # Zero-conversion sources
        zero_conv = [(n, v) for n, v in sources_sorted if v['converted'] == 0 and v['total'] >= 3]
        if zero_conv:
            names = ', '.join(f"{n} ({v['total']} leads)" for n, v in zero_conv[:3])
            insights.append(insight_card("03",
                f"{len(zero_conv)} sources generated zero conversions.",
                f"{names} &mdash; these channels produced leads but none converted. "
                f"Either the lead quality is poor or the follow-up process is broken."))
    
    # Trial retention
    insights.append(insight_card("04",
        f"{new['retained']} of {new['trials']} trials retained ({pct(ctx['trial_retention'])}).",
        f"Retention rate of {pct(ctx['trial_retention'])} means {new['trials'] - new['retained']} trialists did not return. "
        f"{'Retention is healthy' if ctx['trial_retention'] > 25 else 'Retention needs improvement'}."))
    
    # Conversion vs baseline
    insights.append(insight_card("05",
        f"Conversion rate {ctx['conv_mom']} MoM, {ctx['conv_baseline']} vs baseline.",
        f"The {pct(leads['rate'])} conversion rate is {ctx['conv_mom']} vs {ctx['mo']['prev_month_name']} and "
        f"{ctx['conv_baseline']} vs the {ctx['baseline_label']} baseline of {pct(ctx['baseline']['leads']['rate'])}."))
    
    # Pipeline volume
    if ctx['leads_mom'].startswith('-'):
        pipeline_msg = "Even a strong conversion rate cannot offset volume loss if this continues."
    else:
        pipeline_msg = "This is a positive signal for next month's conversion potential."
    insights.append(insight_card("06",
        f"Lead pipeline at {leads['total']} &mdash; {ctx['leads_mom']} MoM.",
        f"{'Pipeline is thinning' if ctx['leads_mom'].startswith('-') else 'Pipeline is growing'} vs {ctx['mo']['prev_month_name']}. "
        f"{pipeline_msg}"))
    
    return "\n".join(insights)


def build_lead_source_table(ctx, sources_sorted, total_leads):
    rows = []
    for name, v in sources_sorted:
        rate = (v['converted'] / v['total'] * 100) if v['total'] else 0
        share = (v['total'] / total_leads * 100) if total_leads else 0
        rows.append(f'''            <tr>
              <td>{name}</td>
              <td class="num">{v['total']}</td>
              <td class="num">{v['converted']}</td>
              <td class="num">{pct(rate)}</td>
              <td class="num">{pct(share, 0)}</td>
            </tr>''')
    
    total_conv = sum(v['converted'] for _, v in sources_sorted)
    rows.append(f'''            <tr class="total-row">
              <td>Total</td>
              <td class="num">{total_leads}</td>
              <td class="num">{total_conv}</td>
              <td class="num">{pct(total_conv/total_leads*100) if total_leads else 'n/a'}</td>
              <td class="num">100%</td>
            </tr>''')
    
    return f'''        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Lead Source</th>
                <th>Leads</th>
                <th>Converted</th>
                <th>Conv Rate</th>
                <th>Share</th>
              </tr>
            </thead>
            <tbody>
{chr(10).join(rows)}
            </tbody>
          </table>
        </div>'''


def build_trial_type_section(ctx, trial_types, total_trials):
    if not trial_types:
        return ""
    
    types_sorted = sorted(trial_types.items(), key=lambda x: -x[1])
    
    rows = []
    for name, count in types_sorted:
        share = (count / total_trials * 100) if total_trials else 0
        clean_name = name.replace("New - ", "")
        rows.append(f'''            <tr>
              <td>{clean_name}</td>
              <td class="num">{count}</td>
              <td class="num">{pct(share, 0)}</td>
            </tr>''')
    
    insights = []
    for i, (name, count) in enumerate(types_sorted[:4], 1):
        share = (count / total_trials * 100) if total_trials else 0
        clean_name = name.replace("New - ", "")
        insights.append(insight_card(f"{i:02d}",
            f"{clean_name}: {count} trials ({pct(share, 0)}).",
            f"{'The dominant trial type' if i == 1 else 'A secondary trial channel'}. "
            f"{count} first visits through this channel."))
    
    return f'''
{subsection("Trial type breakdown &mdash; how first visits were acquired",
    "The trial type breakdown shows the acquisition channel for each first visit / trial.")}

    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">Trial type insights</div>

{chr(10).join(insights)}
      </div>

      <div class="data-pane">
        <div class="pane-title" style="padding: 16px 16px 8px;">Trials by Type &middot; {ctx['mo']['month_name']} {ctx['mo']['year']}</div>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Trial Type</th>
                <th>Count</th>
                <th>Share</th>
              </tr>
            </thead>
            <tbody>
{chr(10).join(rows)}
            </tbody>
          </table>
        </div>
      </div>
    </div>'''


# ─── Section 04: Sessions & Class Performance ─────────────────────────────────

def section_04(ctx):
    loc = ctx['loc']
    mo = ctx['mo']
    sess = ctx['sessions']
    
    loc_name = loc['short_name']
    month_name = mo['month_name']
    
    classes = get_sessions_by_class(ctx['loc_key'], ctx['month_key'])
    classes_sorted = sorted(classes.items(), key=lambda x: -x[1]['sessions'])
    
    trainers = get_sessions_by_trainer(ctx['loc_key'], ctx['month_key'])
    trainers_sorted = sorted(trainers.items(), key=lambda x: -x[1]['sessions'])
    
    formats = get_sessions_by_format(ctx['loc_key'], ctx['month_key'])
    formats_sorted = sorted(formats.items(), key=lambda x: -x[1]['sessions'])
    
    # Identify best and worst fill classes
    fill_data = []
    for name, v in classes.items():
        if v['capacity'] > 0 and v['sessions'] >= 3:
            fill_data.append((name, v['visits']/v['capacity']*100, v))
    fill_data.sort(key=lambda x: -x[1])
    
    best_fill = fill_data[0] if fill_data else None
    worst_fill = fill_data[-1] if fill_data else None
    
    # Format insights
    format_insights = build_format_insights(ctx, formats_sorted, sess)
    format_table = build_format_table(ctx, formats_sorted)
    
    # Class insights & table
    class_insights = build_class_insights(ctx, classes_sorted, fill_data)
    class_table = build_class_table(ctx, classes_sorted)
    
    # Trainer insights & table
    trainer_formats = get_sessions_by_trainer_format(ctx['loc_key'], ctx['month_key'])
    trainer_insights = build_trainer_insights(ctx, trainers_sorted, sess, trainer_formats)
    trainer_table = build_trainer_table(ctx, trainers_sorted)
    
    # Heatmap
    heatmap_html = build_heatmap_section(ctx)
    
    title_parts = []
    title_parts.append(f"{sess['sessions']} sessions, {fmt_int(sess['visits'])} visits, {pct(sess['fill'])} fill")
    if best_fill:
        title_parts.append(f"{best_fill[0]} is the supply-constrained hero at {pct(best_fill[1])} fill")
    if worst_fill:
        title_parts.append(f"{worst_fill[0]} at {pct(worst_fill[1])} is the structural underperformer")
    title = " &mdash; ".join(title_parts[:3]) + "."
    
    avg_visits_str = f"Average class size is {sess['avg_visits']:.1f} visits per session."
    best_fill_str = f"{best_fill[0]} fill rate at {pct(best_fill[1])} makes it the supply-constrained hero." if best_fill else ""
    worst_fill_str = f"{worst_fill[0]} at {pct(worst_fill[1])} fill is the structural underperformer." if worst_fill else ""
    
    deck = (f"The session portfolio delivered <strong>{lakh(sess['revenue'])} of session-attributed revenue</strong> "
            f"across {len(classes)} distinct class formats in {month_name}. "
            f"{avg_visits_str} "
            f"{best_fill_str} "
            f"{worst_fill_str}")
    
    html = f'''
<section class="report-section" id="sessions{ctx.get('id_suffix', '')}">
  <div class="container">
{section_header("04 &middot; Sessions &amp; Class Performance", title, deck, 4, loc_key=ctx["loc_key"], month_key=ctx["month_key"], id_suffix=ctx.get("id_suffix", ""))}

{subsection("Format-level view &mdash; Barre, PowerCycle, Strength Lab",
    f"At the format level, the breakdown shows sessions, visits, capacity, revenue, and fill rate for each of the 3 formats: Barre, PowerCycle, and Strength Lab.")}

    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">Format-level insights</div>

{format_insights}
      </div>

      <div class="data-pane">
        <div class="pane-title" style="padding: 16px 16px 8px;">Sessions by Format &middot; {month_name} {ctx['mo']['year']}</div>
{format_table}
      </div>
    </div>

{subsection("Class-level view &mdash; every class format with fill rate",
    "The class table below shows every distinct class format with sessions, visits, capacity, fill rate, and revenue. Classes with fewer than 3 sessions are included for completeness but should be evaluated with caution.")}

    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">Class-level insights</div>

{class_insights}
      </div>

      <div class="data-pane">
        <div class="pane-title" style="padding: 16px 16px 8px;">Sessions by Class &middot; {month_name} {ctx['mo']['year']}</div>
{class_table}
      </div>
    </div>

{subsection("Trainer performance &mdash; sessions, visits, revenue by trainer",
    "The trainer table shows sessions, visits, capacity, fill rate, and revenue attributed to each trainer.")}

    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">Trainer-level insights</div>

{trainer_insights}
      </div>

      <div class="data-pane">
        <div class="pane-title" style="padding: 16px 16px 8px;">Sessions by Trainer &middot; {month_name} {ctx['mo']['year']}</div>
{trainer_table}
      </div>
    </div>

{heatmap_html}
  </div>
</section>
'''
    return html


def build_format_insights(ctx, formats_sorted, sess):
    insights = []
    total_sessions = sum(v['sessions'] for _, v in formats_sorted)
    total_visits = sum(v['visits'] for _, v in formats_sorted)
    top_fill = None

    for i, (name, v) in enumerate(formats_sorted[:5], 1):
        sess_share = (v['sessions'] / total_sessions * 100) if total_sessions else 0
        visit_share = (v['visits'] / total_visits * 100) if total_visits else 0
        fill = (v['visits'] / v['capacity'] * 100) if v['capacity'] else 0
        bucket = ('supply-constrained' if fill > 70 else 'running at healthy fill' if fill > 50
                  else 'structurally under-utilised' if fill < 30 else 'at moderate fill')

        if i == 1:
            top_fill = fill
            title = f"{name} anchors the schedule at {pct(sess_share, 0)} of sessions and {pct(fill)} fill."
            text = (f"{v['sessions']} sessions ({pct(sess_share, 0)} of total) delivered {v['visits']} visits "
                    f"({pct(visit_share, 0)} of total) and {lakh(v['revenue'])} in revenue. "
                    f"{'With fill above 70%, added capacity here would likely sell out.' if fill > 70 else 'There is still headroom before this format is supply-constrained.'}")
        else:
            gap = fill - top_fill if top_fill is not None else 0
            gap_phrase = (f", {abs(gap):.0f}pp {'ahead of' if gap > 0 else 'behind'} {formats_sorted[0][0]}"
                          if top_fill is not None and abs(gap) >= 1 else "")
            title = f"{name} is {bucket} at {pct(fill)} fill{gap_phrase}."
            text = (f"{v['sessions']} sessions ({pct(sess_share, 0)} of total), {v['visits']} visits ({pct(visit_share, 0)} of total), "
                    f"{lakh(v['revenue'])} revenue. "
                    f"{'Consider trimming low-demand slots here in favour of ' + formats_sorted[0][0] + '.' if fill < 30 else 'Fill is healthy; no schedule change needed.' if fill > 50 else 'Watch this format for another month before reallocating slots.'}")

        insights.append(insight_card(f"{i:02d}", title, text))

    return "\n".join(insights)


def build_format_table(ctx, formats_sorted):
    rows = []
    total_sessions = sum(v['sessions'] for _, v in formats_sorted)
    total_visits = sum(v['visits'] for _, v in formats_sorted)
    total_capacity = sum(v['capacity'] for _, v in formats_sorted)
    total_revenue = sum(v['revenue'] for _, v in formats_sorted)
    
    for name, v in formats_sorted:
        fill = (v['visits'] / v['capacity'] * 100) if v['capacity'] else 0
        avg = v['visits'] / v['sessions'] if v['sessions'] else 0
        rows.append(f'''            <tr>
              <td>{name}</td>
              <td class="num">{v['sessions']}</td>
              <td class="num">{v['visits']}</td>
              <td class="num">{v['capacity']}</td>
              <td class="num">{pct(fill)}</td>
              <td class="num">{avg:.1f}</td>
              <td class="num">{lakh(v['revenue'])}</td>
            </tr>''')
    
    fill_total = (total_visits / total_capacity * 100) if total_capacity else 0
    rows.append(f'''            <tr class="total-row">
              <td>Total</td>
              <td class="num">{total_sessions}</td>
              <td class="num">{total_visits}</td>
              <td class="num">{total_capacity}</td>
              <td class="num">{pct(fill_total)}</td>
              <td class="num">{total_visits/total_sessions:.1f}</td>
              <td class="num">{lakh(total_revenue)}</td>
            </tr>''')
    
    return f'''        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Format</th>
                <th>Sessions</th>
                <th>Visits</th>
                <th>Capacity</th>
                <th>Fill %</th>
                <th>Avg Size</th>
                <th>Revenue</th>
              </tr>
            </thead>
            <tbody>
{chr(10).join(rows)}
            </tbody>
          </table>
        </div>'''


def build_class_insights(ctx, classes_sorted, fill_data):
    insights = []
    
    # Best fill
    if fill_data:
        best = fill_data[0]
        insights.append(insight_card("01",
            f"{best[0]} is the highest-fill class at {pct(best[1])}.",
            f"{best[2]['sessions']} sessions, {best[2]['visits']} visits against {best[2]['capacity']} capacity. "
            f"{'Supply-constrained &mdash; every additional session would likely fill.' if best[1] > 70 else 'Strong demand.'}"))
    
    # Worst fill (min 5 sessions)
    low_fill = [f for f in fill_data if f[1] < 30 and f[2]['sessions'] >= 5]
    if low_fill:
        worst = low_fill[-1]
        insights.append(insight_card("02",
            f"{worst[0]} at {pct(worst[1])} fill is the structural underperformer.",
            f"{worst[2]['sessions']} sessions, {worst[2]['visits']} visits against {worst[2]['capacity']} capacity. "
            f"{'Consider discontinuing or consolidating.' if worst[1] < 25 else 'Needs schedule optimisation.'}"))
    
    # Top by volume
    if classes_sorted:
        top = classes_sorted[0]
        fill = (top[1]['visits'] / top[1]['capacity'] * 100) if top[1]['capacity'] else 0
        insights.append(insight_card("03",
            f"{top[0]} is the highest-volume class with {top[1]['sessions']} sessions.",
            f"{top[1]['sessions']} sessions, {top[1]['visits']} visits at {pct(fill)} fill. "
            f"Revenue: {lakh(top[1]['revenue'])}."))
    
    # Revenue leader
    rev_sorted = sorted(classes_sorted, key=lambda x: -x[1]['revenue'])
    if rev_sorted:
        top_rev = rev_sorted[0]
        insights.append(insight_card("04",
            f"{top_rev[0]} is the revenue leader at {lakh(top_rev[1]['revenue'])}.",
            f"Revenue of {lakh(top_rev[1]['revenue'])} from {top_rev[1]['sessions']} sessions. "
            f"That is {rupee(top_rev[1]['revenue']/top_rev[1]['visits']) if top_rev[1]['visits'] else 'n/a'} per visit."))
    
    # Portfolio breadth
    insights.append(insight_card("05",
        f"{len(classes_sorted)} distinct class formats in the schedule.",
        f"The portfolio spans {len(classes_sorted)} class types. "
        f"{'A diverse schedule' if len(classes_sorted) > 20 else 'A focused schedule'}. "
        f"Total of {sum(v['sessions'] for _, v in classes_sorted)} sessions across all formats."))
    
    return "\n".join(insights)


def build_class_table(ctx, classes_sorted):
    rows = []
    for name, v in classes_sorted:
        fill = (v['visits'] / v['capacity'] * 100) if v['capacity'] else 0
        avg = v['visits'] / v['sessions'] if v['sessions'] else 0
        rows.append(f'''            <tr>
              <td>{name}</td>
              <td class="num">{v['sessions']}</td>
              <td class="num">{v['visits']}</td>
              <td class="num">{v['capacity']}</td>
              <td class="num">{pct(fill)}</td>
              <td class="num">{avg:.1f}</td>
              <td class="num">{lakh(v['revenue'])}</td>
            </tr>''')
    
    return f'''        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Class</th>
                <th>Sessions</th>
                <th>Visits</th>
                <th>Capacity</th>
                <th>Fill %</th>
                <th>Avg Size</th>
                <th>Revenue</th>
              </tr>
            </thead>
            <tbody>
{chr(10).join(rows)}
            </tbody>
          </table>
        </div>'''


def build_trainer_insights(ctx, trainers_sorted, sess, trainer_formats=None):
    trainer_formats = trainer_formats or {}
    insights = []
    total_sessions = sum(v['sessions'] for _, v in trainers_sorted)
    studio_fill = (sess['visits'] / sess['capacity'] * 100) if sess.get('capacity') else 0

    def trainer_fill(v):
        return (v['visits'] / v['capacity'] * 100) if v['capacity'] else 0

    def dominant_format(name):
        fmts = trainer_formats.get(name, {})
        if not fmts:
            return None, 0
        top_fmt, top_v = max(fmts.items(), key=lambda kv: kv[1]['sessions'])
        trainer_total = sum(f['sessions'] for f in fmts.values())
        share = (top_v['sessions'] / trainer_total * 100) if trainer_total else 0
        return top_fmt, share

    idx = 1
    for name, v in trainers_sorted[:5]:
        fill = trainer_fill(v)
        sess_share = (v['sessions'] / total_sessions * 100) if total_sessions else 0
        avg = v['visits'] / v['sessions'] if v['sessions'] else 0
        top_fmt, fmt_share = dominant_format(name)
        specialization = (f" {pct(fmt_share, 0)} of {name.split()[0]}'s sessions are {top_fmt}."
                           if top_fmt and fmt_share >= 60 else
                           f" Teaches across multiple formats ({', '.join(trainer_formats.get(name, {}).keys())})."
                           if top_fmt else "")

        if idx == 1:
            title = f"{name} is the top trainer by volume with {v['sessions']} sessions."
            text = (f"{v['sessions']} sessions ({pct(sess_share, 0)} of total), {v['visits']} visits at {pct(fill)} fill. "
                    f"Revenue: {lakh(v['revenue'])}. Average class size: {avg:.1f}.{specialization}")
        else:
            title = f"{name}: {v['sessions']} sessions at {pct(fill)} fill."
            text = (f"{pct(sess_share, 0)} of total sessions, {v['visits']} visits. "
                    f"Revenue: {lakh(v['revenue'])}. Average class size: {avg:.1f}.{specialization}")

        insights.append(insight_card(f"{idx:02d}", title, text))
        idx += 1

    # Pattern: trainers meaningfully outperforming or underperforming the studio fill rate
    qualified = [(name, v, trainer_fill(v)) for name, v in trainers_sorted if v['sessions'] >= 5]
    over = sorted([t for t in qualified if t[2] - studio_fill >= 10], key=lambda t: -t[2])
    under = sorted([t for t in qualified if studio_fill - t[2] >= 10], key=lambda t: t[2])

    if over:
        name, v, fill = over[0]
        insights.append(insight_card(f"{idx:02d}",
            f"{name} outperforms the studio fill rate by {fill - studio_fill:.1f}pp.",
            f"{name} runs at {pct(fill)} fill vs the studio average of {pct(studio_fill)} across {v['sessions']} sessions. "
            f"Recommendation: give {name} first claim on peak-demand slots and use their format mix as the template for underperforming trainers."))
        idx += 1

    if under:
        name, v, fill = under[0]
        top_fmt, fmt_share = dominant_format(name)
        fmt_note = f" concentrated in {top_fmt} ({pct(fmt_share, 0)} of their sessions)" if top_fmt and fmt_share >= 60 else ""
        insights.append(insight_card(f"{idx:02d}",
            f"{name} trails the studio fill rate by {studio_fill - fill:.1f}pp &mdash; a coaching or scheduling opportunity.",
            f"{name} runs at {pct(fill)} fill vs the studio average of {pct(studio_fill)} across {v['sessions']} sessions,{fmt_note}. "
            f"Recommendation: pair {name} with the top-performing trainer's format mix, or shift their slots to higher-demand time windows before cutting sessions."))
        idx += 1

    # Pattern: format specialists vs generalists, using dominant_format concentration
    specialists = [n for n, v in trainers_sorted if v['sessions'] >= 5 and dominant_format(n)[1] >= 90]
    if len(specialists) >= 2:
        insights.append(insight_card(f"{idx:02d}",
            f"{len(specialists)} trainers are single-format specialists.",
            f"{', '.join(specialists[:4])} each run 90%+ of their sessions in one format. "
            f"Recommendation: cross-train at least one specialist per format as a backup to reduce single-trainer dependency risk."))
        idx += 1

    return "\n".join(insights)


def build_trainer_table(ctx, trainers_sorted):
    rows = []
    for name, v in trainers_sorted:
        fill = (v['visits'] / v['capacity'] * 100) if v['capacity'] else 0
        avg = v['visits'] / v['sessions'] if v['sessions'] else 0
        rows.append(f'''            <tr>
              <td>{name}</td>
              <td class="num">{v['sessions']}</td>
              <td class="num">{v['visits']}</td>
              <td class="num">{v['capacity']}</td>
              <td class="num">{pct(fill)}</td>
              <td class="num">{avg:.1f}</td>
              <td class="num">{lakh(v['revenue'])}</td>
            </tr>''')
    
    return f'''        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Trainer</th>
                <th>Sessions</th>
                <th>Visits</th>
                <th>Capacity</th>
                <th>Fill %</th>
                <th>Avg Size</th>
                <th>Revenue</th>
              </tr>
            </thead>
            <tbody>
{chr(10).join(rows)}
            </tbody>
          </table>
        </div>'''


def build_heatmap_section(ctx):
    heatmap = get_heatmap(ctx['loc_key'], ctx['month_key'])
    if not heatmap:
        return ""

    # Build day x time heatmap
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    # Collect all time slots
    time_slots = set()
    day_time_data = {}  # (day, time) -> visits
    day_time_meta = {}  # (day, time) -> (top_format, top_trainer)

    for time_str, day_data in heatmap.items():
        for day_name, info in day_data.items():
            day_short = day_name[:3] if len(day_name) >= 3 else day_name
            if day_short in days:
                time_slots.add(time_str)
                if isinstance(info, dict):
                    day_time_data[(day_short, time_str)] = info.get('visits', 0)
                    formats = info.get('formats') or {}
                    trainers = info.get('trainers') or {}
                    top_format = max(formats.items(), key=lambda kv: kv[1])[0] if formats else None
                    top_trainer = max(trainers.items(), key=lambda kv: kv[1])[0] if trainers else None
                    day_time_meta[(day_short, time_str)] = (top_format, top_trainer)
                else:
                    day_time_data[(day_short, time_str)] = info

    if not time_slots:
        return ""
    
    # Sort time slots chronologically
    def sort_time(t):
        try:
            h, m = t.split(':')
            return int(h) * 60 + int(m)
        except:
            return 9999
    
    sorted_times = sorted(time_slots, key=sort_time)
    
    # Find max visits for color scaling
    max_visits = max(day_time_data.values()) if day_time_data else 1
    
    # Build heatmap HTML
    insights = []
    
    # Find peak slots
    peak_slots = sorted(day_time_data.items(), key=lambda x: -x[1])[:5]
    if peak_slots:
        insights.append(insight_card("01",
            f"Peak demand at {peak_slots[0][0][1]} {peak_slots[0][0][0]} with {peak_slots[0][1]} visits.",
            f"The highest-traffic slot is {peak_slots[0][0][1]} on {peak_slots[0][0][0]} with {peak_slots[0][1]} visits. "
            f"Top 5 slots: {', '.join(f'{t} {d} ({v})' for (d,t), v in peak_slots)}."))
    
    # Find weak slots
    weak_slots = sorted([(k,v) for k,v in day_time_data.items() if v <= 2], key=lambda x: x[1])[:5]
    if weak_slots:
        insights.append(insight_card("02",
            f"{len(weak_slots)} slots have 2 or fewer visits &mdash; candidates for schedule trimming.",
            f"Weakest slots: {', '.join(f'{t} {d} ({v})' for (d,t), v in weak_slots[:3])}. "
            f"Consider reallocating these to high-demand time windows."))
    
    # Build table
    header_cells = "".join(f"<th>{t}</th>" for t in sorted_times)
    
    body_rows = []
    for day in days:
        cells = f"<td class='row-label'>{day}</td>"
        for t in sorted_times:
            v = day_time_data.get((day, t), 0)
            if v == 0:
                cells += "<td class='heat-cell empty'>&mdash;</td>"
            else:
                intensity = v / max_visits if max_visits else 0
                cls = 'heat-cell'
                if intensity > 0.75:
                    cls += ' hot'
                elif intensity > 0.5:
                    cls += ' warm'
                elif intensity > 0.25:
                    cls += ' cool'
                else:
                    cls += ' cold'
                top_format, top_trainer = day_time_meta.get((day, t), (None, None))
                sub_bits = [b for b in [top_format, top_trainer] if b]
                sub_html = f"<span class='heat-sub'>{' &middot; '.join(sub_bits)}</span>" if sub_bits else ""
                cells += f"<td class='{cls}'>{v}{sub_html}</td>"
        body_rows.append(f"            <tr>{cells}</tr>")

    return f'''
{subsection("Session heatmap &mdash; day &times; time slot demand intensity",
    "The heatmap below shows visit volume by day of week and time slot, with the leading format and trainer for each slot. Hot cells indicate peak demand; cold cells indicate under-utilised slots. Use this to optimise the weekly schedule.")}

    <div class="insights-pane full-width-block">
      <div class="pane-title">Heatmap insights</div>

{chr(10).join(insights)}
    </div>

    <div class="data-pane full-width-block">
      <div class="pane-title" style="padding: 16px 16px 8px;">Visit Heatmap &middot; {ctx['mo']['month_name']} {ctx['mo']['year']}</div>
      <div class="table-wrap">
        <table class="data-table heatmap-table">
          <thead>
            <tr>
              <th>Day</th>
              {header_cells}
            </tr>
          </thead>
          <tbody>
{chr(10).join(body_rows)}
          </tbody>
        </table>
      </div>
    </div>'''


# ─── Section 05: Lapsed Memberships Deep Dive ────────────────────────────────

def section_05(ctx):
    loc = ctx['loc']
    mo = ctx['mo']
    lapsed = ctx['lapsed']
    
    loc_name = loc['short_name']
    month_name = mo['month_name']
    
    lapsed_prod = get_lapsed_product(ctx['loc_key'], ctx['month_key'])
    cumulative = get_lapsed_cumulative(ctx['loc_key'])
    
    # Sort products by total
    prod_sorted = sorted(lapsed_prod.items(), key=lambda x: -x[1]['total'])
    
    # Status insights
    status_insights = build_lapsed_status_insights(ctx)
    status_table = build_lapsed_status_table(ctx)
    
    # Product insights & table
    prod_insights = build_lapsed_product_insights(ctx, prod_sorted, lapsed)
    prod_table = build_lapsed_product_table(ctx, prod_sorted)
    
    # Cumulative trend
    cumul_html = build_cumulative_section(ctx, cumulative)
    
    # Find top lapsed product
    top_lapsed_prod = max(prod_sorted, key=lambda x: x[1]['lapsed']) if prod_sorted else None
    
    title = (f"{lapsed['total']} memberships reached end-of-life, {pct(lapsed['renewal_rate'])} renewed, "
             f"{pct(lapsed['churn'])} churned. "
             f"{'The lapsed book is concentrated in ' + top_lapsed_prod[0] + ' holders' if top_lapsed_prod else 'The lapsed book is diversified'} "
             f"&mdash; the highest-leverage reactivation target.")
    
    deck = (f"{month_name}&rsquo;s expiration book had <strong>{lapsed['total']} memberships reach end-of-life</strong>: "
            f"<strong>{lapsed['renewed']} renewed ({pct(lapsed['renewal_rate'])})</strong>, "
            f"<strong>{lapsed['lapsed']} lapsed ({pct(lapsed['churn'])})</strong>, "
            f"<strong>{lapsed['frozen']} frozen</strong>. "
            f"Churn rate is {ctx['churn_mom']} MoM and {ctx['churn_baseline']} vs the {ctx['baseline_label']} baseline. "
            f"{'Renewal rate is improving' if ctx['renewal_mom'].startswith('+') else 'Renewal rate needs attention'}. "
            f"The cumulative lapsed book now stands at {fmt_int(ctx['cumulative_lapsed'])} unique lapsed members.")
    
    html = f'''
<section class="report-section" id="lapsed{ctx.get('id_suffix', '')}">
  <div class="container">
{section_header("05 &middot; Lapsed Memberships &mdash; Deep Dive", title, deck, 5, loc_key=ctx["loc_key"], month_key=ctx["month_key"], id_suffix=ctx.get("id_suffix", ""))}

{callout("<strong>Exclusions applied in this section (per management guidance):</strong> zero-value memberships, "
    "&lsquo;Newcomers 2 For 1&rsquo; SKUs, &lsquo;Studio Single Class&rsquo; SKUs, and all Private-class memberships. "
    "Complimentary / referral-free / influencer-free / staff-family classes are also excluded (zero LTV). "
    "The cleaned table below covers only revenue-bearing memberships where the lapse represents real lost revenue.")}

{subsection("Expiration status &mdash; the headline split",
    f"Of {lapsed['total']} memberships that reached end-of-life, {pct(lapsed['renewal_rate'])} renewed, {pct(lapsed['churn'])} lapsed. The renewal rate is {'healthy' if lapsed['renewal_rate'] > 50 else 'below benchmark'}; the lapse count of {lapsed['lapsed']} is the actionable book.")}

    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">Status-level insights</div>

{status_insights}
      </div>

      <div class="data-pane">
        <div class="pane-title" style="padding: 16px 16px 8px;">Expiration Status &middot; {month_name} {ctx['mo']['year']}</div>
{status_table}
      </div>
    </div>

{subsection("Lapse by product &mdash; where the churn is concentrated",
    "The product table below shows every membership SKU that reached end-of-life, split by renewal, lapse, and frozen status. The highest-lapse products are the priority reactivation targets.")}

    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">Product-level insights</div>

{prod_insights}
      </div>

      <div class="data-pane">
        <div class="pane-title" style="padding: 16px 16px 8px;">Lapse by Product &middot; {month_name} {ctx['mo']['year']}</div>
{prod_table}
      </div>
    </div>

{cumul_html}
  </div>
</section>
'''
    return html


def build_lapsed_status_insights(ctx):
    lapsed = ctx['lapsed']
    baseline = ctx['baseline']
    insights = []
    
    insights.append(insight_card("01",
        f"Renewal rate at {pct(lapsed['renewal_rate'])} is {'the studio&rsquo;s strongest retention signal' if lapsed['renewal_rate'] > 50 else 'below the healthy band'}.",
        f"{lapsed['renewed']} of {lapsed['total']} expirations renewed. Industry benchmark for boutique fitness is 50&ndash;60% &mdash; "
        f"{ctx['loc']['short_name']} is {'in the healthy band' if lapsed['renewal_rate'] > 50 else 'below benchmark'}. "
        f"The rate is {ctx['renewal_mom']} MoM and {ctx['renewal_baseline']} vs baseline."))
    
    insights.append(insight_card("02",
        f"{lapsed['lapsed']} lapses in {ctx['mo']['month_name']} is the actionable reactivation book.",
        f"Each lapsed member has a known LTV. Reactivating even 15% ({int(lapsed['lapsed']*0.15)} members) "
        f"at 50% of their previous LTV would recover approximately &#8377;{lapsed['lapsed']*0.15*20000/1e5:.1f}L of revenue over 3 months."))
    
    insights.append(insight_card("03",
        f"Only {lapsed['frozen']} frozen memberships &mdash; {'low' if lapsed['frozen'] < 10 else 'moderate'} recoverable inventory.",
        f"Frozen memberships typically thaw into either renewal or lapse. "
        f"With {lapsed['frozen']} in the frozen state, the near-term recovery opportunity from this segment is "
        f"{'small' if lapsed['frozen'] < 10 else 'meaningful'}."))
    
    insights.append(insight_card("04",
        f"Churn rate at {pct(lapsed['churn'])} &mdash; {ctx['churn_mom']} MoM.",
        f"The churn rate is {ctx['churn_mom']} vs {ctx['mo']['prev_month_name']} and {ctx['churn_baseline']} vs the {ctx['baseline_label']} baseline of {pct(baseline['lapsed']['churn'])}. "
        f"{'Retention work is gaining traction.' if lapsed['churn'] < baseline['lapsed']['churn'] else 'Churn is above baseline &mdash; retention needs reinforcement.'}"))
    
    return "\n".join(insights)


def build_lapsed_status_table(ctx):
    lapsed = ctx['lapsed']
    total = lapsed['total']
    
    statuses = [
        ("Renewed", lapsed['renewed'], 'good'),
        ("Lapsed", lapsed['lapsed'], 'bad'),
        ("Frozen", lapsed['frozen'], 'neutral'),
    ]
    
    rows = []
    for name, count, tone in statuses:
        share = (count / total * 100) if total else 0
        rows.append(f'''            <tr>
              <td>{name}</td>
              <td class="num">{count}</td>
              <td class="num">{pct(share)}</td>
            </tr>''')
    rows.append(f'''            <tr class="total-row">
              <td>Total</td>
              <td class="num">{total}</td>
              <td class="num">100%</td>
            </tr>''')
    
    return f'''        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Status</th>
                <th>Count</th>
                <th>Share</th>
              </tr>
            </thead>
            <tbody>
{chr(10).join(rows)}
            </tbody>
          </table>
        </div>'''


def build_lapsed_product_insights(ctx, prod_sorted, lapsed):
    insights = []
    
    # Top lapsed product
    lapsed_prods = [(n, v) for n, v in prod_sorted if v['lapsed'] > 0]
    lapsed_prods.sort(key=lambda x: -x[1]['lapsed'])
    
    if lapsed_prods:
        top = lapsed_prods[0]
        insights.append(insight_card("01",
            f"{top[0]} is the highest-lapse product with {top[1]['lapsed']} lapses.",
            f"{top[1]['total']} total expirations, {top[1]['renewed']} renewed, {top[1]['lapsed']} lapsed "
            f"({pct(top[1]['lapsed']/top[1]['total']*100) if top[1]['total'] else 'n/a'} churn rate for this SKU). "
            f"This is the highest-leverage reactivation target."))
    
    # Best renewal product
    if prod_sorted:
        renewal_prods = [(n, v) for n, v in prod_sorted if v['total'] >= 5]
        renewal_prods.sort(key=lambda x: -x[1]['renewed']/x[1]['total'] if x[1]['total'] else 0)
        if renewal_prods:
            best = renewal_prods[0]
            rate = best[1]['renewed'] / best[1]['total'] * 100 if best[1]['total'] else 0
            insights.append(insight_card("02",
                f"{best[0]} has the highest renewal rate at {pct(rate)}.",
                f"{best[1]['renewed']} of {best[1]['total']} renewed ({pct(rate)}). "
                f"This product has strong stickiness and loyalty."))
    
    # Top by volume
    if prod_sorted:
        top_vol = prod_sorted[0]
        insights.append(insight_card("03",
            f"{top_vol[0]} has the highest expiration volume at {top_vol[1]['total']}.",
            f"{top_vol[1]['total']} memberships reached end-of-life: {top_vol[1]['renewed']} renewed, "
            f"{top_vol[1]['lapsed']} lapsed, {top_vol[1]['frozen']} frozen."))
    
    # Overall
    insights.append(insight_card("04",
        f"{len(prod_sorted)} distinct products in the expiration book.",
        f"The lapsed book spans {len(prod_sorted)} membership SKUs. "
        f"Total: {lapsed['total']} expirations, {lapsed['renewed']} renewed, {lapsed['lapsed']} lapsed."))
    
    return "\n".join(insights)


def build_lapsed_product_table(ctx, prod_sorted):
    rows = []
    total_total = sum(v['total'] for _, v in prod_sorted)
    total_renewed = sum(v['renewed'] for _, v in prod_sorted)
    total_lapsed = sum(v['lapsed'] for _, v in prod_sorted)
    total_frozen = sum(v['frozen'] for _, v in prod_sorted)
    
    for name, v in prod_sorted:
        churn = (v['lapsed'] / v['total'] * 100) if v['total'] else 0
        rows.append(f'''            <tr>
              <td>{name}</td>
              <td class="num">{v['total']}</td>
              <td class="num">{v['renewed']}</td>
              <td class="num">{v['lapsed']}</td>
              <td class="num">{v['frozen']}</td>
              <td class="num">{pct(churn)}</td>
            </tr>''')
    
    rows.append(f'''            <tr class="total-row">
              <td>Total</td>
              <td class="num">{total_total}</td>
              <td class="num">{total_renewed}</td>
              <td class="num">{total_lapsed}</td>
              <td class="num">{total_frozen}</td>
              <td class="num">{pct(total_lapsed/total_total*100) if total_total else 'n/a'}</td>
            </tr>''')
    
    return f'''        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Total</th>
                <th>Renewed</th>
                <th>Lapsed</th>
                <th>Frozen</th>
                <th>Churn %</th>
              </tr>
            </thead>
            <tbody>
{chr(10).join(rows)}
            </tbody>
          </table>
        </div>'''


def build_cumulative_section(ctx, cumulative):
    if not cumulative:
        return ""
    
    months_order = sorted(cumulative.keys())

    rows = []
    for m in months_order:
        month_name = datetime_month_name(m)
        rows.append(f'''            <tr>
              <td>{month_name}</td>
              <td class="num">{fmt_int(cumulative[m])}</td>
            </tr>''')
    
    insights = []
    insights.append(insight_card("01",
        f"Cumulative lapsed book now at {fmt_int(ctx['cumulative_lapsed'])} unique members.",
        f"The cumulative count of unique lapsed members has grown to {fmt_int(ctx['cumulative_lapsed'])} as of {ctx['mo']['month_name']} {ctx['mo']['year']}. "
        f"This is the total reactivation pool available for win-back campaigns."))
    
    # Growth rate
    prev_cumul = cumulative.get(ctx['mo']['prev_month'], 0)
    if prev_cumul:
        growth = pct_change(prev_cumul, ctx['cumulative_lapsed'])
        insights.append(insight_card("02",
            f"Cumulative lapsed grew {growth} MoM.",
            f"The lapsed book added {ctx['cumulative_lapsed'] - prev_cumul} new unique lapsed members in {ctx['mo']['month_name']}. "
            f"{'The pool is expanding faster than reactivation efforts.' if ctx['cumulative_lapsed'] - prev_cumul > 100 else 'Reactivation is keeping pace with new lapses.'}"))
    
    return f'''
{subsection("Cumulative lapsed trend &mdash; the growing reactivation pool",
    "The cumulative lapsed member count grows each month as new lapses are added. This is the total pool available for win-back campaigns and reactivation outreach.")}

    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">Cumulative insights</div>

{chr(10).join(insights)}
      </div>

      <div class="data-pane">
        <div class="pane-title" style="padding: 16px 16px 8px;">Cumulative Lapsed Members Trend</div>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Month</th>
                <th>Cumulative Lapsed</th>
              </tr>
            </thead>
            <tbody>
{chr(10).join(rows)}
            </tbody>
          </table>
        </div>
      </div>
    </div>'''


def month_offset_label(month_key, n):
    """'YYYY-MM' shifted forward n months -> 'Month YYYY'."""
    year, mon = (int(x) for x in month_key.split('-'))
    total = (year * 12 + (mon - 1)) + n
    year, mon = total // 12, total % 12 + 1
    return f'{calendar.month_name[mon]} {year}'


def datetime_month_name(m):
    """'YYYY-MM' -> 'Month YYYY', e.g. '2026-07' -> 'July 2026'."""
    try:
        year, mon = m.split('-')
        return f'{calendar.month_name[int(mon)]} {year}'
    except (ValueError, IndexError):
        return m


# ─── Section 06: Strategic Recommendations ───────────────────────────────────

def section_06(ctx):
    loc = ctx['loc']
    mo = ctx['mo']
    s = ctx['sales']
    sess = ctx['sessions']
    leads = ctx['leads']
    lapsed = ctx['lapsed']
    checkins = ctx['checkins']
    
    loc_name = loc['short_name']
    month_name = mo['month_name']
    
    # Build recommendations based on data
    sched_insights, sched_table = build_scheduling_recommendations(ctx)
    discount_insights = build_discount_recommendations(ctx)
    funnel_recs = build_funnel_recommendations(ctx)
    retention_recs = build_retention_recommendations(ctx)
    ops_recs = build_ops_recommendations(ctx)
    
    title = (f"Five business decisions for senior management to make this quarter &mdash; "
             f"each anchored to a {month_name} {ctx['mo']['year']} data point with a target and an owner.")
    
    deck = (f"The recommendations below consolidate the action items from sections 1&ndash;5 into a single decision-ready view. "
            f"Each recommendation has a quantified opportunity (in &#8377; or members), a target metric, "
            f"a 60- or 90-day timeline, and a single accountable owner. "
            f"These are the five decisions that, taken together, would move the studio from "
            f"{'baseline-plus to baseline-strong' if s['net'] > ctx['baseline']['sales']['net'] else 'baseline to baseline-plus'} "
            f"by {mo['next_month_name']} {ctx['mo']['next_year']}.")
    
    html = f'''
<section class="report-section" id="recommendations{ctx.get('id_suffix', '')}">
  <div class="container">
{section_header("06 &middot; Strategic Recommendations", title, deck, 6, loc_key=ctx["loc_key"], month_key=ctx["month_key"], id_suffix=ctx.get("id_suffix", ""))}

{subsection("Class scheduling &mdash; additions, discontinuations, format-specific moves",
    "The scheduling decisions below are anchored to the Session Intelligence table. Every addition is justified by excess demand (fill &gt; 60%); every discontinuation by structural under-fill (fill &lt; 25%) over a sustained period.")}

    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">Scheduling recommendations</div>

{sched_insights}
      </div>

      <div class="data-pane">
        <div class="pane-title" style="padding: 16px 16px 8px;">Schedule Action Items &middot; {month_name} {ctx['mo']['year']}</div>
{sched_table}
      </div>
    </div>

{subsection("Discount discipline &mdash; capping the margin leak",
    "Discount efficiency and penetration are the most controllable inputs. The recommendations below target a hard cap and SKU-level review.")}

    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">Discount recommendations</div>

{discount_insights}
      </div>
      <div class="data-pane">
        <div class="pane-title" style="padding: 16px 16px 8px;">Discount Action Items &middot; {month_name} {ctx['mo']['year']}</div>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr><th>Action</th><th>Target</th><th>Timeline</th><th>Owner</th></tr>
            </thead>
            <tbody>
              <tr><td>Cap monthly discount at {lakh(s['disc']*1.2)} (current {lakh(s['disc'])})</td><td>Disc penetration &le; 8%</td><td>Immediate</td><td>Studio Manager</td></tr>
              <tr><td>Review high-discount SKUs</td><td>Disc ratio &le; 15% per SKU</td><td>30 days</td><td>Sales Lead</td></tr>
              <tr><td>Approve all discounts &gt; &#8377;5,000</td><td>100% approval coverage</td><td>Immediate</td><td>Studio Manager</td></tr>
              <tr><td>Monthly discount report to management</td><td>Auto-generated</td><td>Monthly</td><td>Operations</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

{subsection("Funnel repair &mdash; pipeline volume and conversion quality",
    "The funnel recommendations target both lead volume (top of funnel) and conversion quality (mid-funnel). Lead pipeline replenishment is the most time-sensitive workstream.")}

    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">Funnel recommendations</div>

{funnel_recs}
      </div>
      <div class="data-pane">
        <div class="pane-title" style="padding: 16px 16px 8px;">Funnel Action Items &middot; {month_name} {ctx['mo']['year']}</div>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr><th>Action</th><th>Target</th><th>Timeline</th><th>Owner</th></tr>
            </thead>
            <tbody>
              <tr><td>Increase lead volume to {int(leads['total']*1.2)}+/month</td><td>+20% pipeline</td><td>60 days</td><td>Marketing</td></tr>
              <tr><td>Double down on referral channel</td><td>Referral = 25% of leads</td><td>90 days</td><td>Community Manager</td></tr>
              <tr><td>Follow-up protocol for all trials within 48h</td><td>100% coverage</td><td>Immediate</td><td>Front Desk</td></tr>
              <tr><td>Targeted win-back for zero-conversion sources</td><td>5% min conv per source</td><td>60 days</td><td>Sales Lead</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

{subsection("Retention &mdash; the lapsed-member reactivation engine",
    "The retention recommendations target the reactivation of lapsed members and the prevention of future lapses through proactive CRM.")}

    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">Retention recommendations</div>

{retention_recs}
      </div>
      <div class="data-pane">
        <div class="pane-title" style="padding: 16px 16px 8px;">Retention Action Items &middot; {month_name} {ctx['mo']['year']}</div>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr><th>Action</th><th>Target</th><th>Timeline</th><th>Owner</th></tr>
            </thead>
            <tbody>
              <tr><td>Reactivation campaign for {fmt_int(ctx['cumulative_lapsed'])} lapsed members</td><td>15% reactivation</td><td>90 days</td><td>Community Manager</td></tr>
              <tr><td>30/60/90-day pre-expiry outreach</td><td>100% coverage</td><td>30 days</td><td>CRM / Front Desk</td></tr>
              <tr><td>Priority reactivation for top-lapse SKUs</td><td>20% reactivation of top SKU</td><td>60 days</td><td>Sales Lead</td></tr>
              <tr><td>Monthly retention dashboard</td><td>Auto-generated</td><td>Monthly</td><td>Operations</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

{subsection("Operations &mdash; late-cancel policy and check-in discipline",
    "The operations recommendations target the late-cancel leak &mdash; a near-zero-risk policy intervention that recovers revenue and improves scheduling discipline.")}

    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">Operations recommendations</div>

{ops_recs}
      </div>
      <div class="data-pane">
        <div class="pane-title" style="padding: 16px 16px 8px;">Operations Action Items &middot; {month_name} {ctx['mo']['year']}</div>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr><th>Action</th><th>Target</th><th>Timeline</th><th>Owner</th></tr>
            </thead>
            <tbody>
              <tr><td>Implement late-cancel penalty (&#8377;500 or 1 class deduction)</td><td>{checkins['late_cancel']} &rarr; &le; 50% reduction</td><td>Immediate</td><td>Studio Manager</td></tr>
              <tr><td>Flag heavy cancelers ({checkins['heavy_cancelers']} members with 5+ cancels)</td><td>Personal outreach</td><td>30 days</td><td>Front Desk</td></tr>
              <tr><td>Auto-reminder 2h before class</td><td>Reduce no-shows</td><td>60 days</td><td>Operations</td></tr>
              <tr><td>Weekly late-cancel report</td><td>Track trend</td><td>Weekly</td><td>Operations</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</section>
'''
    return html


def build_scheduling_recommendations(ctx):
    classes = get_sessions_by_class(ctx['loc_key'], ctx['month_key'])
    
    # Find high-fill classes (add sessions)
    high_fill = []
    low_fill = []
    for name, v in classes.items():
        if v['capacity'] > 0 and v['sessions'] >= 3:
            fill = v['visits'] / v['capacity'] * 100
            if fill > 65:
                high_fill.append((name, fill, v))
            elif fill < 25:
                low_fill.append((name, fill, v))
    
    high_fill.sort(key=lambda x: -x[1])
    low_fill.sort(key=lambda x: x[1])
    
    insights = []
    
    for i, (name, fill, v) in enumerate(high_fill[:4], 1):
        insights.append(insight_card(f"{i:02d}",
            f"Add {name} sessions &mdash; at {pct(fill)} fill, demand exceeds supply.",
            f"{v['sessions']} sessions, {v['visits']} visits against {v['capacity']} capacity. "
            f"Every additional session would likely fill. Estimated incremental revenue: "
            f"&#8377;{int(v['revenue']/v['sessions']*0.8):,.0f}/session."))
    
    for i, (name, fill, v) in enumerate(low_fill[:3], len(high_fill[:4])+1):
        insights.append(insight_card(f"{i:02d}",
            f"Discontinue or consolidate {name} at {pct(fill)} fill.",
            f"{v['sessions']} sessions, {v['visits']} visits against {v['capacity']} capacity. "
            f"The format is under-utilised. Reallocate slots to high-fill formats."))
    
    if not high_fill and not low_fill:
        insights.append(insight_card("01",
            "Schedule is balanced &mdash; no extreme fill or under-fill classes.",
            "No classes exceed 65% fill or fall below 25% fill with sufficient volume. "
            "The schedule is reasonably balanced. Monitor for drift."))
    
    # Build action table
    rows = []
    for name, fill, v in high_fill[:4]:
        rows.append(f"<tr><td>Add {name} sessions</td><td>Fill &gt; 65% ({pct(fill)})</td><td>30 days</td><td>Scheduling Lead</td></tr>")
    for name, fill, v in low_fill[:3]:
        rows.append(f"<tr><td>Discontinue/consolidate {name}</td><td>Fill &lt; 25% ({pct(fill)})</td><td>30 days</td><td>Scheduling Lead</td></tr>")
    rows.append(f"<tr><td>Rebalance 5-10 slots from low-fill to high-fill</td><td>Overall fill +2-3pp</td><td>60 days</td><td>Studio Manager</td></tr>")
    rows.append(f"<tr><td>Review weekly heatmap for slot optimisation</td><td>Eliminate &le;2 visit slots</td><td>Monthly</td><td>Operations</td></tr>")
    
    table = f'''        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr><th>Action</th><th>Target</th><th>Timeline</th><th>Owner</th></tr>
            </thead>
            <tbody>
{chr(10).join(f"              {r}" for r in rows)}
            </tbody>
          </table>
        </div>'''
    
    return "\n".join(insights), table


def build_discount_recommendations(ctx):
    s = ctx['sales']
    baseline = ctx['baseline']
    
    insights = []
    
    insights.append(insight_card("01",
        f"Discount penetration at {pct(ctx['disc_penetration'])} &mdash; {'above' if ctx['disc_penetration'] > 10 else 'within'} acceptable range.",
        f"Total discount of {lakh(s['disc'])} on {lakh(s['gross'])} gross. "
        f"{'This is above the 10% threshold and warrants a hard cap.' if ctx['disc_penetration'] > 10 else 'This is within the healthy range but should be monitored.'} "
        f"Baseline penetration: {pct(baseline['sales']['disc']/baseline['sales']['gross']*100)}."))
    
    bd = get_sales_breakdowns(ctx['loc_key'], ctx['month_key'])
    cat_bd = bd.get('category', {})
    high_disc_cats = [(n, v) for n, v in cat_bd.items() if v['gross'] > 0 and v['disc']/v['gross'] > 0.15]
    high_disc_cats.sort(key=lambda x: -x[1]['disc']/x[1]['gross'])
    
    if high_disc_cats:
        insights.append(insight_card("02",
            f"{len(high_disc_cats)} categories have discount ratios above 15%.",
            f"{' and '.join(n for n, _ in high_disc_cats[:2])} have the highest discount ratios. "
            f"Review pricing and discount authorisation for these categories."))
    else:
        insights.append(insight_card("02",
            "All categories are within 15% discount ratio.",
            "No category exceeds the 15% discount threshold. Discount discipline is holding."))
    
    bl_disc_eff = baseline['sales']['disc_eff']
    if s['disc_eff'] < bl_disc_eff:
        eff_msg = f"Efficiency has eroded vs the baseline of &#8377;{bl_disc_eff:.2f}."
        action_msg = "A hard cap on monthly discount spend would protect this ratio."
    else:
        eff_msg = f"Efficiency is above the baseline of &#8377;{bl_disc_eff:.2f}."
        action_msg = "Maintain current discipline."
    
    insights.append(insight_card("03",
        f"Discount efficiency at &#8377;{s['disc_eff']:.2f} per &#8377;1 discounted.",
        f"{eff_msg} {action_msg}"))
    
    return "\n".join(insights)


def build_funnel_recommendations(ctx):
    leads = ctx['leads']
    new = ctx['new']
    sources = get_leads_source(ctx['loc_key'], ctx['month_key'])
    baseline = ctx['baseline']
    
    insights = []
    
    insights.append(insight_card("01",
        f"Lead pipeline at {leads['total']} &mdash; {ctx['leads_mom']} MoM, {pct_change(baseline['leads']['total'], leads['total'])} vs baseline.",
        f"{'Pipeline is thinning and needs replenishment.' if leads['total'] < baseline['leads']['total'] else 'Pipeline is healthy vs baseline.'} "
        f"Target: {int(baseline['leads']['total']*1.2)} leads/month to sustain conversion volume."))
    
    if sources:
        # Referral channel
        referral = next(((n, v) for n, v in sources.items() if 'referral' in n.lower()), None)
        if referral:
            rate = referral[1]['converted'] / referral[1]['total'] * 100 if referral[1]['total'] else 0
            insights.append(insight_card("02",
                f"Client Referral: {referral[1]['total']} leads at {pct(rate)} conversion &mdash; highest-quality channel.",
                f"Referral leads convert at {mult(rate/leads['rate']) if leads['rate'] else 'n/a'} the portfolio average. "
                f"Double down on referral incentives: member-get-member programme, referral credits, social proof."))
        
        # Zero-conversion sources
        zero = [(n, v) for n, v in sources.items() if v['total'] >= 3 and v['converted'] == 0]
        if zero:
            insights.append(insight_card("03",
                f"{len(zero)} lead sources produced zero conversions.",
                f"{' and '.join(n for n, _ in zero[:2])} generated {sum(v['total'] for _, v in zero)} leads with 0 conversions. "
                f"Either improve lead quality or redirect spend to higher-converting channels."))
    
    insights.append(insight_card("04",
        f"Trial retention at {pct(ctx['trial_retention'])} &mdash; {new['retained']} of {new['trials']} trials retained.",
        f"{'Retention is healthy' if ctx['trial_retention'] > 30 else 'Retention needs improvement'}. "
        f"Implement a 48-hour post-trial follow-up protocol and a 14-day upgrade nudge for trial-to-package conversion."))
    
    return "\n".join(insights)


def build_retention_recommendations(ctx):
    lapsed = ctx['lapsed']
    baseline = ctx['baseline']
    lapsed_prod = get_lapsed_product(ctx['loc_key'], ctx['month_key'])
    
    insights = []
    
    insights.append(insight_card("01",
        f"Reactivation pool: {fmt_int(ctx['cumulative_lapsed'])} cumulative lapsed members.",
        f"The cumulative lapsed book is the single largest revenue recovery opportunity. "
        f"Reactivating 15% ({int(ctx['cumulative_lapsed']*0.15)} members) at 50% LTV would recover approximately &#8377;{ctx['cumulative_lapsed']*0.15*20000/1e5:.1f}L."))
    
    insights.append(insight_card("02",
        f"Churn rate at {pct(lapsed['churn'])} &mdash; {ctx['churn_baseline']} vs baseline.",
        f"{'Churn is above baseline &mdash; retention needs reinforcement.' if lapsed['churn'] > baseline['lapsed']['churn'] else 'Churn is below baseline &mdash; retention is improving.'} "
        f"Implement 30/60/90-day pre-expiry outreach to reduce future lapses."))
    
    # Top lapse product
    lapsed_prods = [(n, v) for n, v in lapsed_prod.items() if v['lapsed'] > 0]
    lapsed_prods.sort(key=lambda x: -x[1]['lapsed'])
    if lapsed_prods:
        top = lapsed_prods[0]
        insights.append(insight_card("03",
            f"Priority reactivation: {top[0]} with {top[1]['lapsed']} lapses.",
            f"This SKU has the highest lapse count. Targeted win-back campaign with a time-limited offer "
            f"(e.g., 20% off renewal within 30 days) could recover an estimated {int(top[1]['lapsed']*0.2)} members."))
    
    insights.append(insight_card("04",
        f"Renewal rate at {pct(lapsed['renewal_rate'])} &mdash; {ctx['renewal_baseline']} vs baseline.",
        f"{'Renewal rate is above baseline &mdash; maintain current retention practices.' if lapsed['renewal_rate'] > baseline['lapsed']['renewal_rate'] else 'Renewal rate is below baseline &mdash; strengthen renewal outreach.'} "
        f"Industry benchmark: 50&ndash;60% for boutique fitness."))
    
    return "\n".join(insights)


def build_ops_recommendations(ctx):
    checkins = ctx['checkins']
    
    insights = []
    
    insights.append(insight_card("01",
        f"{checkins['late_cancel']} late cancels at {pct(ctx['lc_rate'])} of all check-ins.",
        f"Late-cancel rate of {pct(ctx['lc_rate'])} means roughly 1 in {int(100/ctx['lc_rate']) if ctx['lc_rate'] else 'n/a'} check-ins is a late cancel. "
        f"Implementing a &#8377;500 penalty or 1-class deduction would reduce this by an estimated 50%."))
    
    insights.append(insight_card("02",
        f"{checkins['heavy_cancelers']} heavy cancelers with 5+ late cancels each.",
        f"These {checkins['heavy_cancelers']} members account for a disproportionate share of late cancels. "
        f"Personal outreach to understand the root cause (scheduling friction, motivation, etc.) and a tailored solution."))
    
    insights.append(insight_card("03",
        "Total penalty collected: &#8377;0 &mdash; a near-zero-risk policy intervention.",
        f"No late-cancel penalty is currently enforced. Implementing one is the single easiest operational win: "
        f"it recovers revenue, improves scheduling discipline, and frees up capacity for waitlisted members. "
        f"Estimated recovery at &#8377;500/cancel: &#8377;{checkins['late_cancel']*500/1e5:.1f}L/month."))
    
    insights.append(insight_card("04",
        f"Auto-reminder 2 hours before class would reduce no-shows.",
        f"An automated reminder (SMS/push) 2 hours before class would reduce both late cancels and no-shows. "
        f"This is a quick CRM configuration, not a policy change."))
    
    return "\n".join(insights)


# ─── Section 07: Predictions & Forward View ───────────────────────────────────

def section_07(ctx):
    loc = ctx['loc']
    mo = ctx['mo']
    s = ctx['sales']
    sess = ctx['sessions']
    leads = ctx['leads']
    lapsed = ctx['lapsed']
    baseline = ctx['baseline']
    
    loc_name = loc['short_name']
    month_name = mo['month_name']
    next_name = mo['next_month_name']
    steady_state_end = month_offset_label(ctx['month_key'], 3)

    # Forecast calculations
    net_base = s['net']
    # Base case: flat to -5% seasonality
    base_low = net_base * 0.95
    base_high = net_base * 1.0
    # Upside case: +10-15% with interventions
    upside_low = net_base * 1.10
    upside_high = net_base * 1.15
    
    title = (f"{next_name} {ctx['mo']['next_year']} forecast: {lakh(base_low)}&ndash;{lakh(base_high)} net sales if no intervention, "
             f"{lakh(upside_low)}&ndash;{lakh(upside_high)} if the five decisions are executed. "
             f"Three red flags to monitor weekly.")
    
    deck = (f"The forward view below blends the {month_name} baseline with the historical {ctx['baseline_label']} trajectory and the "
            f"five recommended interventions. The base-case forecast assumes no operational change; the upside case "
            f"assumes execution of the five decisions starting {next_name} W2. Three red flags &mdash; discount penetration, "
            f"late-cancel rate, and lead pipeline volume &mdash; should be monitored weekly and acted on if they deteriorate "
            f"beyond the thresholds below.")
    
    # Forecast insights
    forecast_insights = build_forecast_insights(ctx, base_low, base_high, upside_low, upside_high)
    
    # Red flags
    red_flags = build_red_flags(ctx)
    
    # Steady-state
    steady_state = build_steady_state(ctx, baseline)
    
    html = f'''
<section class="report-section" id="predictions{ctx.get('id_suffix', '')}">
  <div class="container">
{section_header("07 &middot; Predictions &amp; Forward View", title, deck, 7, loc_key=ctx["loc_key"], month_key=ctx["month_key"], id_suffix=ctx.get("id_suffix", ""))}

{subsection(f"{next_name} {ctx['mo']['next_year']} forecast &mdash; base case vs upside case",
    f"The forecast below assumes (a) no major exogenous shock, (b) historical seasonality, and (c) for the upside case, the five decisions beginning to deliver from {next_name} W3.")}

    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">Forecast insights</div>

{forecast_insights}
      </div>

      <div class="data-pane">
        <div class="pane-title" style="padding: 16px 16px 8px;">{next_name} {ctx['mo']['next_year']} Forecast &middot; Base vs Upside</div>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr><th>Metric</th><th>{month_name} Actual</th><th>Base Case</th><th>Upside Case</th></tr>
            </thead>
            <tbody>
              <tr><td>Net Sales</td><td class="num">{lakh(s['net'])}</td><td class="num">{lakh(base_low)}&ndash;{lakh(base_high)}</td><td class="num">{lakh(upside_low)}&ndash;{lakh(upside_high)}</td></tr>
              <tr><td>Sessions</td><td class="num">{sess['sessions']}</td><td class="num">{int(sess['sessions']*0.98)}&ndash;{sess['sessions']}</td><td class="num">{sess['sessions']}&ndash;{int(sess['sessions']*1.05)}</td></tr>
              <tr><td>Visits</td><td class="num">{fmt_int(sess['visits'])}</td><td class="num">{fmt_int(sess['visits']*0.97)}&ndash;{fmt_int(sess['visits'])}</td><td class="num">{fmt_int(sess['visits'])}&ndash;{fmt_int(sess['visits']*1.05)}</td></tr>
              <tr><td>Fill Rate</td><td class="num">{pct(sess['fill'])}</td><td class="num">{pct(sess['fill']-1)}&ndash;{pct(sess['fill'])}</td><td class="num">{pct(sess['fill'])}&ndash;{pct(sess['fill']+3)}</td></tr>
              <tr><td>Leads</td><td class="num">{leads['total']}</td><td class="num">{int(leads['total']*0.95)}&ndash;{leads['total']}</td><td class="num">{int(leads['total']*1.15)}&ndash;{int(leads['total']*1.25)}</td></tr>
              <tr><td>Conversion Rate</td><td class="num">{pct(leads['rate'])}</td><td class="num">{pct(leads['rate'])}</td><td class="num">{pct(leads['rate']+3)}&ndash;{pct(leads['rate']+5)}</td></tr>
              <tr><td>Churn Rate</td><td class="num">{pct(lapsed['churn'])}</td><td class="num">{pct(lapsed['churn'])}</td><td class="num">{pct(max(0,lapsed['churn']-5))}&ndash;{pct(max(0,lapsed['churn']-8))}</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

{subsection("Three red flags to monitor weekly",
    "These are the leading indicators that, if they deteriorate beyond the thresholds below, should trigger immediate management intervention.")}

    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">Red flag insights</div>

{red_flags}
      </div>
      <div class="data-pane">
        <div class="pane-title" style="padding: 16px 16px 8px;">Red Flag Thresholds &middot; {next_name} {ctx['mo']['next_year']}</div>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr><th>Red Flag</th><th>{month_name} Actual</th><th>Threshold</th><th>Action if Breached</th></tr>
            </thead>
            <tbody>
              <tr><td>Discount Penetration</td><td class="num">{pct(ctx['disc_penetration'])}</td><td class="num">&gt; 10%</td><td>Freeze all discounts &gt; &#8377;2,000</td></tr>
              <tr><td>Late-Cancel Rate</td><td class="num">{pct(ctx['lc_rate'])}</td><td class="num">&gt; 12%</td><td>Implement penalty policy</td></tr>
              <tr><td>Lead Pipeline Volume</td><td class="num">{leads['total']}</td><td class="num">&lt; {int(baseline['leads']['total']*0.8)}</td><td>Emergency marketing sprint</td></tr>
              <tr><td>Churn Rate</td><td class="num">{pct(lapsed['churn'])}</td><td class="num">&gt; {pct(baseline['lapsed']['churn']+5, 0)}</td><td>Activate reactivation campaign</td></tr>
              <tr><td>Fill Rate</td><td class="num">{pct(sess['fill'])}</td><td class="num">&lt; {pct(baseline['sessions']['fill']-5, 0)}</td><td>Schedule review &amp; slot trimming</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

{subsection(f"Steady-state outlook &mdash; {mo['next_month_name']} {ctx['mo']['next_year']}&ndash;{steady_state_end}",
    f"Once all five decisions are fully delivered (estimated 60&ndash;90 days), the monthly run-rate could reach a structural step-up from the {ctx['baseline_label']} baseline.")}

    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">Steady-state insights</div>

{steady_state}
      </div>
      <div class="data-pane">
        <div class="pane-title" style="padding: 16px 16px 8px;">Steady-State Target &middot; {steady_state_end}</div>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr><th>Metric</th><th>{ctx['baseline_label']} Baseline</th><th>{month_name} Actual</th><th>Steady-State Target</th></tr>
            </thead>
            <tbody>
              <tr><td>Net Sales</td><td class="num">{lakh(baseline['sales']['net'])}</td><td class="num">{lakh(s['net'])}</td><td class="num">{lakh(baseline['sales']['net']*1.3)}&ndash;{lakh(baseline['sales']['net']*1.5)}</td></tr>
              <tr><td>Sessions</td><td class="num">{baseline['sessions']['sessions']:.0f}</td><td class="num">{sess['sessions']}</td><td class="num">{int(baseline['sessions']['sessions']*1.1)}&ndash;{int(baseline['sessions']['sessions']*1.2)}</td></tr>
              <tr><td>Fill Rate</td><td class="num">{pct(baseline['sessions']['fill'])}</td><td class="num">{pct(sess['fill'])}</td><td class="num">50%&ndash;55%</td></tr>
              <tr><td>Conversion Rate</td><td class="num">{pct(baseline['leads']['rate'])}</td><td class="num">{pct(leads['rate'])}</td><td class="num">15%&ndash;20%</td></tr>
              <tr><td>Churn Rate</td><td class="num">{pct(baseline['lapsed']['churn'])}</td><td class="num">{pct(lapsed['churn'])}</td><td class="num">30%&ndash;35%</td></tr>
              <tr><td>Discount Penetration</td><td class="num">{pct(baseline['sales']['disc']/baseline['sales']['gross']*100)}</td><td class="num">{pct(ctx['disc_penetration'])}</td><td class="num">&le; 8%</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</section>
'''
    return html


def build_forecast_insights(ctx, base_low, base_high, upside_low, upside_high):
    s = ctx['sales']
    mo = ctx['mo']
    baseline = ctx['baseline']
    
    insights = []
    
    insights.append(insight_card("01",
        f"Base-case {mo['next_month_name']} net sales: {lakh(base_low)}&ndash;{lakh(base_high)}.",
        f"{mo['month_name']} baseline ({lakh(s['net'])}) + typical seasonality = {lakh(base_low)}&ndash;{lakh(base_high)}. "
        f"Essentially flat vs {mo['month_name']}. Without intervention, the studio will continue at current run-rate."))
    
    insights.append(insight_card("02",
        f"Upside-case {mo['next_month_name']} net sales: {lakh(upside_low)}&ndash;{lakh(upside_high)}.",
        f"If discount discipline delivers &#8377;0.5-1L of saving + schedule restructuring delivers &#8377;0.5L of incremental revenue "
        f"+ funnel repair delivers 2 extra conversions (&#8377;50K LTV), {mo['next_month_name']} upside = {lakh(upside_low)}&ndash;{lakh(upside_high)}."))
    
    insights.append(insight_card("03",
        f"Steady-state upside: {lakh(baseline['sales']['net']*1.3)}&ndash;{lakh(baseline['sales']['net']*1.5)}/month.",
        f"Once all five decisions are fully delivered (estimated 60-90 days), the monthly run-rate could reach "
        f"{lakh(baseline['sales']['net']*1.3)}&ndash;{lakh(baseline['sales']['net']*1.5)}. "
        f"This is +30-50% over the {ctx['baseline_label']} baseline."))
    
    insights.append(insight_card("04",
        f"Lead pipeline is the most volatile input.",
        f"{mo['month_name']}'s {ctx['leads']['total']} leads is {'the lowest in recent months' if ctx['leads']['total'] < baseline['leads']['total'] else 'healthy'}. "
        f"If {mo['next_month_name']} repeats the trend, even an improved conversion rate cannot offset the volume loss. "
        f"Lead pipeline replenishment is the most time-sensitive workstream."))
    
    insights.append(insight_card("05",
        f"Discount penetration is the most controllable input.",
        f"Unlike lead volume, discount penetration is fully within management control. "
        f"A hard cap at {lakh(s['disc']*1.2)}/month can be enforced from {mo['next_month_name']} W1 with no operational complexity."))
    
    insights.append(insight_card("06",
        f"Late-cancel policy is the fastest-implementing win.",
        f"Implementing a &#8377;500 late-cancel penalty is a single policy change that can be enacted immediately. "
        f"Estimated revenue recovery: &#8377;{ctx['checkins']['late_cancel']*500/1e5:.1f}L/month at current cancel volume."))
    
    return "\n".join(insights)


def build_red_flags(ctx):
    s = ctx['sales']
    leads = ctx['leads']
    lapsed = ctx['lapsed']
    sess = ctx['sessions']
    baseline = ctx['baseline']
    
    insights = []
    
    insights.append(insight_card("01",
        f"Discount penetration at {pct(ctx['disc_penetration'])} &mdash; threshold 10%.",
        f"{'Currently above threshold &mdash; action needed.' if ctx['disc_penetration'] > 10 else 'Currently within threshold.'} "
        f"If penetration exceeds 10%, freeze all discounts above &#8377;2,000 pending management approval."))
    
    insights.append(insight_card("02",
        f"Late-cancel rate at {pct(ctx['lc_rate'])} &mdash; threshold 12%.",
        f"{'Currently above threshold &mdash; implement penalty.' if ctx['lc_rate'] > 12 else 'Currently within threshold.'} "
        f"If rate exceeds 12%, implement the &#8377;500 penalty policy immediately."))
    
    insights.append(insight_card("03",
        f"Lead pipeline at {leads['total']} &mdash; threshold {int(baseline['leads']['total']*0.8)}.",
        f"{'Currently below threshold &mdash; emergency sprint needed.' if leads['total'] < baseline['leads']['total']*0.8 else 'Currently above threshold.'} "
        f"If pipeline drops below {int(baseline['leads']['total']*0.8)}, launch an emergency marketing sprint within 7 days."))
    
    insights.append(insight_card("04",
        f"Churn rate at {pct(lapsed['churn'])} &mdash; threshold {pct(baseline['lapsed']['churn']+5, 0)}.",
        f"{'Currently above threshold &mdash; activate reactivation.' if lapsed['churn'] > baseline['lapsed']['churn']+5 else 'Currently within threshold.'} "
        f"If churn exceeds {pct(baseline['lapsed']['churn']+5, 0)}, activate the full reactivation campaign immediately."))
    
    insights.append(insight_card("05",
        f"Fill rate at {pct(sess['fill'])} &mdash; threshold {pct(baseline['sessions']['fill']-5, 0)}.",
        f"{'Currently below threshold &mdash; schedule review needed.' if sess['fill'] < baseline['sessions']['fill']-5 else 'Currently above threshold.'} "
        f"If fill rate drops below {pct(baseline['sessions']['fill']-5, 0)}, conduct a full schedule review and trim low-fill slots."))
    
    return "\n".join(insights)


def build_steady_state(ctx, baseline):
    s = ctx['sales']
    leads = ctx['leads']
    lapsed = ctx['lapsed']
    sess = ctx['sessions']
    
    insights = []
    
    insights.append(insight_card("01",
        f"Net sales target: {lakh(baseline['sales']['net']*1.3)}&ndash;{lakh(baseline['sales']['net']*1.5)}/month.",
        f"A 30-50% step-up from the {ctx['baseline_label']} baseline of {lakh(baseline['sales']['net'])}. "
        f"This would represent a structural improvement in studio economics, not a one-month spike."))
    
    insights.append(insight_card("02",
        f"Fill rate target: 50&ndash;55% (from {pct(baseline['sessions']['fill'])} baseline).",
        f"Schedule rebalancing from low-fill to high-fill formats would lift overall fill rate by 5-10pp. "
        f"Each percentage point of fill rate is worth approximately &#8377;{sess['revenue']/sess['capacity']*0.01/1e5:.2f}L in incremental revenue."))
    
    insights.append(insight_card("03",
        f"Conversion rate target: 15&ndash;20% (from {pct(baseline['leads']['rate'])} baseline).",
        f"Funnel repair &mdash; referral amplification, trial follow-up protocol, and zero-conversion source cleanup &mdash; "
        f"would lift conversion by 3-8pp. Each additional conversion is worth approximately &#8377;25,000 in LTV."))
    
    insights.append(insight_card("04",
        f"Churn rate target: 30&ndash;35% (from {pct(baseline['lapsed']['churn'])} baseline).",
        f"Proactive retention &mdash; pre-expiry outreach, reactivation campaigns, and CRM improvements &mdash; "
        f"would reduce churn by 5-10pp. Each percentage point of churn reduction retains approximately {int(lapsed['total']*0.01)} members/month."))
    
    return "\n".join(insights)
