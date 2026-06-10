"""Dump full filter JSON for cross-table parameter filters (Inadequate, AIP)."""
import json
import os

base = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'

found = 0
for root, dirs, files in os.walk(base):
    for f in files:
        if f != 'visual.json':
            continue
        fp = os.path.join(root, f)
        vid = os.path.basename(os.path.dirname(fp))
        page = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(fp))))
        with open(fp, encoding='utf-8') as fh:
            data = json.load(fh)
        fc = data.get('filterConfig', {})
        for flt in fc.get('filters', []):
            fname = flt.get('name', '?')
            # Look for filters involving Inadequate or AIP
            filt_str = json.dumps(flt)
            if 'Inadequate' in filt_str or 'AIP' in filt_str:
                if found < 3:
                    print(f'=== {fname} on {page}/{vid} ===')
                    print(json.dumps(flt, indent=2)[:2000])
                    print()
                found += 1

print(f'\nTotal filters involving Inadequate/AIP: {found}')

# Also let's check: is Fix 2 (Advanced/Comparison for measures) being applied?
print('\n--- All Advanced type filters ---')
adv_count = 0
for root, dirs, files in os.walk(base):
    for f in files:
        if f != 'visual.json':
            continue
        fp = os.path.join(root, f)
        with open(fp, encoding='utf-8') as fh:
            data = json.load(fh)
        fc = data.get('filterConfig', {})
        for flt in fc.get('filters', []):
            if flt.get('type') == 'Advanced':
                adv_count += 1
                if adv_count <= 3:
                    fname = flt.get('name', '?')
                    vid2 = os.path.basename(os.path.dirname(fp))
                    print(f'  Advanced: {fname} ({vid2})')
                    print(f'    {json.dumps(flt, indent=2)[:800]}')
                    print()

print(f'Total Advanced filters: {adv_count}')
