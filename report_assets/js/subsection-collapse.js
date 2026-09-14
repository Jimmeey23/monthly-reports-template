
(function () {
  var subsections = document.querySelectorAll('.subsection');
  subsections.forEach(function (sub) {
    var title = sub.querySelector('.subsection-title');
    if (!title) return;
    var body = [];
    var node = sub.nextElementSibling;
    while (node && !node.classList.contains('subsection') && node.tagName !== 'SECTION') {
      body.push(node);
      node = node.nextElementSibling;
    }
    if (!body.length) return;
    var toggle = document.createElement('button');
    toggle.type = 'button';
    toggle.className = 'subsection-collapse-btn';
    toggle.setAttribute('aria-expanded', 'true');
    toggle.setAttribute('aria-label', 'Collapse section');
    toggle.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"></path></svg>';
    title.classList.add('subsection-title-collapsible');
    title.appendChild(toggle);
    function setCollapsed(collapsed) {
      sub.classList.toggle('collapsed', collapsed);
      toggle.setAttribute('aria-expanded', String(!collapsed));
      body.forEach(function (el) { el.style.display = collapsed ? 'none' : ''; });
    }
    title.addEventListener('click', function (e) {
      setCollapsed(!sub.classList.contains('collapsed'));
    });
  });
}());
