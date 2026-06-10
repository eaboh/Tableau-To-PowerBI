"""Check why measures/columns are missing from the TMDL model."""
import json, os

extraction_dir = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\_extraction'

# Load extracted calculations
with open(os.path.join(extraction_dir, 'calculations.json'), encoding='utf-8') as f:
    calcs = json.load(f)

# Load extracted datasources
with open(os.path.join(extraction_dir, 'datasources.json'), encoding='utf-8') as f:
    datasources = json.load(f)

# Missing measures from the cross-ref script
missing_measures = [
    'Non conformes', 'N_1', 'N_3', 'N_4', 'N_7', 'Index', 'BOOL', 
    'A_9_2', 'Observations_par_confo_%_total', 'A_1 Date PAR',
    'Moy_N_3_Site', 'N_3 AT', 'N_3 EDF', 'N_7 EC CNEPE', 'N_7 EC DIPDE',
    'Obs eFeP - NC % A_1 Date PAR', 'PCT_OBs_AIP_Commentaires',
    'PS_IS_PFI_HORS_AAP', 'Ps - Adhérence aux procédures et DSI en cours de réalisation',
    'Inadequate (copie)', 'Inadequate PAR', 'FLT AIP 2', 'FLT AIP PAR',
    'Alerte_generale', 'Alerte_infobulle', 'Stats Prog Thème 3 + 6',
    '% Obs. prog. (3+6)', '0', 'Info',
    '% ou Nbr d\'appel - Domaine', '% ou Nbr d\'appel - Sous Domaine',
    'A_10_5 - Ps non AIP avec une observation AIP',
    'Utilisation du catalogue national Total',
]

# Missing columns
missing_columns = [
    'AAP_DSI_PAR', 'AT', 'A_10_1', 'A_9_3', 'BOOL A_9_3',
    'Date Signature Surveillant PAR', 'FLT AIP Indicateur nationaux',
    'FLT_Commentaire', 'ID', 'Lien Argos', 'PFI_HORS_AAP_PAR',
    'Type d\'affaire', 'Numéro d\'affaire',
    'FLT Ps date de modification PAR', 'Avancement PS',
    'D_10 - Ps à finaliser BOOL', 'Date Modification PAR',
    'FLT Plan Action (ENS)', 'Ps Id',
    'Ps observations réalisées (3 + 6) % ',
    'FLT Date Signature surveillant PAR', 'Observation Id',
    'Date signature surveillance PAR', 'Date Signature Surveillant PAR',
]

print("=== MISSING MEASURES: lookup in calculations.json ===")
calc_names = {c.get('name'): c for c in calcs}
for m in missing_measures:
    if m in calc_names:
        c = calc_names[m]
        print(f"  FOUND: [{m}] role={c.get('role')}, type={c.get('type')}, ds={c.get('datasource','?')[:40]}")
    else:
        print(f"  NOT FOUND: [{m}]")

print("\n=== MISSING COLUMNS: lookup in datasources ===")
all_ds_cols = {}
for ds in datasources:
    ds_name = ds.get('name', '?')
    for table in ds.get('tables', []):
        tbl_name = table.get('name', '?')
        for col in table.get('columns', []):
            col_name = col.get('name', '')
            all_ds_cols[col_name] = (ds_name, tbl_name)

for c in missing_columns:
    if c in all_ds_cols:
        ds_name, tbl_name = all_ds_cols[c]
        print(f"  FOUND: [{c}] in ds={ds_name[:30]}, table={tbl_name[:30]}")
    else:
        # Also check calcs (calc columns)
        if c in calc_names:
            cc = calc_names[c]
            print(f"  FOUND AS CALC: [{c}] role={cc.get('role')}, type={cc.get('type')}")
        else:
            print(f"  NOT FOUND: [{c}]")

print(f"\n=== Total calculations in extraction: {len(calcs)} ===")
print(f"=== Total datasources: {len(datasources)} ===")
for ds in datasources:
    total_cols = sum(len(t.get('columns', [])) for t in ds.get('tables', []))
    print(f"  DS '{ds.get('name','?')[:50]}': {len(ds.get('tables',[]))} tables, {total_cols} columns")
