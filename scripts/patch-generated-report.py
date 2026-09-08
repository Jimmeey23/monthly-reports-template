#!/usr/bin/env python3
"""Patch reports that were generated BEFORE the interaction fixes landed.

Fixes applied in place:
  1. Drill-down child rows render as a horizontal strip instead of stacked cards
  2. The "Month-on-Month Analysis" toggle actually opens its table
     (the .expanded class used to land on the button, while the wrapper is
      collapsed with `max-height: 0`, so nothing ever became visible)
  3. The copilot sends the report's location + month with every question

Per-cell drill-down analytics inside the MoM tables are emitted by the
generator, so those only appear after the report is rebuilt.

Usage:
    python3 scripts/patch-generated-report.py <report.html> [<report2.html> ...]
"""
from __future__ import annotations

import io
import re
import sys

DD_OLD = """.drill-down-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--space-3);
  font-size: 12px;
}

.drill-down-metric {
  display: flex;
  flex-direction: column;
  padding: var(--space-2);
  background: var(--bg-card);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
}"""

DD_NEW = """.drill-down-content {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  align-items: stretch;
  gap: 0;
  font-size: 12px;
  overflow-x: auto;
}

.drill-down-metric {
  display: flex;
  flex-direction: column;
  justify-content: center;
  flex: 1 1 130px;
  min-width: 118px;
  padding: 6px 18px;
  background: transparent;
  border-right: 1px solid var(--border);
}

.drill-down-metric:first-child {
  padding-left: 4px;
}

.drill-down-metric:last-of-type {
  border-right: none;
}

.drill-down-metric[style*="grid-column"] {
  flex: 1 1 100%;
  border-right: none;
  border-top: 1px solid var(--border);
  margin-top: var(--space-2);
  padding-top: var(--space-2);
}"""

CHART_OLD = """.drill-down-chart {
  grid-column: 1 / -1;"""
CHART_NEW = """.drill-down-chart {
  flex: 1 1 100%;"""

MOM_CSS_OLD = ".mom-table-container.expanded {\n  max-height: 800px;\n}"
MOM_CSS_NEW = """.mom-table-container.expanded {
  max-height: 1200px;
}

/* The toggle marks the button; the wrapper is its next sibling — keep both paths working. */
.mom-toggle-btn.expanded + .mom-table-container,
.mom-toggle.expanded + .mom-table-container {
  max-height: 1200px;
}"""

MOM_JS_OLD = """function toggleMoMTable(sectionId) {
  const container = document.getElementById('mom-table-' + sectionId);
  const btn = container?.previousElementSibling;
  if (!container) return;

  const isExpanded = container.style.display !== 'none';
  container.style.display = isExpanded ? 'none' : 'block';
  btn?.setAttribute('aria-expanded', !isExpanded);
  btn?.classList.toggle('expanded', !isExpanded);
}"""

MOM_JS_NEW = """function toggleMoMTable(sectionId) {
  const container = document.getElementById('mom-table-' + sectionId);
  if (!container) return;
  const btn = container.closest('.mom-toggle-wrapper')?.querySelector('.mom-toggle-btn, .mom-toggle')
    || container.previousElementSibling;

  const isExpanded = container.classList.contains('expanded')
    || (container.style.display !== 'none' && container.style.maxHeight !== '0px');

  if (isExpanded) {
    container.classList.remove('expanded');
    container.style.display = 'none';
  } else {
    container.classList.add('expanded');
    container.style.display = 'block';
    container.style.maxHeight = 'none';
  }
  btn?.setAttribute('aria-expanded', String(!isExpanded));
  btn?.classList.toggle('expanded', !isExpanded);
}"""

COPILOT_OLD = "      const sessionId = window.location.pathname.split('/')[2];\n      const response = await fetch('/ai-copilot/' + sessionId, {"
COPILOT_NEW = "      const sessionId = window.location.pathname.split('/')[2];\n      const __ctx = window.__REPORT_CTX__ || {};\n      const response = await fetch('/ai-copilot/' + sessionId, {"
COPILOT_BODY_OLD = "body: JSON.stringify({ prompt })"
COPILOT_BODY_NEW = "body: JSON.stringify({ prompt, loc: __ctx.loc, month: __ctx.month })"


def patch(path: str) -> bool:
    with io.open(path, encoding='utf-8') as fh:
        s = fh.read()
    original = s
    applied = []

    if DD_OLD in s:
        s = s.replace(DD_OLD, DD_NEW, 1)
        applied.append('drill-down rows → horizontal')
    elif '.drill-down-content {' in s and 'display: flex;\n  flex-direction: row;' in s:
        applied.append('drill-down rows already horizontal')

    if CHART_OLD in s:
        s = s.replace(CHART_OLD, CHART_NEW, 1)

    if MOM_CSS_OLD in s:
        s = s.replace(MOM_CSS_OLD, MOM_CSS_NEW, 1)
        applied.append('MoM container opens (css)')

    n_js = s.count(MOM_JS_OLD)
    if n_js:
        # reports contain two copies: one live, one accidentally pasted into the
        # stylesheet (never executed) — patch both so they stay in sync.
        s = s.replace(MOM_JS_OLD, MOM_JS_NEW)
        applied.append('MoM toggle expands the container (js ×%d)' % n_js)

    if COPILOT_BODY_OLD in s and '__REPORT_CTX__' in s:
        if COPILOT_OLD in s:
            s = s.replace(COPILOT_OLD, COPILOT_NEW, 1)
        if COPILOT_BODY_OLD in s:
            s = s.replace(COPILOT_BODY_OLD, COPILOT_BODY_NEW, 1)
        applied.append('copilot sends loc + month')

    # Insight chip inside the drill-down belongs on its own line
    s = s.replace(
        "insights.style.gridColumn = '1 / -1';",
        "insights.style.flex = '1 1 100%';\n        insights.style.marginTop = 'var(--space-2)';",
        1,
    )

    if s == original:
        print('  · %s — nothing to patch' % path)
        return False

    with io.open(path, 'w', encoding='utf-8') as fh:
        fh.write(s)
    print('  ✓ %s — %s' % (path, ', '.join(applied) or 'no changes'))
    return True


def main(argv):
    files = argv[1:]
    if not files:
        print(__doc__)
        return 1
    for f in files:
        patch(f)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
