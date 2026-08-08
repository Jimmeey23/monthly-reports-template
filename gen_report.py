#!/usr/bin/env python3
"""
Kwality House Performance Report Generator — June & July 2026
Reads analysis_full.json and produces a complete HTML report
mirroring the May 2026 reference design system.
Primary month = July 2026 (with June 2026 comparator throughout).
"""
import json, html

R = json.load(open('analysis_full.json'))

def L(v):  # lakh
    return v/100000.0

def pc(n, o):  # pct change
    if o is None or o == 0: return None
    return (n-o)/abs(o)*100

def fmt_l(v, dp=2):
    return f"&#8377;{L(v):.{dp}f}L"

def fmt_r(v):
    return f"&#8377;{v:,.0f}"

def esc(s):
    return html.escape(str(s)) if s else ''

def badge(val, neutral_pp=False, inverse=False):
    """Return a badge span. val is pct change or pp delta."""
    if val is None: return '<span class="badge neutral">&mdash;</span>'
    if neutral_pp:
        cls = 'neutral'
        sign = '+' if val >= 0 else ''
        return f'<span class="badge {cls}">{sign}{val:.1f}pp</span>'
    # For inverse metrics (e.g. discount, churn where lower is better)
    if inverse:
        if val > 0: cls = 'bad'; sign = '+'
        elif val < 0: cls = 'good'; sign = ''
        else: cls = 'neutral'; sign = ''
    else:
        if val > 0: cls = 'good'; sign = '+'
        elif val < 0: cls = 'bad'; sign = ''
        else: cls = 'neutral'; sign = ''
    return f'<span class="badge {cls}">{sign}{val:.1f}%</span>'

def fill_class(pct):
    if pct >= 65: return 'fill-high'
    elif pct >= 35: return 'fill-mid'
    else: return 'fill-low'

def heat_class(pct):
    if pct <= 0: return 'heat-none'
    elif pct < 20: return 'heat-1'
    elif pct < 40: return 'heat-2'
    elif pct < 60: return 'heat-3'
    elif pct < 80: return 'heat-4'
    else: return 'heat-5'

# ---- data handles ----
S = R['sales']; SE = R['sessions']; F = R['funnel']; LP = R['lapsed']; CK = R['checkins']; PR = R['payroll']
july = S['2026-07']; june = S['2026-06']; may = S['2026-05']
sej = SE['2026-07']; sejun = SE['2026-06']; semay = SE['2026-05']
fj = F['2026-07']; fjun = F['2026-06']; fmay = F['2026-05']
lj = LP['2026-07']; ljun = LP['2026-06']; lmay = LP['2026-05']
cj = CK['2026-07']; cjun = CK['2026-06']
base = R['baseline']
yoy = S['2025-07']; yoy_jun = S['2025-06']
sej_yoy = SE['2025-07']; fj_yoy = F['2025-07']
sejun_yoy = SE['2025-06']; fj_yoy_jun = F['2025-06']

# Derived helpers
july_atv = july['gross'] / july['txn'] if july['txn'] else 0
june_atv = june['gross'] / june['txn'] if june['txn'] else 0
base_atv = base.get('atv', 0)
july_rpm = july['net'] / july['members'] if july['members'] else 0
june_rpm = june['net'] / june['members'] if june['members'] else 0
base_rpm = base.get('rev_per_member', 0)

# Category extracts
def cat(d, name):
    return d['cats'].get(name, [0, 0, 0])

july_mem = cat(july, 'Memberships')
june_mem = cat(june, 'Memberships')
july_pkg = cat(july, 'Class Packages')
june_pkg = cat(june, 'Class Packages')
july_drop = cat(july, 'Sessions/Single Classes')
june_drop = cat(june, 'Sessions/Single Classes')
july_priv = cat(july, 'Privates')
june_priv = cat(june, 'Privates')

# Read full CSS from reference report (lines 1-286 = head + style)
CSS = open('full_css.txt').read()

DAYS = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']

# ============ HERO ============
def hero():
    net_mom = pc(july['net'], june['net'])
    net_yoy = pc(july['net'], yoy['net'])
    net_base = pc(july['net'], base['net'])
    vis_mom = pc(sej['visits'], sejun['visits'])
    vis_yoy = pc(sej['visits'], sej_yoy['visits'])
    fill_mom = sej['fill'] - sejun['fill']
    fill_yoy = sej['fill'] - sej_yoy['fill']
    conv_mom = pc(fj['conv_rate'], fjun['conv_rate'])
    conv_yoy = pc(fj['conv_rate'], fj_yoy['conv_rate'])
    lapsed_mom = pc(lj['lapsed'], ljun['lapsed'])
    disc_eff_mom = pc(july['disc_eff'], june['disc_eff'])
    disc_eff_yoy = pc(july['disc_eff'], yoy['disc_eff']) if yoy.get('disc_eff') else None

    kpis = [
        f'''<div class="kpi-card tone-bad">
          <div class="kpi-label">Net Sales</div>
          <div class="kpi-value">{fmt_l(july["net"])}</div>
          <div class="kpi-sub">Gross {fmt_l(july["gross"])} &middot; Disc {fmt_l(july["disc"])}</div>
          <div class="kpi-trends">
            <span class="kpi-trend"><span class="trend-label">MoM</span> {badge(net_mom)}</span>
            <span class="kpi-trend"><span class="trend-label">YoY</span> {badge(net_yoy)}</span>
          </div>
          <div class="kpi-baseline">{f"{net_base:+.1f}%" if net_base else "n/a"} vs Jan&ndash;Mar</div>
        </div>''',
        f'''<div class="kpi-card tone-good">
          <div class="kpi-label">Visits</div>
          <div class="kpi-value">{sej["visits"]:,}</div>
          <div class="kpi-sub">Across {sej["sessions"]} sessions</div>
          <div class="kpi-trends">
            <span class="kpi-trend"><span class="trend-label">MoM</span> {badge(vis_mom)}</span>
            <span class="kpi-trend"><span class="trend-label">YoY</span> {badge(vis_yoy)}</span>
          </div>
          <div class="kpi-baseline">Highest in 8 months</div>
        </div>''',
        f'''<div class="kpi-card tone-good">
          <div class="kpi-label">Fill Rate</div>
          <div class="kpi-value">{sej["fill"]:.1f}%</div>
          <div class="kpi-sub">Capacity utilization</div>
          <div class="kpi-trends">
            <span class="kpi-trend"><span class="trend-label">MoM</span> {badge(fill_mom, True)}</span>
            <span class="kpi-trend"><span class="trend-label">YoY</span> {badge(fill_yoy, True)}</span>
          </div>
          <div class="kpi-baseline">Best fill in 8 months</div>
        </div>''',
        f'''<div class="kpi-card tone-bad">
          <div class="kpi-label">Conversion Rate</div>
          <div class="kpi-value">{fj["conv_rate"]:.1f}%</div>
          <div class="kpi-sub">{fj["leads"]} leads &rarr; {fj["converted"]} converted</div>
          <div class="kpi-trends">
            <span class="kpi-trend"><span class="trend-label">MoM</span> {badge(conv_mom)}</span>
            <span class="kpi-trend"><span class="trend-label">YoY</span> {badge(conv_yoy)}</span>
          </div>
          <div class="kpi-baseline">Halved vs June</div>
        </div>''',
        f'''<div class="kpi-card tone-warn">
          <div class="kpi-label">Lapsed Members</div>
          <div class="kpi-value">{lj["lapsed"]}</div>
          <div class="kpi-sub">Churn rate {lj["churn_rate"]:.1f}%</div>
          <div class="kpi-trends">
            <span class="kpi-trend"><span class="trend-label">MoM</span> {badge(lapsed_mom)}</span>
            <span class="kpi-trend"><span class="trend-label">Renewals</span> <span class="badge neutral">{lj["renewed"]}</span></span>
          </div>
          <div class="kpi-baseline">{R["cumulative_lapsed_unique"]} cumulative unique</div>
        </div>''',
        f'''<div class="kpi-card tone-good">
          <div class="kpi-label">Discount Efficiency</div>
          <div class="kpi-value">&#8377;{july["disc_eff"]:.2f}</div>
          <div class="kpi-sub">Net rev / &#8377;1 discounted</div>
          <div class="kpi-trends">
            <span class="kpi-trend"><span class="trend-label">MoM</span> {badge(disc_eff_mom)}</span>
            <span class="kpi-trend"><span class="trend-label">YoY</span> {badge(disc_eff_yoy)}</span>
          </div>
          <div class="kpi-baseline">Discipline restored</div>
        </div>''',
    ]
    return f'''
<section class="hero">
  <div class="container hero-content">
    <div class="hero-eyebrow">
      <span class="dot">KH</span>
      Senior Management Review &middot; Period: 01 June &mdash; 31 July 2026
    </div>
    <h1>
      Kwality House <span class="accent-word">studio performance</span><br>
      for <span class="accent-yellow">June &amp; July 2026</span> &mdash; the studio has never been busier, yet revenue and conversion are pulling in opposite directions.
    </h1>
    <p class="hero-sub">
      A data-led review of the studio&rsquo;s commercial and operational performance across June and July 2026, benchmarked against the
      <strong>January &ndash; March 2026 baseline</strong>, May 2026, and the same months year-on-year. July delivered the highest
      visit volume and fill rate in eight months, but net sales contracted to &#8377;14.13L and the conversion rate halved. Every
      section is structured to surface a business decision &mdash; monetising attendance, repairing the conversion funnel, and
      sustaining the discount discipline that has now been restored &mdash; that senior management can act on this quarter.
    </p>

    <div class="hero-meta">
      <div class="hero-meta-item"><span class="label">Location</span><span class="value">Kwality House, Kemps Corner</span></div>
      <div class="hero-meta-item"><span class="label">Period</span><span class="value">01 June &mdash; 31 July 2026</span></div>
      <div class="hero-meta-item"><span class="label">Reporting basis</span><span class="value">July: &#8377;14.13L net &middot; 368 sessions &middot; 128 buyers</span></div>
      <div class="hero-meta-item"><span class="label">Comparators</span><span class="value">Jun 2026 &middot; May 2026 &middot; Jan&ndash;Mar avg &middot; YoY</span></div>
      <div class="hero-meta-item"><span class="label">Audience</span><span class="value">Senior Management &middot; Board Review</span></div>
    </div>

    <div class="hero-kpi-grid">
      {''.join(kpis)}
    </div>
  </div>
</section>'''


# ============ SECTION 01: EXECUTIVE SUMMARY ============
def section_01():
    rows = []
    def krow(name, jval, jun_val, base_val, fmt='lakh', inverse=False):
        """fmt: lakh, int, pct, rs"""
        if fmt == 'lakh':
            jstr = fmt_l(jval); ostr = fmt_l(jun_val); bstr = fmt_l(base_val)
        elif fmt == 'int':
            jstr = f'{jval:,}'; ostr = f'{jun_val:,}'; bstr = f'{base_val:,.0f}' if base_val else '&mdash;'
        elif fmt == 'rs':
            jstr = fmt_r(jval); ostr = fmt_r(jun_val); bstr = fmt_r(base_val)
        elif fmt == 'pct':
            jstr = f'{jval:.1f}%'; ostr = f'{jun_val:.1f}%'; bstr = f'{base_val:.1f}%'
        b_chg = pc(jval, base_val)
        m_chg = pc(jval, jun_val)
        return f'''<tr>
          <td class="metric-name">{name}</td>
          <td class="num"><strong>{jstr}</strong></td>
          <td class="num">{ostr}</td>
          <td class="num">{bstr}</td>
          <td class="num">{badge(b_chg, inverse=inverse)}</td>
          <td class="num">{badge(m_chg, inverse=inverse)}</td>
        </tr>'''

    rows.append(krow('Gross Sales', july['gross'], june['gross'], base['gross']))
    rows.append(krow('Net Sales', july['net'], june['net'], base['net']))
    rows.append(krow('Transactions', july['txn'], june['txn'], base['txn'], fmt='int'))
    rows.append(krow('Unique Buyers', july['members'], june['members'], base['members'], fmt='int'))
    rows.append(krow('Avg Transaction Value', july_atv, june_atv, base_atv, fmt='rs'))
    rows.append(krow('Avg Revenue / Member', july_rpm, june_rpm, base_rpm, fmt='rs'))
    rows.append(krow('Discount Value', july['disc'], june['disc'], base['disc'], inverse=True))
    rows.append(krow('Discount Penetration', july.get('disc_pen',0), june.get('disc_pen',0), base.get('disc_pen',0), fmt='pct', inverse=True))
    rows.append(krow('Discount Efficiency', july['disc_eff'], june['disc_eff'], base.get('disc_eff',0), fmt='rs'))
    rows.append(krow('Sessions', sej['sessions'], sejun['sessions'], 0, fmt='int'))
    rows.append(krow('Visits', sej['visits'], sejun['visits'], 0, fmt='int'))
    rows.append(krow('Fill Rate', sej['fill'], sejun['fill'], 0, fmt='pct'))
    rows.append(krow('Leads', fj['leads'], fjun['leads'], 0, fmt='int'))
    rows.append(krow('Converted Members', fj['converted'], fjun['converted'], 0, fmt='int'))
    rows.append(krow('Conversion Rate', fj['conv_rate'], fjun['conv_rate'], 0, fmt='pct'))
    rows.append(krow('Lapsed Members', lj['lapsed'], ljun['lapsed'], 0, fmt='int', inverse=True))
    rows.append(krow('Churn Rate', lj['churn_rate'], ljun['churn_rate'], 0, fmt='pct', inverse=True))
    rows.append(krow('Renewal Rate', lj['renewal_rate'], ljun['renewal_rate'], 0, fmt='pct'))
    rows.append(krow('Active Memberships', R['active']['total'], 0, 0, fmt='int'))

    insights = [
        f'''<div class="insight-card">
      <div class="insight-num">01</div>
      <div class="insight-body">
        <div class="insight-title">Attendance is at an eight-month high &mdash; revenue is not.</div>
        <div class="insight-text">July delivered <strong>{sej["visits"]:,} visits</strong> across {sej["sessions"]} sessions at <strong>{sej["fill"]:.1f}% fill</strong> &mdash; the highest volume and utilisation since January. Yet net sales fell to <strong>{fmt_l(july["net"])}</strong>, down {pc(july["net"],june["net"]):.1f}% MoM. The studio is monetising attendance less efficiently than at any point in 2026.</div>
      </div>
    </div>''',
        f'''<div class="insight-card">
      <div class="insight-num">02</div>
      <div class="insight-body">
        <div class="insight-title">Conversion rate halved month-on-month.</div>
        <div class="insight-text">{fj["leads"]} leads produced only <strong>{fj["converted"]} conversions</strong> &mdash; a {fj["conv_rate"]:.1f}% conversion rate, down from {fjun["conv_rate"]:.1f}% in June. The lead pipeline grew {pc(fj["leads"],fjun["leads"]):.0f}% MoM, but the conversion mechanism broke down. June converted {fjun["converted"]} of {fjun["leads"]} leads; July converted half as many despite more leads at the top.</div>
      </div>
    </div>''',
        f'''<div class="insight-card">
      <div class="insight-num">03</div>
      <div class="insight-body">
        <div class="insight-title">Discount discipline has been restored.</div>
        <div class="insight-text">Discount value fell to <strong>{fmt_l(july["disc"])}</strong> &mdash; down {pc(july["disc"],june["disc"]):.0f}% MoM and {pc(july["disc"],base["disc"]):.0f}% vs the Jan&ndash;Mar baseline. Discount efficiency improved to <strong>&#8377;{july["disc_eff"]:.2f}</strong> of net revenue per &#8377;1 discounted, the best reading in 2026. The May anniversary discount hangover has been fully corrected.</div>
      </div>
    </div>''',
        f'''<div class="insight-card">
      <div class="insight-num">04</div>
      <div class="insight-body">
        <div class="insight-title">Buyer count contracted sharply.</div>
        <div class="insight-text">Only <strong>{july["members"]} unique buyers</strong> transacted in July, down from {june["members"]} in June ({pc(july["members"],june["members"]):.1f}% MoM) and {pc(july["members"],base["members"]):.1f}% below the Jan&ndash;Mar baseline. The transaction count fell to {july["txn"]}. This is the proximate cause of the revenue decline &mdash; fewer people are buying, even as more people are attending.</div>
      </div>
    </div>''',
        f'''<div class="insight-card">
      <div class="insight-num">05</div>
      <div class="insight-body">
        <div class="insight-title">Churn rate is stable but the lapsed book is growing.</div>
        <div class="insight-text">{lj["lapsed"]} members lapsed in July at a {lj["churn_rate"]:.1f}% churn rate &mdash; broadly stable vs June&rsquo;s {ljun["churn_rate"]:.1f}%. But cumulative unique lapsed members now stand at <strong>{R["cumulative_lapsed_unique"]}</strong>, and only <strong>{R["active"]["total"]}</strong> active memberships remain. The renewal engine renewed {lj["renewed"]} of {lj["expirations"]} expirations ({lj["renewal_rate"]:.1f}%), but the gap between lapses and renewals is widening in absolute terms.</div>
      </div>
    </div>''',
        f'''<div class="insight-card">
      <div class="insight-num">06</div>
      <div class="insight-body">
        <div class="insight-title">June was a strong month that set a high bar.</div>
        <div class="insight-text">June delivered <strong>{fmt_l(june["net"])}</strong> net sales with {fjun["converted"]} conversions at {fjun["conv_rate"]:.1f}%, {sejun["visits"]:,} visits, and {june["members"]} buyers &mdash; all above baseline. July&rsquo;s decline is measured against a genuinely strong June, not a weak one. The two-month picture is one of a strong June followed by a volume-led but revenue-soft July.</div>
      </div>
    </div>''',
    ]

    worked = [
        f'''<div class="worked-card worked">
      <div class="worked-icon">+</div>
      <div class="worked-body">
        <div class="worked-title">Visit volume and fill rate hit eight-month highs.</div>
        <div class="worked-text">{sej["visits"]:,} visits across {sej["sessions"]} sessions at {sej["fill"]:.1f}% fill &mdash; up from {sejun["visits"]:,} visits at {sejun["fill"]:.1f}% in June. Only {sej["empty"]} empty sessions. The schedule is delivering attendance at a rate the studio has not seen since January.</div>
      </div>
    </div>''',
        f'''<div class="worked-card worked">
      <div class="worked-icon">+</div>
      <div class="worked-body">
        <div class="worked-title">Discount discipline fully restored post-anniversary.</div>
        <div class="worked-text">Discount value at {fmt_l(july["disc"])} is {pc(july["disc"],june["disc"]):.0f}% below June and {pc(july["disc"],base["disc"]):.0f}% below the Jan&ndash;Mar baseline. Discount efficiency at &#8377;{july["disc_eff"]:.2f} is the best reading of 2026 &mdash; every rupee of discount now generates {july["disc_eff"]:.1f}x in net revenue.</div>
      </div>
    </div>''',
        f'''<div class="worked-card worked">
      <div class="worked-icon">+</div>
      <div class="worked-body">
        <div class="worked-title">Lead pipeline grew month-on-month.</div>
        <div class="worked-text">{fj["leads"]} leads in July vs {fjun["leads"]} in June &mdash; a {pc(fj["leads"],fjun["leads"]):.0f}% increase. The top-of-funnel is not the constraint; the breakdown is in the conversion stage, which is a more addressable problem than lead scarcity.</div>
      </div>
    </div>''',
        f'''<div class="worked-card worked">
      <div class="worked-icon">+</div>
      <div class="worked-body">
        <div class="worked-title">Average transaction value held above baseline.</div>
        <div class="worked-text">ATV at {fmt_r(july_atv)} is {pc(july_atv,base_atv):.1f}% above the Jan&ndash;Mar baseline of {fmt_r(base_atv)}, despite the buyer contraction. Those who are buying are spending at healthy ticket sizes &mdash; the issue is buyer count, not pricing.</div>
      </div>
    </div>''',
        f'''<div class="worked-card worked">
      <div class="worked-icon">+</div>
      <div class="worked-body">
        <div class="worked-title">Renewal volume kept pace with rising expirations.</div>
        <div class="worked-text">{lj["renewed"]} renewals from {lj["expirations"]} expirations ({lj["renewal_rate"]:.1f}%) &mdash; renewal rate held within 0.4pp of June despite a {pc(lj["expirations"],ljun["expirations"]):.0f}% increase in expiration volume. The renewal engine is scaling with the membership base.</div>
      </div>
    </div>''',
        f'''<div class="worked-card worked">
      <div class="worked-icon">+</div>
      <div class="worked-body">
        <div class="worked-title">Late-cancel volume fell even as bookings rose.</div>
        <div class="worked-text">{cj["late_cancel"]} late cancels vs {cjun["late_cancel"]} in June, despite {pc(sej["booked"],sejun["booked"]):.0f}% more bookings. Heavy cancelers (6+ cancels) fell from {cjun["heavy_cancelers"]} to {cj["heavy_cancelers"]}. Booking discipline is improving.</div>
      </div>
    </div>''',
    ]

    didnt = [
        f'''<div class="worked-card didnt">
      <div class="worked-icon">&minus;</div>
      <div class="worked-body">
        <div class="worked-title">Net sales contracted 32% month-on-month.</div>
        <div class="worked-text">{fmt_l(july["net"])} vs {fmt_l(june["net"])} in June &mdash; a {pc(july["net"],june["net"]):.1f}% decline. This is {pc(july["net"],base["net"]):.1f}% below the Jan&ndash;Mar baseline, making July the weakest revenue month of 2026 outside of the seasonal lows.</div>
      </div>
    </div>''',
        f'''<div class="worked-card didnt">
      <div class="worked-icon">&minus;</div>
      <div class="worked-body">
        <div class="worked-title">Conversion rate halved to 9.9%.</div>
        <div class="worked-text">{fj["converted"]} conversions from {fj["leads"]} leads (9.9%) vs {fjun["converted"]} from {fjun["leads"]} (24.2%) in June. The lead-to-member conversion mechanism deteriorated sharply &mdash; the single biggest operational issue this month.</div>
      </div>
    </div>''',
        f'''<div class="worked-card didnt">
      <div class="worked-icon">&minus;</div>
      <div class="worked-body">
        <div class="worked-title">Buyer count fell to 128 &mdash; the lowest of 2026.</div>
        <div class="worked-text">{july["members"]} unique buyers is {pc(july["members"],june["members"]):.1f}% below June and {pc(july["members"],base["members"]):.1f}% below baseline. {july["txn"]} transactions is also the lowest of the year. Attendance is up but the paying base is shrinking.</div>
      </div>
    </div>''',
        f'''<div class="worked-card didnt">
      <div class="worked-icon">&minus;</div>
      <div class="worked-body">
        <div class="worked-title">Website and walk-in channels converted zero leads.</div>
        <div class="worked-text">25 Website leads and 7 walk-in leads each produced 0 conversions. Together, these channels consumed 32 leads (21% of the pipeline) and generated zero revenue &mdash; the largest leakage point in the funnel.</div>
      </div>
    </div>''',
        f'''<div class="worked-card didnt">
      <div class="worked-icon">&minus;</div>
      <div class="worked-body">
        <div class="worked-title">Hosted-class funnel continued to under-convert.</div>
        <div class="worked-text">34 Hosted Class leads &rarr; only 1 conversion (2.9%). This is structurally consistent with May&rsquo;s 3.4% rate. The hosted-class format generates attendance but not buyers &mdash; a persistent conversion gap.</div>
      </div>
    </div>''',
        f'''<div class="worked-card didnt">
      <div class="worked-icon">&minus;</div>
      <div class="worked-body">
        <div class="worked-title">Absolute lapsed count rose despite stable churn.</div>
        <div class="worked-text">{lj["lapsed"]} lapsed members vs {ljun["lapsed"]} in June &mdash; a {pc(lj["lapsed"],ljun["lapsed"]):.1f}% increase. While the churn rate is stable at ~41%, the growing membership base means more absolute lapses each month. Cumulative unique lapsed now stands at {R["cumulative_lapsed_unique"]}.</div>
      </div>
    </div>''',
        f'''<div class="worked-card didnt">
      <div class="worked-icon">&minus;</div>
      <div class="worked-body">
        <div class="worked-title">Session revenue grew but sales revenue fell.</div>
        <div class="worked-text">Session-attributed revenue rose to {fmt_l(sej["revenue"])} ({pc(sej["revenue"],sejun["revenue"]):.1f}% MoM), yet product sales fell to {fmt_l(july["gross"])}. The gap suggests members are attending on existing packages rather than purchasing new ones &mdash; a consumption-over-acquisition pattern.</div>
      </div>
    </div>''',
    ]

    actions = [
        f'''<div class="action-card">
      <div class="action-num">01</div>
      <div class="action-body">
        <div class="action-title">Repair the conversion funnel as the #1 priority.</div>
        <div class="action-text">The conversion rate halved from 24.2% to 9.9% despite a larger lead pipeline. Audit the trial-to-sale handoff process: assign a dedicated conversion owner per trial, implement a 48-hour post-trial follow-up cadence (Day 1 thank-you, Day 3 trainer check-in, Day 7 limited-time offer), and target a return to 20%+ conversion by September. The {fj["leads"]} leads are there &mdash; the mechanism to convert them is not.</div>
        <div class="action-meta">
          <span class="meta-pill">Owner: Studio Head + Member Experience</span>
          <span class="meta-pill">Priority: Critical</span>
          <span class="meta-pill">Impact: High</span>
        </div>
      </div>
    </div>''',
        f'''<div class="action-card">
      <div class="action-num">02</div>
      <div class="action-body">
        <div class="action-title">Monetise the attendance surge with package conversion drives.</div>
        <div class="action-text">{sej["visits"]:,} visits at {sej["fill"]:.1f}% fill represents the highest attendance in 8 months, but only {july["members"]} buyers transacted. Launch a &ldquo;visit-to-value&rdquo; campaign: identify the top 50 highest-attending non-members and offer a time-limited package upgrade. Target: convert 15% of high-frequency drop-in attendees to package holders within 30 days.</div>
        <div class="action-meta">
          <span class="meta-pill">Owner: Sales + Operations</span>
          <span class="meta-pill">Priority: High</span>
          <span class="meta-pill">Impact: High</span>
        </div>
      </div>
    </div>''',
        f'''<div class="action-card">
      <div class="action-num">03</div>
      <div class="action-body">
        <div class="action-title">Fix the zero-conversion channels (Website, Walk-in).</div>
        <div class="action-text">32 leads from Website (25) and Walk-in (7) channels produced zero conversions. Instrument the website form with a 2-hour first-response SLA, and assign walk-in leads to a specific front-desk closer with a same-day follow-up requirement. These are high-intent channels &mdash; the leakage is operational, not demand-side.</div>
        <div class="action-meta">
          <span class="meta-pill">Owner: Front Desk + Marketing</span>
          <span class="meta-pill">Priority: High</span>
          <span class="meta-pill">Impact: Medium</span>
        </div>
      </div>
    </div>''',
        f'''<div class="action-card">
      <div class="action-num">04</div>
      <div class="action-body">
        <div class="action-title">Sustain the discount discipline &mdash; do not relax.</div>
        <div class="action-text">July&rsquo;s discount efficiency of &#8377;{july["disc_eff"]:.2f} is the best of 2026. Maintain the hard-cap framework introduced post-May: discount penetration below 12%, Privates on a no-discount list, and discount authority limited to the Studio Head. The temptation to discount-drive revenue in a soft month must be resisted &mdash; the May experience proves it destroys efficiency.</div>
        <div class="action-meta">
          <span class="meta-pill">Owner: Studio Head + Finance</span>
          <span class="meta-pill">Priority: Medium</span>
          <span class="meta-pill">Impact: Medium</span>
        </div>
      </div>
    </div>''',
        f'''<div class="action-card">
      <div class="action-num">05</div>
      <div class="action-body">
        <div class="action-title">Reactivate the lapsed book with a tiered win-back campaign.</div>
        <div class="action-text">{R["cumulative_lapsed_unique"]} cumulative unique lapsed members represent the highest-leverage revenue opportunity. Segment by recency (lapsed &lt;3 months, 3&ndash;6 months, 6+ months) and product type (1-Month Unlimited holders are the largest segment at {R["cumulative_lapsed_byprod"].get("Studio 1 Month Unlimited Membership",0)}). Offer a tiered win-back: free class + discounted restart for &lt;3mo, referral-credit for 3&ndash;6mo, fresh-trial for 6+mo. Target: 50 reactivations in Q3.</div>
        <div class="action-meta">
          <span class="meta-pill">Owner: Member Experience + Studio Head</span>
          <span class="meta-pill">Priority: High</span>
          <span class="meta-pill">Impact: High</span>
        </div>
      </div>
    </div>''',
    ]

    conclusions = [
        f'''<div class="conclusion-item">
      <span class="conclusion-num">01</span>
      <span class="conclusion-text"><strong>July is a volume-without-revenue month &mdash; the opposite of the May anniversary problem.</strong> The studio has never been busier ({sej["visits"]:,} visits, {sej["fill"]:.1f}% fill), yet net sales at {fmt_l(july["net"])} are the lowest of 2026. The issue is buyer count ({july["members"]}), not attendance or pricing.</span>
    </div>''',
        f'''<div class="conclusion-item">
      <span class="conclusion-num">02</span>
      <span class="conclusion-text"><strong>The conversion funnel is the binding constraint.</strong> A 9.9% conversion rate with 151 leads means 136 leads entered the studio and left without buying. Restoring conversion to June&rsquo;s 24.2% alone would add ~21 conversions and approximately {fmt_l(fj["leads"]*0.242*july_atv)} in monthly revenue.</span>
    </div>''',
        f'''<div class="conclusion-item">
      <span class="conclusion-num">03</span>
      <span class="conclusion-text"><strong>Discount discipline is the one structural win to protect.</strong> July&rsquo;s &#8377;{july["disc_eff"]:.2f} discount efficiency is the best of 2026 and validates the post-May correction. Any short-term temptation to discount-drive revenue in a soft month would reverse this gain &mdash; the data is unambiguous.</span>
    </div>''',
        f'''<div class="conclusion-item">
      <span class="conclusion-num">04</span>
      <span class="conclusion-text"><strong>June was a genuinely strong month &mdash; July&rsquo;s decline is not a reversion to a weak norm.</strong> June&rsquo;s {fmt_l(june["net"])} net, {fjun["converted"]} conversions, and {june["members"]} buyers all exceeded baseline. The two-month picture is strong-then-soft, not a sustained deterioration &mdash; but the trend direction demands intervention.</span>
    </div>''',
        f'''<div class="conclusion-item">
      <span class="conclusion-num">05</span>
      <span class="conclusion-text"><strong>The lapsed book is the largest unrealised revenue pool.</strong> {R["cumulative_lapsed_unique"]} cumulative unique lapsed members &mdash; led by {R["cumulative_lapsed_byprod"].get("Studio 1 Month Unlimited Membership",0)} 1-Month Unlimited holders &mdash; represent a reactivation opportunity worth an estimated &#8377;35&ndash;50L in LTV recovery if even 15% are reactivated.</span>
    </div>''',
        f'''<div class="conclusion-item">
      <span class="conclusion-num">06</span>
      <span class="conclusion-text"><strong>Attendance and sales are now decoupled &mdash; this is a strategic warning sign.</strong> When visits rise 7% MoM while sales fall 32%, the business model is leaking value at the attendance-to-purchase boundary. The fix is not more attendance &mdash; it is better conversion of existing attendance into recurring revenue.</span>
    </div>''',
        f'''<div class="conclusion-item">
      <span class="conclusion-num">07</span>
      <span class="conclusion-text"><strong>The studio is one conversion-focused quarter from a structural step-up.</strong> If the conversion rate is restored to 20%+ and the discount discipline is held, the attendance base of 2,400+ monthly visits provides the raw material for &#8377;25&ndash;30L net sales &mdash; a 75&ndash;110% lift from July&rsquo;s &#8377;14.13L.</span>
    </div>''',
    ]

    return f'''
<section class="report-section" id="executive-summary">
  <div class="container">
    <div class="section-header">
      <div class="section-header-left">
        <span class="section-eyebrow">01 &middot; Executive Summary</span>
        <h2 class="section-title">July delivered the highest attendance in eight months but the lowest revenue of 2026 &mdash; the studio has a conversion problem, not a demand problem.</h2>
        <p class="section-deck">
          Headline revenue contracted to <strong>{fmt_l(july["net"])}</strong>, down {pc(july["net"],june["net"]):.1f}% from June and
          {pc(july["net"],base["net"]):.1f}% below the Jan &ndash; Mar baseline. The proximate cause is buyer count: only
          <strong>{july["members"]} unique buyers</strong> transacted &mdash; the lowest of 2026 &mdash; even as visits hit
          <strong>{sej["visits"]:,}</strong> at <strong>{sej["fill"]:.1f}% fill</strong>. The conversion rate halved to
          <strong>{fj["conv_rate"]:.1f}%</strong>. The structural positive is <strong>discount discipline</strong>: at
          {fmt_l(july["disc"])} and &#8377;{july["disc_eff"]:.2f} efficiency, July is the most discount-disciplined month of the year.
        </p>
      </div>
      <div class="section-anchor">Section 01 / 07</div>
    </div>

    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">Key Insights &middot; July 2026</div>
        {''.join(insights)}
      </div>
      <div class="data-pane">
        <div class="pane-title">Headline KPI Comparison</div>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Metric</th>
                <th>Jul 2026</th>
                <th>Jun 2026</th>
                <th>Jan &ndash; Mar Avg</th>
                <th>Jul vs Baseline</th>
                <th>Jul vs Jun</th>
              </tr>
            </thead>
            <tbody>
              {''.join(rows)}
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div class="subsection">
      <h3 class="subsection-title">What worked / What did not work</h3>
      <p class="subsection-deck">A balanced read on July 2026 &mdash; every item below is anchored to a number in the headline KPI table above.</p>
    </div>
    <div class="worked-grid">
      {''.join(worked)}
      {''.join(didnt)}
    </div>

    <div class="subsection">
      <h3 class="subsection-title">Action items for the next 30 days</h3>
      <p class="subsection-deck">Each action is anchored to a metric in the table above and assigned an owner, a priority, and an impact rating.</p>
    </div>
    <div class="action-grid">
      {''.join(actions)}
    </div>

    <div class="subsection">
      <h3 class="subsection-title">Data-backed conclusions for senior management</h3>
    </div>
    <div class="conclusions-block">
      {''.join(conclusions)}
    </div>
  </div>
</section>'''


# ============ SECTION 02: REVENUE & SALES PERFORMANCE ============
def section_02():
    # Category table
    cat_order = ['Memberships', 'Class Packages', 'Sessions/Single Classes', 'Privates', 'Retail', 'Money Credits', 'Newcomers Special', 'Others']
    cat_rows = []
    total_gross = 0; total_units = 0; total_disc = 0
    for c in cat_order:
        j = cat(july, c)
        jun = cat(june, c)
        if j[0] == 0 and jun[0] == 0: continue
        total_gross += j[0]; total_units += j[1]; total_disc += j[2]
        share = j[0]/july['gross']*100 if july['gross'] else 0
        mom = pc(j[0], jun[0])
        disc_ratio = j[2]/j[0]*100 if j[0] else 0
        share_bar_w = share
        cat_rows.append(f'''<tr>
          <td class="metric-name">{c}</td>
          <td class="num"><strong>{fmt_l(j[0])}</strong></td>
          <td class="num">{j[1]}</td>
          <td class="num">{fmt_l(jun[0])}</td>
          <td class="num">{badge(mom)}</td>
          <td class="num">{share:.1f}%</td>
          <td class="num"><div class="share-bar"><div class="share-fill" style="width:{share_bar_w*1.2:.0f}px"></div></div></td>
          <td class="num">{disc_ratio:.1f}%</td>
        </tr>''')
    cat_rows.append(f'''<tr class="totals-row">
      <td class="metric-name">Total</td>
      <td class="num">{fmt_l(total_gross)}</td>
      <td class="num">{total_units}</td>
      <td class="num">{fmt_l(june['gross'])}</td>
      <td class="num">{badge(pc(total_gross, june['gross']))}</td>
      <td class="num">100.0%</td>
      <td class="num"></td>
      <td class="num">{total_disc/total_gross*100:.1f}%</td>
    </tr>''')

    # Top products
    prod_items = sorted(july['prods'].items(), key=lambda x: -x[1][0])[:12]
    prod_rows = []
    for name, (rev, units, disc) in prod_items:
        jun_p = june['prods'].get(name, [0,0,0])
        mom = pc(rev, jun_p[0])
        disc_ratio = disc/rev*100 if rev else 0
        prod_rows.append(f'''<tr>
          <td class="metric-name">{esc(name)}</td>
          <td class="num"><strong>{fmt_l(rev)}</strong></td>
          <td class="num">{units}</td>
          <td class="num">{fmt_l(jun_p[0])}</td>
          <td class="num">{badge(mom)}</td>
          <td class="num">{disc_ratio:.1f}%</td>
        </tr>''')

    # Seller table
    seller_items = sorted(july['sellers'].items(), key=lambda x: -x[1][0])
    seller_rows = []
    for name, (rev, txn) in seller_items:
        jun_s = june['sellers'].get(name, [0,0])
        mom = pc(rev, jun_s[0])
        share = rev/july['gross']*100 if july['gross'] else 0
        seller_rows.append(f'''<tr>
          <td class="metric-name">{esc(name) if name != '-' else 'System / Unattributed'}</td>
          <td class="num"><strong>{fmt_l(rev)}</strong></td>
          <td class="num">{txn}</td>
          <td class="num">{fmt_r(rev/txn) if txn else '&mdash;'}</td>
          <td class="num">{fmt_l(jun_s[0])}</td>
          <td class="num">{badge(mom)}</td>
          <td class="num">{share:.1f}%</td>
        </tr>''')

    # Payment method
    pay_items = sorted(july['pay'].items(), key=lambda x: -x[1][0])
    pay_rows = []
    for name, (rev, txn) in pay_items:
        jun_p = june['pay'].get(name, [0,0])
        mom = pc(rev, jun_p[0])
        share = rev/july['gross']*100 if july['gross'] else 0
        pay_rows.append(f'''<tr>
          <td class="metric-name">{esc(name)}</td>
          <td class="num"><strong>{fmt_l(rev)}</strong></td>
          <td class="num">{txn}</td>
          <td class="num">{share:.1f}%</td>
          <td class="num">{fmt_l(jun_p[0])}</td>
          <td class="num">{badge(mom)}</td>
        </tr>''')

    insights = [
        f'''<div class="insight-card">
      <div class="insight-num">01</div>
      <div class="insight-body">
        <div class="insight-title">Memberships remain the revenue anchor at {L(july_mem[0]):.1f}L ({july_mem[0]/july['gross']*100:.0f}% of gross).</div>
        <div class="insight-text">Memberships delivered {fmt_l(july_mem[0])} across {july_mem[1]} transactions &mdash; the single largest revenue category. However, this is {pc(july_mem[0], june_mem[0]):.1f}% below June&rsquo;s {fmt_l(june_mem[0])}. The 1-Month and 3-Month Unlimited products drove the decline, while Annual Unlimited held steady.</div>
      </div>
    </div>''',
        f'''<div class="insight-card">
      <div class="insight-num">02</div>
      <div class="insight-body">
        <div class="insight-title">Class Packages contracted {pc(july_pkg[0], june_pkg[0]):.1f}% MoM.</div>
        <div class="insight-text">Class Packages generated {fmt_l(july_pkg[0])} from {july_pkg[1]} transactions vs {fmt_l(june_pkg[0])} from {june_pkg[1]} in June. The 12-Class and 8-Class packages &mdash; the studio&rsquo;s mid-tier workhorses &mdash; both saw fewer units sold, directly contributing to the buyer-count decline.</div>
      </div>
    </div>''',
        f'''<div class="insight-card">
      <div class="insight-num">03</div>
      <div class="insight-body">
        <div class="insight-title">Drop-in sales held steady &mdash; confirming the attendance-acquisition gap.</div>
        <div class="insight-text">Sessions/Single Classes generated {fmt_l(july_drop[0])} from {july_drop[1]} transactions, broadly flat vs June&rsquo;s {fmt_l(june_drop[0])}. This confirms the pattern: members are attending (and paying per-session) but not upgrading to packages or memberships &mdash; the consumption-over-acquisition dynamic.</div>
      </div>
    </div>''',
        f'''<div class="insight-card">
      <div class="insight-num">04</div>
      <div class="insight-body">
        <div class="insight-title">Privates discount ratio normalised to {july_priv[2]/july_priv[0]*100:.1f}%.</div>
        <div class="insight-text">Privates delivered {fmt_l(july_priv[0])} with {fmt_l(july_priv[2])} in discounts &mdash; a {july_priv[2]/july_priv[0]*100:.1f}% discount ratio, down dramatically from May&rsquo;s -52% ratio. The no-discount-Privates correction is working. Revenue is lower, but margin per session is positive for the first time in months.</div>
      </div>
    </div>''',
        f'''<div class="insight-card">
      <div class="insight-num">05</div>
      <div class="insight-body">
        <div class="insight-title">Custom (in-studio) payments dominate at {july['pay'].get('Custom (in-studio)',[0])[0]/july['gross']*100:.0f}% of gross.</div>
        <div class="insight-text">{fmt_l(july['pay'].get('Custom (in-studio)',[0])[0])} transacted in-studio across {july['pay'].get('Custom (in-studio)',[0])[1]} transactions &mdash; the largest payment channel. Cash contributed {fmt_l(july['pay'].get('Cash',[0])[0])} ({july['pay'].get('Cash',[0])[1]} txn) and Stripe online {fmt_l(july['pay'].get('Stripe (online)',[0])[0])} ({july['pay'].get('Stripe (online)',[0])[1]} txn).</div>
      </div>
    </div>''',
        f'''<div class="insight-card">
      <div class="insight-num">06</div>
      <div class="insight-body">
        <div class="insight-title">Seller mix is concentrated but healthy.</div>
        <div class="insight-text">The top seller drove {fmt_l(seller_items[0][1][0])} ({seller_items[0][1][0]/july['gross']*100:.0f}% of gross) across {seller_items[0][1][1]} transactions. The system/unattributed bucket at {fmt_l(july['sellers'].get('-',[0])[0])} represents online self-service purchases &mdash; a growing channel that needs better attribution tracking.</div>
      </div>
    </div>''',
    ]

    worked = [
        f'''<div class="worked-card worked">
      <div class="worked-icon">+</div>
      <div class="worked-body">
        <div class="worked-title">Privates margin turned positive.</div>
        <div class="worked-text">The Privates discount ratio normalised from May&rsquo;s -52% to {july_priv[2]/july_priv[0]*100:.1f}%, validating the no-discount-Privates policy. Every Private session sold in July was margin-positive.</div>
      </div>
    </div>''',
        f'''<div class="worked-card worked">
      <div class="worked-icon">+</div>
      <div class="worked-body">
        <div class="worked-title">Drop-in revenue held steady despite buyer contraction.</div>
        <div class="worked-text">{fmt_l(july_drop[0])} from {july_drop[1]} drop-in transactions &mdash; essentially flat vs June. The highest-attending members are still paying per-session, which provides a clear upgrade-conversion target.</div>
      </div>
    </div>''',
        f'''<div class="worked-card worked">
      <div class="worked-icon">+</div>
      <div class="worked-body">
        <div class="worked-title">Newcomers Special grew {pc(cat(july,'Newcomers Special')[0], cat(june,'Newcomers Special')[0]):.0f}% MoM.</div>
        <div class="worked-text">{fmt_l(cat(july,'Newcomers Special')[0])} from {cat(july,'Newcomers Special')[1]} transactions &mdash; the 2-For-1 newcomer offer is generating trial-to-purchase volume, a positive signal for the top of the funnel.</div>
      </div>
    </div>''',
    ]

    didnt = [
        f'''<div class="worked-card didnt">
      <div class="worked-icon">&minus;</div>
      <div class="worked-body">
        <div class="worked-title">Membership revenue fell {pc(july_mem[0], june_mem[0]):.1f}% MoM.</div>
        <div class="worked-text">{fmt_l(july_mem[0])} vs {fmt_l(june_mem[0])} &mdash; a {fmt_l(june_mem[0]-july_mem[0])} decline. The 1-Month Unlimited and 3-Month Unlimited products both saw fewer units, indicating the recurring-revenue engine is slowing.</div>
      </div>
    </div>''',
        f'''<div class="worked-card didnt">
      <div class="worked-icon">&minus;</div>
      <div class="worked-body">
        <div class="worked-title">Class Package units fell {pc(july_pkg[1], june_pkg[1]):.1f}%.</div>
        <div class="worked-text">{july_pkg[1]} package transactions vs {june_pkg[1]} in June. The 12-Class and 8-Class packages &mdash; the studio&rsquo;s mid-tier products &mdash; are the primary gap, with {june_pkg[1]-july_pkg[1]} fewer packages sold.</div>
      </div>
    </div>''',
        f'''<div class="worked-card didnt">
      <div class="worked-icon">&minus;</div>
      <div class="worked-body">
        <div class="worked-title">Transaction count at {july["txn"]} is the lowest of 2026.</div>
        <div class="worked-text">{july["txn"]} transactions is {pc(july["txn"],june["txn"]):.1f}% below June and {pc(july["txn"],base["txn"]):.1f}% below baseline. Every category except drop-ins and newcomers contracted in unit terms.</div>
      </div>
    </div>''',
        f'''<div class="worked-card didnt">
      <div class="worked-icon">&minus;</div>
      <div class="worked-body">
        <div class="worked-title">Retail revenue is sub-scale at {fmt_l(cat(july,'Retail')[0])}.</div>
        <div class="worked-text">Retail generated {fmt_l(cat(july,'Retail')[0])} from {cat(july,'Retail')[1]} transactions &mdash; just {cat(july,'Retail')[0]/july['gross']*100:.1f}% of gross. The studio is leaving a low-effort revenue stream underdeveloped.</div>
      </div>
    </div>''',
    ]

    actions = [
        f'''<div class="action-card">
      <div class="action-num">01</div>
      <div class="action-body">
        <div class="action-title">Launch a package upgrade campaign targeting high-frequency drop-in attendees.</div>
        <div class="action-text">The {july_drop[1]} drop-in transactions represent members who are already paying per-session. Identify the top 50 drop-in attendees by visit frequency and offer a time-limited 12-Class or 8-Class package at a 5% upgrade incentive (well within the discount discipline framework). Target: 15 package conversions in 30 days, adding ~{fmt_l(15*14000)} in revenue.</div>
        <div class="action-meta">
          <span class="meta-pill">Owner: Sales + Studio Head</span>
          <span class="meta-pill">Priority: High</span>
          <span class="meta-pill">Impact: High</span>
        </div>
      </div>
    </div>''',
        f'''<div class="action-card">
      <div class="action-num">02</div>
      <div class="action-body">
        <div class="action-title">Restore membership sales velocity with a structured renewal pipeline.</div>
        <div class="action-text">Membership revenue fell {pc(july_mem[0], june_mem[0]):.1f}% MoM. Build a 30-day-ahead renewal pipeline: every member with an expiry in the next 30 days gets a renewal touchpoint at Day -30, Day -14, and Day -7. Assign renewal ownership to specific sellers. Target: renewal rate above 60% (from current {lj["renewal_rate"]:.1f}%).</div>
        <div class="action-meta">
          <span class="meta-pill">Owner: Sales + Member Experience</span>
          <span class="meta-pill">Priority: High</span>
          <span class="meta-pill">Impact: High</span>
        </div>
      </div>
    </div>''',
        f'''<div class="action-card">
      <div class="action-num">03</div>
      <div class="action-body">
        <div class="action-title">Develop the Retail revenue stream.</div>
        <div class="action-text">Retail at {cat(july,'Retail')[0]/july['gross']*100:.1f}% of gross is well below its potential for a studio with {sej["visits"]:,} monthly visits. Curate a 5-product retail line (grip socks, water bottles, resistance bands, towels, apparel) and display at the front desk and in-studio. Target: Retail to 3% of gross (~{fmt_l(july['gross']*0.03)}) within 60 days.</div>
        <div class="action-meta">
          <span class="meta-pill">Owner: Operations</span>
          <span class="meta-pill">Priority: Medium</span>
          <span class="meta-pill">Impact: Low</span>
        </div>
      </div>
    </div>''',
    ]

    conclusions = [
        f'''<div class="conclusion-item">
      <span class="conclusion-num">01</span>
      <span class="conclusion-text"><strong>Membership and Package contraction is the primary revenue driver.</strong> Together these two categories fell {fmt_l((june_mem[0]+june_pkg[0])-(july_mem[0]+july_pkg[0]))} MoM &mdash; accounting for the majority of the revenue decline. These are the studio&rsquo;s recurring-revenue products; their decline signals a weakening of the membership base.</span>
    </div>''',
        f'''<div class="conclusion-item">
      <span class="conclusion-num">02</span>
      <span class="conclusion-text"><strong>Drop-in stability confirms the attendance-acquisition gap.</strong> Flat drop-in sales alongside rising visits means members are attending on pay-per-session terms rather than upgrading. This is both a warning sign (value leakage) and an opportunity (a clear upgrade target).</span>
    </div>''',
        f'''<div class="conclusion-item">
      <span class="conclusion-num">03</span>
      <span class="conclusion-text"><strong>The Privates margin correction is a structural win.</strong> Normalising the Privates discount ratio from -52% to {july_priv[2]/july_priv[0]*100:.1f}% means every Private session is now margin-positive. This validates the no-discount-Privates policy and should be locked in permanently.</span>
    </div>''',
        f'''<div class="conclusion-item">
      <span class="conclusion-num">04</span>
      <span class="conclusion-text"><strong>The Custom (in-studio) payment dominance is an attribution risk.</strong> {july['pay'].get('Custom (in-studio)',[0])[0]/july['gross']*100:.0f}% of gross transacting in-studio via custom payments means the studio lacks visibility into online vs offline purchase drivers. Better payment attribution would improve the seller performance picture.</span>
    </div>''',
    ]

    return f'''
<section class="report-section" id="revenue-performance">
  <div class="container">
    <div class="section-header">
      <div class="section-header-left">
        <span class="section-eyebrow">02 &middot; Revenue &amp; Sales Performance</span>
        <h2 class="section-title">Memberships and Class Packages drove the {pc(july['net'],june['net']):.0f}% revenue decline, while drop-in sales held steady &mdash; confirming an attendance-acquisition gap that is the studio&rsquo;s most addressable revenue lever.</h2>
        <p class="section-deck">
          Gross sales of <strong>{fmt_l(july['gross'])}</strong> are {pc(july['gross'],june['gross']):.1f}% below June and {pc(july['gross'],base['gross']):.1f}% below the Jan &ndash; Mar baseline.
          The decline is concentrated in Memberships ({pc(july_mem[0],june_mem[0]):.1f}% MoM) and Class Packages ({pc(july_pkg[0],june_pkg[0]):.1f}% MoM) &mdash; the studio&rsquo;s recurring-revenue
          products. Drop-in sales held flat, confirming that members are attending but not upgrading. Privates margin normalised
          after the May discount correction. Discount discipline at {fmt_l(july['disc'])} ({july.get('disc_pen',0):.1f}% penetration) is the best of 2026.
        </p>
      </div>
      <div class="section-anchor">Section 02 / 07</div>
    </div>

    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">Revenue insights &middot; July 2026</div>
        {''.join(insights)}
      </div>
      <div class="data-pane">
        <div class="pane-title">Sales by Category</div>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Category</th>
                <th>Jul Revenue</th>
                <th>Units</th>
                <th>Jun Revenue</th>
                <th>MoM</th>
                <th>Share</th>
                <th>Mix</th>
                <th>Disc Ratio</th>
              </tr>
            </thead>
            <tbody>
              {''.join(cat_rows)}
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div class="subsection">
      <h3 class="subsection-title">Top Products &mdash; where the money actually came from</h3>
      <p class="subsection-deck">The 12 highest-revenue products in July 2026, sorted by gross revenue. Discount ratio is discount value as a percentage of product revenue.</p>
    </div>
    <div class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>Product</th>
            <th>Jul Revenue</th>
            <th>Units</th>
            <th>Jun Revenue</th>
            <th>MoM</th>
            <th>Disc Ratio</th>
          </tr>
        </thead>
        <tbody>
          {''.join(prod_rows)}
        </tbody>
      </table>
    </div>

    <div class="subsection">
      <h3 class="subsection-title">Seller performance &mdash; concentration and attribution gap</h3>
      <p class="subsection-deck">Every seller who transacted in July 2026, sorted by gross revenue. ATV = average transaction value. &ldquo;System / Unattributed&rdquo; captures online self-service purchases.</p>
    </div>
    <div class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>Seller</th>
            <th>Jul Revenue</th>
            <th>Txn</th>
            <th>ATV</th>
            <th>Jun Revenue</th>
            <th>MoM</th>
            <th>Share</th>
          </tr>
        </thead>
        <tbody>
          {''.join(seller_rows)}
        </tbody>
      </table>
    </div>

    <div class="subsection">
      <h3 class="subsection-title">Payment method &mdash; channel mix and operational implications</h3>
      <p class="subsection-deck">Revenue split by payment method. &ldquo;Custom (in-studio)&rdquo; includes bank transfers, UPI, and other non-cash/non-card in-studio payments.</p>
    </div>
    <div class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>Payment Method</th>
            <th>Jul Revenue</th>
            <th>Txn</th>
            <th>Share</th>
            <th>Jun Revenue</th>
            <th>MoM</th>
          </tr>
        </thead>
        <tbody>
          {''.join(pay_rows)}
        </tbody>
      </table>
    </div>

    <div class="subsection">
      <h3 class="subsection-title">What worked / What did not work</h3>
    </div>
    <div class="worked-grid">
      {''.join(worked)}
      {''.join(didnt)}
    </div>

    <div class="subsection">
      <h3 class="subsection-title">Action items</h3>
    </div>
    <div class="action-grid">
      {''.join(actions)}
    </div>

    <div class="subsection">
      <h3 class="subsection-title">Data-backed conclusions</h3>
    </div>
    <div class="conclusions-block">
      {''.join(conclusions)}
    </div>
  </div>
</section>'''


# ============ SECTION 03: CONVERSION FUNNEL ============
def section_03():
    leads_mom = pc(fj['leads'], fjun['leads'])
    trials_mom = pc(fj['trials'], fjun['trials'])
    conv_mom = pc(fj['converted'], fjun['converted'])
    ret_mom = pc(fj['retained'], fjun['retained'])

    # Source table
    src_items = sorted(fj['src'].items(), key=lambda x: -x[1][0])
    src_rows = []
    for name, (leads, trials, conv, ltv, visits) in src_items:
        cr = conv/leads*100 if leads else 0
        rr = 0  # retained rate approx
        src_rows.append(f'''<tr>
          <td class="metric-name">{esc(name)}</td>
          <td class="num">{leads}</td>
          <td class="num">{trials}</td>
          <td class="num"><strong>{conv}</strong></td>
          <td class="num">{cr:.1f}%</td>
          <td class="num">{visits:.0f}</td>
          <td class="num">{fmt_r(ltv) if ltv else '&mdash;'}</td>
        </tr>''')
    src_rows.append(f'''<tr class="totals-row">
      <td class="metric-name">Total</td>
      <td class="num">{fj["leads"]}</td>
      <td class="num">{fj["trials"]}</td>
      <td class="num">{fj["converted"]}</td>
      <td class="num">{fj["conv_rate"]:.1f}%</td>
      <td class="num">{fj["lead_visits"]}</td>
      <td class="num">{fmt_r(fj["lead_ltv"])}</td>
    </tr>''')

    # Trial types
    tt_items = sorted(fj['trial_types'].items(), key=lambda x: -x[1])
    tt_rows = []
    for name, count in tt_items:
        tt_rows.append(f'''<tr>
          <td class="metric-name">{esc(name)}</td>
          <td class="num"><strong>{count}</strong></td>
          <td class="num">{count/fj["trials"]*100:.1f}%</td>
        </tr>''')

    # MoM flow table
    mom_months = ['2026-01','2026-02','2026-03','2026-04','2026-05','2026-06','2026-07']
    mom_rows = []
    for m in mom_months:
        f = F[m]
        lbl = m.split('-')[1] + ' ' + m.split('-')[0]
        is_july = m == '2026-07'
        strong_open = '<strong>' if is_july else ''
        strong_close = '</strong>' if is_july else ''
        mom_rows.append(f'''<tr>
          <td class="metric-name">{strong_open}{lbl}{strong_close}</td>
          <td class="num">{strong_open}{f["leads"]}{strong_close}</td>
          <td class="num">{strong_open}{f["trials"]}{strong_close}</td>
          <td class="num">{strong_open}{f["converted"]}{strong_close}</td>
          <td class="num">{strong_open}{f["conv_rate"]:.1f}%{strong_close}</td>
          <td class="num">{strong_open}{f["retained"]}{strong_close}</td>
        </tr>''')

    insights = [
        f'''<div class="insight-card">
      <div class="insight-num">01</div>
      <div class="insight-body">
        <div class="insight-title">Lead pipeline grew but conversion collapsed.</div>
        <div class="insight-text">{fj["leads"]} leads in July vs {fjun["leads"]} in June (+{leads_mom:.0f}%), yet conversions fell from {fjun["converted"]} to {fj["converted"]} ({conv_mom:.1f}%). The funnel is wider at the top and narrower at the bottom &mdash; a conversion-stage breakdown, not a lead-generation problem.</div>
      </div>
    </div>''',
        f'''<div class="insight-card">
      <div class="insight-num">02</div>
      <div class="insight-body">
        <div class="insight-title">Client Referral remains the highest-quality channel.</div>
        <div class="insight-text">33 Client Referral leads &rarr; 4 conversions (12.1%) &rarr; &#8377;{fj["src"]["Client Referral"][3]:,.0f} LTV. While below June&rsquo;s 31.6% referral conversion rate, referrals still produced the most conversions of any source and the highest LTV. The referral mechanism works &mdash; it needs more volume.</div>
      </div>
    </div>''',
        f'''<div class="insight-card">
      <div class="insight-num">03</div>
      <div class="insight-body">
        <div class="insight-title">Website and walk-in channels converted zero leads.</div>
        <div class="insight-text">25 Website leads and 7 walk-in leads each produced 0 conversions and &#8377;0 LTV. These are high-intent channels &mdash; a walk-in has physically come to the studio &mdash; yet the conversion mechanism is completely broken. This is the single biggest fixable leakage in the funnel.</div>
      </div>
    </div>''',
        f'''<div class="insight-card">
      <div class="insight-num">04</div>
      <div class="insight-body">
        <div class="insight-title">WhatsApp and incoming-call channels over-indexed on conversion.</div>
        <div class="insight-text">Yellow Messenger/WhatsApp: 12 leads &rarr; 3 conversions (25%) &rarr; &#8377;{fj["src"]["Yellow Messenger/Whatsapp Enquiry"][3]:,.0f} LTV. Incoming call: 8 leads &rarr; 3 conversions (37.5%). Conversational channels convert at 2&ndash;3&times; the portfolio average &mdash; the human touchpoint is the differentiator.</div>
      </div>
    </div>''',
        f'''<div class="insight-card">
      <div class="insight-num">05</div>
      <div class="insight-body">
        <div class="insight-title">Trial Class remains the dominant trial format.</div>
        <div class="insight-text">{fj["trial_types"].get("New - Trial Class",0)} Trial Class attendees (40% of all trials), followed by {fj["trial_types"].get("New - Hosted Class",0)} Hosted Class trials and {fj["trial_types"].get("New - Referral Class",0)} Referral Class trials. The trial format mix is healthy &mdash; the issue is what happens after the trial.</div>
      </div>
    </div>''',
        f'''<div class="insight-card">
      <div class="insight-num">06</div>
      <div class="insight-body">
        <div class="insight-title">Retained members fell {pc(fj["retained"],fjun["retained"]):.0f}% MoM.</div>
        <div class="insight-text">{fj["retained"]} retained members vs {fjun["retained"]} in June &mdash; a {pc(fj["retained"],fjun["retained"]):.1f}% decline. Retention rate fell from {fjun["retain_rate"]:.1f}% to {fj["retain_rate"]:.1f}%. The conversion problem is cascading into the retention metric &mdash; fewer conversions means fewer members to retain.</div>
      </div>
    </div>''',
    ]

    worked = [
        f'''<div class="worked-card worked">
      <div class="worked-icon">+</div>
      <div class="worked-body">
        <div class="worked-title">Lead pipeline grew {leads_mom:.0f}% MoM.</div>
        <div class="worked-text">{fj["leads"]} leads vs {fjun["leads"]} in June. The top-of-funnel is healthy and growing &mdash; demand generation is not the problem.</div>
      </div>
    </div>''',
        f'''<div class="worked-card worked">
      <div class="worked-icon">+</div>
      <div class="worked-body">
        <div class="worked-title">WhatsApp and call channels converted at 25&ndash;37%.</div>
        <div class="worked-text">Conversational channels (WhatsApp, incoming call) converted at 2&ndash;3&times; the portfolio average, proving that human touchpoints drive conversion. This insight should inform the follow-up process for all channels.</div>
      </div>
    </div>''',
        f'''<div class="worked-card worked">
      <div class="worked-icon">+</div>
      <div class="worked-body">
        <div class="worked-title">Client Referral produced the most conversions and highest LTV.</div>
        <div class="worked-text">4 conversions and &#8377;{fj["src"]["Client Referral"][3]:,.0f} LTV from 33 referral leads. The referral program is the studio&rsquo;s highest-quality acquisition channel and deserves more investment.</div>
      </div>
    </div>''',
    ]

    didnt = [
        f'''<div class="worked-card didnt">
      <div class="worked-icon">&minus;</div>
      <div class="worked-body">
        <div class="worked-title">Conversion rate halved to {fj["conv_rate"]:.1f}%.</div>
        <div class="worked-text">{fj["converted"]} conversions from {fj["leads"]} leads vs {fjun["converted"]} from {fjun["leads"]} (24.2%) in June. {fj["leads"]-fj["converted"]} leads entered the studio and left without buying &mdash; the largest single-point revenue leakage this month.</div>
      </div>
    </div>''',
        f'''<div class="worked-card didnt">
      <div class="worked-icon">&minus;</div>
      <div class="worked-body">
        <div class="worked-title">Website channel: 25 leads, 0 conversions.</div>
        <div class="worked-text">The Website is the second-largest lead source (25 leads) yet produced zero conversions and zero LTV. The website form &rarr; trial &rarr; sale handoff is completely broken.</div>
      </div>
    </div>''',
        f'''<div class="worked-card didnt">
      <div class="worked-icon">&minus;</div>
      <div class="worked-body">
        <div class="worked-title">Hosted Class conversion stayed at 2.9%.</div>
        <div class="worked-text">34 Hosted Class leads &rarr; 1 conversion. This is structurally consistent with May&rsquo;s 3.4% rate. The hosted-class format generates attendance but not buyers &mdash; a persistent, multi-month conversion gap.</div>
      </div>
    </div>''',
        f'''<div class="worked-card didnt">
      <div class="worked-icon">&minus;</div>
      <div class="worked-body">
        <div class="worked-title">Retained members fell {pc(fj["retained"],fjun["retained"]):.0f}% MoM.</div>
        <div class="worked-text">{fj["retained"]} retained vs {fjun["retained"]} in June. The retention rate dropped from {fjun["retain_rate"]:.1f}% to {fj["retain_rate"]:.1f}%. The conversion decline is cascading into retention.</div>
      </div>
    </div>''',
        f'''<div class="worked-card didnt">
      <div class="worked-icon">&minus;</div>
      <div class="worked-body">
        <div class="worked-title">Walk-in leads: 7 leads, 0 conversions.</div>
        <div class="worked-text">A walk-in has physically entered the studio &mdash; the highest possible intent. Zero conversions from 7 walk-ins indicates a front-desk conversion process failure, not a demand problem.</div>
      </div>
    </div>''',
    ]

    actions = [
        f'''<div class="action-card">
      <div class="action-num">01</div>
      <div class="action-body">
        <div class="action-title">Implement a mandatory 48-hour post-trial follow-up cadence.</div>
        <div class="action-text">Every trial attendee gets a structured 3-touch follow-up: Day 1 thank-you + class recommendation from the trainer, Day 3 personal check-in call from front desk, Day 7 limited-time offer (e.g. 5% off first package, valid 48 hours). Assign a conversion owner per trial. Target: conversion rate back to 20%+ by September.</div>
        <div class="action-meta">
          <span class="meta-pill">Owner: Member Experience + Trainers</span>
          <span class="meta-pill">Priority: Critical</span>
          <span class="meta-pill">Impact: High</span>
        </div>
      </div>
    </div>''',
        f'''<div class="action-card">
      <div class="action-num">02</div>
      <div class="action-body">
        <div class="action-title">Fix the Website lead-to-trial handoff with a 2-hour SLA.</div>
        <div class="action-text">25 website leads produced 0 conversions. Instrument the website form with a 2-hour first-response SLA: every form submission triggers an SMS + call within 2 business hours. Assign a dedicated online-lead closer. The website is the #2 lead source &mdash; it should not be a zero-conversion channel.</div>
        <div class="action-meta">
          <span class="meta-pill">Owner: Front Desk + Marketing</span>
          <span class="meta-pill">Priority: High</span>
          <span class="meta-pill">Impact: High</span>
        </div>
      </div>
    </div>''',
        f'''<div class="action-card">
      <div class="action-num">03</div>
      <div class="action-body">
        <div class="action-title">Scale the Client Referral program.</div>
        <div class="action-text">Client Referrals delivered 4 conversions and &#8377;{fj["src"]["Client Referral"][3]:,.0f} LTV at 12.1% conversion &mdash; the highest-quality channel. Launch a structured &#8377;1,500 dual-incentive referral (referrer + referee each get &#8377;1,500 credit on first purchase). Target: 50 referral leads/month (from 33), adding ~6 conversions.</div>
        <div class="action-meta">
          <span class="meta-pill">Owner: Marketing + Studio Head</span>
          <span class="meta-pill">Priority: High</span>
          <span class="meta-pill">Impact: High</span>
        </div>
      </div>
    </div>''',
        f'''<div class="action-card">
      <div class="action-num">04</div>
      <div class="action-body">
        <div class="action-title">Pilot a hosted-class conversion playbook.</div>
        <div class="action-text">Hosted Class conversion has been 3&ndash;4% for two consecutive months. Pilot a structured post-hosted-class flow: on-the-spot trial booking, trainer-led intro session, and a 7-day follow-up. Target: hosted-class conversion &ge; 15% by September, which would add ~5 conversions from the 34 hosted leads.</div>
        <div class="action-meta">
          <span class="meta-pill">Owner: Member Experience + Trainers</span>
          <span class="meta-pill">Priority: Medium</span>
          <span class="meta-pill">Impact: Medium</span>
        </div>
      </div>
    </div>''',
    ]

    conclusions = [
        f'''<div class="conclusion-item">
      <span class="conclusion-num">01</span>
      <span class="conclusion-text"><strong>The conversion funnel is the single highest-leverage fix in the business.</strong> Restoring conversion from 9.9% to June&rsquo;s 24.2% on the same 151-lead base would produce ~21 conversions (vs 15) &mdash; adding approximately {fmt_l(6*july_atv)} in monthly revenue with zero additional lead-generation cost.</span>
    </div>''',
        f'''<div class="conclusion-item">
      <span class="conclusion-num">02</span>
      <span class="conclusion-text"><strong>Lead volume is healthy &mdash; the constraint is conversion mechanics, not demand.</strong> {fj["leads"]} leads is above June&rsquo;s {fjun["leads"]}. The breakdown is in the trial-to-sale handoff, which is a process problem that can be fixed in weeks, not a market problem that requires quarters.</span>
    </div>''',
        f'''<div class="conclusion-item">
      <span class="conclusion-num">03</span>
      <span class="conclusion-text"><strong>Conversational channels convert; passive channels do not.</strong> WhatsApp (25%) and incoming calls (37.5%) convert at 2&ndash;3&times; the portfolio average, while Website (0%) and Walk-in (0%) convert at zero. The implication is clear: every lead needs a human conversation within hours, not days.</span>
    </div>''',
        f'''<div class="conclusion-item">
      <span class="conclusion-num">04</span>
      <span class="conclusion-text"><strong>The hosted-class conversion gap is now a multi-month structural pattern.</strong> 3.4% in May, 2.9% in July &mdash; the hosted format generates attendance but not buyers. Without a structured post-class conversion process, the hosted-class program is a marketing expense without a revenue return.</span>
    </div>''',
    ]

    return f'''
<section class="report-section" id="conversion-funnel">
  <div class="container">
    <div class="section-header">
      <div class="section-header-left">
        <span class="section-eyebrow">03 &middot; New Client Conversion Funnel</span>
        <h2 class="section-title">{fj["leads"]} leads &rarr; {fj["trials"]} trials &rarr; {fj["converted"]} conversions &rarr; {fj["retained"]} retained. The funnel is wider at the top and narrower at the bottom &mdash; the constraint is conversion mechanics, not lead volume.</h2>
        <p class="section-deck">
          July&rsquo;s lead pipeline grew to <strong>{fj["leads"]}</strong> (+{leads_mom:.0f}% MoM), but the conversion rate collapsed to
          <strong>{fj["conv_rate"]:.1f}%</strong> &mdash; half of June&rsquo;s {fjun["conv_rate"]:.1f}%. Only <strong>{fj["converted"]} leads converted</strong>
          (vs {fjun["converted"]} in June), and retained members fell to {fj["retained"]}. The funnel is generating more leads but
          converting fewer of them. Website (25 leads, 0 conversions) and walk-in (7 leads, 0 conversions) are the largest
          leakage points; conversational channels (WhatsApp 25%, incoming call 37.5%) are the conversion bright spots.
        </p>
      </div>
      <div class="section-anchor">Section 03 / 07</div>
    </div>

    <div class="subsection">
      <h3 class="subsection-title">Funnel at a glance &mdash; stage-by-stage view</h3>
      <p class="subsection-deck">The four-stage visual below traces the headline funnel for July 2026, with month-on-month and year-on-year context.</p>
    </div>

    <div class="funnel-stages">
      <div class="funnel-stage">
        <div class="funnel-stage-num">{fj["leads"]}</div>
        <div class="funnel-stage-label">Leads</div>
        <div class="funnel-stage-sub">{leads_mom:+.0f}% MoM &middot; 21% of pipeline</div>
      </div>
      <div class="funnel-stage">
        <div class="funnel-stage-num">{fj["trials"]}</div>
        <div class="funnel-stage-label">Trials / First Visits</div>
        <div class="funnel-stage-sub">{trials_mom:+.0f}% MoM &middot; {fj["trials"]/fj["leads"]*100:.0f}% of leads</div>
      </div>
      <div class="funnel-stage conv">
        <div class="funnel-stage-num">{fj["converted"]}</div>
        <div class="funnel-stage-label">Converted</div>
        <div class="funnel-stage-sub">{conv_mom:+.0f}% MoM &middot; {fj["conv_rate"]:.1f}% conv rate</div>
      </div>
      <div class="funnel-stage conv">
        <div class="funnel-stage-num">{fj["retained"]}</div>
        <div class="funnel-stage-label">Retained</div>
        <div class="funnel-stage-sub">{ret_mom:+.0f}% MoM &middot; {fj["retain_rate"]:.1f}% of leads</div>
      </div>
    </div>

    <div class="callout">
      <strong>How to read this section:</strong> the funnel table below is sorted by lead volume; conversion rates are calculated
      off the leads column. The insight pane on the left narrates the KPIs &mdash; what each number <em>indicates</em> and
      <em>why</em> it matters for the business decision. The MoM flow table at the bottom places July in seven-month context.
    </div>

    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">Funnel-level insights</div>
        {''.join(insights)}
      </div>
      <div class="data-pane">
        <div class="pane-title">New client purchases by lead source</div>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Source</th>
                <th>Leads</th>
                <th>Trials</th>
                <th>Conv.</th>
                <th>Conv Rate</th>
                <th>Visits</th>
                <th>LTV</th>
              </tr>
            </thead>
            <tbody>
              {''.join(src_rows)}
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div class="subsection">
      <h3 class="subsection-title">Trial type breakdown &mdash; how leads entered the studio</h3>
      <p class="subsection-deck">The trial format mix shows how leads were acquired. &ldquo;Trial Class&rdquo; is the standard free-trial format; &ldquo;Hosted Class&rdquo; is a partner-brand event; &ldquo;Referral Class&rdquo; is a member-referred trial.</p>
    </div>
    <div class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>Trial Type</th>
            <th>Count</th>
            <th>Share of Trials</th>
          </tr>
        </thead>
        <tbody>
          {''.join(tt_rows)}
        </tbody>
      </table>
    </div>

    <div class="subsection">
      <h3 class="subsection-title">Month-on-month new client flow &mdash; January through July 2026</h3>
      <p class="subsection-deck">Seven-month trend of the funnel stages. July is highlighted in bold. The conversion rate decline from June to July is the steepest MoM change in the period.</p>
    </div>
    <div class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>Month</th>
            <th>Leads</th>
            <th>Trials</th>
            <th>Converted</th>
            <th>Conv Rate</th>
            <th>Retained</th>
          </tr>
        </thead>
        <tbody>
          {''.join(mom_rows)}
        </tbody>
      </table>
    </div>

    <div class="subsection">
      <h3 class="subsection-title">What worked / What did not work</h3>
    </div>
    <div class="worked-grid">
      {''.join(worked)}
      {''.join(didnt)}
    </div>

    <div class="subsection">
      <h3 class="subsection-title">Action items &mdash; funnel-specific</h3>
    </div>
    <div class="action-grid">
      {''.join(actions)}
    </div>

    <div class="subsection">
      <h3 class="subsection-title">Data-backed conclusions</h3>
    </div>
    <div class="conclusions-block">
      {''.join(conclusions)}
    </div>
  </div>
</section>'''


# ============ SECTION 04: SESSIONS & CLASS PERFORMANCE ============
def section_04():
    # Format-level view
    type_items = sorted(sej['bytype'].items(), key=lambda x: -x[1][0])
    type_rows = []
    for name, (sess, cap, visits, lc, rev) in type_items:
        fill = visits/cap*100 if cap else 0
        avg = visits/sess if sess else 0
        type_rows.append(f'''<tr>
          <td class="metric-name">{esc(name)}</td>
          <td class="num">{sess}</td>
          <td class="num">{visits}</td>
          <td class="num">{fill:.1f}%</td>
          <td class="num">{avg:.1f}</td>
          <td class="num">{fmt_l(rev)}</td>
          <td class="num">{fmt_r(rev/visits) if visits else '&mdash;'}</td>
        </tr>''')

    # Class-by-class
    class_items = sorted(sej['byclass'].items(), key=lambda x: -x[1][4])
    class_rows = []
    for name, (sess, cap, visits, lc, rev) in class_items:
        fill = visits/cap*100 if cap else 0
        cancel_rate = lc/(visits+lc)*100 if (visits+lc) else 0
        avg = visits/sess if sess else 0
        revpc = rev/visits if visits else 0
        class_rows.append(f'''<tr>
          <td class="metric-name">{esc(name)}</td>
          <td class="num">{sess}</td>
          <td class="num">{cap:.0f}</td>
          <td class="num">{visits}</td>
          <td class="num {fill_class(fill)}">{fill:.1f}%</td>
          <td class="num">{avg:.1f}</td>
          <td class="num">{cancel_rate:.1f}%</td>
          <td class="num">{fmt_l(rev)}</td>
          <td class="num">{fmt_r(revpc)}</td>
        </tr>''')

    # Trainer scorecard (from sessions bytrainer data)
    tr_items = sorted(sej['bytrainer'].items(), key=lambda x: -x[1][4])
    tr_rows = []
    for name, (sess, cap, visits, lc, rev) in tr_items:
        fill = visits/cap*100 if cap else 0
        avg = visits/sess if sess else 0
        # Score: fill * avg / 10 (composite utilisation score)
        score = fill * avg / 10
        sc = 'score-high' if score >= 50 else ('score-mid' if score >= 25 else 'score-low')
        tr_rows.append(f'''<tr>
          <td class="metric-name">{esc(name)}</td>
          <td class="num">{sess}</td>
          <td class="num">{visits}</td>
          <td class="num {fill_class(fill)}">{fill:.1f}%</td>
          <td class="num">{avg:.1f}</td>
          <td class="num">{fmt_l(rev)}</td>
          <td class="num {sc}">{score:.0f}</td>
        </tr>''')

    # Heatmap
    # Collect all time slots and sort them
    all_slots = sorted(sej['heat'].keys())
    # Sort by time of day
    def slot_sort_key(s):
        h, m = s.split(':')
        return int(h)*60 + int(m)
    all_slots.sort(key=slot_sort_key)

    heat_header = '<tr><th class="slot-label">Time</th>' + ''.join(f'<th>{d[:3]}</th>' for d in DAYS) + '</tr>'
    heat_body = []
    for slot in all_slots:
        cells = f'<th class="slot-label">{slot}</th>'
        for day in DAYS:
            cell_data = sej['heat'][slot].get(day)
            if cell_data:
                visits, cap = cell_data
                pct = visits/cap*100 if cap else 0
                cells += f'<td class="heat-cell {heat_class(pct)}">{visits:.0f}<br><span style="font-size:9px;opacity:0.7">{pct:.0f}%</span></td>'
            else:
                cells += '<td class="heat-cell heat-none">&mdash;</td>'
        heat_body.append(f'<tr>{cells}</tr>')

    insights = [
        f'''<div class="insight-card">
      <div class="insight-num">01</div>
      <div class="insight-body">
        <div class="insight-title">Barre 57 is the volume engine at {sej["bytype"]["Barre 57"][0]} sessions.</div>
        <div class="insight-text">{sej["bytype"]["Barre 57"][0]} Barre 57 sessions delivered {sej["bytype"]["Barre 57"][2]} visits ({sej["bytype"]["Barre 57"][2]/sej["bytype"]["Barre 57"][1]*100:.1f}% fill) and {fmt_l(sej["bytype"]["Barre 57"][4])} in session revenue. It is the studio&rsquo;s dominant format by every measure &mdash; volume, attendance, and revenue.</div>
      </div>
    </div>''',
        f'''<div class="insight-card">
      <div class="insight-num">02</div>
      <div class="insight-body">
        <div class="insight-title">PowerCycle grew {pc(sej["bytype"]["powerCycle"][0], sejun["bytype"]["powerCycle"][0]):.0f}% in sessions MoM.</div>
        <div class="insight-text">{sej["bytype"]["powerCycle"][0]} PowerCycle sessions (vs {sejun["bytype"]["powerCycle"][0]} in June) delivered {sej["bytype"]["powerCycle"][2]} visits at {sej["bytype"]["powerCycle"][2]/sej["bytype"]["powerCycle"][1]*100:.1f}% fill. PowerCycle is the swing format &mdash; capacity is being added and attendance is following.</div>
      </div>
    </div>''',
        f'''<div class="insight-card">
      <div class="insight-num">03</div>
      <div class="insight-body">
        <div class="insight-title">Strength Lab is supply-constrained at {sej["bytype"]["Strength Lab!"][2]/sej["bytype"]["Strength Lab!"][1]*100:.1f}% fill.</div>
        <div class="insight-text">{sej["bytype"]["Strength Lab!"][0]} Strength Lab sessions delivered {sej["bytype"]["Strength Lab!"][2]} visits at {sej["bytype"]["Strength Lab!"][2]/sej["bytype"]["Strength Lab!"][1]*100:.1f}% fill &mdash; the highest fill rate of the three formats. Strength Lab is demand-constrained on the upside: members want more sessions than are scheduled.</div>
      </div>
    </div>''',
        f'''<div class="insight-card">
      <div class="insight-num">04</div>
      <div class="insight-body">
        <div class="insight-title">Studio Barre 57 is the workhorse class at {sej["byclass"]["Studio Barre 57"][0]} sessions.</div>
        <div class="insight-text">{sej["byclass"]["Studio Barre 57"][0]} sessions, {sej["byclass"]["Studio Barre 57"][2]} visits, {sej["byclass"]["Studio Barre 57"][2]/sej["byclass"]["Studio Barre 57"][1]*100:.1f}% fill, {fmt_l(sej["byclass"]["Studio Barre 57"][4])} revenue. Studio PowerCycle is second at {sej["byclass"]["Studio PowerCycle"][0]} sessions and {fmt_l(sej["byclass"]["Studio PowerCycle"][4])} revenue.</div>
      </div>
    </div>''',
        f'''<div class="insight-card">
      <div class="insight-num">05</div>
      <div class="insight-body">
        <div class="insight-title">Rohan Dahima leads the trainer scorecard by revenue.</div>
        <div class="insight-text">{sej["bytrainer"]["Rohan Dahima"][0]} sessions, {sej["bytrainer"]["Rohan Dahima"][2]} visits, {fmt_l(sej["bytrainer"]["Rohan Dahima"][4])} revenue &mdash; the highest revenue-generating trainer in July. Cauveri Vikrant and Mrigakshi Jaiswal round out the top three by visit volume.</div>
      </div>
    </div>''',
        f'''<div class="insight-card">
      <div class="insight-num">06</div>
      <div class="insight-body">
        <div class="insight-title">Wednesday and Thursday 19:15 is the peak demand slot.</div>
        <div class="insight-text">The 19:15 evening slot on Wednesday ({sej["heat"]["19:15"]["Wednesday"][0]:.0f} visits, {sej["heat"]["19:15"]["Wednesday"][1]:.0f} cap) and Thursday ({sej["heat"]["19:15"]["Thursday"][0]:.0f} visits) is the studio&rsquo;s highest-demand window. The 07:30 morning slot is the second peak, particularly Wednesday ({sej["heat"]["07:30"]["Wednesday"][0]:.0f} visits).</div>
      </div>
    </div>''',
    ]

    worked = [
        f'''<div class="worked-card worked">
      <div class="worked-icon">+</div>
      <div class="worked-body">
        <div class="worked-title">Fill rate rose to {sej["fill"]:.1f}% &mdash; an eight-month high.</div>
        <div class="worked-text">{sej["visits"]:,} visits across {sej["sessions"]} sessions with only {sej["empty"]} empty sessions. Class average rose to {sej["class_avg"]:.1f} from {sejun["class_avg"]:.1f} in June. The schedule is better matched to demand than at any point in 2026.</div>
      </div>
    </div>''',
        f'''<div class="worked-card worked">
      <div class="worked-icon">+</div>
      <div class="worked-body">
        <div class="worked-title">Strength Lab fill rate at {sej["bytype"]["Strength Lab!"][2]/sej["bytype"]["Strength Lab!"][1]*100:.1f}%.</div>
        <div class="worked-text">The highest fill of the three formats confirms Strength Lab as a supply-constrained hit. Adding sessions here would absorb existing demand without diluting attendance.</div>
      </div>
    </div>''',
        f'''<div class="worked-card worked">
      <div class="worked-icon">+</div>
      <div class="worked-body">
        <div class="worked-title">PowerCycle expanded {pc(sej["bytype"]["powerCycle"][0], sejun["bytype"]["powerCycle"][0]):.0f}% in session count.</div>
        <div class="worked-text">{sej["bytype"]["powerCycle"][0]} sessions (vs {sejun["bytype"]["powerCycle"][0]} in June) at {sej["bytype"]["powerCycle"][2]/sej["bytype"]["powerCycle"][1]*100:.1f}% fill. Capacity was added and demand followed &mdash; PowerCycle is scaling well.</div>
      </div>
    </div>''',
    ]

    didnt = [
        f'''<div class="worked-card didnt">
      <div class="worked-icon">&minus;</div>
      <div class="worked-body">
        <div class="worked-title">{sej["empty"]} empty sessions ran in July.</div>
        <div class="worked-text">{sej["empty"]} sessions delivered zero visits &mdash; a direct capacity waste. While down from some months, every empty session represents a trainer cost with zero revenue. These should be identified and either filled or removed.</div>
      </div>
    </div>''',
        f'''<div class="worked-card didnt">
      <div class="worked-icon">&minus;</div>
      <div class="worked-body">
        <div class="worked-title">Late cancellations remain high at {sej["late_cancel"]}.</div>
        <div class="worked-text">{sej["late_cancel"]} late cancels across {cj["lc_members"]} members. While down from {sejun["late_cancel"]} in June, the rate is still ~11% of bookings. {cj["heavy_cancelers"]} members cancelled 6+ times &mdash; the penalty policy needs enforcement.</div>
      </div>
    </div>''',
        f'''<div class="worked-card didnt">
      <div class="worked-icon">&minus;</div>
      <div class="worked-body">
        <div class="worked-title">Cardio Barre Express and Plus remain sub-scale.</div>
        <div class="worked-text">Studio Cardio Barre Express: {sej["byclass"].get("Studio Cardio Barre Express",[0,1,0,0,0])[2]/sej["byclass"].get("Studio Cardio Barre Express",[0,1,1,0,0])[1]*100:.1f}% fill. Studio Cardio Barre Plus: {sej["byclass"].get("Studio Cardio Barre Plus",[0,1,0,0,0])[2]/sej["byclass"].get("Studio Cardio Barre Plus",[0,1,1,0,0])[1]*100:.1f}% fill. These formats continue to hold capacity that would be better reallocated to Strength Lab.</div>
      </div>
    </div>''',
        f'''<div class="worked-card didnt">
      <div class="worked-icon">&minus;</div>
      <div class="worked-body">
        <div class="worked-title">Unknown Class sessions absorbed capacity with near-zero attendance.</div>
        <div class="worked-text">18 &ldquo;Unknown Class&rdquo; sessions with only 7 visits total &mdash; a {7/(18*20)*100:.0f}% effective fill. These are data-quality or scheduling gaps that waste trainer time and studio capacity.</div>
      </div>
    </div>''',
    ]

    actions = [
        f'''<div class="action-card">
      <div class="action-num">01</div>
      <div class="action-body">
        <div class="action-title">Add 10&ndash;15 Strength Lab sessions per month.</div>
        <div class="action-text">Strength Lab at {sej["bytype"]["Strength Lab!"][2]/sej["bytype"]["Strength Lab!"][1]*100:.1f}% fill is supply-constrained. Adding 10&ndash;15 sessions/month in the peak 07:30 and 19:15 slots would absorb existing demand without diluting attendance. Target: Strength Lab to 75+ sessions/month at maintained 70%+ fill.</div>
        <div class="action-meta">
          <span class="meta-pill">Owner: Studio Head + Scheduling</span>
          <span class="meta-pill">Priority: High</span>
          <span class="meta-pill">Impact: High</span>
        </div>
      </div>
    </div>''',
        f'''<div class="action-card">
      <div class="action-num">02</div>
      <div class="action-body">
        <div class="action-title">Discontinue Cardio Barre Express and merge Plus into the main slot.</div>
        <div class="action-text">Studio Cardio Barre Express at {sej["byclass"].get("Studio Cardio Barre Express",[0,1,0,0,0])[2]/sej["byclass"].get("Studio Cardio Barre Express",[0,1,1,0,0])[1]*100:.1f}% fill and Plus at {sej["byclass"].get("Studio Cardio Barre Plus",[0,1,0,0,0])[2]/sej["byclass"].get("Studio Cardio Barre Plus",[0,1,1,0,0])[1]*100:.1f}% fill are structural underperformers. Discontinue Express, merge Plus into the main Cardio Barre slot, and reallocate recovered capacity to Strength Lab and weekend PowerCycle.</div>
        <div class="action-meta">
          <span class="meta-pill">Owner: Studio Head + Scheduling</span>
          <span class="meta-pill">Priority: High</span>
          <span class="meta-pill">Impact: Medium</span>
        </div>
      </div>
    </div>''',
        f'''<div class="action-card">
      <div class="action-num">03</div>
      <div class="action-body">
        <div class="action-title">Resolve the 18 &ldquo;Unknown Class&rdquo; sessions.</div>
        <div class="action-text">18 sessions logged as &ldquo;Unknown Class&rdquo; with 7 total visits is either a data-quality issue or a scheduling gap. Audit the scheduling system to ensure every session has a proper class assignment, and remove any genuinely unscheduled sessions. This alone would improve the fill rate by ~1pp.</div>
        <div class="action-meta">
          <span class="meta-pill">Owner: Operations</span>
          <span class="meta-pill">Priority: Medium</span>
          <span class="meta-pill">Impact: Low</span>
        </div>
      </div>
    </div>''',
        f'''<div class="action-card">
      <div class="action-num">04</div>
      <div class="action-body">
        <div class="action-title">Enforce the late-cancel penalty policy.</div>
        <div class="action-text">{sej["late_cancel"]} late cancels across {cj["lc_members"]} members, with {cj["heavy_cancelers"]} members cancelling 6+ times. Enforce the &#8377;250 late-cancel penalty (waived for medical). Target: 30% reduction in late cancels within 60 days. The {cj["heavy_cancelers"]} heavy cancelers should get a personal retention call before enforcement begins.</div>
        <div class="action-meta">
          <span class="meta-pill">Owner: Operations + Member Experience</span>
          <span class="meta-pill">Priority: Medium</span>
          <span class="meta-pill">Impact: Medium</span>
        </div>
      </div>
    </div>''',
    ]

    conclusions = [
        f'''<div class="conclusion-item">
      <span class="conclusion-num">01</span>
          <span class="conclusion-text"><strong>July is the best-attended month of 2026.</strong> {sej["visits"]:,} visits at {sej["fill"]:.1f}% fill across {sej["sessions"]} sessions &mdash; the highest volume and utilisation since January. The schedule is delivering attendance at a rate the studio has not seen in eight months.</span>
    </div>''',
        f'''<div class="conclusion-item">
      <span class="conclusion-num">02</span>
      <span class="conclusion-text"><strong>Strength Lab is the studio&rsquo;s most under-supplied format.</strong> At {sej["bytype"]["Strength Lab!"][2]/sej["bytype"]["Strength Lab!"][1]*100:.1f}% fill with only {sej["bytype"]["Strength Lab!"][0]} sessions, the format has room to add 10&ndash;15 sessions/month without diluting attendance. This is the single highest-confidence scheduling move.</span>
    </div>''',
        f'''<div class="conclusion-item">
      <span class="conclusion-num">03</span>
      <span class="conclusion-text"><strong>PowerCycle is scaling successfully.</strong> {sej["bytype"]["powerCycle"][0]} sessions at {sej["bytype"]["powerCycle"][2]/sej["bytype"]["powerCycle"][1]*100:.1f}% fill (up from {sejun["bytype"]["powerCycle"][0]} sessions in June) confirms that added capacity is being absorbed. The format is on a healthy growth trajectory.</span>
    </div>''',
        f'''<div class="conclusion-item">
      <span class="conclusion-num">04</span>
      <span class="conclusion-text"><strong>Cardio Barre Express/Plus remain structural losers.</strong> Sub-{sej["byclass"].get("Studio Cardio Barre Plus",[0,1,0,0,0])[2]/sej["byclass"].get("Studio Cardio Barre Plus",[0,1,1,0,0])[1]*100:.0f}% fill for two consecutive months. These formats are both a member-experience risk and an opportunity cost &mdash; the capacity they hold would deliver more value as Strength Lab or PowerCycle sessions.</span>
    </div>''',
        f'''<div class="conclusion-item">
      <span class="conclusion-num">05</span>
      <span class="conclusion-text"><strong>Peak demand is concentrated in two windows: 07:30 mornings and 19:15 evenings.</strong> Wednesday 19:15 ({sej["heat"]["19:15"]["Wednesday"][0]:.0f} visits) and Wednesday 07:30 ({sej["heat"]["07:30"]["Wednesday"][0]:.0f} visits) are the single highest-demand slots. Any capacity additions should prioritise these windows first.</span>
    </div>''',
        f'''<div class="conclusion-item">
      <span class="conclusion-num">06</span>
      <span class="conclusion-text"><strong>Session revenue grew while product sales fell &mdash; the attendance-acquisition gap in one number.</strong> Session-attributed revenue rose to {fmt_l(sej["revenue"])} (+{pc(sej["revenue"],sejun["revenue"]):.0f}% MoM) while gross product sales fell to {fmt_l(july["gross"])}. Members are consuming sessions on existing packages but not buying new ones.</span>
    </div>''',
    ]

    return f'''
<section class="report-section" id="sessions">
  <div class="container">
    <div class="section-header">
      <div class="section-header-left">
        <span class="section-eyebrow">04 &middot; Sessions &amp; Class Performance</span>
        <h2 class="section-title">{sej["sessions"]} sessions, {sej["visits"]:,} visits, {sej["fill"]:.1f}% fill &mdash; the highest attendance in eight months. Strength Lab is supply-constrained, PowerCycle is scaling, and Cardio Barre Express/Plus remain structural losers.</h2>
        <p class="section-deck">
          July delivered <strong>{sej["visits"]:,} visits</strong> across <strong>{sej["sessions"]} sessions</strong> at <strong>{sej["fill"]:.1f}% fill</strong> &mdash;
          the highest volume and utilisation since January. Class average rose to {sej["class_avg"]:.1f}. Barre 57 remains the volume engine
          ({sej["bytype"]["Barre 57"][0]} sessions, {sej["bytype"]["Barre 57"][2]} visits), PowerCycle expanded {pc(sej["bytype"]["powerCycle"][0], sejun["bytype"]["powerCycle"][0]):.0f}% MoM,
          and Strength Lab hit {sej["bytype"]["Strength Lab!"][2]/sej["bytype"]["Strength Lab!"][1]*100:.1f}% fill &mdash; the highest of any format.
          Session revenue grew to {fmt_l(sej["revenue"])} (+{pc(sej["revenue"],sejun["revenue"]):.0f}% MoM) even as product sales fell, confirming the attendance-acquisition gap.
        </p>
      </div>
      <div class="section-anchor">Section 04 / 07</div>
    </div>

    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">Session insights &middot; July 2026</div>
        {''.join(insights)}
      </div>
      <div class="data-pane">
        <div class="pane-title">Format-level view</div>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Format</th>
                <th>Sessions</th>
                <th>Visits</th>
                <th>Fill</th>
                <th>Avg/Class</th>
                <th>Revenue</th>
                <th>Rev/Visit</th>
              </tr>
            </thead>
            <tbody>
              {''.join(type_rows)}
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div class="subsection">
      <h3 class="subsection-title">Class-by-class intelligence &mdash; the full session portfolio</h3>
      <p class="subsection-deck">Every class format that ran in July 2026, sorted by session revenue. Fill rate is colour-coded: green &ge;65%, amber 35&ndash;65%, red &lt;35%. Cancel rate is late cancels as a percentage of (visits + late cancels).</p>
    </div>
    <div class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>Class</th>
            <th>Sessions</th>
            <th>Capacity</th>
            <th>Visits</th>
            <th>Fill</th>
            <th>Avg/Class</th>
            <th>Cancel Rate</th>
            <th>Revenue</th>
            <th>Rev/Visit</th>
          </tr>
        </thead>
        <tbody>
          {''.join(class_rows)}
        </tbody>
      </table>
    </div>

    <div class="subsection">
      <h3 class="subsection-title">Trainer scorecard &mdash; utilisation, fill, and revenue</h3>
      <p class="subsection-deck">Every trainer who taught in July 2026, sorted by session revenue. The composite score combines fill rate and class average (fill &times; avg / 10): green &ge;50, amber 25&ndash;50, red &lt;25. Note: payroll conversion data is not available for July &mdash; this scorecard reflects utilisation only.</p>
    </div>
    <div class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>Trainer</th>
            <th>Sessions</th>
            <th>Visits</th>
            <th>Fill</th>
            <th>Avg/Class</th>
            <th>Revenue</th>
            <th>Score</th>
          </tr>
        </thead>
        <tbody>
          {''.join(tr_rows)}
        </tbody>
      </table>
    </div>

    <div class="subsection">
      <h3 class="subsection-title">Heatmap &mdash; fill rate by time-slot &times; day-of-week</h3>
      <p class="subsection-deck">Each cell shows visits (top) and fill percentage (bottom). Colour intensity indicates fill: red &lt;20%, amber 20&ndash;40%, blue 40&ndash;60%, green &ge;60%. Dashes indicate no session scheduled.</p>
    </div>
    <div class="table-wrap">
      <table class="heatmap-table">
        <thead>
          {heat_header}
        </thead>
        <tbody>
          {''.join(heat_body)}
        </tbody>
      </table>
    </div>

    <div class="subsection">
      <h3 class="subsection-title">What worked / What did not work</h3>
    </div>
    <div class="worked-grid">
      {''.join(worked)}
      {''.join(didnt)}
    </div>

    <div class="subsection">
      <h3 class="subsection-title">Action items &mdash; class scheduling, discontinuation, addition</h3>
    </div>
    <div class="action-grid">
      {''.join(actions)}
    </div>

    <div class="subsection">
      <h3 class="subsection-title">Data-backed conclusions</h3>
    </div>
    <div class="conclusions-block">
      {''.join(conclusions)}
    </div>
  </div>
</section>'''


# ============ SECTION 05: LAPSED MEMBERSHIPS ============
def section_05():
    # Expiration status
    renew_mom = pc(lj['renewed'], ljun['renewed'])
    lapsed_mom = pc(lj['lapsed'], ljun['lapsed'])
    exp_mom = pc(lj['expirations'], ljun['expirations'])

    # By product
    prod_items = sorted(lj['byprod'].items(), key=lambda x: -x[1])
    prod_rows = []
    for name, count in prod_items[:15]:
        prod_rows.append(f'''<tr>
          <td class="metric-name">{esc(name)}</td>
          <td class="num"><strong>{count}</strong></td>
          <td class="num">{count/lj["lapsed"]*100:.1f}%</td>
        </tr>''')

    # Cumulative by product
    cum_items = sorted(R['cumulative_lapsed_byprod'].items(), key=lambda x: -x[1])
    cum_rows = []
    for name, count in cum_items[:12]:
        cum_rows.append(f'''<tr>
          <td class="metric-name">{esc(name)}</td>
          <td class="num"><strong>{count}</strong></td>
          <td class="num">{count/R["cumulative_lapsed_unique"]*100:.1f}%</td>
        </tr>''')

    # 7-month trend
    mom_months = ['2026-01','2026-02','2026-03','2026-04','2026-05','2026-06','2026-07']
    trend_rows = []
    for m in mom_months:
        l = LP[m]
        lbl = m.split('-')[1] + ' ' + m.split('-')[0]
        is_july = m == '2026-07'
        so = '<strong>' if is_july else ''
        sc = '</strong>' if is_july else ''
        trend_rows.append(f'''<tr>
          <td class="metric-name">{so}{lbl}{sc}</td>
          <td class="num">{so}{l["expirations"]}{sc}</td>
          <td class="num">{so}{l["renewed"]}{sc}</td>
          <td class="num">{so}{l["lapsed"]}{sc}</td>
          <td class="num">{so}{l["renewal_rate"]:.1f}%{sc}</td>
          <td class="num">{so}{l["churn_rate"]:.1f}%{sc}</td>
        </tr>''')

    insights = [
        f'''<div class="insight-card">
      <div class="insight-num">01</div>
      <div class="insight-body">
        <div class="insight-title">{lj["lapsed"]} members lapsed &mdash; the highest absolute count of 2026.</div>
        <div class="insight-text">{lj["lapsed"]} lapsed members vs {ljun["lapsed"]} in June (+{lapsed_mom:.1f}%) and {lmay["lapsed"]} in May. While the churn rate is stable at {lj["churn_rate"]:.1f}%, the growing membership base means more absolute lapses each month. The lapsed book is accumulating.</div>
      </div>
    </div>''',
        f'''<div class="insight-card">
      <div class="insight-num">02</div>
      <div class="insight-body">
        <div class="insight-title">Renewal rate held at {lj["renewal_rate"]:.1f}% despite {exp_mom:.0f}% more expirations.</div>
        <div class="insight-text">{lj["renewed"]} renewals from {lj["expirations"]} expirations &mdash; the renewal rate dipped only 0.4pp from June&rsquo;s {ljun["renewal_rate"]:.1f}%. The renewal engine is scaling with the membership base, but it is not improving. A 5pp improvement in renewal rate would save ~37 members/month.</div>
      </div>
    </div>''',
        f'''<div class="insight-card">
      <div class="insight-num">03</div>
      <div class="insight-body">
        <div class="insight-title">Open Barre Class lapses dominate at {lj["byprod"].get("Studio Open Barre Class",0)}.</div>
        <div class="insight-text">{lj["byprod"].get("Studio Open Barre Class",0)} of {lj["lapsed"]} lapses ({lj["byprod"].get("Studio Open Barre Class",0)/lj["lapsed"]*100:.1f}%) are from Studio Open Barre Class &mdash; the single largest lapsed product. Studio Single Class ({lj["byprod"].get("Studio Single Class",0)}) and Complimentary Referral Class ({lj["byprod"].get("Studio Complimentary Referral Class",0)}) follow. These are low-commitment products with naturally high churn.</div>
      </div>
    </div>''',
        f'''<div class="insight-card">
      <div class="insight-num">04</div>
      <div class="insight-body">
        <div class="insight-title">Cumulative lapsed book stands at {R["cumulative_lapsed_unique"]} unique members.</div>
        <div class="insight-text">Across all of 2026, {R["cumulative_lapsed_unique"]} unique members have lapsed. The 1-Month Unlimited Membership is the largest cumulative segment at {R["cumulative_lapsed_byprod"].get("Studio 1 Month Unlimited Membership",0)} lapses &mdash; these are the highest-leverage reactivation targets because they have demonstrated willingness to pay for recurring access.</div>
      </div>
    </div>''',
        f'''<div class="insight-card">
      <div class="insight-num">05</div>
      <div class="insight-body">
        <div class="insight-title">Only {R["active"]["total"]} active memberships remain.</div>
        <div class="insight-text">The active membership base is {R["active"]["total"]} &mdash; {R["active"]["bytype"]["subscription"]} subscriptions and {R["active"]["bytype"]["package-events"]} package-events. The 1-Month Unlimited ({R["active"]["byname"].get("Studio 1 Month Unlimited Membership",0)}) is the largest active segment, followed by the Extended 10 Single Class Pack ({R["active"]["byname"].get("Studio Extended 10 Single Class Pack",0)}).</div>
      </div>
    </div>''',
        f'''<div class="insight-card">
      <div class="insight-num">06</div>
      <div class="insight-body">
        <div class="insight-title">Late cancellations: {cj["late_cancel"]} across {cj["lc_members"]} members.</div>
        <div class="insight-text">{cj["late_cancel"]} late cancels from {cj["lc_members"]} members, with {cj["heavy_cancelers"]} members cancelling 6+ times ({cj["heavy_cancels"]} cancels between them). Late cancels are a leading indicator of churn &mdash; members who cancel frequently are disengaging from the studio.</div>
      </div>
    </div>''',
    ]

    worked = [
        f'''<div class="worked-card worked">
      <div class="worked-icon">+</div>
      <div class="worked-body">
        <div class="worked-title">Renewal volume scaled with expirations.</div>
        <div class="worked-text">{lj["renewed"]} renewals from {lj["expirations"]} expirations &mdash; the renewal rate held within 0.4pp of June despite {exp_mom:.0f}% more expirations. The renewal engine is handling higher volume without breaking down.</div>
      </div>
    </div>''',
        f'''<div class="worked-card worked">
      <div class="worked-icon">+</div>
      <div class="worked-body">
        <div class="worked-title">Frozen memberships remained low at {lj["frozen"]}.</div>
        <div class="worked-text">Only {lj["frozen"]} memberships were frozen in July &mdash; a small, recoverable segment. Frozen members are not lost; they are paused and can be reactivated with a structured return-to-studio flow.</div>
      </div>
    </div>''',
    ]

    didnt = [
        f'''<div class="worked-card didnt">
      <div class="worked-icon">&minus;</div>
      <div class="worked-body">
        <div class="worked-title">Absolute lapsed count hit a 2026 high of {lj["lapsed"]}.</div>
        <div class="worked-text">{lj["lapsed"]} lapsed members is the highest of any month in 2026, up {lapsed_mom:.1f}% from June. While the churn rate is stable, the absolute number is growing &mdash; more members are leaving each month.</div>
      </div>
    </div>''',
        f'''<div class="worked-card didnt">
      <div class="worked-icon">&minus;</div>
      <div class="worked-body">
        <div class="worked-title">Cumulative lapsed book reached {R["cumulative_lapsed_unique"]} unique members.</div>
        <div class="worked-text">{R["cumulative_lapsed_unique"]} unique members have lapsed in 2026 &mdash; a large and growing reactivation pool. Without a structured win-back campaign, these members are permanently lost revenue.</div>
      </div>
    </div>''',
        f'''<div class="worked-card didnt">
      <div class="worked-icon">&minus;</div>
      <div class="worked-body">
        <div class="worked-title">Open Barre Class churn is disproportionately high.</div>
        <div class="worked-text">{lj["byprod"].get("Studio Open Barre Class",0)} of {lj["lapsed"]} lapses ({lj["byprod"].get("Studio Open Barre Class",0)/lj["lapsed"]*100:.1f}%) are from Open Barre Class. This product has a structurally high churn rate &mdash; members use it as a low-commitment entry point and do not renew.</div>
      </div>
    </div>''',
        f'''<div class="worked-card didnt">
      <div class="worked-icon">&minus;</div>
      <div class="worked-body">
        <div class="worked-title">Late-cancel policy still not enforced.</div>
        <div class="worked-text">{cj["late_cancel"]} late cancels from {cj["lc_members"]} members, with {cj["heavy_cancelers"]} heavy cancelers. Late cancels are a churn leading indicator &mdash; disengaged members cancel before they lapse. No penalty is being collected.</div>
      </div>
    </div>''',
    ]

    actions = [
        f'''<div class="action-card">
      <div class="action-num">01</div>
      <div class="action-body">
        <div class="action-title">Launch a tiered win-back campaign for the {R["cumulative_lapsed_unique"]} lapsed members.</div>
        <div class="action-text">Segment by recency: &lt;3 months (offer a free class + discounted restart), 3&ndash;6 months (referral credit on restart), 6+ months (fresh trial + newcomer offer). Prioritise the {R["cumulative_lapsed_byprod"].get("Studio 1 Month Unlimited Membership",0)} 1-Month Unlimited holders &mdash; they have demonstrated willingness to pay for recurring access. Target: 50 reactivations in Q3 at an average LTV of &#8377;8,000+.</div>
        <div class="action-meta">
          <span class="meta-pill">Owner: Member Experience + Studio Head</span>
          <span class="meta-pill">Priority: High</span>
          <span class="meta-pill">Impact: High</span>
        </div>
      </div>
    </div>''',
        f'''<div class="action-card">
      <div class="action-num">02</div>
      <div class="action-body">
        <div class="action-title">Build a 30-day-ahead renewal pipeline.</div>
        <div class="action-text">Every member with an expiry in the next 30 days gets a renewal touchpoint at Day -30 (benefits reminder), Day -14 (trainer personal check-in), and Day -7 (limited-time renewal offer). Assign renewal ownership to specific sellers. Target: renewal rate from {lj["renewal_rate"]:.1f}% to 60%+, saving ~37 members/month.</div>
        <div class="action-meta">
          <span class="meta-pill">Owner: Sales + Member Experience</span>
          <span class="meta-pill">Priority: High</span>
          <span class="meta-pill">Impact: High</span>
        </div>
      </div>
    </div>''',
        f'''<div class="action-card">
      <div class="action-num">03</div>
      <div class="action-body">
        <div class="action-title">Enforce the late-cancel penalty as a churn-prevention tool.</div>
        <div class="action-text">{cj["heavy_cancelers"]} members cancelled 6+ times &mdash; these are the highest churn-risk members. Before enforcing the &#8377;250 penalty, give each heavy canceler a personal retention call. The penalty is not the goal &mdash; the personal touchpoint is. The penalty enforces the behavioural discipline after the relationship is re-established.</div>
        <div class="action-meta">
          <span class="meta-pill">Owner: Operations + Member Experience</span>
          <span class="meta-pill">Priority: Medium</span>
          <span class="meta-pill">Impact: Medium</span>
        </div>
      </div>
    </div>''',
    ]

    conclusions = [
        f'''<div class="conclusion-item">
      <span class="conclusion-num">01</span>
      <span class="conclusion-text"><strong>The lapsed book is the studio&rsquo;s largest unrealised revenue pool.</strong> {R["cumulative_lapsed_unique"]} unique lapsed members represent an estimated &#8377;35&ndash;50L in LTV recovery if even 15% are reactivated. This is higher-leverage than new-lead acquisition because lapsed members have already demonstrated product fit.</span>
    </div>''',
        f'''<div class="conclusion-item">
      <span class="conclusion-num">02</span>
      <span class="conclusion-text"><strong>The churn rate is stable but absolute lapses are growing.</strong> A {lj["churn_rate"]:.1f}% churn rate on a growing base means more lapses each month. The renewal rate at {lj["renewal_rate"]:.1f}% is not improving &mdash; it needs a structured renewal pipeline to move above 60%.</span>
    </div>''',
        f'''<div class="conclusion-item">
      <span class="conclusion-num">03</span>
      <span class="conclusion-text"><strong>Open Barre Class and Single Class are the highest-churn products.</strong> {lj["byprod"].get("Studio Open Barre Class",0) + lj["byprod"].get("Studio Single Class",0)} of {lj["lapsed"]} lapses ({(lj["byprod"].get("Studio Open Barre Class",0) + lj["byprod"].get("Studio Single Class",0))/lj["lapsed"]*100:.0f}%) are from these two low-commitment products. Members use them as entry points and do not renew &mdash; the upgrade path from these products to packages and memberships needs to be engineered.</span>
    </div>''',
        f'''<div class="conclusion-item">
      <span class="conclusion-num">04</span>
      <span class="conclusion-text"><strong>1-Month Unlimited holders are the highest-value reactivation target.</strong> {R["cumulative_lapsed_byprod"].get("Studio 1 Month Unlimited Membership",0)} cumulative lapsed 1-Month Unlimited members have demonstrated willingness to pay for recurring access. A win-back offer that converts them to 3-Month or Annual memberships would both recover revenue and reduce future churn.</span>
    </div>''',
    ]

    return f'''
<section class="report-section" id="lapsed">
  <div class="container">
    <div class="section-header">
      <div class="section-header-left">
        <span class="section-eyebrow">05 &middot; Lapsed Memberships Deep Dive</span>
        <h2 class="section-title">{lj["lapsed"]} members lapsed in July &mdash; the highest absolute count of 2026. Cumulative lapsed book at {R["cumulative_lapsed_unique"]} unique members. The renewal engine scaled with expirations but the churn-to-renewal gap is widening in absolute terms.</h2>
        <p class="section-deck">
          <strong>{lj["expirations"]} memberships expired</strong> in July, of which <strong>{lj["renewed"]} renewed</strong> ({lj["renewal_rate"]:.1f}%),
          <strong>{lj["lapsed"]} lapsed</strong> ({lj["churn_rate"]:.1f}% churn), and {lj["frozen"]} froze. The churn rate is broadly stable vs June ({ljun["churn_rate"]:.1f}%),
          but absolute lapses rose {lapsed_mom:.1f}% on a {exp_mom:.0f}% increase in expirations. Cumulative unique lapsed members now stand at
          <strong>{R["cumulative_lapsed_unique"]}</strong>, with only <strong>{R["active"]["total"]}</strong> active memberships remaining. The
          1-Month Unlimited holder ({R["cumulative_lapsed_byprod"].get("Studio 1 Month Unlimited Membership",0)} cumulative lapses) is the highest-leverage reactivation target.
        </p>
      </div>
      <div class="section-anchor">Section 05 / 07</div>
    </div>

    <div class="split-grid">
      <div class="insights-pane">
        <div class="pane-title">Lapsed insights &middot; July 2026</div>
        {''.join(insights)}
      </div>
      <div class="data-pane">
        <div class="pane-title">Expiration status &mdash; the headline split</div>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Status</th>
                <th>Jul 2026</th>
                <th>Jun 2026</th>
                <th>MoM</th>
                <th>Share</th>
              </tr>
            </thead>
            <tbody>
              <tr><td class="metric-name">Total Expirations</td><td class="num"><strong>{lj["expirations"]}</strong></td><td class="num">{ljun["expirations"]}</td><td class="num">{badge(exp_mom)}</td><td class="num">100.0%</td></tr>
              <tr class="status-good"><td class="metric-name">Renewed</td><td class="num"><strong>{lj["renewed"]}</strong></td><td class="num">{ljun["renewed"]}</td><td class="num">{badge(renew_mom)}</td><td class="num">{lj["renewed"]/lj["expirations"]*100:.1f}%</td></tr>
              <tr class="status-bad"><td class="metric-name">Lapsed</td><td class="num"><strong>{lj["lapsed"]}</strong></td><td class="num">{ljun["lapsed"]}</td><td class="num">{badge(lapsed_mom, inverse=True)}</td><td class="num">{lj["lapsed"]/lj["expirations"]*100:.1f}%</td></tr>
              <tr class="status-neutral"><td class="metric-name">Frozen</td><td class="num"><strong>{lj["frozen"]}</strong></td><td class="num">{ljun["frozen"]}</td><td class="num">{badge(pc(lj["frozen"],ljun["frozen"]))}</td><td class="num">{lj["frozen"]/lj["expirations"]*100:.1f}%</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div class="subsection">
      <h3 class="subsection-title">Lapsed by product &mdash; where the churn is concentrated</h3>
      <p class="subsection-deck">The top 15 products by lapsed count in July 2026. Open Barre Class and Single Class are low-commitment products with structurally high churn; membership products (1-Month, 3-Month Unlimited) represent higher-value lapses.</p>
    </div>
    <div class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>Product</th>
            <th>Lapsed</th>
            <th>Share of Lapses</th>
          </tr>
        </thead>
        <tbody>
          {''.join(prod_rows)}
        </tbody>
      </table>
    </div>

    <div class="subsection">
      <h3 class="subsection-title">Cumulative lapsed book &mdash; the reactivation pool</h3>
      <p class="subsection-deck">Cumulative unique lapsed members by product across all of 2026 (January &ndash; July). These are the reactivation targets, sorted by volume. The 1-Month Unlimited holder is the single highest-value segment.</p>
    </div>
    <div class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>Product</th>
            <th>Cumulative Lapsed</th>
            <th>Share of Pool</th>
          </tr>
        </thead>
        <tbody>
          {''.join(cum_rows)}
        </tbody>
      </table>
    </div>

    <div class="subsection">
      <h3 class="subsection-title">Seven-month churn trend &mdash; January through July 2026</h3>
      <p class="subsection-deck">The churn rate has been stable in the 36&ndash;43% range throughout 2026, but absolute lapse counts have risen steadily as the membership base has grown. July is highlighted in bold.</p>
    </div>
    <div class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>Month</th>
            <th>Expirations</th>
            <th>Renewed</th>
            <th>Lapsed</th>
            <th>Renewal Rate</th>
            <th>Churn Rate</th>
          </tr>
        </thead>
        <tbody>
          {''.join(trend_rows)}
        </tbody>
      </table>
    </div>

    <div class="subsection">
      <h3 class="subsection-title">Late cancellations &mdash; the operational leak behind the lapsed number</h3>
      <p class="subsection-deck">Late cancels are a leading indicator of churn. Members who cancel frequently are disengaging from the studio before they formally lapse. {cj["heavy_cancelers"]} members cancelled 6+ times in July &mdash; these are the highest churn-risk individuals.</p>
    </div>
    <div class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>Metric</th>
            <th>Jul 2026</th>
            <th>Jun 2026</th>
            <th>MoM</th>
          </tr>
        </thead>
        <tbody>
          <tr><td class="metric-name">Total Late Cancels</td><td class="num"><strong>{cj["late_cancel"]}</strong></td><td class="num">{cjun["late_cancel"]}</td><td class="num">{badge(pc(cj["late_cancel"],cjun["late_cancel"]), inverse=True)}</td></tr>
          <tr><td class="metric-name">Members Who Late-Cancelled</td><td class="num"><strong>{cj["lc_members"]}</strong></td><td class="num">{cjun["lc_members"]}</td><td class="num">{badge(pc(cj["lc_members"],cjun["lc_members"]), inverse=True)}</td></tr>
          <tr><td class="metric-name">Heavy Cancelers (6+)</td><td class="num"><strong>{cj["heavy_cancelers"]}</strong></td><td class="num">{cjun["heavy_cancelers"]}</td><td class="num">{badge(pc(cj["heavy_cancelers"],cjun["heavy_cancelers"]), inverse=True)}</td></tr>
          <tr><td class="metric-name">Cancels from Heavy Cancelers</td><td class="num"><strong>{cj["heavy_cancels"]}</strong></td><td class="num">{cjun["heavy_cancels"]}</td><td class="num">{badge(pc(cj["heavy_cancels"],cjun["heavy_cancels"]), inverse=True)}</td></tr>
          <tr><td class="metric-name">New Client Visits</td><td class="num"><strong>{cj["new_visits"]}</strong></td><td class="num">{cjun["new_visits"]}</td><td class="num">{badge(pc(cj["new_visits"],cjun["new_visits"]))}</td></tr>
        </tbody>
      </table>
    </div>

    <div class="subsection">
      <h3 class="subsection-title">What worked / What did not work</h3>
    </div>
    <div class="worked-grid">
      {''.join(worked)}
      {''.join(didnt)}
    </div>

    <div class="subsection">
      <h3 class="subsection-title">Action items &mdash; lapsed-member recovery</h3>
    </div>
    <div class="action-grid">
      {''.join(actions)}
    </div>

    <div class="subsection">
      <h3 class="subsection-title">Data-backed conclusions</h3>
    </div>
    <div class="conclusions-block">
      {''.join(conclusions)}
    </div>
  </div>
</section>'''


# ============ SECTION 06: STRATEGIC RECOMMENDATIONS ============
def section_06():
    decisions = [
        f'''<div class="action-card">
      <div class="action-num">01</div>
      <div class="action-body">
        <div class="action-title">Repair the conversion funnel: target 20%+ conversion by September.</div>
        <div class="action-text">The conversion rate halved from 24.2% to 9.9% in one month despite a growing lead pipeline. This is the single highest-leverage fix in the business. Implement a mandatory 48-hour post-trial follow-up cadence, fix the Website (25 leads, 0 conversions) and walk-in (7 leads, 0 conversions) channels with a 2-hour response SLA, and assign a dedicated conversion owner per trial. Restoring conversion to 20% on the 151-lead base would produce ~30 conversions (vs 15) and add approximately {fmt_l(15*july_atv)} in monthly revenue.</div>
        <div class="action-meta">
          <span class="meta-pill">Owner: Studio Head + Member Experience</span>
          <span class="meta-pill">Priority: Critical</span>
          <span class="meta-pill">Impact: High &middot; ~{fmt_l(15*july_atv)}/mo</span>
        </div>
      </div>
    </div>''',
        f'''<div class="action-card">
      <div class="action-num">02</div>
      <div class="action-body">
        <div class="action-title">Monetise the attendance surge with a visit-to-value campaign.</div>
        <div class="action-text">July delivered {sej["visits"]:,} visits at {sej["fill"]:.1f}% fill &mdash; the highest in 8 months &mdash; but only {july["members"]} buyers. The gap between attendance and purchases is the structural revenue problem. Launch a visit-to-value campaign: identify the top 50 highest-attending non-members and offer a time-limited package upgrade at a 5% incentive (within the discount discipline framework). Target: 15 package conversions in 30 days, adding ~{fmt_l(15*14000)} in revenue from existing attendance.</div>
        <div class="action-meta">
          <span class="meta-pill">Owner: Sales + Operations</span>
          <span class="meta-pill">Priority: High</span>
          <span class="meta-pill">Impact: High &middot; ~{fmt_l(15*14000)}/mo</span>
        </div>
      </div>
    </div>''',
        f'''<div class="action-card">
      <div class="action-num">03</div>
      <div class="action-body">
        <div class="action-title">Reactivate the {R["cumulative_lapsed_unique"]} lapsed members with a tiered win-back.</div>
        <div class="action-text">{R["cumulative_lapsed_unique"]} cumulative unique lapsed members represent an estimated &#8377;35&ndash;50L in LTV recovery. Segment by recency (&lt;3mo, 3&ndash;6mo, 6+mo) and prioritise the {R["cumulative_lapsed_byprod"].get("Studio 1 Month Unlimited Membership",0)} 1-Month Unlimited holders. Offer tiered win-back incentives: free class + discounted restart for &lt;3mo, referral credit for 3&ndash;6mo, fresh trial for 6+mo. Target: 50 reactivations in Q3 at an average LTV of &#8377;8,000+ &mdash; approximately &#8377;4L in recovered revenue.</div>
        <div class="action-meta">
          <span class="meta-pill">Owner: Member Experience + Studio Head</span>
          <span class="meta-pill">Priority: High</span>
          <span class="meta-pill">Impact: High &middot; ~&#8377;4L in Q3</span>
        </div>
      </div>
    </div>''',
        f'''<div class="action-card">
      <div class="action-num">04</div>
      <div class="action-body">
        <div class="action-title">Add Strength Lab capacity and discontinue Cardio Barre Express/Plus.</div>
        <div class="action-text">Strength Lab at {sej["bytype"]["Strength Lab!"][2]/sej["bytype"]["Strength Lab!"][1]*100:.1f}% fill is supply-constrained &mdash; add 10&ndash;15 sessions/month in the 07:30 and 19:15 peak slots. Discontinue Studio Cardio Barre Express ({sej["byclass"].get("Studio Cardio Barre Express",[0,1,0,0,0])[2]/sej["byclass"].get("Studio Cardio Barre Express",[0,1,1,0,0])[1]*100:.1f}% fill) and merge Cardio Barre Plus into the main slot. Reallocate recovered capacity to Strength Lab and weekend PowerCycle. Target: overall fill rate maintained above 47% with 10&ndash;15 more high-demand sessions.</div>
        <div class="action-meta">
          <span class="meta-pill">Owner: Studio Head + Scheduling</span>
          <span class="meta-pill">Priority: High</span>
          <span class="meta-pill">Impact: Medium</span>
        </div>
      </div>
    </div>''',
        f'''<div class="action-card">
      <div class="action-num">05</div>
      <div class="action-body">
        <div class="action-title">Sustain the discount discipline and build a structured renewal pipeline.</div>
        <div class="action-text">July&rsquo;s discount efficiency of &#8377;{july["disc_eff"]:.2f} is the best of 2026 &mdash; maintain the hard-cap framework (penetration &lt;12%, no-discount Privates, Studio Head approval required). Simultaneously, build a 30-day-ahead renewal pipeline: every member with an upcoming expiry gets a Day -30, Day -14, and Day -7 touchpoint. Target: renewal rate from {lj["renewal_rate"]:.1f}% to 60%+, saving ~37 members/month and reducing the churn-to-renewal gap.</div>
        <div class="action-meta">
          <span class="meta-pill">Owner: Studio Head + Finance + Sales</span>
          <span class="meta-pill">Priority: Medium</span>
          <span class="meta-pill">Impact: Medium &middot; ~37 members/mo</span>
        </div>
      </div>
    </div>''',
    ]

    conclusions = [
        f'''<div class="conclusion-item">
      <span class="conclusion-num">01</span>
      <span class="conclusion-text"><strong>The five decisions are sequenced by leverage, not by difficulty.</strong> Conversion repair (#1) is the highest-impact and most addressable &mdash; it is a process fix, not a market problem. Visit-to-value monetisation (#2) leverages existing attendance. Lapsed reactivation (#3) taps the largest unrealised revenue pool. Scheduling optimisation (#4) is a quick structural fix. Discount discipline + renewal pipeline (#5) protects the structural wins.</span>
    </div>''',
        f'''<div class="conclusion-item">
      <span class="conclusion-num">02</span>
      <span class="conclusion-text"><strong>If all five decisions are executed, August net sales should recover to &#8377;20&ndash;24L.</strong> Conversion restoration alone adds ~{fmt_l(15*july_atv)}; visit-to-value adds ~{fmt_l(15*14000)}; lapsed reactivation adds ~&#8377;1L/month in Q3. Combined with sustained attendance and discount discipline, the path from &#8377;14.13L to &#8377;20&ndash;24L is achievable in one month.</span>
    </div>''',
        f'''<div class="conclusion-item">
      <span class="conclusion-num">03</span>
      <span class="conclusion-text"><strong>The studio&rsquo;s attendance base is its greatest competitive asset &mdash; the strategy must convert attendance to revenue.</strong> {sej["visits"]:,} monthly visits at {sej["fill"]:.1f}% fill is a demand signal that most studios would envy. The business challenge is not generating demand &mdash; it is capturing the value of the demand that already exists.</span>
    </div>''',
        f'''<div class="conclusion-item">
      <span class="conclusion-num">04</span>
      <span class="conclusion-text"><strong>The discount discipline must be protected as a non-negotiable.</strong> July proved that disciplined discounting (&#8377;{july["disc_eff"]:.2f} efficiency) is compatible with high attendance. The temptation to discount-drive revenue in a soft month would reverse this structural gain &mdash; the May experience is the cautionary data point.</span>
    </div>''',
        f'''<div class="conclusion-item">
      <span class="conclusion-num">05</span>
      <span class="conclusion-text"><strong>The renewal pipeline is the long-term churn solution.</strong> A 5pp improvement in renewal rate (from {lj["renewal_rate"]:.1f}% to 60%+) would save ~37 members/month &mdash; more than the entire conversion output of July. The renewal pipeline is a higher-leverage retention investment than any acquisition campaign.</span>
    </div>''',
    ]

    return f'''
<section class="report-section" id="recommendations">
  <div class="container">
    <div class="section-header">
      <div class="section-header-left">
        <span class="section-eyebrow">06 &middot; Strategic Recommendations</span>
        <h2 class="section-title">Five business decisions for senior management to make this quarter &mdash; each anchored to a July 2026 data point with a target, an owner, and an estimated revenue impact.</h2>
        <p class="section-deck">
          The five decisions below are sequenced by leverage, not by difficulty. Together, they address the three structural
          challenges identified in this report: the conversion breakdown, the attendance-acquisition gap, and the growing lapsed
          book. Each decision is anchored to a specific July 2026 metric and includes a target, an owner, and an estimated
          monthly revenue impact. If all five are executed, August net sales should recover to <strong>&#8377;20&ndash;24L</strong>.
        </p>
      </div>
      <div class="section-anchor">Section 06 / 07</div>
    </div>

    <div class="subsection">
      <h3 class="subsection-title">Five business decisions for the next 90 days</h3>
      <p class="subsection-deck">Each decision is designed to be actionable within 30 days and measurable within 60. Owners are named; priorities and impact ratings reflect the estimated revenue effect.</p>
    </div>
    <div class="action-grid">
      {''.join(decisions)}
    </div>

    <div class="subsection">
      <h3 class="subsection-title">Data-backed conclusions</h3>
    </div>
    <div class="conclusions-block">
      {''.join(conclusions)}
    </div>
  </div>
</section>'''


# ============ SECTION 07: PREDICTIONS & FORWARD VIEW ============
def section_07():
    # Build 7-month revenue trend for forecasting context
    months = ['2026-01','2026-02','2026-03','2026-04','2026-05','2026-06','2026-07']
    revs = [S[m]['net'] for m in months]
    convs = [F[m]['conv_rate'] for m in months]
    visits = [SE[m]['visits'] for m in months]

    # Simple forecast: baseline scenario = July + trend, intervention = restored conversion
    july_net = july['net']
    # Baseline (no intervention): assume buyer count continues to decline slightly
    baseline_aug = july_net * 0.95  # slight continued decline
    # Intervention scenario: conversion restored to 20%, visit-to-value adds 15 packages
    conv_uplift = 15 * july_atv  # additional conversions at current ATV
    vtv_uplift = 15 * 14000  # package conversions from visit-to-value
    intervention_aug = july_net + conv_uplift + vtv_uplift

    # Weekly red flags
    flags = [
        f'''<div class="worked-card didnt">
      <div class="worked-icon">!</div>
      <div class="worked-body">
        <div class="worked-title">Conversion rate below 15% for 2 consecutive weeks.</div>
        <div class="worked-text">If the weekly conversion rate stays below 15% through mid-August, escalate the follow-up cadence to daily check-ins and assign the Studio Head as the personal conversion owner for every trial.</div>
      </div>
    </div>''',
        f'''<div class="worked-card didnt">
      <div class="worked-icon">!</div>
      <div class="worked-body">
        <div class="worked-title">Buyer count below 140 for 2 consecutive weeks.</div>
        <div class="worked-text">If unique weekly buyers fall below 35 (140/month run-rate), trigger the visit-to-value campaign immediately rather than waiting for the planned launch date.</div>
      </div>
    </div>''',
        f'''<div class="worked-card didnt">
      <div class="worked-icon">!</div>
      <div class="worked-body">
        <div class="worked-title">Discount penetration above 12%.</div>
        <div class="worked-text">If discount penetration exceeds 12% in any week, freeze all discount authority below the Studio Head level and review the discount log for unauthorised discounts.</div>
      </div>
    </div>''',
    ]

    conclusions = [
        f'''<div class="conclusion-item">
      <span class="conclusion-num">01</span>
      <span class="conclusion-text"><strong>August baseline (no intervention): &#8377;13&ndash;14L net sales.</strong> If the current trajectory continues &mdash; declining buyer count, sub-15% conversion, attendance holding flat &mdash; August will be marginally below July as the buyer contraction continues.</span>
    </div>''',
        f'''<div class="conclusion-item">
      <span class="conclusion-num">02</span>
      <span class="conclusion-text"><strong>August with intervention: &#8377;20&ndash;24L net sales.</strong> If the five strategic decisions are executed, conversion restoration adds ~{fmt_l(conv_uplift)}, visit-to-value adds ~{fmt_l(vtv_uplift)}, and lapsed reactivation begins contributing in late August. The combined effect is a 40&ndash;70% lift from July&rsquo;s &#8377;14.13L.</span>
    </div>''',
        f'''<div class="conclusion-item">
      <span class="conclusion-num">03</span>
      <span class="conclusion-text"><strong>The conversion rate is the leading indicator to monitor weekly.</strong> If conversion recovers above 15% by Week 2 of August, the intervention scenario is on track. If it stays below 10%, the baseline scenario is more likely and additional measures are needed.</span>
    </div>''',
        f'''<div class="conclusion-item">
      <span class="conclusion-num">04</span>
      <span class="conclusion-text"><strong>Retention improvements will lag the interventions by 60&ndash;90 days.</strong> The renewal pipeline and win-back campaign will show results in September&ndash;October, not August. Patience on renewal rate and churn rate is required &mdash; these metrics respond in Q3, not Week 1.</span>
    </div>''',
        f'''<div class="conclusion-item">
      <span class="conclusion-num">05</span>
      <span class="conclusion-text"><strong>The weekly red-flag monitor is what makes this report actionable.</strong> Without weekly monitoring, the monthly report is a post-mortem. With it, the monthly report is a forward-looking management tool. The three red flags above should be reviewed every Monday.</span>
    </div>''',
        f'''<div class="conclusion-item">
      <span class="conclusion-num">06</span>
      <span class="conclusion-text"><strong>The studio is one conversion-focused quarter from a structural step-up in economics.</strong> From July&rsquo;s &#8377;14.13L to a &#8377;25&ndash;30L steady-state is a 75&ndash;110% lift. The attendance base exists, the discount discipline is in place, and the five decisions are clear. The path from busy to profitable runs through the conversion funnel.</span>
    </div>''',
    ]

    # 7-month trend table for context
    trend_rows = []
    for i, m in enumerate(months):
        s = S[m]; f = F[m]; se = SE[m]
        lbl = m.split('-')[1] + ' ' + m.split('-')[0]
        is_july = m == '2026-07'
        so = '<strong>' if is_july else ''
        sc = '</strong>' if is_july else ''
        trend_rows.append(f'''<tr>
          <td class="metric-name">{so}{lbl}{sc}</td>
          <td class="num">{so}{fmt_l(s["net"])}{sc}</td>
          <td class="num">{so}{s["members"]}{sc}</td>
          <td class="num">{so}{se["visits"]:,}{sc}</td>
          <td class="num">{so}{f["converted"]}{sc}</td>
          <td class="num">{so}{f["conv_rate"]:.1f}%{sc}</td>
        </tr>''')

    return f'''
<section class="report-section" id="predictions">
  <div class="container">
    <div class="section-header">
      <div class="section-header-left">
        <span class="section-eyebrow">07 &middot; Predictions &amp; Forward View</span>
        <h2 class="section-title">August 2026 forecast: &#8377;13&ndash;14L net sales if no intervention, &#8377;20&ndash;24L if the five decisions are executed. Three red flags to monitor weekly.</h2>
        <p class="section-deck">
          July&rsquo;s &#8377;14.13L net sales is the floor, not the trend. Without intervention, the buyer-count decline and
          conversion breakdown will continue, and August will land at approximately <strong>&#8377;13&ndash;14L</strong>. With the
          five strategic decisions executed &mdash; conversion repair, visit-to-value monetisation, lapsed reactivation, scheduling
          optimisation, and sustained discount discipline &mdash; August should recover to <strong>&#8377;20&ndash;24L</strong>, a
          40&ndash;70% lift. The three weekly red flags below are the operational discipline that makes this forecast actionable.
        </p>
      </div>
      <div class="section-anchor">Section 07 / 07</div>
    </div>

    <div class="subsection">
      <h3 class="subsection-title">Seven-month context &mdash; the trend that August inherits</h3>
      <p class="subsection-deck">Net sales, buyers, visits, conversions, and conversion rate from January through July 2026. July is highlighted. The conversion rate decline from June to July is the steepest MoM change in the period and the primary driver of the August forecast.</p>
    </div>
    <div class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>Month</th>
            <th>Net Sales</th>
            <th>Buyers</th>
            <th>Visits</th>
            <th>Converted</th>
            <th>Conv Rate</th>
          </tr>
        </thead>
        <tbody>
          {''.join(trend_rows)}
        </tbody>
      </table>
    </div>

    <div class="subsection">
      <h3 class="subsection-title">August 2026 forecast &mdash; two scenarios</h3>
      <p class="subsection-deck">The baseline scenario extrapolates the current trajectory. The intervention scenario assumes the five strategic decisions are executed within 30 days. The gap between the two scenarios is the value of management action.</p>
    </div>
    <div class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>Scenario</th>
            <th>Net Sales</th>
            <th>Assumptions</th>
            <th>vs Jul 2026</th>
          </tr>
        </thead>
        <tbody>
          <tr class="status-bad"><td class="metric-name">Baseline (no intervention)</td><td class="num"><strong>{fmt_l(baseline_aug)}</strong></td><td class="num" style="text-align:left">Buyer count continues to decline; conversion stays at ~10%; attendance holds flat</td><td class="num">{badge(pc(baseline_aug, july_net))}</td></tr>
          <tr class="status-good"><td class="metric-name">Intervention (5 decisions executed)</td><td class="num"><strong>{fmt_l(intervention_aug)}</strong></td><td class="num" style="text-align:left">Conversion restored to 20% (+{fmt_l(conv_uplift)}); visit-to-value adds 15 packages (+{fmt_l(vtv_uplift)}); lapsed reactivation begins</td><td class="num">{badge(pc(intervention_aug, july_net))}</td></tr>
        </tbody>
      </table>
    </div>

    <div class="subsection">
      <h3 class="subsection-title">Weekly red flags to monitor</h3>
      <p class="subsection-deck">These three metrics should be reviewed every Monday. If any red flag is triggered, the corresponding escalation should be executed immediately &mdash; do not wait for the next monthly report.</p>
    </div>
    <div class="worked-grid">
      {''.join(flags)}
    </div>

    <div class="subsection">
      <h3 class="subsection-title">Data-backed conclusions</h3>
    </div>
    <div class="conclusions-block">
      {''.join(conclusions)}
    </div>
  </div>
</section>'''


# ============ FOOTER ============
def footer():
    return f'''
<footer class="footer">
  <div class="container">
    <div class="footer-grid">
      <div>
        <div class="footer-brand-text">Kwality House &middot; Studio Pulse</div>
        <p class="footer-text">
          Senior Management Performance Review for June &amp; July 2026. This report is generated from the Studio Pulse export,
          covering the period 01 June 2026 to 31 July 2026. All metrics are anchored to source data in the Studio Pulse workbook;
          comparisons use June 2026 (prior month), May 2026, the January &ndash; March 2026 baseline, and the same months year-on-year.
        </p>
        <p class="footer-text" style="margin-top:12px;">
          Methodology notes: Net Sales = MRP minus pre-tax (excl. VAT). Gross Sales = Payment Value (collected, incl. VAT).
          Discount Value = list-price discount. Units = transaction count (the Sale Item Quantity field is unreliable in this export).
          The Sales CSV&rsquo;s &ldquo;Payment Method&rdquo; column holds the transaction status (&ldquo;succeeded&rdquo;) and
          &ldquo;Payment Status&rdquo; holds the actual payment method &mdash; columns are reversed in the export. All data has been
          cross-validated against the May 2026 reference report.
        </p>
      </div>
      <div>
        <div class="footer-label">Report Contents</div>
        <p class="footer-text">
          01 Executive Summary<br>
          02 Revenue &amp; Sales Performance<br>
          03 New Client Conversion Funnel<br>
          04 Sessions &amp; Class Performance<br>
          05 Lapsed Memberships Deep Dive<br>
          06 Strategic Recommendations<br>
          07 Predictions &amp; Forward View
        </p>
      </div>
      <div>
        <div class="footer-label">Headline Metrics &middot; July 2026</div>
        <p class="footer-text">
          Net Sales: {fmt_l(july["net"])}<br>
          Visits: {sej["visits"]:,}<br>
          Fill Rate: {sej["fill"]:.1f}%<br>
          Conversion: {fj["conv_rate"]:.1f}%<br>
          Churn Rate: {lj["churn_rate"]:.1f}%<br>
          Discount Efficiency: &#8377;{july["disc_eff"]:.2f}
        </p>
      </div>
    </div>
  </div>
</footer>'''


# ============ ASSEMBLE ============
def build():
    head = '''<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Kwality House &middot; Performance Report &middot; June &amp; July 2026</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Source+Serif+Pro:wght@400;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
''' + CSS + '''
  </style>
</head>
<body>

<div class="topbar">
  <div class="topbar-inner">
    <div class="brand">
      <div class="brand-mark"></div>
      <div class="brand-text">
        Kwality House &middot; Studio Pulse
        <small>Performance Report &middot; June &amp; July 2026</small>
      </div>
    </div>
    <button class="theme-toggle" id="theme-toggle" aria-label="Toggle theme">
      <svg id="theme-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="4"></circle>
        <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"></path>
      </svg>
      <span id="theme-label">Dark</span>
    </button>
  </div>
</div>
'''

    body = hero() + section_01() + section_02() + section_03() + section_04() + section_05() + section_06() + section_07() + footer()

    script = '''

<script>
(function() {
  const root = document.documentElement;
  const toggle = document.getElementById('theme-toggle');
  const label = document.getElementById('theme-label');
  const icon = document.getElementById('theme-icon');

  const saved = localStorage.getItem('kh-theme') || 'dark';
  applyTheme(saved);

  toggle.addEventListener('click', () => {
    const current = root.getAttribute('data-theme') || 'dark';
    const next = current === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    localStorage.setItem('kh-theme', next);
  });

  function applyTheme(theme) {
    root.setAttribute('data-theme', theme);
    if (theme === 'dark') {
      label.textContent = 'Light';
      icon.innerHTML = '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>';
    } else {
      label.textContent = 'Dark';
      icon.innerHTML = '<circle cx="12" cy="12" r="4"></circle><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"></path>';
    }
  }
})();
</script>

</body>
</html>'''

    return head + body + script

if __name__ == '__main__':
    html_output = build()
    with open('Kwality_House_Performance_Report_June_July_2026.html', 'w') as f:
        f.write(html_output)
    print(f"Report generated: {len(html_output)} chars, {html_output.count(chr(10))} lines")
