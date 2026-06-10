"""Deep scan for malformed SQ Expressions in PBIR filter JSON.

Looks for any `Comparison` whose Left/Right is NOT one of the valid SQExpr shapes,
and any `In.Expressions` element that is not a Column/Measure/HierarchyLevel/Aggregation.

A valid Compare Left/Right should be one of:
  Column, Measure, Literal, Aggregation, HierarchyLevel, ScopedEval, Not, Compare,
  And, Or, Arithmetic, Variable, DateSpan, FillRule, Discretize, ResourcePackageItem,
  TransformOutputRoleRef, NativeReferenceName, Subquery, Member, NamedQueryReference

For our use case any Compare operand should be Column/Measure/Literal/Aggregation/HierarchyLevel.
"""
import json
import sys
from pathlib import Path

VALID_OPERAND_KEYS = {
    'Column', 'Measure', 'Literal', 'Aggregation', 'HierarchyLevel',
    'Arithmetic', 'ScopedEval', 'TransformOutputRoleRef', 'NativeReferenceName',
    'Variable', 'Member', 'NamedQueryReference', 'Subquery', 'DateSpan',
    'PercentOfGrandTotal', 'DefaultValue',
}

base = Path(r"C:\Tableau to Power BI\PowerBI\UC80_new\UC80\UC80.Report\definition\pages")
issues = []

def walk(node, path, page, visual):
    if isinstance(node, dict):
        # Detect Comparison
        if 'Comparison' in node and isinstance(node['Comparison'], dict):
            cmp = node['Comparison']
            for side in ('Left', 'Right'):
                if side in cmp:
                    operand = cmp[side]
                    if not isinstance(operand, dict):
                        issues.append((page, visual, f"{path}/Comparison/{side}",
                                       f"Operand is not dict: {type(operand).__name__}",
                                       json.dumps(operand)[:200]))
                        continue
                    keys = set(operand.keys())
                    if not (keys & VALID_OPERAND_KEYS):
                        issues.append((page, visual, f"{path}/Comparison/{side}",
                                       f"No valid operand key (got {keys})",
                                       json.dumps(operand)[:200]))
        # Detect In
        if 'In' in node and isinstance(node['In'], dict):
            inn = node['In']
            for i, exp in enumerate(inn.get('Expressions') or []):
                if not isinstance(exp, dict):
                    issues.append((page, visual, f"{path}/In/Expressions[{i}]",
                                   f"Not dict: {type(exp).__name__}",
                                   json.dumps(exp)[:200]))
                    continue
                keys = set(exp.keys())
                if not (keys & VALID_OPERAND_KEYS):
                    issues.append((page, visual, f"{path}/In/Expressions[{i}]",
                                   f"No valid operand key (got {keys})",
                                   json.dumps(exp)[:200]))
            for vi, vgroup in enumerate(inn.get('Values') or []):
                if not isinstance(vgroup, list):
                    issues.append((page, visual, f"{path}/In/Values[{vi}]",
                                   f"Not list: {type(vgroup).__name__}",
                                   json.dumps(vgroup)[:200]))
                    continue
                for li, lit in enumerate(vgroup):
                    if not isinstance(lit, dict):
                        issues.append((page, visual, f"{path}/In/Values[{vi}][{li}]",
                                       f"Not dict: {type(lit).__name__}",
                                       json.dumps(lit)[:200]))
                        continue
                    keys = set(lit.keys())
                    if not (keys & {'Literal', 'Column', 'Measure', 'Variable'}):
                        issues.append((page, visual, f"{path}/In/Values[{vi}][{li}]",
                                       f"Not valid literal (got {keys})",
                                       json.dumps(lit)[:200]))
        for k, v in node.items():
            walk(v, f"{path}/{k}", page, visual)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            walk(item, f"{path}[{i}]", page, visual)

for page_dir in base.iterdir():
    if not page_dir.is_dir():
        continue
    page_json = json.loads((page_dir / "page.json").read_text(encoding="utf-8"))
    page_name = page_json.get("displayName", page_dir.name)
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
        except Exception as e:
            issues.append((page_name, vdir.name, "(parse)", str(e), ""))
            continue
        walk(data, "", page_name, vdir.name)

# Also scan report-level / page-level filters
for page_dir in base.iterdir():
    if not page_dir.is_dir():
        continue
    page_json_file = page_dir / "page.json"
    if page_json_file.exists():
        try:
            data = json.loads(page_json_file.read_text(encoding="utf-8"))
            walk(data, "", "(PAGE)" + page_dir.name, "page.json")
        except Exception as e:
            pass

report_json_file = base.parent / "report.json"
if report_json_file.exists():
    data = json.loads(report_json_file.read_text(encoding="utf-8"))
    walk(data, "", "(REPORT)", "report.json")

if not issues:
    print("No malformed SQExpr operands found.")
else:
    print(f"Found {len(issues)} suspicious operands:")
    for page, visual, path, msg, snippet in issues[:50]:
        print(f"  {page} | {visual} | {path}")
        print(f"      {msg}")
        print(f"      {snippet}")
        print()
