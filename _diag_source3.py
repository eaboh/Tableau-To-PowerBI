"""Inspect D_10 - Ps en cours source XML in detail."""
import os, zipfile, xml.etree.ElementTree as ET

src = r'C:\Tableau to Power BI\Tableau\UC80.twbx'
with zipfile.ZipFile(src) as z:
    twb_name = [n for n in z.namelist() if n.endswith('.twb')][0]
    with z.open(twb_name) as fh:
        tree = ET.parse(fh)
root = tree.getroot()

TARGETS = ['D_10 - Ps en cours', 'Ps en cours', 'Ps repris en écriture', 'Assistance_sollen', 'D_2 - Obs prog v2 (2)']

for ws in root.findall('.//worksheet'):
    name = ws.get('name', '')
    if name not in TARGETS:
        continue
    print(f'\n==== {name} ====')
    # Print mark type
    panes = ws.findall('.//panes/pane')
    for p in panes:
        mark = p.find('mark')
        if mark is not None:
            print(f'  mark class = {mark.get("class")!r}')
    # Show table cols/rows
    for tag in ('cols', 'rows'):
        elem = ws.find(f'./table/{tag}')
        if elem is not None and elem.text:
            print(f'  table/{tag}: {elem.text.strip()!r}')
    # Show encodings
    encs = ws.findall('.//encodings')
    for enc in encs:
        for child in list(enc):
            print(f'  encoding/{child.tag}: column={child.get("column")!r}')
    # Show slices
    slices = ws.findall('.//slices/column')
    print(f'  slices: {len(slices)}')
    for s in slices[:20]:
        print(f'    slice: {s.text!r}')
    # Show column-instances
    cis = ws.findall('.//datasource-dependencies/column-instance')
    print(f'  column-instances: {len(cis)}')
    for ci in cis[:25]:
        print(f'    ci: column={ci.get("column")!r}  derivation={ci.get("derivation")!r}  type={ci.get("type")!r}  pivot={ci.get("pivot")!r}')
    # Show columns marked as measure
    cols = ws.findall('.//datasource-dependencies/column')
    print(f'  ds-deps/columns: {len(cols)}')
    for c in cols[:10]:
        print(f'    col: name={c.get("name")!r} role={c.get("role")!r} caption={c.get("caption")!r}')
