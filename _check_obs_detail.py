"""Dump full visual.json content of empty scatter charts + check obs NC page."""
import os, json, glob

pages_dir = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'

# 1. Full content of first empty scatterChart
obs_page = 'ReportSection2794f1e7a8454c049b91'
vdir = os.path.join(pages_dir, obs_page, 'visuals')
for d in sorted(os.listdir(vdir)):
    if d.startswith('067e00a2'):
        vjson = os.path.join(vdir, d, 'visual.json')
        with open(vjson, encoding='utf-8') as f:
            data = json.load(f)
        print("=== 067e00a2 (scatterChart) FULL ===")
        print(json.dumps(data, indent=2)[:3000])
        break

# 2. Check second Observations page
obs2 = 'ReportSectiona7871d2101d74013aa2c'
pjson = os.path.join(pages_dir, obs2, 'page.json')
with open(pjson, encoding='utf-8') as f:
    pdata = json.load(f)
print(f"\n=== PAGE FILTERS for '{pdata.get('displayName', '')}' ({len(pdata.get('filters', []))}) ===")
for fi in pdata.get('filters', []):
    print(json.dumps(fi, indent=2)[:400])
    print("---")

# 3. List visuals on second Observations page
vdir2 = os.path.join(pages_dir, obs2, 'visuals')
print(f"\n=== VISUALS on Observations NC ===")
for vid in sorted(os.listdir(vdir2)):
    vjson = os.path.join(vdir2, vid, 'visual.json')
    if not os.path.exists(vjson):
        continue
    with open(vjson, encoding='utf-8') as f:
        data = json.load(f)
    vis = data.get('visual', {})
    vtype = vis.get('visualType', '?')
    q = vis.get('query', {})
    qs = q.get('queryState', {})
    roles = list(qs.keys())
    refs = []
    for role, rd in qs.items():
        for p in rd.get('projections', []):
            refs.append(f"{role}:{p.get('queryRef', '')}")
    filters = data.get('filters', [])
    print(f"  {vid[:8]} | {vtype:25s} | roles={roles} | refs={refs[:3]} | filters={len(filters)}")
