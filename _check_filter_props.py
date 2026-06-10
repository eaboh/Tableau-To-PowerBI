"""Verify filter field/property combinations exist in the correct TMDL tables."""
import os, json, re

tmdl_dir = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.SemanticModel\definition\tables'
pages_dir = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'

# Build per-table column map from TMDL
table_columns = {}
for f in os.listdir(tmdl_dir):
    if not f.endswith('.tmdl'):
        continue
    filepath = os.path.join(tmdl_dir, f)
    with open(filepath, encoding='utf-8') as fh:
        content = fh.read()
    # Get table name from first line
    m = re.match(r"table\s+'([^']+(?:''[^']*)*)'|table\s+(\S+)", content)
    if not m:
        continue
    table_name = (m.group(1) or m.group(2)).replace("''", "'")
    # Extract columns and measures
    cols = set()
    for cm in re.finditer(r"\t(?:column|measure)\s+'([^']+(?:''[^']*)*)'", content):
        cols.add(cm.group(1).replace("''", "'"))
    for cm in re.finditer(r"\t(?:column|measure)\s+([A-Za-z_]\w*)", content):
        cols.add(cm.group(1))
    table_columns[table_name] = cols

print(f"Loaded {len(table_columns)} tables from TMDL\n")

# Now scan ALL filterConfig across all visuals and check Entity+Property
broken = []
total_filters = 0

for page in os.listdir(pages_dir):
    vdir = os.path.join(pages_dir, page, 'visuals')
    if not os.path.isdir(vdir):
        continue
    for vis_id in os.listdir(vdir):
        vjpath = os.path.join(vdir, vis_id, 'visual.json')
        if not os.path.exists(vjpath):
            continue
        with open(vjpath, encoding='utf-8') as fh:
            data = json.load(fh)
        fc = data.get('filterConfig', {})
        for fi in fc.get('filters', []):
            total_filters += 1
            # Check field.Column.Expression.SourceRef.Entity + field.Column.Property
            field = fi.get('field', {})
            col = field.get('Column', {})
            entity = col.get('Expression', {}).get('SourceRef', {}).get('Entity', '')
            prop = col.get('Property', '')
            if entity and prop:
                if entity not in table_columns:
                    broken.append((page, vis_id, fi.get('name',''), f"Entity not found: '{entity}'"))
                elif prop not in table_columns[entity]:
                    broken.append((page, vis_id, fi.get('name',''), f"Property '{prop}' not in table '{entity}'"))

print(f"Total filters checked: {total_filters}")
print(f"Broken: {len(broken)}")
for b in broken[:30]:
    print(f"  {b[0]}/{b[1]}: {b[2]} → {b[3]}")
