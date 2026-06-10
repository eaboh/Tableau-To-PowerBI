"""Dump Where clauses from visuals with empty queryState on Observations page."""
import os, json, glob, re

pages_dir = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'
tmdl_dir = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.SemanticModel\definition\tables'

# Build model symbols
model_cols = {}
for tmdl in glob.glob(os.path.join(tmdl_dir, '*.tmdl')):
    table_name = os.path.splitext(os.path.basename(tmdl))[0]
    with open(tmdl, encoding='utf-8') as f:
        content = f.read()
    items = re.findall(r"\t(?:column|measure)\s+'([^']+(?:''[^']*)*)'", content, re.MULTILINE)
    items += re.findall(r'^\t(?:column|measure)\s+([A-Za-z_][A-Za-z0-9_ ]*?)(?:\s*=|\s*$)', content, re.MULTILINE)
    cleaned = set()
    for c in items:
        c = c.replace("''", "'")
        cleaned.add(c.strip())
    model_cols[table_name] = cleaned

# Check ALL visuals with Where clauses
obs_pages = ['ReportSection2794f1e7a8454c049b91', 'ReportSectiona7871d2101d74013aa2c']

for page in obs_pages:
    vdir = os.path.join(pages_dir, page, 'visuals')
    if not os.path.isdir(vdir):
        continue
    for vid in sorted(os.listdir(vdir)):
        vjson = os.path.join(vdir, vid, 'visual.json')
        if not os.path.exists(vjson):
            continue
        with open(vjson, encoding='utf-8') as f:
            content = f.read()
        if '"Where"' not in content:
            continue
        
        data = json.loads(content)
        vis = data.get('visual', {})
        vtype = vis.get('visualType', '?')
        q = vis.get('query', {})
        qs = q.get('queryState', {})
        
        # Find Where clauses recursively
        def find_where(obj, path=''):
            results = []
            if isinstance(obj, dict):
                if 'Where' in obj:
                    results.append((path, obj['Where']))
                for k, v in obj.items():
                    results.extend(find_where(v, f"{path}.{k}"))
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    results.extend(find_where(item, f"{path}[{i}]"))
            return results
        
        wheres = find_where(data)
        if wheres:
            print(f"\n=== {vid[:8]} ({vtype}) queryState={'empty' if not qs else 'has data'} ===")
            for path, where_content in wheres:
                print(f"  Path: {path}")
                print(f"  Where: {json.dumps(where_content, indent=2)[:600]}")
                
                # Check refs in Where clause
                refs = []
                def find_refs_in(obj):
                    if isinstance(obj, dict):
                        if 'Column' in obj:
                            col = obj['Column']
                            if isinstance(col, dict) and 'Expression' in col and 'Property' in col:
                                sr = col['Expression'].get('SourceRef', {})
                                if 'Entity' in sr:
                                    refs.append((sr['Entity'], col['Property'], 'Column'))
                                elif 'Source' in sr:
                                    refs.append(('SOURCE:' + sr['Source'], col['Property'], 'Column'))
                        for v in obj.values():
                            find_refs_in(v)
                    elif isinstance(obj, list):
                        for item in obj:
                            find_refs_in(item)
                
                find_refs_in(where_content)
                for entity, prop, kind in refs:
                    if entity.startswith('SOURCE:'):
                        print(f"    REF (Source): {entity}.{prop}")
                    elif entity in model_cols:
                        if prop in model_cols[entity]:
                            print(f"    REF OK: [{entity}].[{prop}]")
                        else:
                            print(f"    *** BROKEN: [{entity}].[{prop}] - column not found!")
                    else:
                        print(f"    *** BROKEN: [{entity}].[{prop}] - table not found!")
