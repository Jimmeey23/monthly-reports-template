var RM = (window.__REPORT_META__ || {});

(function () {
  'use strict';
  var button = document.getElementById('pdf-export-btn');
  if (!button) return;
  var overlay = document.getElementById('pdf-export-overlay');
  var statusNode = document.getElementById('pdf-export-status');
  var progressBar = document.getElementById('pdf-export-progress-bar');
  var isExporting = false;

  function setProgress(percent, message) {
    if (progressBar) progressBar.style.width = Math.max(4, Math.min(100, percent)) + '%';
    if (statusNode && message) statusNode.textContent = message;
  }
  function showOverlay(show) {
    if (!overlay) return;
    overlay.classList.toggle('is-visible', show);
    overlay.setAttribute('aria-hidden', show ? 'false' : 'true');
  }
  function nextFrame() {
    return new Promise(function (resolve) { requestAnimationFrame(function () { requestAnimationFrame(resolve); }); });
  }
  function legacyCssColors(value) {
    if (!value || (value.indexOf('color(') === -1 && value.indexOf('oklab(') === -1 && value.indexOf('oklch(') === -1)) return value;
    var converted = value.replace(/color\(\s*([a-z0-9-]+)\s+([^)]*)\)/gi, function (_, space, body) {
      var sides = body.trim().split(/\s*\/\s*/);
      var channels = sides[0].trim().split(/\s+/).slice(0, 3).map(function (part) {
        if (/%$/.test(part)) return Math.round(Math.max(0, Math.min(100, parseFloat(part))) * 2.55);
        return Math.round(Math.max(0, Math.min(1, parseFloat(part))) * 255);
      });
      if (channels.some(function (n) { return !isFinite(n); })) return 'rgba(30, 58, 138,1)';
      var alpha = sides[1] == null ? 1 : (/%$/.test(sides[1]) ? parseFloat(sides[1]) / 100 : parseFloat(sides[1]));
      alpha = isFinite(alpha) ? Math.max(0, Math.min(1, alpha)) : 1;
      return 'rgba(' + channels[0] + ',' + channels[1] + ',' + channels[2] + ',' + alpha + ')';
    });
    // The report no longer relies on OKLab colors in the PDF surface; this is a defensive fallback.
    converted = converted.replace(/okl(?:ab|ch)\([^)]*\)/gi, 'rgb(30,58,138)');
    return converted;
  }
  function sanitizePdfColors(root, view) {
    if (!root || !view) return;
    var properties = [
      'color', 'background-color', 'border-top-color', 'border-right-color',
      'border-bottom-color', 'border-left-color', 'outline-color',
      'text-decoration-color', 'caret-color', 'column-rule-color',
      'box-shadow', 'text-shadow', 'fill', 'stroke', 'stop-color', 'flood-color'
    ];
    var nodes = [root].concat(Array.prototype.slice.call(root.querySelectorAll('*')));
    nodes.forEach(function (node) {
      var computed;
      try { computed = view.getComputedStyle(node); } catch (_) { return; }
      properties.forEach(function (property) {
        var current = computed.getPropertyValue(property);
        if (!current || (current.indexOf('color(') === -1 && current.indexOf('oklab(') === -1 && current.indexOf('oklch(') === -1)) return;
        node.style.setProperty(property, legacyCssColors(current), 'important');
      });
    });
  }
  function directChildren(element) {
    return element ? Array.prototype.slice.call(element.children) : [];
  }
  function chapterTitle(section) {
    var title = section && section.querySelector('.section-eyebrow');
    return title ? title.textContent.replace(/\s+/g, ' ').trim() : 'Performance Report';
  }
  function makeChapterChunk(section, nodes, title) {
    var outer = document.createElement('div');
    outer.className = 'pdf-capture-chunk';
    var sectionClone = document.createElement('section');
    sectionClone.className = 'report-section';
    if (section && section.id) sectionClone.setAttribute('data-source-section', section.id);
    var container = document.createElement('div');
    container.className = 'container';
    nodes.forEach(function (node) {
      var clone = node.cloneNode(true);
      if (clone.tagName === 'DETAILS') clone.open = true;
      clone.querySelectorAll && clone.querySelectorAll('details').forEach(function (d) { d.open = true; });
      container.appendChild(clone);
    });
    sectionClone.appendChild(container);
    outer.appendChild(sectionClone);
    return { element: outer, title: title || chapterTitle(section) };
  }
  function buildChunks() {
    var chunks = [];
    var hero = document.querySelector('body > .hero');
    if (hero) {
      var wrap = document.createElement('div');
      wrap.className = 'pdf-capture-chunk';
      wrap.appendChild(hero.cloneNode(true));
      chunks.push({ element: wrap, title: 'Executive Cover' });
    }
    document.querySelectorAll('section.report-section').forEach(function (section) {
      if (section.id === 'appendix') {
        var summary = section.querySelector('summary.section-hero');
        if (summary) chunks.push(makeChapterChunk(section, [summary], 'Appendix · Metric Dictionary'));
        var appendixBody = section.querySelector('.appendix-body');
        if (appendixBody) {
          var bodyKids = directChildren(appendixBody);
          for (var a = 0; a < bodyKids.length; a++) {
            var appendixGroup = [bodyKids[a]];
            if (bodyKids[a].classList.contains('appendix-group-label') && bodyKids[a + 1]) appendixGroup.push(bodyKids[++a]);
            chunks.push(makeChapterChunk(section, appendixGroup, 'Appendix · Metric Dictionary'));
          }
        }
        return;
      }
      var container = section.querySelector(':scope > .container');
      if (!container) return;
      var kids = directChildren(container).filter(function (node) {
        return !node.classList.contains('section-edit-bar');
      });
      for (var i = 0; i < kids.length; i++) {
        var node = kids[i];
        var group = [node];
        if (node.classList.contains('section-hero') && kids[i + 1] && kids[i + 1].classList.contains('section-marquee')) {
          group.push(kids[++i]);
        } else if (node.classList.contains('subsection')) {
          if (kids[i + 1] && !kids[i + 1].classList.contains('subsection')) group.push(kids[++i]);
        } else if (node.classList.contains('pane-title') && kids[i + 1]) {
          group.push(kids[++i]);
        }
        chunks.push(makeChapterChunk(section, group, chapterTitle(section)));
      }
    });
    var footer = document.querySelector('body > footer.footer');
    if (footer) {
      var footerWrap = document.createElement('div');
      footerWrap.className = 'pdf-capture-chunk';
      footerWrap.appendChild(footer.cloneNode(true));
      chunks.push({ element: footerWrap, title: 'Report Notes' });
    }
    return chunks;
  }

  function safeBreakpoints(element, canvas) {
    var rootRect = element.getBoundingClientRect();
    var scale = canvas.height / Math.max(1, rootRect.height);
    var selector = [
      '.section-hero', '.section-marquee', '.hero-media-grid', '.ai-result-header', '.ai-summary-narrative-block',
      '.ai-bullet-item', '.insight-card', '.worked-card', '.action-card', '.funnel-stage',
      '.subsection', '.panel-header', 'table.data-table tr', '.callout', '.conclusion-item',
      '.appendix-group-label', '.footer-grid > div'
    ].join(',');
    var points = Array.prototype.slice.call(element.querySelectorAll(selector)).map(function (node) {
      return Math.round((node.getBoundingClientRect().bottom - rootRect.top) * scale);
    }).filter(function (value) { return value > 30 && value < canvas.height - 15; });
    return Array.from(new Set(points)).sort(function (a, b) { return a - b; });
  }

  button.addEventListener('click', async function (event) {
    event.preventDefault();
    if (isExporting) return;
    isExporting = true;
    button.classList.add('is-exporting');
    button.disabled = true;
    showOverlay(true);
    setProgress(4, 'Preparing the A4 document structure…');

    var stage = document.createElement('div');
    stage.className = 'pdf-export-stage';
    stage.setAttribute('aria-hidden', 'true');
    document.body.appendChild(stage);

    try {
      if (typeof window.html2canvas !== 'function' || !window.jspdf || !window.jspdf.jsPDF) {
        throw new Error('The embedded PDF renderer could not be initialized.');
      }
      if (document.fonts && document.fonts.ready) await document.fonts.ready;
      var chunks = buildChunks();
      if (!chunks.length) throw new Error('No report content was available to export.');

      var jsPDF = window.jspdf.jsPDF;
      var pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4', compress: true, putOnlyUsedFonts: true });
      var pageW = 210, pageH = 297;
      var marginX = 10, contentW = 190;
      var contentTop = 16, contentBottom = 283.5, contentH = contentBottom - contentTop;
      var currentY = contentTop;
      var currentTitle = 'Performance Report';
      var pageCount = 1;

      function decoratePage(title) {
        pdf.setFillColor(242, 242, 242);
        pdf.rect(0, 0, pageW, pageH, 'F');
        pdf.setFillColor(255, 255, 255);
        pdf.roundedRect(7, 7, 196, 283, 2.5, 2.5, 'F');
        pdf.setFillColor(30, 58, 138);
        pdf.roundedRect(10, 9.5, 4, 4, 1, 1, 'F');
        pdf.setTextColor(16, 21, 34);
        pdf.setFont('helvetica', 'bold');
        pdf.setFontSize(7.5);
        pdf.text(RM.pdfHeader, 16.5, 12.6);
        pdf.setTextColor(105, 113, 126);
        pdf.setFont('helvetica', 'normal');
        pdf.setFontSize(6.4);
        var shortTitle = (title || 'Performance Report').replace(/\s+/g, ' ').slice(0, 76);
        pdf.text(shortTitle.toUpperCase(), 200, 12.6, { align: 'right' });
        pdf.setDrawColor(222, 226, 233);
        pdf.setLineWidth(.25);
        pdf.line(10, 15, 200, 15);
      }
      function newPage(title) {
        if (pageCount > 0) pdf.addPage('a4', 'portrait');
        pageCount += 1;
        currentTitle = title || currentTitle;
        decoratePage(currentTitle);
        currentY = contentTop;
      }
      // The constructor already creates page one.
      pageCount = 0;
      decoratePage(currentTitle);
      pageCount = 1;

      function chooseSliceEnd(start, idealEnd, maxEnd, breaks) {
        var minUseful = start + (maxEnd - start) * .58;
        var candidates = breaks.filter(function (point) { return point > minUseful && point <= idealEnd; });
        return candidates.length ? candidates[candidates.length - 1] : idealEnd;
      }
      function canvasSlice(source, y, height) {
        var slice = document.createElement('canvas');
        slice.width = source.width;
        slice.height = Math.max(1, height);
        var ctx = slice.getContext('2d');
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, slice.width, slice.height);
        ctx.drawImage(source, 0, y, source.width, height, 0, 0, source.width, height);
        return slice;
      }
      function addCanvas(canvas, title, breaks) {
        var mmPerPixel = contentW / canvas.width;
        currentTitle = title || currentTitle;
        var start = 0;
        while (start < canvas.height) {
          var availableMm = contentBottom - currentY;
          // Very small remnants create visually awkward slivers; advance only when less than 12% remains.
          if (availableMm < contentH * .12) {
            newPage(currentTitle);
            availableMm = contentBottom - currentY;
          }
          var availablePixels = Math.max(80, Math.floor(availableMm / mmPerPixel));
          var ideal = Math.min(canvas.height, start + availablePixels);
          var end = ideal;
          if (ideal < canvas.height) {
            end = chooseSliceEnd(start, ideal, start + availablePixels, breaks || []);
            // If no useful semantic break exists, use a new page rather than cut a card through its first line.
            if (end - start < availablePixels * .38 && currentY > contentTop + 2) {
              newPage(currentTitle);
              continue;
            }
          }
          if (end <= start + 20) end = ideal;
          var piece = canvasSlice(canvas, start, end - start);
          var pieceMm = piece.height * mmPerPixel;
          pdf.addImage(piece.toDataURL('image/jpeg', .91), 'JPEG', marginX, currentY, contentW, pieceMm, undefined, 'FAST');
          currentY += pieceMm + 2;
          start = end;
          if (start < canvas.height) newPage(currentTitle);
        }
      }

      for (var i = 0; i < chunks.length; i++) {
        var chunk = chunks[i];
        stage.replaceChildren(chunk.element);
        await nextFrame();
        setProgress(8 + Math.round((i / chunks.length) * 82), 'Rendering ' + chunk.title + ' · block ' + (i + 1) + ' of ' + chunks.length + '…');
        sanitizePdfColors(chunk.element, window);
        var canvas = await window.html2canvas(chunk.element, {
          scale: 1.35,
          backgroundColor: '#ffffff',
          useCORS: true,
          allowTaint: false,
          logging: false,
          imageTimeout: 0,
          removeContainer: true,
          windowWidth: 1100,
          onclone: function (clonedDocument) {
            var clonedStage = clonedDocument.querySelector('.pdf-export-stage');
            if (clonedStage) sanitizePdfColors(clonedStage, clonedDocument.defaultView);
            clonedDocument.querySelectorAll('.reveal').forEach(function (node) {
              node.classList.add('is-visible');
              node.style.opacity = '1'; node.style.transform = 'none'; node.style.filter = 'none';
            });
            clonedDocument.querySelectorAll('details').forEach(function (details) { details.open = true; });
          }
        });
        var breaks = safeBreakpoints(chunk.element, canvas);
        addCanvas(canvas, chunk.title, breaks);
        stage.replaceChildren();
        await new Promise(function (resolve) { setTimeout(resolve, 0); });
      }

      setProgress(94, 'Adding page numbers and document metadata…');
      var pages = pdf.getNumberOfPages();
      for (var page = 1; page <= pages; page++) {
        pdf.setPage(page);
        pdf.setDrawColor(222, 226, 233);
        pdf.setLineWidth(.25);
        pdf.line(10, 285, 200, 285);
        pdf.setTextColor(113, 121, 135);
        pdf.setFont('helvetica', 'normal');
        pdf.setFontSize(6.5);
        pdf.text('PHYSIQUE 57  ·  SENIOR MANAGEMENT REVIEW', 10, 288.3);
        pdf.setTextColor(30, 58, 138);
        pdf.setFont('helvetica', 'bold');
        pdf.text(String(page).padStart(2, '0') + ' / ' + String(pages).padStart(2, '0'), 200, 288.3, { align: 'right' });
      }
      pdf.setProperties({
        title: RM.pdfTitle,
        subject: 'Senior Management Review',
        author: RM.pdfAuthor,
        keywords: RM.pdfKeywords,
        creator: 'Kwality House Studio Pulse'
      });
      setProgress(100, 'Your styled A4 PDF is ready. Starting the download…');
      pdf.save(RM.pdfFilename);
      await new Promise(function (resolve) { setTimeout(resolve, 850); });
    } catch (error) {
      console.error('PDF export failed:', error);
      setProgress(100, 'The PDF could not be completed: ' + (error && error.message ? error.message : 'unknown rendering error') + '. Please retry in a current Chrome, Edge, or Firefox browser.');
      await new Promise(function (resolve) { setTimeout(resolve, 4200); });
    } finally {
      if (stage && stage.parentNode) stage.parentNode.removeChild(stage);
      showOverlay(false);
      button.disabled = false;
      button.classList.remove('is-exporting');
      isExporting = false;
      setProgress(4, 'Preparing the A4 document structure…');
    }
  });
})();
