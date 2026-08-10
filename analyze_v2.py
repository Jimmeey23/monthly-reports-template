#!/usr/bin/env python3
"""
Comprehensive analysis for 4 reports:
  Kwality House, Kemps Corner — June 2026
  Kwality House, Kemps Corner — July 2026
  Supreme HQ, Bandra — June 2026
  Supreme HQ, Bandra — July 2026

Key changes from v1:
  - Uses Sales file (15) with correct column labels (Payment Status = status, Payment Method = method)
  - Gross = Sale Total Paid In Currency (deduplicated by Sale ID)
  - Net = Mrp - Pre Tax (summed per row)
  - Discount = Sale Item Unit Discount Value (summed per row) — per user request
  - Location filter: Calculated Location contains 'Kwality' or 'Supreme'
  - Separate reports per location and per month
"""

import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime

INPUT_DIR = sys.argv[1] if len(sys.argv) > 1 else '.'
OUTPUT_JSON = sys.argv[2] if len(sys.argv) > 2 else 'analysis_v2.json'

SALES_FILE = os.path.join(INPUT_DIR, 'sales.csv')
SESSIONS_FILE = os.path.join(INPUT_DIR, 'sessions.csv')
CHECKINS_FILE = os.path.join(INPUT_DIR, 'checkins.csv')
LEADS_FILE = os.path.join(INPUT_DIR, 'leads.csv')
NEW_FILE = os.path.join(INPUT_DIR, 'new.csv')
LAPSED_FILE = os.path.join(INPUT_DIR, 'lapsed.csv')
LAPSED_UNIQUE_FILE = os.path.join(INPUT_DIR, 'lapsed_unique.csv')
ACTIVE_FILE = os.path.join(INPUT_DIR, 'active.csv')


def run_analysis(input_dir, output_json):
    global INPUT_DIR, OUTPUT_JSON, SALES_FILE, SESSIONS_FILE, CHECKINS_FILE, LEADS_FILE, NEW_FILE, LAPSED_FILE, LAPSED_UNIQUE_FILE, ACTIVE_FILE
    INPUT_DIR = input_dir
    OUTPUT_JSON = output_json
    SALES_FILE = os.path.join(INPUT_DIR, 'sales.csv')
    SESSIONS_FILE = os.path.join(INPUT_DIR, 'sessions.csv')
    CHECKINS_FILE = os.path.join(INPUT_DIR, 'checkins.csv')
    LEADS_FILE = os.path.join(INPUT_DIR, 'leads.csv')
    NEW_FILE = os.path.join(INPUT_DIR, 'new.csv')
    LAPSED_FILE = os.path.join(INPUT_DIR, 'lapsed.csv')
    LAPSED_UNIQUE_FILE = os.path.join(INPUT_DIR, 'lapsed_unique.csv')
    ACTIVE_FILE = os.path.join(INPUT_DIR, 'active.csv')
    main()


def slugify(name):
    token = re.sub(r'[^a-z0-9]', '', name.split(',')[0].split(' ')[0].lower())
    return token or 'loc'


def sniff_delimiter(path):
    """Exports come in as comma or tab separated depending on source; pick
    whichever delimiter actually splits the header into multiple columns."""
    try:
        with open(path, encoding='utf-8-sig') as f:
            header = f.readline()
    except OSError:
        return ','
    return '\t' if header.count('\t') > header.count(',') else ','


def _require_column(fieldnames, name):
    if fieldnames is not None and name not in fieldnames:
        raise RuntimeError(
            f"sales.csv is missing the required column '{name}'. "
            f"Columns found: {', '.join(fieldnames) if fieldnames else '(none — file may be empty)'}"
        )


def detect_locations():
    """Scan the sales file for distinct 'Calculated Location' values and build
    {loc_key: full_name} from them. loc_key is derived from the first word of
    the location name (e.g. 'Kwality House, Kemps Corner' -> 'kwality')."""
    names = []
    seen = set()
    with open(SALES_FILE, encoding='utf-8-sig') as f:
        r = csv.DictReader(f, delimiter=sniff_delimiter(SALES_FILE))
        _require_column(r.fieldnames, 'Calculated Location')
        row_count = 0
        for row in r:
            row_count += 1
            loc = (row.get('Calculated Location') or '').strip()
            if loc and loc not in seen:
                seen.add(loc)
                names.append(loc)

    if row_count == 0:
        raise RuntimeError('sales.csv has a header row but no data rows.')

    locations = {}
    used_keys = set()
    for name in names:
        key = slugify(name)
        base_key = key
        i = 2
        while key in used_keys:
            key = f'{base_key}{i}'
            i += 1
        used_keys.add(key)
        locations[key] = name

    if not locations:
        raise RuntimeError(
            f"Scanned {row_count} row(s) in sales.csv but every 'Calculated Location' value was blank."
        )
    return locations


def detect_months():
    """Scan the sales file for distinct YYYY-MM values in 'Payment Date'
    among rows whose 'Payment Status' is 'succeeded' (case-insensitive)."""
    months = set()
    succeeded_rows = 0
    with open(SALES_FILE, encoding='utf-8-sig') as f:
        r = csv.DictReader(f, delimiter=sniff_delimiter(SALES_FILE))
        _require_column(r.fieldnames, 'Payment Date')
        _require_column(r.fieldnames, 'Payment Status')
        for row in r:
            if (row.get('Payment Status') or '').strip().lower() != 'succeeded':
                continue
            succeeded_rows += 1
            m = month_key(row.get('Payment Date', ''))
            if re.match(r'^\d{4}-\d{2}$', m or ''):
                months.add(m)

    if succeeded_rows == 0:
        raise RuntimeError(
            "sales.csv has no rows with Payment Status = 'succeeded' — check the export filter."
        )
    if not months:
        raise RuntimeError(
            f"Found {succeeded_rows} succeeded row(s) in sales.csv but none had a parseable "
            "'Payment Date' (expected it to start with YYYY-MM)."
        )
    return sorted(months)


def yoy_month(m):
    """Given 'YYYY-MM', return the same month one year earlier."""
    year, mon = m.split('-')
    return f'{int(year) - 1}-{mon}'


def loc_key_for(location_str):
    """Match a raw location string (from any file) to a detected loc_key by
    checking whether that location's distinguishing first word appears in it."""
    for key, full_name in LOCATIONS.items():
        token = full_name.split(',')[0].split(' ')[0]
        if token and token in location_str:
            return key
    return None


def to_float(v):
    try:
        return float(v or '0')
    except:
        return 0.0

def to_int(v):
    try:
        return int(float(v or '0'))
    except:
        return 0

def month_key(pd_str):
    """Extract YYYY-MM from date string."""
    if not pd_str:
        return ''
    # Handle '2026-07-15, 10:30:00' format
    return pd_str[:7]


LOCATIONS = detect_locations()
MONTHS = detect_months()
YOY_MONTHS = sorted({yoy_month(m) for m in MONTHS})

# ===================== SALES =====================
def analyze_sales():
    """Analyze sales for all locations and months."""
    # Data structure: {loc_key: {month: {metrics}}}
    data = {lk: {} for lk in LOCATIONS}
    
    # Also track category, product, seller, payment breakdowns
    breakdowns = {lk: {m: {'category': defaultdict(lambda: {'gross': 0, 'net': 0, 'disc': 0, 'rows': 0, 'sales': set()}),
                           'product': defaultdict(lambda: {'gross': 0, 'net': 0, 'disc': 0, 'rows': 0, 'sales': set()}),
                           'seller': defaultdict(lambda: {'gross': 0, 'net': 0, 'disc': 0, 'rows': 0, 'sales': set()}),
                           'payment': defaultdict(lambda: {'gross': 0, 'net': 0, 'disc': 0, 'rows': 0, 'sales': set()})}
                      for m in MONTHS + YOY_MONTHS}
                 for lk in LOCATIONS}
    
    with open(SALES_FILE, encoding='utf-8-sig') as f:
        r = csv.DictReader(f, delimiter=sniff_delimiter(SALES_FILE))
        # sales_data[loc_key][month][sale_id] = sale_total_paid
        sales_data = {lk: defaultdict(dict) for lk in LOCATIONS}
        # per-row accumulators
        row_data = {lk: defaultdict(lambda: {'net': 0, 'disc': 0, 'rows': 0, 'members': set(), 'sale_ids': set()})
                   for lk in LOCATIONS}
        
        for row in r:
            if row.get('Payment Status') != 'succeeded':
                continue
            loc = row.get('Calculated Location', '')
            loc_key = loc_key_for(loc)
            if not loc_key:
                continue
            
            pd = row.get('Payment Date', '')
            month = month_key(pd)
            if month not in MONTHS + YOY_MONTHS:
                continue
            
            sid = row.get('Sale ID', '')
            stp = to_float(row.get('Sale Total Paid In Currency', '0'))
            mrp = to_float(row.get('Mrp - Pre Tax', '0'))
            disc = to_float(row.get('Sale Item Unit Discount Value', '0'))
            
            # Store sale total (deduplicated)
            if sid not in sales_data[loc_key][month]:
                sales_data[loc_key][month][sid] = stp
            
            # Accumulate per-row
            rd = row_data[loc_key][month]
            rd['net'] += mrp
            rd['disc'] += disc
            rd['rows'] += 1
            rd['members'].add(row.get('Paying Member ID', ''))
            rd['sale_ids'].add(sid)
            
            # Breakdowns
            cat = row.get('Cleaned Category', '') or 'Uncategorized'
            prod = row.get('Sale Item Name', '') or 'Unknown'
            seller = row.get('Sold By', '') or 'System / Unattributed'
            pay_method = row.get('Payment Method', '') or 'Unknown'
            
            for btype, bval in [('category', cat), ('product', prod), ('seller', seller), ('payment', pay_method)]:
                bd = breakdowns[loc_key][month][btype][bval]
                bd['net'] += mrp
                bd['disc'] += disc
                bd['rows'] += 1
                bd['sales'].add(sid)
                # We'll fill gross later from sales_data
        
        # Compute gross from deduplicated sales
        for loc_key in LOCATIONS:
            for month in MONTHS + YOY_MONTHS:
                gross = sum(sales_data[loc_key][month].values())
                rd = row_data[loc_key][month]
                net = rd['net']
                disc = rd['disc']
                sales_count = len(rd['sale_ids'])
                members = len(rd['members'])
                atv = gross / sales_count if sales_count else 0
                # Discount efficiency = actual revenue collected per rupee discounted
                disc_eff = gross / disc if disc > 0 else 0
                
                data[loc_key][month] = {
                    'gross': gross,
                    'net': net,
                    'disc': disc,
                    'sales': sales_count,
                    'members': members,
                    'atv': atv,
                    'disc_eff': disc_eff,
                    'rows': rd['rows'],
                }
                
                # Fill breakdown gross from sales_data
                for btype in ['category', 'product', 'seller', 'payment']:
                    for bval, bd in breakdowns[loc_key][month][btype].items():
                        # Sum gross for sales that have this breakdown value
                        # We need to re-iterate... actually let's compute gross per breakdown
                        # by summing unique sale totals for sales that have this value
                        pass  # We'll compute this separately
        
        # Now compute breakdowns properly - need to re-read for gross per breakdown
        # Actually, let's compute it from the sales_data we already have
        # For each breakdown, we need to track which sale IDs have which breakdown values
        # Let's redo this more carefully
    
    # Re-read for breakdowns with gross per sale
    breakdown_data = {lk: {m: {'category': defaultdict(lambda: {'gross': 0, 'net': 0, 'disc': 0, 'rows': 0, 'sales': set()}),
                                'product': defaultdict(lambda: {'gross': 0, 'net': 0, 'disc': 0, 'rows': 0, 'sales': set()}),
                                'seller': defaultdict(lambda: {'gross': 0, 'net': 0, 'disc': 0, 'rows': 0, 'sales': set()}),
                                'payment': defaultdict(lambda: {'gross': 0, 'net': 0, 'disc': 0, 'rows': 0, 'sales': set()})}
                      for m in MONTHS + YOY_MONTHS}
                     for lk in LOCATIONS}
    
    # Track sale -> breakdown values mapping
    sale_breakdown = {lk: defaultdict(lambda: {'category': set(), 'product': set(), 'seller': set(), 'payment': set()})
                     for lk in LOCATIONS}
    
    with open(SALES_FILE, encoding='utf-8-sig') as f:
        r = csv.DictReader(f, delimiter=sniff_delimiter(SALES_FILE))
        for row in r:
            if row.get('Payment Status') != 'succeeded':
                continue
            loc = row.get('Calculated Location', '')
            loc_key = loc_key_for(loc)
            if not loc_key:
                continue
            pd = row.get('Payment Date', '')
            month = month_key(pd)
            if month not in MONTHS + YOY_MONTHS:
                continue
            
            sid = row.get('Sale ID', '')
            mrp = to_float(row.get('Mrp - Pre Tax', '0'))
            disc = to_float(row.get('Sale Item Unit Discount Value', '0'))
            cat = row.get('Cleaned Category', '') or 'Uncategorized'
            prod = row.get('Sale Item Name', '') or 'Unknown'
            seller = row.get('Sold By', '') or 'System / Unattributed'
            pay_method = row.get('Payment Method', '') or 'Unknown'
            
            sale_breakdown[loc_key][sid]['category'].add(cat)
            sale_breakdown[loc_key][sid]['product'].add(prod)
            sale_breakdown[loc_key][sid]['seller'].add(seller)
            sale_breakdown[loc_key][sid]['payment'].add(pay_method)
            
            for btype, bval in [('category', cat), ('product', prod), ('seller', seller), ('payment', pay_method)]:
                bd = breakdown_data[loc_key][month][btype][bval]
                bd['net'] += mrp
                bd['disc'] += disc
                bd['rows'] += 1
                bd['sales'].add(sid)
    
    # Now fill gross per breakdown from sales_data
    for loc_key in LOCATIONS:
        for month in MONTHS + YOY_MONTHS:
            for btype in ['category', 'product', 'seller', 'payment']:
                for bval, bd in breakdown_data[loc_key][month][btype].items():
                    # Gross = sum of sale totals for sales that have this breakdown value
                    gross = 0
                    for sid in bd['sales']:
                        gross += sales_data[loc_key][month].get(sid, 0)
                    bd['gross'] = gross
    
    return data, breakdown_data, sales_data


def classify_format(class_name):
    """Every class is one of exactly 3 formats: PowerCycle, Strength Lab, or
    Barre (the default for anything not explicitly PowerCycle/Strength Lab)."""
    name = (class_name or '').lower()
    if 'powercycle' in name or 'power cycle' in name:
        return 'PowerCycle'
    if 'strength lab' in name:
        return 'Strength Lab'
    return 'Barre'


# ===================== SESSIONS =====================
def analyze_sessions():
    """Analyze sessions for all locations and months."""
    data = {lk: {} for lk in LOCATIONS}
    # Also track by class, trainer, time slot for heatmap
    by_class = {lk: {m: defaultdict(lambda: {'sessions': 0, 'visits': 0, 'capacity': 0, 'revenue': 0, 'empty': 0})
                    for m in MONTHS}
               for lk in LOCATIONS}
    by_trainer = {lk: {m: defaultdict(lambda: {'sessions': 0, 'visits': 0, 'capacity': 0, 'revenue': 0})
                      for m in MONTHS}
                 for lk in LOCATIONS}
    by_format = {lk: {m: defaultdict(lambda: {'sessions': 0, 'visits': 0, 'capacity': 0, 'revenue': 0, 'empty': 0})
                     for m in MONTHS}
                for lk in LOCATIONS}
    # Trainer x format specialization: {trainer: {format: {'sessions', 'visits', 'capacity'}}}
    by_trainer_format = {lk: {m: defaultdict(lambda: defaultdict(lambda: {'sessions': 0, 'visits': 0, 'capacity': 0}))
                             for m in MONTHS}
                        for lk in LOCATIONS}
    # Heatmap now also tracks which formats/trainers made up each cell
    heatmap = {lk: {m: defaultdict(lambda: defaultdict(lambda: {
                        'visits': 0, 'capacity': 0, 'sessions': 0,
                        'formats': defaultdict(int), 'trainers': defaultdict(int),
                    }))
                   for m in MONTHS}
              for lk in LOCATIONS}

    with open(SESSIONS_FILE, encoding='utf-8-sig') as f:
        r = csv.DictReader(f, delimiter=sniff_delimiter(SESSIONS_FILE))
        for row in r:
            loc = row.get('Location', '')
            loc_key = loc_key_for(loc)
            if not loc_key:
                continue
            d = row.get('Date', '')
            month = month_key(d)
            if month not in MONTHS:
                continue

            cap = to_int(row.get('Capacity', '0'))
            chk = to_int(row.get('CheckedIn', '0'))
            rev = to_float(row.get('Revenue', '0'))
            cls = row.get('Class', '') or 'Unknown Class'
            trainer = row.get('Trainer', '') or 'Unknown'
            day = row.get('Day', '')
            time = row.get('Time', '')
            fmt_name = classify_format(cls)

            if month not in data[loc_key]:
                data[loc_key][month] = {'sessions': 0, 'visits': 0, 'capacity': 0, 'revenue': 0, 'empty': 0}

            dm = data[loc_key][month]
            dm['sessions'] += 1
            dm['visits'] += chk
            dm['capacity'] += cap
            dm['revenue'] += rev
            if chk == 0:
                dm['empty'] += 1

            # By class (uses the 'Class' column, not 'SessionName')
            bc = by_class[loc_key][month][cls]
            bc['sessions'] += 1
            bc['visits'] += chk
            bc['capacity'] += cap
            bc['revenue'] += rev
            if chk == 0:
                bc['empty'] += 1

            # By trainer
            bt = by_trainer[loc_key][month][trainer]
            bt['sessions'] += 1
            bt['visits'] += chk
            bt['capacity'] += cap
            bt['revenue'] += rev

            # By format: Barre / PowerCycle / Strength Lab
            bf = by_format[loc_key][month][fmt_name]
            bf['sessions'] += 1
            bf['visits'] += chk
            bf['capacity'] += cap
            bf['revenue'] += rev
            if chk == 0:
                bf['empty'] += 1

            # Trainer x format specialization
            btf = by_trainer_format[loc_key][month][trainer][fmt_name]
            btf['sessions'] += 1
            btf['visits'] += chk
            btf['capacity'] += cap

            # Heatmap: time slot x day of week, plus format/trainer composition
            time_slot = time[:5] if time else 'Unknown'
            hm = heatmap[loc_key][month][time_slot][day]
            hm['visits'] += chk
            hm['capacity'] += cap
            hm['sessions'] += 1
            hm['formats'][fmt_name] += 1
            hm['trainers'][trainer] += 1

    # Compute fill rates
    for loc_key in LOCATIONS:
        for month in MONTHS:
            if month in data[loc_key]:
                dm = data[loc_key][month]
                dm['fill'] = dm['visits'] / dm['capacity'] * 100 if dm['capacity'] else 0
                dm['avg_visits'] = dm['visits'] / dm['sessions'] if dm['sessions'] else 0

    return data, by_class, by_trainer, by_format, heatmap, by_trainer_format


# ===================== LEADS / FUNNEL =====================
def analyze_leads():
    """Analyze leads for conversion funnel."""
    data = {lk: {} for lk in LOCATIONS}
    by_source = {lk: {m: defaultdict(lambda: {'total': 0, 'converted': 0})
                     for m in MONTHS}
                for lk in LOCATIONS}
    
    with open(LEADS_FILE, encoding='utf-8-sig') as f:
        r = csv.DictReader(f, delimiter=sniff_delimiter(LEADS_FILE))
        for row in r:
            center = row.get('Center', '')
            loc_key = loc_key_for(center)
            if not loc_key:
                continue
            ca = row.get('Created At', '')
            month = month_key(ca)
            if month not in MONTHS:
                continue
            
            if month not in data[loc_key]:
                data[loc_key][month] = {'total': 0, 'converted': 0}
            
            data[loc_key][month]['total'] += 1
            cs = row.get('Conversion Status', '')
            if cs == 'Converted':
                data[loc_key][month]['converted'] += 1
            
            source = row.get('Source Name', '') or 'Unknown'
            by_source[loc_key][month][source]['total'] += 1
            if cs == 'Converted':
                by_source[loc_key][month][source]['converted'] += 1
    
    # Compute rates
    for loc_key in LOCATIONS:
        for month in MONTHS:
            if month in data[loc_key]:
                d = data[loc_key][month]
                d['rate'] = d['converted'] / d['total'] * 100 if d['total'] else 0
    
    return data, by_source


# ===================== NEW (TRIALS) =====================
def analyze_new():
    """Analyze trials from New file."""
    data = {lk: {} for lk in LOCATIONS}
    by_type = {lk: {m: defaultdict(int) for m in MONTHS} for lk in LOCATIONS}
    
    with open(NEW_FILE, encoding='utf-8-sig') as f:
        r = csv.DictReader(f, delimiter=sniff_delimiter(NEW_FILE))
        for row in r:
            fvl = row.get('First Visit Location', '')
            loc_key = loc_key_for(fvl)
            if not loc_key:
                continue
            my = row.get('Month Year', '')
            # Convert "Jul-2026" to "2026-07"
            month = None
            for m_name, m_num in [('Jan', '01'), ('Feb', '02'), ('Mar', '03'), ('Apr', '04'),
                                   ('May', '05'), ('Jun', '06'), ('Jul', '07'), ('Aug', '08'),
                                   ('Sep', '09'), ('Oct', '10'), ('Nov', '11'), ('Dec', '12')]:
                if my.startswith(m_name):
                    year = my.split('-')[1] if '-' in my else ''
                    month = f'{year}-{m_num}'
                    break
            if month not in MONTHS:
                continue
            
            is_new = row.get('Is New', '')
            if not is_new.startswith('New'):
                continue
            
            if month not in data[loc_key]:
                data[loc_key][month] = {'trials': 0, 'retained': 0}
            
            data[loc_key][month]['trials'] += 1
            rs = row.get('Retention Status', '')
            if rs == 'Retained':
                data[loc_key][month]['retained'] += 1
            
            by_type[loc_key][month][is_new] += 1
    
    return data, by_type


# ===================== LAPSED =====================
# Membership names matching any of these (case-insensitive substring) are
# zero/trial-type products and are excluded from lapsed evaluation, e.g.
# 'Studio Single Class', 'Newcomers 2 For 1', 'New Client Intro Pack',
# 'Pop-up Studio Single Class'.
LAPSED_EXCLUDE_PATTERNS = ['single class', '2 for 1', 'intro pack']


def is_excluded_lapsed_membership(product_name, amount_paid):
    """True if this membership should be excluded from lapsed metrics:
    zero-value memberships (comps/freebies) or single-class/trial products."""
    if to_float(amount_paid) <= 0:
        return True
    name = (product_name or '').lower()
    return any(p in name for p in LAPSED_EXCLUDE_PATTERNS)


def analyze_lapsed():
    """Analyze lapsed memberships."""
    data = {lk: {} for lk in LOCATIONS}
    by_product = {lk: {m: defaultdict(lambda: {'total': 0, 'renewed': 0, 'lapsed': 0, 'frozen': 0})
                      for m in MONTHS}
                 for lk in LOCATIONS}
    # Cumulative unique lapsed
    cumulative = {lk: defaultdict(set) for lk in LOCATIONS}

    with open(LAPSED_FILE, encoding='utf-8-sig') as f:
        r = csv.DictReader(f, delimiter=sniff_delimiter(LAPSED_FILE))
        for row in r:
            loc = row.get('Primary Location', '')
            loc_key = loc_key_for(loc)
            if not loc_key:
                continue
            ed = row.get('End Date', '')
            month = month_key(ed)
            if month not in MONTHS:
                continue

            status = row.get('Status', '')
            product = row.get('Membership Name', '') or 'Unknown'
            member_id = row.get('Member ID', '')

            if is_excluded_lapsed_membership(product, row.get('Amount Paid', '0')):
                continue

            if month not in data[loc_key]:
                data[loc_key][month] = {'total': 0, 'renewed': 0, 'lapsed': 0, 'frozen': 0}
            
            d = data[loc_key][month]
            d['total'] += 1
            if status == 'Renewed':
                d['renewed'] += 1
            elif status == 'Lapsed':
                d['lapsed'] += 1
            elif status == 'Frozen':
                d['frozen'] += 1
            
            # By product
            bp = by_product[loc_key][month][product]
            bp['total'] += 1
            if status == 'Renewed':
                bp['renewed'] += 1
            elif status == 'Lapsed':
                bp['lapsed'] += 1
            elif status == 'Frozen':
                bp['frozen'] += 1
            
            # Cumulative unique lapsed members
            if status == 'Lapsed':
                cumulative[loc_key][month].add(member_id)
    
    # Compute rates
    for loc_key in LOCATIONS:
        for month in MONTHS:
            if month in data[loc_key]:
                d = data[loc_key][month]
                d['churn'] = d['lapsed'] / d['total'] * 100 if d['total'] else 0
                d['renewal_rate'] = d['renewed'] / d['total'] * 100 if d['total'] else 0
    
    # Cumulative unique lapsed (running total)
    cum_data = {lk: {} for lk in LOCATIONS}
    for loc_key in LOCATIONS:
        running = set()
        for month in MONTHS:
            running.update(cumulative[loc_key][month])
            cum_data[loc_key][month] = len(running)
    
    return data, by_product, cum_data


# ===================== CHECKINS (LATE CANCELS) =====================
def analyze_checkins():
    """Analyze late cancellations."""
    data = {lk: {} for lk in LOCATIONS}
    member_cancels = {lk: {m: defaultdict(int) for m in MONTHS} for lk in LOCATIONS}
    
    with open(CHECKINS_FILE, encoding='utf-8-sig') as f:
        r = csv.DictReader(f, delimiter=sniff_delimiter(CHECKINS_FILE))
        for row in r:
            loc = row.get('Location', '')
            loc_key = loc_key_for(loc)
            if not loc_key:
                continue
            d = row.get('Date (IST)', '')
            month = month_key(d)
            if month not in MONTHS:
                continue
            
            if month not in data[loc_key]:
                data[loc_key][month] = {'total': 0, 'late_cancel': 0, 'lc_members': set()}
            
            dm = data[loc_key][month]
            dm['total'] += 1
            lc = row.get('Is Late Cancelled', '')
            if lc in ('TRUE', 'True', 'true'):
                dm['late_cancel'] += 1
                mid = row.get('Member ID', '')
                dm['lc_members'].add(mid)
                member_cancels[loc_key][month][mid] += 1
    
    # Convert sets to counts and add heavy canceler stats
    for loc_key in LOCATIONS:
        for month in MONTHS:
            if month in data[loc_key]:
                dm = data[loc_key][month]
                dm['lc_member_count'] = len(dm['lc_members'])
                del dm['lc_members']
                # Heavy cancelers (6+ late cancels)
                cancels = member_cancels[loc_key][month]
                dm['heavy_cancelers'] = sum(1 for c in cancels.values() if c >= 6)
                dm['max_cancels'] = max(cancels.values()) if cancels else 0
    
    return data, member_cancels


# ===================== ACTIVE MEMBERSHIPS =====================
def analyze_active():
    """Analyze active memberships snapshot."""
    data = {lk: {'total': 0, 'types': defaultdict(int)} for lk in LOCATIONS}
    
    with open(ACTIVE_FILE, encoding='utf-8-sig') as f:
        r = csv.DictReader(f, delimiter=sniff_delimiter(ACTIVE_FILE))
        for row in r:
            loc = row.get('Home Location', '')
            loc_key = loc_key_for(loc)
            if not loc_key:
                continue
            
            data[loc_key]['total'] += 1
            mtype = row.get('Membership Type', '') or 'Unknown'
            data[loc_key]['types'][mtype] += 1
    
    return data


# ===================== MAIN =====================
def main():
    print("Analyzing sales...")
    sales_data, sales_breakdowns, sales_by_id = analyze_sales()
    
    print("Analyzing sessions...")
    sessions_data, sessions_by_class, sessions_by_trainer, sessions_by_format, heatmap_data, sessions_by_trainer_format = analyze_sessions()
    
    print("Analyzing leads...")
    leads_data, leads_by_source = analyze_leads()
    
    print("Analyzing trials...")
    new_data, new_by_type = analyze_new()
    
    print("Analyzing lapsed...")
    lapsed_data, lapsed_by_product, lapsed_cumulative = analyze_lapsed()
    
    print("Analyzing checkins...")
    checkins_data, checkins_member_cancels = analyze_checkins()
    
    print("Analyzing active memberships...")
    active_data = analyze_active()
    
    # Build baseline (average of the 3 months trailing right before the most
    # recent month in the data — a recent-quarter reference point)
    baseline = {}
    bl_months = MONTHS[-4:-1] if len(MONTHS) >= 4 else MONTHS[:-1]
    for loc_key in LOCATIONS:
        baseline[loc_key] = {}
        
        # Sales baseline
        bl_sales = {'gross': 0, 'net': 0, 'disc': 0, 'sales': 0, 'members': 0, 'count': 0}
        for m in bl_months:
            if m in sales_data[loc_key]:
                s = sales_data[loc_key][m]
                bl_sales['gross'] += s['gross']
                bl_sales['net'] += s['net']
                bl_sales['disc'] += s['disc']
                bl_sales['sales'] += s['sales']
                bl_sales['members'] += s['members']
                bl_sales['count'] += 1
        if bl_sales['count']:
            for k in ['gross', 'net', 'disc', 'sales', 'members']:
                bl_sales[k] /= bl_sales['count']
            bl_sales['atv'] = bl_sales['gross'] / bl_sales['sales'] if bl_sales['sales'] else 0
            bl_sales['disc_eff'] = bl_sales['gross'] / bl_sales['disc'] if bl_sales['disc'] else 0
        baseline[loc_key]['sales'] = bl_sales
        
        # Sessions baseline
        bl_sess = {'sessions': 0, 'visits': 0, 'capacity': 0, 'revenue': 0, 'empty': 0, 'count': 0}
        for m in bl_months:
            if m in sessions_data[loc_key]:
                s = sessions_data[loc_key][m]
                bl_sess['sessions'] += s['sessions']
                bl_sess['visits'] += s['visits']
                bl_sess['capacity'] += s['capacity']
                bl_sess['revenue'] += s['revenue']
                bl_sess['empty'] += s['empty']
                bl_sess['count'] += 1
        if bl_sess['count']:
            for k in ['sessions', 'visits', 'capacity', 'revenue', 'empty']:
                bl_sess[k] /= bl_sess['count']
            bl_sess['fill'] = bl_sess['visits'] / bl_sess['capacity'] * 100 if bl_sess['capacity'] else 0
            bl_sess['avg_visits'] = bl_sess['visits'] / bl_sess['sessions'] if bl_sess['sessions'] else 0
        baseline[loc_key]['sessions'] = bl_sess
        
        # Leads baseline
        bl_leads = {'total': 0, 'converted': 0, 'count': 0}
        for m in bl_months:
            if m in leads_data[loc_key]:
                l = leads_data[loc_key][m]
                bl_leads['total'] += l['total']
                bl_leads['converted'] += l['converted']
                bl_leads['count'] += 1
        if bl_leads['count']:
            bl_leads['total'] /= bl_leads['count']
            bl_leads['converted'] /= bl_leads['count']
            bl_leads['rate'] = bl_leads['converted'] / bl_leads['total'] * 100 if bl_leads['total'] else 0
        baseline[loc_key]['leads'] = bl_leads
        
        # Lapsed baseline
        bl_lapsed = {'total': 0, 'renewed': 0, 'lapsed': 0, 'frozen': 0, 'count': 0}
        for m in bl_months:
            if m in lapsed_data[loc_key]:
                l = lapsed_data[loc_key][m]
                bl_lapsed['total'] += l['total']
                bl_lapsed['renewed'] += l['renewed']
                bl_lapsed['lapsed'] += l['lapsed']
                bl_lapsed['frozen'] += l['frozen']
                bl_lapsed['count'] += 1
        if bl_lapsed['count']:
            for k in ['total', 'renewed', 'lapsed', 'frozen']:
                bl_lapsed[k] /= bl_lapsed['count']
            bl_lapsed['churn'] = bl_lapsed['lapsed'] / bl_lapsed['total'] * 100 if bl_lapsed['total'] else 0
            bl_lapsed['renewal_rate'] = bl_lapsed['renewed'] / bl_lapsed['total'] * 100 if bl_lapsed['total'] else 0
        baseline[loc_key]['lapsed'] = bl_lapsed
    
    # Assemble all data
    all_data = {
        'sales': sales_data,
        'sales_breakdowns': {lk: {m: {bt: dict(bd) for bt, bd in bts.items()} 
                                   for m, bts in months.items()}
                            for lk, months in sales_breakdowns.items()},
        'sales_by_id': {lk: {m: dict(sids) for m, sids in months.items()}
                       for lk, months in sales_by_id.items()},
        'sessions': sessions_data,
        'sessions_by_class': {lk: {m: dict(bc) for m, bc in months.items()}
                             for lk, months in sessions_by_class.items()},
        'sessions_by_trainer': {lk: {m: dict(bt) for m, bt in months.items()}
                               for lk, months in sessions_by_trainer.items()},
        'sessions_by_format': {lk: {m: dict(bf) for m, bf in months.items()}
                              for lk, months in sessions_by_format.items()},
        'sessions_by_trainer_format': {lk: {m: {tr: dict(fmts) for tr, fmts in trs.items()}
                                           for m, trs in months.items()}
                                      for lk, months in sessions_by_trainer_format.items()},
        'heatmap': {lk: {m: {ts: dict(days) for ts, days in slots.items()}
                        for m, slots in months.items()}
                   for lk, months in heatmap_data.items()},
        'leads': leads_data,
        'leads_by_source': {lk: {m: dict(bs) for m, bs in months.items()}
                           for lk, months in leads_by_source.items()},
        'new': new_data,
        'new_by_type': {lk: {m: dict(bt) for m, bt in months.items()}
                       for lk, months in new_by_type.items()},
        'lapsed': lapsed_data,
        'lapsed_by_product': {lk: {m: dict(bp) for m, bp in months.items()}
                             for lk, months in lapsed_by_product.items()},
        'lapsed_cumulative': lapsed_cumulative,
        'checkins': checkins_data,
        'active': {lk: {'total': v['total'], 'types': dict(v['types'])}
                   for lk, v in active_data.items()},
        'baseline': baseline,
        'meta': {
            'locations': LOCATIONS,
            'months': MONTHS,
            'baseline_months': bl_months,
        },
    }

    with open(OUTPUT_JSON, 'w') as f:
        json.dump(all_data, f, indent=2, default=str)

    print(f"\nAnalysis saved to {OUTPUT_JSON}")

    # Print summary for every detected location x month
    print("\n" + "=" * 80)
    print("SUMMARY: Key metrics")
    print("=" * 80)

    for loc_key, loc_name in LOCATIONS.items():
        for month in MONTHS:
            print(f"\n--- {loc_name} | {month} ---")
            s = sales_data[loc_key].get(month, {})
            sess = sessions_data[loc_key].get(month, {})
            lead = leads_data[loc_key].get(month, {})
            new = new_data[loc_key].get(month, {})
            lap = lapsed_data[loc_key].get(month, {})
            chk = checkins_data[loc_key].get(month, {})

            print(f"  Sales: Gross ₹{s.get('gross',0)/100000:.2f}L, Net ₹{s.get('net',0)/100000:.2f}L, Disc ₹{s.get('disc',0)/100000:.2f}L")
            print(f"  Sales: {s.get('sales',0)} txn, {s.get('members',0)} members, ATV ₹{s.get('atv',0):,.0f}")
            print(f"  Sessions: {sess.get('sessions',0)} sessions, {sess.get('visits',0)} visits, {sess.get('fill',0):.1f}% fill")
            print(f"  Sessions revenue: ₹{sess.get('revenue',0)/100000:.2f}L")
            print(f"  Leads: {lead.get('total',0)} leads, {lead.get('converted',0)} converted ({lead.get('rate',0):.1f}%)")
            print(f"  Trials: {new.get('trials',0)} trials, {new.get('retained',0)} retained")
            print(f"  Lapsed: {lap.get('total',0)} total, {lap.get('renewed',0)} renewed, {lap.get('lapsed',0)} lapsed ({lap.get('churn',0):.1f}% churn)")
            print(f"  Checkins: {chk.get('total',0)} total, {chk.get('late_cancel',0)} late cancels, {chk.get('lc_member_count',0)} LC members")


if __name__ == '__main__':
    main()
