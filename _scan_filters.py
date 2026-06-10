"""Scan all visual.json files for malformed Categorical/In filter Values."""
import json
import os

base = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'
issues = []

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
            ftype = flt.get('type', '?')
            filt = flt.get('filter', {})
            where = filt.get('Where', [])
            for wi, w in enumerate(where):
                cond = w.get('Condition', {})
                # Check In conditions
                if 'In' in cond:
                    vals = cond['In'].get('Values', [])
                    for i, row in enumerate(vals):
                        for j, item in enumerate(row):
                            v = item.get('Literal', {}).get('Value', '')
                            # Check for unquoted values that are NOT boolean/numeric
                            if v and not v.startswith("'") and v not in ('true', 'false', 'null'):
                                try:
                                    float(v)
                                except ValueError:
                                    issues.append(f'BARE STRING: {repr(v)} in {fname} ({page}/{vid})')
            # Check field references
            field = flt.get('field', {})
            if not field:
                issues.append(f'NO FIELD: {fname} {ftype} ({page}/{vid})')
            elif 'Column' not in field and 'Measure' not in field:
                issues.append(f'BAD FIELD: {fname} keys={list(field.keys())} ({page}/{vid})')

# Also check page-level and report-level filters
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
            where = filt.get('Where', [])
            for wi, w in enumerate(where):
                cond = w.get('Condition', {})
                if 'In' in cond:
                    vals = cond['In'].get('Values', [])
                    for i, row in enumerate(vals):
                        for j, item in enumerate(row):
                            v = item.get('Literal', {}).get('Value', '')
                            if v and not v.startswith("'") and v not in ('true', 'false', 'null'):
                                try:
                                    float(v)
                                except ValueError:
                                    issues.append(f'PAGE BARE STRING: {repr(v)} in {fname} ({page})')

# Check report.json filters too
report_json = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\report.json'
if os.path.exists(report_json):
    with open(report_json, encoding='utf-8') as fh:
        data = json.load(fh)
    fc = data.get('filterConfig', {})
    for flt in fc.get('filters', []):
        fname = flt.get('name', '?')
        filt = flt.get('filter', {})
        where = filt.get('Where', [])
        for wi, w in enumerate(where):
            cond = w.get('Condition', {})
            if 'In' in cond:
                vals = cond['In'].get('Values', [])
                for i, row in enumerate(vals):
                    for j, item in enumerate(row):
                        v = item.get('Literal', {}).get('Value', '')
                        if v and not v.startswith("'") and v not in ('true', 'false', 'null'):
                            try:
                                float(v)
                            except ValueError:
                                issues.append(f'REPORT BARE STRING: {repr(v)} in {fname}')

if issues:
    for iss in issues[:40]:
        print(iss)
    print(f'\nTotal: {len(issues)}')
else:
    print('No obvious issues in In filter values')
    print('\n--- Checking for cross-table filter references (different Entity) ---')
    # The issue might be that a filter references a table not in the visual query
    for root, dirs, files in os.walk(base):
        for f in files:
            if f != 'visual.json':
                continue
            fp = os.path.join(root, f)
            vid = os.path.basename(os.path.dirname(fp))
            page = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(fp))))
            with open(fp, encoding='utf-8') as fh:
                data = json.load(fh)
            # Get query entities
            query_entities = set()
            queries = data.get('query', {})
            if isinstance(queries, dict):
                for cmd in queries.get('Commands', []):
                    sq = cmd.get('SemanticQueryDataShapeCommand', {}).get('Query', {})
                    for fr in sq.get('From', []):
                        query_entities.add(fr.get('Name', ''))
            # Check filter From entities
            fc = data.get('filterConfig', {})
            for flt in fc.get('filters', []):
                fname = flt.get('name', '?')
                filt = flt.get('filter', {})
                for fr in filt.get('From', []):
                    ent_name = fr.get('Name', '')
                    ent_entity = fr.get('Entity', '')
                    if ent_name and ent_name not in query_entities and query_entities:
                        print(f'  CROSS-TABLE: filter "{fname}" uses From[{ent_name}={ent_entity}] but query has {query_entities} ({page}/{vid})')
