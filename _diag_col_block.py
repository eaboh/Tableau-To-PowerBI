"""Inspect TMDL block for 'Date Signature Surveillant PAR'."""
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

p = (r'C:\Tableau to Power BI\PowerBI\UC80_new\UC80'
     r'\UC80.SemanticModel\definition\tables\EDH_OBSERVATION_UC80 (2).tmdl')
with open(p, 'r', encoding='utf-8') as f:
    txt = f.read()
m = re.search(r"column 'Date Signature Surveillant PAR'[\s\S]{0,1000}", txt)
print(m.group(0) if m else 'NOT FOUND')
