
(function() {
  // ---- Heatmap metric toggle ----
  var RPV = (window.__REPORT_META__ && window.__REPORT_META__.revenuePerVisit) || 0; // measured revenue per visit
  var cells = Array.prototype.slice.call(document.querySelectorAll('#demand-heatmap td[data-v]'));
  var btns = Array.prototype.slice.call(document.querySelectorAll('.hm-btn'));
  if (cells.length && btns.length) {
    var grand = document.querySelector('#demand-heatmap .hm-grand');
    var TOTAL = grand ? +grand.getAttribute('data-v') : 0;
    if (!TOTAL) { cells.forEach(function(c){ TOTAL += +c.getAttribute('data-v'); }); }
    var fmt = {
      visits:  function(v){ return v.toLocaleString('en-IN'); },
      revenue: function(v){ var r = v * RPV; return r >= 100000 ? '\u20B9' + (r/100000).toFixed(r >= 1000000 ? 1 : 2) + 'L' : '\u20B9' + (r/1000).toFixed(1) + 'K'; },
      share:   function(v){ return (v / TOTAL * 100).toFixed(1) + '%'; }
    };
    btns.forEach(function(b){
      b.addEventListener('click', function(){
        btns.forEach(function(x){ x.classList.toggle('is-active', x === b); });
        var f = fmt[b.getAttribute('data-metric')];
        cells.forEach(function(c){
          if (c.childNodes.length && c.childNodes[0].nodeType === 3) {
            c.childNodes[0].nodeValue = f(+c.getAttribute('data-v'));
          }
        });
        var lbl = document.getElementById('hm-metric-label');
        if (lbl) lbl.innerHTML = b.getAttribute('data-label');
      });
    });
  }

  // ---- Interactive heatmap exploration ----
  var heatmap = document.getElementById('demand-heatmap');
  var selection = document.getElementById('hm-selection');
  if (heatmap) {
    var headers = Array.prototype.slice.call(heatmap.querySelectorAll('thead th'));
    var heatRows = Array.prototype.slice.call(heatmap.querySelectorAll('tbody tr:not(.hm-totals)'));
    var selectableCells = Array.prototype.slice.call(heatmap.querySelectorAll('tbody tr:not(.hm-totals) .heat-cell[data-v]'));
    var clearSelection = function () {
      heatmap.classList.remove('has-selection');
      heatmap.querySelectorAll('.is-selected,.is-context-row,.is-context-column').forEach(function (node) {
        node.classList.remove('is-selected','is-context-row','is-context-column');
      });
    };
    var selectCell = function (cell) {
      clearSelection();
      var row = cell.closest('tr');
      var day = row.querySelector('.row-label').textContent.trim();
      var columnIndex = Array.prototype.indexOf.call(row.children, cell);
      var time = headers[columnIndex] ? headers[columnIndex].textContent.trim() : 'Slot';
      var visits = +cell.getAttribute('data-v');
      var detail = cell.querySelector('.heat-sub');
      var detailText = detail ? detail.textContent.trim() : 'No format detail recorded';
      cell.classList.add('is-selected');
      row.classList.add('is-context-row');
      if (headers[columnIndex]) headers[columnIndex].classList.add('is-context-column');
      heatmap.classList.add('has-selection');
      if (selection) selection.innerHTML = '<strong>' + day + ' · ' + time + '</strong> — ' + visits.toLocaleString('en-IN') + ' visits · ' + detailText;
    };
    selectableCells.forEach(function (cell) {
      var row = cell.closest('tr');
      var day = row.querySelector('.row-label').textContent.trim();
      var columnIndex = Array.prototype.indexOf.call(row.children, cell);
      var time = headers[columnIndex] ? headers[columnIndex].textContent.trim() : 'slot';
      cell.tabIndex = 0;
      cell.setAttribute('role','button');
      cell.setAttribute('aria-label', day + ' ' + time + ', ' + cell.getAttribute('data-v') + ' visits. Select for details.');
      cell.addEventListener('click', function () { selectCell(cell); });
      cell.addEventListener('keydown', function (event) {
        if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); selectCell(cell); }
      });
    });
    document.querySelectorAll('.hm-day-btn').forEach(function (button) {
      button.setAttribute('aria-pressed', String(button.classList.contains('is-active')));
      button.addEventListener('click', function () {
        var day = button.getAttribute('data-day');
        document.querySelectorAll('.hm-day-btn').forEach(function (item) {
          var active = item === button;
          item.classList.toggle('is-active', active);
          item.setAttribute('aria-pressed', String(active));
        });
        heatRows.forEach(function (row) {
          var rowDay = row.querySelector('.row-label').textContent.trim();
          row.hidden = day !== 'all' && rowDay !== day;
        });
        clearSelection();
        if (selection) selection.innerHTML = day === 'all' ? '<strong>All days visible.</strong> Select a populated slot for detail.' : '<strong>' + day + ' isolated.</strong> Select a populated slot for detail.';
      });
    });
    heatmap.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') { clearSelection(); if (selection) selection.innerHTML = '<strong>Selection cleared.</strong> Choose another populated slot.'; }
    });
  }

  // Section headers intentionally remain static.

  // ---- Appendix hint wording ----
  var app = document.getElementById('metric-appendix');
  if (app) {
    app.addEventListener('toggle', function(){
      var l = document.getElementById('app-hint-label');
      if (l) l.textContent = app.open ? 'Collapse metric dictionary' : 'Expand metric dictionary';
    });
  }

  // ---- Expand collapsed appendix for print/PDF export ----
  var closed = [];
  window.addEventListener('beforeprint', function(){
    closed = Array.prototype.slice.call(document.querySelectorAll('details:not([open])'));
    closed.forEach(function(d){ d.open = true; });
  });
  window.addEventListener('afterprint', function(){
    closed.forEach(function(d){ d.open = false; }); closed = [];
  });
})();
