"""Trace _field_map / _bim_sym for selected UC80 visuals."""
import sys
sys.path.insert(0, 'powerbi_import')
sys.path.insert(0, 'tableau_export')

import pbip_generator
_orig = pbip_generator.PowerBIProjectGenerator._build_visual_query
TARGETS = {'Paramètre_erreur', 'D_10 - Ps en cours',
           'Date dernière MAJ - Observations',
           'Info_observation_eFep_droite', 'Assistance_sollen',
           'Observations dans la sélection national',
           'Ps en cours', 'Ps repris en écriture'}

def _patched(self, ws_data):
    name = ws_data.get('name', '')
    if name in TARGETS:
        fields = ws_data.get('fields', [])
        _bim_sym = getattr(self, '_actual_bim_symbols', None) or set()
        print(f'\n>> {name!r}  raw_fields={len(fields)}  bim_syms={len(_bim_sym)}')
        fmap = getattr(self, '_field_map', {})
        for f in fields:
            raw = f.get('name', '')
            clean = self._clean_field_name(raw)
            ds = f.get('datasource', '')
            in_map = clean in fmap
            if in_map:
                resolved_entity, resolved_prop = fmap[clean]
            else:
                resolved_entity, resolved_prop = self._resolve_field_entity(clean, datasource=ds) if hasattr(self, '_resolve_field_entity') else (None, clean)
            in_bim = (resolved_entity, resolved_prop) in _bim_sym if _bim_sym else 'no-bim'
            print(f'   raw={raw!r}  clean={clean!r}  in_map={in_map}  resolved=({resolved_entity!r},{resolved_prop!r})  in_bim={in_bim}')
    return _orig(self, ws_data)

pbip_generator.PowerBIProjectGenerator._build_visual_query = _patched

import migrate
sys.argv = ['migrate.py', r'C:\Tableau to Power BI\Tableau\UC80.twbx',
            '--output-dir', r'_tmp_diag_uc80', '--no-optimize-dax', '--no-compare']
migrate.main()
