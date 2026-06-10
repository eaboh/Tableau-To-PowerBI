"""Inspect all In expressions to find ones with anomalies."""
import os, json, glob

base = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'

def find_in_expressions(node, path=""):
    """Recursively find all 'In' expressions and yield (path, In_node)."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "In" and isinstance(v, dict):
                yield (path + "." + k, v)
            yield from find_in_expressions(v, path + "." + k)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            yield from find_in_expressions(item, path + f"[{i}]")

problematic = []
for vf in glob.glob(os.path.join(base, '**', 'visual.json'), recursive=True):
    with open(vf, encoding='utf-8') as f:
        data = json.load(f)
    visual_id = os.path.basename(os.path.dirname(vf))
    
    for f_idx, filt in enumerate(data.get('filterConfig', {}).get('filters', [])):
        for path, in_expr in find_in_expressions(filt):
            exprs = in_expr.get('Expressions', [])
            values = in_expr.get('Values', [])
            
            # Check Expressions: each must be a Column or Measure ref
            for ei, e in enumerate(exprs):
                if not isinstance(e, dict):
                    problematic.append((visual_id, f_idx, f"Expression[{ei}] is {type(e).__name__}, not dict"))
                elif not any(k in e for k in ['Column', 'Measure', 'HierarchyLevel', 'Aggregation']):
                    problematic.append((visual_id, f_idx, f"Expression[{ei}] missing Column/Measure: keys={list(e.keys())}"))
            
            # Check Values: each row must be a list of Literals
            for ri, row in enumerate(values):
                if not isinstance(row, list):
                    problematic.append((visual_id, f_idx, f"Values[{ri}] is {type(row).__name__}, not list"))
                    continue
                if len(row) != len(exprs):
                    problematic.append((visual_id, f_idx, f"Values[{ri}] length {len(row)} != Expressions length {len(exprs)}"))
                for vi, val in enumerate(row):
                    if not isinstance(val, dict):
                        problematic.append((visual_id, f_idx, f"Values[{ri}][{vi}] is {type(val).__name__}, not dict"))
                    elif 'Literal' not in val:
                        problematic.append((visual_id, f_idx, f"Values[{ri}][{vi}] missing Literal: keys={list(val.keys())}"))

print(f"Total problematic In expressions: {len(problematic)}")
for visual, fidx, msg in problematic[:20]:
    print(f"  visual={visual} filter#{fidx}: {msg}")
