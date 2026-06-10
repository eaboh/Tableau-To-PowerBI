"""Find visual with N_1 on X-axis and Ps Site Trigram on Y-axis (from screenshot).
Also look for visuals with measure-type filters."""
import os, json

pages_dir = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'

# Check both Observations pages
for obs_page in ['ReportSectionf2808a738dea49bbb2f0', 'ReportSection890ca70bd19946a28e2f']:
    vdir = os.path.join(pages_dir, obs_page, 'visuals')
    if not os.path.isdir(vdir):
        continue
    print(f"\n=== Page: {obs_page} ===")
    for d in sorted(os.listdir(vdir)):
        vjson = os.path.join(vdir, d, 'visual.json')
        with open(vjson, encoding='utf-8') as f:
            data = json.load(f)
        vis = data.get('visual', {})
        fc = data.get('filterConfig', {})
        filters = fc.get('filters', [])
        if not filters:
            continue
        # Check for measure filters with Categorical type
        measure_cat_filters = []
        for fi in filters:
            is_measure = 'Measure' in fi.get('field', {})
            ftype = fi.get('type', '')
            if is_measure:
                measure_cat_filters.append(f"{fi.get('field',{}).get('Measure',{}).get('Property','?')} (type={ftype})")
        if measure_cat_filters:
            title = ''
            vco = vis.get('visualContainerObjects', {})
            title_arr = vco.get('title', [])
            if title_arr:
                title = title_arr[0].get('properties', {}).get('text', {}).get('expr', {}).get('Literal', {}).get('Value', '')
                if title.startswith("'") and title.endswith("'"):
                    title = title[1:-1]
            print(f"\n  {d[:12]} ({vis.get('visualType','?')}): {title[:50]}")
            print(f"    MEASURE FILTERS: {measure_cat_filters}")
