"""Dump full JSON of tables with empty refs AND look for non-standard filter structures."""
import os, json, glob

pages_dir = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'

# Check ALL visuals that are NOT textbox/image but have empty queryState
print("=== VISUALS WITH EMPTY QUERY (non-textbox/image) ===\n")
for pj in sorted(glob.glob(os.path.join(pages_dir, '*/page.json'))):
    page_dir = os.path.dirname(pj)
    with open(pj, encoding='utf-8') as f:
        pdata = json.load(f)
    page_name = pdata.get('displayName', '')
    
    vdir = os.path.join(page_dir, 'visuals')
    if not os.path.isdir(vdir):
        continue
    
    for vid in sorted(os.listdir(vdir)):
        vjson = os.path.join(vdir, vid, 'visual.json')
        if not os.path.exists(vjson):
            continue
        with open(vjson, encoding='utf-8') as f:
            data = json.load(f)
        vis = data.get('visual', {})
        vtype = vis.get('visualType', '?')
        if vtype in ('textbox', 'image', 'shape', 'actionButton'):
            continue
        
        q = vis.get('query', {})
        qs = q.get('queryState', {})
        if qs:
            continue  # Has data bindings, skip
        
        # This is a data visual with no query - potential problem
        title_obj = vis.get('visualContainerObjects', {}).get('title', [])
        title = ''
        if title_obj:
            for t in title_obj:
                props = t.get('properties', {})
                text = props.get('text', {}).get('expr', {}).get('Literal', {}).get('Value', '')
                if text:
                    title = text.strip("'")
        
        print(f"  [{page_name}] {vid[:8]} | {vtype} | title='{title}'")
        
        # Check for any remaining structures
        if q:
            print(f"    query keys: {list(q.keys())}")
        obj = vis.get('objects', {})
        if obj:
            print(f"    objects keys: {list(obj.keys())[:5]}")
        vco = vis.get('visualContainerObjects', {})
        if vco:
            vco_keys = [k for k in vco.keys() if k != 'title']
            if vco_keys:
                print(f"    vcObjects (non-title): {vco_keys}")
        filt = data.get('filters', [])
        if filt:
            print(f"    HAS FILTERS: {len(filt)}")
            print(f"    {json.dumps(filt)[:300]}")

# Also check for visual.json files with "filter" key inside visual object
print("\n\n=== CHECK FOR NESTED FILTER STRUCTURES ===")
for vjson in sorted(glob.glob(os.path.join(pages_dir, '*/visuals/*/visual.json'))):
    with open(vjson, encoding='utf-8') as f:
        content = f.read()
    # Quick check for filter-related keys
    if '"filterConfig"' in content or '"defaultFilter"' in content or '"Where"' in content:
        vid = vjson.split(os.sep)[-2][:8]
        data = json.loads(content)
        print(f"  {vid}: has filter-related key")
        # Find Where clauses
        if '"Where"' in content:
            print(f"    Contains 'Where' clause")
