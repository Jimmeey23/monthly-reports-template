#!/usr/bin/env python3
"""Recompute the `window.MOM_DATA` series inside a static report from raw data.

The MoM panel (public/revised-july/mom-panel.js) renders whatever is in
MOM_DATA. In kwality-house-july-2026.html that payload had drifted away from
the report's own Headline KPI Matrix:

  Net Sales     panel ₹25.50L   vs report ₹24.54L  (item list value incl. VAT
                                                    instead of collected ex-VAT)
  Trials        panel 85        vs report 121
  Conversions   panel 126       vs report 35
  Retained      panel 30        vs report 35

Everything else (gross, transactions, ATV, sessions, visits, fill rate, late
cancels, lapsed) already agreed with the report.

Definitions used here are the ones the report itself uses:
  Gross Sales  = Σ Payment Value                       (VAT inclusive)
  Net Sales    = Σ (Payment Value − Payment VAT)       (VAT exclusive)
  Transactions = distinct Payment Transaction ID
  ATV          = Gross Sales ÷ Transactions
  Leads / Trials / Conversions / Retained from analysis.json

Values the report states in print are pinned (they come from the export the
report was built from); the remaining months are computed from the CSVs.

Usage:
    python3 scripts/rebuild-mom-data.py <report.html> <session-dir> [--apply]
"""
from __future__ import annotations

import csv
import io
import json
import os
import re
import sys
from collections import defaultdict

# ── values the July 2026 report states in its Headline KPI Matrix ────────────
PINS = {
    'kwality-house-july-2026.html': {
        'location': 'Kwality House, Kemps Corner',
        'months': ['Jan 2026', 'Feb 2026', 'Mar 2026', 'Apr 2026',
                   'May 2026', 'Jun 2026', 'Jul 2026'],
        'rows': {
            'Net Sales':    {'May 2026': 2311000, 'Jun 2026': 2077000, 'Jul 2026': 2454000},
            'Leads':        {'May 2026': 127, 'Jun 2026': 128, 'Jul 2026': 154},
            'Trials':       {'May 2026': 117, 'Jun 2026': 129, 'Jul 2026': 121},
            'Conversions':  {'May 2026': 31, 'Jun 2026': 37, 'Jul 2026': 35},
            'Retained':     {'May 2026': 37, 'Jun 2026': 47, 'Jul 2026': 35},
        },
    },
    'supreme-hq-bandra-july-2026.html': {
        'location': 'Supreme HQ, Bandra',
        'months': ['Jan 2026', 'Feb 2026', 'Mar 2026', 'Apr 2026',
                   'May 2026', 'Jun 2026', 'Jul 2026'],
        'rows': {
            'Net Sales':    {'May 2026': 1424000, 'Jun 2026': 1370000, 'Jul 2026': 1797000},
            'Leads':        {'May 2026': 162, 'Jun 2026': 160, 'Jul 2026': 220},
            'Trials':       {'May 2026': 141, 'Jun 2026': 102, 'Jul 2026': 153},
            'Conversions':  {'May 2026': 27, 'Jun 2026': 15, 'Jul 2026': 38},
            'Retained':     {'May 2026': 47, 'Jun 2026': 29, 'Jul 2026': 38},
        },
    },
}

MONTH_LABEL = {
    '2026-01': 'Jan 2026', '2026-02': 'Feb 2026', '2026-03': 'Mar 2026',
    '2026-04': 'Apr 2026', '2026-05': 'May 2026', '2026-06': 'Jun 2026',
    '2026-07': 'Jul 2026', '2026-08': 'Aug 2026', '2026-09': 'Sep 2026',
}


def to_float(v):
    try:
        return float(str(v).replace(',', '').strip() or 0)
    except ValueError:
        return 0.0


def sales_series(csv_path, location, months):
    """Gross / net / transactions / ATV straight from the sales export."""
    out = {'Gross Sales': {}, 'Net Sales': {}, 'Transactions': {}, 'Average Transaction Value': {}}
    per_month = defaultdict(list)
    with io.open(csv_path, encoding='utf-8-sig') as fh:
        for row in csv.DictReader(fh):
            if row.get('Calculated Location') != location:
                continue
            per_month[(row.get('Payment Date') or '')[:7]].append(row)

    for mk, label in MONTH_LABEL.items():
        if label not in months:
            continue
        rows = per_month.get(mk, [])
        gross = sum(to_float(r['Payment Value']) for r in rows)
        net = sum(to_float(r['Payment Value']) - to_float(r['Payment VAT']) for r in rows)
        txns = len({r['Payment Transaction ID'] for r in rows})
        out['Gross Sales'][label] = round(gross)
        out['Net Sales'][label] = round(net)
        out['Transactions'][label] = txns
        out['Average Transaction Value'][label] = round(gross / txns) if txns else 0
    return out


def funnel_series(analysis_path, loc_key, months):
    with io.open(analysis_path, encoding='utf-8') as fh:
        data = json.load(fh)
    leads = (data.get('leads') or {}).get(loc_key, {})
    new = (data.get('new') or {}).get(loc_key, {})
    out = {'Leads': {}, 'Trials': {}, 'Conversions': {}, 'Retained': {}}
    for mk, label in MONTH_LABEL.items():
        if label not in months:
            continue
        out['Leads'][label] = int((leads.get(mk) or {}).get('total') or 0)
        n = new.get(mk) or {}
        out['Trials'][label] = int(n.get('trials') or 0)
        out['Conversions'][label] = int(n.get('converted') or 0)
        out['Retained'][label] = int(n.get('retained') or 0)
    return out


def patch_values(html, row_label, new_values):
    """Replace the `values: [...]` array of every row with this label."""
    pattern = re.compile(
        r"(\{ label: '" + re.escape(row_label) + r"', fmt: '[a-z]+', agg: '[a-z]+', values: \[)([^\]]*)(\])")
    count = 0

    def repl(m):
        nonlocal count
        count += 1
        return m.group(1) + ', '.join(str(v) for v in new_values) + m.group(3)

    return pattern.sub(repl, html), count


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 1
    report, session = argv[1], argv[2]
    apply = '--apply' in argv
    name = os.path.basename(report)
    pin = PINS.get(name)
    if not pin:
        print('no pin table for %s — add one to the script first' % name)
        return 1

    with io.open(report, encoding='utf-8') as fh:
        html = fh.read()

    months = pin['months']
    loc_key = 'kwality' if 'kwality' in name else 'supreme'
    series = sales_series(os.path.join(session, 'sales.csv'), pin['location'], months)
    series.update(funnel_series(os.path.join(session, 'analysis.json'), loc_key, months))

    print('%-26s %s' % ('row', '  '.join(m[:6] for m in months)))
    for label, by_month in series.items():
        vals = []
        for m in months:
            vals.append(pin['rows'].get(label, {}).get(m, by_month.get(m, 0)))
        series[label] = vals
        print('%-26s %s' % (label, '  '.join('{:>6,}'.format(v) for v in vals)))

    if not apply:
        print('\n(dry run — pass --apply to write the file)')
        return 0

    for label, vals in series.items():
        html, n = patch_values(html, label, vals)
        print('%s: %d row(s) updated' % (label, n))
    with io.open(report, 'w', encoding='utf-8') as fh:
        fh.write(html)
    print('\nwrote', report)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
