"""Check if visual queryState includes From clause."""
import os, json

pages_dir = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'
obs_page = 'ReportSection2794f1e7a8454c049b91'
vdir = os.path.join(pages_dir, obs_page, 'visuals')

# Check visual 13e3975c (pieChart with queryState)
for d in os.listdir(vdir):
    if d.startswith('13e3975c'):
        vjson = os.path.join(vdir, d, 'visual.json')
        with open(vjson, encoding='utf-8') as f:
            data = json.load(f)
        vis = data.get('visual', {})
        q = vis.get('query', {})
        print("=== QUERY KEYS ===")
        print(list(q.keys()))
        print("\n=== FULL QUERY (queryState) ===")
        print(json.dumps(q.get('queryState', {}), indent=2)[:1500])
        print("\n=== FULL QUERY (other keys) ===")
        for k in q:
            if k != 'queryState':
                print(f"  {k}: {json.dumps(q[k], indent=2)[:500]}")
        print("\n=== filterConfig ===")
        fc = data.get('filterConfig', {})
        print(json.dumps(fc, indent=2)[:2000])
        break
