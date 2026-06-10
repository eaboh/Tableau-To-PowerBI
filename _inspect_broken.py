"""Deep inspect a bar chart with filters on Observations - Suivi general.
Check if the visual query's From clause matches the filter's From."""
import os, json

pages_dir = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'
obs_page = 'ReportSectionf2808a738dea49bbb2f0'
vdir = os.path.join(pages_dir, obs_page, 'visuals')

# Check visual 29010f5185be (clusteredBarChart, 4 filters, title "Observations")
target = '29010f5185be'
for d in os.listdir(vdir):
    if d.startswith(target):
        vjson = os.path.join(vdir, d, 'visual.json')
        with open(vjson, encoding='utf-8') as f:
            data = json.load(f)
        vis = data.get('visual', {})
        q = vis.get('query', {})
        
        print("=== QUERY ===")
        print(json.dumps(q, indent=2))
        
        print("\n=== FILTER CONFIG ===")
        fc = data.get('filterConfig', {})
        print(json.dumps(fc, indent=2)[:4000])
        break
