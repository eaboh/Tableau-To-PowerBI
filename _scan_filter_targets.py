"""Find filters where the (Entity, Property) target doesn't match any table in TMDL."""
import json
import re
from pathlib import Path

base = Path(r"C:\Tableau to Power BI\PowerBI\UC80_new\UC80")
report_pages = base / "UC80.Report" / "definition" / "pages"
tmdl_dir = base / "UC80.SemanticModel" / "definition" / "tables"

# Build (table, name) -> kind map from TMDL
symbols = {}  # (table_name, name) -> "measure" or "column"
for tmdl in tmdl_dir.glob("*.tmdl"):
    try:
        text = tmdl.read_text(encoding="utf-8")
    except Exception:
        continue
    # Extract table name
    mtbl = re.search(r"^table\s+'?([^'\r\n]+?)'?\s*$", text, re.MULTILINE)
    if not mtbl:
        continue
    tname = mtbl.group(1).strip()
    # Find all measures: `^\s+measure 'name' = ...` or `^\s+measure name = ...`
    for m in re.finditer(r"(?m)^\s+measure\s+(?:'([^']+)'|(\S+))\s*=", text):
        nm = m.group(1) or m.group(2)
        symbols[(tname, nm)] = "measure"
    # Find all columns: `^\s+column 'name'` or `^\s+column name`
    for m in re.finditer(r"(?m)^\s+column\s+(?:'([^']+)'|(\S+))(?:\s|$)", text):
        nm = m.group(1) or m.group(2)
        symbols[(tname, nm)] = "column"

print(f"Loaded {len(symbols)} symbols from TMDL")

issues = []

def walk(node, path, page, visual):
    if isinstance(node, dict):
        # Check Comparison.Left / Right and In.Expressions for Measure/Column refs
        # whose entity is from `From: [{Name, Entity}]`
        if 'Comparison' in node and isinstance(node['Comparison'], dict):
            cmp = node['Comparison']
            for side in ('Left', 'Right'):
                operand = cmp.get(side, {})
                for kind in ('Measure', 'Column'):
                    if kind in operand:
                        prop = operand[kind].get('Property', '')
                        # We need the Entity from outer From — track via path
                        # Pass through for verification later; we'll do a 
                        # second pass that resolves Source aliases
                        operand['_kind'] = kind
                        operand['_prop'] = prop
        for k, v in node.items():
            walk(v, f"{path}/{k}", page, visual)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            walk(item, f"{path}[{i}]", page, visual)

def check_filter_block(filter_block, page, visual):
    """For each filter, build {SourceName -> Entity} from From, then check
    every Comparison Left/Right and In.Expressions Measure/Column for
    presence in `symbols`."""
    if not isinstance(filter_block, dict):
        return
    inner = filter_block.get('filter') or {}
    from_list = inner.get('From') or []
    src_map = {}
    for fr in from_list:
        if isinstance(fr, dict):
            src_map[fr.get('Name', '')] = fr.get('Entity', '')
    # Also look at outer field's Entity
    field = filter_block.get('field') or {}
    for kind in ('Column', 'Measure'):
        if kind in field:
            ent = field[kind].get('Expression', {}).get('SourceRef', {}).get('Entity', '')
            prop = field[kind].get('Property', '')
            if ent and prop:
                if (ent, prop) not in symbols:
                    issues.append({
                        'page': page, 'visual': visual, 'where': 'field',
                        'kind': kind, 'entity': ent, 'prop': prop,
                        'note': "field-level target not in TMDL"
                    })
                else:
                    actual_kind = symbols[(ent, prop)]
                    if actual_kind != kind.lower():
                        issues.append({
                            'page': page, 'visual': visual, 'where': 'field',
                            'kind': kind, 'entity': ent, 'prop': prop,
                            'note': f"field declared as {kind} but TMDL has it as {actual_kind}"
                        })
    # Recurse into Where
    where = inner.get('Where') or []
    def chk_operand(operand, where_path):
        if not isinstance(operand, dict):
            return
        for kind in ('Column', 'Measure'):
            if kind in operand:
                src = operand[kind].get('Expression', {}).get('SourceRef', {}).get('Source', '')
                ent = src_map.get(src, src)
                prop = operand[kind].get('Property', '')
                if ent and prop:
                    if (ent, prop) not in symbols:
                        issues.append({
                            'page': page, 'visual': visual, 'where': where_path,
                            'kind': kind, 'entity': ent, 'prop': prop,
                            'note': "operand target not in TMDL"
                        })
                    else:
                        actual_kind = symbols[(ent, prop)]
                        if actual_kind != kind.lower():
                            issues.append({
                                'page': page, 'visual': visual, 'where': where_path,
                                'kind': kind, 'entity': ent, 'prop': prop,
                                'note': f"operand declared as {kind} but TMDL has it as {actual_kind}"
                            })
    def walk_cond(cond, p):
        if not isinstance(cond, dict):
            return
        if 'Comparison' in cond:
            cmp = cond['Comparison']
            chk_operand(cmp.get('Left'), f"{p}/Compare/Left")
            chk_operand(cmp.get('Right'), f"{p}/Compare/Right")
        if 'In' in cond:
            for i, exp in enumerate(cond['In'].get('Expressions') or []):
                chk_operand(exp, f"{p}/In/Expr[{i}]")
        if 'Not' in cond:
            walk_cond(cond['Not'].get('Expression'), f"{p}/Not")
        if 'And' in cond or 'Or' in cond:
            for k in ('And', 'Or'):
                if k in cond:
                    walk_cond(cond[k].get('Left', {}).get('Condition'), f"{p}/{k}/L")
                    walk_cond(cond[k].get('Right', {}).get('Condition'), f"{p}/{k}/R")
    for i, w in enumerate(where):
        walk_cond(w.get('Condition'), f"Where[{i}]")

for page_dir in report_pages.iterdir():
    if not page_dir.is_dir():
        continue
    page_name = page_dir.name
    pj = page_dir / "page.json"
    if pj.exists():
        try:
            data = json.loads(pj.read_text(encoding="utf-8"))
            for f in (data.get('filterConfig', {}) or {}).get('filters', []):
                check_filter_block(f, page_name, "(page)")
        except Exception as e:
            pass
    visuals_dir = page_dir / "visuals"
    if not visuals_dir.exists():
        continue
    for vdir in visuals_dir.iterdir():
        if not vdir.is_dir():
            continue
        vfile = vdir / "visual.json"
        if not vfile.exists():
            continue
        try:
            data = json.loads(vfile.read_text(encoding="utf-8"))
        except Exception:
            continue
        for f in (data.get('filterConfig', {}) or {}).get('filters', []):
            check_filter_block(f, page_name, vdir.name)

# Group and print
print(f"\n{len(issues)} mismatched filter targets:")
seen = set()
for it in issues:
    key = (it['entity'], it['prop'], it['kind'], it['note'])
    if key in seen:
        continue
    seen.add(key)
    print(f"  [{it['kind']}] '{it['entity']}'.'{it['prop']}' :: {it['note']}")
print(f"\n(distinct: {len(seen)} / total occurrences: {len(issues)})")
