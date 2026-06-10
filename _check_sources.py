"""Check for SourceRef.Source vs From[].Name mismatches in filters."""
import json
import os

base = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'
issues = []

def find_source_refs(obj, found):
    """Find all SourceRef.Source values in an expression tree."""
    if isinstance(obj, dict):
        if 'SourceRef' in obj:
            src = obj['SourceRef'].get('Source')
            if src:
                found.add(src)
        for v in obj.values():
            find_source_refs(v, found)
    elif isinstance(obj, list):
        for v in obj:
            find_source_refs(v, found)

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
            filt = flt.get('filter', {})
            from_entries = filt.get('From', [])
            from_names = {fr.get('Name') for fr in from_entries}
            
            # Find all SourceRef.Source in the Where clause
            where = filt.get('Where', [])
            source_refs = set()
            find_source_refs(where, source_refs)
            
            # Check for mismatches
            for src in source_refs:
                if src not in from_names:
                    issues.append(f'MISMATCH: filter "{fname}" uses Source="{src}" but From only has {from_names} ({page}/{vid})')

# Also check report-level filters
report_json = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\report.json'
if os.path.exists(report_json):
    with open(report_json, encoding='utf-8') as fh:
        data = json.load(fh)
    fc = data.get('filterConfig', {})
    for flt in fc.get('filters', []):
        fname = flt.get('name', '?')
        filt = flt.get('filter', {})
        from_entries = filt.get('From', [])
        from_names = {fr.get('Name') for fr in from_entries}
        where = filt.get('Where', [])
        source_refs = set()
        find_source_refs(where, source_refs)
        for src in source_refs:
            if src not in from_names:
                issues.append(f'REPORT MISMATCH: filter "{fname}" uses Source="{src}" but From only has {from_names}')

# Check page-level filters
for root, dirs, files in os.walk(base):
    for f in files:
        if f != 'page.json':
            continue
        fp = os.path.join(root, f)
        page = os.path.basename(os.path.dirname(fp))
        with open(fp, encoding='utf-8') as fh:
            data = json.load(fh)
        fc = data.get('filterConfig', {})
        for flt in fc.get('filters', []):
            fname = flt.get('name', '?')
            filt = flt.get('filter', {})
            from_entries = filt.get('From', [])
            from_names = {fr.get('Name') for fr in from_entries}
            where = filt.get('Where', [])
            source_refs = set()
            find_source_refs(where, source_refs)
            for src in source_refs:
                if src not in from_names:
                    issues.append(f'PAGE MISMATCH: filter "{fname}" uses Source="{src}" but From only has {from_names} ({page})')

if issues:
    for iss in issues[:40]:
        print(iss)
    print(f'\nTotal: {len(issues)}')
else:
    print('No SourceRef.Source / From[].Name mismatches found')
    
    # Let me try another angle - check if any filter Value contains a single-quoted empty string
    print('\n--- Checking for potential problematic literal values ---')
    problem_vals = []
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
                fname = flt.get('name', '?')
                filt = flt.get('filter', {})
                where = filt.get('Where', [])
                for w in where:
                    cond = w.get('Condition', {})
                    if 'In' in cond:
                        vals = cond['In'].get('Values', [])
                        for row in vals:
                            for item in row:
                                v = item.get('Literal', {}).get('Value', '')
                                if v == "''":
                                    problem_vals.append(f"  EMPTY STRING literal '' in {fname} ({vid})")
                                elif v == 'null':
                                    problem_vals.append(f"  NULL literal in {fname} ({vid})")
    if problem_vals:
        for pv in problem_vals[:20]:
            print(pv)
        print(f'  Total: {len(problem_vals)}')
    else:
        print('  No empty string or null literals found')
