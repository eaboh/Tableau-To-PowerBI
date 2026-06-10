"""Inspect filters on 'Pilotage des Ps' page."""
import os, json

pages_dir = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'
page = 'ReportSection53fd3257aa4a44ae96a3'  # Pilotage des Ps
vdir = os.path.join(pages_dir, page, 'visuals')

for vid in sorted(os.listdir(vdir)):
    vjson = os.path.join(vdir, vid, 'visual.json')
    if not os.path.exists(vjson):
        continue
    with open(vjson, encoding='utf-8') as f:
        data = json.load(f)
    vis = data.get('visual', {})
    vtype = vis.get('visualType', '?')
    has_q = 'query' in vis
    fc = data.get('filterConfig', {}).get('filters', [])
    title_obj = vis.get('visualContainerObjects', {}).get('title', [{}])
    title = '?'
    if title_obj:
        title = title_obj[0].get('properties', {}).get('text', {}).get('expr', {}).get('Literal', {}).get('Value', '?')
        title = title.strip("'")[:60]

    if fc:
        filter_names = []
        for fi in fc:
            prop = ''
            ftype = fi.get('type', '?')
            if 'Column' in fi.get('field', {}):
                prop = fi['field']['Column'].get('Property', '')
            elif 'Measure' in fi.get('field', {}):
                prop = fi['field']['Measure'].get('Property', '')
            filter_names.append(f'{prop}({ftype})')
        print(f'{vid[:12]} | {vtype:20s} | q={has_q!s:5s} | {title[:50]}')
        print(f'  filters: {filter_names}')
        print()
