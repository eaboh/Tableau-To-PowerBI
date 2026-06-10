"""Check if measure filter entities exist in TMDL and verify value formatting."""
import os, json, re

# 1. Get all table names from TMDL
tmdl_dir = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.SemanticModel\definition\tables'
tmdl_tables = set()
for f in os.listdir(tmdl_dir):
    if f.endswith('.tmdl'):
        tmdl_tables.add(f[:-5])  # strip .tmdl

# Also check model.tmdl for ref table entries
model_path = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.SemanticModel\definition\model.tmdl'
with open(model_path, encoding='utf-8') as f:
    for line in f:
        m = re.match(r"\s*ref table '?([^']+)'?", line)
        if m:
            tmdl_tables.add(m.group(1))

print(f'=== TMDL tables ({len(tmdl_tables)}) ===')
for t in sorted(tmdl_tables):
    print(f'  {t}')

# 2. Check measure filter entities 
print('\n=== Measure filter entities vs TMDL ===')
pages_dir = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'
measure_entities = set()
for page in sorted(os.listdir(pages_dir)):
    vdir = os.path.join(pages_dir, page, 'visuals')
    if not os.path.isdir(vdir):
        continue
    for vid in sorted(os.listdir(vdir)):
        vjson = os.path.join(vdir, vid, 'visual.json')
        if not os.path.exists(vjson):
            continue
        with open(vjson, encoding='utf-8') as f:
            data = json.load(f)
        fc = data.get('filterConfig', {}).get('filters', [])
        for fi in fc:
            if 'Measure' in fi.get('field', {}):
                entity = fi['field']['Measure']['Expression']['SourceRef'].get('Entity', '')
                prop = fi['field']['Measure'].get('Property', '')
                measure_entities.add((entity, prop))

for entity, prop in sorted(measure_entities):
    exists = entity in tmdl_tables
    print(f'  Entity="{entity}" Prop="{prop}" -> table_exists={exists}')

# 3. Check for the measure within the table
print('\n=== Checking measures exist in their tables ===')
for entity, prop in sorted(measure_entities):
    tmdl_file = os.path.join(tmdl_dir, f'{entity}.tmdl')
    if not os.path.exists(tmdl_file):
        print(f'  MISSING TABLE FILE: {entity}.tmdl')
        continue
    with open(tmdl_file, encoding='utf-8') as f:
        content = f.read()
    # Check for measure definition
    # Format: measure 'Prop Name' = or measure Prop = 
    escaped_prop = re.escape(prop)
    if re.search(rf"measure\s+'?{escaped_prop}'?\s*=", content) or re.search(rf"measure\s+'{re.escape(prop)}'\s*=", content):
        print(f'  OK: {entity}.{prop}')
    else:
        print(f'  MEASURE NOT FOUND: {entity}.{prop}')
        # Show what measures exist in that table
        measures = re.findall(r"measure\s+'([^']+)'|measure\s+(\w+)\s*=", content)
        print(f'    Available measures: {[m[0] or m[1] for m in measures[:10]]}')
