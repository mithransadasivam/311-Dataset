import json, csv, os
from collections import defaultdict

GOOGLE_KEY = "AIzaSyCxMiaz9dcPviOvTGCi9jT1kZLW49Zg37w"
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, 'data')
OUT  = os.path.join(HERE, 'public', 'index.html')

# ── PROBLEM_DETAIL → unified UI type ─────────────────────────────
type_map = {
    'Street Light Out':'Street Light Out',
    'Street Light Lamp Missing':'Street Light Out',
    'Flood Light Lamp Out':'Street Light Out',
    'Flood Light Lamp Missing':'Street Light Out',
    'Fire Alarm Lamp Out':'Street Light Out',
    'Traffic Signal Light':'Street Light Out',
    'New Con Ed Service Request':'Street Light Out',

    'Multiple Street Lights Out':'Multiple Lights Out',

    'Street Light Cycling':'Street Light Cycling',
    'Flood Light Lamp Cycling':'Street Light Cycling',

    'Street Light Dayburning':'Street Light Dayburning',
    'Multiple St Lts Dayburning':'Street Light Dayburning',
    'Flood Light Lamp Dayburning':'Street Light Dayburning',
    'Time Clock Maladjusted':'Street Light Dayburning',

    'Street Light Lamp Dim':'Dim Lamp',
    'Flood Light Lamp Dim':'Dim Lamp',

    'Fixture/Luminaire Door Open':'Fixture/Glassware Issue',
    'Fixture/Luminaire Out Of Position':'Fixture/Glassware Issue',
    'Fixture/Luminaire Hanging':'Fixture/Glassware Issue',
    'Glassware Missing':'Fixture/Glassware Issue',
    'Glassware Hanging':'Fixture/Glassware Issue',
    'Glassware Broken':'Fixture/Glassware Issue',
    'Photocell (PEC) Missing':'Fixture/Glassware Issue',

    'Fixture/Luminaire Damaged':'Lamppost Damage',
    'Fixture/Luminaire Missing':'Lamppost Damage',
    'Lamppost Damaged':'Lamppost Damage',
    'Lamppost Leaning':'Lamppost Damage',
    'Lamppost Knocked Down':'Lamppost Damage',
    'Lamppost Wire Exposed':'Lamppost Damage',
    'Lamppost Missing':'Lamppost Damage',
    'Lamppost Base Door/Cover Open':'Lamppost Damage',
    'Lamppost Base Door/Cover Damaged':'Lamppost Damage',
    'Lamppost Base Door/Cover Missing':'Lamppost Damage',
    'Wood Pole Leaning':'Lamppost Damage',
    'Wood Pole Damaged':'Lamppost Damage',
    'Wood Pole Wires Exposed':'Lamppost Damage',
    'Bracket Arm Missing':'Lamppost Damage',
    'Bracket Arm Loose':'Lamppost Damage',
    'Bracket Arm Bent':'Lamppost Damage',
    'Foreign Attachment On Lamppost':'Lamppost Damage',
    'Foreign Attachment On Wood Pole':'Lamppost Damage',
    'In-Line Fuse Missing':'Lamppost Damage',
    'Control Panel Damaged':'Lamppost Damage',
}
priority_map = {
    'Street Light Out':'High','Multiple Lights Out':'High','Lamppost Damage':'High',
    'Street Light Cycling':'Medium','Dim Lamp':'Medium','Fixture/Glassware Issue':'Medium',
    'Street Light Dayburning':'Low',
}

BOROUGH_NORM = {
    'STATEN ISLAND':'Staten Island','MANHATTAN':'Manhattan','BRONX':'Bronx',
    'BROOKLYN':'Brooklyn','QUEENS':'Queens',
}
BOROUGH_FILES = [
    ('Staten Island','Staten_Island.csv'),('Manhattan','Manhattan.csv'),
    ('Bronx','Bronx.csv'),('Brooklyn','Brooklyn.csv'),('Queens','Queens.csv'),
]

# ── Load all 5 borough 311 CSVs ─────────────────────────────────
rows = []
for borough, fn in BOROUGH_FILES:
    with open(os.path.join(BASE, fn), encoding='utf-8') as f:
        for r in csv.DictReader(f):
            ct = type_map.get(r['PROBLEM_DETAIL'].strip(), 'Street Light Out')
            raw_status = r['STATUS'].strip()
            if raw_status == 'Closed': st = 'Closed'
            elif raw_status == 'Pending': st = 'Pending'
            else: st = 'Open'
            res = None
            if r['DAYS_TO_CLOSE'].strip() and st == 'Closed':
                try:
                    d = int(float(r['DAYS_TO_CLOSE']))
                    res = max(1, d) if d >= 0 else None
                except: pass
            addr, street = r['INCIDENT_ADDRESS'].strip(), r['STREET_NAME'].strip()
            try:   lat = round(float(r['LATITUDE']),  6) if r['LATITUDE'].strip()  else None
            except: lat = None
            try:   lng = round(float(r['LONGITUDE']), 6) if r['LONGITUDE'].strip() else None
            except: lng = None
            if lat is None or lng is None: continue
            rows.append({
                'id': r['UNIQUE_KEY'].strip(), 'date': r['CREATED_DATE'].strip()[:10],
                'type': ct,
                'raw_type': r['PROBLEM_DETAIL'].strip(),  # original PROBLEM_DETAIL for work-order generator
                'status': st, 'resolution': res,
                'address': addr if addr else ('Intersection, ' + street if street else 'Unknown'),
                'street': street if street else 'Unknown',
                'zip': r['INCIDENT_ZIP'].strip(),
                'borough': borough,
                'priority': priority_map.get(ct, 'Medium'),
                'lat': lat, 'lng': lng,
            })

print(f'Loaded {len(rows)} 311 records across {len(BOROUGH_FILES)} boroughs.')

# ── Per-borough ZIP list (sorted, distinct) ─────────────────────
borough_zips = defaultdict(set)
for r in rows:
    if r['zip']:
        borough_zips[r['borough']].add(r['zip'])
borough_zips_map = {b: sorted(zs) for b, zs in borough_zips.items()}

# ── Load vendors (NYC-wide) ─────────────────────────────────────
# The source list is NYC DOB's master electrician license roster, which
# includes institutions holding a license only for in-house maintenance
# (universities, hospitals, city agencies, NYCHA, building management cos.).
# None of these would bid on a 311 street-light repair — filter them out.
import re as _re
NON_CONTRACTOR_PATTERNS = _re.compile(
    # Partial tokens (no trailing \b so UNIVERSITY/HOSPITALS/DEPT./TRANSP.
    # still match) plus full-word tokens where a boundary is safe.
    r'(?:\b(?:UNIVERSIT|UNIV\b|COLLEGE|SCHOOL|ACADEM|HOSPITAL|MEDICAL CENTER|MEDICAL CTR|'
    r'MED CTR|MED\.? CENTER|CLINIC|CHURCH|SYNAGOGUE|MOSQUE|TEMPLE|'
    r'CONDOMINIUM|COOPERATIVE|CO-OP|HOUSING|AUTHORITY|AGENC|'
    r'\bDEPT\b|\bDEPT\.|DEPARTMENT|HOTEL|RESORT|MUSEUM|GALLER|LIBRAR|'
    r'PROPERTIES|REALTY|REAL ESTATE|MANAGEMENT|TRANSIT|AIRPORT|PORT AUTHORITY|'
    r'SUPERMARKET|RESTAURANT|\bBANK\b|RESEARCH|FOUNDATION|INSTITUTE|THEATER|THEATRE|'
    r'POLICE|SANIT|TRANSP))',
    _re.IGNORECASE,
)
vendor_rows = []
_filtered_institutions = []
with open(os.path.join(BASE, 'vendors_final.csv'), encoding='utf-8') as f:
    for v in csv.DictReader(f):
        name = v['business_name'].strip()
        if NON_CONTRACTOR_PATTERNS.search(name):
            _filtered_institutions.append(name)
            continue
        try:
            vlat = round(float(v['lat']),  6) if v['lat'].strip()  else None
            vlng = round(float(v['long']), 6) if v['long'].strip() else None
        except: vlat, vlng = None, None
        b = v['borough'].strip()
        if b not in BOROUGH_FILES[0][0:1] and b not in [x[0] for x in BOROUGH_FILES]: continue
        phone = v['phone'].strip()
        # format phone as (xxx) xxx-xxxx if 10 digits
        if phone and phone.isdigit() and len(phone) == 10:
            phone = f'({phone[:3]}) {phone[3:6]}-{phone[6:]}'
        vendor_rows.append({
            'name': v['business_name'].strip().title(),
            'phone': phone,
            'email': v['email'].strip().lower(),
            'address': v['address'].strip().title() + ', ' + v['city'].strip().title().rstrip(',') + ', NY ' + v['zip'].strip(),
            'zip': v['zip'].strip(),
            'borough': b,
            'license': v['license_number'].strip(),
            'lat': vlat, 'lng': vlng,
        })

print(f'Loaded {len(vendor_rows)} vendors (filtered out {len(_filtered_institutions)} non-contractor institutions).')
if _filtered_institutions:
    print('  Excluded:', ', '.join(sorted(set(_filtered_institutions))))

raw = json.dumps(rows, separators=(',', ':'))
vendors_js = json.dumps(vendor_rows, separators=(',', ':'))
borough_zips_js = json.dumps(borough_zips_map, separators=(',', ':'))

# ── Full HTML ─────────────────────────────────────────────────────
html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>311 Street Lamp Complaint &#8212; NYC</title>
<script src="https://maps.googleapis.com/maps/api/js?key=__GOOGLE_KEY__&libraries=places&callback=onGoogleMapsLoaded" async defer></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background:#0f1923;color:#e0e0e0;min-height:100vh;}}
.header{{background:linear-gradient(135deg,#1a2a3a 0%,#0d1b2a 100%);padding:22px 40px;border-bottom:3px solid #00b4d8;display:flex;align-items:center;justify-content:space-between;}}
.header h1{{font-size:1.5rem;color:#00b4d8;}}.header .sub{{font-size:0.82rem;color:#8899aa;margin-top:4px;}}
.badge{{background:#00b4d8;color:#0f1923;padding:5px 14px;border-radius:20px;font-weight:700;font-size:0.75rem;}}
.page{{max-width:880px;margin:0 auto;padding:36px 24px 60px;}}
.about-section{{background:linear-gradient(180deg,#16253a 0%,#0f1923 100%);border:1px solid #1f3350;border-radius:18px;padding:40px 42px 32px;margin-bottom:28px;position:relative;overflow:hidden;}}
.about-section::before{{content:"";position:absolute;top:-40%;right:-10%;width:280px;height:280px;background:radial-gradient(circle,rgba(0,180,216,.18) 0%,transparent 70%);pointer-events:none;}}
.about-hero h2{{font-size:1.7rem;color:#ffffff;margin-bottom:18px;font-weight:700;line-height:1.25;position:relative;z-index:1;}}
.about-hero h2 .accent{{color:#00b4d8;}}
.about-intro{{font-size:0.95rem;color:#c8d8e8;line-height:1.72;margin-bottom:28px;position:relative;z-index:1;}}
.about-intro strong{{color:#ffffff;font-weight:700;}}
.about-intro .hl-teal{{color:#00b4d8;font-weight:700;}}
.about-intro .hl-red{{color:#ff6b76;font-weight:700;}}
.about-callout{{display:flex;align-items:center;gap:24px;background:rgba(230,57,70,.08);border:1px solid rgba(230,57,70,.35);border-radius:14px;padding:22px 28px;margin:10px 0 30px;position:relative;z-index:1;}}
.callout-big{{font-size:3.2rem;font-weight:800;color:#ff6b76;line-height:1;flex-shrink:0;letter-spacing:-.02em;}}
.callout-text{{flex:1;}}
.callout-text .callout-main{{font-size:0.98rem;color:#ffffff;font-weight:600;margin-bottom:4px;}}
.callout-text .callout-sub{{font-size:0.78rem;color:#8899aa;line-height:1.5;}}
.about-graphics{{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:20px;margin-top:8px;position:relative;z-index:1;}}
.about-graphic{{background:#0d1b2a;border:1px solid #223344;border-radius:12px;padding:16px;display:flex;flex-direction:column;}}
.about-graphic img{{width:100%;height:auto;border-radius:8px;background:#f4f4f4;padding:8px;}}
.about-graphic figcaption{{font-size:0.8rem;color:#8899aa;margin-top:10px;line-height:1.5;text-align:center;}}
.about-disclaimer{{font-size:0.7rem;color:#667788;margin-top:10px;line-height:1.5;font-style:italic;padding:8px 10px;background:rgba(136,153,170,.06);border-left:2px solid #334455;border-radius:4px;}}
.about-disclaimer a{{color:#00b4d8;text-decoration:none;}}
.about-disclaimer a:hover{{text-decoration:underline;}}
.about-cta{{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-top:28px;padding-top:22px;border-top:1px solid #223344;position:relative;z-index:1;flex-wrap:wrap;}}
.about-cta-primary{{background:#00b4d8;color:#0f1923;border:none;padding:12px 26px;border-radius:10px;font-weight:700;font-size:0.9rem;cursor:pointer;transition:all .2s;}}
.about-cta-primary:hover{{background:#48bfe3;transform:translateY(-1px);}}
.about-cta-link{{color:#8899aa;font-size:0.82rem;text-decoration:none;transition:color .2s;}}
.about-cta-link:hover{{color:#00b4d8;}}
@media (max-width:640px){{
  .about-section{{padding:28px 22px;}}
  .about-callout{{flex-direction:column;text-align:center;gap:12px;padding:20px;}}
  .callout-big{{font-size:2.6rem;}}
  .about-hero h2{{font-size:1.4rem;}}
}}
.step-card{{background:#1a2a3a;border:1px solid #223344;border-radius:14px;padding:28px 32px;margin-bottom:20px;transition:border-color .3s,opacity .3s;}}
.step-card.locked{{opacity:.38;pointer-events:none;}}.step-card.active{{border-color:#00b4d8;}}
.step-header{{display:flex;align-items:center;gap:14px;margin-bottom:22px;}}
.step-num{{width:32px;height:32px;border-radius:50%;background:#00b4d8;color:#0f1923;font-weight:800;font-size:0.9rem;display:flex;align-items:center;justify-content:center;flex-shrink:0;}}
.step-card.locked .step-num{{background:#334455;color:#8899aa;}}
.step-title{{font-size:1rem;font-weight:600;color:#e0e0e0;}}.step-hint{{font-size:0.78rem;color:#8899aa;margin-top:2px;}}
.zip-select{{width:100%;background:#0d1b2a;border:1.5px solid #334455;color:#e0e0e0;padding:13px 16px;border-radius:10px;font-size:0.95rem;font-family:inherit;cursor:pointer;transition:border-color .2s;}}
.zip-select:focus{{outline:none;border-color:#00b4d8;}}.zip-select option{{background:#0d1b2a;}}
.addr-row{{display:flex;gap:10px;margin-top:16px;}}
.addr-input{{flex:1;background:#0d1b2a;border:1.5px solid #334455;color:#e0e0e0;padding:13px 16px;border-radius:10px;font-size:0.9rem;font-family:inherit;transition:border-color .2s;}}
.addr-input:focus{{outline:none;border-color:#00b4d8;}}.addr-input::placeholder{{color:#556677;}}
.loc-btn{{background:#0d1b2a;border:1.5px solid #334455;color:#8899aa;padding:0 16px;border-radius:10px;cursor:pointer;font-size:0.82rem;white-space:nowrap;transition:all .2s;display:flex;align-items:center;gap:6px;}}
.loc-btn:hover{{border-color:#00b4d8;color:#00b4d8;}}
.geocode-status{{font-size:0.75rem;margin-top:7px;min-height:16px;}}
.geocode-ok{{color:#2ec4b6;}}.geocode-err{{color:#e63946;}}.geocode-loading{{color:#8899aa;}}
.pac-container{{background:#0d1b2a!important;border:1px solid #334455!important;border-radius:8px!important;margin-top:4px;font-family:'Segoe UI',sans-serif;}}
.pac-item{{background:#0d1b2a!important;color:#c8d8e8!important;padding:8px 14px!important;border-top:1px solid #223344!important;cursor:pointer;}}
.pac-item:hover{{background:#1a2a3a!important;}}.pac-item-query{{color:#00b4d8!important;}}.pac-matched{{color:#00b4d8!important;}}
.type-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:12px;}}
.type-btn{{background:#0d1b2a;border:1.5px solid #334455;color:#c8d8e8;padding:16px 14px;border-radius:12px;cursor:pointer;text-align:left;transition:all .2s;display:flex;align-items:center;gap:12px;}}
.type-btn:hover{{border-color:#00b4d8;background:rgba(0,180,216,.07);}}.type-btn.selected{{border-color:#00b4d8;background:rgba(0,180,216,.13);color:#fff;}}
.type-icon{{font-size:1.5rem;flex-shrink:0;}}.type-label{{font-size:0.82rem;font-weight:600;line-height:1.3;}}
.details-textarea{{width:100%;background:#0d1b2a;border:1.5px solid #334455;color:#e0e0e0;padding:14px 16px;border-radius:10px;font-size:0.9rem;font-family:inherit;resize:vertical;min-height:100px;transition:border-color .2s;}}
.details-textarea:focus{{outline:none;border-color:#00b4d8;}}.details-textarea::placeholder{{color:#556677;}}
.submit-btn{{margin-top:18px;width:100%;background:#00b4d8;color:#0f1923;border:none;padding:15px 28px;border-radius:10px;font-weight:800;cursor:pointer;font-size:1rem;transition:all .2s;}}
.submit-btn:hover{{background:#0096c7;transform:translateY(-1px);}}.submit-btn:disabled{{background:#334455;color:#8899aa;cursor:not-allowed;transform:none;}}
#results{{display:none;}}
/* Results: full-viewport map + sidebar */
body.results-active{{overflow:hidden;}}
body.results-active .header,body.results-active .page{{display:none!important;}}
#results.fullscreen{{display:flex!important;position:fixed;inset:0;width:100vw;height:100vh;z-index:50;background:#0f1923;}}
.result-map-pane{{flex:1 1 auto;position:relative;min-width:0;}}
.result-map-pane #mapContainer{{position:absolute;inset:0;width:100%;height:100%;border-radius:0;}}
.map-overlay{{position:absolute;top:14px;left:14px;right:14px;display:flex;justify-content:space-between;align-items:flex-start;gap:12px;pointer-events:none;z-index:2;}}
.map-overlay>*{{pointer-events:auto;}}
.map-overlay .map-meta{{background:rgba(13,27,42,.88);backdrop-filter:blur(8px);border:1px solid #223344;border-radius:10px;padding:10px 14px;margin-bottom:0;}}
.map-overlay .map-legend{{background:rgba(13,27,42,.88);backdrop-filter:blur(8px);border:1px solid #223344;border-radius:10px;padding:10px 14px;margin-top:0;flex-direction:column;gap:6px;}}
.result-sidebar{{width:420px;max-width:40vw;flex:0 0 auto;background:#0d1623;border-left:1px solid #223344;overflow-y:auto;padding:18px 20px 40px;}}
.result-sidebar::-webkit-scrollbar{{width:8px;}}.result-sidebar::-webkit-scrollbar-thumb{{background:#223344;border-radius:4px;}}
.sidebar-header{{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:14px;padding-bottom:12px;border-bottom:1px solid #223344;position:sticky;top:-18px;background:#0d1623;padding-top:18px;margin-top:-18px;z-index:3;}}
.sidebar-title{{font-size:1rem;font-weight:700;color:#00b4d8;}}
.new-btn-sm{{background:transparent;border:1.5px solid #00b4d8;color:#00b4d8;padding:7px 14px;border-radius:8px;font-weight:700;cursor:pointer;font-size:0.78rem;transition:all .2s;}}
.new-btn-sm:hover{{background:rgba(0,180,216,.1);}}
/* Sidebar card redesign — colored accent borders + tighter type */
.result-sidebar .card{{padding:18px 20px;margin-bottom:16px;border-left:3px solid #334455;position:relative;}}
.result-sidebar .card-title{{font-size:0.82rem;margin-bottom:14px;padding-bottom:10px;text-transform:uppercase;letter-spacing:.06em;font-weight:700;display:flex;align-items:center;gap:8px;}}
.result-sidebar .card.accent-class{{border-left-color:#00b4d8;}}
.result-sidebar .card.accent-vendor{{border-left-color:#2ec4b6;}}
.result-sidebar .card.accent-vendor .card-title{{color:#2ec4b6;}}
.result-sidebar .card.accent-similar{{border-left-color:#8ab4f8;}}
.result-sidebar .card.accent-similar .card-title{{color:#8ab4f8;}}
.result-sidebar .card.accent-cost{{border-left-color:#ffb703;}}
.result-sidebar .card.accent-cost .card-title{{color:#ffb703;}}

/* Stat rows: label above, value+bar below */
.stat-row{{padding:11px 0;border-bottom:1px solid #1e2c3d;}}
.stat-row:last-child{{border-bottom:none;padding-bottom:0;}}
.stat-row:first-child{{padding-top:0;}}
.stat-head{{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;gap:10px;}}
.stat-lbl{{color:#8899aa;font-size:0.74rem;text-transform:uppercase;letter-spacing:.04em;font-weight:600;}}
.stat-val{{font-size:0.9rem;font-weight:700;color:#e0e0e0;}}
.stat-val.accent{{color:#00b4d8;}}
.bar-track{{height:6px;border-radius:3px;background:#0d1623;border:1px solid #1e2c3d;overflow:hidden;}}
.bar-fill{{height:100%;border-radius:3px;transition:width .8s cubic-bezier(.4,.2,.2,1);}}

/* Priority/status pill */
.pill{{display:inline-block;padding:3px 11px;border-radius:10px;font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.04em;}}
.pill-high{{background:rgba(230,57,70,.18);color:#ff6b7a;border:1px solid rgba(230,57,70,.4);}}
.pill-medium{{background:rgba(255,183,3,.18);color:#ffb703;border:1px solid rgba(255,183,3,.4);}}
.pill-low{{background:rgba(46,196,182,.18);color:#2ec4b6;border:1px solid rgba(46,196,182,.4);}}

/* Vendor block */
.vendor-hero{{padding:14px 16px;background:linear-gradient(135deg,rgba(46,196,182,.08),rgba(46,196,182,.02));border:1px solid rgba(46,196,182,.2);border-radius:10px;margin-bottom:12px;}}
.vendor-hero .vname{{font-size:1rem;font-weight:700;color:#fff;margin-bottom:10px;line-height:1.3;}}
.vendor-hero .vline{{display:flex;align-items:center;gap:7px;font-size:0.8rem;color:#c8d8e8;margin:5px 0;}}
.vendor-hero .vline .ico{{flex:0 0 16px;color:#8899aa;}}
.vendor-dist{{display:flex;justify-content:space-between;align-items:center;padding:10px 12px;background:#0d1623;border:1px solid #1e2c3d;border-radius:8px;margin-top:10px;}}
.vendor-dist .num{{font-size:1.3rem;font-weight:800;color:#2ec4b6;}}
.vendor-dist .sub{{font-size:0.7rem;color:#8899aa;text-align:right;}}

/* Similar complaint row redesign */
.sim-row{{background:#0d1623;border:1px solid #1e2c3d;border-radius:10px;padding:12px 14px;margin-bottom:9px;transition:border-color .15s;}}
.sim-row:hover{{border-color:#334455;}}
.sim-row:last-child{{margin-bottom:0;}}
.sim-row-head{{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;font-size:0.72rem;color:#8899aa;}}
.sim-row-tags{{display:flex;gap:5px;flex-wrap:wrap;margin-bottom:6px;}}
.sim-row-addr{{font-size:0.75rem;color:#c8d8e8;margin-bottom:8px;line-height:1.35;}}
.sim-row-foot{{display:flex;justify-content:space-between;align-items:center;gap:8px;}}
.sim-row-bar{{flex:1;}}
.sim-row-bar .bar-track{{height:4px;}}

/* Cost */
.cost-list{{margin-bottom:14px;}}
.cost-row{{display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px solid #1e2c3d;font-size:0.82rem;}}
.cost-row:last-child{{border-bottom:none;}}
.cost-row .cost-item{{color:#c8d8e8;}}.cost-row .cost-amt{{color:#8899aa;font-variant-numeric:tabular-nums;}}
.cost-total-box{{padding:14px 16px;background:linear-gradient(135deg,rgba(255,183,3,.1),rgba(255,183,3,.02));border:1px solid rgba(255,183,3,.3);border-radius:10px;}}
.cost-total-lbl{{font-size:0.72rem;color:#8899aa;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px;}}
.cost-total-val{{font-size:1.25rem;font-weight:800;color:#ffb703;font-variant-numeric:tabular-nums;}}
.cost-range-bar{{height:6px;background:#0d1623;border-radius:3px;margin-top:10px;position:relative;overflow:hidden;}}
.cost-range-fill{{position:absolute;left:15%;right:15%;top:0;bottom:0;background:linear-gradient(90deg,#2ec4b6,#ffb703,#e63946);border-radius:3px;}}
.cost-note{{font-size:0.7rem;color:#8899aa;margin-top:12px;line-height:1.55;padding:10px 12px;background:rgba(136,153,170,.06);border-radius:6px;}}
@media(max-width:900px){{#results.fullscreen{{flex-direction:column;}}.result-map-pane{{height:45vh;flex:0 0 auto;}}.result-sidebar{{width:100%;max-width:100%;max-height:55vh;border-left:none;border-top:1px solid #223344;}}}}
.results-header{{font-size:1.1rem;font-weight:700;color:#00b4d8;margin-bottom:18px;padding-bottom:12px;border-bottom:1px solid #223344;}}
.card{{background:#1a2a3a;border:1.5px solid #223344;border-radius:14px;padding:24px 28px;margin-bottom:18px;}}
.card-title{{font-size:1rem;font-weight:700;color:#00b4d8;margin-bottom:16px;padding-bottom:10px;border-bottom:1px solid #223344;}}
.class-row{{display:flex;justify-content:space-between;align-items:center;padding:9px 0;border-bottom:1px solid #223344;}}
.class-row:last-child{{border-bottom:none;}}.class-label{{color:#8899aa;font-size:0.82rem;}}.class-value{{font-weight:600;font-size:0.88rem;}}
.tag{{display:inline-block;padding:3px 12px;border-radius:12px;font-size:0.75rem;font-weight:700;}}
.tag-type{{background:rgba(0,180,216,.15);color:#00b4d8;}}
.priority-high{{color:#e63946;font-weight:700;}}.priority-medium{{color:#ffb703;font-weight:600;}}.priority-low{{color:#2ec4b6;}}
.badge-status{{padding:3px 10px;border-radius:12px;font-size:0.72rem;font-weight:600;}}
.s-open{{background:rgba(230,57,70,.2);color:#e63946;}}.s-closed{{background:rgba(46,196,182,.2);color:#2ec4b6;}}.s-pending{{background:rgba(255,183,3,.2);color:#ffb703;}}
.pending-chip{{background:rgba(255,183,3,.15);color:#ffb703;padding:2px 8px;border-radius:6px;font-size:0.72rem;font-weight:600;}}
.conf-bar{{height:7px;border-radius:4px;background:#223344;width:120px;overflow:hidden;display:inline-block;vertical-align:middle;margin-left:10px;}}
.conf-fill{{height:100%;border-radius:4px;}}
.fill-blue{{background:linear-gradient(90deg,#00b4d8,#48bfe3);}}.fill-high{{background:linear-gradient(90deg,#e63946,#ff6b6b);}}.fill-med{{background:linear-gradient(90deg,#ffb703,#ffd166);}}.fill-low{{background:linear-gradient(90deg,#2ec4b6,#72efdd);}}
.vendor-main{{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;flex-wrap:wrap;}}
.vendor-name{{font-size:1.05rem;font-weight:700;color:#fff;margin-bottom:5px;}}
.vendor-detail{{font-size:0.8rem;color:#8899aa;margin-top:3px;}}.vendor-detail a{{color:#00b4d8;text-decoration:none;}}
.vendor-score{{text-align:right;flex-shrink:0;}}.vendor-rating{{font-size:1.6rem;font-weight:800;color:#00b4d8;}}
.vendor-stars{{color:#ffb703;font-size:0.9rem;}}.vendor-reviews{{font-size:0.75rem;color:#8899aa;margin-top:2px;}}
.zip-badge{{display:inline-block;background:rgba(0,180,216,.12);color:#00b4d8;border:1px solid rgba(0,180,216,.3);padding:2px 10px;border-radius:8px;font-size:0.72rem;font-weight:600;margin-top:6px;}}
.more-vendors summary{{cursor:pointer;color:#8899aa;font-size:0.76rem;padding:10px 12px;user-select:none;background:#0d1623;border:1px solid #1e2c3d;border-radius:8px;text-transform:uppercase;letter-spacing:.04em;font-weight:600;}}.more-vendors summary:hover{{color:#00b4d8;border-color:#334455;}}
.more-vendor-row{{display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid #223344;}}.more-vendor-row:last-child{{border-bottom:none;}}
.complaint-row{{background:#0d1b2a;border:1px solid #223344;border-radius:10px;padding:14px 16px;margin-bottom:10px;}}
.complaint-row:last-child{{margin-bottom:0;}}
.complaint-top{{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;}}
.complaint-id{{font-size:0.78rem;color:#8899aa;}}.sim-pct{{font-size:0.85rem;font-weight:700;color:#00b4d8;}}
.complaint-meta{{font-size:0.75rem;color:#8899aa;display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-top:6px;}}
.res-chip{{background:rgba(46,196,182,.15);color:#2ec4b6;padding:2px 8px;border-radius:6px;font-size:0.72rem;font-weight:600;}}
.open-chip{{background:rgba(230,57,70,.12);color:#e63946;padding:2px 8px;border-radius:6px;font-size:0.72rem;font-weight:600;}}
#mapContainer{{width:100%;height:100%;min-height:460px;border-radius:0;overflow:hidden;}}
.map-meta{{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px;}}
.map-overlay .map-meta{{flex-direction:column;gap:8px;}}
.map-stat{{background:rgba(13,27,42,.6);border:1px solid #223344;border-radius:8px;padding:8px 14px;}}
.map-overlay .map-stat{{background:transparent;border:none;padding:0;}}
.map-stat .val{{font-size:1rem;font-weight:700;color:#00b4d8;}}.map-stat .lbl{{color:#8899aa;font-size:0.7rem;margin-top:2px;}}
.map-legend{{display:flex;gap:16px;flex-wrap:wrap;margin-top:14px;font-size:0.78rem;color:#8899aa;}}
.legend-dot{{width:12px;height:12px;border-radius:50%;display:inline-block;margin-right:5px;vertical-align:middle;}}
.cost-row{{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #223344;font-size:0.82rem;}}
.cost-row:last-child{{border-bottom:none;}}
.cost-total{{display:flex;justify-content:space-between;padding:12px 0 0;font-size:1rem;font-weight:700;color:#00b4d8;border-top:2px solid #334455;margin-top:6px;}}
.cost-note{{font-size:0.72rem;color:#8899aa;margin-top:10px;line-height:1.5;}}
.new-btn{{width:100%;background:transparent;border:1.5px solid #00b4d8;color:#00b4d8;padding:13px;border-radius:10px;font-weight:700;cursor:pointer;font-size:0.9rem;margin-top:4px;transition:all .2s;}}
.new-btn:hover{{background:rgba(0,180,216,.1);}}
.field-group{{margin-bottom:14px;}}
.field-label{{display:block;font-size:0.78rem;font-weight:600;color:#8899aa;margin-bottom:7px;text-transform:uppercase;letter-spacing:.05em;}}
.continue-btn{{margin-top:18px;width:100%;background:#00b4d8;color:#0f1923;border:none;padding:14px 28px;border-radius:10px;font-weight:800;cursor:pointer;font-size:0.95rem;transition:all .2s;}}
.continue-btn:hover:not(:disabled){{background:#0096c7;transform:translateY(-1px);}}
.continue-btn:disabled{{background:#223344;color:#556677;cursor:not-allowed;transform:none;}}
/* Work-order button + modal */
.wo-cta{{width:100%;margin-top:8px;padding:14px 18px;background:linear-gradient(135deg,#00b4d8,#0077b6);color:#0f1923;border:none;border-radius:10px;font-weight:800;cursor:pointer;font-size:0.92rem;letter-spacing:.03em;transition:transform .15s,box-shadow .15s;display:flex;align-items:center;justify-content:center;gap:8px;}}
.wo-cta:hover:not(:disabled){{transform:translateY(-1px);box-shadow:0 8px 22px rgba(0,180,216,.35);}}
.wo-cta:disabled{{background:#334455;color:#8899aa;cursor:not-allowed;transform:none;box-shadow:none;}}
.wo-sub{{font-size:0.68rem;color:#8899aa;text-align:center;margin-top:6px;line-height:1.4;}}
.marker-days-badge{{background:rgba(13,27,42,.92);color:#fff!important;padding:3px 8px;border-radius:10px;border:1px solid rgba(255,255,255,.25);white-space:nowrap;letter-spacing:.02em;text-shadow:0 1px 2px rgba(0,0,0,.6);}}
.live-pill{{display:inline-block;margin-left:8px;padding:1px 7px;border-radius:8px;background:rgba(46,196,182,.18);color:#2ec4b6;border:1px solid rgba(46,196,182,.45);font-size:0.62rem;font-weight:800;letter-spacing:.08em;vertical-align:middle;}}
.modal-backdrop{{display:none;position:fixed;top:0;left:0;right:0;bottom:0;width:100vw;height:100vh;background:rgba(0,0,0,.75);backdrop-filter:blur(4px);z-index:99999;align-items:center;justify-content:center;padding:30px;}}
.modal-backdrop.show{{display:flex!important;}}
.modal{{background:#0d1623;border:1px solid #223344;border-radius:14px;max-width:720px;width:100%;max-height:85vh;display:flex;flex-direction:column;overflow:hidden;box-shadow:0 30px 80px rgba(0,0,0,.6);}}
.modal-head{{display:flex;justify-content:space-between;align-items:center;padding:16px 22px;border-bottom:1px solid #223344;background:linear-gradient(135deg,rgba(0,180,216,.08),transparent);}}
.modal-title{{font-size:0.95rem;font-weight:700;color:#00b4d8;display:flex;align-items:center;gap:8px;}}
.modal-close{{background:transparent;border:none;color:#8899aa;font-size:1.4rem;cursor:pointer;padding:4px 10px;line-height:1;border-radius:6px;transition:all .15s;}}
.modal-close:hover{{background:#1a2a3a;color:#fff;}}
.modal-body{{padding:22px;overflow-y:auto;flex:1;}}
.wo-loading{{text-align:center;padding:50px 20px;color:#8899aa;}}
.wo-spinner{{display:inline-block;width:38px;height:38px;border:3px solid #223344;border-top-color:#00b4d8;border-radius:50%;animation:spin 0.9s linear infinite;margin-bottom:14px;}}
@keyframes spin{{to{{transform:rotate(360deg);}}}}
.wo-error{{padding:20px;background:rgba(230,57,70,.1);border:1px solid rgba(230,57,70,.3);border-radius:8px;color:#ff6b7a;font-size:0.85rem;line-height:1.5;}}
.wo-grid{{display:grid;grid-template-columns:1fr 1fr;gap:10px 18px;margin-bottom:18px;}}
.wo-field{{display:flex;flex-direction:column;gap:3px;}}
.wo-field .k{{font-size:0.68rem;color:#8899aa;text-transform:uppercase;letter-spacing:.05em;font-weight:600;}}
.wo-field .v{{font-size:0.88rem;color:#e0e0e0;font-weight:600;word-break:break-word;}}
.wo-field .v.id{{color:#00b4d8;font-family:'SF Mono',Consolas,monospace;}}
.wo-section{{margin-top:16px;padding-top:14px;border-top:1px solid #223344;}}
.wo-section-title{{font-size:0.72rem;color:#8899aa;text-transform:uppercase;letter-spacing:.06em;font-weight:700;margin-bottom:8px;}}
.wo-block{{font-size:0.84rem;color:#c8d8e8;line-height:1.6;white-space:pre-wrap;}}
.wo-materials{{background:#0f1923;border:1px solid #223344;border-radius:8px;padding:10px 14px;font-size:0.82rem;color:#c8d8e8;}}
.modal-foot{{display:flex;gap:10px;padding:14px 22px;border-top:1px solid #223344;background:#0a1320;justify-content:flex-end;}}
.modal-btn{{background:transparent;border:1.5px solid #334455;color:#c8d8e8;padding:9px 18px;border-radius:8px;font-weight:600;cursor:pointer;font-size:0.82rem;transition:all .15s;}}
.modal-btn:hover{{border-color:#00b4d8;color:#00b4d8;}}
.modal-btn.primary{{background:#00b4d8;border-color:#00b4d8;color:#0f1923;}}
.modal-btn.primary:hover{{background:#0096c7;border-color:#0096c7;color:#0f1923;}}
@media(max-width:600px){{.header{{padding:18px 20px;}}.page{{padding:20px 16px 40px;}}.step-card{{padding:20px 18px;}}.type-grid{{grid-template-columns:1fr 1fr;}}.map-meta{{gap:10px;}}.wo-grid{{grid-template-columns:1fr;}}}}
</style>
</head>
<body>
<div class="header">
  <div>
    <h1>&#x1F526; Report a Street Lamp Issue</h1>
    <div class="sub">All 5 Boroughs &bull; NYC 311 Complaint Form</div>
  </div>
  <div class="badge">LIVE DATA &bull; NYC-WIDE</div>
</div>

<div class="page">

<!-- ABOUT SECTION -->
<section class="about-section" id="aboutSection">
  <div class="about-hero">
    <h2>Illuminating the city that never sleeps <span class="accent">&mdash; faster.</span></h2>
    <p class="about-intro">
      Every dark streetlight in New York is a quiet safety gap &mdash; and in 2024 alone, more than
      <span class="hl-teal">30,000 outages</span> were reported to 311 across the five boroughs.
      Citywide, nearly <strong>one in four complaints</strong> still sits unresolved a month after it's filed; in Manhattan,
      the rate climbs to <span class="hl-red">one in three</span>. We built this platform to close that loop.
      Residents report an outage in under 60 seconds, our system classifies the fault, prioritizes it by urgency,
      and geo-matches it to a vetted local licensed electrician &mdash; who receives an AI-drafted, municipally-formatted
      work order already aligned with NYC DOT standards, ready for same-day approval. The mission is twofold: keep
      the city that never sleeps lit, and put an estimated
      <span class="hl-teal">$6&ndash;$15M in annual repair revenue</span>
      back into the hands of the neighborhood small businesses best positioned to do the work.
      Faster fixes, stronger local economies, a brighter city &mdash; one block at a time.
    </p>
  </div>

  <div class="about-callout">
    <div class="callout-big">1 in 3</div>
    <div class="callout-text">
      <div class="callout-main">Manhattan street-light complaints still unresolved 30 days after being filed.</div>
      <div class="callout-sub">32.6% of Manhattan's 2024 complaints remain open, pending, or take longer than a month to close &mdash; the worst rate of any borough. <em>Source: NYC OpenData erm2-nwe9, 2024.</em></div>
    </div>
  </div>

  <div class="about-graphics">
    <figure class="about-graphic">
      <img src="/img/about/g1-volume.svg" alt="NYC Street Light Complaints 2024 by borough: Brooklyn 8,639, Queens 8,571, Bronx 6,184, Manhattan 4,962, Staten Island 2,318" loading="lazy">
      <figcaption>30,881 complaints filed to NYC 311 in 2024 across the five boroughs.</figcaption>
    </figure>

    <figure class="about-graphic">
      <img src="/img/about/g2-closure.svg" alt="Speed of Resolution by Borough 2024: Brooklyn and Staten Island 80.4%, Bronx 78.3%, Queens 76.3%, Manhattan 67.4%" loading="lazy">
      <figcaption>Manhattan is second-fastest on same-week closures but worst on 30-day resolution &mdash; its problem is the long tail.</figcaption>
    </figure>

    <figure class="about-graphic" style="grid-column:1/-1">
      <img src="/img/about/g3-revenue.svg" alt="Local Vendor Revenue Opportunity Annualized: total $6.18M to $15.44M across all boroughs depending on per-repair rate" loading="lazy">
      <figcaption>$6.2M &ndash; $15.4M annual local-vendor revenue opportunity across the five boroughs.</figcaption>
      <p class="about-disclaimer">
        <em>Revenue estimates are derived from published NYC electrical service-call market rates and 2024 311 complaint volumes.
        They are <strong>not</strong> NYC DOT contract data and do not represent actual payments made to any current contractor.
        See <a href="/sources.html">Sources &amp; Methodology</a> for full data provenance.</em>
      </p>
    </figure>
  </div>

  <div class="about-cta">
    <button class="about-cta-primary" onclick="document.getElementById('step1').scrollIntoView({behavior:'smooth',block:'start'});">Report a complaint &rarr;</button>
    <a class="about-cta-link" href="/sources.html" target="_blank" rel="noopener">View full sources &amp; methodology &rarr;</a>
  </div>
</section>

<!-- STEP 1 -->
<div class="step-card active" id="step1">
  <div class="step-header">
    <div class="step-num">1</div>
    <div><div class="step-title">Complaint Location</div><div class="step-hint">Where is the street lamp issue located?</div></div>
  </div>

  <!-- Address Line -->
  <div class="field-group">
    <label class="field-label" for="addrInput">Address Line</label>
    <div class="addr-row">
      <input type="text" class="addr-input" id="addrInput" placeholder="e.g. 450 Victory Blvd" />
      <button class="loc-btn" onclick="useCurrentLocation()">&#x1F4CD; My Location</button>
    </div>
    <div class="geocode-status" id="geocodeStatus"></div>
  </div>

  <!-- Borough -->
  <div class="field-group">
    <label class="field-label" for="boroughSelect">Borough</label>
    <select class="zip-select" id="boroughSelect" onchange="onBoroughChange()">
      <option value="">&#8212; Select borough &#8212;</option>
      <option value="Manhattan">Manhattan</option>
      <option value="Bronx">The Bronx</option>
      <option value="Brooklyn">Brooklyn</option>
      <option value="Queens">Queens</option>
      <option value="Staten Island">Staten Island</option>
    </select>
  </div>

  <button class="continue-btn" id="continueBtn" onclick="continueToStep2()">Continue &#8594;</button>
</div>

<!-- STEP 2 -->
<div class="step-card locked" id="step2">
  <div class="step-header">
    <div class="step-num">2</div>
    <div><div class="step-title">Type of Issue</div><div class="step-hint">Select the option that best describes the problem</div></div>
  </div>
  <div class="type-grid">
    <button class="type-btn" onclick="selectType('Street Light Out',this)"><span class="type-icon">&#x1F4A1;</span><span class="type-label">Street Light Out</span></button>
    <button class="type-btn" onclick="selectType('Street Light Cycling',this)"><span class="type-icon">&#x1F501;</span><span class="type-label">Flickering / Cycling</span></button>
    <button class="type-btn" onclick="selectType('Street Light Dayburning',this)"><span class="type-icon">&#x2600;&#xFE0F;</span><span class="type-label">On During Daytime</span></button>
    <button class="type-btn" onclick="selectType('Multiple Lights Out',this)"><span class="type-icon">&#x1F526;</span><span class="type-label">Multiple Lights Out</span></button>
    <button class="type-btn" onclick="selectType('Dim Lamp',this)"><span class="type-icon">&#x1F319;</span><span class="type-label">Dim / Faint Light</span></button>
    <button class="type-btn" onclick="selectType('Fixture/Glassware Issue',this)"><span class="type-icon">&#x1F527;</span><span class="type-label">Broken Fixture / Glass</span></button>
    <button class="type-btn" onclick="selectType('Lamppost Damage',this)"><span class="type-icon">&#x26A0;&#xFE0F;</span><span class="type-label">Pole Damage / Missing</span></button>
  </div>
</div>

<!-- STEP 3 -->
<div class="step-card locked" id="step3">
  <div class="step-header">
    <div class="step-num">3</div>
    <div><div class="step-title">Additional Details</div><div class="step-hint">Optional &#8212; describe anything that helps identify the issue</div></div>
  </div>
  <textarea class="details-textarea" id="detailsInput" placeholder="e.g. The lamp on the corner has been out for 3 days. Very dark at night, kids walk here after school..."></textarea>
  <button class="submit-btn" id="submitBtn" onclick="submitComplaint()" disabled>Submit Complaint &#8594;</button>
</div>

</div> <!-- /.page -->

<!-- RESULTS (must be OUTSIDE .page so it stays visible when .page is hidden) -->
<div id="results">
  <div class="result-map-pane">
    <div id="mapContainer"></div>
    <div class="map-overlay">
      <div class="map-meta" id="mapMeta"></div>
      <div class="map-legend" id="mapLegend"></div>
    </div>
  </div>
  <aside class="result-sidebar">
    <div class="sidebar-header">
      <div class="sidebar-title">&#x1F4CB; Complaint Assessment</div>
      <button class="new-btn-sm" onclick="resetForm()">&#x2B; New</button>
    </div>
    <div class="card accent-class"><div class="card-title">&#x1F3F7;&#xFE0F; Classification</div><div id="classBody"></div></div>
    <div class="card accent-vendor"><div class="card-title">&#x1F3E2; Recommended Vendor</div><div id="vendorBody"></div></div>
    <div class="card accent-similar"><div class="card-title">&#x1F50D; Similar Past Complaints <span id="liveCount" style="margin-left:8px;font-size:0.7rem;font-weight:600"></span></div><div id="similarBody"></div></div>
    <div class="card accent-cost"><div class="card-title">&#x1F4B0; Estimated Repair Cost</div><div id="costBody"></div></div>
    <button id="createWoBtn" class="wo-cta" onclick="openWorkOrderModal()">
      <span>&#x1F4DD;</span><span>Create Work Order with AI</span>
    </button>
    <div class="wo-sub">Generates a structured NYC DOT dispatch order using Claude + similar past complaints</div>
  </aside>
</div>

<!-- WORK ORDER MODAL -->
<div class="modal-backdrop" id="woModal" onclick="if(event.target===this)closeWorkOrderModal()">
  <div class="modal">
    <div class="modal-head">
      <div class="modal-title">&#x1F4DD; <span id="woModalTitle">Generating Work Order...</span></div>
      <button class="modal-close" onclick="closeWorkOrderModal()" aria-label="Close">&times;</button>
    </div>
    <div class="modal-body" id="woModalBody"></div>
    <div class="modal-foot" id="woModalFoot" style="display:none">
      <button class="modal-btn" onclick="closeWorkOrderModal()">Close</button>
      <button class="modal-btn" onclick="copyWorkOrderJson()">&#x1F4CB; Copy JSON</button>
      <button class="modal-btn primary" onclick="downloadWorkOrderJson()">&#x2B07;&#xFE0F; Download .json</button>
    </div>
  </div>
</div>

<script>
// ================================================================
// GOOGLE MAPS BOOTSTRAP
// ================================================================
let googleMapsReady = false;
let placesAutocomplete = null;

function onGoogleMapsLoaded() {
  googleMapsReady = true;
  initPlacesAutocomplete();
}

function waitForMaps() {
  return new Promise(resolve => {
    if (googleMapsReady) return resolve();
    const t = setInterval(() => { if (googleMapsReady) { clearInterval(t); resolve(); } }, 80);
  });
}

// Map Google sublocality → our borough names
function detectBoroughFromComponents(components){
  const all = (components||[]).flatMap(c => c.long_name ? [c.long_name] : []);
  const joined = all.join(' ').toLowerCase();
  if (joined.includes('staten island')) return 'Staten Island';
  if (joined.includes('manhattan') || joined.includes('new york, ny')) return 'Manhattan';
  if (joined.includes('bronx')) return 'Bronx';
  if (joined.includes('brooklyn')) return 'Brooklyn';
  if (joined.includes('queens')) return 'Queens';
  return null;
}

function initPlacesAutocomplete() {
  const input = document.getElementById('addrInput');
  // NYC-wide bounds
  const nyc_bounds = new google.maps.LatLngBounds(
    new google.maps.LatLng(40.477, -74.260),
    new google.maps.LatLng(40.917, -73.700)
  );
  placesAutocomplete = new google.maps.places.Autocomplete(input, {
    bounds: nyc_bounds, strictBounds: false,
    componentRestrictions: { country: 'us' },
    fields: ['geometry','formatted_address','address_components'],
  });
  placesAutocomplete.addListener('place_changed', () => {
    const place = placesAutocomplete.getPlace();
    if (!place.geometry) return;
    complaintLatLng = {
      lat: place.geometry.location.lat(),
      lng: place.geometry.location.lng(),
      display: place.formatted_address,
    };
    // Auto-fill borough + ZIP from selected place
    const detectedBoro = detectBoroughFromComponents(place.address_components);
    const zipComp = (place.address_components||[]).find(c => c.types.includes('postal_code'));
    if (detectedBoro) {
      document.getElementById('boroughSelect').value = detectedBoro;
      selectedBorough = detectedBoro;
    }
    if (zipComp && zipComp.long_name) {
      selectedZip = zipComp.long_name;
    }
    setGeoStatus('ok', '&#10003; Address confirmed: ' + place.formatted_address);
  });
}

// ================================================================
// VENDOR DATA
// ================================================================
const vendors = __VENDORS_JS__;

// Haversine distance in miles
function milesBetween(a, b){
  if(!a||!b||a.lat==null||b.lat==null) return 9999;
  const toRad=d=>d*Math.PI/180, R=3958.8;
  const dLat=toRad(b.lat-a.lat), dLng=toRad(b.lng-a.lng);
  const s1=Math.sin(dLat/2), s2=Math.sin(dLng/2);
  const c=s1*s1+Math.cos(toRad(a.lat))*Math.cos(toRad(b.lat))*s2*s2;
  return 2*R*Math.asin(Math.sqrt(c));
}
// No rating/reviews in the new dataset — rank by: same ZIP > same borough > distance,
// with contactability (phone/email/license) as tiebreaker.
function vendorScore(v){
  let s = 0;
  if (v.phone)   s += 1.0;
  if (v.email)   s += 0.5;
  if (v.license) s += 0.3;
  return s;
}
function getRankedVendors(zip, borough, origin){
  const scored = vendors.map(v => ({
    ...v,
    score: vendorScore(v),
    dist: origin ? milesBetween(origin, v) : 9999,
  }));
  const sameZip  = scored.filter(v => v.zip === zip);
  const sameBoro = scored.filter(v => v.zip !== zip && v.borough === borough);
  const other    = scored.filter(v => v.zip !== zip && v.borough !== borough);
  const byDist = (a,b) => (a.dist - b.dist) || (b.score - a.score);
  return [...sameZip.sort(byDist), ...sameBoro.sort(byDist), ...other.sort(byDist)];
}

// ================================================================
// COST ESTIMATES
// ================================================================
const costData = {
  "Street Light Out":        {low:150,high:350,items:[["Labor (1–2 hrs)","$100–$200"],["Bulb / Ballast replacement","$50–$150"]]},
  "Street Light Cycling":    {low:200,high:450,items:[["Labor (2–3 hrs)","$150–$250"],["Ballast / Photocell unit","$50–$200"]]},
  "Street Light Dayburning": {low:100,high:250,items:[["Labor (1 hr)","$75–$150"],["Photocell (PEC) unit","$25–$100"]]},
  "Multiple Lights Out":     {low:500,high:1200,items:[["Labor (3–6 hrs)","$300–$700"],["Circuit diagnosis","$100–$250"],["Fuses / cable / parts","$100–$250"]]},
  "Dim Lamp":                {low:150,high:300,items:[["Labor (1–2 hrs)","$100–$200"],["Lamp / Driver","$50–$100"]]},
  "Fixture/Glassware Issue": {low:250,high:600,items:[["Labor (2–3 hrs)","$150–$300"],["Fixture / Globe parts","$100–$300"]]},
  "Lamppost Damage":         {low:800,high:3000,items:[["Labor (4–10 hrs)","$400–$1,200"],["Structural parts / pole","$300–$1,500"],["Permits & inspection","$100–$300"]]},
};
function renderCost(type){
  const d=costData[type]||{low:150,high:400,items:[["Labor","$100–$250"],["Parts","$50–$150"]]};
  const rows = d.items.map(([i,c])=>`<div class="cost-row"><span class="cost-item">${i}</span><span class="cost-amt">${c}</span></div>`).join('');
  return `<div class="cost-list">${rows}</div>
    <div class="cost-total-box">
      <div class="cost-total-lbl">Estimated Total Range</div>
      <div class="cost-total-val">$${d.low.toLocaleString()} &ndash; $${d.high.toLocaleString()}</div>
      <div class="cost-range-bar"><div class="cost-range-fill"></div></div>
    </div>
    <div class="cost-note">&#x2139;&#xFE0F; Based on NYC DOT average contractor rates. Actual costs vary by borough, site conditions, and contractor. Street lamp repairs on public property are typically handled by NYC DOT at no direct cost to residents when reported via 311.</div>`;
}

// ================================================================
// REAL 311 DATA
// ================================================================
const complaintTypes=["Street Light Out","Street Light Cycling","Street Light Dayburning","Multiple Lights Out","Dim Lamp","Fixture/Glassware Issue","Lamppost Damage"];
const statuses=["Open","Closed","Pending"];
const priorities=["High","Medium","Low"];
const boroughList=["Manhattan","Bronx","Brooklyn","Queens","Staten Island"];
const boroughZips = __BOROUGH_ZIPS_JS__;
const allZips = Array.from(new Set(Object.values(boroughZips).flat())).sort();
// Borough centroids (fallback when no address provided)
const BOROUGH_CENTROIDS = {
  "Manhattan":     [40.7831, -73.9712],
  "Bronx":         [40.8448, -73.8648],
  "Brooklyn":      [40.6782, -73.9442],
  "Queens":        [40.7282, -73.7949],
  "Staten Island": [40.5795, -74.1502],
};
""" + "const rawCallsData=" + raw + ";\n" + """
const descTpl={
  "Street Light Out":["Lamp at {addr} completely out for several days. Pitch black and unsafe at night.","Street light not working at {addr}. Dangerous after sunset.","Dead street light near {addr}. Multiple residents complained.","No light from lamp at {addr}. Out for over a week.","Lamp gone out at {addr}. Unsafe — kids and elderly use this walkway."],
  "Street Light Cycling":["Lamp at {addr} cycling on and off all night. Very disorienting for drivers.","Light near {addr} flickers — on a minute, off 30 seconds, repeating.","Light at {addr} cycling intermittently for several days.","Street light near {addr} turns on and off repeatedly.","Cycling lamp at {addr}. Disruptive and unsafe."],
  "Street Light Dayburning":["Lamp at {addr} stays on all day. Sensor must be broken — burning 24/7.","Street light near {addr} never turns off, even in daylight.","Photocell failure at {addr}. Light on continuously day and night.","Lamp at {addr} burning through the day non-stop.","Street light at {addr} on during daylight. Needs photocell repair."],
  "Multiple Lights Out":["Multiple lights out near {addr}. Several consecutive lamps not working.","Block-wide outage near {addr}. 4–5 lights dark — whole stretch unsafe.","Several lights failed near {addr}. Major section unlit at night.","Multiple lights out near {addr}. Possible circuit issue.","3+ lamps out near {addr}. Whole block dark and unsafe."],
  "Dim Lamp":["Lamp at {addr} extremely dim. Barely any illumination at night.","Light near {addr} very faint — barely on. Needs bulb replacement.","Lamp at {addr} progressively dimmer over weeks. Almost useless.","Very weak output from lamp at {addr}. Inadequate illumination.","Dim street light at {addr}. Not providing adequate visibility."],
  "Fixture/Glassware Issue":["Glass globe on lamp at {addr} missing, damaged, or hanging loose.","Lamp at {addr} has fixture issue — glassware missing or door open.","Fixture problem at {addr}. Housing needs attention.","Glassware or fixture damaged at street lamp near {addr}.","Fixture door open or glass broken on light at {addr}."],
  "Lamppost Damage":["Lamp pole at {addr} damaged — leaning, cracked, or missing. Unsafe.","Street light pole near {addr} has structural damage. Needs inspection.","Damaged or missing lamppost at {addr}. Hazard to pedestrians.","Lamp pole at {addr} bent, knocked down, or visibly damaged.","Lamppost damage near {addr}. Structure appears unstable."]
};
const BORO_PREFIX = {"Manhattan":"MN","Bronx":"BX","Brooklyn":"BK","Queens":"QN","Staten Island":"SI"};
const calls=rawCallsData.map((r,idx)=>{
  const tpls=descTpl[r.type]||["Street lamp issue at {addr}."];
  const loc=(r.address&&r.address!=='Unknown')?r.address:((r.street&&r.street!=='Unknown')?r.street:'this location');
  const desc=tpls[idx%tpls.length].replace(/{addr}/g,loc).replace(/{street}/g,r.street&&r.street!=='Unknown'?r.street:'this street');
  const d=new Date(r.date+'T00:00:00');
  const pfx=BORO_PREFIX[r.borough]||'NYC';
  return{...r,id:pfx+'-'+r.id,rawId:r.id,date:d,dateStr:d.toLocaleDateString('en-US'),month:d.getMonth(),year:d.getFullYear(),description:desc,
    address:(r.address&&r.address!=='Unknown')?r.address:((r.street&&r.street!=='Unknown')?r.street:'Address not recorded')};
});

// ================================================================
// CLASSIFIER
// ================================================================
const keywordMap={
  "Street Light Out":["out","dark","dead","not working","no light","pitch black","stopped","gone out","completely out","lamp out","light out"],
  "Street Light Cycling":["cycling","cycle","flicker","blink","strobe","intermittent","on and off","blinking","flashing","flickering","repeating"],
  "Street Light Dayburning":["daytime","dayburning","24/7","never turns off","always on","sensor","photocell","stays on","during the day","burning all day","daylight"],
  "Multiple Lights Out":["multiple","several","block","consecutive","circuit","stretch","block-wide","many lights","outage","whole block","entire block"],
  "Dim Lamp":["dim","faint","weak","barely","low light","almost useless","very dim","not bright","fading","dimming"],
  "Fixture/Glassware Issue":["glass","glassware","globe","fixture","luminaire","door open","missing glass","broken glass","hanging","cover","housing"],
  "Lamppost Damage":["leaning","bent","cracked","damaged","tilted","hit","knocked","broken pole","fallen","pole","missing post","lamppost","exposed wire","structural","knocked down"]
};
function classifyText(type,text){
  const lower=text.toLowerCase(),scores={};
  for(const[t,kws]of Object.entries(keywordMap)){scores[t]=t===type?5:0;for(const kw of kws)if(lower.includes(kw))scores[t]++;}
  if(lower.includes('cycling'))scores["Street Light Cycling"]+=2;
  if(lower.includes('photocell')||lower.includes('sensor'))scores["Street Light Dayburning"]+=2;
  if(lower.includes('multiple')||lower.includes('whole block'))scores["Multiple Lights Out"]+=2;
  if(lower.includes('dim')||lower.includes('faint'))scores["Dim Lamp"]+=2;
  if(lower.includes('glass')||lower.includes('fixture'))scores["Fixture/Glassware Issue"]+=2;
  if(lower.includes('leaning')||lower.includes('bent')||lower.includes('pole'))scores["Lamppost Damage"]+=2;
  if(lower.includes('out')||lower.includes('dead')||lower.includes('dark'))scores["Street Light Out"]++;
  const sorted=Object.entries(scores).sort((a,b)=>b[1]-a[1]);
  const total=sorted.reduce((s,e)=>s+e[1],0);
  return{type:sorted[0][0],confidence:Math.min(0.98,sorted[0][1]/Math.max(1,total)+0.15),allScores:sorted};
}
function determinePriority(type,text){
  const lower=text.toLowerCase();
  const uw=["dangerous","unsafe","hazard","urgent","kids","children","elderly","accident","fall","dark","pitch black","knocked down","missing","structural"];
  let boost=0;for(const w of uw)if(lower.includes(w))boost+=0.10;
  const base={"Street Light Out":0.60,"Multiple Lights Out":0.75,"Lamppost Damage":0.80,"Street Light Cycling":0.45,"Dim Lamp":0.35,"Fixture/Glassware Issue":0.40,"Street Light Dayburning":0.20};
  const score=Math.min(1,(base[type]||0.50)+boost);
  return{priority:score>=0.65?"High":score>=0.38?"Medium":"Low",urgencyScore:score};
}

// ================================================================
// SIMILARITY ENGINE
// ================================================================
function featureVec(c){
  return[...complaintTypes.map(t=>t===c.type?1:0),
         ...allZips.map(z=>z===c.zip?1:0),
         ...boroughList.map(b=>b===c.borough?1:0),
         ...priorities.map(p=>p===c.priority?1:0),
         ...statuses.map(s=>s===c.status?1:0),
         (c.month||0)/11,c.resolution?Math.min(1,c.resolution/30):0.5];
}
function cosineSim(a,b){let d=0,mA=0,mB=0;for(let i=0;i<a.length;i++){d+=a[i]*b[i];mA+=a[i]*a[i];mB+=b[i]*b[i];}return mA&&mB?d/(Math.sqrt(mA)*Math.sqrt(mB)):0;}

// Records fetched live from NYC OpenData before each similarity search.
let callsLive = [];

function normalizeLiveRecord(r){
  const tpls = descTpl[r.type] || ["Street lamp issue at {addr}."];
  const loc  = (r.address && r.address!=='Unknown') ? r.address
             : (r.street && r.street!=='Unknown')   ? r.street
             : 'this location';
  const desc = tpls[0].replace(/{addr}/g, loc).replace(/{street}/g, r.street||'this street');
  const d    = new Date((r.date||'2020-01-01') + 'T00:00:00');
  const pfx  = BORO_PREFIX[r.borough] || 'NYC';
  return {
    ...r,
    id: pfx + '-' + r.id,
    rawId: r.id,
    date: d,
    dateStr: d.toLocaleDateString('en-US'),
    month: d.getMonth(),
    year: d.getFullYear(),
    description: desc,
    priority: 'Medium',
    address: (r.address && r.address!=='Unknown') ? r.address
           : (r.street  && r.street!=='Unknown')  ? r.street
           : 'Address not recorded',
    live: true,
  };
}

// Maps Socrata `descriptor` values to our 7 canonical complaint types.
const DESCRIPTOR_TO_TYPE = {
  'street light out':          'Street Light Out',
  'multiple streetlights out': 'Multiple Lights Out',
  'multiple lights out':       'Multiple Lights Out',
  'street light dayburning':   'Street Light Dayburning',
  'street light cycling':      'Street Light Cycling',
  'dim street light':          'Dim Lamp',
  'street light dim':          'Dim Lamp',
  'dim lamp':                  'Dim Lamp',
  'damaged luminaire':         'Fixture/Glassware Issue',
  'missing luminaire':         'Fixture/Glassware Issue',
  'broken globe':              'Fixture/Glassware Issue',
  'fixture/glassware issue':   'Fixture/Glassware Issue',
  'damaged pole':              'Lamppost Damage',
  'knocked down pole':         'Lamppost Damage',
  'missing pole':              'Lamppost Damage',
  'lamppost damage':           'Lamppost Damage',
};
function canonicalType(descriptor){
  if(!descriptor) return 'Street Light Out';
  const k = descriptor.trim().toLowerCase();
  if(DESCRIPTOR_TO_TYPE[k]) return DESCRIPTOR_TO_TYPE[k];
  for(const key in DESCRIPTOR_TO_TYPE){
    if(k.indexOf(key) !== -1) return DESCRIPTOR_TO_TYPE[key];
  }
  return 'Street Light Out';
}

// Browser-direct call to NYC OpenData Socrata (public, CORS-enabled, no key
// needed for low volume). Bypasses Vercel's Python sandbox which can't
// resolve data.cityofnewyork.gov reliably.
async function fetchLiveRecords(zip, borough){
  if(!zip && !borough) return [];
  const where = ["complaint_type='Street Light Condition'"];
  if (zip)          where.push("incident_zip='" + zip + "'");
  else if (borough) where.push("borough='" + borough.toUpperCase() + "'");
  const params = new URLSearchParams({
    '$where':  where.join(' AND '),
    '$limit':  '200',
    '$order':  'created_date DESC',
    '$select': 'unique_key,created_date,closed_date,complaint_type,descriptor,status,incident_address,street_name,incident_zip,borough,latitude,longitude',
  });
  const url = 'https://data.cityofnewyork.gov/resource/erm2-nwe9.json?' + params.toString();
  try {
    const ctrl = new AbortController();
    const t = setTimeout(()=>ctrl.abort(), 5000);
    const resp = await fetch(url, {signal: ctrl.signal, headers: {'Accept':'application/json'} });
    clearTimeout(t);
    if (!resp.ok) { console.warn('[live] Socrata returned', resp.status); return []; }
    const rows = await resp.json();
    const bakedIds = new Set(calls.map(c => c.rawId));
    const out = [];
    for (const r of rows) {
      const lat = parseFloat(r.latitude), lng = parseFloat(r.longitude);
      if (!lat || !lng) continue;
      const created = (r.created_date||'').slice(0,10);
      const closed  = (r.closed_date ||'').slice(0,10);
      const status  = (r.status||'Open').trim();
      let resolution = null;
      if (status.toLowerCase()==='closed' && created && closed) {
        resolution = Math.max(0, Math.floor((new Date(closed) - new Date(created))/86400000));
      }
      const rec = {
        id: r.unique_key || '',
        rawId: r.unique_key || '',
        date: created,
        type: canonicalType(r.descriptor),
        raw_type: r.descriptor || '',
        status: status,
        resolution: resolution,
        address: (r.incident_address || r.street_name || 'Unknown').trim(),
        street: (r.street_name || '').trim(),
        zip: (r.incident_zip || '').trim(),
        borough: (r.borough || '').replace(/\b\w/g, ch => ch.toUpperCase()),
        lat: +lat.toFixed(6),
        lng: +lng.toFixed(6),
        live: true,
      };
      if (bakedIds.has(rec.rawId)) continue;
      out.push(normalizeLiveRecord(rec));
    }
    console.log('[live] merged', out.length, 'fresh 311 records for', zip || borough);
    return out;
  } catch(e) {
    console.warn('[live] NYC OpenData fetch failed:', e.message);
    return [];
  }
}

function findSimilar(type,zip,borough,n=5){
  const qp=determinePriority(type,"").priority;
  const qv=featureVec({type,zip,borough,priority:qp,status:"Open",month:0,resolution:null});
  // Score baked + live separately so fresh NYC OpenData records aren't drowned
  // out by the 10K-row baked corpus. Tie-break by date DESC (most recent wins).
  const scored = arr => arr.filter(c=>c.lat&&c.lng)
    .map(c=>({...c, sim: cosineSim(qv, featureVec(c))}))
    .sort((a,b) => (b.sim - a.sim) || ((+b.date||0) - (+a.date||0)));
  const liveRanked  = scored(callsLive);
  const bakedRanked = scored(calls);
  // Reserve up to half the slots for live records when they exist. This
  // guarantees recent 311 activity surfaces even when the baked corpus has
  // thousands of equally-similar 2018/2019 entries.
  const liveQuota = Math.min(liveRanked.length, Math.ceil(n/2));
  const picked = liveRanked.slice(0, liveQuota)
               .concat(bakedRanked.slice(0, n - liveQuota));
  return picked.sort((a,b) => (b.sim - a.sim) || ((+b.date||0) - (+a.date||0)));
}

// ================================================================
// FORM STATE
// ================================================================
let selectedType=null,selectedZip=null,selectedBorough=null,complaintLatLng=null;
let lastAssessment=null, lastWorkOrder=null;

function setGeoStatus(type,msg){
  const el=document.getElementById('geocodeStatus');
  el.className='geocode-status geocode-'+type;
  el.innerHTML=msg;
}

function onBoroughChange(){
  const borough=document.getElementById('boroughSelect').value;
  selectedBorough=borough||null;
}

async function continueToStep2(){
  const boroVal = document.getElementById('boroughSelect').value;
  const addrVal = (document.getElementById('addrInput').value||'').trim();
  if(!addrVal){
    setGeoStatus('err','&#x26A0; Please enter an address before continuing.');
    document.getElementById('addrInput').focus();
    return;
  }
  if(!boroVal){
    setGeoStatus('err','&#x26A0; Please select a borough before continuing.');
    document.getElementById('boroughSelect').focus();
    return;
  }
  selectedBorough = boroVal;

  // If autocomplete didn't already capture a ZIP, try to geocode the address
  // to extract it. This is best-effort; we continue regardless.
  if(!selectedZip){
    try{
      await waitForMaps();
      const geocoder = new google.maps.Geocoder();
      const zipFromGeo = await new Promise((resolve)=>{
        geocoder.geocode(
          {address: addrVal + ', ' + boroVal + ', NY'},
          (results, status)=>{
            if(status==='OK' && results && results[0]){
              const zc=(results[0].address_components||[])
                .find(c=>c.types.includes('postal_code'));
              if(!complaintLatLng){
                complaintLatLng={
                  lat: results[0].geometry.location.lat(),
                  lng: results[0].geometry.location.lng(),
                  display: results[0].formatted_address,
                };
              }
              resolve(zc ? zc.long_name : null);
            } else resolve(null);
          }
        );
      });
      if(zipFromGeo) selectedZip = zipFromGeo;
    }catch(_){ /* non-fatal */ }
  }

  setGeoStatus('','');
  document.getElementById('step2').classList.remove('locked');
  document.getElementById('step2').classList.add('active');
  document.getElementById('step2').scrollIntoView({behavior:'smooth',block:'start'});
}

async function useCurrentLocation(){
  setGeoStatus('loading','&#x23F3; Getting your location...');
  if(!navigator.geolocation){setGeoStatus('err','Geolocation not supported by your browser.');return;}
  navigator.geolocation.getCurrentPosition(async pos=>{
    const lat=pos.coords.latitude,lng=pos.coords.longitude;
    complaintLatLng={lat,lng,display:'Current location'};
    await waitForMaps();
    const geocoder=new google.maps.Geocoder();
    geocoder.geocode({location:{lat,lng} },(results,status)=>{
      if(status==='OK'&&results[0]){
        complaintLatLng.display=results[0].formatted_address;
        const zipC=(results[0].address_components||[]).find(c=>c.types.includes('postal_code'));
        const snC=(results[0].address_components||[]).find(c=>c.types.includes('street_number'));
        const rtC=(results[0].address_components||[]).find(c=>c.types.includes('route'));
        const street=(snC?snC.long_name+' ':'')+(rtC?rtC.long_name:'');
        if(street)document.getElementById('addrInput').value=street;
        const boro=detectBoroughFromComponents(results[0].address_components);
        if(boro){
          document.getElementById('boroughSelect').value=boro;
          selectedBorough=boro;
        }
        if(zipC&&zipC.long_name){
          selectedZip=zipC.long_name;
        }
        setGeoStatus('ok','&#10003; Location found: '+results[0].formatted_address);
      }else{
        setGeoStatus('ok','&#10003; Location captured ('+lat.toFixed(5)+', '+lng.toFixed(5)+')');
      }
    });
  },err=>{setGeoStatus('err','Could not get location: '+err.message);});
}

function selectType(type,btn){
  selectedType=type;
  document.querySelectorAll('.type-btn').forEach(b=>b.classList.remove('selected'));
  btn.classList.add('selected');
  document.getElementById('step3').classList.remove('locked');
  document.getElementById('step3').classList.add('active');
  document.getElementById('submitBtn').disabled=false;
}

function starsHtml(r){
  if(!r)return'<span style="color:#556677">No rating</span>';
  let s='';for(let i=0;i<Math.floor(r);i++)s+='&#9733;';
  if(r-Math.floor(r)>=0.5)s+='&#9734;';
  return`<span class="vendor-stars">${s}</span>`;
}

// ================================================================
// GOOGLE MAPS — Dark Style
// ================================================================
const DARK_STYLE = [
  {elementType:'geometry',stylers:[{color:'#0d1b2a'}]},
  {elementType:'labels.text.stroke',stylers:[{color:'#0d1b2a'}]},
  {elementType:'labels.text.fill',stylers:[{color:'#8899aa'}]},
  {featureType:'administrative',elementType:'geometry',stylers:[{color:'#334455'}]},
  {featureType:'road',elementType:'geometry',stylers:[{color:'#1a2a3a'}]},
  {featureType:'road',elementType:'geometry.stroke',stylers:[{color:'#223344'}]},
  {featureType:'road',elementType:'labels.text.fill',stylers:[{color:'#8899aa'}]},
  {featureType:'road.highway',elementType:'geometry',stylers:[{color:'#223344'}]},
  {featureType:'road.highway',elementType:'geometry.stroke',stylers:[{color:'#334455'}]},
  {featureType:'road.highway',elementType:'labels.text.fill',stylers:[{color:'#00b4d8'}]},
  {featureType:'water',elementType:'geometry',stylers:[{color:'#060e18'}]},
  {featureType:'water',elementType:'labels.text.fill',stylers:[{color:'#334455'}]},
  // Hide ALL points of interest (restaurants, hotels, hospitals, parks, schools, businesses, etc.)
  {featureType:'poi',stylers:[{visibility:'off'}]},
  {featureType:'poi.business',stylers:[{visibility:'off'}]},
  {featureType:'poi.park',stylers:[{visibility:'off'}]},
  {featureType:'poi.medical',stylers:[{visibility:'off'}]},
  {featureType:'poi.school',stylers:[{visibility:'off'}]},
  {featureType:'poi.attraction',stylers:[{visibility:'off'}]},
  {featureType:'poi.place_of_worship',stylers:[{visibility:'off'}]},
  {featureType:'poi.sports_complex',stylers:[{visibility:'off'}]},
  {featureType:'poi.government',stylers:[{visibility:'off'}]},
  // Hide all transit (stations, bus stops, train lines)
  {featureType:'transit',stylers:[{visibility:'off'}]},
];

function makeMarkerIcon(color, scale=10){
  return {
    path: google.maps.SymbolPath.CIRCLE,
    scale, fillColor: color, fillOpacity: 1,
    strokeColor: '#ffffff', strokeWeight: 2,
  };
}

// Emoji-in-a-circle marker. labelOrigin is placed above the icon so
// marker.label (the days-count badge for similar complaints) renders above.
function makeEmojiIcon(emoji, borderColor='#ffffff', size=42){
  const svg =
    "<svg xmlns='http://www.w3.org/2000/svg' width='" + size + "' height='" + size + "'>" +
      "<circle cx='" + (size/2) + "' cy='" + (size/2) + "' r='" + (size/2-2) + "' fill='#0d1b2a' stroke='" + borderColor + "' stroke-width='2.5'/>" +
      "<text x='50%' y='52%' dominant-baseline='central' text-anchor='middle' font-size='" + Math.round(size*0.52) + "'>" + emoji + "</text>" +
    "</svg>";
  return {
    url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(svg),
    scaledSize: new google.maps.Size(size, size),
    anchor: new google.maps.Point(size/2, size/2),
    labelOrigin: new google.maps.Point(size/2, -12),  // badge floats above
  };
}

// Complaint type -> emoji
const TYPE_EMOJI = {
  'Street Light Out':          '💡',
  'Street Light Cycling':      '🔁',
  'Street Light Dayburning':   '☀️',
  'Multiple Lights Out':       '🔦',
  'Dim Lamp':                  '🌙',
  'Fixture/Glassware Issue':   '🔧',
  'Lamppost Damage':           '⚠️',
};
function emojiForType(t){ return TYPE_EMOJI[t] || '💡'; }

// Days between a YYYY-MM-DD (or Date) and today, >=0.
function daysSince(d){
  if(!d) return null;
  const then = (d instanceof Date) ? d : new Date(d);
  if(isNaN(then)) return null;
  return Math.max(0, Math.floor((Date.now() - then.getTime()) / 86400000));
}

function makeInfoContent(title, lines, accentColor='#00b4d8'){
  const rows = lines.map(l=>`<div style="margin:2px 0;font-size:12px;color:#c8d8e8">${l}</div>`).join('');
  return `<div style="background:#0d1b2a;padding:10px 14px;border-radius:8px;min-width:180px;font-family:'Segoe UI',sans-serif">
    <div style="font-weight:700;color:${accentColor};margin-bottom:6px;font-size:13px">${title}</div>
    ${rows}
  </div>`;
}

let gMap = null;

async function buildMap(ll, similar, vendor){
  await waitForMaps();
  await new Promise(r => setTimeout(r, 50));

  const mapEl = document.getElementById('mapContainer');
  gMap = new google.maps.Map(mapEl, {
    center: {lat: ll.lat, lng: ll.lng},
    zoom: 13,
    styles: DARK_STYLE,
    mapTypeControl: false,
    streetViewControl: false,
    fullscreenControl: false,
    clickableIcons: false,  // disable click on any stray POI
    gestureHandling: 'greedy',
  });

  const infoWindow = new google.maps.InfoWindow({disableAutoPan: false});

  // Similar complaint markers — bandage if closed (days-to-close),
  // low-battery if still open (days-open). Days render as a small
  // badge above the emoji via the marker's native label.
  similar.forEach(c => {
    if (!c.lat || !c.lng) return;
    const isClosed = c.status === 'Closed' && c.resolution;
    const emoji    = isClosed ? '🩹' : '🪫';
    const border   = isClosed ? '#2ec4b6'   : '#e63946';
    const daysVal  = isClosed ? c.resolution : daysSince(c.date);
    const daysText = daysVal==null ? '' : (daysVal + 'd ' + (isClosed ? 'closed' : 'open'));
    const marker = new google.maps.Marker({
      position: {lat: c.lat, lng: c.lng}, map: gMap,
      icon: makeEmojiIcon(emoji, border, 40),
      title: c.id + ' — ' + (isClosed ? ('closed in ' + c.resolution + 'd') : (daysVal + 'd open')),
      zIndex: 1,
      label: {
        text: daysText,
        color: '#ffffff',
        fontSize: '11px',
        fontWeight: '700',
        className: 'marker-days-badge',
      },
    });
    const resLine = isClosed
      ? `<span style="color:#2ec4b6">Closed in ${c.resolution} day${c.resolution!==1?'s':''}</span>`
      : `<span style="color:#e63946">Still open (${daysVal}d)</span>`;
    marker.addListener('click', () => {
      infoWindow.setContent(makeInfoContent(c.id + ' &mdash; Similar Complaint', [
        c.type, c.address + ', ' + c.zip, c.dateStr, resLine,
      ], border));
      infoWindow.open(gMap, marker);
    });
  });

  // Vendor marker — electrician
  const vendorMarker = new google.maps.Marker({
    position: {lat: vendor.lat, lng: vendor.lng}, map: gMap,
    icon: makeEmojiIcon('⚡', '#2ec4b6', 46),
    title: vendor.name, zIndex: 2,
  });
  const licenseLine = vendor.license ? ('License #' + vendor.license) : 'Licensed NYC electrician';
  vendorMarker.addListener('click', () => {
    infoWindow.setContent(makeInfoContent('&#x1F3E2; ' + vendor.name, [
      vendor.phone || 'No phone listed', vendor.address, licenseLine,
    ], '#2ec4b6'));
    infoWindow.open(gMap, vendorMarker);
  });

  // Complaint marker — emoji matches the complaint type the user selected
  const complaintMarker = new google.maps.Marker({
    position: {lat: ll.lat, lng: ll.lng}, map: gMap,
    icon: makeEmojiIcon(emojiForType(selectedType), '#e63946', 50),
    title: 'Your Complaint', zIndex: 3,
  });
  complaintMarker.addListener('click', () => {
    infoWindow.setContent(makeInfoContent('&#x1F6A8; Your Complaint', [
      selectedType, ll.display || selectedZip,
      (selectedBorough||'') + (selectedZip?(' &bull; ZIP '+selectedZip):''),
    ], '#e63946'));
    infoWindow.open(gMap, complaintMarker);
  });
  infoWindow.setContent(makeInfoContent('&#x1F6A8; Your Complaint', [
    selectedType, ll.display || selectedZip,
    (selectedBorough||'') + (selectedZip?(' &bull; ZIP '+selectedZip):''),
  ], '#e63946'));
  infoWindow.open(gMap, complaintMarker);

  // Directions: vendor → complaint
  const dirService  = new google.maps.DirectionsService();
  const dirRenderer = new google.maps.DirectionsRenderer({
    map: gMap, suppressMarkers: true,
    polylineOptions: {strokeColor: '#2ec4b6', strokeWeight: 4, strokeOpacity: 0.75},
  });

  dirService.route({
    origin:      {lat: vendor.lat, lng: vendor.lng},
    destination: {lat: ll.lat, lng: ll.lng},
    travelMode:  google.maps.TravelMode.DRIVING,
  }, (result, status) => {
    if (status === 'OK') {
      dirRenderer.setDirections(result);
      const leg = result.routes[0].legs[0];
      document.getElementById('mapMeta').innerHTML =
        `<div class="map-stat"><div class="val">${leg.distance.text}</div><div class="lbl">Distance to Vendor</div></div>
         <div class="map-stat"><div class="val">${leg.duration.text}</div><div class="lbl">Est. Drive Time</div></div>
         <div class="map-stat"><div class="val">${vendor.name.split(' ').slice(0,3).join(' ')}</div><div class="lbl">Assigned Vendor</div></div>`;
    } else {
      // Fallback: just fit all markers
      const bounds = new google.maps.LatLngBounds();
      bounds.extend({lat: ll.lat, lng: ll.lng});
      bounds.extend({lat: vendor.lat, lng: vendor.lng});
      similar.filter(c=>c.lat&&c.lng).forEach(c => bounds.extend({lat:c.lat,lng:c.lng}));
      gMap.fitBounds(bounds);
      document.getElementById('mapMeta').innerHTML =
        `<div class="map-stat"><div class="val">${vendor.name.split(' ').slice(0,3).join(' ')}</div><div class="lbl">Assigned Vendor</div></div>`;
    }
  });

  // Legend
  document.getElementById('mapLegend').innerHTML =
    `<span><span class="legend-dot" style="background:#e63946"></span>Your Complaint</span>
     <span><span class="legend-dot" style="background:#00b4d8"></span>Similar Past Complaints</span>
     <span><span class="legend-dot" style="background:#2ec4b6"></span>Assigned Vendor</span>
     <span><span style="display:inline-block;width:22px;border-top:3px solid #2ec4b6;vertical-align:middle;margin-right:5px"></span>Driving Route</span>`;
}

// ================================================================
// GEOCODE ADDRESS (Google Geocoding API)
// ================================================================
async function geocodeAddress(addr, zip) {
  await waitForMaps();
  const geocoder = new google.maps.Geocoder();
  return new Promise(resolve => {
    const boroPart = selectedBorough ? (', ' + selectedBorough) : '';
    geocoder.geocode({address: addr + boroPart + ', NY ' + (zip||'')}, (results, status) => {
      if (status === 'OK' && results[0]) {
        const loc = results[0].geometry.location;
        resolve({lat: loc.lat(), lng: loc.lng(), display: results[0].formatted_address});
      } else {
        resolve(null);
      }
    });
  });
}

// ================================================================
// SUBMIT
// ================================================================
async function submitComplaint(){
  if (!selectedZip || !selectedType) return;
  const details = document.getElementById('detailsInput').value.trim();
  const addr    = document.getElementById('addrInput').value.trim();
  const btn     = document.getElementById('submitBtn');
  btn.disabled = true; btn.textContent = 'Processing...';
  try {
  const clf  = classifyText(selectedType, selectedType + ' ' + details);
  const {priority, urgencyScore} = determinePriority(selectedType, details);
  // Geocode / pick origin first so distance ranking works
  let originLL = complaintLatLng;
  if (!originLL && addr) {
    originLL = await geocodeAddress(addr, selectedZip);
  }
  if (!originLL) {
    const c = BOROUGH_CENTROIDS[selectedBorough] || [40.7128, -74.0060];
    originLL = {lat: c[0], lng: c[1], display: selectedBorough + ' (approximate — enter address for precision)'};
  }
  complaintLatLng = originLL;

  const ranked = getRankedVendors(selectedZip, selectedBorough, originLL);
  const topVendor = ranked[0] || {name:'No vendor available',phone:'',address:'',zip:'',borough:'',lat:originLL.lat,lng:originLL.lng,license:''};
  const moreVendors = ranked.slice(1, 4);

  // Pull the latest 311 records for this ZIP from NYC OpenData and
  // merge them into the similarity corpus. Bounded by a short timeout
  // so a slow/failing upstream can't block submission.
  btn.textContent = 'Pulling live 311 data...';
  callsLive = await fetchLiveRecords(selectedZip, selectedBorough);

  const similar = findSimilar(selectedType, selectedZip, selectedBorough, 5);
  // Small badge next to the "Similar Past Complaints" header so the user
  // can see that the NYC OpenData feed actually fired and how many fresh
  // records were merged.
  const liveCountEl = document.getElementById('liveCount');
  if (liveCountEl) {
    if (callsLive.length > 0) {
      liveCountEl.innerHTML = '<span class="live-pill">&#x1F7E2; ' + callsLive.length + ' LIVE PULLED</span>';
    } else {
      liveCountEl.innerHTML = '<span style="color:#8899aa;font-size:0.7rem">(no new live records for this ZIP)</span>';
    }
  }

  // Stash context for the "Create Work Order" button
  lastAssessment = {
    complaint: {
      complaint_id: 'NYC-' + Date.now().toString(36).toUpperCase(),
      complaint_type: selectedType,
      address: addr || (originLL.display || ''),
      borough: selectedBorough,
      zip: selectedZip,
      reported_date: new Date().toISOString().slice(0,10),
      details: details,
      priority: priority,
      urgency_score: urgencyScore,
    },
    similar_past_orders: similar.map(c => ({
      complaint_id:   c.rawId,
      complaint_type: c.raw_type || c.type,
      address:        c.address,
      borough:        c.borough,
      reported_date:  c.dateStr,
      closed_date:    c.status==='Closed' ? 'closed' : null,
      days_to_close:  c.resolution,
      status:         c.status,
    })),
    vendor: {
      name:    topVendor.name,
      phone:   topVendor.phone,
      email:   topVendor.email,
      license: topVendor.license,
      address: topVendor.address,
    },
  };

  // Classification
  const priPill  = priority==="High"?"pill-high":priority==="Medium"?"pill-medium":"pill-low";
  const priColor = priority==="High"?"#e63946":priority==="Medium"?"#ffb703":"#2ec4b6";
  const confPct  = Math.round(clf.confidence*100);
  const urgPct   = Math.round(urgencyScore*100);
  document.getElementById('classBody').innerHTML =
    `<div class="stat-row">
       <div class="stat-head"><span class="stat-lbl">Complaint Type</span><span class="stat-val accent">${clf.type}</span></div>
     </div>
     <div class="stat-row">
       <div class="stat-head"><span class="stat-lbl">Classification Confidence</span><span class="stat-val">${confPct}%</span></div>
       <div class="bar-track"><div class="bar-fill" style="width:${confPct}%;background:linear-gradient(90deg,#00b4d8,#48bfe3);"></div></div>
     </div>
     <div class="stat-row">
       <div class="stat-head"><span class="stat-lbl">Priority</span><span class="pill ${priPill}">${priority}</span></div>
     </div>
     <div class="stat-row">
       <div class="stat-head"><span class="stat-lbl">Urgency Score</span><span class="stat-val">${urgPct}%</span></div>
       <div class="bar-track"><div class="bar-fill" style="width:${urgPct}%;background:${priColor};"></div></div>
     </div>
     <div class="stat-row">
       <div class="stat-head"><span class="stat-lbl">Location</span><span class="stat-val">${selectedBorough}${selectedZip?(' &bull; '+selectedZip):''}</span></div>
     </div>`;

  // Vendor
  const proximityPill = v => {
    if (v.zip === selectedZip)         return '<span class="pill pill-low">&#x2714; Same ZIP</span>';
    if (v.borough === selectedBorough) return `<span class="pill" style="background:rgba(0,180,216,.14);color:#00b4d8;border:1px solid rgba(0,180,216,.35)">Same borough</span>`;
    return `<span class="pill" style="background:rgba(136,153,170,.14);color:#8899aa;border:1px solid #334455">${v.borough}</span>`;
  };
  const distLabel = v => (v.dist!=null && v.dist<9999) ? `${v.dist.toFixed(1)} mi` : '';
  const moreHtml = moreVendors.map(v => {
    const m = (v.zip===selectedZip) ? '&#x2714; Same ZIP'
            : (v.borough===selectedBorough ? 'Same borough' : v.borough);
    return `<div class="sim-row" style="margin-bottom:6px">
              <div style="display:flex;justify-content:space-between;gap:10px;align-items:flex-start">
                <div style="flex:1;min-width:0">
                  <div style="font-weight:600;font-size:0.82rem;color:#e0e0e0;line-height:1.3;margin-bottom:3px">${v.name}</div>
                  <div style="font-size:0.72rem;color:#8899aa">${v.phone||'No phone'} &bull; ${m} &bull; ${v.zip}</div>
                </div>
                <div style="text-align:right;font-size:0.78rem;color:#2ec4b6;font-weight:700;white-space:nowrap">${distLabel(v)}</div>
              </div>
            </div>`;
  }).join('');
  document.getElementById('vendorBody').innerHTML =
    `<div class="vendor-hero">
       <div class="vname">${topVendor.name}</div>
       <div class="vline"><span class="ico">&#x1F4DE;</span><span>${topVendor.phone||'No phone listed'}</span></div>
       ${topVendor.email ? `<div class="vline"><span class="ico">&#x2709;&#xFE0F;</span><span>${topVendor.email}</span></div>` : ''}
       <div class="vline"><span class="ico">&#x1F4CD;</span><span>${topVendor.address}</span></div>
       ${topVendor.license ? `<div class="vline"><span class="ico">&#x1F4DC;</span><span>NYC License #${topVendor.license}</span></div>` : ''}
       <div style="margin-top:10px">${proximityPill(topVendor)}</div>
     </div>
     <div class="vendor-dist">
       <div>
         <div class="stat-lbl">Distance to Site</div>
         <div class="num">${distLabel(topVendor)||'&mdash;'}</div>
       </div>
       <div class="sub">${distLabel(topVendor) ? 'Driving distance via<br>Google Directions' : 'Distance unknown'}</div>
     </div>
     ${moreHtml ? `<details class="more-vendors" style="margin-top:14px"><summary>&#x25BC; ${moreVendors.length} more nearby vendors</summary><div style="margin-top:10px">${moreHtml}</div></details>` : ''}`;

  // Similar
  document.getElementById('similarBody').innerHTML = similar.map(c => {
    let res;
    if (c.status==='Closed' && c.resolution) res = `<span class="pill pill-low">Closed ${c.resolution}d</span>`;
    else if (c.status==='Pending')           res = `<span class="pill pill-medium">Pending</span>`;
    else                                     res = `<span class="pill pill-high">Still Open</span>`;
    const simPct = Math.round(c.sim*100);
    const livePill = c.live ? '<span class="live-pill">&#x1F7E2; LIVE</span>' : '';
    return `<div class="sim-row">
      <div class="sim-row-head"><span>${c.id} &bull; ${c.dateStr} ${livePill}</span>${res}</div>
      <div class="sim-row-tags"><span class="tag tag-type">${c.type}</span><span class="tag" style="background:rgba(136,153,170,.15);color:#c8d8e8">${c.borough}</span></div>
      <div class="sim-row-addr">&#x1F4CD; ${c.address}${c.zip?', '+c.zip:''}</div>
      <div class="sim-row-foot">
        <div class="sim-row-bar"><div class="bar-track"><div class="bar-fill" style="width:${simPct}%;background:linear-gradient(90deg,#8ab4f8,#00b4d8);"></div></div></div>
        <span class="stat-val accent" style="font-size:0.78rem;white-space:nowrap">${simPct}% match</span>
      </div>
    </div>`;
  }).join('');

  // Cost
  document.getElementById('costBody').innerHTML = renderCost(selectedType);

  // Show results — fullscreen map + sidebar
  ['step1','step2','step3'].forEach(id => document.getElementById(id).classList.add('locked'));
  document.body.classList.add('results-active');
  document.getElementById('results').classList.add('fullscreen');
  // Ensure Google Maps picks up the new container size
  window.scrollTo({top:0});

  // Origin already resolved earlier (originLL). Build the map.
  try {
    await buildMap(originLL, similar, topVendor);
  } catch(mapErr) {
    console.error('Map build failed:', mapErr);
    document.getElementById('mapMeta').innerHTML =
      '<div style="color:#e63946;font-size:0.85rem">&#x26A0; Map unavailable (Google Maps API error). Check browser console — usually a referrer restriction on the API key when opening via file:// URL. Serve via http://127.0.0.1:8000 instead.</div>';
  }
  } catch(err) {
    console.error('Submit failed:', err);
    alert('Something went wrong while processing the complaint. Open the browser console (F12) for details.\\n\\n'+(err&&err.message?err.message:err));
  } finally {
    btn.disabled = false; btn.textContent = 'Submit Complaint \\u2192';
  }
}

// ================================================================
// WORK ORDER GENERATION (Claude via /api/generate-work-order)
// ================================================================
async function openWorkOrderModal(){
  console.log('[WO] openWorkOrderModal clicked, lastAssessment=', !!lastAssessment);
  if(!lastAssessment){
    alert('Submit a complaint first.');
    return;
  }
  const modal = document.getElementById('woModal');
  const body  = document.getElementById('woModalBody');
  const foot  = document.getElementById('woModalFoot');
  const title = document.getElementById('woModalTitle');
  // Make sure modal is attached to <body> so no ancestor transform/filter
  // breaks position:fixed. Safe to re-append even if already there.
  if (modal.parentNode !== document.body) document.body.appendChild(modal);
  modal.classList.add('show');
  modal.style.display = 'flex';
  // Force a repaint so the modal becomes visible even if some GPU layer
  // was stale (was the bug where it only appeared after F12 resize).
  void modal.offsetHeight;
  console.log('[WO] modal.show applied. computed display=', getComputedStyle(modal).display, 'z=', getComputedStyle(modal).zIndex);
  foot.style.display = 'none';
  title.textContent = 'Generating Work Order...';
  body.innerHTML = `<div class="wo-loading">
    <div class="wo-spinner"></div>
    <div style="font-size:0.88rem;color:#c8d8e8;margin-bottom:6px">Asking Claude to draft the dispatch order</div>
    <div style="font-size:0.76rem">Using ${lastAssessment.similar_past_orders.length} similar past complaints as examples...</div>
  </div>`;
  try {
    let resp, attempt = 0;
    while (true) {
      resp = await fetch('/api/generate-work-order', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(lastAssessment),
      });
      if (resp.status !== 503 || attempt >= 1) break;
      attempt++;
      body.innerHTML = `<div class="wo-loading">
        <div class="wo-spinner"></div>
        <div style="font-size:0.88rem;color:#c8d8e8;margin-bottom:6px">Claude is briefly overloaded &mdash; retrying...</div>
      </div>`;
      await new Promise(r=>setTimeout(r, 2500));
    }
    if (resp.status === 429) {
      throw new Error('Rate limit reached. Please wait a few minutes before generating another work order.');
    }
    if (!resp.ok) {
      let msg = 'Server returned ' + resp.status;
      try { const j = await resp.json(); if(j && j.error) msg = j.error; } catch(_){}
      throw new Error(msg);
    }
    const wo = await resp.json();
    lastWorkOrder = wo;
    renderWorkOrder(wo);
    title.textContent = 'Work Order Generated';
    foot.style.display = 'flex';
  } catch(err){
    console.error('Work order generation failed:', err);
    title.textContent = 'Generation Failed';
    body.innerHTML = `<div class="wo-error"><strong>Unable to generate work order.</strong><br><br>${(err&&err.message)||err}<br><br><span style="color:#8899aa;font-size:0.78rem">If this persists, check that the /api/generate-work-order endpoint is deployed and the ANTHROPIC_API_KEY env var is set.</span></div>`;
  }
}

function renderWorkOrder(wo){
  const body = document.getElementById('woModalBody');
  const field = (k,v) => v!=null && v!=='' ? `<div class="wo-field"><div class="k">${k}</div><div class="v">${v}</div></div>` : '';
  const idField = v => `<div class="wo-field"><div class="k">Work Order ID</div><div class="v id">${v||'—'}</div></div>`;
  body.innerHTML = `
    <div class="wo-grid">
      ${idField(wo.work_order_id)}
      ${field('Complaint ID', wo.complaint_id)}
      ${field('Complaint Type', wo.complaint_type)}
      ${field('Priority', wo.priority)}
      ${field('Address', wo.address)}
      ${field('Borough', wo.borough)}
      ${field('Reported', wo.reported_date)}
      ${field('Est. Days', wo.estimated_days_to_complete)}
      ${field('Assigned Vendor', wo.assigned_vendor)}
      ${field('Status', wo.status)}
    </div>
    ${wo.materials_needed ? `<div class="wo-section"><div class="wo-section-title">&#x1F527; Materials Needed</div><div class="wo-materials">${wo.materials_needed}</div></div>`:''}
    ${wo.instructions ? `<div class="wo-section"><div class="wo-section-title">&#x1F4CB; Instructions</div><div class="wo-block">${wo.instructions}</div></div>`:''}
    ${wo.safety_notes ? `<div class="wo-section"><div class="wo-section-title">&#x26A0;&#xFE0F; Safety Notes</div><div class="wo-block">${wo.safety_notes}</div></div>`:''}
  `;
}

function closeWorkOrderModal(){
  const m = document.getElementById('woModal');
  m.classList.remove('show');
  m.style.display = '';  // clear the inline style set in openWorkOrderModal
}

async function copyWorkOrderJson(){
  if(!lastWorkOrder) return;
  try {
    await navigator.clipboard.writeText(JSON.stringify(lastWorkOrder, null, 2));
    // visual feedback
    const btns = document.querySelectorAll('#woModalFoot .modal-btn');
    btns.forEach(b => { if(b.textContent.includes('Copy')){ const o=b.textContent; b.textContent='✓ Copied'; setTimeout(()=>b.textContent=o, 1400); } });
  } catch(e){ alert('Clipboard write failed: '+e.message); }
}

function downloadWorkOrderJson(){
  if(!lastWorkOrder) return;
  const blob = new Blob([JSON.stringify(lastWorkOrder, null, 2)], {type:'application/json'});
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = (lastWorkOrder.work_order_id||'work_order')+'.json';
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ================================================================
// RESET
// ================================================================
function resetForm(){
  selectedType=null; selectedZip=null; selectedBorough=null; complaintLatLng=null;
  lastAssessment=null; lastWorkOrder=null;
  const wm = document.getElementById('woModal');
  wm.classList.remove('show');
  wm.style.display = '';
  document.getElementById('boroughSelect').value='';
  document.getElementById('addrInput').value='';
  document.getElementById('detailsInput').value='';
  document.getElementById('geocodeStatus').textContent='';
  document.querySelectorAll('.type-btn').forEach(b=>b.classList.remove('selected'));
  document.getElementById('submitBtn').disabled=true;
  document.getElementById('results').classList.remove('fullscreen');
  document.getElementById('results').style.display='';
  document.body.classList.remove('results-active');
  document.getElementById('mapMeta').innerHTML='';
  document.getElementById('mapLegend').innerHTML='';
  ['step1','step2','step3'].forEach(id=>{
    const el=document.getElementById(id);
    el.classList.remove('locked','active');
  });
  document.getElementById('step1').classList.add('active');
  document.getElementById('step2').classList.add('locked');
  document.getElementById('step3').classList.add('locked');
  if(gMap){gMap=null;}
  window.scrollTo({top:0,behavior:'smooth'});
}
</script>
</body>
</html>"""

# Unescape Python format-string double-braces in a SINGLE pass.
# Using a while-loop here is wrong: it over-collapses runs of closing braces
# (e.g. `}}}}` should become `}}`, but a while loop reduces it to `}`),
# which silently drops the closing brace of @media blocks and breaks every
# CSS rule downstream until the next valid close.
html = html.replace("{{", "{").replace("}}", "}")

html = html.replace("__GOOGLE_KEY__", GOOGLE_KEY)
html = html.replace("__VENDORS_JS__", vendors_js)
html = html.replace("__BOROUGH_ZIPS_JS__", borough_zips_js)

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)
print("Done.", len(html), "chars /", round(len(html)/1024,1), "KB")
