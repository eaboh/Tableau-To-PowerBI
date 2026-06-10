"""Investigate the 12 missing references in detail."""
import os, re, json

tmdl_dir = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.SemanticModel\definition\tables'
base = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'

# 1. Check table names with special chars
print("=== TMDL Table declarations with apostrophes ===")
for tmdl in sorted(os.listdir(tmdl_dir)):
    if not tmdl.endswith('.tmdl'):
        continue
    fpath = os.path.join(tmdl_dir, tmdl)
    with open(fpath, encoding='utf-8') as f:
        first_line = f.readline()
    m = re.match(r'^table\s+(.+)', first_line)
    if m:
        table_decl = m.group(1).strip()
        file_stem = tmdl[:-5]
        if "'" in table_decl or "'" in file_stem:
            print(f"  File: [{file_stem}]")
            print(f"  Decl: [{table_decl}]")
            print()

# 2. Check what columns exist in the affected tables
print("\n=== Checking specific tables for missing cols ===")
tables_to_check = {
    'sqlproxy': ['FLT AIP Indicateur nationaux', 'ID'],
    'sqlproxy (EDH_PROGRAMMES_SURVEILLANCES_UC80 (2))': ['Lien Argos', 'Ps Id', 'Ps observations réalisées (3 + 6) % '],
    'sqlproxy (EDH_UTILISATION_CATALOGUE_NATIONAL_D_UC80 (2))': ['Observation Id'],
    'sqlproxy (EDH_UTILISATION_CATALOGUE_NATIONAL_UC80 (2))': [],
    '[Surveillance IPE Historique]vision_domaine': ['Name'],
}

for table, cols_to_find in tables_to_check.items():
    tmdl_file = os.path.join(tmdl_dir, table + '.tmdl')
    if not os.path.exists(tmdl_file):
        print(f"  TABLE FILE NOT FOUND: [{table}]")
        continue
    with open(tmdl_file, encoding='utf-8') as f:
        content = f.read()
    # Find all column/measure names
    items = re.findall(r"^\t(?:column|measure)\s+'([^']+(?:''[^']*)*)'", content, re.MULTILINE)
    items += re.findall(r"^\t(?:column|measure)\s+([A-Za-z_][A-Za-z0-9_ ]*?)(?:\s*=|\s*$)", content, re.MULTILINE)
    names = set(i.replace("''", "'").strip() for i in items)
    for col in cols_to_find:
        if col in names:
            print(f"  [{table}].[{col}] -> EXISTS")
        else:
            # Try fuzzy match
            close = [n for n in names if col.lower() in n.lower() or n.lower() in col.lower()]
            print(f"  [{table}].[{col}] -> MISSING (close: {close[:3]})")

# 3. Check % ou Nombre d 'appel table
print("\n=== % ou Nombre d 'appel table ===")
appel_file = os.path.join(tmdl_dir, "% ou Nombre d 'appel.tmdl")
if os.path.exists(appel_file):
    with open(appel_file, encoding='utf-8') as f:
        content = f.read()
    items = re.findall(r"^\t(?:column|measure)\s+'([^']+(?:''[^']*)*)'", content, re.MULTILINE)
    items += re.findall(r"^\t(?:column|measure)\s+([A-Za-z_][A-Za-z0-9_ ]*?)(?:\s*=|\s*$)", content, re.MULTILINE)
    names = set(i.replace("''", "'").strip() for i in items)
    print(f"  Columns/measures: {names}")
    print(f"  Has 'Name': {'Name' in names}")
else:
    print(f"  FILE NOT FOUND: {appel_file}")

# 4. Check the visual reference to see exactly what entity name is used
print("\n=== Visual Entity reference for '% ou Nombre d' table ===")
import glob
for vj in glob.glob(os.path.join(base, '*', 'visuals', '*', 'visual.json')):
    with open(vj, encoding='utf-8') as f:
        txt = f.read()
    if "Nombre d" in txt and "appel" in txt:
        data = json.loads(txt)
        # Find the entity ref
        def find_entity(obj, depth=0):
            if isinstance(obj, dict):
                if 'Entity' in obj:
                    if "Nombre" in str(obj['Entity']):
                        print(f"  Entity value: [{obj['Entity']}]")
                        return
                for v in obj.values():
                    find_entity(v, depth+1)
            elif isinstance(obj, list):
                for item in obj:
                    find_entity(item, depth+1)
        find_entity(data)
        break
