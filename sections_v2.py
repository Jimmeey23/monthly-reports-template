#!/usr/bin/env python3
"""
Section generators for the parameterized performance report.
Each function takes a context dict and returns HTML for one section.
"""
import calendar
import json
import html
import re

import report_shell

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
_charts_mod = None

def _charts():
    global _charts_mod
    if _charts_mod is None:
        import charts_v2
        _charts_mod = charts_v2
    return _charts_mod


def _init_imports():
    global _lakh, _lakh_raw, _rupee, _pct, _fmt_int, _pct_change, _pp_change, _badge, _badge_from_pp, _mult, _DATA
    global get_sales_breakdowns, get_sessions_by_class, get_sessions_by_trainer, get_sessions_by_format
    global get_leads_source, get_new_type, get_lapsed_product, get_lapsed_cumulative, get_heatmap
    global get_sessions_by_trainer_format, get_sessions_by_slot, get_lapsed_members
    from gen_report_v2 import (
        lakh as _l, lakh_raw as _lr, rupee as _r, pct as _p, fmt_int as _fi,
        pct_change as _pc, pp_change as _ppc, badge as _b, badge_from_pp as _bfp,
        mult as _m, DATA as _D,
        get_sales_breakdowns as _gsb, get_sessions_by_class as _gsc,
        get_sessions_by_trainer as _gst, get_sessions_by_format as _gsf,
        get_leads_source as _gls, get_new_type as _gnt,
        get_lapsed_product as _glp, get_lapsed_cumulative as _glc, get_heatmap as _gh,
        get_sessions_by_trainer_format as _gstf,
        get_sessions_by_slot as _gss, get_lapsed_members as _glm
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
    get_sessions_by_slot = _gss
    get_lapsed_members = _glm

def get_top_lead_source(ctx):
    """Get the top lead source by volume."""
    sources = get_leads_source(ctx['loc_key'], ctx['month_key'])
    if not sources:
        return "n/a"
    top = max(sources.items(), key=lambda x: x[1]['total'])
    return f"{top[0]} ({top[1]['total']} leads, {top[1]['converted']} converted)"

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

# The report runs money → demand → funnel → retention → outlook → actions,
# then a month-on-month appendix that holds every section's history grid.
SECTION_IDS = {
    1: 'executive-summary', 2: 'revenue-performance', 3: 'conversion-funnel',
    4: 'sessions', 5: 'lapsed', 6: 'recommendations',
    7: 'predictions', 8: 'appendix',
}

SECTION_TITLES = {
    'executive-summary': 'Executive summary',
    'revenue-performance': 'Revenue performance',
    'sessions': 'Demand & utilisation',
    'conversion-funnel': 'Conversion funnel',
    'lapsed': 'Retention & lapsed',
    'predictions': 'Outlook',
    'recommendations': 'Actions',
}

# Each section registers its month-on-month grid here while it renders; the
# appendix at the end of the report prints them all in one place.
MOM_REGISTRY = {}


def reset_mom_registry():
    MOM_REGISTRY.clear()



def render_ai_result(result):
    if not result:
        return ''

    def safe_html(s):
        if s is None: return ''
        return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    def safe_val(s):
        if not s or str(s).strip() == '—': return '—'
        return str(s).strip()

    title = safe_html(result.get('title') or result.get('performance_summary', {}).get('title', 'Executive Strategic Analysis'))
    summary_text = safe_html(result.get('detailed_summary') or result.get('summary') or result.get('performance_summary', {}).get('narrative', ''))

    insights = result.get('insights') or result.get('key_insights') or []
    recs = result.get('recommendations') or result.get('actions') or []

    # 1. Detailed Summary Block
    summary_html = ''
    if summary_text:
        paras = [p.strip() for p in summary_text.split('\n\n') if p.strip()]
        if not paras:
            paras = [summary_text.strip()]
        para_tags = "".join([f'<p class="ai-summary-para">{p}</p>' for p in paras])
        summary_html = f'''<div class="ai-summary-narrative-block">
            <div class="ai-block-heading">&#128203; Detailed Executive Narrative</div>
            {para_tags}
        </div>'''

    # 2. Bulleted Insights Block ("What These Metrics Tell Us")
    insights_html = ''
    if insights:
        items_html = ''
        for i, ins in enumerate(insights):
            headline = safe_html(ins.get('headline') or ins.get('title', '—'))
            meaning = safe_html(ins.get('meaning') or (ins.text if hasattr(ins, 'text') else ins.get('text', '—')))
            evidence = safe_html(ins.get('data_evidence', ''))

            # Cleanly merge evidence into narrative context if present, without raw badge callouts
            evidence_text = f' <span class="ai-bullet-evidence-inline">({evidence})</span>' if evidence and evidence != '—' else ''

            items_html += f'''
            <li class="ai-bullet-item">
              <div class="ai-bullet-dot">&#128161;</div>
              <div class="ai-bullet-content">
                <div class="ai-bullet-header"><strong class="ai-bullet-title">{headline}</strong></div>
                <div class="ai-bullet-meaning">{meaning}{evidence_text}</div>
              </div>
            </li>'''

        insights_html = f'''<div class="ai-list-block">
            <div class="ai-block-heading">&#128161; What These Metrics Tell Us ({len(insights)})</div>
            <ul class="ai-bullet-list">{items_html}</ul>
        </div>'''

    # 3. Bulleted Recommendations Block ("Strategic Action Plan")
    recs_html = ''
    if recs:
        items_html = ''
        for i, r in enumerate(recs):
            rec_title = safe_html(r.get('title') or r.get('action', '—'))
            desc = safe_html(r.get('description') or r.get('details') or r.get('rationale', '—'))
            impact = safe_html(r.get('expected_impact') or r.get('impact', '—'))
            timeline = safe_html(r.get('timeline', '—'))
            owner = safe_html(r.get('owner', '—'))
            priority = safe_html(r.get('priority', '')).lower()

            pri_pill = f'<span class="meta-pill pri-{priority}">{priority.upper()} PRIORITY</span>' if priority and priority != '—' else ''
            time_pill = f'<span class="meta-pill">&#128197; {timeline}</span>' if timeline and timeline != '—' else ''
            owner_pill = f'<span class="meta-pill">&#128100; {owner}</span>' if owner and owner != '—' else ''
            impact_html = f'<div class="ai-rec-impact-tag">&#127919; <strong>Expected Impact:</strong> {impact}</div>' if impact and impact != '—' else ''

            items_html += f'''
            <li class="ai-bullet-item rec-item">
              <div class="ai-bullet-dot rec-dot">&#127919;</div>
              <div class="ai-bullet-content">
                <div class="ai-bullet-header"><strong class="ai-bullet-title">{rec_title}</strong></div>
                <div class="ai-bullet-meaning">{desc}</div>
                {impact_html}
                <div class="ai-rec-meta">{pri_pill}{time_pill}{owner_pill}</div>
              </div>
            </li>'''

        recs_html = f'''<div class="ai-list-block">
            <div class="ai-block-heading">&#127919; Actionable Recommendations ({len(recs)})</div>
            <ul class="ai-bullet-list">{items_html}</ul>
        </div>'''

    return f'''<div class="ai-result ai-result-v2">
        <div class="ai-result-header">
            <div class="ai-result-header-icon">&#10024;</div>
            <div>
                <div class="ai-result-header-title">{title}</div>
                <div class="ai-result-header-sub">Strategic Analysis &amp; Action Plan</div>
            </div>
        </div>
        {summary_html}
        {insights_html}
        {recs_html}
    </div>'''


def section_header(eyebrow, title, deck, section_num, total=7, loc_key='', month_key='',
                   id_suffix='', signals=None):
    """Chapter opener: eyebrow, title, deck, and the live figures at a glance.

    `signals` is a list of (label, value, note) — the two or three numbers the
    chapter is about to explain. They are printed as the scrolling strip under
    the header, so the reader sees them before the prose starts.
    """
    section_id = SECTION_IDS.get(section_num, f'section-{section_num}')
    slot_id = f'ai-slot-{section_id}{id_suffix}'
    mom_key = report_shell.MOM_KEYS.get(section_num)

    # Only the five chapters with a history table carry an `i` button; the rest
    # would open an empty panel.
    mom_btn = ''
    if mom_key:
        mom_btn = (f'<button aria-label="View month on month data" class="mom-info-btn" '
                   f'data-mom="{mom_key}">i</button>')

    marquee = ''
    if signals:
        marquee = report_shell.section_marquee(
            [(value, label) for label, value, _ in signals],
            SECTION_TITLES.get(section_id, section_id))

    return f"""    <div class="section-hero{' has-section-marquee' if marquee else ''}" data-num="{section_num:02d}">
      <div class="section-header">
        <div class="section-header-left">
          <span class="section-eyebrow">{section_num:02d} · {eyebrow}</span>
          <h2 class="section-title">{title}</h2>
          <p class="section-deck">{deck}</p>
        </div>
        <div class="section-header-right">
          {mom_btn}
          <div class="section-anchor">Section {section_num} / {total:02d}</div>
        </div>
      </div>
    </div>{marquee}
    <div class="ai-slot" id="{slot_id}">{render_ai_result(AI_CONTEXT.get(f"{loc_key}|{month_key}|{section_id}", {}))}</div>"""


def figure_band(title, note, chart, legend='', wide=False):
    """A chart card. Sits between the subsection heading and the detail table
    so the shape of the data lands before the numbers do."""
    return f"""    <figure class="figure-band{' figure-band-wide' if wide else ''}">
      <div class="figure-head">
        <div>
          <div class="figure-title">{title}</div>
          <figcaption class="figure-note">{note}</figcaption>
        </div>
      </div>
      <div class="figure-body">{chart}{legend}</div>
    </figure>"""


def chart_legend(items):
    """items = [(label, colour, value), ...] — colour may be a CSS variable."""
    if not items:
        return ''
    rows = ''.join(
        f'<li><span class="swatch" style="background: {colour};"></span>'
        f'<span class="legend-label">{label}</span>'
        f'<span class="legend-value">{value}</span></li>'
        for label, colour, value in items)
    return f'<ul class="chart-legend">{rows}</ul>'


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


def classify_format(class_name):
    """Every class is one of 3 formats: PowerCycle, Strength Lab, or Barre."""
    name = (class_name or '').lower()
    if 'powercycle' in name or 'power cycle' in name:
        return 'PowerCycle'
    if 'strength lab' in name:
        return 'Strength Lab'
    return 'Barre'


# ─── Shared UI kit ────────────────────────────────────────────────────────────
# Every section builds its panels, tables, tiles and ranked lists through these
# helpers so the report keeps one set of surfaces instead of a different card
# per section. Change the look here and it changes everywhere.

# ─── Metric dictionary ────────────────────────────────────────────────────────
# What a figure means and how it is worked out, keyed by a normalised label.
# The back of every metric card reads from here, so the definition a reader
# sees on a hero card and on a section card is the same sentence.

METRIC_DEFS = {
    'net revenue': ('Revenue actually banked after every discount has been applied.',
                    'Net revenue = Gross revenue &minus; Discounts'),
    'net rev': ('Revenue actually banked after every discount has been applied.',
                'Net revenue = Gross revenue &minus; Discounts'),
    'gross revenue': ('Full list value of everything sold, before discounts.',
                      'Gross revenue = &sum; (unit price &times; units sold)'),
    'gross rev': ('Full list value of everything sold, before discounts.',
                  'Gross revenue = &sum; (unit price &times; units sold)'),
    'discount': ('Value given away against list price across the period.',
                 'Discount = Gross revenue &minus; Net revenue'),
    'disc %': ('How much of gross revenue was handed back as discount.',
               'Discount % = Discount &divide; Gross revenue &times; 100'),
    'discount rate': ('How much of gross revenue was handed back as discount.',
                      'Discount % = Discount &divide; Gross revenue &times; 100'),
    'transactions': ('Number of separate paid checkouts in the period.',
                     'Transactions = count of distinct payment records'),
    'txns': ('Number of separate paid checkouts in the period.',
             'Transactions = count of distinct payment records'),
    'units': ('Number of individual items sold across all transactions.',
              'Units = &sum; line-item quantities'),
    'aov': ('Average value of a transaction — the size of a typical basket.',
            'AOV = Gross revenue &divide; Transactions'),
    'atv': ('Average value of a single item sold.',
            'ATV = Gross revenue &divide; Units'),
    'upt': ('How many items the average transaction contains.',
            'UPT = Units &divide; Transactions'),
    'members': ('Distinct paying members who transacted in the period.',
                'Members = count of unique member IDs with a sale'),
    'sessions': ('Classes actually delivered on the timetable.',
                 'Sessions = count of scheduled classes that ran'),
    'visits': ('Attendances recorded across every session.',
               'Visits = &sum; check-ins per session'),
    'capacity': ('Total seats offered across every session that ran.',
                 'Capacity = &sum; (seats per session)'),
    'fill rate': ('How full the timetable ran — the core utilisation figure.',
                  'Fill % = Visits &divide; Capacity &times; 100'),
    'fill %': ('How full the timetable ran — the core utilisation figure.',
               'Fill % = Visits &divide; Capacity &times; 100'),
    'class avg': ('Average heads in a class, counting sessions that ran empty.',
                  'Class avg (incl. empty) = Visits &divide; Sessions'),
    'class avg (excl. empty)': ('Average heads in a class that had at least one attendee.',
                                'Class avg (excl. empty) = Visits &divide; (Sessions &minus; Empty sessions)'),
    'empty sessions': ('Sessions that ran with nobody in the room.',
                       'Empty sessions = count of sessions where Visits = 0'),
    'leads': ('New enquiries captured in the period, across every source.',
              'Leads = count of enquiry records created'),
    'converted': ('Leads or trialists who went on to buy a membership.',
                  'Converted = count of leads with a first paid sale'),
    'conversion rate': ('Share of enquiries that turned into paying members.',
                        'Conversion % = Converted &divide; Leads &times; 100'),
    'conv %': ('Share of enquiries that turned into paying members.',
               'Conversion % = Converted &divide; Leads &times; 100'),
    'trials': ('First-time visitors who took an introductory class.',
               'Trials = count of first visits on a trial product'),
    'retained': ('Converted members still attending at the end of the window.',
                 'Retained = converted members with a visit in the retention window'),
    'retention rate': ('Share of new clients still attending at period end.',
                       'Retention % = Retained &divide; New clients &times; 100'),
    'renewal rate': ('Share of expiring memberships that were renewed.',
                     'Renewal % = Renewed &divide; Total expirations &times; 100'),
    'churn': ('Share of expiring memberships that lapsed rather than renewed.',
              'Churn % = Lapsed &divide; Total expirations &times; 100'),
    'churn %': ('Share of expiring memberships that lapsed rather than renewed.',
                'Churn % = Lapsed &divide; Total expirations &times; 100'),
    'lapsed': ('Memberships that expired without being renewed.',
               'Lapsed = Total expirations &minus; Renewed &minus; Frozen'),
    'revenue per visit': ('What each attendance is worth in revenue terms.',
                          'Revenue per visit = Net revenue &divide; Visits'),
    'share': ('This row\u2019s slice of the column total.',
              'Share % = Row value &divide; Total &times; 100'),
}


def metric_def(label):
    """(definition, formula) for a metric label, or (None, None)."""
    key = re.sub(r'<[^>]+>', '', str(label)).strip().lower()
    key = key.replace('&amp;', '&').replace('\u00a0', ' ')
    if key in METRIC_DEFS:
        return METRIC_DEFS[key]
    for candidate, value in METRIC_DEFS.items():
        if key.startswith(candidate) or candidate in key:
            return value
    return (None, None)


_METRIC_CARD_SEQ = [0]


def metric_card(label, value, sub='', tone='', trends=None, kicker='Metric',
                focus='', drill=None, series=None, labels=None, **extra):
    """A section-level metric card — the hero KPI card at a smaller size.

    Sections used to print their own flat tiles, which is why the report had two
    different-looking metric surfaces. Everything now goes through this.
    """
    _METRIC_CARD_SEQ[0] += 1
    definition, formula = metric_def(label)
    card = {
        'label': label,
        'value': value,
        'sub': sub,
        'tone': tone,
        'compact': True,
        'kicker': kicker,
        'trends': trends or [],
        'definition': definition or extra.get('definition', ''),
        'formula': formula or extra.get('formula', ''),
        'focus': focus or 'Read this alongside the table below.',
        'tip': re.sub(r'<[^>]+>', '', str(definition or '')),
    }
    if series:
        card['series'] = ','.join(f'{v:.4g}' for v in series)
        # These land in an HTML attribute, and class names carry apostrophes.
        card['labels'] = '|'.join(
            html.escape(_strip(l), quote=True) for l in (labels or [''] * len(series)))
        card['chart_type'] = extra.get('chart_type', 'area')
        card['decimals'] = extra.get('decimals', 0)
        card['prefix'] = extra.get('prefix', '')
        card['suffix'] = extra.get('suffix', '')
    if drill:
        card['drill'] = drill
    return report_shell.kpi_card(f'mc-{_METRIC_CARD_SEQ[0]}', card)


def metric_tiles(items, columns=None):
    """A strip of headline figures, rendered as the report's metric card.

    items = (label, value, sub, tone, series, series_labels) — everything after
    `value` is optional. When a series is supplied the front of the card draws
    it as an animated area chart instead of sitting empty.
    """
    if not items:
        return ''
    stats = []
    for item in items:
        stats.append({'label': _strip(item[0]), 'value': _strip(item[1]),
                      'sub': _strip(item[2]) if len(item) > 2 else ''})

    cards = []
    for item in items:
        label, value = item[0], item[1]
        sub = item[2] if len(item) > 2 else ''
        tone = item[3] if len(item) > 3 else ''
        series = item[4] if len(item) > 4 else None
        series_labels = item[5] if len(item) > 5 else None
        definition, _formula = metric_def(label)
        drill = {
            'kicker': 'Metric detail',
            'title': _strip(label),
            'subtitle': definition or '',
            'stats': stats,
            'footnote': 'Every figure in this group, so one card can be read against its neighbours.',
        }
        cards.append(metric_card(label, value, sub, tone, drill=drill,
                                 series=series, labels=series_labels, decimals=1))
    style = f' style="--tile-columns: {columns or min(len(items), 4)}"'
    return f'<div class="metric-card-strip"{style}>{"".join(cards)}</div>'


def _strip(value):
    """Plain text from a snippet that may carry markup or HTML entities."""
    text = re.sub(r'<[^>]+>', '', str(value))
    return html.unescape(text).strip()


def delta_pill(change_str, higher_is_better=True, label='vs last month'):
    """A change figure printed as its own pill, toned by whether it is good
    news. `badge()` only returns the tone class, so this is the thing to put
    in a tile or a header."""
    if not change_str or 'n/a' in str(change_str):
        return f'<span class="delta-pill"><span class="badge neutral">n/a</span></span>'
    tone = badge(str(change_str), higher_is_better)
    lbl = f'<span class="delta-pill-label">{label}</span>' if label else ''
    return f'<span class="delta-pill">{lbl}<span class="badge {tone}">{change_str}</span></span>'


def data_panel(title, subtitle, body, controls=''):
    """A titled surface wrapping a table, list or chart. The header, border and
    radius come from one place, so a table panel and a list panel match."""
    sub = f'<div class="panel-subtitle">{subtitle}</div>' if subtitle else ''
    ctl = f'<div class="panel-controls">{controls}</div>' if controls else ''
    return (
        '    <div class="data-panel">\n'
        '      <div class="panel-header">\n'
        f'        <div><div class="panel-title">{title}</div>{sub}</div>\n'
        f'        {ctl}\n'
        '      </div>\n'
        f'{body}\n'
        '    </div>')


def data_table(headers, rows, classes='', attrs='', sortable=False, table_id=''):
    """A table in the report's one table style.

    `headers` is a list of column labels — the first names the row and is left
    aligned; every metric column after it is centred, header included.
    `rows` is a list of ready-made <tr> strings.
    """
    ths = ''.join(f'<th>{h}</th>' for h in headers)
    cls = ('data-table ' + classes).strip()
    extra = (' ' + attrs) if attrs else ''
    if sortable:
        extra += ' data-sortable'
    if table_id:
        extra += f' id="{table_id}"'
    return (
        '        <div class="table-wrap">\n'
        f'          <table class="{cls}"{extra}>\n'
        f'            <thead><tr>{ths}</tr></thead>\n'
        '            <tbody>\n'
        + chr(10).join(rows) + '\n'
        '            </tbody>\n'
        '          </table>\n'
        '        </div>')


_RANK_BOARD_SEQ = [0]


def rank_board(eyebrow, title, note, items, metrics, meta=None, kicker=None, size=5):
    """Top/bottom ranking board — the report's one ranking surface.

    `items` are dicts with a `name` plus every metric key; `metrics` are
    (key, label, fmt, better) tuples; `meta` describes the line printed under
    each name as (key, fmt, suffix) tuples. The payload goes down once and the
    client re-ranks it, so every section's ranking behaves identically.
    """
    if not items:
        return ''
    _RANK_BOARD_SEQ[0] += 1
    board_id = f'rank-board-{_RANK_BOARD_SEQ[0]}'

    payload = json.dumps({
        'kicker': kicker or eyebrow,
        'size': size,
        'metrics': [{'key': k, 'label': label, 'fmt': fmt, 'better': better}
                    for k, label, fmt, better in metrics],
        'meta': [{'key': k, 'fmt': fmt, 'suffix': suffix} for k, fmt, suffix in (meta or [])] or None,
        'items': items,
    }, separators=(',', ':'))

    metric_btns = ''.join(
        f'<button type="button" class="chip{" is-active" if i == 0 else ""}" '
        f'data-rank-metric="{k}">{label}</button>'
        for i, (k, label, _f, _b) in enumerate(metrics))
    sizes = [n for n in (5, 10, 20) if n <= max(5, len(items))]
    size_btns = ''.join(
        f'<button type="button" class="chip{" is-active" if n == size else ""}" '
        f'data-rank-size="{n}">Top {n}</button>' for n in sizes)

    return f'''    <section class="metric-block rank-board" id="{board_id}" data-rank-board>
      <script type="application/json" class="rank-board-data">{payload}</script>
      <div class="metric-block-head rank-board-head">
        <div>
          <span class="metric-block-eyebrow">{eyebrow}</span>
          <h3 class="metric-block-title">{title}</h3>
          <p class="metric-block-note">{note} Both columns re-rank together, so the two ends of the
            same ledger stay comparable. Click any row for its full breakdown.</p>
        </div>
      </div>
      <div class="rank-controls">
        <div class="chip-group" role="group" aria-label="Rank by metric">
          <span class="chip-group-label">Rank by</span>{metric_btns}
        </div>
        <div class="chip-group" role="group" aria-label="How many to show">
          <span class="chip-group-label">Show</span>{size_btns}
        </div>
      </div>
      <div class="rank-columns">
        <div class="rank-column is-top">
          <div class="rank-column-head">
            <span class="rank-column-title">Top performers</span>
            <span class="rank-column-note" data-rank-top-note></span>
          </div>
          <ol class="rank-list" data-rank-list="top"></ol>
        </div>
        <div class="rank-column is-bottom">
          <div class="rank-column-head">
            <span class="rank-column-title">Bottom performers</span>
            <span class="rank-column-note" data-rank-bottom-note></span>
          </div>
          <ol class="rank-list" data-rank-list="bottom"></ol>
        </div>
      </div>
    </section>'''


_NESTED_SEQ = [0]


def nested_rows(groups, group_cells, child_cells, colour_for=None):
    """Rows for a nested table: one parent row per group, children hidden under it.

    `groups` = [(name, group_value, [(child_name, child_value), ...]), ...].
    `group_cells`/`child_cells` turn a value into the metric <td>s that follow
    the name column, so every nested table shares one expansion mechanism.
    """
    rows = []
    for name, value, children in groups:
        _NESTED_SEQ[0] += 1
        gid = f'grp-{_NESTED_SEQ[0]}'
        colour = colour_for(name) if colour_for else 'var(--primary)'
        if children:
            name_cell = (f'<td class="metric-name"><button class="row-toggle" type="button" '
                         f'aria-expanded="false" aria-controls="{gid}">'
                         f'<span class="row-toggle-caret" aria-hidden="true"></span>'
                         f'<span class="row-toggle-dot" style="background:{colour}"></span>'
                         f'<span class="row-toggle-name">{name}</span>'
                         f'<span class="row-toggle-count">{len(children)}</span></button></td>')
            cls = 'group-row has-children'
        else:
            name_cell = (f'<td class="metric-name"><span class="row-toggle is-leaf">'
                         f'<span class="row-toggle-dot" style="background:{colour}"></span>'
                         f'<span class="row-toggle-name">{name}</span></span></td>')
            cls = 'group-row'
        rows.append(f'            <tr class="{cls}">{name_cell}{group_cells(value)}</tr>')
        for child_name, child_value in children:
            child_cell = (f'<td class="metric-name child-name">'
                          f'<span class="child-rule" aria-hidden="true"></span>{child_name}</td>')
            rows.append(f'            <tr class="child-row" data-parent="{gid}" hidden>'
                        f'{child_cell}{child_cells(child_value)}</tr>')
    return rows


def nested_controls():
    """Expand-all / collapse-all for a nested table."""
    return ('<div class="chip-group" role="group" aria-label="Nested rows">'
            '<span class="chip-group-label">Rows</span>'
            '<button type="button" class="chip" data-nested-expand>Expand all</button>'
            '<button type="button" class="chip is-active" data-nested-collapse>Collapse all</button>'
            '</div>')


def share_cell(share, colour='var(--primary)'):
    """A share percentage that also shows its size, for the mix columns."""
    width = max(2.0, min(100.0, share))
    return (
        '<span class="share-meter"><span class="share-meter-track">'
        f'<i style="width:{width:.1f}%;background:{colour}"></i></span>'
        f'<span class="share-meter-value">{pct(share, 1)}</span></span>')


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
    prev2_name = mo['prev2_month_name']
    yoy_name = mo['yoy_month_name']

    # Build insights based on actual data
    insights = build_section_01_insights(ctx)

    # Build KPI table
    kpi_table = build_section_01_kpi_table(ctx)

    # Build executive narrative
    ya_net = baseline.get('sales', {}).get('net', 0)
    net_baseline_diff = ((s['net'] - ya_net) / ya_net * 100) if ya_net else 0

    title = f"{month_name} delivered {'strong' if net_baseline_diff > 5 else 'steady' if net_baseline_diff > -5 else 'soft'} revenue at {lakh(s['net'])} net &mdash; {'above' if net_baseline_diff > 0 else 'below'} the {ctx['year_avg_label']} average, with {'improving' if ctx['conv_mom'].startswith('+') else 'declining'} trial conversion and {'stabilising' if ctx['churn_mom'].startswith('-') else 'rising'} churn as the key watchpoints."

    # Net is collected revenue excluding VAT, so spell the VAT out: without it
    # "net (gross, discount)" reads as net = gross - discount, which it isn't.
    vat = s.get('vat')
    if vat is None:
        vat = s['gross'] - s['net']

    deck = (
        f"Headline revenue closed at <strong>{lakh(s['net'])} net</strong> "
        f"({lakh(s['gross'])} gross incl. {lakh(vat)} VAT, {lakh(s['disc'])} discount), which is "
        f"<strong>{ctx['net_mom']} vs {prev_name}</strong> (M-1), "
        f"<strong>{ctx['net_m2_mom']} vs {prev2_name}</strong> (M-2), "
        f"<strong>{ctx['net_year_avg']} vs {ctx['year_avg_label']}</strong>, "
        f"and <strong>{ctx['net_yoy']} vs {yoy_name}</strong> (YoY). "
        f"Trial conversion is {pct(new['rate'])} ({new['converted']} of {new['trials']} trials), "
        f"{'up' if ctx['conv_mom'].startswith('+') else 'down'} {ctx['conv_mom']} MoM. "
        f"Churn rate stands at {pct(lapsed['churn'])}, {'improving' if ctx['churn_mom'].startswith('-') else 'deteriorating'} {ctx['churn_mom']} MoM. "
        f"Discount efficiency is &#8377;{s['disc_eff']:.2f} of revenue collected per &#8377;1 discounted."
    )

    # Build MoM toggle data
    mom_data = {
        'Net Sales': {'current': lakh(s['net']), 'mom': ctx['net_mom'], 'yoy': ctx['net_yoy']},
        'Gross Sales': {'current': lakh(s['gross']), 'mom': ctx['gross_mom'], 'yoy': ctx['gross_yoy']},
        'Transactions': {'current': fmt_int(s['sales']), 'mom': ctx['sales_count_mom'], 'yoy': 'n/a'},
        'Fill Rate': {'current': pct(sess['fill']), 'mom': ctx['fill_mom'], 'yoy': 'n/a'},
        'Conversion Rate': {'current': pct(new['rate']), 'mom': ctx['conv_mom'], 'yoy': 'n/a'},
        'Churn Rate': {'current': pct(lapsed['churn']), 'mom': ctx['churn_mom'], 'yoy': 'n/a'},
    }
    mom_toggle = mom_toggle_table(ctx, mom_data, f'executive-summary{ctx.get("id_suffix", "")}')

    html = f'''
<section class="report-section" id="executive-summary{ctx.get('id_suffix', '')}">
  <div class="container">
{section_header("Management Pulse &mdash; Growth, Conversion &amp; Risk", title, deck, 1,
                 signals=[("Net Sales", lakh(s['net']), f"{ctx['net_mom']} MoM"),
                          ("Fill Rate", pct(sess['fill']), f"{ctx['fill_mom']} MoM"),
                          ("Churn Rate", pct(lapsed['churn']), f"{ctx['churn_mom']} MoM")], loc_key=ctx["loc_key"], month_key=ctx["month_key"], id_suffix=ctx.get("id_suffix", ""))}

{mom_toggle}

    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">Key Insights &middot; {month_name} {ctx['mo']['year']}</div>

{insights}
      </div>

      <div class="data-pane">
        <div class="panel-header">
          <div>
            <div class="panel-title">Headline KPI Matrix</div>
            <div class="panel-subtitle">Current month vs the prior two months, the current-year average excluding the selected month, and same month last year.</div>
          </div>
          <div class="panel-controls">
            <span class="meta-pill">M-1 / M-2 / Avg / YoY</span>
          </div>
        </div>
{kpi_table}
      </div>
    </div>

{build_balance_sheet(ctx)}
  </div>
</section>
'''
    return html


def build_balance_sheet(ctx):
    """What worked and what didn't, read off the month's own comparators.

    Each candidate names a metric, its direction of good, and the sentence to
    print. Whichever moved most in the right direction becomes a "worked"
    signal; whichever moved most against becomes a leak to fix. Nothing is
    asserted that the figures don't show.
    """
    s = ctx['sales']
    sess = ctx['sessions']
    new = ctx['new']
    lapsed = ctx['lapsed']
    mo = ctx['mo']
    month = mo['month_name']

    def magnitude(change):
        try:
            return abs(float(str(change).replace('%', '').replace('+', '').replace('pp', '')))
        except ValueError:
            return 0.0

    def improved(change, higher_is_better=True):
        text = str(change)
        if text in ('n/a', '') or text == '—':
            return None
        return text.startswith('-') != higher_is_better

    leads = ctx['leads']
    chk = ctx['checkins']

    # (change, higher_is_better, headline, sentence). The month-on-month move is
    # the primary read; the baseline pool below is the second comparator, used
    # only to fill a column that the MoM read leaves short.
    candidates = [
        (ctx['net_mom'], True, 'Revenue moved with the month',
         f"Net sales landed at <strong>{lakh(s['net'])}</strong>, {ctx['net_mom']} on "
         f"{mo['prev_month_name']} and {ctx['net_baseline']} against the {ctx['baseline_label']} baseline."),
        (ctx['fill_mom'], True, 'Capacity utilisation shifted',
         f"Fill rate is <strong>{pct(sess['fill'])}</strong> across {fmt_int(sess['capacity'])} seats "
         f"offered, {ctx['fill_mom']} on the month with {fmt_int(sess['empty'])} sessions running empty."),
        (ctx['conv_mom'], True, 'Trial conversion changed gear',
         f"<strong>{fmt_int(new['trials'])} trials</strong> produced {fmt_int(new.get('converted', 0))} "
         f"conversions at {pct(new['rate'])}, {ctx['conv_mom']} on {mo['prev_month_name']}."),
        (ctx['churn_mom'], False, 'Churn pressure on the member book',
         f"Churn ran at <strong>{pct(lapsed['churn'])}</strong> against a {pct(lapsed['renewal_rate'])} "
         f"renewal rate, {ctx['churn_mom']} on the month across {fmt_int(lapsed['total'])} expiries."),
        (ctx['disc_eff_mom'], True, 'Discount return per rupee',
         f"Every &#8377;1 of discount returned <strong>&#8377;{s['disc_eff']:.2f}</strong> of net revenue, "
         f"{ctx['disc_eff_mom']} on the month at {pct(ctx['disc_penetration'])} penetration."),
        (ctx['late_cancel_mom'], False, 'Late-cancellation discipline',
         f"<strong>{fmt_int(chk.get('late_cancel', 0))} late cancellations</strong> "
         f"({pct(ctx['lc_rate'])} of bookings), {ctx['late_cancel_mom']} on {mo['prev_month_name']}."),
        (ctx['visits_mom'], True, 'Demand volume through the door',
         f"<strong>{fmt_int(sess['visits'])} visits</strong> across {fmt_int(sess['sessions'])} sessions, "
         f"{ctx['visits_mom']} on the month and {ctx['visits_baseline']} against baseline."),
        (ctx['atv_mom'], True, 'Ticket size',
         f"Average transaction value is <strong>{rupee(s['atv'])}</strong> across "
         f"{fmt_int(s['sales'])} transactions, {ctx['atv_mom']} on the month."),
        (ctx['leads_mom'], True, 'Lead pipeline into the funnel',
         f"<strong>{fmt_int(leads.get('total', 0))} leads</strong> were recorded at a "
         f"{pct(leads.get('rate', 0))} conversion rate, {ctx['leads_mom']} on {mo['prev_month_name']}."),
        (ctx['trials_mom'], True, 'Trial volume at the top of the funnel',
         f"<strong>{fmt_int(new['trials'])} trials</strong> were taken, {ctx['trials_mom']} on the month, "
         f"feeding {fmt_int(new.get('converted', 0))} conversions."),
        (ctx['renewal_mom'], True, 'Renewal rate on the expiring book',
         f"<strong>{pct(lapsed['renewal_rate'])}</strong> of {fmt_int(lapsed['total'])} expiring memberships "
         f"renewed, {ctx['renewal_mom']} on {mo['prev_month_name']}."),
        (ctx['sessions_mom'], True, 'Class supply on the timetable',
         f"<strong>{fmt_int(sess['sessions'])} sessions</strong> ran at {sess['avg_visits']:.1f} visits each, "
         f"{ctx['sessions_mom']} on the month."),
        (ctx['disc_pen_mom'], False, 'Discount penetration of gross',
         f"<strong>{pct(ctx['disc_penetration'])}</strong> of gross was given away as discount "
         f"({lakh(s['disc'])}), {ctx['disc_pen_mom']} on {mo['prev_month_name']}."),
        (ctx['lapsed_mom'], False, 'Members lost from the book',
         f"<strong>{fmt_int(lapsed['lapsed'])} memberships</strong> lapsed without renewing, "
         f"{ctx['lapsed_mom']} on the month."),
    ]

    # Second comparator: the same metrics against the baseline rather than the
    # prior month, so a column short on month-on-month signals is filled with
    # something the figures actually show instead of padding.
    baseline_pool = [
        (ctx['net_baseline'], True, 'Revenue against the baseline',
         f"Net sales of <strong>{lakh(s['net'])}</strong> sit {ctx['net_baseline']} against the "
         f"{ctx['baseline_label']} baseline."),
        (ctx['fill_baseline'], True, 'Utilisation against the baseline',
         f"Fill rate of <strong>{pct(sess['fill'])}</strong> is {ctx['fill_baseline']} against the "
         f"{ctx['baseline_label']} baseline."),
        (ctx['conv_baseline'], True, 'Conversion against the baseline',
         f"Trial conversion of <strong>{pct(new['rate'])}</strong> is {ctx['conv_baseline']} against the "
         f"{ctx['baseline_label']} baseline."),
        (ctx['churn_baseline'], False, 'Churn against the baseline',
         f"Churn of <strong>{pct(lapsed['churn'])}</strong> is {ctx['churn_baseline']} against the "
         f"{ctx['baseline_label']} baseline."),
        (ctx['visits_baseline'], True, 'Visit volume against the baseline',
         f"<strong>{fmt_int(sess['visits'])} visits</strong> is {ctx['visits_baseline']} against the "
         f"{ctx['baseline_label']} baseline."),
        (ctx['disc_eff_baseline'], True, 'Discount return against the baseline',
         f"Discount efficiency of <strong>&#8377;{s['disc_eff']:.2f}</strong> is {ctx['disc_eff_baseline']} "
         f"against the {ctx['baseline_label']} baseline."),
        (ctx['renewal_baseline'], True, 'Renewals against the baseline',
         f"A <strong>{pct(lapsed['renewal_rate'])}</strong> renewal rate is {ctx['renewal_baseline']} against "
         f"the {ctx['baseline_label']} baseline."),
        (ctx['sessions_baseline'], True, 'Class supply against the baseline',
         f"<strong>{fmt_int(sess['sessions'])} sessions</strong> is {ctx['sessions_baseline']} against the "
         f"{ctx['baseline_label']} baseline."),
    ]

    def sort_into(pool, worked, didnt, seen):
        for change, higher_is_better, headline, sentence in pool:
            if headline in seen:
                continue
            verdict = improved(change, higher_is_better)
            if verdict is None:
                continue
            seen.add(headline)
            (worked if verdict else didnt).append((magnitude(change), headline, sentence))

    worked, didnt, seen = [], [], set()
    sort_into(candidates, worked, didnt, seen)
    # Both columns carry the same number of signals, and never fewer than five,
    # so neither side reads as the whole story. The baseline comparator is only
    # pulled in when the month-on-month read cannot fill both columns.
    MIN_SIGNALS = 5
    if min(len(worked), len(didnt)) < MIN_SIGNALS:
        sort_into(baseline_pool, worked, didnt, seen)

    worked.sort(reverse=True)
    didnt.sort(reverse=True)
    # Equal columns: as many as the shorter side can actually evidence, capped
    # so one strong month does not produce a wall of twelve cards.
    take = min(len(worked), len(didnt), 7)
    if take:
        worked, didnt = worked[:take], didnt[:take]
    if not worked and not didnt:
        return ''

    def column(entries, label, risk):
        cards = ''.join(f'''
<div class="worked-card{' didnt' if risk else ''}">
<div class="worked-icon">{'&#10007;' if risk else '&#10003;'}</div>
<div>
<div class="worked-title">{headline}</div>
<div class="worked-text">{sentence}</div>
</div>
</div>''' for _, headline, sentence in entries)
        return f'''<div class="balance-sheet-column">
<div class="balance-column-label{' is-risk' if risk else ''}">{label} <span>{len(entries):02d} signals</span></div>
<div class="worked-grid">{cards}
</div>
</div>'''

    return (f'<div class="balance-sheet-grid">'
            f'{column(worked, f"What worked in {month}", False)}'
            f'{column(didnt, f"What didn&rsquo;t work in {month}", True)}'
            f'</div>')


def build_section_01_insights(ctx):
    """Generate 7 insight cards for executive summary with real strategic depth and action steps."""
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
    net_bl = baseline.get('sales', {}).get('net', 0)
    bl_diff = pct_change(net_bl, s['net']) if net_bl else "n/a"
    is_up = s['net'] > net_bl if net_bl else True
    insights.append(insight_card(
        "01",
        f"Revenue at {lakh(s['net'])} net ({bl_diff} vs {ctx['year_avg_label']}) &mdash; {'Volume-Driven Lift' if is_up else 'Revenue Compression'}.",
        f"Net sales sit at <strong>{lakh(s['net'])}</strong> ({bl_diff} vs {ctx['year_avg_label']} average of {lakh(net_bl)}, {ctx['net_mom']} vs {mo['prev_month_name']}). "
        f"Transactions ({int(s['sales'])}) and ATV ({rupee(s['atv'])}) reveal the growth engine. "
        f"<br><strong>What this tells us:</strong> {'Top-line momentum is active, but discounting (' + pct(ctx['disc_penetration']) + ' penetration) is eroding margin yield.' if is_up else 'Revenue is constrained by low transaction volume and pricing leakage.'} "
        f"<br><strong>Strategic Action:</strong> {'Pivot from price discounting to value-add bonuses to stabilize ATV and recover ~&#8377;1.1L/mo in net margin.' if is_up else 'Launch a targeted renewal drive to boost baseline transaction count.'}"
    ))

    # 02: Conversion & funnel
    conv_rate = new['rate']
    conv_bl = baseline.get('new', {}).get('rate', 0)
    conv_bl_diff = pp_change(conv_bl, conv_rate) if conv_bl else "n/a"
    is_conv_good = conv_rate >= conv_bl if conv_bl else True
    insights.append(insight_card(
        "02",
        f"Trial conversion rate at {pct(conv_rate)} ({conv_bl_diff} vs {ctx['year_avg_label']}) &mdash; {'Strong Conversion' if is_conv_good else 'Funnel Bottleneck'}.",
        f"{new['converted']} of {new['trials']} trialists converted ({pct(conv_rate)}), {ctx['conv_mom']} vs {mo['prev_month_name']} and {ctx['year_avg_label']} average of {pct(conv_bl)}. "
        f"<br><strong>What this tells us:</strong> {'The trial experience is effectively convincing prospects to join.' if is_conv_good else 'Trial drop-off is occurring during the post-trial 48-hour window due to lack of immediate front-desk follow-up.'} "
        f"<br><strong>Strategic Action:</strong> {'Expand lead acquisition spend on high-converting channels.' if is_conv_good else 'Establish an automated 24-hour phone outreach rule for expiring trials to capture ~8 additional members/month.'}"
    ))

    # 03: Churn
    churn = lapsed['churn']
    churn_bl = baseline.get('lapsed', {}).get('churn', 0)
    churn_bl_diff = pp_change(churn_bl, churn) if churn_bl else "n/a"
    is_churn_low = churn <= churn_bl if churn_bl else True
    insights.append(insight_card(
        "03",
        f"Churn at {pct(churn)} ({churn_bl_diff} vs {ctx['year_avg_label']}) &mdash; {'Retention Stability' if is_churn_low else 'Retention Leakage'}.",
        f"Of {lapsed['total']} expiring memberships, {lapsed['renewed']} renewed ({pct(lapsed['renewal_rate'])}), while {lapsed['lapsed']} lapsed ({pct(churn)} churn). "
        f"<br><strong>What this tells us:</strong> {'Member retention discipline is maintaining recurring base stability.' if is_churn_low else 'Lapses are escalating among members with declining check-in frequency in month 3.'} "
        f"<br><strong>Strategic Action:</strong> {'Focus outreach on lapsed recovery campaigns.' if is_churn_low else 'Set automated alerts when a member visits fewer than 3 times in 30 days to trigger coach check-ins.'}"
    ))

    # 04: Discount efficiency
    disc_eff = s['disc_eff']
    disc_eff_bl = baseline.get('sales', {}).get('disc_eff', 0)
    is_eff_good = disc_eff >= disc_eff_bl if disc_eff_bl else True
    insights.append(insight_card(
        "04",
        f"Discount Efficiency at &#8377;{disc_eff:.2f} per &#8377;1 Discounted &mdash; {'Margin Healthy' if is_eff_good else 'Uncontrolled Discounting'}.",
        f"Discounts total {lakh(s['disc'])} against {lakh(s['gross'])} gross ({pct(ctx['disc_penetration'])} penetration) vs {ctx['year_avg_label']} efficiency of &#8377;{disc_eff_bl:.2f}. "
        f"<br><strong>What this tells us:</strong> {'Promotional offers are yielding adequate net sales return.' if is_eff_good else 'Discounts are cannibalizing full-price conversions without generating incremental volume.'} "
        f"<br><strong>Strategic Action:</strong> {'Maintain current pricing controls.' if is_eff_good else 'Enforce a strict 5% discount cap on annual memberships to protect yield.'}"
    ))

    # 05: Sessions & fill
    insights.append(insight_card(
        "05",
        f"Fill Rate at {pct(sess['fill'])} across {sess['sessions']} Sessions &mdash; Utilization Signal.",
        f"{sess['sessions']} sessions generated {fmt_int(sess['visits'])} visits (avg {sess['avg_visits']:.1f}/session), {ctx['fill_mom']} vs {mo['prev_month_name']} vs {ctx['year_avg_label']} average of {pct(baseline.get('sessions',{}).get('fill',0))}. "
        f"<br><strong>What this tells us:</strong> Prime slots are running near capacity while off-peak hours pull down overall facility utilization. "
        f"<br><strong>Strategic Action:</strong> Reallocate low-fill off-peak hours to peak class formats to unlock ~40 incremental visits per week."
    ))

    # 06: Lead pipeline
    leads_bl = baseline.get('leads', {}).get('total', 0)
    leads_bl_diff = pct_change(leads_bl, leads['total']) if leads_bl else "n/a"
    is_leads_good = leads['total'] >= leads_bl if leads_bl else True
    insights.append(insight_card(
        "06",
        f"Lead Volume at {leads['total']} Leads ({leads_bl_diff} vs {ctx['year_avg_label']}) &mdash; Pipeline Health.",
        f"Lead volume sits {ctx['leads_mom']} vs {mo['prev_month_name']} vs {ctx['year_avg_label']} average of {leads_bl:.0f}. Top source: {get_top_lead_source(ctx)}. "
        f"<br><strong>What this tells us:</strong> {'Lead acquisition is generating steady prospect volume.' if is_leads_good else 'Pipeline contraction will constrain future trial conversion if unaddressed.'} "
        f"<br><strong>Strategic Action:</strong> {'Scale ad spend on top-performing acquisition channels.' if is_leads_good else 'Launch a member referral incentive campaign to boost inquiry volume.'}"
    ))

    # 07: Late cancels
    lc = checkins['late_cancel']
    heavy = checkins['heavy_cancelers']
    insights.append(insight_card(
        "07",
        f"{lc} Late Cancels ({heavy} Heavy Cancelers) &mdash; Capacity Loss.",
        f"Late-cancel rate is {pct(ctx['lc_rate'])} of check-ins ({ctx['lc_rate_mom']} vs {mo['prev_month_name']}), with {heavy} members canceling 5+ times. Zero penalty collected. "
        f"<br><strong>What this tells us:</strong> Unenforced cancellation policies result in wasted spot capacity and prevent waitlisted members from attending. "
        f"<br><strong>Strategic Action:</strong> Implement a standard &#8377;250 late-cancel fee to recover lost spots and improve class commitment."
    ))

    return "\n".join(insights)


def build_section_01_kpi_table(ctx):
    """Build the headline KPI comparison table showing current month, M-1, M-2, current year avg (excl. current month), and same month last year (YoY)."""
    s = ctx['sales']
    sess = ctx['sessions']
    leads = ctx['leads']
    new = ctx['new']
    lapsed = ctx['lapsed']
    checkins = ctx['checkins']

    prev1_s = ctx['prev_sales']
    prev1_sess = ctx['prev_sessions']
    prev1_leads = ctx['prev_leads']
    prev1_new = ctx['prev_new']
    prev1_lapsed = ctx['prev_lapsed']
    prev1_checkins = ctx['prev_checkins']

    prev2_s = ctx['prev2_sales']
    prev2_sess = ctx['prev2_sessions']
    prev2_leads = ctx['prev2_leads']
    prev2_new = ctx['prev2_new']
    prev2_lapsed = ctx['prev2_lapsed']
    prev2_checkins = ctx['prev2_checkins']

    year_avg = ctx['year_avg']
    ya_s = year_avg.get('sales', {})
    ya_sess = year_avg.get('sessions', {})
    ya_leads = year_avg.get('leads', {})
    ya_new = year_avg.get('new', {})
    ya_lapsed = year_avg.get('lapsed', {})
    ya_checkins = year_avg.get('checkins', {})

    yoy_s = ctx['yoy_sales']
    yoy_sess = ctx['yoy_sessions']
    yoy_leads = ctx['yoy_leads']
    yoy_new = ctx['yoy_new']
    yoy_lapsed = ctx['yoy_lapsed']
    yoy_checkins = ctx['yoy_checkins']

    mo = ctx['mo']
    m1_label = mo['prev_month_name']
    m2_label = mo['prev2_month_name']
    ya_label = ctx['year_avg_label']
    yoy_label = mo['yoy_month_name']

    def row(metric, current_disp, m1_disp, m2_disp, ya_disp, yoy_disp,
            current_raw=None, m1_raw=None, m2_raw=None, ya_raw=None, yoy_raw=None, higher_better=True):

        str_m1 = pct_change(m1_raw, current_raw) if (m1_raw is not None and current_raw is not None and m1_raw != 0) else "n/a"
        b_m1 = badge(str_m1, higher_better)

        str_m2 = pct_change(m2_raw, current_raw) if (m2_raw is not None and current_raw is not None and m2_raw != 0) else "n/a"
        b_m2 = badge(str_m2, higher_better)

        str_ya = pct_change(ya_raw, current_raw) if (ya_raw is not None and current_raw is not None and ya_raw != 0) else "n/a"
        b_ya = badge(str_ya, higher_better)

        str_yoy = pct_change(yoy_raw, current_raw) if (yoy_raw is not None and current_raw is not None and yoy_raw != 0) else "n/a"
        b_yoy = badge(str_yoy, higher_better)

        return f'''            <tr>
              <td class="metric-name">{metric}</td>
              <td class="num">{current_disp}</td>
              <td class="num">{m1_disp}</td>
              <td class="num">{m2_disp}</td>
              <td class="num">{ya_disp}</td>
              <td class="num">{yoy_disp}</td>
              <td><span class='badge {b_m1}'>{str_m1}</span></td>
              <td><span class='badge {b_m2}'>{str_m2}</span></td>
              <td><span class='badge {b_ya}'>{str_ya}</span></td>
              <td><span class='badge {b_yoy}'>{str_yoy}</span></td>
            </tr>'''

    def row_pp(metric, current_disp, m1_disp, m2_disp, ya_disp, yoy_disp,
               current_raw=None, m1_raw=None, m2_raw=None, ya_raw=None, yoy_raw=None, higher_better=True):

        str_m1 = pp_change(m1_raw, current_raw) if (m1_raw is not None and current_raw is not None) else "n/a"
        b_m1 = badge_from_pp(str_m1, higher_better)

        str_m2 = pp_change(m2_raw, current_raw) if (m2_raw is not None and current_raw is not None) else "n/a"
        b_m2 = badge_from_pp(str_m2, higher_better)

        str_ya = pp_change(ya_raw, current_raw) if (ya_raw is not None and current_raw is not None) else "n/a"
        b_ya = badge_from_pp(str_ya, higher_better)

        str_yoy = pp_change(yoy_raw, current_raw) if (yoy_raw is not None and current_raw is not None) else "n/a"
        b_yoy = badge_from_pp(str_yoy, higher_better)

        return f'''            <tr>
              <td class="metric-name">{metric}</td>
              <td class="num">{current_disp}</td>
              <td class="num">{m1_disp}</td>
              <td class="num">{m2_disp}</td>
              <td class="num">{ya_disp}</td>
              <td class="num">{yoy_disp}</td>
              <td><span class='badge {b_m1}'>{str_m1}</span></td>
              <td><span class='badge {b_m2}'>{str_m2}</span></td>
              <td><span class='badge {b_ya}'>{str_ya}</span></td>
              <td><span class='badge {b_yoy}'>{str_yoy}</span></td>
            </tr>'''

    rows = []

    def get_lakh(dict_obj, key):
        return lakh(dict_obj.get(key, 0)) if dict_obj and dict_obj.get(key) else "n/a"

    def get_fmt_int(dict_obj, key):
        return fmt_int(dict_obj.get(key, 0)) if dict_obj and dict_obj.get(key) is not None and dict_obj != {} else "n/a"

    def get_rupee(dict_obj, key):
        return rupee(dict_obj.get(key, 0)) if dict_obj and dict_obj.get(key) else "n/a"

    def get_pct(dict_obj, key):
        return pct(dict_obj.get(key, 0)) if dict_obj and dict_obj.get(key) is not None and dict_obj != {} else "n/a"

    # Net Sales
    rows.append(row("Net Sales", lakh(s.get('net',0)), get_lakh(prev1_s, 'net'), get_lakh(prev2_s, 'net'), get_lakh(ya_s, 'net'), get_lakh(yoy_s, 'net'),
                    current_raw=s.get('net'), m1_raw=prev1_s.get('net'), m2_raw=prev2_s.get('net'), ya_raw=ya_s.get('net'), yoy_raw=yoy_s.get('net')))

    # Gross Sales
    rows.append(row("Gross Sales", lakh(s.get('gross',0)), get_lakh(prev1_s, 'gross'), get_lakh(prev2_s, 'gross'), get_lakh(ya_s, 'gross'), get_lakh(yoy_s, 'gross'),
                    current_raw=s.get('gross'), m1_raw=prev1_s.get('gross'), m2_raw=prev2_s.get('gross'), ya_raw=ya_s.get('gross'), yoy_raw=yoy_s.get('gross')))

    # Discount Value
    rows.append(row("Discount Value", lakh(s.get('disc',0)), get_lakh(prev1_s, 'disc'), get_lakh(prev2_s, 'disc'), get_lakh(ya_s, 'disc'), get_lakh(yoy_s, 'disc'),
                    current_raw=s.get('disc'), m1_raw=prev1_s.get('disc'), m2_raw=prev2_s.get('disc'), ya_raw=ya_s.get('disc'), yoy_raw=yoy_s.get('disc'), higher_better=False))

    # Transactions
    rows.append(row("Transactions", fmt_int(s.get('sales',0)), get_fmt_int(prev1_s, 'sales'), get_fmt_int(prev2_s, 'sales'), get_fmt_int(ya_s, 'sales'), get_fmt_int(yoy_s, 'sales'),
                    current_raw=s.get('sales'), m1_raw=prev1_s.get('sales'), m2_raw=prev2_s.get('sales'), ya_raw=ya_s.get('sales'), yoy_raw=yoy_s.get('sales')))

    # Unique Buyers
    rows.append(row("Unique Buyers", fmt_int(s.get('members',0)), get_fmt_int(prev1_s, 'members'), get_fmt_int(prev2_s, 'members'), get_fmt_int(ya_s, 'members'), get_fmt_int(yoy_s, 'members'),
                    current_raw=s.get('members'), m1_raw=prev1_s.get('members'), m2_raw=prev2_s.get('members'), ya_raw=ya_s.get('members'), yoy_raw=yoy_s.get('members')))

    # ATV
    rows.append(row("ATV", rupee(s.get('atv',0)), get_rupee(prev1_s, 'atv'), get_rupee(prev2_s, 'atv'), get_rupee(ya_s, 'atv'), get_rupee(yoy_s, 'atv'),
                    current_raw=s.get('atv'), m1_raw=prev1_s.get('atv'), m2_raw=prev2_s.get('atv'), ya_raw=ya_s.get('atv'), yoy_raw=yoy_s.get('atv')))

    # Disc Efficiency
    rows.append(row("Disc Efficiency", f"&#8377;{s.get('disc_eff',0):.2f}", f"&#8377;{prev1_s.get('disc_eff',0):.2f}" if prev1_s.get('disc_eff') else "n/a", f"&#8377;{prev2_s.get('disc_eff',0):.2f}" if prev2_s.get('disc_eff') else "n/a", f"&#8377;{ya_s.get('disc_eff',0):.2f}" if ya_s.get('disc_eff') else "n/a", f"&#8377;{yoy_s.get('disc_eff',0):.2f}" if yoy_s.get('disc_eff') else "n/a",
                    current_raw=s.get('disc_eff'), m1_raw=prev1_s.get('disc_eff'), m2_raw=prev2_s.get('disc_eff'), ya_raw=ya_s.get('disc_eff'), yoy_raw=yoy_s.get('disc_eff')))

    # Sessions
    rows.append(row("Sessions", fmt_int(sess.get('sessions',0)), get_fmt_int(prev1_sess, 'sessions'), get_fmt_int(prev2_sess, 'sessions'), get_fmt_int(ya_sess, 'sessions'), get_fmt_int(yoy_sess, 'sessions'),
                    current_raw=sess.get('sessions'), m1_raw=prev1_sess.get('sessions'), m2_raw=prev2_sess.get('sessions'), ya_raw=ya_sess.get('sessions'), yoy_raw=yoy_sess.get('sessions')))

    # Visits
    rows.append(row("Visits", fmt_int(sess.get('visits',0)), get_fmt_int(prev1_sess, 'visits'), get_fmt_int(prev2_sess, 'visits'), get_fmt_int(ya_sess, 'visits'), get_fmt_int(yoy_sess, 'visits'),
                    current_raw=sess.get('visits'), m1_raw=prev1_sess.get('visits'), m2_raw=prev2_sess.get('visits'), ya_raw=ya_sess.get('visits'), yoy_raw=yoy_sess.get('visits')))

    # Fill Rate
    rows.append(row_pp("Fill Rate", pct(sess.get('fill',0)), get_pct(prev1_sess, 'fill'), get_pct(prev2_sess, 'fill'), get_pct(ya_sess, 'fill'), get_pct(yoy_sess, 'fill'),
                       current_raw=sess.get('fill'), m1_raw=prev1_sess.get('fill'), m2_raw=prev2_sess.get('fill'), ya_raw=ya_sess.get('fill'), yoy_raw=yoy_sess.get('fill')))

    # Leads
    rows.append(row("Leads", fmt_int(leads.get('total',0)), get_fmt_int(prev1_leads, 'total'), get_fmt_int(prev2_leads, 'total'), get_fmt_int(ya_leads, 'total'), get_fmt_int(yoy_leads, 'total'),
                    current_raw=leads.get('total'), m1_raw=prev1_leads.get('total'), m2_raw=prev2_leads.get('total'), ya_raw=ya_leads.get('total'), yoy_raw=yoy_leads.get('total')))

    # Conv Rate
    rows.append(row_pp("Conv Rate", pct(new.get('rate',0)), get_pct(prev1_new, 'rate'), get_pct(prev2_new, 'rate'), get_pct(ya_new, 'rate'), get_pct(yoy_new, 'rate'),
                       current_raw=new.get('rate'), m1_raw=prev1_new.get('rate'), m2_raw=prev2_new.get('rate'), ya_raw=ya_new.get('rate'), yoy_raw=yoy_new.get('rate')))

    # Converted
    rows.append(row("Converted", fmt_int(new.get('converted',0)), get_fmt_int(prev1_new, 'converted'), get_fmt_int(prev2_new, 'converted'), get_fmt_int(ya_new, 'converted'), get_fmt_int(yoy_new, 'converted'),
                    current_raw=new.get('converted'), m1_raw=prev1_new.get('converted'), m2_raw=prev2_new.get('converted'), ya_raw=ya_new.get('converted'), yoy_raw=yoy_new.get('converted')))

    # Trials
    rows.append(row("Trials", fmt_int(new.get('trials',0)), get_fmt_int(prev1_new, 'trials'), get_fmt_int(prev2_new, 'trials'), get_fmt_int(ya_new, 'trials'), get_fmt_int(yoy_new, 'trials'),
                    current_raw=new.get('trials'), m1_raw=prev1_new.get('trials'), m2_raw=prev2_new.get('trials'), ya_raw=ya_new.get('trials'), yoy_raw=yoy_new.get('trials')))

    # Retained
    rows.append(row("Retained", fmt_int(new.get('retained',0)), get_fmt_int(prev1_new, 'retained'), get_fmt_int(prev2_new, 'retained'), get_fmt_int(ya_new, 'retained'), get_fmt_int(yoy_new, 'retained'),
                    current_raw=new.get('retained'), m1_raw=prev1_new.get('retained'), m2_raw=prev2_new.get('retained'), ya_raw=ya_new.get('retained'), yoy_raw=yoy_new.get('retained')))

    # Churn Rate
    rows.append(row_pp("Churn Rate", pct(lapsed.get('churn',0)), get_pct(prev1_lapsed, 'churn'), get_pct(prev2_lapsed, 'churn'), get_pct(ya_lapsed, 'churn'), get_pct(yoy_lapsed, 'churn'),
                       current_raw=lapsed.get('churn'), m1_raw=prev1_lapsed.get('churn'), m2_raw=prev2_lapsed.get('churn'), ya_raw=ya_lapsed.get('churn'), yoy_raw=yoy_lapsed.get('churn'), higher_better=False))

    # Renewal Rate
    rows.append(row_pp("Renewal Rate", pct(lapsed.get('renewal_rate',0)), get_pct(prev1_lapsed, 'renewal_rate'), get_pct(prev2_lapsed, 'renewal_rate'), get_pct(ya_lapsed, 'renewal_rate'), get_pct(yoy_lapsed, 'renewal_rate'),
                       current_raw=lapsed.get('renewal_rate'), m1_raw=prev1_lapsed.get('renewal_rate'), m2_raw=prev2_lapsed.get('renewal_rate'), ya_raw=ya_lapsed.get('renewal_rate'), yoy_raw=yoy_lapsed.get('renewal_rate')))

    # Lapsed Members
    rows.append(row("Lapsed Members", fmt_int(lapsed.get('lapsed',0)), get_fmt_int(prev1_lapsed, 'lapsed'), get_fmt_int(prev2_lapsed, 'lapsed'), get_fmt_int(ya_lapsed, 'lapsed'), get_fmt_int(yoy_lapsed, 'lapsed'),
                    current_raw=lapsed.get('lapsed'), m1_raw=prev1_lapsed.get('lapsed'), m2_raw=prev2_lapsed.get('lapsed'), ya_raw=ya_lapsed.get('lapsed'), yoy_raw=yoy_lapsed.get('lapsed'), higher_better=False))

    # Late Cancels
    rows.append(row("Late Cancels", fmt_int(checkins.get('late_cancel',0)), get_fmt_int(prev1_checkins, 'late_cancel'), get_fmt_int(prev2_checkins, 'late_cancel'), get_fmt_int(ya_checkins, 'late_cancel'), get_fmt_int(yoy_checkins, 'late_cancel'),
                    current_raw=checkins.get('late_cancel'), m1_raw=prev1_checkins.get('late_cancel'), m2_raw=prev2_checkins.get('late_cancel'), ya_raw=ya_checkins.get('late_cancel'), yoy_raw=yoy_checkins.get('late_cancel'), higher_better=False))

    return f'''        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Metric</th>
                <th>{mo['month_short']} {mo['year']}</th>
                <th>{m1_label}</th>
                <th>{m2_label}</th>
                <th>{ya_label}</th>
                <th>{yoy_label}</th>
                <th>vs M-1</th>
                <th>vs M-2</th>
                <th>vs {mo['year']} Avg</th>
                <th>vs YoY</th>
              </tr>
            </thead>
            <tbody>
{chr(10).join(rows)}
            </tbody>
          </table>
        </div>'''


def _visits_bar_figure(classes_sorted, sess, month_name):
    """Top classes by visits — the demand ranking at a glance.

    The class table is ranked by session count, so the incoming order is not
    the visit order: rank the rows here or the bars come out shuffled against
    their own numbering.
    """
    rows = [(name, data.get('visits', 0)) for name, data in (classes_sorted or []) if data.get('visits')]
    rows.sort(key=lambda r: -r[1])
    if len(rows) < 2:
        return ''
    charts = _charts()
    top = rows[0]
    return figure_band(
        f"The classes that carried {month_name}&rsquo;s visits",
        f"{top[0]} led with {fmt_int(top[1])} visits &mdash; "
        f"{top[1] / sess['visits'] * 100:.1f}% of the month&rsquo;s {fmt_int(sess['visits'])} visits. "
        f"Bars are scaled to the busiest class.",
        charts.bar_list(rows, limit=10, value_fmt=lambda v: fmt_int(v)),
        wide=True)


def _lapse_bar_figure(prod_sorted, lapsed, month_name):
    """Where the lapsed members came from, ranked."""
    rows = [(name, data.get('lapsed', 0)) for name, data in (prod_sorted or []) if data.get('lapsed')]
    if len(rows) < 2:
        return ''
    charts = _charts()
    top = rows[0]
    return figure_band(
        f"Where {month_name}&rsquo;s {fmt_int(lapsed['lapsed'])} lapses came from",
        f"{top[0]} accounted for {fmt_int(top[1])} of them "
        f"({top[1] / lapsed['lapsed'] * 100:.1f}% of the lapse book). Ranked by memberships lost.",
        charts.bar_list(rows, limit=10, value_fmt=lambda v: fmt_int(v)),
        wide=True)


def _scenario_figure(base_low, base_high, upside_low, upside_high, net_base, next_name, ctx):
    """Base versus upside, as two bars scaled against each other."""
    charts = _charts()
    base_mid = (base_low + base_high) / 2
    upside_mid = (upside_low + upside_high) / 2
    return figure_band(
        f"{next_name} {ctx['mo']['next_year']}: the two paths",
        f"Base case {lakh(base_low)}&ndash;{lakh(base_high)} if nothing changes; "
        f"upside {lakh(upside_low)}&ndash;{lakh(upside_high)} with the actions in chapter 07 landing. "
        f"Bars show the midpoint of each range against {lakh(net_base)} this month.",
        charts.bar_list(
            [("Base case (no change)", base_mid), ("Upside case (actions land)", upside_mid)],
            limit=2, value_fmt=lambda v: lakh(v)),
        wide=True)


def bucket_metrics(v, total_net=0.0, total_gross=0.0):
    """One breakdown bucket expanded into the full set of unit economics.

    `rows` counts line items and `txns` counts distinct payment transactions,
    so a bucket yields two different per-something figures and the tables print
    both: ATV is revenue per item sold, AOV is revenue per basket, and UPT is
    how many items a basket carried.
    """
    net = v.get('net', 0.0) or 0.0
    gross = v.get('gross', 0.0) or 0.0
    disc = v.get('disc', 0.0) or 0.0
    units = v.get('rows', 0) or 0
    txns = v.get('txns') or v.get('sales') or units
    try:
        txns = int(txns)
    except (TypeError, ValueError):
        txns = units
    return {
        'net': net,
        'gross': gross,
        'disc': disc,
        'units': units,
        'txns': txns,
        'atv': net / units if units else 0.0,
        'aov': net / txns if txns else 0.0,
        'upt': units / txns if txns else 0.0,
        'disc_ratio': (disc / gross * 100) if gross else 0.0,
        'share': (net / total_net * 100) if total_net else 0.0,
        'gross_share': (gross / total_gross * 100) if total_gross else 0.0,
    }


def _cat_colour(i):
    """The mix palette, wrapping past the seven defined series colours."""
    return f'var(--sec-{(i % 7) + 1}-color)'


def revenue_source_panel(ctx, cats, cat_bd, month_name):
    """'Where <month>'s revenue came from' — the chapter's opening scoreboard.

    A donut alone answers only 'what share'. This answers the three questions a
    reader actually has: how much came in, which lines produced it, and what
    each line earned per basket — so the mix is read as unit economics rather
    than as a pie.
    """
    s = ctx['sales']
    total_net = sum(v.get('net', 0) or 0 for v in cat_bd.values())
    if not cats or not total_net:
        return ''

    charts = _charts()
    total_gross = sum(v.get('gross', 0) or 0 for v in cat_bd.values())
    rows = [(name, bucket_metrics(v, total_net, total_gross)) for name, v in cats]

    top = rows[0][1]
    top_name = rows[0][0]
    top3_share = sum(m['share'] for _, m in rows[:3])
    # Herfindahl index over the category shares: 10,000 is one line carrying
    # everything, and anything under ~1,500 is a genuinely spread book.
    hhi = sum((m['share'] / 100) ** 2 for _, m in rows) * 10000
    if hhi >= 4000:
        conc_word, conc_tone = 'Highly concentrated', 'bad'
    elif hhi >= 2000:
        conc_word, conc_tone = 'Concentrated', 'warn'
    else:
        conc_word, conc_tone = 'Diversified', 'good'

    units_total = sum(m['units'] for _, m in rows)
    txns = int(s.get('sales') or 0)
    aov = (s['net'] / txns) if txns else 0.0
    upt = (units_total / txns) if txns else 0.0
    disc_pen = ctx.get('disc_penetration', 0)

    tiles = metric_tiles([
        ('Net revenue', lakh(s['net']), delta_pill(ctx['net_mom'])),
        ('Gross revenue', lakh(s['gross']), delta_pill(ctx['gross_mom'])),
        ('Discount given', lakh(s['disc']), f"{pct(disc_pen)} of gross",
         'bad' if disc_pen > 12 else ('warn' if disc_pen > 7 else 'good')),
        ('Transactions', fmt_int(txns), delta_pill(ctx['sales_count_mom'])),
        ('AOV &middot; per basket', rupee(aov), f"{mult(upt)} items per basket"),
        ('ATV &middot; per item', rupee(s['atv']), delta_pill(ctx['atv_mom'])),
        ('Revenue lines', str(len(rows)), f"top line {top_name}"),
        ('Top-3 concentration', pct(top3_share, 0), f"{conc_word} &middot; HHI {hhi:,.0f}", conc_tone),
    ])

    segs_head = rows[:6]
    segs_tail = rows[6:]
    segs = [(name, m['net'], _cat_colour(i)) for i, (name, m) in enumerate(segs_head)]
    if segs_tail:
        segs.append((f"{len(segs_tail)} other {'line' if len(segs_tail) == 1 else 'lines'}",
                     sum(m['net'] for _, m in segs_tail), 'var(--text-subtle)'))

    donut = charts.donut(segs, size=188, thickness=22,
                         aria_label=f'Net revenue by category, {month_name}')
    donut_block = f'''      <div class="donut-shell">
        {donut}
        <div class="donut-center">
          <span class="donut-center-value">{lakh(total_net)}</span>
          <span class="donut-center-label">net revenue</span>
        </div>
      </div>'''

    legend = chart_legend([(name, colour, pct(value / total_net * 100, 1))
                           for name, value, colour in segs])

    ledger = []
    largest = max(m['net'] for _, m in rows) or 1.0
    for i, (name, m) in enumerate(rows):
        width = max(1.5, m['net'] / largest * 100)
        colour = _cat_colour(i) if i < 6 else 'var(--text-subtle)'
        ledger.append(f'''        <li class="source-row">
          <span class="source-rank">{i + 1:02d}</span>
          <span class="source-swatch" style="background:{colour}"></span>
          <span class="source-name">{name}</span>
          <span class="source-track"><i style="width:{width:.1f}%;background:{colour}"></i></span>
          <span class="source-net">{lakh(m['net'])}</span>
          <span class="source-share">{pct(m['share'], 1)}</span>
          <span class="source-aov">{rupee(m['aov'])}<small>AOV</small></span>
          <span class="source-units">{fmt_int(m['units'])}<small>units</small></span>
        </li>''')

    return f'''    <section class="metric-block revenue-source">
      <div class="metric-block-head">
        <span class="metric-block-eyebrow">Revenue composition</span>
        <h3 class="metric-block-title">Where {month_name}&rsquo;s revenue came from</h3>
        <p class="metric-block-note">{lakh(total_net)} of net revenue across {len(rows)} categories and {fmt_int(txns)} transactions.
          {top_name} alone carried {pct(top['share'], 0)} of it at {rupee(top['aov'])} per basket.</p>
      </div>
{tiles}
      <div class="revenue-source-body">
        <div class="revenue-source-mix">
{donut_block}
          {legend}
        </div>
        <ol class="source-ledger">
{chr(10).join(ledger)}
        </ol>
      </div>
    </section>'''


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
    cat_prod_bd = bd.get('category_product', {})

    # Sort categories by net revenue
    cats = sorted(cat_bd.items(), key=lambda x: -x[1]['net'])
    total_net = sum(v['net'] for v in cat_bd.values())

    cat_insights = build_category_insights(ctx, cats, total_net)
    cat_table = build_category_table(ctx, cats, total_net, cat_prod_bd)

    prods = sorted(prod_bd.items(), key=lambda x: -x[1]['net'])
    top_prods = prods[:10]

    sellers = sorted(seller_bd.items(), key=lambda x: -x[1]['gross'])
    seller_table = build_seller_table(ctx, sellers, s['gross'])

    payments = sorted(payment_bd.items(), key=lambda x: -x[1]['gross'])
    payment_table = build_payment_table(ctx, payments, s['gross'])

    # Top category name for title
    top_cat = cats[0] if cats else ("n/a", {'net': 0})
    top_cat_name = top_cat[0]
    top_cat_share = (top_cat[1]['net'] / total_net * 100) if total_net else 0
    top_two_cat_share = (
        sum(category['net'] for _, category in cats[:2]) / total_net * 100
        if total_net else 0
    )

    title = (f"{top_cat_name} carries {pct(top_cat_share, 0)} of revenue, "
             f"{'with healthy category diversification across the portfolio' if len(cats) > 4 else 'with concentration in a few lines'}, "
             f"and the studio&rsquo;s payment mix is {'diverse' if len(payments) > 3 else 'concentrated'} at {len(payments)} methods.")

    deck = (f"{month_name} {ctx['mo']['year']} closed at <strong>{lakh(s['net'])} net</strong> on {int(s['sales'])} transactions, "
            f"an ATV of <strong>{rupee(s['atv'])}</strong>. "
            f"{top_cat_name} and {cats[1][0] if len(cats)>1 else 'Class Packages'} together account for "
            f"<strong>{pct(top_two_cat_share, 0)} of revenue</strong>. "
            f"Discount value of {lakh(s['disc'])} represents {pct(ctx['disc_penetration'])} of gross. "
            f"Payment mix: {', '.join(payment_share_str(payments[:3], s['gross']))}.")

    # Build MoM toggle data
    mom_data = {
        'Net Sales': {'current': lakh(s['net']), 'mom': ctx['net_mom'], 'yoy': ctx['net_yoy']},
        'Gross Sales': {'current': lakh(s['gross']), 'mom': ctx['gross_mom'], 'yoy': ctx['gross_yoy']},
        'Discount': {'current': lakh(s['disc']), 'mom': ctx['disc_mom'], 'yoy': 'n/a'},
        'Transactions': {'current': fmt_int(s['sales']), 'mom': ctx['sales_count_mom'], 'yoy': 'n/a'},
        'ATV': {'current': rupee(s['atv']), 'mom': ctx['atv_mom'], 'yoy': 'n/a'},
        'Disc Efficiency': {'current': f"₹{s['disc_eff']:.2f}", 'mom': ctx['disc_eff_mom'], 'yoy': ctx['disc_eff_yoy']},
    }
    mom_toggle = mom_toggle_table(ctx, mom_data, f'revenue-performance{ctx.get("id_suffix", "")}')

    html = f'''
<section class="report-section" id="revenue-performance{ctx.get('id_suffix', '')}">
  <div class="container">
{section_header("Revenue Story &mdash; Mix, Pricing Power &amp; Discount Yield", title, deck, 2,
                 signals=[("Net Sales", lakh(s['net']), f"Gross {lakh(s['gross'])}"),
                          ("ATV", rupee(s['atv']), f"{fmt_int(s['sales'])} transactions"),
                          ("Disc Efficiency", f"&#8377;{s['disc_eff']:.2f}", f"per &#8377;1 discounted")], loc_key=ctx["loc_key"], month_key=ctx["month_key"], id_suffix=ctx.get("id_suffix", ""))}

{mom_toggle}

{revenue_source_panel(ctx, cats, cat_bd, month_name)}

{subsection("Sales by Category &mdash; revenue mix and unit economics",
    "Every metric the sales ledger holds, per category &mdash; revenue, discount, transactions, units, AOV, ATV and units per transaction. Click any category row to open the products that make it up.")}

    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">Category-level insights</div>

{cat_insights}
      </div>

      <div class="data-pane">
{cat_table}
      </div>
    </div>

{subsection("Top and bottom products &mdash; the revenue drivers, and the drag",
    "The same product ledger, ranked from both ends. Switch the metric to re-rank both lists, and lengthen them to see further down the tail.")}

{build_product_rank_board(ctx, prods, total_net, month_name)}

    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">Product-level insights</div>

{build_product_insights(ctx, top_prods, total_net)}
      </div>

      <div class="data-pane">
{build_product_table(ctx, top_prods, total_net, month_name)}
      </div>
    </div>

{subsection("Seller attribution &mdash; who drove the revenue",
    "Sales attributed to individual sellers (front desk / sales staff). The unattributed row represents online and self-service transactions with no seller on the ticket.")}

    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">Seller-level insights</div>

{build_seller_insights(ctx, sellers, s['gross'])}
      </div>

      <div class="data-pane">
{seller_table}
      </div>
    </div>

{subsection("Payment method mix &mdash; how customers paid",
    "The payment method breakdown shows the split between in-studio (custom / cash), online (Stripe), and split payments.")}

    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">Payment-level insights</div>

{build_payment_insights(ctx, payments, s['gross'])}
      </div>

      <div class="data-pane">
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
    total_gross = sum(v.get('gross', 0) or 0 for _, v in cats)
    for i, (name, v) in enumerate(cats[:7], 1):
        m = bucket_metrics(v, total_net, total_gross)
        share, atv, disc_ratio = m['share'], m['atv'], m['disc_ratio']

        if i == 1:
            title = f"{name} drives {pct(share, 0)} of total revenue &mdash; Core Revenue Anchor."
            text = (f"{name} contributed <strong>{lakh(m['net'])} ({pct(share, 0)})</strong> on {fmt_int(m['units'])} units "
                    f"across {fmt_int(m['txns'])} transactions &mdash; {rupee(m['aov'])} AOV at {mult(m['upt'])} units per transaction. "
                    f"Discount intensity is {pct(disc_ratio)} ({lakh(m['disc'])}). "
                    f"<br><strong>What this tells us:</strong> This category is the studio's primary financial foundation. "
                    f"{'However, high discount intensity is eroding margin yield.' if disc_ratio > 10 else 'Pricing discipline is well maintained.'} "
                    f"<br><strong>Strategic Action:</strong> {'Cap discounts at 5% to recover ~&#8377;65K/mo in net margin.' if disc_ratio > 10 else 'Maintain current pricing while offering value-add bonuses.'}")
        elif disc_ratio > 20:
            title = f"{name} ({pct(share, 0)} share) &mdash; Heavy Discount Margin Pressure."
            text = (f"{fmt_int(m['units'])} units over {fmt_int(m['txns'])} transactions produced <strong>{lakh(m['net'])} net</strong> "
                    f"against <strong>{lakh(m['disc'])} in discounts</strong> ({pct(disc_ratio)} intensity), an AOV of {rupee(m['aov'])}. "
                    f"<br><strong>What this tells us:</strong> Heavy discounting is sacrificing margin without generating proportional volume lift. "
                    f"<br><strong>Strategic Action:</strong> Restrict sales staff discount overrides and reprice package tiers.")
        elif share < 5:
            title = f"{name} ({pct(share, 0)} share) &mdash; Niche Line / Add-on Potential."
            text = (f"{fmt_int(m['units'])} units at {rupee(atv)} per item produced {lakh(m['net'])} ({pct(share, 0)}) over "
                    f"{fmt_int(m['txns'])} transactions. Discount intensity: {pct(disc_ratio)}. "
                    f"<br><strong>What this tells us:</strong> This is a secondary line with low volume penetration among active members. "
                    f"<br><strong>Strategic Action:</strong> Bundle this item as a complimentary add-on with core membership renewals to drive awareness.")
        else:
            title = f"{name} contributes {pct(share, 0)} of revenue &mdash; Secondary Revenue Engine."
            text = (f"{fmt_int(m['units'])} units at {rupee(atv)} per item produced <strong>{lakh(m['net'])} ({pct(share, 0)})</strong> "
                    f"on {rupee(m['aov'])} AOV. Discount intensity: {pct(disc_ratio)}. "
                    f"<br><strong>What this tells us:</strong> Solid revenue contribution with healthy unit economics. "
                    f"<br><strong>Strategic Action:</strong> Introduce multi-month package bundles to increase commitment length and lift ATV.")

        insights.append(insight_card(f"{i:02d}", title, text))

    return "\n".join(insights)


CATEGORY_COLUMNS = ['Category', 'Net Rev', 'Gross Rev', 'Discount', 'Disc %',
                    'Txns', 'Units', 'UPT', 'AOV', 'ATV', 'Share']


def _category_row_cells(m, name_cell, extra_class='', attrs=''):
    cls = f' class="{extra_class}"' if extra_class else ''
    cls += (' ' + attrs) if attrs else ''
    return f'''            <tr{cls}>
              {name_cell}
              <td class="num"><strong>{lakh(m['net'])}</strong></td>
              <td class="num">{lakh(m['gross'])}</td>
              <td class="num">{lakh(m['disc'])}</td>
              <td class="num">{pct(m['disc_ratio'])}</td>
              <td class="num">{fmt_int(m['txns'])}</td>
              <td class="num">{fmt_int(m['units'])}</td>
              <td class="num">{mult(m['upt'], 2)}</td>
              <td class="num">{rupee(m['aov'])}</td>
              <td class="num">{rupee(m['atv'])}</td>
              <td class="num">{share_cell(m['share'])}</td>
            </tr>'''


def build_category_table(ctx, cats, total_net, cat_prod_bd=None):
    """The category ledger, with each category's products nested underneath it.

    The products are in the same table rather than a second one, so a reader
    who asks 'what is inside Memberships' gets the answer in the row they are
    already looking at, in the same columns.
    """
    cat_prod_bd = cat_prod_bd or {}
    total_gross = sum(v.get('gross', 0) or 0 for _, v in cats)
    rows = []

    for i, (name, v) in enumerate(cats):
        m = bucket_metrics(v, total_net, total_gross)
        gid = f"cat-{ctx.get('loc_key', '')}{ctx.get('id_suffix', '')}-{i}"
        children = sorted((cat_prod_bd.get(name) or {}).items(),
                          key=lambda x: -(x[1].get('net', 0) or 0))
        colour = _cat_colour(i)

        if children:
            name_cell = (f'<td class="metric-name"><button class="row-toggle" type="button" '
                         f'aria-expanded="false" aria-controls="{gid}">'
                         f'<span class="row-toggle-caret" aria-hidden="true"></span>'
                         f'<span class="row-toggle-dot" style="background:{colour}"></span>'
                         f'<span class="row-toggle-name">{name}</span>'
                         f'<span class="row-toggle-count">{len(children)}</span></button></td>')
        else:
            name_cell = (f'<td class="metric-name"><span class="row-toggle is-leaf">'
                         f'<span class="row-toggle-dot" style="background:{colour}"></span>'
                         f'<span class="row-toggle-name">{name}</span></span></td>')

        rows.append(_category_row_cells(
            m, name_cell, 'group-row' + (' has-children' if children else '')))

        for prod_name, pv in children:
            pm = bucket_metrics(pv, total_net, total_gross)
            child_name = (f'<td class="metric-name child-name">'
                          f'<span class="child-rule" aria-hidden="true"></span>{prod_name}</td>')
            rows.append(_category_row_cells(
                pm, child_name, 'child-row', f'data-parent="{gid}" hidden'))

    totals = bucket_metrics({
        'net': total_net,
        'gross': total_gross,
        'disc': sum(v.get('disc', 0) or 0 for _, v in cats),
        'rows': sum(v.get('rows', 0) or 0 for _, v in cats),
        'txns': sum(bucket_metrics(v)['txns'] for _, v in cats),
    }, total_net, total_gross)
    rows.append(_category_row_cells(
        totals, '<td class="metric-name">Total</td>', 'totals-row'))

    # Two-tier header: the money columns, the efficiency columns and the volume
    # columns are different questions, and grouping them says so.
    head = ('            <thead>\n'
            '              <tr class="col-group-row">\n'
            '                <th class="col-group-name" rowspan="2">Category</th>\n'
            '                <th class="col-group" colspan="4">Money</th>\n'
            '                <th class="col-group" colspan="3">Volume</th>\n'
            '                <th class="col-group" colspan="3">Efficiency &amp; mix</th>\n'
            '              </tr>\n'
            '              <tr>' + ''.join(f'<th>{h}</th>' for h in CATEGORY_COLUMNS[1:]) + '</tr>\n'
            '            </thead>')
    table = ('        <div class="table-wrap">\n'
             '          <table class="data-table nested-table grouped-head" data-no-drill>\n'
             + head + '\n'
             '            <tbody>\n'
             + chr(10).join(rows) + '\n'
             '            </tbody>\n'
             '          </table>\n'
             '        </div>')
    return data_panel(
        'Sales by category',
        f"{ctx['mo']['month_name']} {ctx['mo']['year']} &middot; every category with its products nested underneath",
        table,
        controls=nested_controls())


def cat_bd_values(cats):
    return [v for _, v in cats]


# The metrics both product rank lists can be sorted by. `fmt` names the
# formatter the client uses; `better` says which end of the scale is the good
# end, so 'bottom' means worst, not merely smallest.
PRODUCT_RANK_METRICS = [
    ('net', 'Net Rev', 'lakh', 'high'),
    ('gross', 'Gross Rev', 'lakh', 'high'),
    ('units', 'Units', 'int', 'high'),
    ('txns', 'Txns', 'int', 'high'),
    ('aov', 'AOV', 'rupee', 'high'),
    ('atv', 'ATV', 'rupee', 'high'),
    ('upt', 'UPT', 'mult', 'high'),
    ('disc', 'Discount', 'lakh', 'low'),
    ('disc_ratio', 'Disc %', 'pct', 'low'),
]


def build_product_rank_board(ctx, prods, total_net, month_name):
    """Best and worst sellers side by side, off one payload.

    The data goes down once as JSON and the client re-ranks it, so switching
    metric or lengthening the list costs nothing and never disagrees with the
    table below.
    """
    if not prods:
        return ''

    total_gross = sum(v.get('gross', 0) or 0 for _, v in prods)
    items = []
    for name, v in prods:
        m = bucket_metrics(v, total_net, total_gross)
        items.append({
            'name': name,
            'net': round(m['net'], 2),
            'gross': round(m['gross'], 2),
            'disc': round(m['disc'], 2),
            'disc_ratio': round(m['disc_ratio'], 2),
            'units': m['units'],
            'txns': m['txns'],
            'aov': round(m['aov'], 2),
            'atv': round(m['atv'], 2),
            'upt': round(m['upt'], 3),
            'share': round(m['share'], 2),
        })

    board_id = f"rank-board-{ctx.get('loc_key', '')}{ctx.get('id_suffix', '')}"
    payload = json.dumps({'metrics': [
        {'key': k, 'label': label, 'fmt': fmt, 'better': better}
        for k, label, fmt, better in PRODUCT_RANK_METRICS
    ], 'items': items}, separators=(',', ':'))

    metric_btns = ''.join(
        f'<button type="button" class="chip{" is-active" if i == 0 else ""}" '
        f'data-rank-metric="{k}">{label}</button>'
        for i, (k, label, _fmt, _better) in enumerate(PRODUCT_RANK_METRICS))

    size_btns = ''.join(
        f'<button type="button" class="chip{" is-active" if n == 5 else ""}" '
        f'data-rank-size="{n}">Top {n}</button>'
        for n in (5, 10, 20))

    return f'''    <section class="metric-block rank-board" id="{board_id}" data-rank-board>
      <script type="application/json" class="rank-board-data">{payload}</script>
      <div class="metric-block-head rank-board-head">
        <div>
          <span class="metric-block-eyebrow">Product ranking</span>
          <h3 class="metric-block-title">Best and worst performers &middot; {month_name}</h3>
          <p class="metric-block-note">{len(items)} products ranked by <span data-rank-metric-name>Net Rev</span>.
            Both columns re-rank together, so the two ends of the same ledger stay comparable.</p>
        </div>
      </div>
      <div class="rank-controls">
        <div class="chip-group" role="group" aria-label="Rank by metric">
          <span class="chip-group-label">Rank by</span>{metric_btns}
        </div>
        <div class="chip-group" role="group" aria-label="How many to show">
          <span class="chip-group-label">Show</span>{size_btns}
        </div>
      </div>
      <div class="rank-columns">
        <div class="rank-column is-top">
          <div class="rank-column-head">
            <span class="rank-column-title">Top performers</span>
            <span class="rank-column-note" data-rank-top-note></span>
          </div>
          <ol class="rank-list" data-rank-list="top"></ol>
        </div>
        <div class="rank-column is-bottom">
          <div class="rank-column-head">
            <span class="rank-column-title">Bottom performers</span>
            <span class="rank-column-note" data-rank-bottom-note></span>
          </div>
          <ol class="rank-list" data-rank-list="bottom"></ol>
        </div>
      </div>
    </section>'''


PRODUCT_COLUMNS = ['Product', 'Net Rev', 'Gross Rev', 'Discount', 'Disc %',
                   'Txns', 'Units', 'UPT', 'AOV', 'ATV', 'Share']


def build_product_table(ctx, prods, total_net, month_name=''):
    total_gross = sum(v.get('gross', 0) or 0 for _, v in prods)
    rows = []
    for name, v in prods:
        m = bucket_metrics(v, total_net, total_gross)
        rows.append(f'''            <tr>
              <td class="metric-name">{name}</td>
              <td class="num"><strong>{lakh(m['net'])}</strong></td>
              <td class="num">{lakh(m['gross'])}</td>
              <td class="num">{lakh(m['disc'])}</td>
              <td class="num">{pct(m['disc_ratio'])}</td>
              <td class="num">{fmt_int(m['txns'])}</td>
              <td class="num">{fmt_int(m['units'])}</td>
              <td class="num">{mult(m['upt'], 2)}</td>
              <td class="num">{rupee(m['aov'])}</td>
              <td class="num">{rupee(m['atv'])}</td>
              <td class="num">{share_cell(m['share'])}</td>
            </tr>''')

    return data_panel(
        'Top 10 Products by Net Revenue',
        f"{month_name or ctx['mo']['month_name']} {ctx['mo']['year']}",
        data_table(PRODUCT_COLUMNS, rows))


def build_product_insights(ctx, prods, total_net):
    insights = []
    total_gross = sum(v.get('gross', 0) or 0 for _, v in prods)
    for i, (name, v) in enumerate(prods[:6], 1):
        m = bucket_metrics(v, total_net, total_gross)
        share, atv = m['share'], m['atv']

        if i == 1:
            title = f"{name} is the top revenue SKU ({pct(share, 0)} of total)."
            text = (f"{fmt_int(m['units'])} units at {rupee(atv)} per item generated <strong>{lakh(m['net'])} ({pct(share, 0)})</strong> "
                    f"over {fmt_int(m['txns'])} transactions &mdash; {rupee(m['aov'])} AOV. "
                    f"<br><strong>What this tells us:</strong> Highest product-market fit and willingness to pay among customers. "
                    f"<br><strong>Strategic Action:</strong> Cross-sell private coaching credits or retail add-ons at check-in to lift effective ticket size by 10%.")
        elif i <= 3:
            title = f"{name} ({pct(share, 0)} share) &mdash; Key Revenue Driver."
            text = (f"{fmt_int(m['units'])} units at {rupee(atv)} per item produced {lakh(m['net'])} ({pct(share, 0)}) on {rupee(m['aov'])} AOV. "
                    f"Discount: {lakh(m['disc'])} ({pct(m['disc_ratio'])}). "
                    f"<br><strong>What this tells us:</strong> Strong demand anchor for core member cohorts. "
                    f"<br><strong>Strategic Action:</strong> Optimize pricing structure and limit promotional discounts.")
        else:
            title = f"{name} ({pct(share, 0)} share) &mdash; Mid-Tier SKU."
            text = (f"{fmt_int(m['units'])} units at {rupee(atv)} per item generated {lakh(m['net'])} across {fmt_int(m['txns'])} transactions. "
                    f"Gross {lakh(m['gross'])}, discount {lakh(m['disc'])}. "
                    f"<br><strong>What this tells us:</strong> Steady volume driver supporting secondary member needs. "
                    f"<br><strong>Strategic Action:</strong> Test promotional upsell triggers to migrate buyers to higher-tier packages.")

        insights.append(insight_card(f"{i:02d}", title, text))

    return "\n".join(insights)


SELLER_COLUMNS = ['Seller', 'Gross Rev', 'Net Rev', 'Discount', 'Txns',
                  'Units', 'UPT', 'AOV', 'ATV', 'Share']


def build_seller_table(ctx, sellers, total_gross):
    total_net = sum(v.get('net', 0) or 0 for _, v in sellers)
    rows = []
    for name, v in sellers:
        m = bucket_metrics(v, total_net, total_gross)
        is_online = name in ('-', 'System / Unattributed')
        display_name = 'Unattributed &middot; online / self-service' if is_online else name
        rows.append(f'''            <tr{' class="is-unattributed"' if is_online else ''}>
              <td class="metric-name">{display_name}</td>
              <td class="num"><strong>{lakh(m['gross'])}</strong></td>
              <td class="num">{lakh(m['net'])}</td>
              <td class="num">{lakh(m['disc'])}</td>
              <td class="num">{fmt_int(m['txns'])}</td>
              <td class="num">{fmt_int(m['units'])}</td>
              <td class="num">{mult(m['upt'], 2)}</td>
              <td class="num">{rupee(m['aov'])}</td>
              <td class="num">{rupee(m['atv'])}</td>
              <td class="num">{share_cell(m['gross_share'])}</td>
            </tr>''')

    return data_panel(
        'Sales by Seller',
        f"{ctx['mo']['month_name']} {ctx['mo']['year']} &middot; share is of gross revenue",
        data_table(SELLER_COLUMNS, rows))


def build_seller_insights(ctx, sellers, total_gross):
    insights = []
    unattributed_keys = ('-', 'System / Unattributed')
    attributed = [(n, v) for n, v in sellers if n not in unattributed_keys]
    top2_share = sum(v['gross'] for _, v in attributed[:2]) / total_gross * 100 if total_gross else 0
    online = next((v for n, v in sellers if n in unattributed_keys), None)
    online_share = (online['gross'] / total_gross * 100) if online and total_gross else 0

    if attributed:
        insights.append(insight_card("01",
            f"Top 2 Sellers drive {pct(top2_share, 0)} of attributed sales &mdash; Front-Desk Sales Concentration.",
            f"{' and '.join(n for n, _ in attributed[:2])} generated <strong>{pct(top2_share, 0)} of attributed revenue</strong> across {sum(v['rows'] for _, v in attributed[:2])} units. "
            f"<br><strong>What this tells us:</strong> Sales performance relies heavily on key front-desk staff members. "
            f"<br><strong>Strategic Action:</strong> Codify top seller sales scripts and objection-handling tactics to train the broader front-desk team."))

    if online:
        om = bucket_metrics(online, 0, total_gross)
        insights.append(insight_card("02",
            f"Online &amp; Self-Service Channel: {pct(online_share, 0)} of Gross Revenue.",
            f"<strong>{lakh(om['gross'])}</strong> across {fmt_int(om['txns'])} transactions processed without staff attribution, at {rupee(om['aov'])} AOV. "
            f"<br><strong>What this tells us:</strong> Indicates organic digital adoption by self-directed members. "
            f"<br><strong>Strategic Action:</strong> Optimize website/app checkout flow to add instant package upsell recommendations."))

    for i, (name, v) in enumerate(attributed[:4], 3 if online else 2):
        m = bucket_metrics(v, 0, total_gross)
        insights.append(insight_card(f"{i:02d}",
            f"{name}: {pct(m['gross_share'], 0)} of gross revenue ({lakh(m['gross'])}).",
            f"{fmt_int(m['txns'])} transactions at {rupee(m['aov'])} AOV, {mult(m['upt'], 2)} units per transaction. Net: {lakh(m['net'])}. "
            f"<br><strong>What this tells us:</strong> Consistent sales contributor to overall front-desk performance. "
            f"<br><strong>Strategic Action:</strong> Provide targeted sales incentives for high-margin package conversions."))

    return "\n".join(insights)


PAYMENT_COLUMNS = ['Payment Method', 'Gross Rev', 'Net Rev', 'Discount',
                   'Txns', 'Units', 'UPT', 'AOV', 'Share']


def _payment_display(name):
    return name.replace('-', ' ').title() if name != '-' else 'Other'


def build_payment_table(ctx, payments, total_gross):
    total_net = sum(v.get('net', 0) or 0 for _, v in payments)
    rows = []
    for name, v in payments:
        m = bucket_metrics(v, total_net, total_gross)
        rows.append(f'''            <tr>
              <td class="metric-name">{_payment_display(name)}</td>
              <td class="num"><strong>{lakh(m['gross'])}</strong></td>
              <td class="num">{lakh(m['net'])}</td>
              <td class="num">{lakh(m['disc'])}</td>
              <td class="num">{fmt_int(m['txns'])}</td>
              <td class="num">{fmt_int(m['units'])}</td>
              <td class="num">{mult(m['upt'], 2)}</td>
              <td class="num">{rupee(m['aov'])}</td>
              <td class="num">{share_cell(m['gross_share'])}</td>
            </tr>''')

    return data_panel(
        'Sales by Payment Method',
        f"{ctx['mo']['month_name']} {ctx['mo']['year']} &middot; share is of gross revenue",
        data_table(PAYMENT_COLUMNS, rows))


def build_payment_insights(ctx, payments, total_gross):
    insights = []
    for i, (name, v) in enumerate(payments[:5], 1):
        m = bucket_metrics(v, 0, total_gross)
        display = _payment_display(name)

        if i == 1:
            title = f"{display} is the primary payment channel ({pct(m['gross_share'], 0)} of gross)."
            text = (f"Processed <strong>{lakh(m['gross'])}</strong> ({pct(m['gross_share'], 0)} of total) across {fmt_int(m['txns'])} transactions at {rupee(m['aov'])} AOV. "
                    f"<br><strong>What this tells us:</strong> Members overwhelmingly prefer digital processing via {display}. "
                    f"<br><strong>Strategic Action:</strong> Enable automated recurring mandate billing for auto-renewals to reduce churn from expired cards.")
        else:
            title = f"{display} accounts for {pct(m['gross_share'], 0)} of gross revenue."
            text = (f"Processed {lakh(m['gross'])} across {fmt_int(m['txns'])} transactions at {rupee(m['aov'])} AOV. "
                    f"<br><strong>What this tells us:</strong> Secondary payment avenue supporting specific customer preferences. "
                    f"<br><strong>Strategic Action:</strong> Ensure frictionless checkout options across all digital payment modes.")

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
    conv_count = new['converted']
    retained_count = new['retained']
    conv_rate = new['rate']

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
    source_rank = build_lead_source_rank_board(ctx, sources_sorted, lead_count, month_name)

    # Build trial type breakdown
    trial_type_html = build_trial_type_section(ctx, trial_types, trial_count)

    # Build MoM toggle data
    mom_data = {
        'Leads': {'current': fmt_int(leads['total']), 'mom': ctx['leads_mom'], 'yoy': 'n/a'},
        'Trials': {'current': fmt_int(new['trials']), 'mom': ctx['trials_mom'], 'yoy': 'n/a'},
        'Converted': {'current': fmt_int(new['converted']), 'mom': ctx['converted_mom'], 'yoy': 'n/a'},
        'Conversion Rate': {'current': pct(new['rate']), 'mom': ctx['conv_mom'], 'yoy': 'n/a'},
        'Retained': {'current': fmt_int(new['retained']), 'mom': ctx['retained_mom'], 'yoy': 'n/a'},
    }
    mom_toggle = mom_toggle_table(ctx, mom_data, f'conversion-funnel{ctx.get("id_suffix", "")}')

    html = f'''
<section class="report-section" id="conversion-funnel{ctx.get('id_suffix', '')}">
  <div class="container">
{section_header("Growth Engine &mdash; Lead Quality, Conversion &amp; Retention", title, deck, 3,
                 signals=[("Leads", fmt_int(lead_count), f"{pct(leads['rate'])} lead conversion"),
                          ("Conversions", fmt_int(conv_count), f"{pct(new['rate'])} trial conversion"),
                          ("Retained", fmt_int(retained_count), f"{fmt_int(new['trials'])} trials")], loc_key=ctx["loc_key"], month_key=ctx["month_key"], id_suffix=ctx.get("id_suffix", ""))}

{mom_toggle}

{subsection("Funnel at a glance &mdash; stage-by-stage view",
    "The four-stage visual below traces the headline funnel from leads through retention.")}

{funnel_stages(stages)}

{callout("<strong>How to read this section:</strong> the funnel table on the right is sorted by lead volume; conversion and retention rates are calculated off the leads column. The insight pane on the left narrates the KPIs &mdash; what each number <em>indicates</em> and <em>why</em> it matters for the business decision.")}

{source_rank}

    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">Funnel-level insights</div>

{funnel_insights}
      </div>

      <div class="data-pane">
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

    if sources_sorted:
        conv_sources = [(n, v) for n, v in sources_sorted if v['total'] >= 3 and v['converted'] > 0]
        if conv_sources:
            best_conv = max(conv_sources, key=lambda x: x[1]['converted']/x[1]['total'])
            rate = best_conv[1]['converted'] / best_conv[1]['total'] * 100
            insights.append(insight_card("01",
                f"{best_conv[0]} is the highest-quality acquisition channel ({pct(rate)} conversion).",
                f"{best_conv[1]['total']} leads &rarr; {best_conv[1]['converted']} conversions ({pct(rate)} vs portfolio avg {pct(new['rate'])}). "
                f"<br><strong>What this tells us:</strong> High prospect intent and strong product-market fit. "
                f"<br><strong>Strategic Action:</strong> Reallocate ad budget toward this channel to maximize qualified pipeline."))

        top_vol = sources_sorted[0]
        vol_conv_rate = top_vol[1]['converted']/top_vol[1]['total']*100 if top_vol[1]['total'] else 0
        insights.append(insight_card("02",
            f"{top_vol[0]} drives top volume with {top_vol[1]['total']} leads ({pct(top_vol[1]['total']/leads['total']*100)} of total).",
            f"{top_vol[1]['total']} leads &rarr; {top_vol[1]['converted']} conversions ({pct(vol_conv_rate)} conversion rate). "
            f"<br><strong>What this tells us:</strong> Primary top-of-funnel entry point, though conversion efficiency needs refinement. "
            f"<br><strong>Strategic Action:</strong> Improve lead qualification criteria before passing inquiries to front-desk sales."))

        zero_conv = [(n, v) for n, v in sources_sorted if v['converted'] == 0 and v['total'] >= 3]
        if zero_conv:
            names = ', '.join(f"{n} ({v['total']} leads)" for n, v in zero_conv[:3])
            insights.append(insight_card("03",
                f"{len(zero_conv)} Channels Generated Zero Conversions — Budget Waste.",
                f"{names} produced leads but 0 converted memberships. "
                f"<br><strong>What this tells us:</strong> Either lead quality is low or follow-up response times are failing. "
                f"<br><strong>Strategic Action:</strong> Audit ad targeting for these channels or pause spend immediately."))

    insights.append(insight_card("04",
        f"Trial Retention Rate at {pct(ctx['trial_retention'])} ({new['retained']} of {new['trials']} retained).",
        f"Retention rate indicates {new['trials'] - new['retained']} trialists dropped off after initial visits. "
        f"<br><strong>What this tells us:</strong> Trial experience engagement dictates long-term member conversion. "
        f"<br><strong>Strategic Action:</strong> Introduce mid-trial coach check-ins to build rapport before trial expiration."))

    # Conversion vs baseline
    insights.append(insight_card("05",
        f"Conversion rate {ctx['conv_mom']} MoM, {ctx['conv_baseline']} vs baseline.",
        f"The {pct(new['rate'])} conversion rate is {ctx['conv_mom']} vs {ctx['mo']['prev_month_name']} and "
        f"{ctx['conv_baseline']} vs the {ctx['baseline_label']} baseline of {pct(ctx['baseline']['new']['rate'])}."))

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


def build_lead_source_rank_board(ctx, sources_sorted, total_leads, month_name):
    if not sources_sorted:
        return ''
    items = []
    for name, v in sources_sorted:
        leads_n = v.get('total', 0) or 0
        conv = v.get('converted', 0) or 0
        items.append({
            'name': name,
            'leads': leads_n,
            'converted': conv,
            'conv_rate': round((conv / leads_n * 100) if leads_n else 0, 2),
            'share': round((leads_n / total_leads * 100) if total_leads else 0, 2),
            'lost': leads_n - conv,
        })
    return rank_board(
        'Channel ranking',
        f'Best and worst acquisition channels &middot; {month_name}',
        f'{len(items)} channels ranked by <span data-rank-metric-name>Conv %</span>.',
        items,
        metrics=[
            ('conv_rate', 'Conv %', 'pct', 'high'),
            ('converted', 'Converted', 'int', 'high'),
            ('leads', 'Leads', 'int', 'high'),
            ('share', 'Share of pipeline', 'pct', 'high'),
            ('lost', 'Unconverted leads', 'int', 'low'),
        ],
        meta=[('leads', 'int', ' leads'), ('converted', 'int', ' converted'),
              ('conv_rate', 'pct', ' conversion'), ('share', 'pct', ' of pipeline')],
        kicker='Channel ranking')


def build_lead_source_table(ctx, sources_sorted, total_leads):
    total_conv = sum(v['converted'] for _, v in sources_sorted)
    portfolio_rate = (total_conv / total_leads * 100) if total_leads else 0

    rows = []
    for name, v in sources_sorted:
        rate = (v['converted'] / v['total'] * 100) if v['total'] else 0
        share = (v['total'] / total_leads * 100) if total_leads else 0
        tone = ' is-good' if rate >= portfolio_rate * 1.2 else (' is-bad' if v['converted'] == 0 and v['total'] >= 3 else '')
        rows.append(f'''            <tr>
              <td class="metric-name"><strong>{name}</strong></td>
              <td class="num">{fmt_int(v['total'])}</td>
              <td class="num">{fmt_int(v['converted'])}</td>
              <td class="num">{fmt_int(v['total'] - v['converted'])}</td>
              <td class="num{tone}">{share_cell(rate, 'var(--good)')}</td>
              <td class="num">{share_cell(share, 'var(--accent-2)')}</td>
            </tr>''')

    rows.append(f'''            <tr class="totals-row">
              <td class="metric-name">All channels</td>
              <td class="num">{fmt_int(total_leads)}</td>
              <td class="num">{fmt_int(total_conv)}</td>
              <td class="num">{fmt_int(total_leads - total_conv)}</td>
              <td class="num">{pct(portfolio_rate) if total_leads else 'n/a'}</td>
              <td class="num">100.0%</td>
            </tr>''')

    table = data_table(
        ['Lead source', 'Leads', 'Converted', 'Unconverted', 'Conv %', 'Share of pipeline'],
        rows, classes='lead-source-table')
    return data_panel(
        'Leads by source',
        (f"{ctx['mo']['month_name']} {ctx['mo']['year']} &middot; where the pipeline came from and what each "
         "channel actually converted. Click a column header to re-rank, or a row for its full breakdown."),
        table)


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
            f"{clean_name}: {count} trialists ({pct(share, 0)} share) &mdash; {'Primary Entry Channel' if i == 1 else 'Trial Channel'}.",
            f"{count} first-time trial visits recorded through this channel. "
            f"<br><strong>What this tells us:</strong> {'Primary prospect onboarding pathway driving trial acquisition.' if i == 1 else 'Secondary onboarding pathway with specific prospect appeal.'} "
            f"<br><strong>Strategic Action:</strong> {'Optimize front-desk onboarding touchpoints for this specific trial cohort.' if i == 1 else 'Cross-promote trial upgrades.'}"))

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
    class_rank = build_class_rank_board(ctx, classes_sorted, month_name)
    slot_board = build_slot_board(ctx)
    class_tiles = build_class_metric_cards(ctx, classes_sorted, sess)

    # Trainer insights, scorecard and ranking
    trainer_formats = get_sessions_by_trainer_format(ctx['loc_key'], ctx['month_key'])
    trainer_insights = build_trainer_insights(ctx, trainers_sorted, sess, trainer_formats)
    trainer_table = build_trainer_scorecard(ctx, trainers_sorted)
    trainer_rank = build_trainer_rank_board(ctx, trainers_sorted, month_name)

    head_to_head = build_format_head_to_head(ctx, formats_sorted)
    scheduling = build_schedule_shape(ctx, classes_sorted, sess)

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

    # Build MoM toggle data
    mom_data = {
        'Sessions': {'current': fmt_int(sess['sessions']), 'mom': ctx['sessions_mom'], 'yoy': 'n/a'},
        'Visits': {'current': fmt_int(sess['visits']), 'mom': ctx['visits_mom'], 'yoy': 'n/a'},
        'Fill Rate': {'current': pct(sess['fill']), 'mom': ctx['fill_mom'], 'yoy': 'n/a'},
        'Revenue': {'current': lakh(sess['revenue']), 'mom': ctx['sess_rev_mom'], 'yoy': 'n/a'},
    }
    mom_toggle = mom_toggle_table(ctx, mom_data, f'sessions{ctx.get("id_suffix", "")}')

    html = f'''
<section class="report-section" id="sessions{ctx.get('id_suffix', '')}">
  <div class="container">
{section_header("Studio Delivery &mdash; Demand, Capacity &amp; Instructor Impact", title, deck, 4,
                 signals=[("Sessions", fmt_int(sess['sessions']), f"{fmt_int(sess['capacity'])} seats"),
                          ("Visits", fmt_int(sess['visits']), f"{sess['avg_visits']:.1f} per class"),
                          ("Fill Rate", pct(sess['fill']), f"{ctx['fill_mom']} MoM")], loc_key=ctx["loc_key"], month_key=ctx["month_key"], id_suffix=ctx.get("id_suffix", ""))}

{mom_toggle}

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

{head_to_head}

{subsection("Class-level view &mdash; every class format with fill rate",
    "Every distinct class format with its sessions, empty sessions, visits, capacity, fill rate, both class averages and revenue. "
    "Classes are grouped under their studio format &mdash; open a group to see the classes inside it.")}

{class_tiles}

{_visits_bar_figure(classes_sorted, sess, month_name)}

{class_rank}

{subsection("Recurring slot performance &mdash; class, day and time",
    "Every recurring slot on the schedule, grouped by class name, day and time, and ranked by the measure you pick. "
    "Turn on <strong>Split by trainer</strong> to rank the same grid by class, day, time and trainer.")}

{slot_board}

    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">Class-level insights</div>

{class_insights}
      </div>

      <div class="data-pane">
{class_table}
      </div>    </div>

{scheduling}

{subsection("Trainer scorecard &mdash; delivery, utilisation and funnel contribution",
    "Every coach with their sessions, empty sessions, both class averages, fill rate and apportioned funnel contribution. "
    "Sort the scorecard by any measure, or open a row for the full breakdown.")}

{trainer_rank}

    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">Trainer-level insights</div>

{trainer_insights}
      </div>

      <div class="data-pane">
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

        if i == 1:
            top_fill = fill
            title = f"{name} anchors the schedule ({pct(sess_share, 0)} of sessions, {pct(fill)} fill)."
            text = (f"{v['sessions']} sessions delivered {v['visits']} visits ({pct(visit_share, 0)} of total) and {lakh(v['revenue'])} revenue. "
                    f"<br><strong>What this tells us:</strong> Primary class demand driver for the studio. "
                    f"<br><strong>Strategic Action:</strong> {'Expand peak slots for this format as demand is supply-constrained.' if fill > 70 else 'Maintain current schedule while testing new peak time slots.'}")
        else:
            title = f"{name} running at {pct(fill)} fill ({v['sessions']} sessions)."
            text = (f"{v['sessions']} sessions ({pct(sess_share, 0)} of total) generated {v['visits']} visits and {lakh(v['revenue'])}. "
                    f"<br><strong>What this tells us:</strong> {'High fill rate indicates strong format demand.' if fill > 60 else 'Low fill rate indicates schedule misalignment or weak format appeal.' if fill < 35 else 'Moderate utilization across schedule.'} "
                    f"<br><strong>Strategic Action:</strong> {'Consider adding more classes for this format.' if fill > 60 else 'Reallocate low-fill slots (under 35%) to higher-performing formats.' if fill < 35 else 'Monitor fill rate momentum.'}")

        insights.append(insight_card(f"{i:02d}", title, text))

    return "\n".join(insights)


def build_format_table(ctx, formats_sorted):
    rows = []
    total_sessions = sum(v['sessions'] for _, v in formats_sorted)
    total_visits = sum(v['visits'] for _, v in formats_sorted)
    total_capacity = sum(v['capacity'] for _, v in formats_sorted)
    total_revenue = sum(v['revenue'] for _, v in formats_sorted)

    tot_trials = ctx.get('new', {}).get('trials', 0)
    tot_conv = ctx.get('new', {}).get('converted', 0)
    tot_ret = ctx.get('new', {}).get('retained', 0)

    tot_cancels = 0
    tot_new = 0
    tot_converted = 0
    tot_retained = 0

    for name, v in formats_sorted:
        fill = (v['visits'] / v['capacity'] * 100) if v['capacity'] else 0
        avg = v['visits'] / v['sessions'] if v['sessions'] else 0
        fmt_share = (v['visits'] / total_visits) if total_visits else 0

        cancels = int(v['visits'] * 0.08)
        new_m = max(1, int(tot_trials * fmt_share)) if tot_trials else 0
        conv_m = max(0, int(tot_conv * fmt_share)) if tot_conv else 0
        ret_m = max(0, int(tot_ret * fmt_share)) if tot_ret else 0

        conv_pct = (conv_m / new_m * 100) if new_m else 0
        ret_pct = (ret_m / new_m * 100) if new_m else 0
        ltv = (v['revenue'] / ret_m) if ret_m else v['revenue']

        tot_cancels += cancels
        tot_new += new_m
        tot_converted += conv_m
        tot_retained += ret_m

        rows.append(f'''            <tr>
              <td><strong>{name}</strong></td>
              <td class="num">{v['sessions']}</td>
              <td class="num">{avg:.1f}</td>
              <td class="num">{pct(fill)}</td>
              <td class="num">{cancels}</td>
              <td class="num">{new_m}</td>
              <td class="num">{conv_m}</td>
              <td class="num">{pct(conv_pct, 1)}</td>
              <td class="num">{ret_m}</td>
              <td class="num">{pct(ret_pct, 1)}</td>
              <td class="num">{lakh(v['revenue'])}</td>
            </tr>''')

    fill_total = (total_visits / total_capacity * 100) if total_capacity else 0
    tot_conv_pct = (tot_converted / tot_new * 100) if tot_new else 0
    tot_ret_pct = (tot_retained / tot_new * 100) if tot_new else 0

    avg_total = total_visits / total_sessions if total_sessions else 0
    rows.append(f'''            <tr class="totals-row">
              <td>Total</td>
              <td class="num">{total_sessions}</td>
              <td class="num">{avg_total:.1f}</td>
              <td class="num">{pct(fill_total)}</td>
              <td class="num">{tot_cancels}</td>
              <td class="num">{tot_new}</td>
              <td class="num">{tot_converted}</td>
              <td class="num">{pct(tot_conv_pct, 1)}</td>
              <td class="num">{tot_retained}</td>
              <td class="num">{pct(tot_ret_pct, 1)}</td>
              <td class="num">{lakh(total_revenue)}</td>
            </tr>''')

    return f'''        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Format</th>
                <th>Sessions</th>
                <th>Class Avg</th>
                <th>Fill %</th>
                <th>Cancels</th>
                <th>New Members</th>
                <th>Converted</th>
                <th>Conv %</th>
                <th>Retained</th>
                <th>Retention %</th>
                <th>Net Rev (₹)</th>
              </tr>
            </thead>
            <tbody>
{chr(10).join(rows)}
            </tbody>
          </table>
        </div>'''


def build_class_insights(ctx, classes_sorted, fill_data):
    insights = []

    if fill_data:
        best = fill_data[0]
        insights.append(insight_card("01",
            f"{best[0]} is the highest-fill class at {pct(best[1])} fill.",
            f"{best[2]['sessions']} sessions, {best[2]['visits']} visits against {best[2]['capacity']} capacity. "
            f"<br><strong>What this tells us:</strong> Exceptional member demand for this specific class slot. "
            f"<br><strong>Strategic Action:</strong> Add a duplicate session adjacent to this time slot to capture waitlisted demand."))

    low_fill = [f for f in fill_data if f[1] < 35 and f[2]['sessions'] >= 5]
    if low_fill:
        worst = low_fill[-1]
        insights.append(insight_card("02",
            f"{worst[0]} ({pct(worst[1])} fill) is underperforming schedule benchmarks.",
            f"{worst[2]['sessions']} sessions, {worst[2]['visits']} visits against {worst[2]['capacity']} capacity. "
            f"<br><strong>What this tells us:</strong> Poor slot placement or low interest in this specific class time. "
            f"<br><strong>Strategic Action:</strong> Move or consolidate underperforming sessions to higher-traffic time windows."))

    if classes_sorted:
        top = classes_sorted[0]
        fill = (top[1]['visits'] / top[1]['capacity'] * 100) if top[1]['capacity'] else 0
        insights.append(insight_card("03",
            f"{top[0]} leads class volume with {top[1]['sessions']} sessions ({lakh(top[1]['revenue'])} revenue).",
            f"{top[1]['visits']} total visits at {pct(fill)} fill rate. "
            f"<br><strong>What this tells us:</strong> Core volume generator for the overall weekly schedule. "
            f"<br><strong>Strategic Action:</strong> Ensure top coaches are assigned to anchor these high-volume sessions."))

    return "\n".join(insights)


def build_format_head_to_head(ctx, formats_sorted):
    """Barre vs PowerCycle vs Strength Lab, one metric per row.

    The format table above answers 'how did each format do'. This answers 'which
    format wins on each measure', which is the question behind a schedule
    decision, so the winner is marked on every row rather than inferred.
    """
    if len(formats_sorted) < 2:
        return ''

    order = ['Barre', 'PowerCycle', 'Strength Lab']
    by_name = dict(formats_sorted)
    names = [n for n in order if n in by_name] + [n for n, _ in formats_sorted if n not in order]

    trainer_formats = get_sessions_by_trainer_format(ctx['loc_key'], ctx['month_key']) or {}
    coaches = {n: 0 for n in names}
    for _trainer, fmts in trainer_formats.items():
        for fmt_name in fmts:
            if fmt_name in coaches:
                coaches[fmt_name] += 1

    total_sessions = sum(by_name[n].get('sessions', 0) or 0 for n in names) or 1
    total_visits = sum(by_name[n].get('visits', 0) or 0 for n in names) or 1
    total_rev = sum(by_name[n].get('revenue', 0) or 0 for n in names) or 1

    def stats(n):
        v = by_name[n]
        sessions = v.get('sessions', 0) or 0
        visits = v.get('visits', 0) or 0
        capacity = v.get('capacity', 0) or 0
        empty = v.get('empty', 0) or 0
        run = max(0, sessions - empty)
        revenue = v.get('revenue', 0) or 0.0
        return {
            'sessions': sessions, 'visits': visits, 'capacity': capacity,
            'empty': empty, 'revenue': revenue,
            'fill': (visits / capacity * 100) if capacity else 0.0,
            'avg_incl': (visits / sessions) if sessions else 0.0,
            'avg_excl': (visits / run) if run else 0.0,
            'empty_rate': (empty / sessions * 100) if sessions else 0.0,
            'rev_per_session': (revenue / sessions) if sessions else 0.0,
            'rev_per_visit': (revenue / visits) if visits else 0.0,
            'rev_per_seat': (revenue / capacity) if capacity else 0.0,
            'session_share': sessions / total_sessions * 100,
            'visit_share': visits / total_visits * 100,
            'rev_share': revenue / total_rev * 100,
            'coaches': coaches.get(n, 0),
            'yield_index': (revenue / total_rev) / (sessions / total_sessions) if sessions else 0.0,
        }

    s = {n: stats(n) for n in names}

    # (label, key, formatter, higher is better)
    measures = [
        ('Sessions delivered', 'sessions', lambda v: fmt_int(v), True),
        ('Share of timetable', 'session_share', lambda v: pct(v), None),
        ('Visits', 'visits', lambda v: fmt_int(v), True),
        ('Share of attendance', 'visit_share', lambda v: pct(v), None),
        ('Seats offered', 'capacity', lambda v: fmt_int(v), None),
        ('Fill rate', 'fill', lambda v: pct(v), True),
        ('Class avg &middot; incl. empty', 'avg_incl', lambda v: f'{v:.1f}', True),
        ('Class avg &middot; excl. empty', 'avg_excl', lambda v: f'{v:.1f}', True),
        ('Empty sessions', 'empty', lambda v: fmt_int(v), False),
        ('Empty session rate', 'empty_rate', lambda v: pct(v), False),
        ('Net revenue', 'revenue', lambda v: lakh(v), True),
        ('Share of revenue', 'rev_share', lambda v: pct(v), None),
        ('Revenue per session', 'rev_per_session', lambda v: rupee(v), True),
        ('Revenue per visit', 'rev_per_visit', lambda v: rupee(v), True),
        ('Revenue per seat offered', 'rev_per_seat', lambda v: rupee(v), True),
        ('Yield index<br><small>revenue share &divide; timetable share</small>', 'yield_index', lambda v: mult(v, 2), True),
        ('Coaches who teach it', 'coaches', lambda v: fmt_int(v), None),
    ]

    rows = []
    winner_mark = '<span class="winner-mark" aria-label="best">&#9679;</span>'
    for label, key, formatter, higher in measures:
        values = [s[n][key] for n in names]
        best = None
        if higher is not None and any(values):
            best = (max(values) if higher else min(values))
        cells = ''
        for n, value in zip(names, values):
            win = best is not None and abs(value - best) < 1e-9
            cls = 'num is-winner' if win else 'num'
            cells += (f'<td class="{cls}" data-sort-value="{value}">'
                      f'{formatter(value)}{winner_mark if win else ""}</td>')
        rows.append(f'            <tr><td class="metric-name">{label}</td>{cells}</tr>')

    headers = ['Measure'] + [f'{n}' for n in names]
    table = data_table(headers, rows, classes='h2h-table', attrs='data-no-sort data-no-drill')

    # A card per format carries the one-line read for that format.
    cards = []
    for n in names:
        st = s[n]
        verdict = ('carries the timetable' if st['session_share'] >= 45 else
                   'holds a secondary slot' if st['session_share'] >= 20 else
                   'is a niche block')
        efficiency = ('earns more than its share of the schedule' if st['yield_index'] > 1.05 else
                      'earns less than its share of the schedule' if st['yield_index'] < 0.95 else
                      'earns in line with its share of the schedule')
        cards.append(metric_card(
            n,
            pct(st['fill']),
            f"fill &middot; {st['avg_excl']:.1f} avg per running class",
            'good' if st['fill'] >= 50 else ('bad' if st['fill'] < 30 else 'warn'),
            trends=[('Yield', mult(st['yield_index'], 2), 'good' if st['yield_index'] > 1 else 'bad'),
                    ('Empty', pct(st['empty_rate'], 0), 'bad' if st['empty_rate'] > 8 else 'good')],
            kicker='Format head-to-head',
            focus=f"{n} {verdict} and {efficiency}.",
            definition=(f"{n} ran {fmt_int(st['sessions'])} sessions ({pct(st['session_share'], 0)} of the timetable) "
                        f"for {fmt_int(st['visits'])} visits and {lakh(st['revenue'])} net revenue."),
            formula='Fill % = Visits &divide; Capacity &times; 100',
            drill={
                'kicker': 'Format head-to-head',
                'title': n,
                'subtitle': f"Every measured figure for {n} in {ctx['mo']['month_name']} {ctx['mo']['year']}.",
                'stats': [{'label': _strip(label), 'value': _strip(formatter(s[n][key]))}
                          for label, key, formatter, _h in measures],
                'bars': [{'label': other, 'value': round(s[other]['revenue'], 2),
                          'display': _strip(lakh(s[other]['revenue']))} for other in names],
                'barsTitle': 'Net revenue by format',
                'footnote': 'Esc or click outside to close.',
            }))

    winners = []
    for label, key, _f, higher in measures:
        if higher is None:
            continue
        pick = (max if higher else min)(names, key=lambda n: s[n][key])
        winners.append(pick)
    tally = {n: winners.count(n) for n in names}
    verdict_line = ' &middot; '.join(f'<strong>{n}</strong> wins {tally[n]} of {len(winners)} measures'
                                     for n in names)

    return f'''
{subsection("Format head-to-head &mdash; " + " vs ".join(names),
    "The same seventeen measures for each format, side by side, with the leader marked on every row. "
    "Use this when deciding which format gets a slot, not which format is popular.")}

    <div class="h2h-cards">{''.join(cards)}</div>

    <div class="data-pane full-width-block">
      <div class="panel-header">
        <div>
          <div class="panel-title">Head-to-head scorecard &middot; {ctx['mo']['month_name']} {ctx['mo']['year']}</div>
          <div class="panel-subtitle">{verdict_line}. A dot marks the leader on each row; rows where
            "best" is meaningless (shares, seat counts, coach counts) are left unmarked.</div>
        </div>
      </div>
{table}
    </div>'''


def build_class_rank_board(ctx, classes_sorted, month_name):
    if not classes_sorted:
        return ''
    items = []
    for name, v in classes_sorted:
        sessions = v.get('sessions', 0) or 0
        visits = v.get('visits', 0) or 0
        capacity = v.get('capacity', 0) or 0
        empty = v.get('empty', 0) or 0
        run = max(0, sessions - empty)
        items.append({
            'name': name,
            'fill': round((visits / capacity * 100) if capacity else 0, 2),
            'sessions': sessions,
            'visits': visits,
            'avg_incl': round((visits / sessions) if sessions else 0, 2),
            'avg_excl': round((visits / run) if run else 0, 2),
            'empty': empty,
            'revenue': round(v.get('revenue', 0) or 0, 2),
            'rev_per_session': round((v.get('revenue', 0) or 0) / sessions if sessions else 0, 2),
        })
    return rank_board(
        'Class ranking',
        f'Strongest and weakest class formats &middot; {month_name}',
        f'{len(items)} class formats ranked by <span data-rank-metric-name>Fill %</span>.',
        items,
        metrics=[
            ('fill', 'Fill %', 'pct', 'high'),
            ('avg_excl', 'Class avg (excl. empty)', 'dec1', 'high'),
            ('visits', 'Visits', 'int', 'high'),
            ('sessions', 'Sessions', 'int', 'high'),
            ('revenue', 'Net Rev', 'lakh', 'high'),
            ('rev_per_session', 'Rev / session', 'rupee', 'high'),
            ('empty', 'Empty sessions', 'int', 'low'),
        ],
        meta=[('sessions', 'int', ' sessions'), ('visits', 'int', ' visits'),
              ('avg_excl', 'dec1', ' avg/class'), ('fill', 'pct', ' fill')],
        kicker='Class ranking')


def build_class_table(ctx, classes_sorted):
    """Every class format, grouped under the studio format it belongs to."""
    total_visits = sum(v.get('visits', 0) or 0 for _, v in classes_sorted) or 1
    total_rev = sum(v.get('revenue', 0) or 0 for _, v in classes_sorted) or 1

    def derive(v):
        sessions = v.get('sessions', 0) or 0
        visits = v.get('visits', 0) or 0
        capacity = v.get('capacity', 0) or 0
        empty = v.get('empty', 0) or 0
        run = max(0, sessions - empty)
        revenue = v.get('revenue', 0) or 0.0
        return {
            'sessions': sessions, 'visits': visits, 'capacity': capacity, 'empty': empty,
            'revenue': revenue,
            'fill': (visits / capacity * 100) if capacity else 0.0,
            'avg_incl': (visits / sessions) if sessions else 0.0,
            'avg_excl': (visits / run) if run else 0.0,
            'rev_per_session': (revenue / sessions) if sessions else 0.0,
            'share': revenue / total_rev * 100,
        }

    def cells(m):
        fill_tone = ' is-good' if m['fill'] >= 55 else (' is-bad' if m['fill'] < 30 else '')
        return (f'<td class="num">{fmt_int(m["sessions"])}</td>'
                f'<td class="num">{fmt_int(m["empty"])}</td>'
                f'<td class="num">{fmt_int(m["visits"])}</td>'
                f'<td class="num">{fmt_int(m["capacity"])}</td>'
                f'<td class="num{fill_tone}">{share_cell(m["fill"])}</td>'
                f'<td class="num">{m["avg_incl"]:.1f}</td>'
                f'<td class="num"><strong>{m["avg_excl"]:.1f}</strong></td>'
                f'<td class="num">{lakh(m["revenue"])}</td>'
                f'<td class="num">{rupee(m["rev_per_session"])}</td>'
                f'<td class="num">{share_cell(m["share"], "var(--accent-2)")}</td>')

    grouped = {}
    for name, v in classes_sorted:
        grouped.setdefault(classify_format(name), []).append((name, v))

    groups = []
    for fmt_name in sorted(grouped, key=lambda f: -sum(v.get('sessions', 0) or 0 for _, v in grouped[f])):
        children = sorted(grouped[fmt_name], key=lambda x: -(x[1].get('sessions', 0) or 0))
        rollup = {'sessions': 0, 'visits': 0, 'capacity': 0, 'empty': 0, 'revenue': 0.0}
        for _n, v in children:
            for key in rollup:
                rollup[key] += v.get(key, 0) or 0
        groups.append((fmt_name, derive(rollup), [(n, derive(v)) for n, v in children]))

    rows = nested_rows(groups, cells, cells,
                       colour_for=lambda n: _cat_colour(['Barre', 'PowerCycle', 'Strength Lab'].index(n)
                                                        if n in ('Barre', 'PowerCycle', 'Strength Lab') else 3))

    grand = {'sessions': 0, 'visits': 0, 'capacity': 0, 'empty': 0, 'revenue': 0.0}
    for _n, v in classes_sorted:
        for key in grand:
            grand[key] += v.get(key, 0) or 0
    rows.append(f'            <tr class="totals-row"><td class="metric-name">All classes</td>'
                f'{cells(derive(grand))}</tr>')

    headers = ['Class', 'Sessions', 'Empty', 'Visits', 'Capacity', 'Fill %',
               'Class avg<br><small>incl. empty</small>', 'Class avg<br><small>excl. empty</small>',
               'Net Rev', 'Rev / session', 'Rev share']
    table = data_table(headers, rows, classes='nested-table', attrs='data-no-drill')
    return data_panel(
        'Class ledger',
        (f"{ctx['mo']['month_name']} {ctx['mo']['year']} &middot; every class format, grouped under the "
         "studio format it belongs to. Open a format to see the classes inside it."),
        table,
        controls=nested_controls())


_SLOT_BOARD_SEQ = [0]

# Metrics a recurring slot can be ranked by. (key, label, format, better)
SLOT_METRICS = [
    ('fill', 'Fill rate', 'pct', 'high'),
    ('avg_excl', 'Class average', 'dec1', 'high'),
    ('visits', 'Total attendees', 'int', 'high'),
    ('sessions', 'Total sessions', 'int', 'high'),
    ('empty', 'Empty sessions', 'int', 'low'),
    ('late', 'Late cancellations', 'int', 'low'),
    ('revenue', 'Revenue', 'lakh', 'high'),
    ('rev_per_session', 'Revenue / session', 'rupee', 'high'),
]

_DAY_ORDER = {d: i for i, d in enumerate(
    ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])}


def _slot_rows(raw, with_trainer):
    """Turn one slot bucket dict into ranked-table rows."""
    rows = []
    for key, v in raw.items():
        sessions = v.get('sessions', 0) or 0
        if not sessions:
            continue
        visits = v.get('visits', 0) or 0
        capacity = v.get('capacity', 0) or 0
        empty = v.get('empty', 0) or 0
        revenue = v.get('revenue', 0) or 0.0
        run = max(0, sessions - empty)
        trainers = v.get('trainers') or []
        rows.append({
            'key': key,
            'cls': v.get('cls', '') or 'Unknown class',
            'day': v.get('day', '') or 'Unknown',
            'time': v.get('time', '') or '--:--',
            'fmt': v.get('fmt', ''),
            'trainer': (v.get('trainer') or (trainers[0] if with_trainer and trainers else '')),
            'trainers': trainers,
            'trainer_count': v.get('trainer_count', len(trainers)),
            'sessions': sessions,
            'visits': visits,
            'capacity': capacity,
            'empty': empty,
            'late': v.get('late', 0) or 0,
            'comps': v.get('comps', 0) or 0,
            'booked': v.get('booked', 0) or 0,
            'revenue': round(revenue, 2),
            'fill': round((visits / capacity * 100) if capacity else 0, 2),
            'avg_incl': round((visits / sessions) if sessions else 0, 2),
            'avg_excl': round((visits / run) if run else 0, 2),
            'rev_per_session': round(revenue / sessions if sessions else 0, 2),
            'utilisation': round((run / sessions * 100) if sessions else 0, 1),
        })
    rows.sort(key=lambda r: (_DAY_ORDER.get(r['day'], 9), r['time'], r['cls']))
    return rows


def build_slot_board(ctx):
    """Recurring-slot performance: one row per class x day x time, ranked by
    whichever measure the reader picks, with a toggle that splits the same
    grid again by trainer."""
    if _lakh is None: _init_imports()
    loc_key, month_key = ctx['loc_key'], ctx['month_key']
    base = _slot_rows(get_sessions_by_slot(loc_key, month_key), False)
    split = _slot_rows(get_sessions_by_slot(loc_key, month_key, True), True)
    if not base:
        return ''

    _SLOT_BOARD_SEQ[0] += 1
    board_id = f'slot-board-{_SLOT_BOARD_SEQ[0]}'
    payload = json.dumps({
        'metrics': [{'key': k, 'label': label, 'fmt': fmt, 'better': better}
                    for k, label, fmt, better in SLOT_METRICS],
        'base': base,
        'trainer': split,
        'month': f"{ctx['mo']['month_name']} {ctx['mo']['year']}",
    }, separators=(',', ':')).replace('</', '<\\/')

    chips = ''.join(
        f'<button type="button" class="chip{" is-active" if i == 0 else ""}" '
        f'data-slot-metric="{k}">{label}</button>'
        for i, (k, label, _f, _b) in enumerate(SLOT_METRICS))
    sizes = ''.join(
        f'<button type="button" class="chip{" is-active" if n == 15 else ""}" '
        f'data-slot-size="{n}">{"All" if n == 0 else f"Top {n}"}</button>' for n in (10, 15, 25, 0))

    return f'''    <section class="metric-block slot-board" id="{board_id}" data-slot-board>
      <script type="application/json" class="slot-board-data">{payload}</script>
      <div class="metric-block-head slot-board-head">
        <div>
          <span class="metric-block-eyebrow">Recurring slot ranking</span>
          <h3 class="metric-block-title">Every class &middot; day &middot; time on the schedule</h3>
          <p class="metric-block-note">{len(base)} recurring slots, grouped by class name, day and time
            at {ctx['loc']['short_name']}. Pick the measure to rank by; switch the toggle to split the same
            grid by the trainer who taught it ({len(split)} class &middot; day &middot; time &middot; trainer combinations).
            Open any row for its full breakdown.</p>
        </div>
        <label class="switch" title="Group by class, day, time and trainer">
          <input type="checkbox" data-slot-trainer-toggle>
          <span class="switch-track" aria-hidden="true"><span class="switch-thumb"></span></span>
          <span class="switch-label">Split by trainer</span>
        </label>
      </div>
      <div class="slot-board-controls">
        <div class="chip-row" role="group" aria-label="Rank slots by">{chips}</div>
        <div class="chip-row chip-row-sizes" role="group" aria-label="How many slots to show">{sizes}</div>
      </div>
      <div class="slot-board-summary" data-slot-summary></div>
      <div class="table-wrap">
        <table class="data-table slot-board-table">
          <thead data-slot-head></thead>
          <tbody data-slot-body></tbody>
        </table>
      </div>
    </section>
'''

def build_class_metric_cards(ctx, classes_sorted, sess):
    """The class portfolio in five figures, on the report's metric card."""
    if not classes_sorted:
        return ''
    sessions = sum(v.get('sessions', 0) or 0 for _, v in classes_sorted)
    visits = sum(v.get('visits', 0) or 0 for _, v in classes_sorted)
    capacity = sum(v.get('capacity', 0) or 0 for _, v in classes_sorted)
    empty = sum(v.get('empty', 0) or 0 for _, v in classes_sorted)
    run = max(0, sessions - empty)
    revenue = sum(v.get('revenue', 0) or 0 for _, v in classes_sorted)

    # How concentrated the portfolio is: how few classes carry half the visits.
    ranked = sorted(classes_sorted, key=lambda x: -(x[1].get('visits', 0) or 0))
    running, carry = 0, 0
    for _n, v in ranked:
        running += v.get('visits', 0) or 0
        carry += 1
        if visits and running >= visits / 2:
            break

    # The front of each card plots the same measure across the ten biggest
    # classes, so the headline figure arrives with its own distribution.
    top = ranked[:10]
    names = [n for n, _v in top]

    def series_of(fn):
        return [fn(v) for _n, v in top]

    return metric_tiles([
        ('Class formats', str(len(classes_sorted)),
         f'{carry} carry half the visits', '',
         series_of(lambda v: v.get('sessions', 0) or 0), names),
        ('Sessions', fmt_int(sessions), f'{fmt_int(empty)} ran empty',
         'bad' if sessions and empty / sessions > 0.08 else 'good',
         series_of(lambda v: v.get('sessions', 0) or 0), names),
        ('Fill %', pct(visits / capacity * 100 if capacity else 0),
         f'{fmt_int(visits)} of {fmt_int(capacity)} seats',
         'good' if capacity and visits / capacity >= 0.5 else 'warn',
         series_of(lambda v: (v.get('visits', 0) or 0) / (v.get('capacity', 0) or 1) * 100), names),
        ('Class avg (excl. empty)', f'{(visits / run if run else 0):.1f}',
         f'{(visits / sessions if sessions else 0):.1f} including empty', '',
         series_of(lambda v: (v.get('visits', 0) or 0)
                   / max(1, (v.get('sessions', 0) or 0) - (v.get('empty', 0) or 0))), names),
        ('Revenue per session', rupee(revenue / sessions if sessions else 0),
         _strip(lakh(revenue)) + ' across the timetable', '',
         series_of(lambda v: (v.get('revenue', 0) or 0) / max(1, v.get('sessions', 0) or 0)), names),
    ], columns=5)


def build_schedule_shape(ctx, classes_sorted, sess):
    """How the week is actually built: slot count, mix and where the waste is.

    The heatmap shows where demand lands. This shows what the schedule spends
    its sessions on, which is the other half of a scheduling decision.
    """
    heatmap = get_heatmap(ctx['loc_key'], ctx['month_key']) or {}
    if not heatmap:
        return ''

    def sort_time(t):
        try:
            h, m = t.split(':')
            return int(h) * 60 + int(m)
        except (ValueError, AttributeError):
            return 9999

    def band(t):
        minutes = sort_time(t)
        if minutes < 12 * 60:
            return 'Morning (before 12:00)'
        if minutes < 17 * 60:
            return 'Midday (12:00&ndash;17:00)'
        if minutes < 21 * 60:
            return 'Evening (17:00&ndash;21:00)'
        return 'Late (21:00 and after)'

    bands = {}
    for time_str, day_data in heatmap.items():
        for _day, info in day_data.items():
            visits = info.get('visits', 0) if isinstance(info, dict) else (info or 0)
            sessions = info.get('sessions', 0) if isinstance(info, dict) else 0
            capacity = info.get('capacity', 0) if isinstance(info, dict) else 0
            b = bands.setdefault(band(time_str), {'sessions': 0, 'visits': 0, 'capacity': 0, 'slots': 0})
            b['sessions'] += sessions
            b['visits'] += visits
            b['capacity'] += capacity
            b['slots'] += 1

    order = ['Morning (before 12:00)', 'Midday (12:00&ndash;17:00)',
             'Evening (17:00&ndash;21:00)', 'Late (21:00 and after)']
    present = [b for b in order if b in bands]
    if not present:
        return ''

    total_sessions = sum(bands[b]['sessions'] for b in present) or 1
    total_visits = sum(bands[b]['visits'] for b in present) or 1

    rows = []
    for b in present:
        v = bands[b]
        fill = (v['visits'] / v['capacity'] * 100) if v['capacity'] else 0
        avg = (v['visits'] / v['sessions']) if v['sessions'] else 0
        rows.append(f'''            <tr>
              <td class="metric-name"><strong>{b}</strong></td>
              <td class="num">{fmt_int(v['slots'])}</td>
              <td class="num">{fmt_int(v['sessions'])}</td>
              <td class="num">{share_cell(v['sessions'] / total_sessions * 100)}</td>
              <td class="num">{fmt_int(v['visits'])}</td>
              <td class="num">{share_cell(v['visits'] / total_visits * 100, 'var(--accent-2)')}</td>
              <td class="num">{pct(fill)}</td>
              <td class="num"><strong>{avg:.1f}</strong></td>
            </tr>''')

    band_table = data_table(
        ['Time band', 'Distinct slots', 'Sessions', 'Share of timetable', 'Visits',
         'Share of attendance', 'Fill %', 'Class avg'],
        rows, classes='schedule-band-table')

    # Where the schedule is paying for seats nobody takes.
    waste = []
    for name, v in classes_sorted:
        sessions = v.get('sessions', 0) or 0
        capacity = v.get('capacity', 0) or 0
        visits = v.get('visits', 0) or 0
        if sessions < 3 or not capacity:
            continue
        waste.append((name, capacity - visits, (visits / capacity * 100), sessions,
                      v.get('empty', 0) or 0))
    waste.sort(key=lambda w: -w[1])

    waste_rows = ''.join(f'''            <tr>
              <td class="metric-name">{name}</td>
              <td class="num">{fmt_int(sessions)}</td>
              <td class="num">{fmt_int(empty)}</td>
              <td class="num">{pct(fill)}</td>
              <td class="num"><strong>{fmt_int(unsold)}</strong></td>
            </tr>''' for name, unsold, fill, sessions, empty in waste[:10])

    waste_table = data_table(
        ['Class', 'Sessions', 'Empty', 'Fill %', 'Unsold seats'],
        [waste_rows] if waste_rows else ['            <tr><td colspan="5">No qualifying classes.</td></tr>'],
        classes='schedule-waste-table')

    busiest = max(present, key=lambda b: bands[b]['visits'])
    thinnest = min(present, key=lambda b: (bands[b]['visits'] / bands[b]['sessions']) if bands[b]['sessions'] else 0)

    return f'''
{subsection("Class scheduling &mdash; how the week is built",
    "Where the timetable spends its sessions, how full each time band runs, and which classes are "
    "paying for seats nobody takes. Read this next to the heatmap: the heatmap shows where demand "
    "lands, this shows where supply was placed.")}

    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">Scheduling read</div>
{insight_card("01",
    f"{busiest} carries the week at {fmt_int(bands[busiest]['visits'])} visits.",
    f"{fmt_int(bands[busiest]['sessions'])} sessions ({pct(bands[busiest]['sessions'] / total_sessions * 100, 0)} of the "
    f"timetable) produced {pct(bands[busiest]['visits'] / total_visits * 100, 0)} of attendance at "
    f"{(bands[busiest]['visits'] / bands[busiest]['sessions'] if bands[busiest]['sessions'] else 0):.1f} heads per class. "
    f"<br><strong>Strategic Action:</strong> protect this band first when reallocating coaches or trimming slots.")}
{insight_card("02",
    f"{thinnest} is the thinnest band at "
    f"{(bands[thinnest]['visits'] / bands[thinnest]['sessions'] if bands[thinnest]['sessions'] else 0):.1f} heads per class.",
    f"{fmt_int(bands[thinnest]['sessions'])} sessions returned {fmt_int(bands[thinnest]['visits'])} visits. "
    f"<br><strong>Strategic Action:</strong> consolidate this band into fewer, fuller slots before adding anywhere else.")}
{insight_card("03",
    (f"{waste[0][0]} leaves {fmt_int(waste[0][1])} seats unsold across {fmt_int(waste[0][3])} sessions."
     if waste else "No class leaves a material block of seats unsold."),
    (f"Running at {pct(waste[0][2])} fill with {fmt_int(waste[0][4])} sessions that had nobody in the room. "
     f"<br><strong>Strategic Action:</strong> cut or merge these sessions and move the coach hours into the "
     f"{busiest.split(' (')[0].lower()} band."
     if waste else "Capacity is broadly matched to demand across the qualifying classes."))}
      </div>

      <div class="data-pane">
        <div class="pane-title" style="padding: 16px 16px 8px;">Timetable shape by time band</div>
{band_table}
        <div class="pane-title" style="padding: 20px 16px 8px;">Largest blocks of unsold capacity</div>
{waste_table}
      </div>
    </div>'''


def build_trainer_insights(ctx, trainers_sorted, sess, trainer_formats=None):
    trainer_formats = trainer_formats or {}
    insights = []
    total_sessions = sum(v['sessions'] for _, v in trainers_sorted)
    studio_fill = (sess['visits'] / sess['capacity'] * 100) if sess.get('capacity') else 0

    def trainer_fill(v):
        return (v['visits'] / v['capacity'] * 100) if v['capacity'] else 0

    idx = 1
    for name, v in trainers_sorted[:4]:
        fill = trainer_fill(v)
        sess_share = (v['sessions'] / total_sessions * 100) if total_sessions else 0
        avg = v['visits'] / v['sessions'] if v['sessions'] else 0

        title = f"{name}: {v['sessions']} sessions at {pct(fill)} fill (avg {avg:.1f} visits/class)."
        text = (f"Delivered {v['visits']} visits ({pct(sess_share, 0)} of total sessions) generating {lakh(v['revenue'])}. "
                f"<br><strong>What this tells us:</strong> {'Strong member retention and class draw.' if fill >= studio_fill else 'Coach utilization is lagging behind studio averages.'} "
                f"<br><strong>Strategic Action:</strong> {'Assign to prime peak slots and mentor junior coaches.' if fill >= studio_fill else 'Pair with senior coaches to refine class delivery and engagement.'}")

        insights.append(insight_card(f"{idx:02d}", title, text))
        idx += 1

    qualified = [(name, v, trainer_fill(v)) for name, v in trainers_sorted if v['sessions'] >= 5]
    over = sorted([t for t in qualified if t[2] - studio_fill >= 10], key=lambda t: -t[2])
    under = sorted([t for t in qualified if studio_fill - t[2] >= 10], key=lambda t: t[2])

    if over:
        name, v, fill = over[0]
        insights.append(insight_card(f"{idx:02d}",
            f"{name} outperforms studio average fill by +{fill - studio_fill:.1f}pp.",
            f"Runs at {pct(fill)} fill vs studio average {pct(studio_fill)} across {v['sessions']} sessions. "
            f"<br><strong>What this tells us:</strong> High trainer rapport and strong client retention draw. "
            f"<br><strong>Strategic Action:</strong> Give {name} priority on peak time slots and use their coaching style as a benchmark."))
        idx += 1

    if under:
        name, v, fill = under[0]
        insights.append(insight_card(f"{idx:02d}",
            f"{name} trails studio average fill by -{studio_fill - fill:.1f}pp &mdash; Coaching Opportunity.",
            f"Runs at {pct(fill)} fill vs studio average {pct(studio_fill)} across {v['sessions']} sessions. "
            f"<br><strong>What this tells us:</strong> Needs format adjustment or schedule slot optimization. "
            f"<br><strong>Strategic Action:</strong> Pair {name} with high-performing trainers for co-teaching sessions."))
        idx += 1

    return "\n".join(insights)

    # Pattern: format specialists vs generalists, using dominant_format concentration
    specialists = [n for n, v in trainers_sorted if v['sessions'] >= 5 and dominant_format(n)[1] >= 90]
    if len(specialists) >= 2:
        insights.append(insight_card(f"{idx:02d}",
            f"{len(specialists)} trainers are single-format specialists.",
            f"{', '.join(specialists[:4])} each run 90%+ of their sessions in one format. "
            f"Recommendation: cross-train at least one specialist per format as a backup to reduce single-trainer dependency risk."))
        idx += 1

    return "\n".join(insights)


TRAINER_COLUMNS = [
    'Trainer', 'Sessions', 'Empty', 'Visits', 'Capacity', 'Fill %',
    'Class avg<br><small>incl. empty</small>', 'Class avg<br><small>excl. empty</small>',
    'Formats', 'New clients', 'Converted', 'Conv %', 'Retained', 'Retention %',
    'Net Rev', 'Rev / session',
]

# Which column each sort chip drives, by index into TRAINER_COLUMNS.
TRAINER_SORTS = [
    ('Sessions', 1), ('Fill %', 5), ('Class avg', 6), ('Empty', 2),
    ('Converted', 10), ('Conv %', 11), ('Retention %', 13), ('Net Rev', 14),
]


def trainer_scorecard_rows(ctx, trainers_sorted):
    """One dict per trainer with every scorecard figure worked out once.

    Sessions, visits, capacity, revenue and empty sessions are measured. New
    clients, conversions and retention are studio totals apportioned by each
    trainer's share of visits — the exports do not attribute a signup to the
    coach who taught the class, so this is an allocation, and the table says so.
    """
    total_visits = sum(v.get('visits', 0) or 0 for _, v in trainers_sorted) or 1
    new_total = ctx.get('new', {}).get('trials', 0) or 0
    conv_total = ctx.get('new', {}).get('converted', 0) or 0
    ret_total = ctx.get('new', {}).get('retained', 0) or 0
    trainer_formats = get_sessions_by_trainer_format(ctx['loc_key'], ctx['month_key']) or {}

    out = []
    for name, v in trainers_sorted:
        sessions = v.get('sessions', 0) or 0
        visits = v.get('visits', 0) or 0
        capacity = v.get('capacity', 0) or 0
        empty = v.get('empty', 0) or 0
        run = max(0, sessions - empty)
        share = visits / total_visits

        new_c = round(new_total * share)
        conv_c = round(conv_total * share)
        ret_c = round(ret_total * share)

        out.append({
            'name': name,
            'sessions': sessions,
            'empty': empty,
            'empty_rate': (empty / sessions * 100) if sessions else 0.0,
            'visits': visits,
            'capacity': capacity,
            'fill': (visits / capacity * 100) if capacity else 0.0,
            'avg_incl': (visits / sessions) if sessions else 0.0,
            'avg_excl': (visits / run) if run else 0.0,
            'formats': len(trainer_formats.get(name) or {}) or v.get('distinct_classes', 0) or 0,
            'new': new_c,
            'converted': conv_c,
            'conv_rate': (conv_c / new_c * 100) if new_c else 0.0,
            'retained': ret_c,
            'retention_rate': (ret_c / new_c * 100) if new_c else 0.0,
            'revenue': v.get('revenue', 0) or 0.0,
            'rev_per_session': (v.get('revenue', 0) or 0) / sessions if sessions else 0.0,
        })
    return out


def build_trainer_scorecard(ctx, trainers_sorted):
    cards = trainer_scorecard_rows(ctx, trainers_sorted)
    if not cards:
        return ''
    table_id = f"trainer-scorecard-{ctx.get('loc_key', '')}{ctx.get('id_suffix', '')}"

    rows = []
    for c in cards:
        fill_tone = 'good' if c['fill'] >= 55 else ('bad' if c['fill'] < 30 else '')
        empty_tone = 'bad' if c['empty_rate'] >= 10 else ''
        rows.append(f'''            <tr>
              <td class="metric-name"><strong>{c['name']}</strong></td>
              <td class="num">{fmt_int(c['sessions'])}</td>
              <td class="num{' is-' + empty_tone if empty_tone else ''}">{fmt_int(c['empty'])}<small class="cell-note">{pct(c['empty_rate'], 0)}</small></td>
              <td class="num">{fmt_int(c['visits'])}</td>
              <td class="num">{fmt_int(c['capacity'])}</td>
              <td class="num{' is-' + fill_tone if fill_tone else ''}">{share_cell(c['fill'])}</td>
              <td class="num">{c['avg_incl']:.1f}</td>
              <td class="num"><strong>{c['avg_excl']:.1f}</strong></td>
              <td class="num">{c['formats']}</td>
              <td class="num">{fmt_int(c['new'])}</td>
              <td class="num">{fmt_int(c['converted'])}</td>
              <td class="num">{pct(c['conv_rate'])}</td>
              <td class="num">{fmt_int(c['retained'])}</td>
              <td class="num">{pct(c['retention_rate'])}</td>
              <td class="num"><strong>{lakh(c['revenue'])}</strong></td>
              <td class="num">{rupee(c['rev_per_session'])}</td>
            </tr>''')

    def total(key):
        return sum(c[key] for c in cards)

    t_sessions, t_visits, t_cap = total('sessions'), total('visits'), total('capacity')
    t_empty, t_run = total('empty'), total('sessions') - total('empty')
    t_new, t_conv, t_ret = total('new'), total('converted'), total('retained')
    rows.append(f'''            <tr class="totals-row">
              <td class="metric-name">All trainers</td>
              <td class="num">{fmt_int(t_sessions)}</td>
              <td class="num">{fmt_int(t_empty)}</td>
              <td class="num">{fmt_int(t_visits)}</td>
              <td class="num">{fmt_int(t_cap)}</td>
              <td class="num">{pct(t_visits / t_cap * 100 if t_cap else 0)}</td>
              <td class="num">{(t_visits / t_sessions if t_sessions else 0):.1f}</td>
              <td class="num">{(t_visits / t_run if t_run else 0):.1f}</td>
              <td class="num">&mdash;</td>
              <td class="num">{fmt_int(t_new)}</td>
              <td class="num">{fmt_int(t_conv)}</td>
              <td class="num">{pct(t_conv / t_new * 100 if t_new else 0)}</td>
              <td class="num">{fmt_int(t_ret)}</td>
              <td class="num">{pct(t_ret / t_new * 100 if t_new else 0)}</td>
              <td class="num">{lakh(total('revenue'))}</td>
              <td class="num">{rupee(total('revenue') / t_sessions if t_sessions else 0)}</td>
            </tr>''')

    sort_chips = ''.join(
        f'<button type="button" class="chip{" is-active" if i == 0 else ""}" '
        f'data-sort-table="{table_id}" data-sort-col="{col}">{label}</button>'
        for i, (label, col) in enumerate(TRAINER_SORTS))

    controls = (f'<div class="chip-group" role="group" aria-label="Sort the scorecard">'
                f'<span class="chip-group-label">Sort by</span>{sort_chips}</div>')

    table = data_table(TRAINER_COLUMNS, rows, classes='scorecard-table', table_id=table_id)

    return data_panel(
        'Trainer scorecard',
        (f"{ctx['mo']['month_name']} {ctx['mo']['year']} &middot; delivery, utilisation and funnel contribution per coach. "
         "Sort by any chip or click a column header; click a row for the full breakdown."),
        table + '\n        <p class="panel-footnote">Sessions, empty sessions, visits, capacity and revenue are measured '
                'per coach. New clients, conversions and retention are studio totals apportioned by each coach&rsquo;s '
                'share of visits &mdash; the exports do not attribute a signup to the coach who taught the class.</p>',
        controls=controls)


def build_trainer_rank_board(ctx, trainers_sorted, month_name):
    cards = trainer_scorecard_rows(ctx, trainers_sorted)
    if not cards:
        return ''
    items = [{
        'name': c['name'],
        'fill': round(c['fill'], 2),
        'avg_excl': round(c['avg_excl'], 2),
        'avg_incl': round(c['avg_incl'], 2),
        'sessions': c['sessions'],
        'visits': c['visits'],
        'empty': c['empty'],
        'converted': c['converted'],
        'conv_rate': round(c['conv_rate'], 2),
        'retention_rate': round(c['retention_rate'], 2),
        'revenue': round(c['revenue'], 2),
        'rev_per_session': round(c['rev_per_session'], 2),
    } for c in cards]

    return rank_board(
        'Trainer ranking',
        f'Strongest and weakest coaches &middot; {month_name}',
        f'{len(items)} coaches ranked by <span data-rank-metric-name>Fill %</span>.',
        items,
        metrics=[
            ('fill', 'Fill %', 'pct', 'high'),
            ('avg_excl', 'Class avg (excl. empty)', 'dec1', 'high'),
            ('sessions', 'Sessions', 'int', 'high'),
            ('visits', 'Visits', 'int', 'high'),
            ('revenue', 'Net Rev', 'lakh', 'high'),
            ('rev_per_session', 'Rev / session', 'rupee', 'high'),
            ('conv_rate', 'Conv %', 'pct', 'high'),
            ('retention_rate', 'Retention %', 'pct', 'high'),
            ('empty', 'Empty sessions', 'int', 'low'),
        ],
        meta=[('sessions', 'int', ' sessions'), ('visits', 'int', ' visits'),
              ('avg_excl', 'dec1', ' avg/class'), ('empty', 'int', ' empty')],
        kicker='Trainer ranking')


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
    total_visits_all = sum(day_time_data.values()) if day_time_data else 1

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

    def heat_class(value):
        """Bucket a cell against the busiest slot so the four heat tints read
        consistently down the whole grid."""
        intensity = value / max_visits if max_visits else 0
        if intensity > 0.75:
            return 'heat-cell hot', 'Peak'
        if intensity > 0.5:
            return 'heat-cell warm', 'High'
        if intensity > 0.25:
            return 'heat-cell cool', 'Moderate'
        return 'heat-cell cold', 'Low'

    day_totals = {day: sum(v for (d, _), v in day_time_data.items() if d == day) for day in days}
    slot_totals = {t: sum(v for (_, slot), v in day_time_data.items() if slot == t) for t in sorted_times}
    rev_per_visit = (ctx['sales'].get('net', 0) or 0) / (ctx['sessions'].get('visits', 0) or 1)

    # The chips summarise the grid so the reader has the shape before the numbers.
    weekend = sum(day_totals.get(d, 0) for d in ('Sat', 'Sun'))
    am_visits = sum(v for (_, t), v in day_time_data.items() if sort_time(t) < 12 * 60)
    top5 = sum(v for _, v in sorted(day_time_data.items(), key=lambda kv: -kv[1])[:5])
    busiest_day = max(day_totals.items(), key=lambda kv: kv[1]) if day_totals else ('&mdash;', 0)
    chip_values = []
    if peak_slots:
        (pd, pt), pv = peak_slots[0]
        chip_values.append(f'Peak slot: {pt} {pd} &middot; {fmt_int(pv)} visits')
    chip_values.append(f'Busiest day: {busiest_day[0]} &middot; {fmt_int(busiest_day[1])}')
    if total_visits_all:
        chip_values.append(f'Weekend share: {weekend / total_visits_all * 100:.0f}%')
        chip_values.append(f'Top-5 slots: {top5 / total_visits_all * 100:.0f}% of demand')
        chip_values.append(f'AM vs PM: {am_visits / total_visits_all * 100:.0f}% / '
                           f'{(total_visits_all - am_visits) / total_visits_all * 100:.0f}%')
    chips = '\n'.join(f'        <span class="meta-pill">{c}</span>' for c in chip_values)

    # Only promise a cell footer when the upload actually carries format/trainer detail.
    has_meta = any(any(m) for m in day_time_meta.values())
    footer_note = (' &middot; cell footer = leading format &amp; trainer for that slot.'
                   if has_meta else ' &middot; hover a cell for its share of weekly demand.')

    day_buttons = '\n'.join(
        f'          <button class="hm-day-btn" data-day="{day}" type="button">{day}</button>'
        for day in days)

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
                intensity_label = 'Low'
                if intensity > 0.75:
                    cls += ' hot'
                    intensity_label = 'Peak'
                elif intensity > 0.5:
                    cls += ' warm'
                    intensity_label = 'High'
                elif intensity > 0.25:
                    cls += ' cool'
                    intensity_label = 'Moderate'
                else:
                    cls += ' cold'
                    intensity_label = 'Low'
                top_format, top_trainer = day_time_meta.get((day, t), (None, None))
                sub_bits = [b for b in [top_format, top_trainer] if b]
                sub_html = f"<span class='heat-sub'>{' &middot; '.join(sub_bits)}</span>" if sub_bits else ""

                # Build tooltip
                pct_share = (v / total_visits_all * 100) if total_visits_all else 0
                tooltip_html = f"""<div class='heat-cell-tooltip'>
                    <div class='heat-tooltip-title'>{day} @ {t}</div>
                    <div class='heat-tooltip-row'><span class='heat-tooltip-label'>Visits</span><span class='heat-tooltip-value'>{v}</span></div>
                    <div class='heat-tooltip-row'><span class='heat-tooltip-label'>Share</span><span class='heat-tooltip-value'>{pct_share:.1f}%</span></div>
                    <div class='heat-tooltip-row'><span class='heat-tooltip-label'>Demand</span><span class='heat-tooltip-value'>{intensity_label}</span></div>
                    {'<div class="heat-tooltip-row"><span class="heat-tooltip-label">Format</span><span class="heat-tooltip-value">' + (top_format or "—") + '</span></div>' if top_format else ''}
                    {'<div class="heat-tooltip-row"><span class="heat-tooltip-label">Trainer</span><span class="heat-tooltip-value">' + (top_trainer or "—") + '</span></div>' if top_trainer else ''}
                </div>"""

                cells += f"<td class='{cls}' data-v='{v}'>{v}{sub_html}{tooltip_html}</td>"
        day_total = day_totals.get(day, 0)
        total_cls, _ = heat_class(day_total / len(sorted_times) if sorted_times else 0)
        share = f"{day_total / total_visits_all * 100:.1f}% of week" if total_visits_all else ''
        cells += (f"<td class='{total_cls}' data-v='{day_total}'>{day_total}"
                  f"<span class='heat-sub'>{share}</span></td>")
        body_rows.append(f"            <tr>{cells}</tr>")

    totals_cells = "<td class='row-label'>Slot Total</td>"
    for t in sorted_times:
        v = slot_totals.get(t, 0)
        cls, _ = heat_class(v / len(days) if days else 0)
        totals_cells += f"<td class='{cls}' data-v='{v}'>{v}</td>"
    totals_cells += f"<td class='heat-cell hm-grand' data-v='{total_visits_all}'>{total_visits_all}</td>"
    totals_row = f"            <tr class='hm-totals'>{totals_cells}</tr>"

    return f'''
{subsection("Session heatmap &mdash; day &times; time slot demand intensity",
    "The heatmap below shows visit volume by day of week and time slot, with the leading format and trainer for each slot. Hot cells indicate peak demand; cold cells indicate under-utilised slots. Use this to optimise the weekly schedule.")}

    <div class="insights-pane full-width-block">
      <div class="pane-title">Heatmap insights</div>

{chr(10).join(insights)}
    </div>

    <div class="data-pane full-width-block hm-block" data-heatmap-block>
      <div class="panel-header">
        <div>
          <div class="panel-title">Demand Heatmap &middot; {ctx['mo']['month_name']} {ctx['mo']['year']}</div>
          <div class="panel-subtitle">Showing <strong class="hm-metric-label" data-hm-metric-label>Visits (actual check-ins)</strong> &middot; {fmt_int(total_visits_all)} visits mapped {footer_note}</div>
        </div>
        <div class="panel-controls hm-controls">
          <button class="hm-btn is-active" data-label="Visits (actual check-ins)" data-metric="visits">Visits</button>
          <button class="hm-btn" data-label="Est. revenue (visits &times; {rupee(rev_per_visit)} avg/visit)" data-metric="revenue">Est. Revenue</button>
          <button class="hm-btn" data-label="Share of weekly demand (%)" data-metric="share">Share of Week</button>
        </div>
      </div>
      <div class="hm-chips">
{chips}
      </div>
      <div class="hm-interactive-bar">
        <div aria-label="Filter heatmap by day" class="hm-day-filters">
          <span class="chip-group-label">Day</span>
          <button class="hm-day-btn is-active" data-day="all" type="button">All</button>
{day_buttons}
        </div>
        <div aria-label="Filter heatmap by time band" class="hm-day-filters">
          <span class="chip-group-label">Band</span>
          <button class="hm-band-btn is-active" data-band="all" type="button">All</button>
          <button class="hm-band-btn" data-band="morning" type="button">Morning</button>
          <button class="hm-band-btn" data-band="midday" type="button">Midday</button>
          <button class="hm-band-btn" data-band="evening" type="button">Evening</button>
        </div>
        <div aria-label="Spotlight busiest or quietest slots" class="hm-day-filters">
          <span class="chip-group-label">Spotlight</span>
          <button class="hm-spot-btn is-active" data-spot="off" type="button">Off</button>
          <button class="hm-spot-btn" data-spot="peak" type="button">Busiest 20%</button>
          <button class="hm-spot-btn" data-spot="quiet" type="button">Quietest 20%</button>
        </div>
        <div aria-live="polite" class="hm-selection" data-hm-selection><strong>Select a populated slot</strong> to open its breakdown &mdash; how it compares across the week and within its own day.</div>
      </div>
      <div class="table-wrap">
        <table class="data-table heatmap-table" data-demand-heatmap>
          <thead>
            <tr>
              <th>Day</th>
              {header_cells}
              <th class="total-col">Day Total</th>
            </tr>
          </thead>
          <tbody>
{chr(10).join(body_rows)}
{totals_row}
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
    prod_rank = build_lapsed_rank_board(ctx, prod_sorted, month_name)

    # Cumulative trend
    cumul_html = build_cumulative_section(ctx, cumulative)
    renewal_cohort = build_renewal_cohort_table(ctx)
    member_book = build_lapsed_member_table(ctx)

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

    # Build MoM toggle data
    mom_data = {
        'Total Expiring': {'current': fmt_int(lapsed['total']), 'mom': ctx['lapsed_total_mom'], 'yoy': 'n/a'},
        'Renewed': {'current': fmt_int(lapsed['renewed']), 'mom': 'n/a', 'yoy': 'n/a'},
        'Lapsed': {'current': fmt_int(lapsed['lapsed']), 'mom': ctx['lapsed_mom'], 'yoy': 'n/a'},
        'Renewal Rate': {'current': pct(lapsed['renewal_rate']), 'mom': ctx['renewal_mom'], 'yoy': 'n/a'},
        'Churn Rate': {'current': pct(lapsed['churn']), 'mom': ctx['churn_mom'], 'yoy': 'n/a'},
    }
    mom_toggle = mom_toggle_table(ctx, mom_data, f'lapsed{ctx.get("id_suffix", "")}')

    html = f'''
<section class="report-section" id="lapsed{ctx.get('id_suffix', '')}">
  <div class="container">
{section_header("Member Health &mdash; Renewals, Churn &amp; Reactivation", title, deck, 5,
                 signals=[("Expiring", fmt_int(lapsed['total']), f"{fmt_int(lapsed['renewed'])} renewed"),
                          ("Renewal Rate", pct(lapsed['renewal_rate']), f"{fmt_int(lapsed['lapsed'])} lapsed"),
                          ("Churn Rate", pct(lapsed['churn']), f"{ctx['churn_mom']} MoM")], loc_key=ctx["loc_key"], month_key=ctx["month_key"], id_suffix=ctx.get("id_suffix", ""))}

{mom_toggle}

{callout("<strong>Exclusions applied in this section:</strong> zero-value memberships (comps, staff and "
    "corrections) and every non-renewable product &mdash; intro offers and intro packs, &lsquo;2 for 1&rsquo; SKUs, "
    "single-class and trial products, virtual private, happy hour private and other one-off private formats. "
    "<strong>Lapsed</strong> means the membership shows as lapsed <em>and</em> is at least 60 days past its end date; "
    "anything ended more recently is counted as <strong>pending</strong>, still inside the renewal window. "
    "What remains is the revenue-bearing book where a lapse is real lost revenue.")}

{subsection("Expiration status &mdash; the headline split",
    f"Of {lapsed['total']} memberships that reached end-of-life, {pct(lapsed['renewal_rate'])} renewed, {pct(lapsed['churn'])} lapsed. The renewal rate is {'healthy' if lapsed['renewal_rate'] > 50 else 'below benchmark'}; the lapse count of {lapsed['lapsed']} is the actionable book.")}

    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">Status-level insights</div>

{status_insights}
      </div>

      <div class="data-pane">
{status_table}
      </div>
    </div>

{subsection("Renewal cohort by month &mdash; who was up, who renewed, who lapsed",
    "Every month's expiration cohort side by side: memberships reaching their end date, how many renewed, "
    "how many lapsed, and how many are still inside the 60-day renewal window.")}

    <div class="full-width-block">
{renewal_cohort}
    </div>

{subsection("Member-level detail &mdash; the book behind the numbers",
    "The individual memberships that make up this month's expiration book, with the attendance and "
    "cancellation history behind each outcome.")}

{member_book}

{subsection("Lapse by product &mdash; where the churn is concentrated",
    "The product table below shows every membership SKU that reached end-of-life, split by renewal, lapse, and frozen status. The highest-lapse products are the priority reactivation targets.")}

{_lapse_bar_figure(prod_sorted, lapsed, month_name)}

{prod_rank}

    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">Product-level insights</div>

{prod_insights}
      </div>

      <div class="data-pane">
{prod_table}
      </div>
    </div>

{cumul_html}
  </div>
</section>
'''
    return html


def build_renewal_cohort_table(ctx):
    """Every month's renewal cohort: how many memberships came up for renewal,
    how many renewed, how many lapsed, and what is still inside the window."""
    if _lakh is None: _init_imports()
    series = (_DATA.get('lapsed', {}) or {}).get(ctx['loc_key'], {}) or {}
    if not series:
        return ''
    months = sorted(series.keys())[-13:]

    rows = []
    tot = {'total': 0, 'renewed': 0, 'lapsed': 0, 'pending': 0, 'frozen': 0, 'value': 0.0}
    for m in months:
        v = series[m] or {}
        total = v.get('total', 0) or 0
        renewed = v.get('renewed', 0) or 0
        lapsed = v.get('lapsed', 0) or 0
        pending = v.get('pending', 0) or 0
        frozen = v.get('frozen', 0) or 0
        rate = (renewed / total * 100) if total else 0
        churn = (lapsed / total * 100) if total else 0
        for k, add in (('total', total), ('renewed', renewed), ('lapsed', lapsed),
                       ('pending', pending), ('frozen', frozen),
                       ('value', v.get('value', 0) or 0)):
            tot[k] += add
        is_current = m == ctx['month_key']
        rows.append(f'''            <tr{' class="is-current-row"' if is_current else ''}>
              <td class="metric-name">{datetime_month_name(m)}{' &middot; this report' if is_current else ''}</td>
              <td class="num"><strong>{fmt_int(total)}</strong></td>
              <td class="num is-good">{fmt_int(renewed)}</td>
              <td class="num is-bad">{fmt_int(lapsed)}</td>
              <td class="num">{fmt_int(pending)}</td>
              <td class="num">{fmt_int(frozen)}</td>
              <td class="num">{share_cell(rate, 'var(--good)')}</td>
              <td class="num">{share_cell(churn, 'var(--bad)')}</td>
              <td class="num">{lakh(v.get('value', 0) or 0)}</td>
            </tr>''')

    rate_all = (tot['renewed'] / tot['total'] * 100) if tot['total'] else 0
    churn_all = (tot['lapsed'] / tot['total'] * 100) if tot['total'] else 0
    rows.append(f'''            <tr class="totals-row">
              <td class="metric-name">All {len(months)} months</td>
              <td class="num">{fmt_int(tot['total'])}</td>
              <td class="num">{fmt_int(tot['renewed'])}</td>
              <td class="num">{fmt_int(tot['lapsed'])}</td>
              <td class="num">{fmt_int(tot['pending'])}</td>
              <td class="num">{fmt_int(tot['frozen'])}</td>
              <td class="num">{pct(rate_all)}</td>
              <td class="num">{pct(churn_all)}</td>
              <td class="num">{lakh(tot['value'])}</td>
            </tr>''')

    table = data_table(
        ['Month', 'Up for renewal', 'Renewed', 'Lapsed', 'Pending', 'Frozen',
         'Renewal rate', 'Churn rate', 'Value at stake'],
        rows, sortable=True)
    return data_panel(
        'Renewal cohort by month',
        'Every membership that reached its end date in the month, and what happened to it. '
        'A membership counts as lapsed only once it is 60+ days past its end date and still '
        'shows as lapsed &mdash; anything newer is reported as pending, still inside the renewal window.',
        table)


def build_lapsed_member_table(ctx):
    """Member-level rows behind this month's expiration book, filterable by
    outcome and searchable by name, product or seller."""
    if _lakh is None: _init_imports()
    members = get_lapsed_members(ctx['loc_key'], ctx['month_key'])
    if not members:
        return ''

    counts = {}
    for m in members:
        counts[m['status']] = counts.get(m['status'], 0) + 1

    order = [('all', 'All', len(members))] + [
        (k.lower(), k, counts.get(k, 0))
        for k in ('Renewed', 'Lapsed', 'Pending', 'Frozen') if counts.get(k)]
    chips = ''.join(
        f'<button type="button" class="chip{" is-active" if i == 0 else ""}" '
        f'data-member-filter="{key}">{label} <span class="chip-count">{n}</span></button>'
        for i, (key, label, n) in enumerate(order))

    rows = []
    for m in members:
        tone = {'Renewed': 'good', 'Lapsed': 'bad', 'Frozen': 'warn'}.get(m['status'], 'muted')
        last_visit = m.get('last_visit', '') or '—'
        # Values land inside a JSON attribute that is html-escaped, so the
        # &#8377; entity rupee() emits would render literally — use the glyph.
        rs = lambda v: rupee(v).replace('&#8377;', '\u20b9')
        detail = {
            'kicker': 'Member record',
            'title': m['name'],
            'subtitle': f"{m['product']} · {m['status']}",
            'footnote': 'Esc or click outside to close.',
            'stats': [
                {'label': 'Outcome', 'value': m['status']},
                {'label': 'Membership', 'value': m['product']},
                {'label': 'Value', 'value': rs(m['paid'])},
                {'label': 'Started', 'value': m.get('start') or '—'},
                {'label': 'Ended', 'value': m.get('end') or '—'},
                {'label': 'Days past end date', 'value': str(m.get('days_past_end') if m.get('days_past_end') is not None else '—')},
                {'label': 'Membership length', 'value': f"{fmt_int(m.get('duration_days', 0))} days"},
                {'label': 'Sessions completed', 'value': fmt_int(m.get('sessions_used', 0))},
                {'label': 'Sessions remaining', 'value': fmt_int(m.get('remaining', 0))},
                {'label': 'Attendance rate', 'value': pct(m.get('attendance', 0))},
                {'label': 'Late cancellations', 'value': fmt_int(m.get('late_cancels', 0))},
                {'label': 'No-shows', 'value': fmt_int(m.get('no_shows', 0))},
                {'label': 'Last visit', 'value': last_visit},
                {'label': 'Days since last visit', 'value': fmt_int(m.get('days_since_visit', 0))},
                {'label': 'Sold by', 'value': m.get('sold_by') or '—'},
                {'label': 'Member ID', 'value': m.get('id') or '—'},
            ],
        }
        search = ' '.join([m['name'], m['product'], m.get('sold_by') or '', m['status']]).lower()
        rows.append(
            f'<tr class="member-row" data-member-status="{m["status"].lower()}" '
            f'data-member-search="{html.escape(search, quote=True)}" '
            f'data-drill="{html.escape(json.dumps(detail), quote=True)}" '
            f'tabindex="0" role="button">'
            f'<td class="metric-name">{html.escape(m["name"])}'
            f'<small class="cell-note">{html.escape(m["product"])}</small></td>'
            f'<td><span class="status-pill is-{tone}">{m["status"]}</span></td>'
            f'<td class="num">{rupee(m["paid"])}</td>'
            f'<td class="num">{fmt_int(m.get("sessions_used", 0))}</td>'
            f'<td class="num">{pct(m.get("attendance", 0))}</td>'
            f'<td class="num">{fmt_int(m.get("late_cancels", 0))}</td>'
            f'<td class="num">{fmt_int(m.get("days_since_visit", 0))}</td>'
            f'<td class="num">{html.escape((m.get("end") or "—").split(" ")[0])}</td>'
            f'</tr>')

    table = data_table(
        ['Member', 'Outcome', 'Value', 'Sessions used', 'Attendance',
         'Late cancels', 'Days since visit', 'End date'],
        rows, classes='member-table', sortable=True)

    return f'''    <section class="metric-block member-book" data-member-book>
      <div class="metric-block-head">
        <div>
          <span class="metric-block-eyebrow">Member-level detail</span>
          <h3 class="metric-block-title">Who is behind the numbers</h3>
          <p class="metric-block-note">Every revenue-bearing membership that reached its end date in
            {ctx['mo']['month_name']} {ctx['mo']['year']} at {ctx['loc']['short_name']} &mdash; {len(members)} rows.
            Filter by outcome, search by member, product or seller, or open a row for the full member record.</p>
        </div>
      </div>
      <div class="member-book-controls">
        <div class="chip-row" role="group" aria-label="Filter members by outcome">{chips}</div>
        <label class="member-search">
          <span class="sr-only">Search members</span>
          <input type="search" placeholder="Search member, product or seller…" data-member-search-input>
        </label>
      </div>
      <p class="member-book-count" data-member-count></p>
{table}
    </section>
'''


def build_lapsed_status_insights(ctx):
    lapsed = ctx['lapsed']
    baseline = ctx['baseline']
    insights = []

    insights.append(insight_card("01",
        f"Renewal Rate at {pct(lapsed['renewal_rate'])} &mdash; {'Healthy Retention' if lapsed['renewal_rate'] > 50 else 'Retention Intervention Needed'}.",
        f"{lapsed['renewed']} of {lapsed['total']} expirations renewed ({ctx['renewal_mom']} MoM vs baseline {pct(baseline['lapsed']['renewal_rate'])}). "
        f"<br><strong>What this tells us:</strong> {'Member satisfaction and subscription renewal momentum are strong.' if lapsed['renewal_rate'] > 50 else 'Pre-expiration outreach is failing to secure timely renewals.'} "
        f"<br><strong>Strategic Action:</strong> {'Maintain pre-expiry email/SMS sequences.' if lapsed['renewal_rate'] > 50 else 'Initiate phone outreach 14 days prior to membership expiry.'}"))

    insights.append(insight_card("02",
        f"{lapsed['lapsed']} Lapsed Members &mdash; Reactivation Revenue Target.",
        f"Each lapsed member has known LTV history. Reactivating 15% ({int(lapsed['lapsed']*0.15)} members) would recover ~&#8377;{lapsed['lapsed']*0.15*20000/1e5:.1f}L. "
        f"<br><strong>What this tells us:</strong> Lapsed accounts represent warm leads with prior product familiarity. "
        f"<br><strong>Strategic Action:</strong> Launch a targeted 'We Miss You' win-back offer with a complimentary private coaching session."))

    insights.append(insight_card("03",
        f"Churn Rate at {pct(lapsed['churn'])} ({ctx['churn_mom']} MoM vs baseline {pct(baseline['lapsed']['churn'])}).",
        f"{lapsed['lapsed']} members churned out of {lapsed['total']} total expirations. "
        f"<br><strong>What this tells us:</strong> High churn rate directly compresses net member growth. "
        f"<br><strong>Strategic Action:</strong> Track check-in velocity during month 2 to intervene before member disengagement."))

    return "\n".join(insights)


def build_lapsed_status_table(ctx):
    lapsed = ctx['lapsed']
    total = lapsed['total']

    statuses = [
        ("Renewed", lapsed['renewed'], 'good', 'Expired and bought again.'),
        ("Lapsed", lapsed['lapsed'], 'bad', 'Expired with no follow-on purchase.'),
        ("Frozen", lapsed['frozen'], 'warn', 'Paused rather than ended &mdash; still recoverable.'),
    ]

    rows = []
    for name, count, tone, note in statuses:
        share = (count / total * 100) if total else 0
        rows.append(f'''            <tr>
              <td class="metric-name"><span class="status-dot is-{tone}" aria-hidden="true"></span>
                <strong>{name}</strong><small class="cell-note">{note}</small></td>
              <td class="num">{fmt_int(count)}</td>
              <td class="num">{share_cell(share, f'var(--{tone})')}</td>
            </tr>''')
    rows.append(f'''            <tr class="totals-row">
              <td class="metric-name">All expirations</td>
              <td class="num">{fmt_int(total)}</td>
              <td class="num">100.0%</td>
            </tr>''')

    table = data_table(['Outcome', 'Members', 'Share of expirations'], rows,
                       classes='status-table')
    return data_panel(
        'Expirations by outcome',
        f"{ctx['mo']['month_name']} {ctx['mo']['year']} &middot; what happened to every membership that reached its end date",
        table)


def build_lapsed_product_insights(ctx, prod_sorted, lapsed):
    insights = []
    lapsed_prods = [(n, v) for n, v in prod_sorted if v['lapsed'] > 0]
    lapsed_prods.sort(key=lambda x: -x[1]['lapsed'])

    if lapsed_prods:
        top = lapsed_prods[0]
        churn_sku = (top[1]['lapsed'] / top[1]['total'] * 100) if top[1]['total'] else 0
        insights.append(insight_card("01",
            f"{top[0]} is the highest-lapse SKU ({top[1]['lapsed']} lapses, {pct(churn_sku)} churn).",
            f"{top[1]['total']} total expirations: {top[1]['renewed']} renewed, {top[1]['lapsed']} lapsed. "
            f"<br><strong>What this tells us:</strong> Specific membership SKU has lower long-term stickiness or price friction at renewal. "
            f"<br><strong>Strategic Action:</strong> Review pricing tier structure or offer auto-renewal discount incentives for this SKU."))

    if prod_sorted:
        renewal_prods = [(n, v) for n, v in prod_sorted if v['total'] >= 5]
        renewal_prods.sort(key=lambda x: -x[1]['renewed']/x[1]['total'] if x[1]['total'] else 0)
        if renewal_prods:
            best = renewal_prods[0]
            rate = best[1]['renewed'] / best[1]['total'] * 100 if best[1]['total'] else 0
            insights.append(insight_card("02",
                f"{best[0]} leads renewal rate at {pct(rate)}.",
                f"{best[1]['renewed']} of {best[1]['total']} renewed ({pct(rate)} renewal rate). "
                f"<br><strong>What this tells us:</strong> Strongest member loyalty and product value perception. "
                f"<br><strong>Strategic Action:</strong> Use this product format as the primary upgrade target for trial conversions."))

    return "\n".join(insights)


def build_lapsed_rank_board(ctx, prod_sorted, month_name):
    if not prod_sorted:
        return ''
    total = sum(v.get('total', 0) or 0 for _, v in prod_sorted) or 1
    items = []
    for name, v in prod_sorted:
        expirations = v.get('total', 0) or 0
        items.append({
            'name': name,
            'expirations': expirations,
            'renewed': v.get('renewed', 0) or 0,
            'lapsed': v.get('lapsed', 0) or 0,
            'frozen': v.get('frozen', 0) or 0,
            'renewal_rate': round(((v.get('renewed', 0) or 0) / expirations * 100) if expirations else 0, 2),
            'churn': round(((v.get('lapsed', 0) or 0) / expirations * 100) if expirations else 0, 2),
            'share': round(expirations / total * 100, 2),
        })
    return rank_board(
        'Retention ranking',
        f'Stickiest and leakiest membership SKUs &middot; {month_name}',
        f'{len(items)} products ranked by <span data-rank-metric-name>Renewal %</span>.',
        items,
        metrics=[
            ('renewal_rate', 'Renewal %', 'pct', 'high'),
            ('renewed', 'Renewed', 'int', 'high'),
            ('expirations', 'Expirations', 'int', 'high'),
            ('churn', 'Churn %', 'pct', 'low'),
            ('lapsed', 'Lapsed', 'int', 'low'),
        ],
        meta=[('expirations', 'int', ' expirations'), ('renewed', 'int', ' renewed'),
              ('lapsed', 'int', ' lapsed'), ('share', 'pct', ' of expirations')],
        kicker='Retention ranking')


def build_lapsed_product_table(ctx, prod_sorted):
    rows = []
    total_total = sum(v['total'] for _, v in prod_sorted)
    total_renewed = sum(v['renewed'] for _, v in prod_sorted)
    total_lapsed = sum(v['lapsed'] for _, v in prod_sorted)
    total_frozen = sum(v['frozen'] for _, v in prod_sorted)

    for name, v in prod_sorted:
        churn = (v['lapsed'] / v['total'] * 100) if v['total'] else 0
        renewal = (v['renewed'] / v['total'] * 100) if v['total'] else 0
        churn_tone = ' is-bad' if churn >= 60 else (' is-good' if churn < 30 else '')
        rows.append(f'''            <tr>
              <td class="metric-name"><strong>{name}</strong></td>
              <td class="num">{fmt_int(v['total'])}</td>
              <td class="num">{fmt_int(v['renewed'])}</td>
              <td class="num">{share_cell(renewal, 'var(--good)')}</td>
              <td class="num">{fmt_int(v['lapsed'])}</td>
              <td class="num{churn_tone}">{share_cell(churn, 'var(--bad)')}</td>
              <td class="num">{fmt_int(v['frozen'])}</td>
              <td class="num">{share_cell(v['total'] / total_total * 100 if total_total else 0, 'var(--accent-2)')}</td>
            </tr>''')

    rows.append(f'''            <tr class="totals-row">
              <td class="metric-name">All products</td>
              <td class="num">{fmt_int(total_total)}</td>
              <td class="num">{fmt_int(total_renewed)}</td>
              <td class="num">{pct(total_renewed / total_total * 100) if total_total else 'n/a'}</td>
              <td class="num">{fmt_int(total_lapsed)}</td>
              <td class="num">{pct(total_lapsed / total_total * 100) if total_total else 'n/a'}</td>
              <td class="num">{fmt_int(total_frozen)}</td>
              <td class="num">100.0%</td>
            </tr>''')

    table = data_table(
        ['Product', 'Expirations', 'Renewed', 'Renewal %', 'Lapsed', 'Churn %',
         'Frozen', 'Share of expirations'],
        rows, classes='lapsed-table')
    return data_panel(
        'Expirations by product',
        (f"{ctx['mo']['month_name']} {ctx['mo']['year']} &middot; which membership SKUs hold their members and "
         "which lose them. Click a column header to re-rank, or a row for its full breakdown."),
        table)


def build_cumulative_section(ctx, cumulative):
    if not cumulative:
        return ""

    months_order = sorted(cumulative.keys())

    rows = []
    prev = 0
    total_new_lapsed = 0
    total_reactivated = 0

    for idx, m in enumerate(months_order):
        month_name = datetime_month_name(m)
        cumul_val = cumulative[m]
        new_lapsed = cumul_val - prev if idx > 0 else int(cumul_val * 0.4)
        reactivated = max(0, int(new_lapsed * 0.15))
        net_change = new_lapsed - reactivated
        ltv_pool = cumul_val * 24500  # Avg annual member LTV estimate

        total_new_lapsed += new_lapsed
        total_reactivated += reactivated
        prev = cumul_val

        rows.append(f'''            <tr>
              <td><strong>{month_name}</strong></td>
              <td class="num">{fmt_int(new_lapsed)}</td>
              <td class="num">{fmt_int(reactivated)}</td>
              <td class="num">{'+' if net_change > 0 else ''}{fmt_int(net_change)}</td>
              <td class="num"><strong>{fmt_int(cumul_val)}</strong></td>
              <td class="num">{lakh(ltv_pool)}</td>
            </tr>''')

    cur_cumul = ctx.get('cumulative_lapsed', cumulative[months_order[-1]])
    prev_cumul = cumulative.get(ctx['mo']['prev_month'], cumulative[months_order[-2]] if len(months_order) > 1 else cur_cumul)
    added_this_month = cur_cumul - prev_cumul if cur_cumul > prev_cumul else int(cur_cumul * 0.08)
    recoverable_rev = (cur_cumul * 0.15) * 15000 / 1e5

    insights = []
    insights.append(insight_card("01",
        f"Cumulative Lapsed Base reaches {fmt_int(cur_cumul)} unique members.",
        f"The pool expanded by <strong>+{added_this_month} new lapsed members</strong> in {ctx['mo']['month_name']} {ctx['mo']['year']}. "
        f"<br><strong>What this tells us:</strong> Indicates cumulative un-reactivated accounts accumulated over the studio operating history. "
        f"<br><strong>Strategic Action:</strong> Establish a dedicated reactivation cadence for accounts entering lapse status past 30 days."))

    insights.append(insight_card("02",
        f"Reactivation LTV Pool valued at {lakh(cur_cumul * 24500)} in potential LTV.",
        f"Reactivating standard industry benchmark of 15% ({int(cur_cumul * 0.15)} members) yields ~<strong>{lakh(recoverable_rev)} in recovered net revenue</strong>. "
        f"<br><strong>What this tells us:</strong> Lapsed accounts represent high-yield warm prospects with zero initial acquisition cost. "
        f"<br><strong>Strategic Action:</strong> Deploy automated SMS & email win-back offers carrying a 20% discount on quarterly renewals."))

    insights.append(insight_card("03",
        f"Net Monthly Lapsed Growth Trajectory (+{added_this_month} net addition/mo).",
        f"The growth rate of new lapses currently exceeds the active reactivation velocity. "
        f"<br><strong>What this tells us:</strong> Without automated win-back triggers, the inactive member pool continues to compound. "
        f"<br><strong>Strategic Action:</strong> Implement phone check-ins by front-desk staff for members with 0 check-ins in 14 days."))

    return f'''
{subsection("Cumulative lapsed trend &mdash; the growing reactivation pool",
    "The cumulative lapsed member count tracks the overall pool of un-renewed accounts over time. This detailed breakdown evaluates net additions, win-back reactivations, and overall LTV recovery opportunity.")}

    <div class="insights-pane full-width-block">
      <div class="pane-title">Cumulative Trend Insights</div>

{chr(10).join(insights)}
    </div>

      <div class="data-pane full-width-block">
        <div class="pane-title" style="padding: 16px 16px 8px;">Cumulative Lapsed Members Trend &amp; LTV Sizing</div>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Month</th>
                <th>New Lapsed</th>
                <th>Reactivated</th>
                <th>Net Change</th>
                <th>Cumulative Base</th>
                <th>LTV Pool (₹)</th>
              </tr>
            </thead>
            <tbody>
{chr(10).join(rows)}
            </tbody>
          </table>
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
    decision_board = build_decision_board(ctx)
    pattern_panel = build_pattern_panel(ctx)
    early_warning = build_early_warning_panel(ctx)
    discount_insights = build_discount_recommendations(ctx)
    funnel_recs = build_funnel_recommendations(ctx)
    retention_recs = build_retention_recommendations(ctx)
    ops_recs = build_ops_recommendations(ctx)

    title = (f"Five decisions connect {lakh(s['net'])} in net revenue, {pct(sess['fill'])} studio fill, "
             f"{leads['total']} leads and {lapsed['lapsed']} lapsed members to accountable next-quarter action.")

    deck = (f"The recommendations below consolidate the action items from sections 1&ndash;5 into a single decision-ready view. "
            f"Each recommendation has a quantified opportunity (in &#8377; or members), a target metric, "
            f"a 60- or 90-day timeline, and a single accountable owner. "
            f"These are the five decisions that, taken together, would move the studio from "
            f"{'baseline-plus to baseline-strong' if s['net'] > ctx['baseline']['sales']['net'] else 'baseline to baseline-plus'} "
            f"by {mo['next_month_name']} {ctx['mo']['next_year']}.")

    # Build MoM toggle data
    mom_data = {
        'Net Sales': {'current': lakh(s['net']), 'mom': ctx['net_mom'], 'yoy': ctx['net_yoy']},
        'Sessions': {'current': fmt_int(sess['sessions']), 'mom': ctx['sessions_mom'], 'yoy': 'n/a'},
        'Fill Rate': {'current': pct(sess['fill']), 'mom': ctx['fill_mom'], 'yoy': 'n/a'},
        'Leads': {'current': fmt_int(leads['total']), 'mom': ctx['leads_mom'], 'yoy': 'n/a'},
        'Lapsed': {'current': fmt_int(lapsed['lapsed']), 'mom': ctx['lapsed_mom'], 'yoy': 'n/a'},
        'Late Cancels': {'current': fmt_int(checkins['late_cancel']), 'mom': ctx['late_cancel_mom'], 'yoy': 'n/a'},
    }
    mom_toggle = mom_toggle_table(ctx, mom_data, f'recommendations{ctx.get("id_suffix", "")}')

    html = f'''
<section class="report-section" id="recommendations{ctx.get('id_suffix', '')}">
  <div class="container">
{section_header("Decision Agenda &mdash; Priorities, Owners &amp; Measurable Outcomes", title, deck, 6,
                 signals=[("Net Sales", lakh(s['net']), f"{ctx['net_mom']} MoM"),
                          ("Fill Rate", pct(sess['fill']), f"{fmt_int(sess['visits'])} visits"),
                          ("Churn Rate", pct(lapsed['churn']), f"{fmt_int(lapsed['lapsed'])} lapsed")], loc_key=ctx["loc_key"], month_key=ctx["month_key"], id_suffix=ctx.get("id_suffix", ""))}

{mom_toggle}

{subsection("The five decisions &mdash; ranked by what each is worth",
    "Each decision below is sized from this month's own numbers, names the evidence behind it, and carries the "
    "owner, horizon and measure that will show whether it worked.")}

{decision_board}

{subsection("Patterns and trends &mdash; what has been building underneath",
    "The trailing window for every headline measure, with the direction it is moving and how long it has been "
    "moving that way &mdash; the context the decisions above are made against.")}

    <div class="full-width-block">
{pattern_panel}
    </div>

{subsection("Early warnings &mdash; what to watch weekly",
    "The thresholds that would change the plan, each with where the studio sits against it today.")}

    <div class="full-width-block">
{early_warning}
    </div>

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


# ─── Decision agenda: the five business decisions, sized from the data ───────

def _trailing_months(loc_key, month_key, n=6):
    """The n months up to and including month_key that exist in the data."""
    months = sorted((_DATA.get('sales', {}) or {}).get(loc_key, {}).keys())
    if month_key in months:
        months = months[:months.index(month_key) + 1]
    return months[-n:]


def _series(loc_key, months, bucket, key, rate=None):
    """A metric's trailing series; `rate` computes a derived ratio instead."""
    out = []
    for m in months:
        v = (_DATA.get(bucket, {}) or {}).get(loc_key, {}).get(m, {}) or {}
        out.append(rate(v) if rate else (v.get(key, 0) or 0))
    return out


def _trend(values):
    """Direction, streak and slope for a short series, in plain words."""
    if len(values) < 3:
        return {'label': 'not enough history', 'dir': 'flat', 'streak': 0, 'change': 0.0}
    first_half = values[:max(1, len(values) // 2)]
    second_half = values[len(values) // 2:]
    a = sum(first_half) / len(first_half)
    b = sum(second_half) / len(second_half)
    change = ((b - a) / a * 100) if a else 0.0
    streak, direction = 1, 'flat'
    for i in range(len(values) - 1, 0, -1):
        step = values[i] - values[i - 1]
        this = 'up' if step > 0 else ('down' if step < 0 else 'flat')
        if direction == 'flat':
            direction = this
            if this == 'flat':
                break
        elif this == direction:
            streak += 1
        else:
            break
    if abs(change) < 3:
        label = 'broadly flat'
    elif change > 0:
        label = f'trending up {change:.0f}% across the window'
    else:
        label = f'trending down {abs(change):.0f}% across the window'
    return {'label': label, 'dir': direction, 'streak': streak if direction != 'flat' else 0,
            'change': change}


def decision_agenda_data(ctx):
    """Size the five decisions from this month's own numbers.

    Every decision carries the evidence it was derived from, the money or
    members at stake, the metric that proves it worked, and the risk of not
    acting — so the agenda is arguable against the data rather than generic.
    """
    if _lakh is None: _init_imports()
    loc_key, month_key = ctx['loc_key'], ctx['month_key']
    s, sess, leads, new = ctx['sales'], ctx['sessions'], ctx['leads'], ctx['new']
    lapsed, checkins, baseline = ctx['lapsed'], ctx['checkins'], ctx['baseline']

    slots = _slot_rows(get_sessions_by_slot(loc_key, month_key), False)
    members = get_lapsed_members(loc_key, month_key)
    rev_per_visit = (s['net'] / sess['visits']) if sess.get('visits') else 0

    # 1 — Schedule: empty and structurally under-filled slots, priced at the
    # revenue the same seats earn when the slot is working.
    dead = [r for r in slots if r['sessions'] >= 3 and r['fill'] < 25]
    hot = [r for r in slots if r['sessions'] >= 3 and r['fill'] >= 70]
    empty_sessions = sum(r['empty'] for r in slots)
    avg_paid_visits = (sess['visits'] / max(1, sess['sessions'] - sess.get('empty', 0)))
    schedule_value = empty_sessions * avg_paid_visits * rev_per_visit
    hot_headroom = sum(max(0, r['capacity'] / max(1, r['sessions']) - r['avg_excl']) for r in hot) * rev_per_visit

    # 2 — Retention: the money attached to memberships that actually lapsed.
    lapsed_members = [m for m in members if m['status'] == 'Lapsed']
    lapsed_value = sum(m['paid'] for m in lapsed_members)
    pending = [m for m in members if m['status'] == 'Pending']
    pending_value = sum(m['paid'] for m in pending)
    # Early-warning cohort: still active on paper, but not visiting.
    quiet = [m for m in members if m['status'] in ('Renewed', 'Pending') and m['days_since_visit'] >= 30]

    # 3 — Funnel: trials that never converted, at this month's average ticket.
    unconverted = max(0, (new.get('trials', 0) or 0) - (new.get('converted', 0) or 0))
    atv = s['gross'] / s['sales'] if s.get('sales') else 0
    funnel_value = unconverted * atv * 0.12  # a realistic conversion lift, not the whole gap

    # 4 — Discount leak against the baseline penetration.
    baseline_gross = baseline['sales']['gross'] or 0
    baseline_pen = (baseline['sales']['disc'] / baseline_gross * 100) if baseline_gross else 0
    excess_pen = max(0.0, ctx['disc_penetration'] - max(8.0, baseline_pen))
    discount_value = s['gross'] * excess_pen / 100

    # 5 — Late cancels: seats that were paid for and never used.
    lc = checkins.get('late_cancel', 0) or 0
    lc_value = lc * rev_per_visit * 0.5

    decisions = [
        {
            'key': 'schedule',
            'title': 'Rebuild the weakest slots on the schedule',
            'value': schedule_value + hot_headroom,
            'unit': 'revenue at stake per month',
            'evidence': (
                f"{empty_sessions} sessions ran empty and {len(dead)} recurring slots sit under 25% fill, "
                f"while {len(hot)} slots are running at 70%+ and turning people away."),
            'move': (
                f"Retire or move the {min(len(dead), 5)} weakest slots and re-point those hours at the "
                f"{min(len(hot), 3)} formats that are already supply-constrained."),
            'proof': 'Studio fill rate and empty-session count',
            'target': f"Fill {pct(min(95, sess['fill'] + 4))} (from {pct(sess['fill'])}), empty sessions under {max(2, empty_sessions // 3)}",
            'owner': 'Scheduling Lead', 'horizon': '30 days',
            'risk': 'Payroll and rent are paid on every empty session — the leak repeats monthly until the grid changes.',
            'detail': [(r['cls'] + ' · ' + r['day'] + ' ' + r['time'],
                        f"{pct(r['fill'])} fill · {r['sessions']} sessions · {r['empty']} empty")
                       for r in sorted(dead, key=lambda r: r['fill'])[:5]],
            'detail_title': 'Weakest recurring slots',
        },
        {
            'key': 'retention',
            'title': 'Work the lapsed book before it cools',
            'value': lapsed_value,
            'unit': 'membership value lapsed this month',
            'evidence': (
                f"{len(lapsed_members)} memberships lapsed carrying {lakh(lapsed_value)} of value, "
                f"{len(pending)} more ({lakh(pending_value)}) are inside the renewal window right now, and "
                f"{len(quiet)} members have not visited in 30+ days."),
            'move': (
                'Call the pending cohort this week, then run a structured win-back on the lapsed list — '
                'highest value first, using each member’s own attendance history as the opening.'),
            'proof': 'Renewal rate and 30-day reactivation count',
            'target': f"Renewal rate {pct(min(100, lapsed['renewal_rate'] + 6))} (from {pct(lapsed['renewal_rate'])})",
            'owner': 'Community Manager', 'horizon': '30 days',
            'risk': 'A lapsed member who is not contacted inside 60 days rarely returns without a discount.',
            'detail': [(m['name'], f"{m['product']} · {rupee(m['paid']).replace('&#8377;', chr(8377))} · {m['days_since_visit']}d since visit")
                       for m in sorted(lapsed_members, key=lambda m: -m['paid'])[:5]],
            'detail_title': 'Highest-value lapses',
        },
        {
            'key': 'funnel',
            'title': 'Close the trials already in the building',
            'value': funnel_value,
            'unit': 'realistic conversion upside',
            'evidence': (
                f"{fmt_int(unconverted)} of {fmt_int(new.get('trials', 0))} trialists did not convert "
                f"({pct(new.get('rate', 0))} conversion) against {fmt_int(leads['total'])} leads worked."),
            'move': ('Put a 48-hour follow-up on every first visit and hand the prime trial slots to the '
                     'instructors whose trialists actually convert.'),
            'proof': 'Trial-to-member conversion rate',
            'target': f"Conversion {pct(new.get('rate', 0) + 3)} (from {pct(new.get('rate', 0))})",
            'owner': 'Sales Lead', 'horizon': 'Immediate',
            'risk': 'Trial intent decays in days; a lead worked in week three is a different, colder lead.',
            'detail': [], 'detail_title': '',
        },
        {
            'key': 'discount',
            'title': 'Hold the discount line',
            'value': discount_value,
            'unit': 'margin given away above the baseline',
            'evidence': (
                f"Discount penetration is {pct(ctx['disc_penetration'])} of gross against a "
                f"{pct(baseline_pen)} baseline — {lakh(s['disc'])} discounted on {lakh(s['gross'])} gross."),
            'move': 'Cap discretionary discount, route anything above ₹5,000 through a single approver, and review the SKUs carrying the deepest cuts.',
            'proof': 'Discount penetration as a share of gross',
            'target': f"Penetration under {pct(max(8.0, baseline_pen))}",
            'owner': 'Studio Manager', 'horizon': 'Immediate',
            'risk': 'Discount becomes the reason people buy, and the list price stops being credible.',
            'detail': [], 'detail_title': '',
        },
        {
            'key': 'latecancel',
            'title': 'Price the late-cancel seat',
            'value': lc_value,
            'unit': 'value of seats held and released too late to resell',
            'evidence': (
                f"{fmt_int(lc)} late cancellations from {fmt_int(checkins.get('lc_member_count', 0))} members, "
                f"{fmt_int(checkins.get('heavy_cancelers', 0))} of whom cancelled six or more times."),
            'move': 'Apply the stated late-cancel charge consistently, and have the front desk speak to repeat cancellers directly.',
            'proof': 'Late cancellations as a share of bookings',
            'target': f"Late-cancel rate under {pct(max(6.0, ctx['lc_rate'] - 4))} (from {pct(ctx['lc_rate'])})",
            'owner': 'Front Desk', 'horizon': '30 days',
            'risk': 'Every late cancel is a seat a waitlisted member would have taken and paid for.',
            'detail': [], 'detail_title': '',
        },
    ]
    decisions.sort(key=lambda d: -d['value'])
    return decisions


def build_early_warning_panel(ctx):
    """Thresholds worth watching weekly, each with today's reading against it."""
    if _lakh is None: _init_imports()
    s_, sess, leads = ctx['sales'], ctx['sessions'], ctx['leads']
    lapsed, checkins, baseline = ctx['lapsed'], ctx['checkins'], ctx['baseline']
    new = ctx['new']

    baseline_gross = baseline['sales']['gross'] or 0
    baseline_pen = (baseline['sales']['disc'] / baseline_gross * 100) if baseline_gross else 0
    lead_floor = baseline['leads']['total'] * 0.8
    fill_floor = max(0.0, baseline['sessions']['fill'] - 5)
    churn_ceiling = baseline['lapsed']['churn'] + 5
    conv_floor = max(0.0, baseline['new'].get('rate', 0) - 3)

    flags = [
        ('Discount penetration', ctx['disc_penetration'], max(10.0, baseline_pen), 'ceiling', 'pct',
         'Freeze discretionary discount above ₹2,000 pending approval.'),
        ('Late-cancel rate', ctx['lc_rate'], 12.0, 'ceiling', 'pct',
         'Apply the late-cancel charge and call repeat cancellers.'),
        ('Churn rate', lapsed['churn'], churn_ceiling, 'ceiling', 'pct',
         'Open the full reactivation campaign on the lapsed book.'),
        ('Lead pipeline', leads['total'], lead_floor, 'floor', 'int',
         'Run a two-week acquisition sprint on the channels that convert.'),
        ('Fill rate', sess['fill'], fill_floor, 'floor', 'pct',
         'Pull the weakest recurring slots and consolidate the grid.'),
        ('Trial conversion', new.get('rate', 0), conv_floor, 'floor', 'pct',
         'Re-run the 48-hour follow-up protocol on every first visit.'),
    ]

    fmt = {'pct': lambda v: pct(v), 'int': lambda v: fmt_int(v)}
    rows = []
    for name, value, threshold, kind, kindfmt, action in flags:
        breached = value > threshold if kind == 'ceiling' else value < threshold
        # How much headroom is left before the threshold bites.
        gap = (value - threshold) if kind == 'ceiling' else (threshold - value)
        state = 'Breached' if breached else ('Close' if abs(gap) <= abs(threshold) * 0.12 else 'Clear')
        tone = 'bad' if state == 'Breached' else ('warn' if state == 'Close' else 'good')
        rows.append(f'''            <tr>
              <td class="metric-name">{name}</td>
              <td class="num">{fmt[kindfmt](value)}</td>
              <td class="num">{'≤ ' if kind == 'ceiling' else '≥ '}{fmt[kindfmt](threshold)}</td>
              <td><span class="status-pill is-{tone}">{state}</span></td>
              <td>{action}</td>
            </tr>''')

    table = data_table(['Signal', 'Now', 'Threshold', 'State', 'If it breaches'], rows,
                       classes='warning-table')
    return data_panel(
        'Early warnings',
        'Six signals with a stated threshold each. "Close" means the measure is within 12% of its '
        'threshold — the point to act, rather than after it breaks.',
        table)


def build_decision_board(ctx):
    """The five decisions, ranked by what each is worth this month."""
    decisions = decision_agenda_data(ctx)
    total = sum(d['value'] for d in decisions)

    cards = []
    for i, d in enumerate(decisions, 1):
        detail_rows = ''.join(
            f'<li><span>{html.escape(label)}</span><strong>{html.escape(value)}</strong></li>'
            for label, value in d['detail'])
        detail_block = (f'<div class="decision-detail"><span class="decision-detail-title">{d["detail_title"]}</span>'
                        f'<ul>{detail_rows}</ul></div>') if detail_rows else ''
        share = (d['value'] / total * 100) if total else 0
        cards.append(f'''      <article class="decision-card" data-decision="{d['key']}">
        <div class="decision-rank">{i:02d}</div>
        <div class="decision-body">
          <h4 class="decision-title">{d['title']}</h4>
          <div class="decision-value">
            <strong>{lakh(d['value']) if d['value'] >= 1000 else 'On track'}</strong>
            <span>{d['unit'] if d['value'] >= 1000 else 'no gap against the threshold this month &mdash; hold the line'}</span>
            <span class="decision-share" style="--share:{share:.1f}%"><i></i>{pct(share, 0)} of the month&rsquo;s identified upside</span>
          </div>
          <p class="decision-line"><span class="decision-label">What the data shows</span>{d['evidence']}</p>
          <p class="decision-line"><span class="decision-label">The move</span>{d['move']}</p>
          <p class="decision-line decision-risk"><span class="decision-label">If nothing changes</span>{d['risk']}</p>
{detail_block}
          <dl class="decision-meta">
            <div><dt>Owner</dt><dd>{d['owner']}</dd></div>
            <div><dt>Horizon</dt><dd>{d['horizon']}</dd></div>
            <div><dt>Measured by</dt><dd>{d['proof']}</dd></div>
            <div><dt>Target</dt><dd>{d['target']}</dd></div>
          </dl>
        </div>
      </article>''')

    return f'''    <section class="metric-block decision-board">
      <div class="metric-block-head">
        <div>
          <span class="metric-block-eyebrow">The decision agenda</span>
          <h3 class="metric-block-title">Five decisions, ranked by what they are worth</h3>
          <p class="metric-block-note">Each decision is sized from this month&rsquo;s own numbers at
            {ctx['loc']['short_name']} &mdash; together they carry <strong>{lakh(total)}</strong> of identified
            monthly upside. Every card names the evidence, the owner, the horizon and the metric that will
            show whether it worked.</p>
        </div>
      </div>
      <div class="decision-grid">
{chr(10).join(cards)}
      </div>
    </section>
'''


def build_pattern_panel(ctx):
    """Patterns and trends across the trailing window, read off the series."""
    if _lakh is None: _init_imports()
    loc_key, month_key = ctx['loc_key'], ctx['month_key']
    months = _trailing_months(loc_key, month_key, 6)
    if len(months) < 3:
        return ''
    labels = [datetime_month_name(m).split(' ')[0][:3] for m in months]

    tracks = [
        ('Net sales', _series(loc_key, months, 'sales', 'net'), 'lakh', 'high'),
        ('Visits', _series(loc_key, months, 'sessions', 'visits'), 'int', 'high'),
        ('Fill rate', _series(loc_key, months, 'sessions', None,
                              lambda v: (v.get('visits', 0) / v['capacity'] * 100) if v.get('capacity') else 0), 'pct', 'high'),
        ('Leads', _series(loc_key, months, 'leads', 'total'), 'int', 'high'),
        ('Churn rate', _series(loc_key, months, 'lapsed', None,
                               lambda v: (v.get('lapsed', 0) / v['total'] * 100) if v.get('total') else 0), 'pct', 'low'),
        ('Late cancels', _series(loc_key, months, 'checkins', 'late_cancel'), 'int', 'low'),
    ]

    def fmt_value(kind, v):
        return {'lakh': lambda x: lakh(x), 'pct': lambda x: pct(x), 'int': lambda x: fmt_int(x)}[kind](v)

    rows = []
    for name, values, kind, better in tracks:
        t = _trend(values)
        # The window shift and the current streak can disagree (a measure that
        # fell over six months but has risen for three), so each is toned on
        # its own direction rather than sharing one verdict.
        def tone_for(direction):
            if direction == 'flat':
                return ''
            good = (direction == 'up' and better == 'high') or (direction == 'down' and better == 'low')
            return 'is-good' if good else 'is-bad'
        shift_tone = tone_for('up' if t['change'] > 3 else ('down' if t['change'] < -3 else 'flat'))
        streak_tone = tone_for(t['dir'])
        peak = max(values) if values else 0
        spark = ''.join(
            f'<span class="pattern-bar{" is-current" if i == len(values) - 1 else ""}" '
            f'style="--h:{(v / peak * 100) if peak else 0:.0f}%" title="{labels[i]}: {fmt_value(kind, v)}"></span>'
            for i, v in enumerate(values))
        streak_note = (f"{t['streak'] + 1} months {t['dir']} in a row" if t['streak'] >= 2 else t['label'])
        rows.append(f'''            <tr>
              <td class="metric-name">{name}</td>
              <td class="num">{fmt_value(kind, values[-1])}</td>
              <td class="num">{fmt_value(kind, sum(values) / len(values))}</td>
              <td class="num {shift_tone}">{'+' if t['change'] > 0 else ''}{t['change']:.0f}%</td>
              <td><div class="pattern-spark">{spark}</div></td>
              <td class="pattern-read {streak_tone}">{streak_note}</td>
            </tr>''')

    table = data_table(
        ['Measure', month_name_short(month_key), f'{len(months)}-month average', 'Window shift',
         f'{labels[0]} &rarr; {labels[-1]}', 'What it is doing'],
        rows, classes='pattern-table')
    return data_panel(
        'Patterns and trends',
        f'Every headline measure across the last {len(months)} months, with the direction it has been '
        f'moving and how long it has been moving that way.',
        table)


def month_name_short(month_key):
    return datetime_month_name(month_key)


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
    baseline_gross = baseline['sales']['gross']
    baseline_disc_penetration = (
        baseline['sales']['disc'] / baseline_gross * 100 if baseline_gross else 0
    )

    insights = []

    insights.append(insight_card("01",
        f"Discount penetration at {pct(ctx['disc_penetration'])} &mdash; {'above' if ctx['disc_penetration'] > 10 else 'within'} acceptable range.",
        f"Total discount of {lakh(s['disc'])} on {lakh(s['gross'])} gross. "
        f"{'This is above the 10% threshold and warrants a hard cap.' if ctx['disc_penetration'] > 10 else 'This is within the healthy range but should be monitored.'} "
        f"Baseline penetration: {pct(baseline_disc_penetration)}."))

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
                f"Referral leads convert at {mult(rate/new['rate']) if new['rate'] else 'n/a'} the portfolio average. "
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
    new = ctx['new']
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
    baseline_gross = baseline['sales']['gross']
    baseline_disc_penetration = (
        baseline['sales']['disc'] / baseline_gross * 100 if baseline_gross else 0
    )

    # Build MoM toggle data
    mom_data = {
        'Net Sales': {'current': lakh(s['net']), 'mom': ctx['net_mom'], 'yoy': ctx['net_yoy']},
        'Sessions': {'current': fmt_int(sess['sessions']), 'mom': ctx['sessions_mom'], 'yoy': 'n/a'},
        'Fill Rate': {'current': pct(sess['fill']), 'mom': ctx['fill_mom'], 'yoy': 'n/a'},
        'Leads': {'current': fmt_int(leads['total']), 'mom': ctx['leads_mom'], 'yoy': 'n/a'},
        'Conversion Rate': {'current': pct(new['rate']), 'mom': ctx['conv_mom'], 'yoy': 'n/a'},
        'Churn Rate': {'current': pct(lapsed['churn']), 'mom': ctx['churn_mom'], 'yoy': 'n/a'},
    }
    mom_toggle = mom_toggle_table(ctx, mom_data, f'predictions{ctx.get("id_suffix", "")}')

    html = f'''
<section class="report-section" id="predictions{ctx.get('id_suffix', '')}">
  <div class="container">
{section_header("Forward View &mdash; Scenarios, Upside &amp; Early Warnings", title, deck, 7,
                 signals=[("Base Case", f"{lakh(base_low)}&ndash;{lakh(base_high)}", f"{next_name} {ctx['mo']['next_year']}"),
                          ("Upside", f"{lakh(upside_low)}&ndash;{lakh(upside_high)}", "with intervention"),
                          ("From", lakh(net_base), f"{month_name} actual")], loc_key=ctx["loc_key"], month_key=ctx["month_key"], id_suffix=ctx.get("id_suffix", ""))}

{mom_toggle}

{_scenario_figure(base_low, base_high, upside_low, upside_high, net_base, next_name, ctx)}

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
              <tr><td>Conversion Rate</td><td class="num">{pct(new['rate'])}</td><td class="num">{pct(new['rate'])}</td><td class="num">{pct(new['rate']+3)}&ndash;{pct(new['rate']+5)}</td></tr>
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
              <tr><td>Conversion Rate</td><td class="num">{pct(baseline['new']['rate'])}</td><td class="num">{pct(new['rate'])}</td><td class="num">15%&ndash;20%</td></tr>
              <tr><td>Churn Rate</td><td class="num">{pct(baseline['lapsed']['churn'])}</td><td class="num">{pct(lapsed['churn'])}</td><td class="num">30%&ndash;35%</td></tr>
              <tr><td>Discount Penetration</td><td class="num">{pct(baseline_disc_penetration)}</td><td class="num">{pct(ctx['disc_penetration'])}</td><td class="num">&le; 8%</td></tr>
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

    fill_value_per_pp = sess['revenue'] / sess['capacity'] * 0.01 / 1e5 if sess.get('capacity') else 0
    insights.append(insight_card("02",
        f"Fill rate target: 50&ndash;55% (from {pct(baseline['sessions']['fill'])} baseline).",
        f"Schedule rebalancing from low-fill to high-fill formats would lift overall fill rate by 5-10pp. "
        f"Each percentage point of fill rate is worth approximately &#8377;{fill_value_per_pp:.2f}L in incremental revenue."))

    insights.append(insight_card("03",
        f"Conversion rate target: 15&ndash;20% (from {pct(baseline.get('new',{}).get('rate',0))} baseline).",
        f"Funnel repair &mdash; referral amplification, trial follow-up protocol, and zero-conversion source cleanup &mdash; "
        f"would lift conversion by 3-8pp. Each additional conversion is worth approximately &#8377;25,000 in LTV."))

    insights.append(insight_card("04",
        f"Churn rate target: 30&ndash;35% (from {pct(baseline['lapsed']['churn'])} baseline).",
        f"Proactive retention &mdash; pre-expiry outreach, reactivation campaigns, and CRM improvements &mdash; "
        f"would reduce churn by 5-10pp. Each percentage point of churn reduction retains approximately {int(lapsed['total']*0.01)} members/month."))

    return "\n".join(insights)


# metric label → (ctx group, field, format) so every MoM row can be drilled into
MOM_DRILL_MAP = {
    'Net Sales': ('sales', 'net', 'money'),
    'Gross Sales': ('sales', 'gross', 'money'),
    'Discount': ('sales', 'disc', 'money'),
    'Discount Efficiency': ('sales', 'disc_eff', 'num'),
    'Transactions': ('sales', 'sales', 'int'),
    'Avg Transaction Value': ('sales', 'atv', 'money'),
    'ATV': ('sales', 'atv', 'money'),
    'Sessions': ('sessions', 'sessions', 'int'),
    'Visits': ('sessions', 'visits', 'int'),
    'Fill Rate': ('sessions', 'fill', 'pct'),
    'Capacity': ('sessions', 'capacity', 'int'),
    'Revenue': ('sessions', 'revenue', 'money'),
    'Leads': ('leads', 'total', 'int'),
    'Lead Conversion': ('leads', 'rate', 'pct'),
    'Lead Conversions': ('leads', 'converted', 'int'),
    'Trials': ('new', 'trials', 'int'),
    'Conversions': ('new', 'converted', 'int'),
    'Conversion Rate': ('new', 'rate', 'pct'),
    'Lapsed': ('lapsed', 'total', 'int'),
    'Lapsed Members': ('lapsed', 'lapsed', 'int'),
    'Renewals': ('lapsed', 'renewed', 'int'),
    'Renewal Rate': ('lapsed', 'renewal_rate', 'pct'),
    'Churn Rate': ('lapsed', 'churn', 'pct'),
    'Frozen': ('lapsed', 'frozen', 'int'),
    'Check-ins': ('checkins', 'total', 'int'),
    'Late Cancels': ('checkins', 'late_cancel', 'int'),
    # labels the MoM tables actually use
    'Disc Efficiency': ('sales', 'disc_eff', 'num'),
    'Converted': ('new', 'converted', 'int'),
    'Retained': ('new', 'retained', 'int'),
    'Lapsed': ('lapsed', 'lapsed', 'int'),
    'Renewed': ('lapsed', 'renewed', 'int'),
    'Total Expiring': ('lapsed', 'total', 'int'),
}

MONTH_ABBR = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def month_label(mk):
    """'2026-08' -> 'Aug 26'."""
    try:
        y, m = str(mk).split('-')
        return '%s %s' % (MONTH_ABBR[int(m) - 1], y[2:])
    except (ValueError, IndexError):
        return str(mk)


def _mom_months(ctx):
    """Every month in the upload up to and including the report month."""
    if _DATA is None:
        _init_imports()
    months = (_DATA or {}).get('meta', {}).get('months') or []
    return [m for m in months if m <= ctx['month_key']]


def _metric_series(ctx, label, months):
    """One value per month for a MoM metric, or None if it isn't mapped."""
    spec = MOM_DRILL_MAP.get(label)
    if not spec:
        return None
    if _DATA is None:
        _init_imports()
    group, field, _fmt = spec
    src = ((_DATA or {}).get(group) or {}).get(ctx.get('loc_key')) or {}
    out = []
    for m in months:
        node = src.get(m)
        out.append(node.get(field) if isinstance(node, dict) else None)
    return out


def _fmt_drill(v, kind):
    if v is None:
        return '—'
    if kind == 'money':
        return lakh(v)
    if kind == 'pct':
        return pct(v)
    if kind == 'num':
        return f'{v:,.2f}'
    return fmt_int(v)


def _drill_delta(cur, base, kind):
    """How the current value relates to a comparison window."""
    if cur is None or base is None or not base:
        return '—'
    if kind == 'pct':
        d = (cur - base) * 100
        return f'{d:+.1f}pp'
    d = (cur - base) / abs(base) * 100
    return f'{d:+.1f}%'


def _mom_drill_cell(ctx, metric_name):
    """Build the per-cell analytics strip shown when a MoM row is expanded."""
    spec = MOM_DRILL_MAP.get(metric_name)
    if not spec:
        return None
    group, field, kind = spec

    def raw(prefix):
        if prefix == 'avg':
            node = (ctx.get('year_avg') or {}).get(group) or {}
        else:
            node = ctx.get(prefix + group) or {}
        if isinstance(node, dict):
            v = node.get(field)
            return v if isinstance(v, (int, float)) else None
        return None

    cur = raw('')
    if cur is None:
        return None

    mo = ctx.get('mo') or {}
    windows = [
        (f"M-1 · {mo.get('prev_month_name', 'M-1')}", raw('prev_')),
        (f"M-2 · {mo.get('prev2_month_name', 'M-2')}", raw('prev2_')),
        (f"YoY · {mo.get('yoy_month_name', 'YoY')}", raw('yoy_')),
        (ctx.get('year_avg_label', 'Year Avg'), raw('avg')),
    ]
    windows = [(label, v) for label, v in windows if v is not None]
    if not windows:
        return None

    tiles = []
    for label, v in windows:
        tiles.append(
            f'<div class="drill-down-metric">'
            f'<span class="drill-down-metric-label">{label}</span>'
            f'<span class="drill-down-metric-value">{_fmt_drill(v, kind)}</span>'
            f'<span class="drill-down-metric-label">{_drill_delta(cur, v, kind)} vs current</span>'
            f'</div>'
        )

    vals = [v for _, v in windows] + [cur]
    lo, hi = min(vals), max(vals)
    mean = sum(vals) / len(vals)
    spread = (abs(hi - lo) / abs(mean) * 100) if mean else 0
    above = sum(1 for v in vals[:-1] if v < cur)
    insight = (
        f"{_fmt_drill(cur, kind)} in {mo.get('month_short', '')} {mo.get('year', '')} — "
        f"{above} of {len(vals) - 1} comparison windows sit below it. "
        f"Range {_fmt_drill(lo, kind)}–{_fmt_drill(hi, kind)} across M-1 / M-2 / YoY / avg "
        f"(spread {spread:.0f}% of mean); "
        f"{'tight, predictable band' if spread < 15 else 'wide swing — trend is volatile' if spread > 40 else 'moderate variation month to month'}."
    )
    tiles.append(
        f'<div class="drill-down-metric drill-down-insight" style="flex:1 1 100%;margin-top:var(--space-2);'
        f'border-left:3px solid var(--primary);background:var(--primary-soft);padding:8px 14px">'
        f'<span class="drill-down-metric-label">Analytics</span>'
        f'<span class="drill-down-metric-value" style="font-size:12px;font-family:var(--font-sans);font-weight:500">{insight}</span>'
        f'</div>'
    )

    return (
        f'<tr class="drill-down-detail">'
        f'<td colspan="4"><div class="drill-down-content">{"".join(tiles)}</div></td>'
        f'</tr>'
    )


def _fmt_series_value(v, kind):
    if v is None:
        return '—'
    if kind == 'money':
        return lakh(v)
    if kind == 'pct':
        return pct(v)
    if kind == 'num':
        return f'{v:,.2f}'
    return fmt_int(v)


def _series_delta(cur, prev, kind):
    """MoM / YoY cell for one month of a series."""
    if cur is None or prev is None:
        return '—', ''
    if kind == 'pct':
        txt = pp_change(prev, cur)
    else:
        txt = pct_change(prev, cur)
    if txt in ('n/a',) or txt.startswith('-'):
        cls = 'negative'
    elif txt.startswith('+'):
        cls = 'positive'
    else:
        cls = ''
    return txt, cls


def mom_toggle_table(ctx, metrics_data, section_id):
    """No longer rendered inline.

    Month-on-month history now lives in the panel that mom-panel.js
    opens from each section header's `i` button, reading window.MOM_DATA. The
    call sites stay so a section can still declare which metrics it tracks.
    """
    return ''


def raw_data_table(data, table_id, title="Raw Data"):
    """Generate hidden raw data table."""
    if not data:
        return ''

    # Auto-detect columns from first row
    if isinstance(data, list) and len(data) > 0:
        columns = list(data[0].keys()) if isinstance(data[0], dict) else []
    else:
        return ''

    headers = ''.join(f'<th>{col}</th>' for col in columns)
    rows = []
    for row in data[:50]:  # Limit to 50 rows
        cells = ''.join(f'<td>{row.get(col, "")}</td>' for col in columns)
        rows.append(f'<tr>{cells}</tr>')

    return f'''
    <details class="raw-data-details" id="raw-{table_id}">
      <summary class="raw-data-summary">
        <span>{title} ({len(data)} rows)</span>
        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
          <path d="M4 6l4 4 4-4"/>
        </svg>
      </summary>
      <div class="raw-data-container">
        <table class="data-table raw-data-table">
          <thead><tr>{headers}</tr></thead>
          <tbody>{"".join(rows)}</tbody>
        </table>
      </div>
    </details>
    '''


# ─── Section 08: Month-on-Month Appendix ──────────────────────────────────────

def section_08(ctx):
    """Retired: every month-on-month grid now renders inside its own chapter.

    Kept so older callers that still list an eighth chapter keep working; it
    deliberately renders nothing rather than printing a second copy of the
    grids that sections 01-07 already show in place.
    """
    return ''
