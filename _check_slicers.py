"""Check slicer visuals and their objects/filter expressions."""
import json
import os

base = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'

# Find all slicers and dump their structure
slicers = []
all_visuals = []
for root, dirs, files in os.walk(base):
    for f in files:
        if f != 'visual.json':
            continue
        fp = os.path.join(root, f)
        with open(fp, encoding='utf-8') as fh:
            data = json.load(fh)
        vtype = data.get('visual', {}).get('visualType', '')
        vid = os.path.basename(os.path.dirname(fp))
        page = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(fp))))
        all_visuals.append((vtype, vid, page))
        if vtype == 'slicer':
            slicers.append((fp, data, vid, page))

print(f'Total visuals: {len(all_visuals)}')
print(f'Slicers: {len(slicers)}')

# Check visual types
from collections import Counter
type_counts = Counter(v[0] for v in all_visuals)
for t, c in type_counts.most_common():
    print(f'  {t}: {c}')

print('\n--- Slicer details ---')
for fp, data, vid, page in slicers:
    visual = data.get('visual', {})
    objects = visual.get('objects', {})
    print(f'\nSlicer {vid} on {page}')
    print(f'  Objects keys: {list(objects.keys())}')
    # Check for any filter/expression in objects
    for obj_key, obj_val in objects.items():
        if isinstance(obj_val, list):
            for item in obj_val:
                props = item.get('properties', {})
                for pk, pv in props.items():
                    if isinstance(pv, dict) and 'expr' in pv:
                        expr = pv['expr']
                        print(f'  {obj_key}.{pk} has expr: {list(expr.keys()) if isinstance(expr, dict) else type(expr).__name__}')

# Also check if any visual has query with a Where clause containing In
print('\n\n--- Visuals with query Where clauses ---')
for root, dirs, files in os.walk(base):
    for f in files:
        if f != 'visual.json':
            continue
        fp = os.path.join(root, f)
        with open(fp, encoding='utf-8') as fh:
            data = json.load(fh)
        vid = os.path.basename(os.path.dirname(fp))
        query = data.get('query', {})
        if not query:
            continue
        for cmd in query.get('Commands', []):
            sq = cmd.get('SemanticQueryDataShapeCommand', {}).get('Query', {})
            where = sq.get('Where', [])
            if where:
                for w in where:
                    cond = w.get('Condition', {})
                    if 'In' in cond:
                        in_c = cond['In']
                        vals = in_c.get('Values', [])
                        print(f'  Query Where In: {vid} - {len(vals)} values')
                        # Show first value for inspection
                        if vals:
                            print(f'    First value: {json.dumps(vals[0])[:100]}')
