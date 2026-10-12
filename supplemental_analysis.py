"""Supplied studio-specific evidence rendered with the existing report classes."""
import base64
import html
import json
from pathlib import Path

CONTENT = Path(__file__).resolve().parent / 'report_assets' / 'content'


def render(ctx):
    if ctx.get('loc_key') != 'supreme' or ctx.get('month_key') != '2026-09':
        return ''
    source = json.loads((CONTENT / 'supreme-2026-09.json').read_text())
    suffix = html.escape(ctx.get('id_suffix', ''), quote=True)
    out = [f'<section class="report-section" id="supplied-analysis{suffix}">',
           '<div class="section-hero"><h2 class="section-title">September member and operational intelligence</h2>',
           '<p class="section-deck">Supplied analyses for Supreme HQ, Bandra. These documents state a snapshot of 18 October 2026, later than the date this content was added. Their monthly, year-to-date and lifetime populations differ from the uploaded report data. Figures below are source-reported and have not been reconciled to the report above; interpretations and projected value are not verified causal effects.</p></div>',
           '<div class="subsection"><h3 class="subsection-title">Explore the supplied analyses</h3><ul>']
    for i, report in enumerate(source['reports']):
        out.append(f'<li><a href="#supplied-{i}{suffix}">{html.escape(report["title"])}</a></li>')
    out.append('</ul></div>')
    for i, report in enumerate(source['reports']):
        out.extend([f'<div class="subsection" id="supplied-{i}{suffix}">',
                    f'<h3 class="subsection-title">{html.escape(report["title"])}</h3>',
                    f'<p class="subsection-deck">{html.escape(report["intro"])}</p>',
                    f'<p class="subsection-deck">Source: {html.escape(report["filename"])}</p>',
                    '<div class="appendix-body">' + report['html'] + '</div>', '</div>'])
    out.append('<div class="subsection"><h3 class="subsection-title">Supporting workbooks</h3><p>Original supplied workbooks; source calculations are preserved for inspection. The two performance-review HTML editions are identical and appear once.</p><ul>')
    for file in sorted(CONTENT.glob('Bandra_September_2026*.xlsx')):
        data = base64.b64encode(file.read_bytes()).decode('ascii')
        name = html.escape(file.name, quote=True)
        out.append(f'<li><a download="{name}" href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{data}">{name}</a></li>')
    out.append('</ul></div></section>')
    return ''.join(out)
