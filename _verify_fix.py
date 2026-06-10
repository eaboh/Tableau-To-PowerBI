"""Verify no visuals without query have filterConfig after fix."""
import os, json

pages_dir = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'
issues = []
total_visuals = 0
empty_query_with_fc = 0

for page in os.listdir(pages_dir):
    vdir = os.path.join(pages_dir, page, 'visuals')
    if not os.path.isdir(vdir):
        continue
    for vis_id in os.listdir(vdir):
        vjpath = os.path.join(vdir, vis_id, 'visual.json')
        if not os.path.exists(vjpath):
            continue
        total_visuals += 1
        with open(vjpath, encoding='utf-8') as f:
            data = json.load(f)
        vis = data.get('visual', {})
        has_query = 'query' in vis
        has_fc = 'filterConfig' in data
        if not has_query and has_fc:
            empty_query_with_fc += 1
            issues.append((page, vis_id, vis.get('visualType', '?'), len(data['filterConfig'].get('filters', []))))

print(f"Total visuals: {total_visuals}")
print(f"Empty-query visuals WITH filterConfig: {empty_query_with_fc}")
if issues:
    for i in issues[:20]:
        print(f"  {i[0]}/{i[1]} ({i[2]}): {i[3]} filters")
else:
    print("  NONE - fix is working!")
