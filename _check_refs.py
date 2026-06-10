"""Cross-reference visual column/measure refs against TMDL model."""
import os, glob, re, json, sys

# Build model schema
tmdl_dir = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.SemanticModel\definition\tables'
model_cols = {}
for tmdl in glob.glob(os.path.join(tmdl_dir, '*.tmdl')):
    table_name = os.path.splitext(os.path.basename(tmdl))[0]
    with open(tmdl, encoding='utf-8') as f:
        content = f.read()
    # Match column/measure names - they may be quoted with ' or unquoted
    # Format: \tcolumn 'Name' or \tcolumn Name or \tmeasure 'Name' = expr
    items = re.findall(r"^\t(?:column|measure)\s+'([^']+(?:''[^']*)*)'", content, re.MULTILINE)
    # Also unquoted names (no = sign for columns, = for measures)
    items += re.findall(r"^\t(?:column|measure)\s+([A-Za-z_][A-Za-z0-9_ ]*?)(?:\s*=|\s*$)", content, re.MULTILINE)
    cleaned = set()
    for c in items:
        # Unescape TMDL apostrophes
        c = c.replace("''", "'")
        cleaned.add(c.strip())
    model_cols[table_name] = cleaned

def find_refs(obj, refs):
    if isinstance(obj, dict):
        if 'Column' in obj:
            col = obj['Column']
            if isinstance(col, dict) and 'Expression' in col and 'Property' in col:
                sr = col['Expression'].get('SourceRef', {})
                # Skip SourceRef with "Source" (bound alias from Where clause)
                if 'Entity' in sr:
                    entity = sr['Entity']
                    prop = col['Property']
                    refs.add((entity, prop, 'Column'))
        if 'Measure' in obj:
            meas = obj['Measure']
            if isinstance(meas, dict) and 'Expression' in meas and 'Property' in meas:
                sr = meas['Expression'].get('SourceRef', {})
                if 'Entity' in sr:
                    entity = sr['Entity']
                    prop = meas['Property']
                    refs.add((entity, prop, 'Measure'))
        for v in obj.values():
            find_refs(v, refs)
    elif isinstance(obj, list):
        for item in obj:
            find_refs(item, refs)

# Scan all visuals
base = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'
all_refs = set()
for vj in glob.glob(os.path.join(base, '*', 'visuals', '*', 'visual.json')):
    with open(vj, encoding='utf-8') as f:
        data = json.load(f)
    find_refs(data, all_refs)

# Also check report.json
rj = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\report.json'
if os.path.exists(rj):
    with open(rj, encoding='utf-8') as f:
        data = json.load(f)
    find_refs(data, all_refs)

# Check which refs are missing
print(f"Total unique refs: {len(all_refs)}")
missing_count = 0
for entity, prop, kind in sorted(all_refs):
    if entity in model_cols:
        if prop not in model_cols[entity]:
            print(f'MISSING {kind}: [{entity}] -> [{prop}]')
            missing_count += 1
    else:
        print(f'MISSING TABLE: [{entity}] (referenced [{prop}])')
        missing_count += 1

print(f"\nTotal missing: {missing_count}")
