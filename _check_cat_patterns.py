"""Check Categorical filters for unusual patterns: Not wrappers, Measure fields, etc."""
import json
import os

base = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'
issues = []

# Check all categorical filters
cat_patterns = {}
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
            fname = flt.get('name', '?')
            
            # Check field type
            field = flt.get('field', {})
            field_type = list(field.keys())[0] if field else 'NONE'
            if field_type not in ('Column',):
                issues.append(f'NON-COLUMN field: {field_type} in {fname} ({vid})')
            
            # Check for Not/In patterns
            filt = flt.get('filter', {})
            where = filt.get('Where', [])
            for w in where:
                cond = w.get('Condition', {})
                cond_type = list(cond.keys())[0] if cond else 'NONE'
                cat_patterns[cond_type] = cat_patterns.get(cond_type, 0) + 1
                if cond_type == 'Not':
                    # Check what's inside
                    not_expr = cond['Not']
                    inner_keys = list(not_expr.keys()) if isinstance(not_expr, dict) else []
                    issues.append(f'NOT condition: inner={inner_keys} in {fname} ({vid})')
                elif cond_type != 'In':
                    issues.append(f'UNEXPECTED condition type: {cond_type} in {fname} ({vid})')
            
            # Check isExclude
            if flt.get('isExclude'):
                issues.append(f'isExclude=true: {fname} ({vid})')
            
            # Check howCreated
            hc = flt.get('howCreated')
            if hc:
                issues.append(f'howCreated={hc}: {fname} ({vid})')

print('Categorical condition patterns:', cat_patterns)
print()

if issues:
    for iss in issues[:40]:
        print(iss)
    print(f'\nTotal issues: {len(issues)}')
else:
    print('All Categorical filters look standard')

# One more check - look at the FULL JSON of ANY filter that PBI might have trouble with
# Let me check if there are filters with Column.Property that doesn't match any table column
print('\n\n--- All unique Column.Property values in Categorical filters ---')
props = set()
for root, dirs, files in os.walk(base):
    for f in files:
        if f != 'visual.json':
            continue
        fp = os.path.join(root, f)
        with open(fp, encoding='utf-8') as fh:
            data = json.load(fh)
        fc = data.get('filterConfig', {})
        for flt in fc.get('filters', []):
            if flt.get('type') != 'Categorical':
                continue
            field = flt.get('field', {})
            col = field.get('Column', {})
            prop = col.get('Property', '')
            entity = col.get('Expression', {}).get('SourceRef', {}).get('Entity', '')
            if prop:
                props.add(f'{entity}.{prop}')
                
for p in sorted(props):
    print(f'  {p}')
print(f'  Total unique: {len(props)}')
