"""Show one corrected measure filter JSON."""
import os, json

pages_dir = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'
# Find a visual with measure filters
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
        fc = data.get('filterConfig', {}).get('filters', [])
        for fi in fc:
            if 'Measure' in fi.get('field', {}):
                print(f"=== {page}/{d[:12]} ===")
                print(json.dumps(fi, indent=2))
                print()
                # Show just the first one
                exit()
