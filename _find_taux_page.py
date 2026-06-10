"""Find page with 'Taux de réalisation' visuals and N_1 field."""
import os, json

pages_dir = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'

for page in sorted(os.listdir(pages_dir)):
    vdir = os.path.join(pages_dir, page, 'visuals')
    if not os.path.isdir(vdir):
        continue
    for vid in sorted(os.listdir(vdir)):
        vjson = os.path.join(vdir, vid, 'visual.json')
        if not os.path.exists(vjson):
            continue
        with open(vjson, encoding='utf-8') as f:
            data = json.load(f)
        vis = data.get('visual', {})
        title_obj = vis.get('visualContainerObjects', {}).get('title', [{}])
        title = ''
        if title_obj:
            title = title_obj[0].get('properties', {}).get('text', {}).get('expr', {}).get('Literal', {}).get('Value', '')
            title = title.strip("'")
        if 'Taux' in title and 'alisation' in title:
            # Get page name
            pjson = os.path.join(pages_dir, page, 'page.json')
            pname = ''
            if os.path.exists(pjson):
                with open(pjson, encoding='utf-8') as f:
                    pname = json.load(f).get('displayName', '')
            print(f'PAGE: {pname} ({page})')
            print(f'  Visual: {vid[:12]} | {vis.get("visualType","?")} | {title[:80]}')
            # Check query for N_1
            qs = vis.get('query', {}).get('queryState', {})
            for role, role_data in qs.items():
                for proj in role_data.get('projections', []):
                    qref = proj.get('queryRef', '')
                    if 'N_1' in qref or 'N1' in qref:
                        print(f'    QUERY has N_1: {role} -> {qref}')
            # Check filters
            fc = data.get('filterConfig', {}).get('filters', [])
            if fc:
                for fi in fc:
                    prop = ''
                    if 'Column' in fi.get('field', {}):
                        prop = fi['field']['Column'].get('Property', '')
                    elif 'Measure' in fi.get('field', {}):
                        prop = fi['field']['Measure'].get('Property', '')
                    print(f'    FILTER: {prop} (type={fi.get("type","?")})')
            print()
