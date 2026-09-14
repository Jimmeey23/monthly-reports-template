"""Pull every displayed figure out of a generated report, in document order.

Used as a guard rail when restyling: the redesign may move figures around, but
it must not change, drop or invent any of them.
   usage: python3 scripts/verify/extract_figures.py <report.html> [out.txt]
"""
import io
import re
import sys

html = io.open(sys.argv[1], encoding='utf-8').read()

# drop script/style/svg noise, and the base64 hero images
html = re.sub(r'<script[\s\S]*?</script>', ' ', html)
html = re.sub(r'<style[\s\S]*?</style>', ' ', html)
html = re.sub(r'<svg[\s\S]*?</svg>', ' ', html)

text = re.sub(r'<[^>]+>', '\n', html)
text = text.replace('&nbsp;', ' ').replace('&middot;', '·').replace('&mdash;', '—')
text = re.sub(r'&#\d+;', '', text)

tokens = []
for line in text.split('\n'):
    line = line.strip()
    if not line:
        continue
    for tok in re.findall(r'₹[\d.,]+\s?(?:L|Cr|K)?|[+\-]?\d[\d,]*\.?\d*\s?(?:pp|%)|^\d[\d,]*$', line):
        tokens.append(tok.strip())

out = sys.argv[2] if len(sys.argv) > 2 else '/tmp/figures.txt'
io.open(out, 'w', encoding='utf-8').write('\n'.join(tokens))
print(f'{len(tokens)} figures -> {out}')
