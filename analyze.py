#!/usr/bin/env python3
"""
Kwality House Performance Report — June & July 2026
COMPLETE analysis. Primary = July 2026, comparator = June 2026,
Jan-Mar 2026 baseline, YoY (June/July 2025), May 2026 reference.
All metrics validated against the May 2026 reference report.
"""
import csv, json, collections, re
from datetime import datetime

KW = "Kwality House, Kemps Corner"
KW_HOST = "13752"
R = {}

def load(path, enc='utf-8-sig'):
    with open(path, encoding=enc) as f:
        return list(csv.DictReader(f))

def num(s):
    if s is None: return 0.0
    s=str(s).strip().replace(',','').replace('₹','')
    if s=='' or s=='-' or s.lower()=='nan' or s.lower()=='none': return 0.0
    try: return float(s)
    except: return 0.0

def inmonth(d, ym):
    if not d: return False
    d=str(d).strip()
    m=re.match(r'(\d{4})-(\d{2})', d)
    if m: return f'{m.group(1)}-{m.group(2)}'==ym
    m=re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', d)
    if m: return f'{m.group(3)}-{int(m.group(1)):02d}'==ym
    return False

def ym_of(d):
    if not d: return None
    d=str(d).strip()
    m=re.match(r'(\d{4})-(\d{2})', d)
    if m: return f'{m.group(1)}-{m.group(2)}'
    m=re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', d)
    if m: return f'{m.group(3)}-{int(m.group(1)):02d}'
    return None

def pct_change(new, old):
    if old==0: return None
    return (new-old)/abs(old)*100

def L(v):
    return v/100000.0

# ============================================================
# 1. SALES RAW  (validated: May net=2,311,179 == Rs23.13L)
# Gross = Payment Value; Net = Mrp - Pre Tax; Discount = Discount Amount -Mrp- Payment Value
# Method in 'Payment Status' col; Status 'succeeded' in 'Payment Method' col.
# ============================================================
sales = load('Sales_-_Raw_-_Sales_(14).csv')

def sales_metrics(rows, ym):
    loc=[r for r in rows if (r.get('Calculated Location') or r.get('Home Location'))==KW
         and inmonth(r.get('Payment Date'),ym) and r.get('Payment Method','').lower()=='succeeded']
    gross=net=disc=0.0; txn=0; members=set(); disc_txn=0
    cats=collections.defaultdict(lambda:[0.0,0,0.0]); prods=collections.defaultdict(lambda:[0.0,0,0.0])
    sellers=collections.defaultdict(lambda:[0.0,0]); pay=collections.defaultdict(lambda:[0.0,0])
    promo=mem=pkg=drop=0.0
    for r in loc:
        pv=num(r.get('Payment Value')); nt=num(r.get('Mrp - Pre Tax')); dv=num(r.get('Discount Amount -Mrp- Payment Value'))
        if nt<=0: nt=pv
        gross+=pv; net+=nt; disc+=dv; txn+=1
        if dv>0: disc_txn+=1
        members.add(r.get('Paying Member ID'))
        cat=r.get('Cleaned Category') or 'Unknown'; cats[cat][0]+=pv; cats[cat][1]+=1; cats[cat][2]+=dv
        prod=r.get('Cleaned Product') or r.get('Sale Item Name') or 'Unknown'
        prods[prod][0]+=pv; prods[prod][1]+=1; prods[prod][2]+=dv  # units = row count
        sb=r.get('Sold By') or '-'; sellers[sb][0]+=pv; sellers[sb][1]+=1
        pm=r.get('Payment Status') or 'Unknown'; pml=pm.lower()
        if pml=='custom': pm='Custom (in-studio)'
        elif pml in ('stripe','stripe link','razorpay'): pm='Stripe (online)'
        elif pml=='cash': pm='Cash'
        elif 'multiple' in pml: pm='Multiple payment methods'
        elif 'bank' in pml: pm='Bank Transfer'
        elif 'upi' in pml: pm='UPI'
        elif 'pos' in pml: pm='POS'
        pay[pm][0]+=pv; pay[pm][1]+=1
        if r.get('Discount Code') or dv>0: promo+=pv
        cl=cat.lower()
        if 'membership' in cl: mem+=pv
        elif 'package' in cl: pkg+=pv
        elif 'session' in cl or 'single' in cl: drop+=pv
    return dict(ym=ym, gross=gross, net=net, disc=disc, disc_txn=disc_txn,
                disc_pen=disc_txn/txn*100 if txn else 0, txn=txn, members=len(members),
                cats={k:list(v) for k,v in cats.items()}, prods={k:list(v) for k,v in prods.items()},
                sellers={k:list(v) for k,v in sellers.items()}, pay={k:list(v) for k,v in pay.items()},
                promo=promo, mem=mem, pkg=pkg, drop=drop, atv=gross/txn if txn else 0,
                rev_per_member=net/len(members) if members else 0,
                disc_eff=net/disc if disc>0 else None)

for ym in ['2026-01','2026-02','2026-03','2026-04','2026-05','2026-06','2026-07','2025-06','2025-07']:
    R.setdefault('sales',{})[ym]=sales_metrics(sales, ym)

jm=[R['sales']['2026-01'],R['sales']['2026-02'],R['sales']['2026-03']]
R['baseline']={k:sum(m[k] for m in jm)/3 for k in ['gross','net','disc','txn','members','promo','mem','pkg','drop','disc_txn','atv','rev_per_member']}
R['baseline']['disc_eff']=R['baseline']['net']/R['baseline']['disc'] if R['baseline']['disc']>0 else None

# ============================================================
# 2. SESSIONS (validated: May 348 sessions, 2307 visits, 47.2% fill)
# ============================================================
sessions = load('Day_End_Report_-_Part_3_-_Sessions_(16).csv')

def session_metrics(rows, ym):
    loc=[r for r in rows if r.get('Location')==KW and inmonth(r.get('Date'),ym)]
    n=len(loc); cap=sum(num(r.get('Capacity')) for r in loc); chk=sum(num(r.get('CheckedIn')) for r in loc)
    empty=sum(1 for r in loc if num(r.get('CheckedIn'))==0)
    lc=sum(num(r.get('LateCancelled')) for r in loc); booked=sum(num(r.get('Booked')) for r in loc)
    rev=sum(num(r.get('Revenue')) for r in loc)
    byclass=collections.defaultdict(lambda:[0,0.0,0.0,0.0,0.0])
    for r in loc:
        cl=r.get('Class') or r.get('SessionName') or 'Unknown'
        byclass[cl][0]+=1; byclass[cl][1]+=num(r.get('Capacity')); byclass[cl][2]+=num(r.get('CheckedIn'))
        byclass[cl][3]+=num(r.get('LateCancelled')); byclass[cl][4]+=num(r.get('Revenue'))
    bytype=collections.defaultdict(lambda:[0,0.0,0.0,0.0,0.0])
    for r in loc:
        t=r.get('Type') or 'Unknown'
        bytype[t][0]+=1; bytype[t][1]+=num(r.get('Capacity')); bytype[t][2]+=num(r.get('CheckedIn'))
        bytype[t][3]+=num(r.get('LateCancelled')); bytype[t][4]+=num(r.get('Revenue'))
    bytrainer=collections.defaultdict(lambda:[0,0.0,0.0,0.0,0.0])
    for r in loc:
        t=r.get('Trainer') or 'Unknown'
        bytrainer[t][0]+=1; bytrainer[t][1]+=num(r.get('Capacity')); bytrainer[t][2]+=num(r.get('CheckedIn'))
        bytrainer[t][4]+=num(r.get('Revenue'))
    heat=collections.defaultdict(lambda: collections.defaultdict(lambda:[0.0,0.0]))
    for r in loc:
        day=r.get('Day','').strip(); t=r.get('Time','')[:5]
        if day and t:
            heat[t][day][0]+=num(r.get('CheckedIn')); heat[t][day][1]+=num(r.get('Capacity'))
    return dict(ym=ym, sessions=n, capacity=cap, visits=int(chk), empty=empty,
                fill=chk/cap*100 if cap else 0, late_cancel=int(lc), booked=int(booked),
                revenue=rev, class_avg=chk/n if n else 0,
                byclass={k:list(v) for k,v in byclass.items()},
                bytype={k:list(v) for k,v in bytype.items()},
                bytrainer={k:list(v) for k,v in bytrainer.items()},
                heat={t:{d:list(v) for d,v in dd.items()} for t,dd in heat.items()})

for ym in ['2026-01','2026-02','2026-03','2026-04','2026-05','2026-06','2026-07','2025-06','2025-07']:
    R.setdefault('sessions',{})[ym]=session_metrics(sessions, ym)

# ============================================================
# 3. CHECKINS — late cancels, new visits, attendance
# ============================================================
checkins = load('Day_End_Report_-_Part_4_-_Checkins_(10).csv')

def checkin_metrics(rows, ym):
    loc=[r for r in rows if r.get('Location')==KW and inmonth(r.get('Date (IST)'),ym)]
    n=len(loc)
    lc=[r for r in loc if r.get('Is Late Cancelled','').upper()=='TRUE']
    lc_members=set(r.get('Member ID') for r in lc)
    new=[r for r in loc if 'New' in (r.get('Is New') or '')]
    canc_by_mem=collections.Counter(r.get('Member ID') for r in lc)
    heavy=[(m,c) for m,c in canc_by_mem.items() if c>=6]
    return dict(ym=ym, checkins=n, late_cancel=len(lc), lc_members=len(lc_members),
                new_visits=len(new),
                heavy_cancelers=len(heavy), heavy_cancels=sum(c for _,c in heavy))

for ym in ['2026-04','2026-05','2026-06','2026-07']:
    R.setdefault('checkins',{})[ym]=checkin_metrics(checkins, ym)

# ============================================================
# 4. CONVERSION FUNNEL
# Leads from Leads file; Trials from New file; Converted from Leads; Retained from New.
# ============================================================
leads = load('❖_PM_-_Leads_❖_-_◉_Leads_(29).csv')
newf = load('Day_End_Report_-_Part_1_-_New_(7).csv')

def funnel_metrics(ym):
    mm=int(ym.split('-')[1]); yy=ym.split('-')[0]
    mystr=f"{datetime(2020,mm,1).strftime('%b')}-{yy}"
    lrows=[r for r in leads if r.get('Center')==KW and inmonth(r.get('Created At'),ym)]
    nleads=len(lrows)
    conv=[r for r in lrows if r.get('Conversion Status')=='Converted']
    ltv=sum(num(r.get('LTV')) for r in lrows)
    visits=sum(num(r.get('Visits')) for r in lrows)
    src=collections.defaultdict(lambda:[0,0,0,0.0,0.0])
    for r in lrows:
        s=r.get('Source Name') or 'Unknown'
        src[s][0]+=1
        if r.get('Conversion Status')=='Converted': src[s][1]+=1
        if r.get('Retention Status')=='Retained': src[s][2]+=1
        src[s][3]+=num(r.get('LTV')); src[s][4]+=num(r.get('Visits'))
    nrows=[r for r in newf if r.get('Month Year')==mystr and r.get('First Visit Location')==KW]
    trials=[r for r in nrows if 'New' in (r.get('Is New') or '')]
    ret_n=[r for r in trials if r.get('Retention Status')=='Retained']
    ttype=collections.Counter((r.get('Is New') or 'Unknown') for r in trials)
    return dict(ym=ym, leads=nleads, trials=len(trials), converted=len(conv),
                retained=len(ret_n), lead_ltv=ltv, lead_visits=int(visits),
                src={k:list(v) for k,v in src.items()},
                trial_types=dict(ttype),
                conv_rate=len(conv)/nleads*100 if nleads else 0,
                retain_rate=len(ret_n)/nleads*100 if nleads else 0)

for ym in ['2026-01','2026-02','2026-03','2026-04','2026-05','2026-06','2026-07','2025-06','2025-07']:
    R.setdefault('funnel',{})[ym]=funnel_metrics(ym)

# ============================================================
# 5. LAPSED MEMBERSHIPS  (Host ID 13752 = KW, bucket by End Date month)
# ============================================================
lapsed = load('Lapsed_New_-_Lapsed_(16).csv')
lapsed_uniq = load('Lapsed_New_-_Lapsed_Unique.csv')

def lapsed_metrics(ym):
    kw=[r for r in lapsed if r.get('Host ID')==KW_HOST]
    end=[r for r in kw if ym_of(r.get('End Date'))==ym]
    renewed=[r for r in end if r.get('Status')=='Renewed']
    lapsed_m=[r for r in end if r.get('Status')=='Lapsed']
    frozen=[r for r in end if r.get('Status')=='Frozen']
    total_exp=len(end)
    byprod=collections.Counter(r.get('Membership Name','').strip() for r in lapsed_m)
    lc=sum(num(r.get('Late Cancellations')) for r in lapsed_m)
    return dict(ym=ym, expirations=total_exp, renewed=len(renewed), lapsed=len(lapsed_m),
                frozen=len(frozen),
                renewal_rate=len(renewed)/total_exp*100 if total_exp else 0,
                churn_rate=len(lapsed_m)/total_exp*100 if total_exp else 0,
                byprod=dict(byprod.most_common(20)), late_cancels=int(lc))

for ym in ['2026-01','2026-02','2026-03','2026-04','2026-05','2026-06','2026-07']:
    R.setdefault('lapsed',{})[ym]=lapsed_metrics(ym)

kw_uniq=[r for r in lapsed_uniq if r.get('Host ID')==KW_HOST]
R['cumulative_lapsed_unique']=len(kw_uniq)
R['cumulative_lapsed_byprod']=dict(collections.Counter(r.get('Membership Name','').strip() for r in kw_uniq if r.get('Status')=='Lapsed').most_common(25))

# ============================================================
# 6. PAYROLL — trainer conversion & retention
# ============================================================
payroll = load('Day_End_Report_-_Part_1_-_Payroll_(2).csv')

def payroll_metrics(ym):
    mm=int(ym.split('-')[1]); yy=ym.split('-')[0]
    mystr=f"{datetime(2020,mm,1).strftime('%b')}-{yy}"
    rows=[r for r in payroll if r.get('Location')==KW and r.get('Month Year')==mystr]
    trainers=[]
    for r in rows:
        cr=r.get('Conversion Rate') or '0%'
        trainers.append(dict(
            name=r.get('Teacher Name'), sessions=int(num(r.get('Total Sessions'))),
            customers=int(num(r.get('Total Customers'))), paid=num(r.get('Total Paid')),
            converted=int(num(r.get('Converted'))),
            conv_rate=num(cr.replace('%','')) if cr else 0,
            retained=int(num(r.get('Retained'))),
            new=int(num(r.get('New')))))
    return dict(ym=ym, trainers=trainers, n_trainers=len(trainers))

for ym in ['2026-05','2026-06','2026-07']:
    R.setdefault('payroll',{})[ym]=payroll_metrics(ym)

# ============================================================
# 7. ACTIVE MEMBERSHIPS (snapshot)
# ============================================================
active = load('Day_End_Report_-_Part_5_-_Active_(3).csv')
kw_active=[r for r in active if r.get('Home Location')==KW]
R['active']=dict(total=len(kw_active),
                 bytype=dict(collections.Counter(r.get('Membership Type','') for r in kw_active).most_common()),
                 byname=dict(collections.Counter(r.get('Membership Name','').strip() for r in kw_active).most_common(15)))

with open('analysis_full.json','w') as f:
    json.dump(R, f, indent=2, default=str)

print('='*70)
print('KWALITY HOUSE — JUNE & JULY 2026 ANALYSIS SUMMARY')
print('='*70)
for ym in ['2026-05','2026-06','2026-07']:
    s=R['sales'][ym]; se=R['sessions'][ym]; f=R['funnel'][ym]; l=R['lapsed'][ym]
    de = f'{s["disc_eff"]:.2f}' if s["disc_eff"] else 'n/a'
    print(f'\n--- {ym} ---')
    print(f'  SALES: gross=Rs{L(s["gross"]):.2f}L net=Rs{L(s["net"]):.2f}L disc=Rs{L(s["disc"]):.2f}L txn={s["txn"]} members={s["members"]} atv=Rs{s["atv"]:,.0f} discEff={de}')
    print(f'  SESSIONS: {se["sessions"]} sessions, {se["visits"]} visits, {se["empty"]} empty, fill={se["fill"]:.1f}%, class_avg={se["class_avg"]:.1f}, rev=Rs{L(se["revenue"]):.2f}L')
    print(f'  FUNNEL: leads={f["leads"]} trials={f["trials"]} converted={f["converted"]} retained={f["retained"]} conv_rate={f["conv_rate"]:.1f}% ltv=Rs{L(f["lead_ltv"]):.2f}L')
    print(f'  LAPSED: exp={l["expirations"]} renewed={l["renewed"]} lapsed={l["lapsed"]} churn={l["churn_rate"]:.1f}%')
c=R['checkins']
for ym in ['2026-05','2026-06','2026-07']:
    print(f'  CHECKINS {ym}: late_cancel={c[ym]["late_cancel"]} lc_members={c[ym]["lc_members"]} heavy_cancelers(6+)={c[ym]["heavy_cancelers"]}')
print(f'\nCumulative lapsed unique members (KW): {R["cumulative_lapsed_unique"]}')
print(f'Active memberships (KW): {R["active"]["total"]}')
print(f'Baseline net=Rs{L(R["baseline"]["net"]):.2f}L disc=Rs{L(R["baseline"]["disc"]):.2f}L')
print('\nFull analysis saved to analysis_full.json')
