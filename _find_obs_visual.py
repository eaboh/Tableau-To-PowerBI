"""Find the visual with Ps/Site/Trigram on Y-axis on Observations page."""
import os, json

pages_dir = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'
obs_page = 'ReportSection2794f1e7a8454c049b91'
vdir = os.path.join(pages_dir, obs_page, 'visuals')

for vid in sorted(os.listdir(vdir)):
    vjson = os.path.join(vdir, vid, 'visual.json')
    if not os.path.exists(vjson):
        continue
    with open(vjson, encoding='utf-8') as f:
        data = json.load(f)
    
    # Print summary of every visual on this page
    vis = data.get('visual', {})
    vtype = vis.get('visualType', '?')
    title_obj = vis.get('title', {})
    title = title_obj.get('text', '') if isinstance(title_obj, dict) else ''
    
    q = vis.get('query', {})
    qs = q.get('queryState', {})
    roles = list(qs.keys())
    
    # Collect queryRefs
    all_refs = []
    for role, role_data in qs.items():
        projs = role_data.get('projections', [])
        for p in projs:
            qr = p.get('queryRef', '')
            all_refs.append(f"{role}:{qr}")
    
    filters = data.get('filters', [])
    filter_refs = []
    for fi in filters:
        expr = fi.get('expression', {})
        for kind in ('Column', 'Measure'):
            ref = expr.get(kind)
            if ref:
                entity = ref.get('Expression', {}).get('SourceRef', {}).get('Entity', '')
                prop = ref.get('Property', '')
                filter_refs.append(f"{entity}.{prop}")
    
    print(f"{vid[:8]} | {vtype:30s} | {title[:40]:40s} | refs={all_refs[:3]} | filters={filter_refs[:3]}")
