"""Inspect UC80 source worksheets that became empty visuals."""
import zipfile
import xml.etree.ElementTree as ET

twbx = r'C:\Tableau to Power BI\Tableau\UC80.twbx'
with zipfile.ZipFile(twbx) as z:
    twb_name = next(n for n in z.namelist() if n.endswith('.twb'))
    with z.open(twb_name) as fh:
        tree = ET.parse(fh)
root = tree.getroot()

TARGETS = [
    'Parametre_erreur', 'Paramètre_erreur', 'Paramètre_erreur_icone',
    'Assistance_sollen', 'info_blanche',
    'Date dernière MAJ - Observations',
    'Ps repris en écriture', 'Ps en cours',
    'Observations dans la sélection national',
    'Info_observation_eFep',
    'D_2 - Obs prog',
]

for ws in root.iter('worksheet'):
    name = ws.get('name', '')
    if not any(t.lower() in name.lower() for t in TARGETS):
        continue
    rows_elem = ws.find('.//rows')
    cols_elem = ws.find('.//cols')
    rows = (rows_elem.text or '').strip() if rows_elem is not None else ''
    cols = (cols_elem.text or '').strip() if cols_elem is not None else ''
    marks = ws.findall('.//mark')
    mark_class = marks[0].get('class', '') if marks else ''
    col_instances = ws.findall('.//datasource-dependencies/column-instance')
    encs = ws.findall('.//pane/encodings/encoding')
    slices = ws.findall('.//slices/column')
    print(f'--- {name!r}')
    print(f'  rows={rows[:120]!r}')
    print(f'  cols={cols[:120]!r}')
    print(f'  mark={mark_class}  encodings={len(encs)}  col-instances={len(col_instances)}  slices={len(slices)}')
    for ci in col_instances[:5]:
        print(f'    col-inst col={ci.get("column")!r} name={ci.get("name")!r} type={ci.get("type")!r}')
    for enc in encs[:5]:
        print(f'    enc attr={enc.get("attr")!r} column={enc.get("column")!r} type={enc.get("type")!r}')
    for sl in slices[:5]:
        print(f'    slice text={(sl.text or "").strip()[:80]!r}')
