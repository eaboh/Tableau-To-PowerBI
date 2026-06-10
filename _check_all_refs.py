"""Comprehensive reference check - visual, page, and report level filters."""
import os, glob, json, re

base = r'C:\Tableau to Power BI\PowerBI\UC80\UC80'
tmdl_dir = os.path.join(base, 'UC80.SemanticModel', 'definition', 'tables')
report_dir = os.path.join(base, 'UC80.Report', 'definition')

# Build model symbols
model_cols = {}
for tmdl in glob.glob(os.path.join(tmdl_dir, '*.tmdl')):
    table_name = os.path.splitext(os.path.basename(tmdl))[0]
    with open(tmdl, encoding='utf-8') as f:
        content = f.read()
    items = re.findall(r"\t(?:column|measure)\s+'([^']+(?:''[^']*)*)'", content, re.MULTILINE)
    items += re.findall(r'^\t(?:column|measure)\s+([A-Za-z_][A-Za-z0-9_ ]*?)(?:\s*=|\s*$)', content, re.MULTILINE)
    cleaned = set()
    for c in items:
        c = c.replace("''", "'")
        cleaned.add(c.strip())
    model_cols[table_name] = cleaned


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


def check_ref(entity, prop):
    """Returns True if broken."""
    if entity in model_cols:
        return prop not in model_cols[entity]
    return True


total_broken = 0

# 1. Report-level
rj = os.path.join(report_dir, 'report.json')
with open(rj, encoding='utf-8') as f:
    rdata = json.load(f)
refs = []
find_refs(rdata, refs)
for entity, prop, kind, path in refs:
    if check_ref(entity, prop):
        print(f'REPORT: [{entity}].[{prop}] ({kind}) {path}')
        total_broken += 1

# 2. Page-level
pages_dir = os.path.join(report_dir, 'pages')
for pj in sorted(glob.glob(os.path.join(pages_dir, '*/page.json'))):
    with open(pj, encoding='utf-8') as f:
        pdata = json.load(f)
    refs = []
    find_refs(pdata, refs)
    page_name = pdata.get('displayName', os.path.basename(os.path.dirname(pj)))
    for entity, prop, kind, path in refs:
        if check_ref(entity, prop):
            print(f'PAGE [{page_name}]: [{entity}].[{prop}] ({kind}) {path}')
            total_broken += 1

# 3. Visual-level (queryState + filters)
for vj in sorted(glob.glob(os.path.join(pages_dir, '*/visuals/*/visual.json'))):
    with open(vj, encoding='utf-8') as f:
        data = json.load(f)
    refs = []
    find_refs(data, refs)
    parts = vj.split(os.sep)
    page = parts[-4]
    vid = parts[-2]
    for entity, prop, kind, path in refs:
        if check_ref(entity, prop):
            print(f'VISUAL {page}/{vid[:8]}: [{entity}].[{prop}] ({kind}) {path}')
            total_broken += 1

print(f'\nTotal broken: {total_broken}')
