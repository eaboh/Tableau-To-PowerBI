"""Audit DAX-only vs M-based calc columns across all tables."""
import os
import re
import sys
import glob

sys.stdout.reconfigure(encoding='utf-8')

ROOT = (r'C:\Tableau to Power BI\PowerBI\UC80_new\UC80'
        r'\UC80.SemanticModel\definition\tables')

# Calc columns are 'column NAME = EXPR' (DAX) or 'column NAME\n  sourceColumn:' (M-based)
# Source columns (non-calc) look like 'column NAME\n  ... sourceColumn: ...' but
# typically have a dataType from the schema. We're interested in counting calc cols.

dax_cols = []
m_cols = []
for tmdl in sorted(glob.glob(os.path.join(ROOT, '*.tmdl'))):
    table = os.path.basename(tmdl).replace('.tmdl', '')
    with open(tmdl, 'r', encoding='utf-8') as f:
        txt = f.read()

    # Find DAX-style calc columns: `column NAME = EXPR`
    for m in re.finditer(r"^\s*column\s+'?([^'=\n]+?)'?\s*=\s*(.+?)$",
                         txt, re.MULTILINE):
        col_name = m.group(1).strip()
        expr = m.group(2).strip()
        dax_cols.append((table, col_name, expr[:80]))

    # Find M-step Added columns (these are the M-based calc cols)
    for m in re.finditer(r'#"Added ([^"]+)"\s*=\s*Table\.AddColumn', txt):
        m_cols.append((table, m.group(1)))

print(f"=== DAX-only calc columns: {len(dax_cols)} ===")
for t, c, e in dax_cols[:15]:
    print(f"  {t:55s} | {c:40s} | {e}")
if len(dax_cols) > 15:
    print(f"  ... +{len(dax_cols) - 15} more")

print(f"\n=== M-based (Table.AddColumn) columns: {len(m_cols)} ===")
# Group by table
from collections import Counter
by_tbl = Counter(t for t, _ in m_cols)
for t, n in by_tbl.most_common(10):
    print(f"  {t:55s} | {n} M steps")

# Check key columns
print("\n=== Key calc columns from earlier failure ===")
key_cols = ['Date Signature Surveillant PAR', 'FLT Date Signature surveillant PAR',
            'FLT Semaine N', 'FLT Semaine N-1']
for kc in key_cols:
    dax_hit = [x for x in dax_cols if x[1] == kc]
    m_hit = [x for x in m_cols if x[1] == kc]
    status = 'DAX' if dax_hit else ('M' if m_hit else 'MISSING')
    print(f"  {kc:45s} -> {status}")
