/* Recurring-slot board: one row per class x day x time, re-ranked in the page
   by whichever measure the reader picks, with a toggle that re-groups the same
   schedule by trainer. The payload for both groupings ships with the report, so
   switching never needs a round trip. */
(function () {
  'use strict';

  var INR = function (v) { return Math.round(v).toLocaleString('en-IN'); };
  var FMT = {
    int: function (v) { return INR(v || 0); },
    dec1: function (v) { return (+v || 0).toFixed(1); },
    pct: function (v) { return (+v || 0).toFixed(1) + '%'; },
    rupee: function (v) { return '₹' + INR(v || 0); },
    lakh: function (v) {
      var n = +v || 0;
      if (Math.abs(n) >= 100000) return '₹' + (n / 100000).toFixed(2) + 'L';
      if (Math.abs(n) >= 1000) return '₹' + (n / 1000).toFixed(1) + 'K';
      return '₹' + INR(n);
    }
  };
  var fmt = function (kind, value) { return (FMT[kind] || FMT.int)(value); };

  function fillTone(fill) {
    if (fill >= 70) return 'is-good';
    if (fill < 35) return 'is-bad';
    return '';
  }

  function build(board) {
    var script = board.querySelector('.slot-board-data');
    if (!script) return;
    var data;
    try { data = JSON.parse(script.textContent); } catch (e) { return; }

    var head = board.querySelector('[data-slot-head]');
    var body = board.querySelector('[data-slot-body]');
    var summary = board.querySelector('[data-slot-summary]');
    var toggle = board.querySelector('[data-slot-trainer-toggle]');
    var metricKey = (data.metrics[0] || {}).key;
    var size = 15;

    function metric() {
      for (var i = 0; i < data.metrics.length; i++) {
        if (data.metrics[i].key === metricKey) return data.metrics[i];
      }
      return data.metrics[0];
    }

    function rows() {
      var byTrainer = toggle && toggle.checked;
      var list = (byTrainer ? data.trainer : data.base).slice();
      var m = metric();
      /* Always biggest-first: ranking by empty sessions or late cancels means
         "show me the worst offenders", not the slots with none of them. The
         better/worse direction only drives the colour. */
      list.sort(function (a, b) {
        return (b[m.key] || 0) - (a[m.key] || 0) || (b.visits || 0) - (a.visits || 0);
      });
      return list;
    }

    function renderHead(byTrainer) {
      head.innerHTML =
        '<tr>' +
        '<th class="slot-rank-col">#</th>' +
        '<th>Class</th><th>Day</th><th>Time</th>' +
        (byTrainer ? '<th>Trainer</th>' : '<th>Trainers</th>') +
        '<th>Sessions</th><th>Empty</th><th>Attendees</th><th>Capacity</th>' +
        '<th>Fill</th><th>Class avg</th><th>Late cancels</th><th>Revenue</th>' +
        '</tr>';
    }

    function render() {
      var byTrainer = !!(toggle && toggle.checked);
      var all = rows();
      var shown = size > 0 ? all.slice(0, size) : all;
      var m = metric();
      renderHead(byTrainer);

      body.innerHTML = shown.map(function (r, i) {
        var trainerCell = byTrainer
          ? (r.trainer || '—')
          : (r.trainer_count > 1 ? r.trainer_count + ' trainers' : (r.trainers[0] || '—'));
        var detail = [
          ['Sessions run', FMT.int(r.sessions - r.empty) + ' of ' + FMT.int(r.sessions)],
          ['Attendees', FMT.int(r.visits)],
          ['Class average (excl. empty)', FMT.dec1(r.avg_excl)],
          ['Class average (incl. empty)', FMT.dec1(r.avg_incl)],
          ['Fill rate', FMT.pct(r.fill)],
          ['Empty sessions', FMT.int(r.empty)],
          ['Late cancellations', FMT.int(r.late)],
          ['Revenue', FMT.lakh(r.revenue)],
          ['Revenue / session', FMT.rupee(r.rev_per_session)],
          ['Format', r.fmt || '—'],
          ['Trainers', (r.trainers || []).join(', ') || '—']
        ];
        var payload = {
          kicker: 'Recurring slot',
          title: r.cls,
          subtitle: r.day + ' · ' + r.time + (byTrainer && r.trainer ? ' · ' + r.trainer : ''),
          stats: detail.map(function (pair) { return { label: pair[0], value: pair[1] }; }),
          footnote: 'Esc or click outside to close.'
        };
        return '<tr class="slot-row" tabindex="0" role="button" data-drill=\'' +
          JSON.stringify(payload).replace(/'/g, '&#39;') + '\'>' +
          '<td class="num slot-rank-col"><span class="slot-rank">' + (i + 1) + '</span></td>' +
          '<td class="metric-name">' + r.cls + '</td>' +
          '<td>' + r.day + '</td>' +
          '<td class="num">' + r.time + '</td>' +
          '<td>' + trainerCell + '</td>' +
          '<td class="num">' + FMT.int(r.sessions) + '</td>' +
          '<td class="num' + (r.empty > 0 ? ' is-bad' : '') + '">' + FMT.int(r.empty) + '</td>' +
          '<td class="num">' + FMT.int(r.visits) + '</td>' +
          '<td class="num">' + FMT.int(r.capacity) + '</td>' +
          '<td class="num ' + fillTone(r.fill) + '">' + FMT.pct(r.fill) + '</td>' +
          '<td class="num"><strong>' + FMT.dec1(r.avg_excl) + '</strong></td>' +
          '<td class="num">' + FMT.int(r.late) + '</td>' +
          '<td class="num">' + FMT.lakh(r.revenue) + '</td>' +
          '</tr>';
      }).join('');

      if (summary) {
        var best = all[0];
        var worst = all[all.length - 1];
        summary.innerHTML = best
          ? '<span class="slot-summary-line">Ranked by <strong>' + m.label + '</strong> · ' +
            (byTrainer ? 'class · day · time · trainer' : 'class · day · time') + ' · ' +
            all.length + ' slots</span>' +
            '<span class="slot-summary-line">' + (m.better === 'low' ? 'Worst: ' : 'Top: ') + '<strong>' + best.cls + '</strong> ' + best.day + ' ' + best.time +
            (byTrainer && best.trainer ? ' · ' + best.trainer : '') + ' — ' + fmt(m.fmt, best[m.key]) + '</span>' +
            '<span class="slot-summary-line">' + (m.better === 'low' ? 'Cleanest: ' : 'Bottom: ') + '<strong>' + worst.cls + '</strong> ' + worst.day + ' ' + worst.time +
            (byTrainer && worst.trainer ? ' · ' + worst.trainer : '') + ' — ' + fmt(m.fmt, worst[m.key]) + '</span>'
          : '';
      }
    }

    board.querySelectorAll('[data-slot-metric]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        metricKey = btn.getAttribute('data-slot-metric');
        board.querySelectorAll('[data-slot-metric]').forEach(function (b) {
          b.classList.toggle('is-active', b === btn);
        });
        render();
      });
    });

    board.querySelectorAll('[data-slot-size]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        size = +btn.getAttribute('data-slot-size');
        board.querySelectorAll('[data-slot-size]').forEach(function (b) {
          b.classList.toggle('is-active', b === btn);
        });
        render();
      });
    });

    if (toggle) toggle.addEventListener('change', render);

    /* Row detail is handled by the shared drill modal, which picks up each
       row's data-drill payload — including rows this board re-renders. */

    render();
  }

  function init() {
    document.querySelectorAll('[data-slot-board]').forEach(build);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
