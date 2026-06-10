"""Quick summary of Observations page visuals after fix."""
import os, json

pages_dir = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'
obs_page = 'ReportSection890ca70bd19946a28e2f'
vdir = os.path.join(pages_dir, obs_page, 'visuals')

for d in sorted(os.listdir(vdir)):
    vjson = os.path.join(vdir, d, 'visual.json')
    with open(vjson, encoding='utf-8') as f:
        data = json.load(f)
    vis = data.get('visual', {})
    has_q = 'query' in vis
    has_fc = 'filterConfig' in data
    vtype = vis.get('visualType', '?')
    num_fc = len(data.get('filterConfig', {}).get('filters', [])) if has_fc else 0
    print(f"{d[:12]}  type={vtype:25s}  query={str(has_q):5s}  fc_filters={num_fc}")
