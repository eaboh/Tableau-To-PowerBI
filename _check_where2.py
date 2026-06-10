"""Check visuals WITH queryState that have Where clauses - are those OK?"""
import os, json, glob

pages_dir = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'

# Check ALL visuals with Where clauses that DO have queryState
obs_pages = ['ReportSection2794f1e7a8454c049b91', 'ReportSectiona7871d2101d74013aa2c']

for page in obs_pages:
    vdir = os.path.join(pages_dir, page, 'visuals')
    if not os.path.isdir(vdir):
        continue
    for vid in sorted(os.listdir(vdir)):
        vjson = os.path.join(vdir, vid, 'visual.json')
        if not os.path.exists(vjson):
            continue
        with open(vjson, encoding='utf-8') as f:
            content = f.read()
        if '"Where"' not in content:
            continue
        
        data = json.loads(content)
        vis = data.get('visual', {})
        vtype = vis.get('visualType', '?')
        q = vis.get('query', {})
        qs = q.get('queryState', {})
        
        if not qs:
            continue  # Skip empty query visuals (these are the broken ones we fixed)
        
        # This visual HAS queryState AND has Where clauses
        # Check if it has From clause that defines source aliases
        fc = data.get('filterConfig', {})
        filters = fc.get('filters', [])
        
        print(f"\n=== {vid[:8]} ({vtype}) - has queryState ===")
        for fi in filters:
            where = fi.get('filter', {}).get('Where', fi.get('filter', []))
            if isinstance(where, list):
                for cond in where:
                    # Check Source refs in conditions
                    content_str = json.dumps(cond)
                    if '"Source"' in content_str:
                        # Extract source aliases used
                        import re
                        sources = re.findall(r'"Source":\s*"([^"]+)"', content_str)
                        print(f"  Filter uses Source aliases: {set(sources)}")
                        # Check if these aliases are defined in queryState
                        # In PBIR, the From clause is inside queryState entries
                        break
