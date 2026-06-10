"""Deep scan: check ALL In expressions anywhere in visual.json, page.json, report.json."""
import json
import os

base = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'
issues = []

def check_in_expr(obj, path, context):
    """Recursively look for In expressions and validate their structure."""
    if isinstance(obj, dict):
        if 'In' in obj:
            in_cond = obj['In']
            exprs = in_cond.get('Expressions', [])
            vals = in_cond.get('Values', [])
            # Check Expressions
            for i, e in enumerate(exprs):
                if not isinstance(e, dict):
                    issues.append(f'NON-DICT Expression[{i}]: {type(e).__name__}={repr(e)[:50]} in {context} at {path}')
                elif not e:
                    issues.append(f'EMPTY Expression[{i}] in {context} at {path}')
            # Check Values
            if not isinstance(vals, list):
                issues.append(f'Values not a list: {type(vals).__name__} in {context} at {path}')
            else:
                for i, row in enumerate(vals):
                    if not isinstance(row, list):
                        issues.append(f'Values[{i}] not a list: {type(row).__name__}={repr(row)[:80]} in {context} at {path}')
                    elif not row:
                        issues.append(f'EMPTY Values[{i}] (empty list) in {context} at {path}')
                    else:
                        for j, item in enumerate(row):
                            if not isinstance(item, dict):
                                issues.append(f'Values[{i}][{j}] not a dict: {type(item).__name__}={repr(item)[:50]} in {context} at {path}')
                            elif not item:
                                issues.append(f'EMPTY Values[{i}][{j}] (empty dict) in {context} at {path}')
                            elif 'Literal' not in item and 'Column' not in item and 'Measure' not in item:
                                issues.append(f'Values[{i}][{j}] unknown type: keys={list(item.keys())} in {context} at {path}')
        # Recurse
        for k, v in obj.items():
            check_in_expr(v, path + '.' + k, context)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            check_in_expr(v, path + f'[{i}]', context)

# Scan all visual.json and page.json files
for root, dirs, files in os.walk(base):
    for f in files:
        if f not in ('visual.json', 'page.json'):
            continue
        fp = os.path.join(root, f)
        parts = fp.replace(base, '').lstrip(os.sep)
        with open(fp, encoding='utf-8') as fh:
            data = json.load(fh)
        check_in_expr(data, f, parts)

# Also check report.json
report_json = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\report.json'
if os.path.exists(report_json):
    with open(report_json, encoding='utf-8') as fh:
        data = json.load(fh)
    check_in_expr(data, 'report.json', 'report.json')

if issues:
    for iss in issues:
        print(iss)
    print(f'\nTotal: {len(issues)}')
else:
    print('No structural issues found in any In expression')
    print('\n--- Dumping all Categorical filter patterns for manual review ---')
    count = 0
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
                count += 1
    print(f'Total Categorical filters: {count}')
