"""Check full filterConfig of empty-query visuals on Observations page."""
import os, json

pages_dir = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'
obs_page = 'ReportSectiona7871d2101d74013aa2c'  # Observations NC
vdir = os.path.join(pages_dir, obs_page, 'visuals')

# Check visual 05b5721b (table with empty queryState)
for d in os.listdir(vdir):
    if d.startswith('05b5721b'):
        vjson = os.path.join(vdir, d, 'visual.json')
        with open(vjson, encoding='utf-8') as f:
            data = json.load(f)
        vis = data.get('visual', {})
        q = vis.get('query', {})
        print("=== 05b5721b (table, empty query) ===")
        print(f"query keys: {list(q.keys())}")
        fc = data.get('filterConfig', {})
        filters = fc.get('filters', [])
        print(f"Num filters: {len(filters)}")
        for i, fi in enumerate(filters[:3]):
            print(f"\n--- Filter {i} ---")
            print(json.dumps(fi, indent=2)[:600])
        break
