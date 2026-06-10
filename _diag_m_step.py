"""Verify M partition contains the Added 'Date Signature Surveillant PAR' step."""
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

p = (r'C:\Tableau to Power BI\PowerBI\UC80_new\UC80'
     r'\UC80.SemanticModel\definition\tables\EDH_OBSERVATION_UC80 (2).tmdl')
with open(p, 'r', encoding='utf-8') as f:
    txt = f.read()

# Find the M step for the calc column
m = re.search(
    r'#"Added Date Signature Surveillant PAR"\s*=\s*[^\n]+',
    txt
)
if m:
    print("M STEP FOUND:")
    print(m.group(0)[:500])
else:
    print("M STEP NOT FOUND")
    # Look for any 'Date Signature Surveillant PAR' references
    refs = re.findall(r'.{0,80}Date Signature Surveillant PAR.{0,80}', txt)
    print(f"\nTotal references in file: {len(refs)}")
    for r in refs[:5]:
        print(f"  > {r!r}")
