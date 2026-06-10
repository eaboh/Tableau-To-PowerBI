"""Trace what happens to fields in D_10 - Ps en cours during generation."""
import sys
import os
sys.path.insert(0, 'tableau_export')
sys.path.insert(0, 'powerbi_import')

from extract_tableau_data import TableauExtractor

twbx = r'C:\Tableau to Power BI\Tableau\UC80.twbx'
ext = TableauExtractor(twbx, output_dir='_tmp_extract')
ext.extract_all()
import json
import os.path as P

# Load extracted worksheets
with open(P.join('_tmp_extract', 'worksheets.json'), encoding='utf-8') as fh:
    ws_list = json.load(fh)

# Find our targets
TARGETS = {'D_10 - Ps en cours', 'Date dernière MAJ - Observations',
           'Paramètre_erreur', 'Info_observation_eFep_droite',
           'Assistance_sollen', 'Ps en cours', 'Ps repris en écriture',
           'Observations dans la sélection national'}
print('Total worksheets extracted:', len(ws_list))
for ws in ws_list:
    if ws.get('name') not in TARGETS:
        continue
    print('=' * 60)
    print(f'NAME: {ws["name"]!r}')
    print(f'  chart_type: {ws.get("chart_type")!r}')
    print(f'  fields: {len(ws.get("fields", []))}')
    for f in ws.get('fields', []):
        print(f'    - {f}')
