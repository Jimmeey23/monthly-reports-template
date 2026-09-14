
(function () {
  'use strict';
  var charts = Array.prototype.slice.call(document.querySelectorAll('.kpi-chart'));
  if (!charts.length) return;
  var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function esc(value) {
    return String(value).replace(/[&<>"']/g, function (char) {
      return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char];
    });
  }
  function buildChart(chart, index) {
    var values = (chart.getAttribute('data-series') || '').split(',').map(Number).filter(Number.isFinite);
    var labels = (chart.getAttribute('data-labels') || '').split('|');
    if (values.length < 2) return;
    var prefix = chart.getAttribute('data-prefix') || '';
    var suffix = chart.getAttribute('data-suffix') || '';
    var decimals = parseInt(chart.getAttribute('data-decimals') || '0', 10);
    var grouping = chart.getAttribute('data-grouping') === 'true';
    var type = chart.getAttribute('data-chart-type') || 'bar';
    var accent = chart.getAttribute('data-chart-accent') === 'danger'
      ? { a: '#f87171', b: '#dc2626', glow: 'rgba(220,38,38,.4)' }
      : { a: '#2E6BD3', b: '#1E3A8A', glow: 'rgba(30,58,138,.4)' };
    var defaultActive = chart.hasAttribute('data-highlight-index') ? parseInt(chart.getAttribute('data-highlight-index'), 10) : values.length - 1;

    /* The card shows a strip, not a plot: no month labels and no gridlines, so
       the bars can fill the box instead of floating above a band of reserved
       space. Exact months stay available on hover via the tooltip. */
    var width = 360, height = 46, top = 3, bottom = 3, left = 6, right = 6;
    var min = Math.min.apply(null, values), max = Math.max.apply(null, values);
    var plotH = height - top - bottom;
    var slotW = (width - left - right) / values.length;
    var gid = 'kpiChart' + index;

    function xCenter(i) { return left + slotW * (i + .5); }
    var guides = '';
    var text = '';
    function formatValue(value) {
      var number = grouping ? value.toLocaleString('en-IN', {minimumFractionDigits: decimals, maximumFractionDigits: decimals}) : value.toFixed(decimals);
      return prefix + number + suffix;
    }

    if (type === 'bar') {
      var baseline = Math.min(0, min);
      var range = (max - baseline) || Math.max(1, Math.abs(max) * .1);
      var barW = Math.min(26, slotW * .38);
      function barTop(value) { return top + (1 - (value - baseline) / range) * plotH; }
      var baseY = top + plotH;
      var bars = values.map(function (value, i) {
        var isActive = i === defaultActive;
        var y = barTop(value);
        var h = Math.max(3, baseY - y);
        var cx = xCenter(i);
        return '<rect class="chart-bar' + (isActive ? ' is-active' : '') + '" data-index="' + i + '" x="' + (cx - barW / 2).toFixed(1) + '" y="' + y.toFixed(1) + '" width="' + barW.toFixed(1) + '" height="' + h.toFixed(1) + '" rx="3" fill="' + (isActive ? 'url(#' + gid + ')' : 'var(--kpi-bar-muted, #cbd5e1)') + '"></rect>';
      }).join('');
      chart.innerHTML = '<svg viewBox="0 0 360 46" preserveAspectRatio="none" role="img" aria-hidden="true"><defs><linearGradient id="' + gid + '" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="' + accent.a + '"></stop><stop offset="100%" stop-color="' + accent.b + '"></stop></linearGradient></defs><line class="chart-baseline" x1="' + left + '" y1="' + baseY.toFixed(1) + '" x2="' + (width - right) + '" y2="' + baseY.toFixed(1) + '"></line>' + guides + bars + text + '</svg><div class="kpi-chart-tooltip"></div>';
      var svg = chart.querySelector('svg');
      var tooltip = chart.querySelector('.kpi-chart-tooltip');
      var barNodes = Array.prototype.slice.call(chart.querySelectorAll('.chart-bar'));
      function activateBar(i, show) {
        barNodes.forEach(function (bar, barIndex) {
          bar.classList.toggle('is-active', barIndex === i);
          bar.setAttribute('fill', barIndex === i ? 'url(#' + gid + ')' : 'var(--kpi-bar-muted, #cbd5e1)');
        });
        tooltip.textContent = formatValue(values[i]);
        tooltip.style.left = (xCenter(i) / width * 100) + '%';
        tooltip.style.top = (barTop(values[i]) / height * 100) + '%';
        tooltip.classList.toggle('is-visible', show);
      }
      activateBar(defaultActive, false);
      svg.addEventListener('pointermove', function (event) {
        var rect = svg.getBoundingClientRect();
        var x = (event.clientX - rect.left) / rect.width * width;
        var closest = 0, distance = Infinity;
        values.forEach(function (value, i) { var d = Math.abs(xCenter(i) - x); if (d < distance) { closest = i; distance = d; } });
        activateBar(closest, true);
      });
      svg.addEventListener('pointerleave', function () { activateBar(defaultActive, false); });
      return;
    }

    // line / area rendering
    var range2 = max - min || Math.max(1, Math.abs(max) * .1);
    var lo = min - range2 * .18, hi = max + range2 * .18, range3 = hi - lo;
    var pts = values.map(function (value, i) {
      return { x: xCenter(i), y: top + (1 - (value - lo) / range3) * plotH };
    });
    function smoothPath(points) {
      var path = 'M ' + points[0].x.toFixed(2) + ' ' + points[0].y.toFixed(2);
      for (var i = 0; i < points.length - 1; i++) {
        var p0 = points[i - 1] || points[i];
        var p1 = points[i], p2 = points[i + 1], p3 = points[i + 2] || p2;
        var t = .22;
        var cp1x = p1.x + (p2.x - p0.x) * t, cp1y = p1.y + (p2.y - p0.y) * t;
        var cp2x = p2.x - (p3.x - p1.x) * t, cp2y = p2.y - (p3.y - p1.y) * t;
        path += ' C ' + cp1x.toFixed(2) + ' ' + cp1y.toFixed(2) + ', ' + cp2x.toFixed(2) + ' ' + cp2y.toFixed(2) + ', ' + p2.x.toFixed(2) + ' ' + p2.y.toFixed(2);
      }
      return path;
    }
    var linePath = smoothPath(pts);
    var baseLineY = top + plotH;
    var areaPath = linePath + ' L ' + pts[pts.length - 1].x.toFixed(2) + ' ' + baseLineY + ' L ' + pts[0].x.toFixed(2) + ' ' + baseLineY + ' Z';
    var areaMarkup = type === 'area'
      ? '<path class="chart-area" d="' + areaPath + '" fill="url(#' + gid + 'fill)"></path>'
      : '';
    var dots = pts.map(function (p, i) {
      var isActive = i === defaultActive;
      return '<circle class="chart-dot' + (isActive ? ' is-active' : '') + '" data-index="' + i + '" cx="' + p.x.toFixed(2) + '" cy="' + p.y.toFixed(2) + '" r="' + (isActive ? 5 : 3) + '"' + (isActive ? ' stroke="' + accent.b + '"' : '') + '></circle>';
    }).join('');
    chart.innerHTML = '<svg viewBox="0 0 360 46" role="img" aria-hidden="true"><defs><linearGradient id="' + gid + '" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="' + accent.a + '"></stop><stop offset="100%" stop-color="' + accent.b + '"></stop></linearGradient><linearGradient id="' + gid + 'fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="' + accent.b + '" stop-opacity=".32"></stop><stop offset="100%" stop-color="' + accent.b + '" stop-opacity="0"></stop></linearGradient></defs>' + guides + areaMarkup + '<path class="chart-line" style="stroke:url(#' + gid + ');filter:drop-shadow(0 3px 6px ' + accent.glow + ')" d="' + linePath + '"></path>' + dots + text + '</svg><div class="kpi-chart-tooltip"></div>';
    var svg2 = chart.querySelector('svg');
    var tooltip2 = chart.querySelector('.kpi-chart-tooltip');
    var dotNodes = Array.prototype.slice.call(chart.querySelectorAll('.chart-dot'));
    chart.style.setProperty('--kpi-dot-glow', accent.glow);
    function activateLine(i, show) {
      dotNodes.forEach(function (dot, dotIndex) {
        var isActive = dotIndex === i;
        dot.classList.toggle('is-active', isActive);
        dot.setAttribute('r', isActive ? 5 : 3);
        if (isActive) dot.setAttribute('stroke', accent.b); else dot.removeAttribute('stroke');
      });
      tooltip2.textContent = formatValue(values[i]);
      tooltip2.style.left = (pts[i].x / width * 100) + '%';
      tooltip2.style.top = (pts[i].y / height * 100) + '%';
      tooltip2.classList.toggle('is-visible', show);
    }
    activateLine(defaultActive, false);
    svg2.addEventListener('pointermove', function (event) {
      var rect = svg2.getBoundingClientRect();
      var x = (event.clientX - rect.left) / rect.width * width;
      var closest = 0, distance = Infinity;
      pts.forEach(function (p, i) { var d = Math.abs(p.x - x); if (d < distance) { closest = i; distance = d; } });
      activateLine(closest, true);
    });
    svg2.addEventListener('pointerleave', function () { activateLine(defaultActive, false); });
  }

  charts.forEach(buildChart);
  if (reduced || !('IntersectionObserver' in window)) {
    charts.forEach(function (chart) { chart.classList.add('is-drawn'); });
  } else {
    var observer = new IntersectionObserver(function (entries, obs) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) { entry.target.classList.add('is-drawn'); obs.unobserve(entry.target); }
      });
    }, { threshold: .35 });
    charts.forEach(function (chart) { observer.observe(chart); });
  }
})();
