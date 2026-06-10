"""Find In expressions with mismatched Source refs or odd values."""
import os, json, glob, re

base = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'

issues = []
for vf in glob.glob(os.path.join(base, '**', 'visual.json'), recursive=True):
    with open(vf, encoding='utf-8') as f:
        data = json.load(f)
    visual_id = os.path.basename(os.path.dirname(vf))
    
    for f_idx, filt in enumerate(data.get('filterConfig', {}).get('filters', [])):
        f_obj = filt.get('filter', {})
        from_aliases = {fr['Name']: fr.get('Entity') for fr in f_obj.get('From', [])}
        
        # Walk Where to find In expressions
        for cond in f_obj.get('Where', []):
            # Could be Condition.In or Condition.Not.Expression.In
            in_expr = None
            wrapper = "direct"
            cnode = cond.get('Condition', {})
            if 'In' in cnode:
                in_expr = cnode['In']
                wrapper = "direct"
            elif 'Not' in cnode and isinstance(cnode['Not'], dict):
                expr = cnode['Not'].get('Expression', {})
                if 'In' in expr:
                    in_expr = expr['In']
                    wrapper = "Not"
            if in_expr is None:
                continue
            
            # Check each Expression's Source ref
            for e in in_expr.get('Expressions', []):
                col = e.get('Column') or e.get('Measure') or {}
                src = col.get('Expression', {}).get('SourceRef', {})
                src_alias = src.get('Source')
                src_entity = src.get('Entity')
                if src_alias and src_alias not in from_aliases:
                    issues.append((visual_id, f_idx, f"Source alias '{src_alias}' not in From {list(from_aliases.keys())}"))
                if src_entity and src_entity not in from_aliases.values():
                    issues.append((visual_id, f_idx, f"Source entity '{src_entity}' not in From entities {list(from_aliases.values())}"))
            
            # Show all distinct value types
            for ri, row in enumerate(in_expr.get('Values', [])):
                for vi, val in enumerate(row):
                    lit_val = val.get('Literal', {}).get('Value', '')
                    # Categorize
                    if not isinstance(lit_val, str):
                        issues.append((visual_id, f_idx, f"Non-string Literal.Value: {type(lit_val).__name__} = {lit_val!r}"))

print(f"Total issues found: {len(issues)}")
for visual, fidx, msg in issues[:30]:
    print(f"  {visual}#{fidx}: {msg}")
