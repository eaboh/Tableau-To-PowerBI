"""List ALL unique literal values in Categorical In filters to find problematic ones."""
import json
import os

base = r'C:\Tableau to Power BI\PowerBI\UC80\UC80\UC80.Report\definition\pages'

all_values = {}  # value -> list of filter names
for root, dirs, files in os.walk(base):
    for f in files:
        if f != 'visual.json':
            continue
        fp = os.path.join(root, f)
        with open(fp, encoding='utf-8') as fh:
            data = json.load(fh)
        fc = data.get('filterConfig', {})
        for flt in fc.get('filters', []):
            if flt.get('type') != 'Categorical':
                continue
            fname = flt.get('name', '?')
            filt = flt.get('filter', {})
            where = filt.get('Where', [])
            for w in where:
                cond = w.get('Condition', {})
                in_cond = cond.get('In') or cond.get('Not', {}).get('Expression', {}).get('In')
                if not in_cond:
                    continue
                vals = in_cond.get('Values', [])
                for row in vals:
                    for item in row:
                        v = item.get('Literal', {}).get('Value', '')
                        if v not in all_values:
                            all_values[v] = []
                        all_values[v].append(fname)

# Categorize values
strings = []
numbers = []
booleans = []
others = []

for v in sorted(all_values.keys()):
    count = len(all_values[v])
    if v in ('true', 'false'):
        booleans.append((v, count))
    elif v.startswith("'") and v.endswith("'"):
        strings.append((v, count))
    else:
        try:
            float(v)
            numbers.append((v, count))
        except (ValueError, TypeError):
            others.append((v, count))

print(f'Total unique values: {len(all_values)}')
print(f'  Strings: {len(strings)}')
print(f'  Numbers: {len(numbers)}')
print(f'  Booleans: {len(booleans)}')
print(f'  Others/Unknown: {len(others)}')

if others:
    print('\n=== UNKNOWN FORMAT VALUES (potential issue!) ===')
    for v, count in others:
        print(f'  {repr(v)} (used in {count} filters)')
        # Show which filter uses it
        for fname in all_values[v][:2]:
            print(f'    -> {fname}')

if booleans:
    print(f'\n=== Boolean values ===')
    for v, count in booleans:
        print(f'  {repr(v)} (used in {count} filters)')

print(f'\n=== Sample string values (first 10) ===')
for v, count in strings[:10]:
    print(f'  {repr(v)} (used in {count} filters)')

# Also check for values that contain special characters
print(f'\n=== Values with special chars ===')
for v, count in strings:
    inner = v[1:-1]  # strip outer quotes
    if any(c in inner for c in ("'", '"', '\\', '\n', '\r', '\t')):
        print(f'  SPECIAL: {repr(v)} (used in {count} filters)')
