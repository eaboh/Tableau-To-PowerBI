"""Trace _actual_bim_symbols filtering for empty visuals."""
import sys
import os
sys.path.insert(0, 'tableau_export')
sys.path.insert(0, 'powerbi_import')

from extract_tableau_data import TableauExtractor
from import_to_powerbi import import_tableau_to_powerbi

twbx = r'C:\Tableau to Power BI\Tableau\UC80.twbx'
out = '_tmp_uc80_diag'

# Run full pipeline but intercept
ext = TableauExtractor(twbx, output_dir=out)
ext.extract_all()

# Now manually invoke the PBIP generator
import json
with open(os.path.join(out, 'worksheets.json'), encoding='utf-8') as fh:
    ws_list = json.load(fh)
with open(os.path.join(out, 'datasources.json'), encoding='utf-8') as fh:
    ds_list = json.load(fh)
with open(os.path.join(out, 'calculations.json'), encoding='utf-8') as fh:
    calc_list = json.load(fh)
with open(os.path.join(out, 'parameters.json'), encoding='utf-8') as fh:
    params = json.load(fh)
with open(os.path.join(out, 'dashboards.json'), encoding='utf-8') as fh:
    dashboards = json.load(fh)

# Build BIM via tmdl_generator
from tmdl_generator import TMDLGenerator
import io, contextlib
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    tmdl = TMDLGenerator(
        datasources=ds_list,
        calculations=calc_list,
        parameters=params,
        worksheets=ws_list,
        output_dir=os.path.join(out, 'UC80'),
    )
    bim = tmdl.generate()
# Inspect what's in bim
print('Tables:', [t.get('name') for t in bim.get('model', {}).get('tables', [])][:20])
# Look for Calculation_xxx and 'Ps Id' references
for t in bim.get('model', {}).get('tables', []):
    tname = t.get('name', '')
    cols = [c.get('name', '') for c in t.get('columns', []) if c.get('name')]
    meas = [m.get('name', '') for m in t.get('measures', []) if m.get('name')]
    # Look for our missing fields
    for needle in ('Ps Id', 'Date Maj', 'ID', 'Calculation_388154018214371328',
                    'Calculation_1146729079403888647', 'Calculation_1373597908919267330'):
        if needle in cols:
            print(f'  COLUMN {needle!r} -> table {tname!r}')
        if needle in meas:
            print(f'  MEASURE {needle!r} -> table {tname!r}')
