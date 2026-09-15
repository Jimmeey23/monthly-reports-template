#!/usr/bin/env python3
"""Re-inline the current report_assets/report.css into already-generated reports.

A generated report carries its stylesheet inline so it stays portable, which
means a CSS fix does not reach reports that were built before it. This rewrites
the first <style> block — the one the shell fills with report.css — in every
report passed on the command line, leaving the markup and data untouched.

    python3 scripts/refresh-report-css.py uploads/*/*.html *.html
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = open(os.path.join(ROOT, 'report_assets', 'report.css'), encoding='utf-8').read()
BLOCK = re.compile(r'<style>.*?</style>', re.S)


def refresh(path):
    html = open(path, encoding='utf-8').read()
    match = BLOCK.search(html)
    if not match or '.split-grid' not in match.group(0):
        return False, 'no report stylesheet found'
    updated = html[:match.start()] + '<style>\n' + CSS + '\n</style>' + html[match.end():]
    if updated == html:
        return False, 'already current'
    open(path, 'w', encoding='utf-8').write(updated)
    return True, f'{len(match.group(0)):,} -> {len(CSS):,} chars'


if __name__ == '__main__':
    targets = sys.argv[1:]
    if not targets:
        print(__doc__)
        raise SystemExit(2)
    for path in targets:
        try:
            done, note = refresh(path)
        except OSError as err:
            print(f'  ! {path}: {err}')
            continue
        print(('  ✓ ' if done else '  - ') + f'{path}: {note}')
