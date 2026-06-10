"""Detailed reference check - shows visual paths for broken refs."""
import os, glob, json, re

base = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'

def find_refs(obj, refs, path=''):
    if isinstance(obj, dict):
        if 'Column' in obj:
            col = obj['Column']
            if isinstance(col, dict) and 'Expression' in col and 'Property' in col:
                sr = col['Expression'].get('SourceRef', {})
                if 'Entity' in sr:
                    refs.append((sr['Entity'], col['Property'], 'Column', path))
        if 'Measure' in obj:
            meas = obj['Measure']
            if isinstance(meas, dict) and 'Expression' in meas and 'Property' in meas:
                sr = meas['Expression'].get('SourceRef', {})
                if 'Entity' in sr:
                    refs.append((sr['Entity'], meas['Property'], 'Measure', path))
        for k, v in obj.items():
            find_refs(v, refs, path + '.' + k)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            find_refs(item, refs, path + '[' + str(i) + ']')

tmdl_dir = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.SemanticModel\definition\tables'
model_cols = {}
for tmdl in glob.glob(os.path.join(tmdl_dir, '*.tmdl')):
    table_name = os.path.splitext(os.path.basename(tmdl))[0]
    with open(tmdl, encoding='utf-8') as f:
        content = f.read()
    items = re.findall(r"^\t(?:column|measure)\s+'([^']+(?:''[^']*)*)'", content, re.MULTILINE)
    items += re.findall(r'^\t(?:column|measure)\s+([A-Za-z_][A-Za-z0-9_ ]*?)(?:\s*=|\s*$)', content, re.MULTILINE)
    cleaned = set()
    for c in items:
        c = c.replace("''", "'")
        cleaned.add(c.strip())
    model_cols[table_name] = cleaned

for vj in glob.glob(os.path.join(base, '*', 'visuals', '*', 'visual.json')):
    with open(vj, encoding='utf-8') as f:
        data = json.load(f)
    refs = []
    find_refs(data, refs)
    for entity, prop, kind, path in refs:
        missing = False
        if entity in model_cols:
            if prop not in model_cols[entity]:
                missing = True
        else:
            missing = True
        if missing:
            page = vj.split(os.sep)[-4]
            vid = vj.split(os.sep)[-2]
            print(f'{page}/{vid[:8]} [{entity}].[{prop}] ({kind}) {path}')
