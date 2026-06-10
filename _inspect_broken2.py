"""Full dump of a visual with many filters on Observations - Suivi general.
Looking at visual 294b718c36b4 (pieChart, 6 filters) for N_1/range filter."""
import os, json

pages_dir = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'
obs_page = 'ReportSectionf2808a738dea49bbb2f0'
vdir = os.path.join(pages_dir, obs_page, 'visuals')

# The screenshot shows a selected visual with N_1 on X-axis and Y-axis = Ps Site Trigram
# That's likely a bar chart. Let's check 9ceebb026ba4 (clusteredBarChart, 4 filters)
target = '9ceebb026ba4'
for d in os.listdir(vdir):
    if d.startswith(target):
        vjson = os.path.join(vdir, d, 'visual.json')
        with open(vjson, encoding='utf-8') as f:
            data = json.load(f)
        vis = data.get('visual', {})
        q = vis.get('query', {})
        fc = data.get('filterConfig', {})
        
        print("=== VISUAL TYPE ===")
        print(vis.get('visualType'))
        
        print("\n=== QUERY (full) ===")
        print(json.dumps(q, indent=2))
        
        print("\n=== FILTER CONFIG (all filters) ===")
        for i, fi in enumerate(fc.get('filters', [])):
            print(f"\n--- Filter {i}: {fi.get('name')} (type={fi.get('type')}) ---")
            print(f"  field: {json.dumps(fi.get('field', {}))}")
            filt = fi.get('filter', {})
            print(f"  filter.From: {json.dumps(filt.get('From', []))}")
            where = filt.get('Where', [])
            print(f"  filter.Where: {json.dumps(where, indent=4)[:800]}")
        break
