/* Table behaviour the shared chrome scripts don't cover: row drill-downs and
   the card view tables collapse into on a phone. */
(function() {
  /* ─── Drill-Down Functionality ──────────────────────────────── */
  function initDrillDown() {
    const tables = document.querySelectorAll('.data-table:not(.heatmap-table):not(.mom-table)');

    tables.forEach(table => {
      const rows = table.querySelectorAll('tbody tr:not(.totals-row):not(.drill-down-detail)');

      rows.forEach(row => {
        // Only add drill-down to rows with meaningful data
        const cells = row.querySelectorAll('td');
        if (cells.length < 3) return;

        // Add drill-down class
        row.classList.add('drill-down-row');

        // Create detail row
        const detailRow = document.createElement('tr');
        detailRow.className = 'drill-down-detail';
        const detailCell = document.createElement('td');
        detailCell.colSpan = cells.length;

        // Build drill-down content from row data
        const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent.trim());
        const drillContent = document.createElement('div');
        drillContent.className = 'drill-down-content';

        cells.forEach((cell, idx) => {
          if (idx === 0) return; // Skip first column (label)
          const header = headers[idx] || 'Metric ' + idx;
          const value = cell.textContent.trim();

          if (value && value !== '—' && value !== 'n/a') {
            const metric = document.createElement('div');
            metric.className = 'drill-down-metric';
            metric.innerHTML = `<span class="drill-down-metric-label">${header}</span><span class="drill-down-metric-value">${value}</span>`;
            drillContent.appendChild(metric);
          }
        });

        // Add context-aware insights
        const insights = document.createElement('div');
        insights.className = 'drill-down-metric drill-down-insight';
        insights.style.flex = '1 1 100%';
        insights.style.background = 'var(--primary-soft)';
        insights.style.borderLeft = '3px solid var(--primary)';
        insights.style.marginTop = 'var(--space-2)';

        const rowLabel = cells[0]?.textContent.trim() || '';
        insights.innerHTML = `<span class="drill-down-metric-label">💡 Insight</span><span class="drill-down-metric-value" style="font-size:12px;font-family:var(--font-sans)">Click to expand detailed analytics for ${rowLabel}</span>`;
        drillContent.appendChild(insights);

        detailCell.appendChild(drillContent);
        detailRow.appendChild(detailCell);

        // Insert detail row after current row
        row.parentNode.insertBefore(detailRow, row.nextSibling);

        // Add click handler
        row.addEventListener('click', () => {
          row.classList.toggle('expanded');
          detailRow.classList.toggle('visible');
        });
      });
    });
  }

  /* ─── Mobile Table Card View ───────────────────────────────── */
  if (window.innerWidth <= 768) {
    document.querySelectorAll('table.data-table').forEach(table => {
      if (table.closest('.heatmap-table')) return;
      table.classList.add('mobile-cards');
      const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent.trim());
      table.querySelectorAll('tbody td').forEach(td => {
        const idx = Array.from(td.parentNode.children).indexOf(td);
        if (headers[idx]) td.setAttribute('data-label', headers[idx]);
      });
    });
  }


  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDrillDown);
  } else {
    initDrillDown();
  }
})();
