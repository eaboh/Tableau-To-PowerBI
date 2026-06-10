"""Find filter references to 'Date Signature Surveillant PAR' in UC80 visuals."""
import json
import os
import sys
import glob

sys.stdout.reconfigure(encoding='utf-8')

ROOT = (r'C:\Tableau to Power BI\PowerBI\UC80_new\UC80'
        r'\UC80.Report\definition')
target = 'Date Signature Surveillant PAR'

hits = []
for jf in glob.glob(os.path.join(ROOT, '**', '*.json'), recursive=True):
    with open(jf, 'r', encoding='utf-8') as f:
        try:
            j = json.load(f)
        except Exception:
            continue
    s = json.dumps(j)
    if target not in s:
        continue
    # extract filter refs
    def walk(obj, path=''):
        if isinstance(obj, dict):
            if 'Property' in obj and obj.get('Property') == target:
                kind = 'Measure' if 'Measure' in (path or '') else (
                    'Column' if 'Column' in (path or '') else '?')
                ent = obj.get('Expression', {}).get('SourceRef', {})
                hits.append({
                    'file': os.path.relpath(jf, ROOT),
                    'ref_kind': kind,
                    'entity': ent.get('Entity', '?'),
                    'path': path[:120],
                })
            for k, v in obj.items():
                walk(v, f'{path}.{k}')
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                walk(v, f'{path}[{i}]')
    walk(j)

# Group
from collections import Counter
kind_counts = Counter(h['ref_kind'] for h in hits)
print(f'Total references: {len(hits)}')
print(f'By kind: {dict(kind_counts)}')
# Sample first few
for h in hits[:8]:
    print(f"  {h['ref_kind']:8s} entity={h['entity']:42s} {h['file']}")
    print(f'      path={h["path"]}')
