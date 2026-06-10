"""Check ds calculations structure."""
import json
with open(r'_tmp_extract\datasources.json', encoding='utf-8') as fh:
    dss = json.load(fh)
print('Datasources:', len(dss))
for ds in dss:
    name = ds.get('name', '')
    calcs = ds.get('calculations', [])
    print(f'  {name!r}: {len(calcs)} calcs')
    for c in calcs[:3]:
        print(f'    raw={c.get("name")!r} caption={c.get("caption")!r}')
print()
print('Looking for Calculation_1146729079403888647...')
for ds in dss:
    for c in ds.get('calculations', []):
        if '1146729079403888647' in c.get('name', ''):
            print(f'  Found in ds {ds.get("name")!r}: caption={c.get("caption")!r}')
