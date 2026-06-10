"""Catalog all filter shapes in the report — type, where keys, condition structure."""
import json
from pathlib import Path
from collections import Counter

base = Path(r"C:\Tableau to Power BI\PowerBI\UC80_new\UC80\UC80.Report\definition\pages")

shape_counter = Counter()
unusual = []

def shape_of(obj, depth=0):
    if isinstance(obj, dict):
        if depth > 6:
            return "{...}"
        keys = sorted(obj.keys())
        return "{" + ",".join(f"{k}:{shape_of(obj[k], depth+1)}" for k in keys) + "}"
    elif isinstance(obj, list):
        if not obj:
            return "[]"
        # Just show the first elem shape
        return f"[{shape_of(obj[0], depth+1)}](*{len(obj)})"
    elif isinstance(obj, str):
        return "str"
    elif isinstance(obj, bool):
        return "bool"
    elif isinstance(obj, (int, float)):
        return "num"
    elif obj is None:
        return "null"
    return type(obj).__name__

def scan_filter(f, page, visual):
    ftype = f.get('type', '?')
    inner = f.get('filter', {})
    where_list = inner.get('Where', [])
    for i, w in enumerate(where_list):
        cond = w.get('Condition', {})
        cond_keys = sorted(cond.keys())
        shape_key = f"type={ftype} cond=({','.join(cond_keys)})"
        shape_counter[shape_key] += 1
        # Note unusual shapes
        if cond_keys and cond_keys[0] not in ('In', 'Comparison', 'Not', 'And', 'Or', 'RelativeDate', 'DateSpan'):
            unusual.append((page, visual, shape_key, json.dumps(cond)[:300]))
        # Look for nested Compare inside Compare
        if 'Comparison' in cond:
            cmp = cond['Comparison']
            for side in ('Left', 'Right'):
                operand = cmp.get(side, {})
                if isinstance(operand, dict):
                    if 'Comparison' in operand or 'In' in operand or 'Not' in operand:
                        unusual.append((page, visual, f"NESTED_{side}", json.dumps(cmp)[:300]))

for page_dir in base.iterdir():
    if not page_dir.is_dir():
        continue
    page_name = page_dir.name
    pj = page_dir / "page.json"
    if pj.exists():
        try:
            data = json.loads(pj.read_text(encoding="utf-8"))
            for f in (data.get('filterConfig', {}) or {}).get('filters', []):
                scan_filter(f, page_name, '(page)')
        except Exception:
            pass
    vd = page_dir / "visuals"
    if not vd.exists():
        continue
    for vdir in vd.iterdir():
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
            scan_filter(f, page_name, vdir.name)

print("Filter condition shapes:")
for k, v in shape_counter.most_common():
    print(f"  {v:5d} :: {k}")

print(f"\nUnusual ({len(unusual)}):")
for p, v, k, s in unusual[:30]:
    print(f"  {p[:30]} | {v[:30]} | {k}")
    print(f"      {s}")
