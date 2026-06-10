"""Check relationships involving sqlproxy and sqlproxy (EDH_PROGRAMMES_...) tables."""
import os, re

tmdl_dir = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.SemanticModel\definition'

# Check model.tmdl and relationships directory
model_path = os.path.join(tmdl_dir, 'model.tmdl')
with open(model_path, encoding='utf-8') as f:
    content = f.read()

# Find relationship references
print("=== Relationships in model.tmdl ===")
for line in content.split('\n'):
    if 'relationship' in line.lower() or 'ref ' in line.lower():
        if 'relationship' in line.lower():
            print(line.strip())

# Check relationships directory
rel_dir = os.path.join(tmdl_dir, 'relationships')
if os.path.isdir(rel_dir):
    print(f"\n=== Relationships directory ({len(os.listdir(rel_dir))} files) ===")
    for f in sorted(os.listdir(rel_dir)):
        filepath = os.path.join(rel_dir, f)
        with open(filepath, encoding='utf-8') as fh:
            rcontent = fh.read()
        print(f"\n--- {f} ---")
        print(rcontent[:500])
else:
    # Relationships might be in model.tmdl
    print("\n=== Relationship blocks in model.tmdl ===")
    in_rel = False
    block = []
    for line in content.split('\n'):
        if line.strip().startswith('relationship'):
            in_rel = True
            block = [line]
        elif in_rel:
            if line.strip() == '' or (not line.startswith('\t') and not line.startswith(' ')):
                if block:
                    print('\n'.join(block))
                    print()
                in_rel = False
                block = []
            else:
                block.append(line)
    if block:
        print('\n'.join(block))
