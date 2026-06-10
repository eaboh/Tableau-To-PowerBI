"""Quick reference-integrity check for the freshly regenerated UC80 model."""
import re
import sys
from pathlib import Path

base = Path(r"C:\Tableau to Power BI\PowerBI\UC80_new\UC80")
tmdl_dir = base / "UC80.SemanticModel" / "definition" / "tables"
report_dir = base / "UC80.Report" / "definition" / "pages"
report_json = base / "UC80.Report" / "definition" / "report.json"

table_re = re.compile(r"^\s*table\s+(?:'([^']+)'|([\w]+))", re.M)
member_re = re.compile(r"^\s*(?:column|measure)\s+(?:'([^']+)'|([\w]+))", re.M)
ref_re = re.compile(r"'([^']+)'\[([^\]]+)\]")

declared: dict[str, set[str]] = {}
for f in tmdl_dir.glob("*.tmdl"):
    text = f.read_text(encoding="utf-8", errors="replace")
    tm = table_re.search(text)
    if not tm:
        continue
    tbl = tm.group(1) or tm.group(2)
    cols = {(m.group(1) or m.group(2)) for m in member_re.finditer(text)}
    declared[tbl] = cols

scan = list(tmdl_dir.glob("*.tmdl")) + list(report_dir.rglob("*.json"))
if report_json.exists():
    scan.append(report_json)

# Annotation lines store free-form trace text; skip when scanning real DAX refs.
annot_re = re.compile(r"^\s*annotation\s+\w+\s*=", re.M)

broken = 0
total = 0
for f in scan:
    text = f.read_text(encoding="utf-8", errors="replace")
    is_tmdl = f.suffix == ".tmdl"
    for raw_line in text.splitlines():
        if is_tmdl and annot_re.match(raw_line):
            continue
        for m in ref_re.finditer(raw_line):
            total += 1
            t, c = m.group(1), m.group(2)
            if t in declared and c not in declared[t]:
                broken += 1
                if broken <= 30:
                    print(f"BROKEN {f.name}: '{t}'[{c}]  --  {raw_line.strip()[:160]}")

print(f"\nTotal refs scanned: {total}, broken: {broken}")
sys.exit(0 if broken == 0 else 1)
