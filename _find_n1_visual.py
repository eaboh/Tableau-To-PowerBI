"""Find the visual with Y=Ps Site Trigram, X=N_1 on Indicateurs nationaux."""
import os, json

pages_dir = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'
page = 'ReportSection'  # Indicateurs nationaux
vdir = os.path.join(pages_dir, page, 'visuals')

for vid in sorted(os.listdir(vdir)):
    vjson = os.path.join(vdir, vid, 'visual.json')
    if not os.path.exists(vjson):
        continue
    with open(vjson, encoding='utf-8') as f:
        data = json.load(f)
    vis = data.get('visual', {})
    qs = vis.get('query', {}).get('queryState', {})
    
    # Check if this visual has N_1 in query
    has_n1 = False
    has_ps_site = False
    for role, role_data in qs.items():
        for proj in role_data.get('projections', []):
            qref = proj.get('queryRef', '')
            if 'N_1' in qref:
                has_n1 = True
            if 'Ps Site Trigram' in qref:
                has_ps_site = True
    
    if has_n1 and has_ps_site:
        print(f'FOUND: {vid}')
        print(f'Visual type: {vis.get("visualType")}')
        print()
        
        # Print query
        print('=== QUERY ===')
        for role, role_data in qs.items():
            for proj in role_data.get('projections', []):
                print(f'  {role}: {proj.get("queryRef", "")}')
        print()
        
        # Print all filters
        fc = data.get('filterConfig', {}).get('filters', [])
        print(f'=== FILTERS ({len(fc)}) ===')
        for i, fi in enumerate(fc):
            prop = ''
            entity = ''
            ftype = fi.get('type', '?')
            if 'Column' in fi.get('field', {}):
                prop = fi['field']['Column'].get('Property', '')
                entity = fi['field']['Column']['Expression']['SourceRef'].get('Entity', '')
            elif 'Measure' in fi.get('field', {}):
                prop = fi['field']['Measure'].get('Property', '')
                entity = fi['field']['Measure']['Expression']['SourceRef'].get('Entity', '')
            
            # Get filter values
            where = fi.get('filter', {}).get('Where', [])
            vals = []
            for w in where:
                cond = w.get('Condition', {})
                if 'In' in cond:
                    for vv in cond['In'].get('Values', []):
                        for lit in vv:
                            vals.append(lit.get('Literal', {}).get('Value', ''))
                elif 'Comparison' in cond:
                    right = cond['Comparison'].get('Right', {})
                    vals.append(f"CK={cond['Comparison'].get('ComparisonKind','?')} val={right.get('Literal', {}).get('Value', 'MISSING')}")
                elif 'Not' in cond:
                    inner = cond['Not'].get('Expression', {})
                    if 'Comparison' in inner:
                        right = inner['Comparison'].get('Right', {})
                        vals.append(f"NOT CK={inner['Comparison'].get('ComparisonKind','?')} val={right.get('Literal', {}).get('Value', 'MISSING')}")
            
            print(f'  [{i}] {entity}.{prop} (type={ftype})')
            print(f'      values: {vals}')
        print()
        print('=== FULL FILTER JSON ===')
        print(json.dumps(fc, indent=2))
        break
