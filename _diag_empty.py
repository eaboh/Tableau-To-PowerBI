"""Diagnose empty visuals in UC80 migration output."""
import os
import json
import glob
from collections import Counter

ROOT = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'

empty = []
for vj in glob.glob(os.path.join(ROOT, '*', 'visuals', '*', 'visual.json')):
    with open(vj, encoding='utf-8') as fh:
        d = json.load(fh)
    v = d.get('visual') or {}
    vt = v.get('visualType') or ''
    if vt not in ('tableEx', 'scatterChart'):
        continue
    q = (v.get('query') or {}).get('queryState') or {}
    has = any(isinstance(rd, dict) and rd.get('projections') for rd in q.values())
    if has:
        continue
    page = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(vj))))
    title = ''
    try:
        title = v['visualContainerObjects']['title'][0]['properties']['text']['expr']['Literal']['Value']
    except Exception:
        pass
    pos = d.get('position') or {}
    empty.append({
        'vt': vt,
        'page': page,
        'title': title.strip("'\""),
        'w': pos.get('width'),
        'h': pos.get('height'),
        'name': os.path.basename(os.path.dirname(vj)),
    })

print(f'TOTAL EMPTY: {len(empty)}')
print()
titles = Counter(e['title'] for e in empty)
print('Top titles:')
for t, n in titles.most_common(20):
    print(f'  {n:3d}x  {t!r}')
print()
sizes = Counter((e['w'], e['h']) for e in empty)
print('Top sizes (w,h):')
for s, n in sizes.most_common(10):
    print(f'  {n:3d}x  {s}')
print()
# Show 5 examples of differing titles
seen_titles = set()
print('Examples (one per unique title):')
for e in empty:
    if e['title'] in seen_titles:
        continue
    seen_titles.add(e['title'])
    print(f'  {e["vt"]:14s} {e["page"][:30]:30s} title={e["title"]!r:40s} size=({e["w"]}x{e["h"]}) name={e["name"]}')
    if len(seen_titles) >= 25:
        break
