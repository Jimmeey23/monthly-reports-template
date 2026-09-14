#!/usr/bin/env python3
"""
Comprehensive analysis for 4 reports:
  Kwality House, Kemps Corner — June 2026
  Kwality House, Kemps Corner — July 2026
  Supreme HQ, Bandra — June 2026
  Supreme HQ, Bandra — July 2026

Supported sales exports:
  - Legacy 99-column export and revised 48-column export
  - Gross = Sale Total Paid In Currency / Payment Value (summed per line item)
  - Net = Gross - Payment VAT, i.e. collected revenue excluding VAT
  - List value = Mrp - Pre Tax / Price Excluding VAT In Currency, kept as the
    separate `list_value` metric (it is a pre-discount, pre-VAT list figure and
    is deliberately NOT reported as net)
  - Discount = Sale Item Unit Discount Value (summed per row)
  - Transactions = distinct Payment Transaction ID (not Sale ID)
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


def _require_any_column(fieldnames, metric, names):
    """Accept equivalent columns from the legacy and revised sales exports."""
    for name in names:
        if fieldnames is not None and name in fieldnames:
            return name
    raise RuntimeError(
        f"sales.csv is missing a column for {metric}. Expected one of: "
        f"{', '.join(names)}. Columns found: "
        f"{', '.join(fieldnames) if fieldnames else '(none — file may be empty)'}"
    )


def _first_present(fieldnames, names):
    """Return the first of `names` present in the export, or None."""
    for name in names:
        if fieldnames is not None and name in fieldnames:
            return name
    return None


def detect_sales_schema(fieldnames):
    """Map report metrics onto either supported Momence sales export shape."""
    return {
        'gross': _require_any_column(
            fieldnames, 'gross revenue',
            ('Sale Total Paid In Currency', 'Payment Value'),
        ),
        'net': _require_any_column(
            fieldnames, 'net revenue before VAT',
            ('Mrp - Pre Tax', 'Price Excluding VAT In Currency'),
        ),
        'discount': _require_any_column(
            fieldnames, 'item discount',
            ('Sale Item Unit Discount Value', 'Discount Value In Currency'),
        ),
        # Optional: only the revised export carries VAT and a payment
        # transaction id. Both fall back gracefully when absent.
        'vat': _first_present(fieldnames, ('Payment VAT', 'Sale Item Unit VAT Amount')),
        'txn': _first_present(fieldnames, ('Payment Transaction ID', 'Sale ID')),
        'product': _require_any_column(
            fieldnames, 'product name',
            ('Sale Item Name', 'Cleaned Product'),
        ),
    }


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
        cleaned = str(v or '0').strip().replace(',', '').replace('₹', '')
        if cleaned in ('', '-'):
            return 0.0
        if cleaned.startswith('(') and cleaned.endswith(')'):
            cleaned = '-' + cleaned[1:-1]
        return float(cleaned)
    except:
        return 0.0

def to_int(v):
    try:
        return int(float(v or '0'))
    except:
        return 0

def month_key(pd_str):
    """Extract YYYY-MM from a date string. Supports:
    - '2026-07-15, 10:30:00' (ISO, YYYY-MM-DD...)
    - '09/08/2026 21:03:52'  (DD/MM/YYYY...)"""
    if not pd_str:
        return ''
    s = pd_str.strip()
    if re.match(r'^\d{4}-\d{2}-\d{2}', s):
        return s[:7]
    m = re.match(r'^(\d{2})/(\d{2})/(\d{4})', s)
    if m:
        day, month, year = m.groups()
        return f'{year}-{month}'
    return ''


LOCATIONS = detect_locations()
MONTHS = detect_months()
YOY_MONTHS = sorted({yoy_month(m) for m in MONTHS})

# ===================== SALES =====================
def analyze_sales():
    """Analyze sales for all locations and months."""
    # Data structure: {loc_key: {month: {metrics}}}
    data = {lk: {} for lk in LOCATIONS}
    
    # Also track category, product, seller, payment breakdowns
    breakdowns = {lk: {m: {'category': defaultdict(lambda: {'gross': 0.0, 'net': 0.0, 'list_value': 0.0, 'disc': 0.0, 'rows': 0, 'sales': set()}),
                           'product': defaultdict(lambda: {'gross': 0.0, 'net': 0.0, 'list_value': 0.0, 'disc': 0.0, 'rows': 0, 'sales': set()}),
                           'seller': defaultdict(lambda: {'gross': 0.0, 'net': 0.0, 'list_value': 0.0, 'disc': 0.0, 'rows': 0, 'sales': set()}),
                           'payment': defaultdict(lambda: {'gross': 0.0, 'net': 0.0, 'list_value': 0.0, 'disc': 0.0, 'rows': 0, 'sales': set()})}
                      for m in MONTHS + YOY_MONTHS}
                 for lk in LOCATIONS}
    
    with open(SALES_FILE, encoding='utf-8-sig') as f:
        r = csv.DictReader(f, delimiter=sniff_delimiter(SALES_FILE))
        schema = detect_sales_schema(r.fieldnames)
        # sales_data[loc_key][month][sale_id] = sale_total_paid
        sales_data = {lk: defaultdict(dict) for lk in LOCATIONS}
        # per-row accumulators
        row_data = {lk: defaultdict(lambda: {'gross': 0.0, 'net': 0.0, 'list_value': 0.0, 'disc': 0.0, 'rows': 0,
                                             'members': set(), 'sale_ids': set(), 'txn_ids': set()})
                   for lk in LOCATIONS}
        
        for row in r:
            if (row.get('Payment Status') or '').strip().lower() != 'succeeded':
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
            stp = to_float(row.get(schema['gross'], '0'))
            mrp = to_float(row.get(schema['net'], '0'))
            disc = to_float(row.get(schema['discount'], '0'))
            vat = to_float(row.get(schema['vat'], '0')) if schema.get('vat') else 0.0
            txn_id = row.get(schema['txn'], sid) if schema.get('txn') else sid

            # Sale ID -> first row's payment, kept for reference only.
            if sid not in sales_data[loc_key][month]:
                sales_data[loc_key][month][sid] = stp

            # Payment Value is a per-line-item amount, not a sale total
            # repeated on every row (a sale with a Studio Single Class at
            # 1,942 plus a Retail Product at 160 sums to 2,102, which is also
            # unit-price x qty). So every row is counted; keeping only the
            # first row per Sale ID dropped the extra line items — 30 of 339
            # sales in Aug 2026, worth Rs 1.36L or 4.5% of revenue.
            rd = row_data[loc_key][month]
            rd['gross'] += stp
            rd['net'] += stp - vat      # collected revenue, VAT exclusive
            rd['list_value'] += mrp     # pre-VAT list value of every line
            rd['disc'] += disc
            rd['rows'] += 1
            rd['members'].add(row.get('Paying Member ID', ''))
            rd['sale_ids'].add(sid)
            rd['txn_ids'].add(txn_id)
            
            # Breakdowns
            cat = row.get('Cleaned Category', '') or 'Uncategorized'
            prod = row.get(schema['product'], '') or 'Unknown'
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
                rd = row_data[loc_key][month]
                gross = rd['gross']
                net = rd['net']
                disc = rd['disc']
                # Transactions are payment transactions, not Sale IDs: one
                # payment can cover several sale rows (349 vs 340 in Jul 2026,
                # and 349 is the count the published July report prints).
                sales_count = len(rd['txn_ids']) or len(rd['sale_ids'])
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
                    'list_value': rd['list_value'],
                    'vat': gross - net,
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
    
    # Re-read for breakdowns with gross per sale.
    # `txns` holds the distinct payment transactions a bucket touched — the
    # denominator for AOV (revenue per transaction) and UPT (line items per
    # transaction). `rows` counts line items, so net/rows is a per-unit figure
    # and net/txns is a per-basket one; the tables print both.
    def _bucket():
        return {'gross': 0.0, 'net': 0.0, 'list_value': 0.0, 'disc': 0.0, 'rows': 0,
                'sales': set(), 'txns': set()}

    breakdown_data = {lk: {m: {'category': defaultdict(_bucket),
                                'product': defaultdict(_bucket),
                                'seller': defaultdict(_bucket),
                                'payment': defaultdict(_bucket)}
                      for m in MONTHS + YOY_MONTHS}
                     for lk in LOCATIONS}

    # The product rows that sit under each category, so the category table can
    # expand in place instead of sending the reader to a separate product table.
    cat_prod_data = {lk: {m: defaultdict(lambda: defaultdict(_bucket))
                          for m in MONTHS + YOY_MONTHS}
                     for lk in LOCATIONS}
    
    # Track sale -> breakdown values mapping
    sale_breakdown = {lk: defaultdict(lambda: {'category': set(), 'product': set(), 'seller': set(), 'payment': set()})
                     for lk in LOCATIONS}
    
    with open(SALES_FILE, encoding='utf-8-sig') as f:
        r = csv.DictReader(f, delimiter=sniff_delimiter(SALES_FILE))
        schema = detect_sales_schema(r.fieldnames)
        for row in r:
            if (row.get('Payment Status') or '').strip().lower() != 'succeeded':
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
            stp = to_float(row.get(schema['gross'], '0'))
            mrp = to_float(row.get(schema['net'], '0'))
            disc = to_float(row.get(schema['discount'], '0'))
            vat = to_float(row.get(schema['vat'], '0')) if schema.get('vat') else 0.0
            cat = row.get('Cleaned Category', '') or 'Uncategorized'
            prod = row.get(schema['product'], '') or 'Unknown'
            seller = row.get('Sold By', '') or 'System / Unattributed'
            pay_method = row.get('Payment Method', '') or 'Unknown'
            
            sale_breakdown[loc_key][sid]['category'].add(cat)
            sale_breakdown[loc_key][sid]['product'].add(prod)
            sale_breakdown[loc_key][sid]['seller'].add(seller)
            sale_breakdown[loc_key][sid]['payment'].add(pay_method)
            
            txn_id = row.get(schema['txn'], sid) if schema.get('txn') else sid

            for btype, bval in [('category', cat), ('product', prod), ('seller', seller), ('payment', pay_method)]:
                bd = breakdown_data[loc_key][month][btype][bval]
                bd['gross'] += stp
                bd['net'] += stp - vat
                bd['list_value'] += mrp
                bd['disc'] += disc
                bd['rows'] += 1
                bd['sales'].add(sid)
                bd['txns'].add(txn_id)

            cp = cat_prod_data[loc_key][month][cat][prod]
            cp['gross'] += stp
            cp['net'] += stp - vat
            cp['list_value'] += mrp
            cp['disc'] += disc
            cp['rows'] += 1
            cp['sales'].add(sid)
            cp['txns'].add(txn_id)
    
    # Gross is attributed per line item above, so every breakdown bucket adds
    # back up to the month's headline gross (the old pass assigned the whole
    # deduplicated sale total to each bucket, which double counted).
    # The nested product rows ride along inside the breakdown dict so every
    # existing caller of get_sales_breakdowns() keeps working unchanged.
    for lk in LOCATIONS:
        for m in MONTHS + YOY_MONTHS:
            breakdown_data[lk][m]['category_product'] = {
                cat: dict(prods) for cat, prods in cat_prod_data[lk][m].items()}

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
def _truthy(v):
    return str(v or '').strip().upper() in ('TRUE', '1', 'YES', 'Y', 'T')


def detect_sessions_schema(fieldnames):
    """Map the three session export shapes we see onto one vocabulary.

    roster   (checkins.csv): one row per member per class — Session ID,
                             Capacity, Checked In, Date (IST), Location
    bookings (sessions.csv): one row per booking — Location Name,
                             Session Date, Attended, Time Slot (no capacity)
    legacy                 : one row per class — Location, Date, Capacity,
                             CheckedIn, Revenue, Class, Trainer, Day, Time
    """
    def first(*names):
        for n in names:
            if fieldnames and n in fieldnames:
                return n
        return None

    return {
        'location':  first('Location', 'Location Name', 'Center'),
        'date':      first('Date (IST)', 'Session Date', 'Date'),
        'sid':       first('Session ID', 'Session Id'),
        'capacity':  first('Capacity'),
        'visits':    first('Checked In', 'Attended', 'CheckedIn'),
        'revenue':   first('Paid', 'Sale Value', 'Revenue'),
        'cls':       first('Cleaned Class', 'Session Name', 'Class'),
        'trainer':   first('Teacher Name', 'Trainer'),
        'day':       first('Day of Week', 'Day'),
        'time':      first('Time', 'Time Slot'),
        'host':      first('Host ID', 'Host Id'),
        'late':      first('LateCancelled', 'Late Cancelled', 'Is Late Cancelled'),
        'booked':    first('Booked', 'Booked Count'),
        'comps':     first('Complimentary', 'Complementary'),
    }


def sessions_source():
    """Pick the export that can actually answer fill-rate questions.

    Fill rate needs capacity, and only the roster export carries it, so a
    bookings-only upload would otherwise leave sessions at zero.
    """
    candidates = [SESSIONS_FILE, CHECKINS_FILE]
    fallback = None
    for path in candidates:
        if not os.path.exists(path):
            continue
        try:
            with open(path, encoding='utf-8-sig') as f:
                cols = csv.DictReader(f, delimiter=sniff_delimiter(path)).fieldnames or []
        except OSError:
            continue
        sch = detect_sessions_schema(cols)
        if not (sch['location'] and sch['date']):
            continue
        if sch['capacity'] and sch['visits']:
            return path, sch
        if fallback is None:
            fallback = (path, sch)
    if fallback:
        return fallback
    return None, None


def analyze_sessions():
    """Analyze sessions for all locations and months.

    Rows are bookings, not classes, in every export we receive, so rows are
    first collapsed into one record per class (Session ID, or date + time +
    class + host when the export has no id) and only then aggregated.
    """
    data = {lk: {} for lk in LOCATIONS}
    by_class = {lk: {m: defaultdict(lambda: {'sessions': 0, 'visits': 0, 'capacity': 0, 'revenue': 0.0, 'empty': 0})
                    for m in MONTHS}
               for lk in LOCATIONS}
    by_trainer = {lk: {m: defaultdict(lambda: {'sessions': 0, 'visits': 0, 'capacity': 0, 'revenue': 0.0,
                                               'empty': 0, 'classes': set(), 'days': set()})
                      for m in MONTHS}
                 for lk in LOCATIONS}
    by_format = {lk: {m: defaultdict(lambda: {'sessions': 0, 'visits': 0, 'capacity': 0, 'revenue': 0.0, 'empty': 0})
                     for m in MONTHS}
                for lk in LOCATIONS}
    by_trainer_format = {lk: {m: defaultdict(lambda: defaultdict(lambda: {'sessions': 0, 'visits': 0, 'capacity': 0}))
                             for m in MONTHS}
                        for lk in LOCATIONS}
    # Recurring-slot view: one row per class name x day x time (the schedule
    # grid a studio actually manages), and the same split again by trainer.
    def _slot_bucket():
        return {'sessions': 0, 'visits': 0, 'capacity': 0, 'revenue': 0.0, 'empty': 0,
                'late': 0, 'comps': 0, 'booked': 0,
                'cls': '', 'day': '', 'time': '', 'trainer': '', 'fmt': '',
                'trainers': set()}
    by_slot = {lk: {m: defaultdict(_slot_bucket) for m in MONTHS} for lk in LOCATIONS}
    by_slot_trainer = {lk: {m: defaultdict(_slot_bucket) for m in MONTHS} for lk in LOCATIONS}

    heatmap = {lk: {m: defaultdict(lambda: defaultdict(lambda: {
                        'visits': 0, 'capacity': 0, 'sessions': 0,
                        'formats': defaultdict(int), 'trainers': defaultdict(int),
                    }))
                   for m in MONTHS}
              for lk in LOCATIONS}

    path, sch = sessions_source()
    if not path:
        print('  ! no usable sessions export (need a Location and a Date column)')
        return (data, by_class, by_trainer, by_format, heatmap, by_trainer_format,
                by_slot, by_slot_trainer)

    # (loc_key, month, session id) -> one class
    sessions = {}

    with open(path, encoding='utf-8-sig') as f:
        r = csv.DictReader(f, delimiter=sniff_delimiter(path))
        for row in r:
            loc_key = loc_key_for(row.get(sch['location'], '') or '')
            if not loc_key:
                continue
            d = row.get(sch['date'], '') or ''
            month = month_key(d)
            if month not in MONTHS:
                continue

            raw_sid = (row.get(sch['sid'], '') or '').strip() if sch['sid'] else ''
            cls = (row.get(sch['cls'], '') if sch['cls'] else '') or 'Unknown Class'
            trainer = (row.get(sch['trainer'], '') if sch['trainer'] else '') or 'Unknown'
            time_slot = (row.get(sch['time'], '') if sch['time'] else '') or 'Unknown'
            day = (row.get(sch['day'], '') if sch['day'] else '') or 'Unknown'
            host = (row.get(sch['host'], '') if sch['host'] else '') or ''
            sid = raw_sid or '|'.join([d, time_slot, cls, trainer, host])

            key = (loc_key, month, sid)
            rec = sessions.get(key)
            if rec is None:
                rec = sessions[key] = {
                    'visits': 0, 'capacity': 0, 'revenue': 0.0,
                    'late': 0, 'comps': 0, 'booked': 0,
                    'cls': cls, 'trainer': trainer, 'day': day,
                    'time': time_slot, 'fmt': classify_format(cls),
                }

            # Late cancels / comps / bookings: the legacy export carries one
            # row per class with a count, the roster export one row per
            # attendee with a flag — count flags, take counts once.
            for field in ('late', 'comps', 'booked'):
                col = sch.get(field)
                if not col:
                    continue
                raw = (row.get(col, '') or '').strip()
                if _truthy(raw):
                    rec[field] += 1
                elif raw:
                    n = to_int(raw)
                    if n > rec[field]:
                        rec[field] = n

            # Visits: the roster export flags each attendee (TRUE/FALSE); the
            # legacy export already gives a per-class headcount.
            raw_visits = (row.get(sch['visits'], '') if sch['visits'] else '') or ''
            if _truthy(raw_visits):
                rec['visits'] += 1
            else:
                n = to_int(raw_visits)
                if n and not _truthy(raw_visits):
                    rec['visits'] += n

            # Capacity repeats on every row of a class — take it once.
            if sch['capacity']:
                cap = to_int(row.get(sch['capacity'], '0'))
                if cap > rec['capacity']:
                    rec['capacity'] = cap

            if sch['revenue']:
                rec['revenue'] += to_float(row.get(sch['revenue'], '0'))

    for (loc_key, month, _sid), rec in sessions.items():
        dm = data[loc_key].setdefault(
            month, {'sessions': 0, 'visits': 0, 'capacity': 0, 'revenue': 0.0, 'empty': 0})
        dm['sessions'] += 1
        dm['visits'] += rec['visits']
        dm['capacity'] += rec['capacity']
        dm['revenue'] += rec['revenue']
        if rec['visits'] == 0:
            dm['empty'] += 1

        bc = by_class[loc_key][month][rec['cls']]
        bc['sessions'] += 1
        bc['visits'] += rec['visits']
        bc['capacity'] += rec['capacity']
        bc['revenue'] += rec['revenue']
        if rec['visits'] == 0:
            bc['empty'] += 1

        bt = by_trainer[loc_key][month][rec['trainer']]
        bt['sessions'] += 1
        bt['visits'] += rec['visits']
        bt['capacity'] += rec['capacity']
        bt['revenue'] += rec['revenue']
        bt['classes'].add(rec['cls'])
        bt['days'].add(rec['day'])
        if rec['visits'] == 0:
            bt['empty'] += 1

        bf = by_format[loc_key][month][rec['fmt']]
        bf['sessions'] += 1
        bf['visits'] += rec['visits']
        bf['capacity'] += rec['capacity']
        bf['revenue'] += rec['revenue']
        if rec['visits'] == 0:
            bf['empty'] += 1

        btf = by_trainer_format[loc_key][month][rec['trainer']][rec['fmt']]
        btf['sessions'] += 1
        btf['visits'] += rec['visits']
        btf['capacity'] += rec['capacity']

        slot_time = (rec['time'] or 'Unknown')[:5]
        for target, skey in ((by_slot, (rec['cls'], rec['day'], slot_time)),
                             (by_slot_trainer, (rec['cls'], rec['day'], slot_time, rec['trainer']))):
            b = target[loc_key][month]['|'.join(skey)]
            b['sessions'] += 1
            b['visits'] += rec['visits']
            b['capacity'] += rec['capacity']
            b['revenue'] += rec['revenue']
            b['late'] += rec['late']
            b['comps'] += rec['comps']
            b['booked'] += rec['booked']
            if rec['visits'] == 0:
                b['empty'] += 1
            b['cls'], b['day'], b['time'] = rec['cls'], rec['day'], slot_time
            b['fmt'] = rec['fmt']
            b['trainer'] = rec['trainer'] if len(skey) == 4 else ''
            b['trainers'].add(rec['trainer'])

        slot = rec['time'][:5] if rec['time'] else 'Unknown'
        hm = heatmap[loc_key][month][slot][rec['day']]
        hm['visits'] += rec['visits']
        hm['capacity'] += rec['capacity']
        hm['sessions'] += 1
        hm['formats'][rec['fmt']] += 1
        hm['trainers'][rec['trainer']] += 1

    for loc_key in LOCATIONS:
        for month in MONTHS:
            if month in data[loc_key]:
                dm = data[loc_key][month]
                dm['fill'] = dm['visits'] / dm['capacity'] * 100 if dm['capacity'] else 0
                dm['avg_visits'] = dm['visits'] / dm['sessions'] if dm['sessions'] else 0

    return (data, by_class, by_trainer, by_format, heatmap, by_trainer_format,
            by_slot, by_slot_trainer)



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
                data[loc_key][month] = {'trials': 0, 'retained': 0, 'converted': 0}

            data[loc_key][month]['trials'] += 1
            rs = row.get('Retention Status', '')
            if rs == 'Retained':
                data[loc_key][month]['retained'] += 1

            cs = row.get('Conversion Status', '')
            if cs == 'Converted':
                data[loc_key][month]['converted'] += 1

            by_type[loc_key][month][is_new] += 1

    # Conversion rate: trials that converted, per new.csv's own Conversion Status
    for loc_key in LOCATIONS:
        for month in MONTHS:
            if month in data[loc_key]:
                d = data[loc_key][month]
                d['rate'] = d['converted'] / d['trials'] * 100 if d['trials'] else 0

    return data, by_type


# ===================== LAPSED =====================
# Membership names matching any of these (case-insensitive substring) are
# zero/trial-type products and are excluded from lapsed evaluation, e.g.
# 'Studio Single Class', 'Newcomers 2 For 1', 'New Client Intro Pack',
# 'Pop-up Studio Single Class'.
# Products that are not real renewable memberships: trials, single visits,
# promo bundles and one-off private formats. Zero-value rows (comps, staff,
# corrections) are excluded as well.
LAPSED_EXCLUDE_PATTERNS = [
    'single class', '2 for 1', '2for1', 'intro pack', 'intro offer', 'intro',
    'virtual private', 'happy hour private', 'happy hour', 'trial',
    'complimentary', 'comp ', 'staff', 'newcomer', 'open barre',
]

# A membership only counts as lapsed once it is 60+ days past its end date —
# before that the member is still inside the normal renewal window.
LAPSED_MIN_DAYS_PAST_END = 60


def is_excluded_lapsed_membership(product_name, amount_paid):
    """True if this membership should be excluded from lapsed metrics:
    zero-value memberships (comps/freebies) or non-renewable products."""
    if to_float(amount_paid) <= 0:
        return True
    name = (product_name or '').lower()
    return any(p in name for p in LAPSED_EXCLUDE_PATTERNS)


def _parse_date(v):
    """Parse the handful of date shapes the exports use; None when unusable."""
    raw = (v or '').strip()
    if not raw:
        return None
    raw = raw.split(' ')[0]
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%d %b %Y', '%Y/%m/%d'):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def days_past_end(end_date_str, reference=None):
    """Days between a membership end date and the reference date (today)."""
    d = _parse_date(end_date_str)
    if not d:
        return None
    ref = reference or datetime.now()
    return (ref - d).days


def analyze_lapsed():
    """Analyze expiring memberships: who was up for renewal, who renewed, who
    lapsed, and the member-level rows behind every number.

    Excludes zero-value rows and non-renewable products (see
    LAPSED_EXCLUDE_PATTERNS). A membership counts as lapsed only when its
    status says Lapsed *and* it is at least LAPSED_MIN_DAYS_PAST_END days past
    its end date; anything newer is still inside the renewal window and is
    reported as pending instead.
    """
    data = {lk: {} for lk in LOCATIONS}
    by_product = {lk: {m: defaultdict(lambda: {'total': 0, 'renewed': 0, 'lapsed': 0,
                                               'frozen': 0, 'pending': 0, 'value': 0.0})
                      for m in MONTHS}
                 for lk in LOCATIONS}
    # Member-level rows, so the section can drill from any number to the people.
    members = {lk: {m: [] for m in MONTHS} for lk in LOCATIONS}
    cumulative = {lk: defaultdict(set) for lk in LOCATIONS}
    today = datetime.now()

    with open(LAPSED_FILE, encoding='utf-8-sig') as f:
        r = csv.DictReader(f, delimiter=sniff_delimiter(LAPSED_FILE))
        for row in r:
            loc_key = loc_key_for(row.get('Primary Location', ''))
            if not loc_key:
                continue
            ed = row.get('End Date', '')
            month = month_key(ed)
            if month not in MONTHS:
                continue

            product = row.get('Membership Name', '') or 'Unknown'
            paid = to_float(row.get('Amount Paid', '0'))
            if is_excluded_lapsed_membership(product, paid):
                continue

            raw_status = (row.get('Status', '') or '').strip()
            past = days_past_end(ed, today)
            status = raw_status
            if raw_status == 'Lapsed' and past is not None and past < LAPSED_MIN_DAYS_PAST_END:
                # Ended recently — still inside the renewal window.
                status = 'Pending'

            d = data[loc_key].setdefault(
                month, {'total': 0, 'renewed': 0, 'lapsed': 0, 'frozen': 0,
                        'pending': 0, 'value': 0.0, 'lapsed_value': 0.0,
                        'renewed_value': 0.0})
            bp = by_product[loc_key][month][product]
            key = {'Renewed': 'renewed', 'Lapsed': 'lapsed',
                   'Frozen': 'frozen', 'Pending': 'pending'}.get(status)
            for bucket in (d, bp):
                bucket['total'] += 1
                bucket['value'] += paid
                if key:
                    bucket[key] += 1
            if key == 'lapsed':
                d['lapsed_value'] += paid
            elif key == 'renewed':
                d['renewed_value'] += paid

            members[loc_key][month].append({
                'name': row.get('Member Name', '') or 'Unknown',
                'id': row.get('Member ID', ''),
                'email': row.get('Member Email', ''),
                'product': product,
                'status': status,
                'raw_status': raw_status,
                'paid': round(paid, 2),
                'end': ed,
                'start': row.get('Start Date', ''),
                'days_past_end': past,
                'sessions_used': to_int(row.get('Total Sessions Completed', '0')),
                'remaining': to_int(row.get('Remaining Sessions', '0')),
                'last_visit': row.get('Most Recent Visit Date', ''),
                'days_since_visit': to_int(row.get('Days Since Last Visit', '0')),
                'late_cancels': to_int(row.get('Late Cancellations', '0')),
                'no_shows': to_int(row.get('No Shows', '0')),
                'attendance': to_float(row.get('Attendance Rate %', '0')),
                'duration_days': to_int(row.get('Membership Duration (Days)', '0')),
                'sold_by': row.get('Sold By', ''),
            })

            if key == 'lapsed':
                cumulative[loc_key][month].add(row.get('Member ID', ''))

    for loc_key in LOCATIONS:
        for month in MONTHS:
            if month in data[loc_key]:
                d = data[loc_key][month]
                decided = d['renewed'] + d['lapsed']
                d['churn'] = d['lapsed'] / d['total'] * 100 if d['total'] else 0
                d['renewal_rate'] = d['renewed'] / d['total'] * 100 if d['total'] else 0
                # Renewal rate among memberships whose outcome is already known.
                d['decided'] = decided
                d['decided_renewal_rate'] = d['renewed'] / decided * 100 if decided else 0
                d['avg_value'] = d['value'] / d['total'] if d['total'] else 0
            members[loc_key][month].sort(key=lambda m: (-m['paid'], m['name']))

    cum_data = {lk: {} for lk in LOCATIONS}
    for loc_key in LOCATIONS:
        running = set()
        for month in MONTHS:
            running.update(cumulative[loc_key][month])
            cum_data[loc_key][month] = len(running)

    return data, by_product, cum_data, members


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


def _serialise_bucket(b):
    """Sets don't survive JSON, and the report only ever needs their size, so
    the sale and transaction sets are written out as counts."""
    out = {k: v for k, v in b.items() if k not in ('sales', 'txns')}
    out['sales'] = len(b.get('sales') or ())
    out['txns'] = len(b.get('txns') or ()) or out['sales']
    return out


def _serialise_slot(v):
    """Slot buckets carry a set of trainers; JSON wants a sorted list."""
    out = {k: val for k, val in v.items() if not isinstance(val, set)}
    trainers = sorted(v.get('trainers') or ())
    out['trainers'] = trainers
    out['trainer_count'] = len(trainers)
    out['fill'] = v['visits'] / v['capacity'] * 100 if v.get('capacity') else 0
    out['avg'] = v['visits'] / v['sessions'] if v.get('sessions') else 0
    return out


def _serialise_trainer(v):
    """Sets are collected while counting but cannot go into JSON — the report
    only ever wants how many distinct classes and days a trainer covered."""
    out = {k: val for k, val in v.items() if not isinstance(val, set)}
    out['distinct_classes'] = len(v.get('classes') or ())
    out['distinct_days'] = len(v.get('days') or ())
    return out


def _serialise_breakdowns(bts):
    out = {}
    for btype, bd in bts.items():
        if btype == 'category_product':
            out[btype] = {cat: {prod: _serialise_bucket(v) for prod, v in prods.items()}
                          for cat, prods in bd.items()}
        else:
            out[btype] = {k: _serialise_bucket(v) for k, v in bd.items()}
    return out


# ===================== MAIN =====================
def main():
    print("Analyzing sales...")
    sales_data, sales_breakdowns, sales_by_id = analyze_sales()
    
    print("Analyzing sessions...")
    (sessions_data, sessions_by_class, sessions_by_trainer, sessions_by_format,
     heatmap_data, sessions_by_trainer_format,
     sessions_by_slot, sessions_by_slot_trainer) = analyze_sessions()
    
    print("Analyzing leads...")
    leads_data, leads_by_source = analyze_leads()
    
    print("Analyzing trials...")
    new_data, new_by_type = analyze_new()
    
    print("Analyzing lapsed...")
    lapsed_data, lapsed_by_product, lapsed_cumulative, lapsed_members = analyze_lapsed()
    
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

        # New/trials baseline (conversion + retention rates off the New sheet itself)
        bl_new = {'trials': 0, 'retained': 0, 'converted': 0, 'count': 0}
        for m in bl_months:
            if m in new_data[loc_key]:
                n = new_data[loc_key][m]
                bl_new['trials'] += n['trials']
                bl_new['retained'] += n['retained']
                bl_new['converted'] += n['converted']
                bl_new['count'] += 1
        if bl_new['count']:
            bl_new['trials'] /= bl_new['count']
            bl_new['retained'] /= bl_new['count']
            bl_new['converted'] /= bl_new['count']
            bl_new['rate'] = bl_new['converted'] / bl_new['trials'] * 100 if bl_new['trials'] else 0
            bl_new['retention_rate'] = bl_new['retained'] / bl_new['trials'] * 100 if bl_new['trials'] else 0
        baseline[loc_key]['new'] = bl_new

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
        'sales_breakdowns': {lk: {m: _serialise_breakdowns(bts)
                                   for m, bts in months.items()}
                            for lk, months in sales_breakdowns.items()},
        'sales_by_id': {lk: {m: dict(sids) for m, sids in months.items()}
                       for lk, months in sales_by_id.items()},
        'sessions': sessions_data,
        'sessions_by_class': {lk: {m: dict(bc) for m, bc in months.items()}
                             for lk, months in sessions_by_class.items()},
        'sessions_by_slot': {lk: {m: {k: _serialise_slot(v) for k, v in slots.items()}
                                  for m, slots in months.items()}
                            for lk, months in sessions_by_slot.items()},
        'sessions_by_slot_trainer': {lk: {m: {k: _serialise_slot(v) for k, v in slots.items()}
                                          for m, slots in months.items()}
                                    for lk, months in sessions_by_slot_trainer.items()},
        'sessions_by_trainer': {lk: {m: {name: _serialise_trainer(v) for name, v in bt.items()}
                                     for m, bt in months.items()}
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
        'lapsed_members': lapsed_members,
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
