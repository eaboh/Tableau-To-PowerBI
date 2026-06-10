"""Check page-level filters AND visuals with empty queryState on Observations page."""
import os, json

pages_dir = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'
obs_page = 'ReportSection2794f1e7a8454c049b91'

# 1. Page-level filters
pjson = os.path.join(pages_dir, obs_page, 'page.json')
with open(pjson, encoding='utf-8') as f:
    pdata = json.load(f)

page_filters = pdata.get('filters', [])
print(f"=== PAGE FILTERS ({len(page_filters)}) ===")
for fi in page_filters:
    print(json.dumps(fi, indent=2)[:500])
    print("---")

# 2. Check scatter charts with empty refs
vdir = os.path.join(pages_dir, obs_page, 'visuals')
print("\n=== SCATTER CHARTS (full query/filters) ===")
for vid in ['067e00a2f7a04f57aab8', '11538c04f7a04f57aab8', 'fa3d07b0']:
    # Find actual dir starting with this prefix
    for d in os.listdir(vdir):
        if d.startswith(vid[:8]):
            vjson = os.path.join(vdir, d, 'visual.json')
            if os.path.exists(vjson):
                with open(vjson, encoding='utf-8') as f:
                    data = json.load(f)
                vis = data.get('visual', {})
                vtype = vis.get('visualType', '')
                query = vis.get('query', {})
                filters = data.get('filters', [])
                print(f"\n--- {d[:12]} ({vtype}) ---")
                print(f"  query keys: {list(query.keys())}")
                qs = query.get('queryState', {})
                print(f"  queryState roles: {list(qs.keys())}")
                for role, rd in qs.items():
                    projs = rd.get('projections', [])
                    print(f"    {role}: {json.dumps(projs)[:200]}")
                if filters:
                    print(f"  filters: {json.dumps(filters)[:300]}")
                # Also check visual-level vcObjects
                vco = vis.get('vcObjects', {})
                if vco:
                    print(f"  vcObjects keys: {list(vco.keys())[:10]}")
