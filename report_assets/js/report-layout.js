// ─── Adaptive split layouts ─────────────────────────────────────────
// Each two-pane section is measured after render: a table that cannot fit the
// narrow data column first widens that column, and if it still overflows the
// whole section stacks so the table takes the full report width with its
// summary underneath. A pane far taller than its neighbour stops stretching,
// which removes the centred white gap around short tables.
function fitSplitLayout(grid) {
  const data = grid.querySelector(':scope > .data-pane');
  if (!data) return;
  const insights = grid.querySelector(':scope > .insights-pane');
  const overflows = function () {
    let over = false;
    data.querySelectorAll('.table-wrap').forEach(function (w) {
      if (w.scrollWidth > w.clientWidth + 2) over = true;
      // A table that has already been squeezed reports no wrap overflow, so
      // compare what the table wants against what the column gives it.
      w.querySelectorAll('table').forEach(function (t) {
        if (t.scrollWidth > w.clientWidth + 2) over = true;
      });
    });
    return over;
  };

  // A table with this many columns never reads well in a half-width column,
  // whatever it measures at: give it the report's full width up front.
  const WIDE_TABLE_COLUMNS = 7;
  const hasWideTable = function () {
    return Array.prototype.some.call(data.querySelectorAll('table'), function (t) {
      const head = t.tHead && t.tHead.rows[0];
      const cols = head ? head.cells.length : (t.rows[0] ? t.rows[0].cells.length : 0);
      return cols >= WIDE_TABLE_COLUMNS;
    });
  };

  grid.classList.remove('is-wide-data', 'is-stacked', 'is-dense', 'is-dense-2', 'is-loose', 'is-wrapped');
  // Wrapping needs the table ahead of the prose in the DOM; put the panes back
  // in their authored order before measuring anything.
  if (insights && data.previousElementSibling === null && grid.firstElementChild === data) {
    grid.insertBefore(insights, data);
  }
  // Below the single-column breakpoint the CSS already stacks everything.
  if (window.innerWidth <= 1080) return;

  if (hasWideTable()) {
    grid.classList.add('is-stacked');
    if (overflows()) {
      grid.classList.add('is-dense');
      if (overflows()) grid.classList.add('is-dense-2');
    }
  } else if (overflows()) {
    grid.classList.add('is-wide-data');
    if (overflows()) {
      grid.classList.remove('is-wide-data');
      grid.classList.add('is-stacked');
      // Full report width still is not enough: tighten the cells rather than
      // hand the reader a horizontal scrollbar.
      if (overflows()) {
        grid.classList.add('is-dense');
        if (overflows()) grid.classList.add('is-dense-2');
      }
    }
  }

  if (!grid.classList.contains('is-stacked') && insights) {
    // Measure unstretched — while the panes stretch they report equal heights,
    // so the imbalance is only visible with is-loose already applied.
    grid.classList.add('is-loose');
    const a = data.offsetHeight, b = insights.offsetHeight;
    const tall = Math.max(a, b), short = Math.min(a, b);
    const ratio = short > 0 ? tall / short : 1;

    // A summary several times taller than its table means side-by-side leaves
    // one column as a long strip of white. Preferred fix: float the table and
    // let the commentary wrap it, so the prose runs beside the table and then
    // continues at full width once the table ends. If the table cannot render
    // at the floated width, fall back to stacking it full width instead.
    if (tall > 320 && ratio > 1.6) {
      grid.classList.remove('is-loose');
      grid.insertBefore(data, insights);
      grid.classList.add('is-wrapped');
      // Tighten the cells before giving up on the wrap: a slightly denser
      // table that the prose can flow around beats a full-width one that
      // pushes every insight below it.
      if (overflows()) grid.classList.add('is-dense');
      if (overflows()) grid.classList.add('is-dense-2');
      if (overflows()) {
        grid.classList.remove('is-wrapped', 'is-dense', 'is-dense-2');
        grid.insertBefore(insights, data);
        grid.classList.add('is-stacked');
        if (overflows()) {
          grid.classList.add('is-dense');
          if (overflows()) grid.classList.add('is-dense-2');
        }
      }
    } else if (!(tall > 160 && ratio > 1.4)) {
      grid.classList.remove('is-loose');
    }
  }
}

function fitSplitLayouts() {
  document.querySelectorAll('.split-grid').forEach(function (grid) {
    // Hidden sections measure as zero-width; they are re-fitted when shown.
    if (!grid.clientWidth) return;
    fitSplitLayout(grid);
  });
}

let splitFitTimer = null;
function scheduleSplitFit() {
  clearTimeout(splitFitTimer);
  splitFitTimer = setTimeout(fitSplitLayouts, 120);
}

function initSplitLayouts() {
  fitSplitLayouts();
  window.addEventListener('resize', scheduleSplitFit);
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(fitSplitLayouts).catch(function () {});
  }
  // Tab switches, MoM range changes and drill-downs all change table widths.
  document.addEventListener('click', function (e) {
    if (e.target.closest('.location-tab, .mom-metric-tab, .mom-range-btn, .mom-toggle-btn, .tab-btn, td.mom-cell')) {
      scheduleSplitFit();
    }
  }, true);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initSplitLayouts);
} else {
  initSplitLayouts();
}

// Multi-Location Tabs
document.addEventListener('DOMContentLoaded', () => {
  const tabs = document.querySelectorAll('.location-tab');
  const contents = document.querySelectorAll('.location-content');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const targetId = tab.dataset.location;

      tabs.forEach(t => t.classList.remove('active'));
      contents.forEach(c => c.classList.remove('active'));

      tab.classList.add('active');
      document.getElementById('location-' + targetId)?.classList.add('active');
    });
  });

  // Activate first tab by default
  if (tabs.length > 0 && !document.querySelector('.location-tab.active')) {
    tabs[0].click();
  }

  /* The tab bar gets out of the way while the reader scrolls down and comes
     back on scroll-up, on a pointer near the top of the window, or on focus. */
  var bar = document.querySelector('.location-tabs');
  if (!bar) return;
  var peek = document.createElement('div');
  peek.className = 'location-tabs-peek is-armed';
  document.body.appendChild(peek);

  var lastY = window.scrollY;
  var hovering = false;
  var ticking = false;

  function setHidden(hidden) {
    bar.classList.toggle('is-hidden', hidden && !hovering);
  }

  function onScroll() {
    var y = window.scrollY;
    var goingDown = y > lastY + 4;
    var goingUp = y < lastY - 4;
    if (y < 120) setHidden(false);
    else if (goingDown) setHidden(true);
    else if (goingUp) setHidden(false);
    lastY = y;
    ticking = false;
  }

  window.addEventListener('scroll', function () {
    if (!ticking) { requestAnimationFrame(onScroll); ticking = true; }
  }, { passive: true });

  peek.addEventListener('mouseenter', function () { hovering = true; setHidden(false); });
  bar.addEventListener('mouseenter', function () { hovering = true; });
  bar.addEventListener('mouseleave', function () { hovering = false; });
  peek.addEventListener('mouseleave', function () {
    hovering = false;
    if (window.scrollY > 120) setHidden(true);
  });
  bar.addEventListener('focusin', function () { hovering = true; setHidden(false); });
  bar.addEventListener('focusout', function () { hovering = false; });
});
