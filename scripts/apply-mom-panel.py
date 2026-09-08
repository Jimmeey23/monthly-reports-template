#!/usr/bin/env python3
"""Rewire the revised July reports so their Month-on-Month tables render as
in-section panels (public/revised-july/mom-panel.js) instead of the overlay
that used to be mounted at the bottom of the document.

Run:  python3 scripts/apply-mom-panel.py
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = [
    os.path.join(ROOT, 'public', 'revised-july', 'kwality-house-july-2026.html'),
    os.path.join(ROOT, 'public', 'revised-july', 'supreme-hq-bandra-july-2026.html'),
]
SCRIPT_TAG = '<script src="/revised-july/mom-panel.js?v=1"></script>'


def cut(s, start_marker, end_marker, label):
    """Delete text from start_marker up to (not including) end_marker."""
    i = s.find(start_marker)
    if i < 0:
        raise SystemExit('missing start marker for %s: %r' % (label, start_marker[:70]))
    j = s.find(end_marker, i)
    if j < 0:
        raise SystemExit('missing end marker for %s: %r' % (label, end_marker[:70]))
    return s[:i] + s[j:]


def sub1(s, pattern, repl, label):
    new, n = re.subn(pattern, repl, s, count=1)
    if n != 1:
        raise SystemExit('pattern did not match for %s: %r' % (label, pattern[:70]))
    return new


def patch(path):
    with io.open(path, encoding='utf-8') as fh:
        original = fh.read()
    s = original
    name = os.path.basename(path)

    if 'mom-panel.js' in s:
        print('  · %s already patched — skipping' % name)
        return False

    # 1. Drop the MoM overlay markup that sat at the bottom of the document.
    mom_overlay = None
    for marker in ('<div aria-hidden="true" class="mom-modal-overlay" id="mom-modal-overlay">',
                   '<div class="mom-modal-overlay" id="mom-modal-overlay">'):
        if marker in s:
            mom_overlay = marker
            break
    if not mom_overlay:
        raise SystemExit('missing MoM overlay markup in %s' % name)
    next_block = None
    for marker in ('<div aria-hidden="true" class="mom-modal-overlay" id="extra-modal-overlay">',
                   '<div aria-hidden="true" class="mom-modal-overlay sales-matrix-overlay"',
                   '<script>\nwindow.MOM_DATA = {'):
        if marker in s[s.find(mom_overlay):]:
            next_block = marker
            break
    if not next_block:
        raise SystemExit('could not find the block after the MoM overlay in %s' % name)
    s = cut(s, mom_overlay, next_block, name + ' · mom overlay')

    # 2. Drop the old MoM modal script (the MOM_DATA payload is kept as-is).
    if 'kwality' in name:
        s = sub1(s, r"\n\(function \(\) \{\n  function fmtCurrency\(n\) \{[\s\S]*?\n\}\)\(\);\n</script>",
                 '\n</script>\n' + SCRIPT_TAG, name + ' · mom script')
    else:
        s = sub1(s, r"\n\(function \(\) \{\n  var modalOverlay = document\.getElementById\('mom-modal-overlay'\);[\s\S]*?\n\}\)\(\);\n\nwindow\.EXTRA_DATA",
                 '\n\nwindow.EXTRA_DATA', name + ' · mom script')

        # 3. Retire the "extra" drill-down overlay — it is now a panel tab.
        s = cut(s, '<div aria-hidden="true" class="mom-modal-overlay" id="extra-modal-overlay">',
                '<div aria-hidden="true" class="mom-modal-overlay sales-matrix-overlay"',
                name + ' · extra overlay')
        s = sub1(s, r"\n\(function \(\) \{\n  var overlay = document\.getElementById\('extra-modal-overlay'\);[\s\S]*?\n\}\)\(\);\n\nwindow\.SALES_CATEGORY_MATRIX",
                 '\n\nwindow.SALES_CATEGORY_MATRIX', name + ' · extra script')

        # 4. Load the shared module after every data block has been defined.
        s = sub1(s, r"\n</script>\n<script src=\"\./section-audio\.js",
                 '\n</script>\n' + SCRIPT_TAG + '\n<script src="./section-audio.js',
                 name + ' · script tag')

    # sanity checks
    for token in ('window.MOM_DATA = {', SCRIPT_TAG):
        if token not in s:
            raise SystemExit('sanity check failed for %s: missing %s' % (name, token))
    if 'openMomModal' in s or 'openExtraModal' in s:
        raise SystemExit('sanity check failed for %s: modal code still present' % name)

    with io.open(path, 'w', encoding='utf-8') as fh:
        fh.write(s)
    print(u'  ✓ %s patched (%d → %d chars)' % (name, len(original), len(s)))
    return True


def main():
    changed = False
    for f in FILES:
        if not os.path.exists(f):
            raise SystemExit('missing file: %s' % f)
        changed = patch(f) or changed
    print('done' if changed else 'no changes needed')


if __name__ == '__main__':
    sys.exit(main())
