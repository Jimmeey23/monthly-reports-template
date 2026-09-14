"""Build a working analysis.json from the analysis snapshot in the repo root.

The uploads/ directory (which holds real client data) is not in the repo, so
this reconstructs a runnable analysis from `analysis_v2.json` by adding the
`meta` block the generator needs. Figures are the snapshot's own — nothing is
invented — so reports built from it are only as current as that file.

   usage: python3 scripts/verify/make_demo_analysis.py [out.json]
"""
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, 'analysis_v2.json')
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'preview', 'analysis.json')

NAMES = {'kw': 'Kwality House, Kemps Corner', 'supreme': 'Supreme HQ, Bandra'}

data = json.load(io.open(SRC, encoding='utf-8'))

import re
MONTH_RE = re.compile(r'^\d{4}-\d{2}$')
# keys shaped {loc: {month: {...}}} — `active` is {loc: {total, types}}, so it
# has to be filtered by the month pattern rather than assumed.
PER_MONTH = [k for k, v in data.items()
             if isinstance(v, dict) and any(isinstance(x, dict) for x in v.values())]

locs = sorted({k for section in data.values() if isinstance(section, dict) for k in section})
months = sorted({
    m
    for name in PER_MONTH
    for per_loc in data[name].values() if isinstance(per_loc, dict)
    for m in per_loc if MONTH_RE.match(str(m))
})

data['meta'] = {
    'locations': {k: NAMES.get(k, k) for k in locs},
    'months': months,
    'baseline_months': months[:-1],
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with io.open(OUT, 'w', encoding='utf-8') as f:
    json.dump(data, f)

print(f'{SRC} -> {OUT}')
print(f'  locations: {data["meta"]["locations"]}')
print(f'  months:    {months[0]} .. {months[-1]} ({len(months)})')
