"""Dependency-free inline SVG charts for the generated reports.

Everything here renders to a self-contained <svg> string so a report stays a
single offline file — no chart library, no CDN, no JavaScript. Colours come
from CSS custom properties where possible so charts follow the theme; where a
gradient needs a real colour, `currentColor` is used and the caller sets it.

Values may be None (a month with no data) — those points are skipped rather
than plotted as zero, which would be a lie about the data.
"""

from html import escape

SVG_NS_ATTR = 'xmlns="http://www.w3.org/2000/svg"'


def _clean(values):
    """Coerce to floats, keeping None where there genuinely is no figure."""
    out = []
    for v in values or []:
        try:
            out.append(float(v))
        except (TypeError, ValueError):
            out.append(None)
    return out


def sparkline(values, width=220, height=36, stroke=None, fill=True, last_dot=True,
              labels=None, aria_label=''):
    """A smooth area sparkline. `labels` are used for the dots' <title>s."""
    vals = _clean(values)
    pts = [(i, v) for i, v in enumerate(vals) if v is not None]
    if len(pts) < 2:
        return (f'<svg class="sparkline" viewBox="0 0 {width} {height}" '
                f'preserveAspectRatio="none" role="img" aria-label="{escape(aria_label)}"></svg>')

    ys = [v for _, v in pts]
    lo, hi = min(ys), max(ys)
    span = hi - lo or 1.0
    pad = 3.0
    n = len(vals)

    def x(i):
        return pad + (width - pad * 2) * (i / max(1, n - 1))

    def y(v):
        return height - pad - (height - pad * 2) * ((v - lo) / span)

    coords = [(x(i), y(v)) for i, v in pts]
    line = ' '.join(f'{px:.1f},{py:.1f}' for px, py in coords)

    area = ''
    if fill:
        area = (f'<path d="M{coords[0][0]:.1f},{height} L{line.split()[0]} '
                f'{line} L{coords[-1][0]:.1f},{height} Z" fill="currentColor" opacity="0.13"/>')

    stroke_attr = f' stroke="{stroke}"' if stroke else ''
    dot = ''
    if last_dot:
        lx, ly = coords[-1]
        dot = f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="2.6" fill="currentColor"/>'

    titles = ''
    if labels:
        for (px, py), (i, v) in zip(coords, pts):
            name = labels[i] if i < len(labels) else ''
            titles += f'<circle cx="{px:.1f}" cy="{py:.1f}" r="5" fill="transparent"><title>{escape(str(name))}</title></circle>'

    return (f'<svg class="sparkline" viewBox="0 0 {width} {height}" preserveAspectRatio="none" '
            f'role="img" aria-label="{escape(aria_label)}">{area}'
            f'<polyline points="{line}" fill="none" stroke="currentColor" stroke-width="1.6" '
            f'stroke-linecap="round" stroke-linejoin="round"{stroke_attr}/>{dot}{titles}</svg>')


def bar_series(values, labels=None, width=240, height=76, aria_label=''):
    """A compact column chart with the final column highlighted."""
    vals = _clean(values)
    if not vals:
        return ''
    hi = max(v for v in vals if v is not None) or 1.0
    lo = min((v for v in vals if v is not None), default=0.0)
    base = min(0.0, lo)
    span = (hi - base) or 1.0

    n = len(vals)
    gap = 2.0
    bw = max(2.0, (width - gap * (n - 1)) / n)

    bars = []
    for i, v in enumerate(vals):
        if v is None:
            continue
        h = max(1.5, (v - base) / span * (height - 6))
        bx = i * (bw + gap)
        by = height - h - (0 if base == 0 else (0 - base) / span * (height - 6))
        cls = 'bar is-current' if i == n - 1 else 'bar'
        title = f'<title>{escape(str(labels[i]))}: {v:,.1f}</title>' if labels and i < len(labels) else ''
        bars.append(f'<rect class="{cls}" x="{bx:.1f}" y="{by:.1f}" width="{bw:.1f}" height="{h:.1f}" '
                    f'rx="1.5" fill="currentColor" opacity="{1.0 if i == n - 1 else 0.45}">{title}</rect>')

    return (f'<svg class="bar-chart" viewBox="0 0 {width} {height}" preserveAspectRatio="none" '
            f'role="img" aria-label="{escape(aria_label)}">{"".join(bars)}</svg>')


def donut(segments, size=132, thickness=16, aria_label=''):
    """segments = [(label, value, colour), ...]. Empty segments are dropped."""
    segs = [(l, float(v or 0), c) for l, v, c in segments]
    total = sum(v for _, v, _ in segs)
    if total <= 0:
        return ''

    r = (size - thickness) / 2
    c = size / 2
    circumference = 2 * 3.141592653589793 * r
    offset = 0.0
    arcs = []
    for label, value, colour in segs:
        length = circumference * (value / total)
        # stroke is set through style so CSS custom properties resolve and the
        # chart follows the report theme instead of baking in a hex.
        arcs.append(
            f'<circle cx="{c}" cy="{c}" r="{r:.2f}" fill="none" style="stroke: {colour}" '
            f'stroke-width="{thickness}" stroke-dasharray="{length:.2f} {circumference - length:.2f}" '
            f'stroke-dashoffset="{-offset:.2f}" transform="rotate(-90 {c} {c})">'
            f'<title>{escape(str(label))}: {value / total * 100:.1f}%</title></circle>')
        offset += length

    return (f'<svg class="donut" viewBox="0 0 {size} {size}" role="img" aria-label="{escape(aria_label)}">'
            f'<circle cx="{c}" cy="{c}" r="{r:.2f}" fill="none" stroke="currentColor" '
            f'stroke-width="{thickness}" opacity="0.08"/>{"".join(arcs)}</svg>')


def meter(value, maximum=100.0, width=120, height=6, colour=None):
    """A single progress meter, used inside table cells and stat slabs."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return ''
    pct = 0.0 if not maximum else max(0.0, min(1.0, value / maximum))
    fill_attr = f' fill="{colour}"' if colour else ''
    return (f'<svg class="meter" viewBox="0 0 {width} {height}" preserveAspectRatio="none" aria-hidden="true">'
            f'<rect x="0" y="0" width="{width}" height="{height}" rx="{height / 2}" fill="currentColor" opacity="0.10"/>'
            f'<rect x="0" y="0" width="{width * pct:.1f}" height="{height}" rx="{height / 2}" '
            f'fill="currentColor"{fill_attr}/></svg>')


def bar_list(items, limit=8, value_fmt=lambda v: f'{v:,.0f}'):
    """A ranked horizontal bar list — better than columns when labels are long.

    items = [(label, value), ...]; the largest bar is 100% wide and the rest
    are scaled against it, with the share of the total in the footnote.
    """
    rows = [(label, float(value or 0)) for label, value in (items or [])][:limit]
    if not rows:
        return ''

    total = sum(v for _, v in rows) or 1.0
    largest = max(v for _, v in rows) or 1.0
    out = ['<ul class="bar-list">']
    for i, (label, value) in enumerate(rows):
        width = max(1.5, value / largest * 100)
        share = value / total * 100
        out.append(
            f'<li class="bar-row"><span class="bar-rank">{i + 1:02d}</span>'
            f'<span class="bar-name">{escape(str(label))}</span>'
            f'<span class="bar-track"><i style="width: {width:.1f}%"></i></span>'
            f'<span class="bar-value">{value_fmt(value)}</span>'
            f'<span class="bar-share">{share:.1f}%</span></li>')
    out.append('</ul>')
    return ''.join(out)
