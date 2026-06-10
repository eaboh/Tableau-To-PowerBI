"""Dump the full JSON of the 4 Not-condition Categorical filters."""
import json
import os

base = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'

not_filters = []
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
            if flt.get('type') != 'Categorical':
                continue
            filt = flt.get('filter', {})
            where = filt.get('Where', [])
            for w in where:
                cond = w.get('Condition', {})
                if 'Not' in cond:
                    not_filters.append((flt, vid, page))

for flt, vid, page in not_filters:
    print(f'=== {flt["name"]} on {page}/{vid} ===')
    print(json.dumps(flt, indent=2))
    print()
