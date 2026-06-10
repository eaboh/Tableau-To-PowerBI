"""Investigate broken filters on Observations - Suivi general page.
These visuals HAVE queries but still show broken filters in PBI Desktop."""
import os, json

pages_dir = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'
# Observations - Suivi general
obs_page = 'ReportSectionf2808a738dea49bbb2f0'
vdir = os.path.join(pages_dir, obs_page, 'visuals')

print("=== Observations - Suivi général ===\n")
for d in sorted(os.listdir(vdir)):
    vjson = os.path.join(vdir, d, 'visual.json')
    with open(vjson, encoding='utf-8') as f:
        data = json.load(f)
    vis = data.get('visual', {})
    has_q = 'query' in vis
    has_fc = 'filterConfig' in data
    vtype = vis.get('visualType', '?')
    num_fc = len(data.get('filterConfig', {}).get('filters', [])) if has_fc else 0
    # Get title
    title = ''
    vco = vis.get('visualContainerObjects', {})
    title_arr = vco.get('title', [])
    if title_arr:
        title = title_arr[0].get('properties', {}).get('text', {}).get('expr', {}).get('Literal', {}).get('Value', '')
        if title.startswith("'") and title.endswith("'"):
            title = title[1:-1]
    print(f"{d[:12]}  type={vtype:25s}  query={str(has_q):5s}  fc={num_fc:2d}  title={title[:60]}")
