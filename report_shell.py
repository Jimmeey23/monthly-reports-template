"""Document shell for generated reports.

Every report — past or future — is emitted with the chrome, stylesheet and
client scripts lifted from the Supreme HQ · Bandra · July 2026 report, which is
the agreed visual reference. Nothing here is per-studio: the studio's name,
figures and copy arrive through `ctx`, so two reports differ only in their data.

Assets live in `report_assets/` and are inlined so a generated file stays
portable: every stylesheet and script is embedded, so a report works opened from
disk with no server behind it. The only runtime fetch a report makes is for its
narration audio, which the app serves from `/audio/`.

`public/report/` holds the same behaviour scripts for the served app; edit those
under `report_assets/js/` and copy them across, since the generator reads the
`report_assets/` copy.
"""
import base64
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, 'report_assets')

# Chapter order, shared by the top nav, the side rail, the footer contents list
# and the anchors each section header prints.
CHAPTERS = [
    ('executive-summary', 'Overview', '01 Executive Summary'),
    ('revenue-performance', 'Revenue', '02 Revenue &amp; Sales Performance'),
    ('conversion-funnel', 'Funnel', '03 New Client Conversion Funnel'),
    ('sessions', 'Sessions', '04 Sessions &amp; Class Performance'),
    ('lapsed', 'Retention', '05 Lapsed Memberships Deep Dive'),
    ('recommendations', 'Actions', '06 Strategic Recommendations'),
    ('predictions', 'Outlook', '07 Predictions &amp; Forward View'),
]

# section number -> the key its `i` button and MoM panel are registered under
MOM_KEYS = {1: 'exec', 2: 'commercial', 3: 'funnel', 4: 'sessions', 5: 'retention'}


def _read(rel):
    with open(os.path.join(ASSETS, rel), 'r', encoding='utf-8') as f:
        return f.read()


def _data_uri(rel, mime):
    with open(os.path.join(ASSETS, rel), 'rb') as f:
        return f'data:{mime};base64,' + base64.b64encode(f.read()).decode('ascii')


CSS = _read('report.css')
LOGO = _data_uri('img/logo.png', 'image/png')
HERO_SLIDES = [
    (_data_uri('img/hero-1.jpg', 'image/jpeg'), 'Motion in focus'),
    (_data_uri('img/hero-2.jpg', 'image/jpeg'), 'PowerCycle after dark'),
    (_data_uri('img/hero-3.jpg', 'image/jpeg'), 'Barre activation · Controlled strength'),
]
HERO_SIDE = (_data_uri('img/hero-side.jpg', 'image/jpeg'), 'Studio portrait · Power and presence')

# inlined in this order; the vendor pair has to land before the exporter that uses it
INLINE_JS = [
    ('theme-toggle', 'js/theme-toggle.js'),
    ('scroll-chrome', 'js/scroll-chrome.js'),
    ('kpi-charts', 'js/kpi-charts.js'),
    ('heatmap-controls', 'js/heatmap-controls.js'),
    ('metric-card-flip', 'js/metric-card-flip.js'),
    ('hero-carousel', 'js/hero-carousel.js'),
    ('subsection-collapse', 'js/subsection-collapse.js'),
    ('report-layout', 'js/report-layout.js'),
    ('table-behaviour', 'js/table-behaviour.js'),
    ('rank-board', 'js/rank-board.js'),
    # after the tables and boards have rendered, so it sees every trigger
    ('drill-modal', 'js/drill-modal.js'),
    ('brand-audio', 'js/brand-audio.js'),
    ('embedded-html2canvas', 'vendor/html2canvas.min.js'),
    ('embedded-jspdf', 'vendor/jspdf.umd.min.js'),
    ('direct-pdf-export', 'js/pdf-export.js'),
    ('mom-panel', 'js/mom-panel.js'),
    ('section-audio', 'js/section-audio.js'),
    ('sfx-soundboard', 'js/sfx-soundboard.js'),
]


def _js(obj):
    """JSON for embedding in a <script> — `</` escaped so it can't close the tag."""
    return json.dumps(obj, ensure_ascii=False).replace('</', '<\\/')


def _attr(obj):
    """JSON for a double-quoted HTML attribute."""
    return (json.dumps(obj, ensure_ascii=False, separators=(',', ':'))
            .replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;'))


def report_meta(ctx):
    """Identity the client scripts read instead of sniffing the URL or title."""
    loc, mo = ctx['loc'], ctx['mo']
    visits = ctx['sessions'].get('visits', 0) or 0
    net = ctx['sales'].get('net', 0) or 0
    slug = f"{loc['short_name']}_{mo['month_name']}_{mo['year']}".replace(' ', '_').replace(',', '')
    return {
        'locKey': ctx['loc_key'],
        'monthKey': ctx['month_key'],
        'shortName': loc['short_name'],
        'revenuePerVisit': round(net / visits) if visits else 0,
        'audioPrefix': loc.get('audio_prefix', ctx['loc_key']),
        'audioBase': '/audio/',
        'speakerNotesUrl': f"/report/notes/{ctx['loc_key']}-{ctx['month_key']}.md",
        'pdfHeader': f"{loc['full_name'].upper()}  /  {mo['month_name'].upper()} {mo['year']}",
        'pdfTitle': f"{loc['full_name']} Performance Report · {mo['month_name']} {mo['year']}",
        'pdfAuthor': f"Physique 57 · {loc['full_name']}",
        'pdfKeywords': f"performance report, studio, {mo['month_name']} {mo['year']}, {loc['short_name']}",
        'pdfFilename': f'{slug}_Board_Report.pdf',
    }


def head(ctx):
    loc, mo = ctx['loc'], ctx['mo']
    return f'''<!DOCTYPE html>
<html data-theme="light" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>{loc['short_name']} · Performance Report · {mo['month_name']} {mo['year']}</title>
<link href="{LOGO}" rel="icon"/>
<link href="https://fonts.googleapis.com" rel="preconnect"/>
<link crossorigin="" href="https://fonts.gstatic.com" rel="preconnect"/>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;family=Source+Serif+Pro:wght@400;600;700&amp;family=JetBrains+Mono:wght@400;500;600&amp;display=swap" rel="stylesheet"/>
<style>
{CSS}
</style>
</head>
<body class="sp-report">
<div class="print-frame"></div>
<script>window.__REPORT_META__ = {_js(report_meta(ctx))};</script>
'''


def topbar(ctx):
    loc, mo = ctx['loc'], ctx['mo']
    nav = ''.join(f'<a href="#{anchor}">{label}</a>' for anchor, label, _ in CHAPTERS)
    return f'''<div class="topbar"><div aria-hidden="true" class="scroll-progress" id="scroll-progress"></div>
<div class="topbar-inner">
<div class="brand">
<img alt="Physique 57 logo" class="brand-logo" src="{LOGO}"/>
<div class="brand-text">
        {loc['short_name']} Pulse
        <small>Performance Report · {mo['month_name']} {mo['year']}</small>
</div>
</div>
<nav aria-label="Report sections" class="topnav">{nav}</nav><div class="topbar-actions">
<button aria-label="Download styled A4 PDF" class="pdf-btn" id="pdf-export-btn" title="Download a fully styled A4 PDF — no print dialog">
<svg fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewbox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" x2="12" y1="15" y2="3"></line></svg>
<span>Download PDF</span>
</button>
<button aria-label="Toggle theme" class="theme-toggle" id="theme-toggle">
<svg fill="none" id="theme-icon" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewbox="0 0 24 24">
<circle cx="12" cy="12" r="4"></circle>
<path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"></path>
</svg>
<span id="theme-label">Dark</span>
</button>
</div>
</div>
</div>
<nav aria-label="Quick section navigation" class="side-quicknav">{''.join(
    f'<a data-label="{label}" href="#{anchor}"><span></span></a>' for anchor, label, _ in CHAPTERS)}</nav>
'''


def marquee(items, label):
    """The scrolling highlight strip. The group is printed twice — the CSS
    animation relies on a duplicate to loop without a visible seam."""
    group = ''.join(f'<span class="marquee-item"><strong>{v}</strong> {k}</span>' for v, k in items)
    return (f'<div aria-label="{label}" class="performance-marquee"><div class="marquee-track">'
            f'<div class="marquee-group">{group}</div><div class="marquee-group">{group}</div>'
            f'</div></div>')


def section_marquee(items, label):
    group = ''.join(f'<span class="marquee-item"><strong>{v}</strong> {k}</span>' for v, k in items)
    return (f'<div aria-label="{label} highlights" class="section-marquee"><div class="marquee-track">'
            f'<div class="marquee-group">{group}</div><div class="marquee-group">{group}</div>'
            f'</div></div>')


def kpi_card(index, card):
    """One metric card: front face with an animated chart, back face with the
    definition, the formula and a button into the item-level drill-down.

    `card` carries label/value/sub/trends/series/baseline/kicker/copy/focus/tip,
    plus optional `definition`, `formula` and `drill`. The same component is
    used for the hero grid and — with `compact` set — for the cards inside
    sections, so the two never drift apart.
    """
    tip_id = f'metric-tip-{index}'
    trends = ''.join(
        f'<span class="kpi-trend"><span class="trend-label">{name}</span> '
        f'<span class="badge {tone}">{value}</span></span>'
        for name, value, tone in card.get('trends', []))
    back_stats = ''.join(
        f'<div class="kpi-back-stat"><span>{name}</span><strong>{value}</strong></div>'
        for name, value in card.get('back_stats', []))
    chart = ''
    if card.get('series'):
        chart = (
            '<div aria-label="Recent metric trend" class="kpi-chart" '
            f'data-chart-type="{card.get("chart_type", "area")}" '
            f'data-decimals="{card.get("decimals", 0)}" data-grouping="{str(card.get("grouping", False)).lower()}" '
            f'data-labels="{card["labels"]}" data-prefix="{card.get("prefix", "")}" '
            f'data-series="{card["series"]}" data-suffix="{card.get("suffix", "")}" '
            'title="Move across the chart to inspect each comparison point"></div>')
    baseline = f'<div class="kpi-baseline">{card["baseline"]}</div>' if card.get('baseline') else ''

    definition = (f'<p class="kpi-back-copy">{card["definition"]}</p>'
                  if card.get('definition') else
                  (f'<p class="kpi-back-copy">{card.get("copy", "")}</p>' if card.get('copy') else ''))
    formula = (f'<div class="kpi-back-formula"><span class="kpi-back-formula-label">How it is calculated</span>'
               f'<code>{card["formula"]}</code></div>') if card.get('formula') else ''
    drill = ''
    if card.get('drill'):
        drill = ('<button class="kpi-drill-btn" type="button" data-drill="'
                 + _attr(card['drill']) + '">Open item-level detail</button>')

    classes = 'kpi-card' + (' is-compact' if card.get('compact') else '')
    tone = card.get('tone')
    if tone:
        classes += ' tone-' + tone

    return f'''<div aria-describedby="{tip_id}" class="{classes}" tabindex="0"><div class="kpi-flip-shell"><div class="kpi-card-inner kpi-face kpi-card-front"><div aria-hidden="true" class="kpi-card-art"><span></span><span></span><span></span></div>
<div class="kpi-label">{card['label']}</div>
<div class="kpi-value">{card['value']}</div>
<div class="kpi-sub">{card.get('sub', '')}</div>
<div class="kpi-trends">
{trends}
</div>
{chart}{baseline}
<div aria-hidden="true" class="kpi-flip-cue">Click for context  ↗</div></div><div class="kpi-card-back kpi-face"><div class="kpi-back-top"><span class="kpi-back-kicker">{card.get('kicker', '')}</span><span aria-hidden="true" class="kpi-back-return">↺</span></div><h3 class="kpi-back-title">{card['label']}</h3>{definition}{formula}<div class="kpi-back-stats">{back_stats}</div><div class="kpi-back-focus"><strong>Management focus · </strong>{card.get('focus', '')}</div>{drill}</div></div><div class="metric-card-tooltip" id="{tip_id}" role="tooltip">{card.get('tip', '')}</div></div>'''


def hero(ctx, headline, sub, meta_items, marquee_items, kpi_cards):
    loc, mo = ctx['loc'], ctx['mo']
    period = f"01 {mo['month_name']} {mo['year']} — {mo['last_day']} {mo['month_name']} {mo['year']}"

    slides = ''
    for i, (src, caption) in enumerate(HERO_SLIDES):
        active = ' is-active' if i == 0 else ''
        cap = f'{loc["short_name"]} · {caption}' if i == 0 else caption
        slides += (f'<div aria-hidden="{"false" if i == 0 else "true"}" class="hero-carousel-slide{active}">'
                   f'<img alt="{cap}" decoding="async" loading="{"eager" if i == 0 else "lazy"}" src="{src}"/>'
                   f'<span class="hero-media-caption">{cap}</span></div>')
    dots = ''.join(
        f'<button aria-current="{"true" if i == 0 else "false"}" aria-label="Show image {i + 1}" '
        f'class="hero-carousel-dot{" is-active" if i == 0 else ""}" type="button"></button>'
        for i in range(len(HERO_SLIDES)))

    meta = ''.join(
        f'<div class="hero-meta-item">\n<span class="label">{label}</span>\n'
        f'<span class="value">{value}</span>\n</div>\n' for label, value in meta_items)
    cards = '\n'.join(kpi_card(i + 1, c) for i, c in enumerate(kpi_cards))

    return f'''<section class="hero">
<div class="container hero-content">
<div class="hero-topline">
<div class="hero-eyebrow">
<img alt="Physique 57 logo" class="hero-logo" src="{LOGO}"/>
      <span>Senior Management Review · Period: {period}</span>
    </div>
<button class="brand-audio-btn hero-audio-btn hero-topline-audio" id="brand-audio-btn" type="button" aria-label="Play Fiz-zeek Fifty-Seven" title="Play Fiz-zeek Fifty-Seven"><span class="hero-audio-icon"><svg aria-hidden="true" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewbox="0 0 24 24"><path d="M9 18V5l11-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="17" cy="16" r="3"></circle></svg></span><span class="hero-audio-copy"><strong>Play Me</strong><small>Fiz-zeek Fifty-Seven</small></span></button>
</div>
<div class="hero-title-with-audio"><h1>{headline}</h1></div>
<p class="hero-sub">{sub}</p><div aria-label="Studio photography" class="hero-media-grid"><figure aria-label="Studio photography carousel" aria-roledescription="carousel" class="hero-media-card hero-media-main hero-carousel"><div class="hero-carousel-viewport">{slides}</div><div class="hero-carousel-controls"><button aria-label="Previous image" class="hero-carousel-button" data-carousel-prev="" type="button">←</button><div aria-label="Choose image" class="hero-carousel-dots">{dots}</div><button aria-label="Next image" class="hero-carousel-button" data-carousel-next="" type="button">→</button></div><div aria-hidden="true" class="hero-carousel-progress"><span></span></div></figure><figure class="hero-media-card hero-media-side"><img alt="{HERO_SIDE[1]}" decoding="async" loading="eager" src="{HERO_SIDE[0]}"/><figcaption class="hero-media-caption">{HERO_SIDE[1]}</figcaption></figure></div>
<div class="hero-meta">
{meta}</div>
{marquee(marquee_items, 'Performance highlights')}<div class="hero-kpi-grid">
{cards}
</div>
</div>
</section>
'''


def footer(ctx, headline_metrics):
    loc, mo = ctx['loc'], ctx['mo']
    contents = '<br/>\n          '.join(item for _, _, item in CHAPTERS)
    metrics = '<br/>\n          '.join(f'{k}: {v}' for k, v in headline_metrics)
    return f'''<footer class="footer">
<div class="container">
<div class="footer-grid">
<div>
<img alt="Physique 57 logo" class="footer-logo" src="{LOGO}"/>
<div class="footer-brand-text">{loc['short_name']} Pulse</div>
<p class="footer-text">
          Performance Report · {mo['month_name']} {mo['year']}<br/>
          Compiled from studio sales, sessions, leads, membership, and check-in records.<br/>
          Net Sales excludes tax; Gross Sales reflects amount collected per transaction.
          Compared against the {ctx['baseline_label']} baseline.
        </p>
</div>
<div>
<div class="footer-label">Contents</div>
<p class="footer-text">
          {contents}<br/>
          A Appendix · Metric Dictionary
        </p>
</div>
<div>
<div class="footer-label">Headline Metrics</div>
<p class="footer-text">
          {metrics}
        </p>
</div>
</div>
</div>
</footer>
'''


def sales_matrix_modal(ctx):
    loc = ctx['loc']
    return f'''<div aria-hidden="true" class="mom-modal-overlay sales-matrix-overlay" id="sales-matrix-overlay">
<div class="mom-modal sales-matrix-modal" role="dialog" aria-modal="true" aria-labelledby="sales-matrix-title" aria-describedby="sales-matrix-description" tabindex="-1">
<div class="mom-modal-beam is-top" aria-hidden="true"></div>
<div class="mom-modal-beam is-left" aria-hidden="true"></div>
<div class="mom-modal-beam is-right" aria-hidden="true"></div>
<div class="mom-modal-head">
<div class="mom-modal-head-left">
<div class="mom-modal-icon" aria-hidden="true"><svg fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewbox="0 0 24 24"><circle cx="12" cy="12" r="8"></circle><path d="M12 8v4l3 3"></path></svg></div>
<div>
<div class="mom-modal-eyebrow" id="sales-matrix-eyebrow">Sales · Full History</div>
<h3 class="mom-modal-title" id="sales-matrix-title">Monthly Sales — Category &amp; Product Detail</h3>
</div>
</div>
<div class="mom-modal-head-right">
<button class="mom-modal-close" id="sales-matrix-close" aria-label="Close">&times;</button>
</div>
</div>
<div class="smx-metric-tabs" id="smx-metric-tabs"></div>
<div class="smx-table-card">
<div class="smx-table-head">
<div class="smx-table-head-left">
<span class="smx-cal-icon" aria-hidden="true"><svg fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewbox="0 0 24 24"><rect height="18" rx="2" width="18" x="3" y="4"></rect><path d="M3 10h18M8 2v4M16 2v4"></path></svg></span>
<div>
<h4>Month-on-Month Analysis</h4>
<p>Comprehensive monthly performance comparison across categories and products</p>
</div>
</div>
<div class="smx-table-head-right">
<span class="smx-badge" id="smx-items-badge"></span>
<div class="smx-seg" id="smx-mode-toggle">
<button class="is-active" data-smx-mode="values" type="button"><svg fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewbox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8Z"></path><circle cx="12" cy="12" r="3"></circle></svg> Values</button>
<button data-smx-mode="growth" type="button"><svg fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewbox="0 0 24 24"><path d="M3 3v18h18"></path><path d="m19 9-5 5-4-4-3 3"></path></svg> Growth</button>
</div>
<button class="smx-action-btn" id="smx-collapse-all" type="button"><svg fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewbox="0 0 24 24"><path d="M4 14h6v6M20 10h-6V4M14 10l7-7M3 21l7-7"></path></svg> Collapse All</button>
<button class="smx-action-btn" id="smx-expand-all" type="button"><svg fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewbox="0 0 24 24"><path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"></path></svg> Expand All</button>
</div>
</div>
<div class="mom-pulse-divider" aria-hidden="true"><span></span></div>
<div class="smx-table-scroll"><table class="mom-table" id="sales-matrix-table"></table></div>
</div>
<div class="mom-modal-foot" id="sales-matrix-description">Figures are computed month-by-month from real {loc['full_name']} transaction records, grouped by category and product.</div>
</div>
</div>
'''


def page_furniture():
    """The two floating widgets the chrome scripts drive: the back-to-top
    button and the PDF exporter's progress dialog."""
    return '''<button aria-label="Back to top" class="back-to-top" id="back-to-top" title="Back to top" type="button"><svg aria-hidden="true" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" viewbox="0 0 24 24"><path d="M12 19V5"></path><path d="m6 11 6-6 6 6"></path></svg></button><div aria-hidden="true" aria-live="polite" class="pdf-export-overlay" id="pdf-export-overlay" role="status">
<div class="pdf-export-dialog">
<div class="pdf-export-mark">
<svg aria-hidden="true" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" viewbox="0 0 24 24"><path d="M12 3v12"></path><path d="m7 10 5 5 5-5"></path><path d="M5 21h14"></path></svg>
</div>
<div class="pdf-export-title">Building your board-ready PDF</div>
<div class="pdf-export-status" id="pdf-export-status">Preparing the A4 document structure…</div>
<div class="pdf-export-progress"><span id="pdf-export-progress-bar"></span></div>
<div class="pdf-export-note">The report is rendered locally in your browser. No data is uploaded, and the download begins automatically.</div>
</div>
</div>
'''


def data_globals(mom_data, extra_data, sales_matrix):
    return (f'<script>\nwindow.MOM_DATA = {_js(mom_data)};\n'
            f'window.EXTRA_DATA = {_js(extra_data)};\n'
            f'window.SALES_CATEGORY_MATRIX = {_js(sales_matrix)};\n</script>\n')


def scripts():
    out = []
    for script_id, rel in INLINE_JS:
        # Namespaced: `theme-toggle` is also the id of the button in the topbar,
        # and a duplicate id makes getElementById a coin toss.
        out.append(f'<script id="rpt-js-{script_id}">\n{_read(rel)}\n</script>')
    return '\n'.join(out) + '\n</body></html>\n'
