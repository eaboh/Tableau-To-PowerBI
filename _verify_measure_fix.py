"""Verify measure filters now use Advanced type with Comparison."""
import os, json

pages_dir = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'

measure_filters = []
for page in os.listdir(pages_dir):
    vdir = os.path.join(pages_dir, page, 'visuals')
    if not os.path.isdir(vdir):
        continue
    for d in os.listdir(vdir):
        vjson = os.path.join(vdir, d, 'visual.json')
        if not os.path.exists(vjson):
            continue
        with open(vjson, encoding='utf-8') as f:
            data = json.load(f)
        fc = data.get('filterConfig', {})
        for fi in fc.get('filters', []):
            if 'Measure' in fi.get('field', {}):
                measure_filters.append({
                    'page': page,
                    'visual': d[:12],
                    'type': fi.get('type'),
                    'measure': fi['field']['Measure']['Property'],
                    'has_comparison': any(
                        'Comparison' in str(w)
                        for w in fi.get('filter', {}).get('Where', [])
                    )
                })

print(f"Total measure filters: {len(measure_filters)}")
for mf in measure_filters[:15]:
    print(f"  {mf['visual']} | type={mf['type']:12s} | measure={mf['measure']:30s} | comparison={mf['has_comparison']}")
