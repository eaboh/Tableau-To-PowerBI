"""Deep inspect D_10 - Ps en cours worksheet to see all its content."""
import zipfile
import xml.etree.ElementTree as ET

twbx = r'C:\Tableau to Power BI\Tableau\UC80.twbx'
with zipfile.ZipFile(twbx) as z:
    twb_name = next(n for n in z.namelist() if n.endswith('.twb'))
    with z.open(twb_name) as fh:
        tree = ET.parse(fh)
root = tree.getroot()

TARGETS = {'D_10 - Ps en cours', 'Date dernière MAJ - Observations', 'Paramètre_erreur',
           'Info_observation_eFep_droite', 'Assistance_sollen'}
for ws in root.iter('worksheet'):
    name = ws.get('name', '')
    if name not in TARGETS:
        continue
    print('=' * 60)
    print(f'WS: {name!r}')
    print('=' * 60)
    # Dump all <encodings> child elements
    for enc in ws.findall('.//encodings'):
        for child in enc:
            attrs = {k: v[:80] for k, v in child.attrib.items()}
            print(f'  encodings/{child.tag}  attrs={attrs}')
    # Dump <slices>
    slices = ws.find('.//slices')
    if slices is not None:
        for ch in slices:
            print(f'  slices/{ch.tag}  text={(ch.text or "").strip()[:100]!r}')
    # Dump datasource-dependencies col-instances 
    for dep in ws.findall('.//datasource-dependencies'):
        ds = dep.get('datasource', '')
        cols = dep.findall('column')
        cis = dep.findall('column-instance')
        print(f'  ds-dep ds={ds!r}: {len(cols)} columns, {len(cis)} col-instances')
        for ci in cis:
            print(f'    ci col={ci.get("column")!r} deriv={ci.get("derivation")!r} type={ci.get("type")!r}')
    # Marks/style
    mark = ws.find('.//mark')
    if mark is not None:
        print(f'  mark class={mark.get("class")!r}')
