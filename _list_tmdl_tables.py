"""List TMDL tables to verify Entity names from filters exist."""
import os, re

tmdl_dir = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.SemanticModel\definition\tables'

for f in sorted(os.listdir(tmdl_dir)):
    if f.endswith('.tmdl'):
        filepath = os.path.join(tmdl_dir, f)
        with open(filepath, encoding='utf-8') as fh:
            first_line = fh.readline().strip()
        print(f'{f:60s} | {first_line}')
