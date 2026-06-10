"""Find which columns have boolean 'true' in their Categorical In filters."""
import json
import os

base = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'

true_filters = []
for root, dirs, files in os.walk(base):
    for f in files:
        if f != 'visual.json':
            continue
        fp = os.path.join(root, f)
        vid = os.path.basename(os.path.dirname(fp))
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
                in_cond = cond.get('In')
                if not in_cond:
                    continue
                vals = in_cond.get('Values', [])
                has_true = any(
                    item.get('Literal', {}).get('Value') == 'true'
                    for row in vals
                    for item in row
                )
                if has_true:
                    field = flt.get('field', {})
                    col = field.get('Column', {})
                    entity = col.get('Expression', {}).get('SourceRef', {}).get('Entity', '?')
                    prop = col.get('Property', '?')
                    true_filters.append((entity, prop, vid, flt.get('name')))

# Show unique entity.property combinations
from collections import Counter
col_counts = Counter((e, p) for e, p, _, _ in true_filters)
print(f'Filters with boolean true: {len(true_filters)}')
print(f'Unique columns: {len(col_counts)}')
for (entity, prop), count in col_counts.most_common():
    print(f'  {entity}.{prop}: {count} filters')

# Show one example
if true_filters:
    entity, prop, vid, fname = true_filters[0]
    print(f'\nExample: {fname} on {vid}')
    # Find and dump it
    for root, dirs, files in os.walk(base):
        for f in files:
            if f != 'visual.json':
                continue
            fp = os.path.join(root, f)
            if vid not in fp:
                continue
            with open(fp, encoding='utf-8') as fh:
                data = json.load(fh)
            fc = data.get('filterConfig', {})
            for flt in fc.get('filters', []):
                if flt.get('name') == fname:
                    print(json.dumps(flt, indent=2))
                    break
            break
