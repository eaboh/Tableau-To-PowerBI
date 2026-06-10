"""Find WHERE each missing ref appears: filterConfig or queryState."""
import json, os, glob

base = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'

# Props to search for (unique enough)
search_props = [
    'FLT AIP Indicateur nationaux',
    'Lien Argos',
    'Ps Id',
    'Observation Id',
    'Index()',
    "Show % (Indicateur Nat) - Domaine ",
]

# Also check for the apostrophe table issue
found_apostrophe = False
found_surveillance = False

for vj in sorted(glob.glob(os.path.join(base, '*', 'visuals', '*', 'visual.json'))):
    with open(vj, encoding='utf-8') as f:
        txt = f.read()
    
    page = vj.split(os.sep)[-4]
    vid = vj.split(os.sep)[-2]
    
    # Check for the apostrophe escaping issue
    if "Nombre d ''" in txt and not found_apostrophe:
        data = json.loads(txt)
        in_filter = "Nombre d ''" in json.dumps(data.get('filterConfig', {}))
        in_query = "Nombre d ''" in json.dumps(data.get('visual', {}).get('query', {}))
        loc = []
        if in_filter: loc.append('filterConfig')
        if in_query: loc.append('queryState')
        print(f"{page}/{vid}: [% ou Nombre d ''appel].[Name] in {loc}")
        found_apostrophe = True
    
    # Check for [Surveillance IPE Historique]vision_domaine.Name
    if 'vision_domaine' in txt and 'Name' in txt and not found_surveillance:
        data = json.loads(txt)
        query_str = json.dumps(data.get('visual', {}).get('query', {}))
        filter_str = json.dumps(data.get('filterConfig', {}))
        if 'vision_domaine' in query_str:
            print(f"{page}/{vid}: [Surveillance IPE Historique]vision_domaine.[Name] in ['queryState']")
            found_surveillance = True
        elif 'vision_domaine' in filter_str:
            print(f"{page}/{vid}: [Surveillance IPE Historique]vision_domaine.[Name] in ['filterConfig']")
            found_surveillance = True
    
    for prop in search_props:
        if prop in txt:
            data = json.loads(txt)
            in_filter = prop in json.dumps(data.get('filterConfig', {}))
            in_query = prop in json.dumps(data.get('visual', {}).get('query', {}))
            loc = []
            if in_filter: loc.append('filterConfig')
            if in_query: loc.append('queryState')
            if loc:
                print(f"{page}/{vid}: [{prop}] in {loc}")

# Also check: "ID" specifically (it's common, need exact match)
print("\n=== Checking 'ID' column reference ===")
for vj in sorted(glob.glob(os.path.join(base, '*', 'visuals', '*', 'visual.json'))):
    with open(vj, encoding='utf-8') as f:
        data = json.load(f)
    # Look for exact "Property": "ID" with Entity "sqlproxy"
    txt = json.dumps(data)
    if '"Property": "ID"' in txt and '"Entity": "sqlproxy"' in txt:
        page = vj.split(os.sep)[-4]
        vid = vj.split(os.sep)[-2]
        in_filter = '"Property": "ID"' in json.dumps(data.get('filterConfig', {}))
        in_query = '"Property": "ID"' in json.dumps(data.get('visual', {}).get('query', {}))
        loc = []
        if in_filter: loc.append('filterConfig')
        if in_query: loc.append('queryState')
        print(f"  {page}/{vid}: [sqlproxy].[ID] in {loc}")
        break

# Check the "0" and "Index" measures
print("\n=== Checking '0' and 'Index' measures ===")
for vj in sorted(glob.glob(os.path.join(base, '*', 'visuals', '*', 'visual.json'))):
    with open(vj, encoding='utf-8') as f:
        data = json.load(f)
    txt = json.dumps(data)
    if '"Property": "0"' in txt:
        page = vj.split(os.sep)[-4]
        vid = vj.split(os.sep)[-2]
        print(f"  {page}/{vid}: measure '0'")
        break

for vj in sorted(glob.glob(os.path.join(base, '*', 'visuals', '*', 'visual.json'))):
    with open(vj, encoding='utf-8') as f:
        data = json.load(f)
    txt = json.dumps(data)
    entity = 'sqlproxy (EDH_PROGRAMMES_SURVEILLANCES_UC80 (2))'
    if '"Property": "Index"' in txt and entity in txt:
        page = vj.split(os.sep)[-4]
        vid = vj.split(os.sep)[-2]
        in_filter = '"Property": "Index"' in json.dumps(data.get('filterConfig', {}))
        in_query = '"Property": "Index"' in json.dumps(data.get('visual', {}).get('query', {}))
        loc = []
        if in_filter: loc.append('filterConfig')
        if in_query: loc.append('queryState')
        print(f"  {page}/{vid}: [{entity}].[Index] in {loc}")
        break

# Check trailing space issue
print("\n=== Trailing space in column names ===")
for vj in sorted(glob.glob(os.path.join(base, '*', 'visuals', '*', 'visual.json'))):
    with open(vj, encoding='utf-8') as f:
        txt = f.read()
    if 'Ps observations' in txt:
        page = vj.split(os.sep)[-4]
        vid = vj.split(os.sep)[-2]
        # Extract the exact property value
        import re
        m = re.search(r'"Property":\s*"(Ps observations[^"]*)"', txt)
        if m:
            print(f"  {page}/{vid}: Property=[{m.group(1)}] (len={len(m.group(1))})")
            break
